"""Deterministic regular-grid primitives for drainage-guided terrain shaping."""

from dataclasses import dataclass
from heapq import heappop, heappush
from math import hypot

import numpy as np
from numpy.typing import NDArray

_NEIGHBOURS = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)


@dataclass(frozen=True, slots=True)
class DrainageIncision:
    """Canonical automatic-valley products derived from one routing surface."""

    incision_m: NDArray[np.float64]
    accumulation_km2: NDArray[np.float64]
    detail_suppression: NDArray[np.float64]
    channel_mask: NDArray[np.bool_]
    channel_head_mask: NDArray[np.bool_]
    stream_order: NDArray[np.uint16]
    floor_correction_m: NDArray[np.float64]
    steepness_correction_m: NDArray[np.float64]
    unresolved_uphill_channel_edge_count: int
    unresolved_steepening_edge_count: int
    maximum_downstream_steepening_ratio: float


@dataclass(frozen=True, slots=True)
class DrainageDiagnostics:
    """Compact drainage measurements derived from a completed terrain surface."""

    algorithm_id: str
    grid_width: int
    grid_height: int
    x_spacing_km: float
    y_spacing_km: float
    fill_tolerance_m: float
    land_cell_count: int
    outlet_cell_count: int
    potential_sink_cell_count: int
    directly_connected_land_cell_count: int
    depression_cell_count: int
    basin_candidate_count: int
    flat_terminal_cell_count: int
    maximum_fill_depth_m: float
    depression_fill_volume_km3: float
    largest_outlet_catchment_km2: float
    basin_candidates: tuple[DrainageBasinCandidate, ...]


@dataclass(frozen=True, slots=True)
class DrainageBasinCandidate:
    """One coarse connected fill region that merits author review.

    A candidate is derived from the canonical diagnostic grid. It is not an
    authored lake, a watershed polygon, or a promise that the depression is
    natural rather than a scale or generation artefact.
    """

    normalized_x: float
    normalized_y: float
    cell_count: int
    area_km2: float
    floor_elevation_m: float
    spill_elevation_m: float
    maximum_fill_depth_m: float
    fill_volume_km3: float
    terminal_cell_count: int


def _basin_candidates(
    elevation_m: NDArray[np.float64],
    filled_elevation_m: NDArray[np.float64],
    significant_fill: NDArray[np.bool_],
    potential_sinks: NDArray[np.bool_],
    *,
    x_spacing_km: float,
    y_spacing_km: float,
) -> tuple[DrainageBasinCandidate, ...]:
    """Group 8-connected significant fill cells into deterministic candidates."""

    height, width = elevation_m.shape
    remaining = significant_fill.copy()
    fill_depth_m = np.maximum(filled_elevation_m - elevation_m, 0.0)
    flat_depth = fill_depth_m.ravel()
    flat_elevation = elevation_m.ravel()
    flat_filled = filled_elevation_m.ravel()
    flat_sinks = potential_sinks.ravel()
    cell_area_km2 = x_spacing_km * y_spacing_km
    candidates: list[DrainageBasinCandidate] = []

    for starting_index_value in np.flatnonzero(remaining):
        starting_index = int(starting_index_value)
        starting_row, starting_column = divmod(starting_index, width)
        if not remaining[starting_row, starting_column]:
            continue
        remaining[starting_row, starting_column] = False
        stack = [starting_index]
        component: list[int] = []
        while stack:
            flat_index = stack.pop()
            component.append(flat_index)
            row, column = divmod(flat_index, width)
            for row_offset, column_offset in _NEIGHBOURS:
                neighbour_row = row + row_offset
                neighbour_column = column + column_offset
                if not (
                    0 <= neighbour_row < height
                    and 0 <= neighbour_column < width
                    and remaining[neighbour_row, neighbour_column]
                ):
                    continue
                remaining[neighbour_row, neighbour_column] = False
                stack.append(neighbour_row * width + neighbour_column)

        component_indices = np.asarray(component, dtype=np.int64)
        component_depths = flat_depth[component_indices]
        maximum_depth_m = float(np.max(component_depths))
        deepest_index = min(
            int(index)
            for index in component_indices[component_depths == maximum_depth_m]
        )
        deepest_row, deepest_column = divmod(deepest_index, width)
        candidates.append(
            DrainageBasinCandidate(
                normalized_x=deepest_column / max(1, width - 1),
                normalized_y=deepest_row / max(1, height - 1),
                cell_count=len(component),
                area_km2=len(component) * cell_area_km2,
                floor_elevation_m=float(flat_elevation[deepest_index]),
                spill_elevation_m=float(flat_filled[deepest_index]),
                maximum_fill_depth_m=maximum_depth_m,
                fill_volume_km3=(
                    float(np.sum(component_depths)) * cell_area_km2 / 1_000.0
                ),
                terminal_cell_count=int(np.count_nonzero(flat_sinks[component_indices])),
            )
        )

    candidates.sort(
        key=lambda candidate: (
            -candidate.maximum_fill_depth_m,
            -candidate.fill_volume_km3,
            candidate.normalized_y,
            candidate.normalized_x,
        )
    )
    return tuple(candidates)


def _outlet_mask(land_mask: NDArray[np.bool_]) -> NDArray[np.bool_]:
    padded = np.pad(land_mask, 1, mode="constant", constant_values=False)
    surrounded_by_land = land_mask.copy()
    for row_offset, column_offset in _NEIGHBOURS:
        row_slice = slice(1 + row_offset, 1 + row_offset + land_mask.shape[0])
        column_slice = slice(
            1 + column_offset,
            1 + column_offset + land_mask.shape[1],
        )
        surrounded_by_land &= padded[row_slice, column_slice]
    return land_mask & ~surrounded_by_land


def priority_flood_surface(
    elevation_m: NDArray[np.float64],
    land_mask: NDArray[np.bool_],
) -> NDArray[np.float64]:
    """Return a routing surface on which every land cell can reach a coast.

    The returned surface is a temporary hydrology product. It fills accidental
    depressions but never replaces the authored/generated elevation surface.
    Raised cells receive the smallest representable downstream grade so flats
    have a deterministic route toward their spill point.
    """

    if elevation_m.shape != land_mask.shape or elevation_m.ndim != 2:
        raise ValueError("Elevation and land mask must be equally shaped 2D arrays.")
    if np.any(land_mask & ~np.isfinite(elevation_m)):
        raise ValueError("Land elevations must be finite before drainage routing.")

    height, width = elevation_m.shape
    filled = elevation_m.copy()
    visited = np.zeros_like(land_mask)
    queue: list[tuple[float, int, int]] = []

    for row, column in np.argwhere(_outlet_mask(land_mask)):
        visited[row, column] = True
        heappush(queue, (float(filled[row, column]), int(row), int(column)))

    if np.any(land_mask) and not queue:
        raise ValueError("Land mask has no edge or coastline outlet.")

    while queue:
        current_height, row, column = heappop(queue)
        for row_offset, column_offset in _NEIGHBOURS:
            neighbour_row = row + row_offset
            neighbour_column = column + column_offset
            if not (
                0 <= neighbour_row < height
                and 0 <= neighbour_column < width
                and land_mask[neighbour_row, neighbour_column]
                and not visited[neighbour_row, neighbour_column]
            ):
                continue
            visited[neighbour_row, neighbour_column] = True
            original_height = float(filled[neighbour_row, neighbour_column])
            routed_height = max(
                original_height,
                float(np.nextafter(current_height, np.inf)),
            )
            filled[neighbour_row, neighbour_column] = routed_height
            heappush(queue, (routed_height, neighbour_row, neighbour_column))

    if np.any(land_mask & ~visited):
        raise RuntimeError("Priority-Flood left land disconnected from every outlet.")
    return filled


def multiple_flow_accumulation(
    routing_elevation_m: NDArray[np.float64],
    land_mask: NDArray[np.bool_],
    *,
    x_spacing_km: float,
    y_spacing_km: float,
    exponent: float = 1.1,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return MFD contributing area in km2 and maximum local downslope grade.

    Flow is divided among every lower D8 neighbour in proportion to
    ``slope**exponent``. Stable descending ordering and a fixed neighbour order
    make ties reproducible without introducing a mutable random stream.
    """

    if routing_elevation_m.shape != land_mask.shape or routing_elevation_m.ndim != 2:
        raise ValueError("Routing elevation and land mask must be equally shaped 2D arrays.")
    if x_spacing_km <= 0.0 or y_spacing_km <= 0.0 or exponent <= 0.0:
        raise ValueError("Grid spacing and MFD exponent must be positive.")

    height, width = routing_elevation_m.shape
    cell_area_km2 = x_spacing_km * y_spacing_km
    accumulation = np.where(land_mask, cell_area_km2, 0.0).astype(np.float64)
    maximum_slope = np.zeros_like(routing_elevation_m)
    flat_indices = np.flatnonzero(land_mask)
    order = flat_indices[
        np.argsort(-routing_elevation_m.ravel()[flat_indices], kind="stable")
    ]

    for flat_index in order:
        row, column = divmod(int(flat_index), width)
        current_height = float(routing_elevation_m[row, column])
        recipients: list[tuple[int, int, float]] = []
        for row_offset, column_offset in _NEIGHBOURS:
            neighbour_row = row + row_offset
            neighbour_column = column + column_offset
            if not (
                0 <= neighbour_row < height
                and 0 <= neighbour_column < width
                and land_mask[neighbour_row, neighbour_column]
            ):
                continue
            drop_m = current_height - float(
                routing_elevation_m[neighbour_row, neighbour_column]
            )
            if drop_m <= 0.0:
                continue
            distance_km = hypot(
                column_offset * x_spacing_km,
                row_offset * y_spacing_km,
            )
            slope = drop_m / (1_000.0 * distance_km)
            recipients.append((neighbour_row, neighbour_column, slope**exponent))
            maximum_slope[row, column] = max(maximum_slope[row, column], slope)
        if not recipients:
            continue
        total_weight = sum(weight for _row, _column, weight in recipients)
        for neighbour_row, neighbour_column, weight in recipients:
            accumulation[neighbour_row, neighbour_column] += (
                accumulation[row, column] * weight / total_weight
            )

    return accumulation, maximum_slope


def steepest_flow_accumulation(
    routing_elevation_m: NDArray[np.float64],
    land_mask: NDArray[np.bool_],
    *,
    x_spacing_km: float,
    y_spacing_km: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return D8 contributing area and receiver slope for a unique flow tree."""

    receivers, receiver_slope = steepest_flow_receivers(
        routing_elevation_m,
        land_mask,
        x_spacing_km=x_spacing_km,
        y_spacing_km=y_spacing_km,
    )

    accumulation = _accumulate_steepest_receivers(
        routing_elevation_m,
        land_mask,
        receivers,
        cell_area_km2=x_spacing_km * y_spacing_km,
    )
    return accumulation, receiver_slope


def _accumulate_steepest_receivers(
    routing_elevation_m: NDArray[np.float64],
    land_mask: NDArray[np.bool_],
    receivers: NDArray[np.int64],
    *,
    cell_area_km2: float,
) -> NDArray[np.float64]:
    """Accumulate cell area through an already computed receiver tree."""

    accumulation = np.where(land_mask, cell_area_km2, 0.0).astype(np.float64)
    flat_indices = np.flatnonzero(land_mask)
    order = flat_indices[
        np.argsort(-routing_elevation_m.ravel()[flat_indices], kind="stable")
    ]
    flat_receivers = receivers.ravel()
    flat_accumulation = accumulation.ravel()
    for flat_index in order:
        receiver = int(flat_receivers[flat_index])
        if receiver >= 0:
            flat_accumulation[receiver] += flat_accumulation[flat_index]
    return accumulation


def steepest_flow_receivers(
    routing_elevation_m: NDArray[np.float64],
    land_mask: NDArray[np.bool_],
    *,
    x_spacing_km: float,
    y_spacing_km: float,
) -> tuple[NDArray[np.int64], NDArray[np.float64]]:
    """Return each cell's steepest lower D8 receiver and corresponding slope."""

    if routing_elevation_m.shape != land_mask.shape or routing_elevation_m.ndim != 2:
        raise ValueError("Routing elevation and land mask must be equally shaped 2D arrays.")
    if x_spacing_km <= 0.0 or y_spacing_km <= 0.0:
        raise ValueError("Grid spacing must be positive.")

    height, width = routing_elevation_m.shape
    receivers = np.full(routing_elevation_m.shape, -1, dtype=np.int64)
    receiver_slope = np.zeros_like(routing_elevation_m)
    flat_indices = np.flatnonzero(land_mask)

    for flat_index in flat_indices:
        row, column = divmod(int(flat_index), width)
        current_height = float(routing_elevation_m[row, column])
        receiver: tuple[int, int] | None = None
        steepest_slope = 0.0
        for row_offset, column_offset in _NEIGHBOURS:
            neighbour_row = row + row_offset
            neighbour_column = column + column_offset
            if not (
                0 <= neighbour_row < height
                and 0 <= neighbour_column < width
                and land_mask[neighbour_row, neighbour_column]
            ):
                continue
            drop_m = current_height - float(
                routing_elevation_m[neighbour_row, neighbour_column]
            )
            if drop_m <= 0.0:
                continue
            distance_km = hypot(
                column_offset * x_spacing_km,
                row_offset * y_spacing_km,
            )
            slope = drop_m / (1_000.0 * distance_km)
            if slope > steepest_slope:
                steepest_slope = slope
                receiver = neighbour_row, neighbour_column
        if receiver is None:
            continue
        receiver_row, receiver_column = receiver
        receivers[row, column] = receiver_row * width + receiver_column
        receiver_slope[row, column] = steepest_slope

    return receivers, receiver_slope


def drainage_diagnostics(
    elevation_m: NDArray[np.float64],
    land_mask: NDArray[np.bool_],
    *,
    x_spacing_km: float,
    y_spacing_km: float,
    fill_tolerance_m: float = 0.01,
) -> DrainageDiagnostics:
    """Measure direct sea connectivity and required depression conditioning."""

    if elevation_m.shape != land_mask.shape or elevation_m.ndim != 2:
        raise ValueError("Elevation and land mask must be equally shaped 2D arrays.")
    if fill_tolerance_m < 0.0:
        raise ValueError("Fill tolerance must not be negative.")
    if np.any(land_mask & ~np.isfinite(elevation_m)):
        raise ValueError("Land elevations must be finite before drainage analysis.")

    outlets = _outlet_mask(land_mask)
    receivers, _slopes = steepest_flow_receivers(
        elevation_m,
        land_mask,
        x_spacing_km=x_spacing_km,
        y_spacing_km=y_spacing_km,
    )
    flat_land = np.flatnonzero(land_mask)
    ascending = flat_land[
        np.argsort(elevation_m.ravel()[flat_land], kind="stable")
    ]
    connected = outlets.ravel().copy()
    flat_receivers = receivers.ravel()
    for flat_index in ascending:
        receiver = int(flat_receivers[flat_index])
        if receiver >= 0:
            connected[flat_index] = connected[receiver]

    potential_sinks = (
        land_mask.ravel() & ~outlets.ravel() & (flat_receivers < 0)
    ).reshape(land_mask.shape)
    filled = priority_flood_surface(elevation_m, land_mask)
    fill_depth_m = np.where(land_mask, np.maximum(filled - elevation_m, 0.0), 0.0)
    significant_fill = fill_depth_m > fill_tolerance_m
    basin_candidates = _basin_candidates(
        elevation_m,
        filled,
        significant_fill,
        potential_sinks,
        x_spacing_km=x_spacing_km,
        y_spacing_km=y_spacing_km,
    )
    conditioned_receivers, _conditioned_slopes = steepest_flow_receivers(
        filled,
        land_mask,
        x_spacing_km=x_spacing_km,
        y_spacing_km=y_spacing_km,
    )
    conditioned_connected = outlets.ravel().copy()
    flat_conditioned_receivers = conditioned_receivers.ravel()
    conditioned_ascending = flat_land[
        np.argsort(filled.ravel()[flat_land], kind="stable")
    ]
    for flat_index in conditioned_ascending:
        receiver = int(flat_conditioned_receivers[flat_index])
        if receiver >= 0:
            conditioned_connected[flat_index] = conditioned_connected[receiver]
    if np.any(land_mask.ravel() & ~conditioned_connected):
        raise RuntimeError("Conditioned diagnostic surface does not reach an outlet.")

    conditioned_accumulation, _conditioned_slope = steepest_flow_accumulation(
        filled,
        land_mask,
        x_spacing_km=x_spacing_km,
        y_spacing_km=y_spacing_km,
    )
    cell_area_km2 = x_spacing_km * y_spacing_km
    fill_volume_km3 = float(np.sum(fill_depth_m)) * cell_area_km2 / 1_000.0
    return DrainageDiagnostics(
        algorithm_id="canonical-d8-priority-flood-diagnostics@2",
        grid_width=elevation_m.shape[1],
        grid_height=elevation_m.shape[0],
        x_spacing_km=x_spacing_km,
        y_spacing_km=y_spacing_km,
        fill_tolerance_m=fill_tolerance_m,
        land_cell_count=int(np.count_nonzero(land_mask)),
        outlet_cell_count=int(np.count_nonzero(outlets)),
        potential_sink_cell_count=int(np.count_nonzero(potential_sinks)),
        directly_connected_land_cell_count=int(np.count_nonzero(land_mask.ravel() & connected)),
        depression_cell_count=int(np.count_nonzero(significant_fill)),
        basin_candidate_count=len(basin_candidates),
        flat_terminal_cell_count=int(
            np.count_nonzero(potential_sinks & ~significant_fill)
        ),
        maximum_fill_depth_m=float(np.max(fill_depth_m, initial=0.0)),
        depression_fill_volume_km3=fill_volume_km3,
        largest_outlet_catchment_km2=float(
            np.max(conditioned_accumulation[outlets], initial=0.0)
        ),
        basin_candidates=basin_candidates,
    )


def _masked_smooth(
    values: NDArray[np.float64],
    land_mask: NDArray[np.bool_],
    iterations: int,
) -> NDArray[np.float64]:
    result = np.where(land_mask, values, 0.0)
    weights = land_mask.astype(np.float64)
    for _ in range(iterations):
        padded_values = np.pad(result, 1, mode="constant")
        padded_weights = np.pad(weights, 1, mode="constant")
        value_sum = 4.0 * padded_values[1:-1, 1:-1]
        weight_sum = 4.0 * padded_weights[1:-1, 1:-1]
        for row_offset, column_offset in _NEIGHBOURS:
            neighbour_weight = 1.0 if row_offset == 0 or column_offset == 0 else 0.7
            row_slice = slice(1 + row_offset, 1 + row_offset + values.shape[0])
            column_slice = slice(
                1 + column_offset,
                1 + column_offset + values.shape[1],
            )
            value_sum += neighbour_weight * padded_values[row_slice, column_slice]
            weight_sum += neighbour_weight * padded_weights[row_slice, column_slice]
        result = np.divide(
            value_sum,
            weight_sum,
            out=np.zeros_like(value_sum),
            where=weight_sum > 0.0,
        )
        result = np.where(land_mask, result, 0.0)
    return result


def _connected_channel_network(
    initiation_mask: NDArray[np.bool_],
    receivers: NDArray[np.int64],
    land_mask: NDArray[np.bool_],
) -> tuple[NDArray[np.bool_], NDArray[np.bool_]]:
    """Trace every initiated channel downstream and identify network heads."""

    if initiation_mask.shape != land_mask.shape or receivers.shape != land_mask.shape:
        raise ValueError("Channel initiation, receivers, and land must share a shape.")
    flat_channel = (initiation_mask & land_mask).ravel().copy()
    flat_receivers = receivers.ravel()
    for starting_index_value in np.flatnonzero(flat_channel):
        current = int(starting_index_value)
        while True:
            receiver = int(flat_receivers[current])
            if receiver < 0 or flat_channel[receiver]:
                break
            flat_channel[receiver] = True
            current = receiver

    has_channel_donor = np.zeros(flat_channel.shape, dtype=np.bool_)
    for donor_value in np.flatnonzero(flat_channel):
        receiver = int(flat_receivers[int(donor_value)])
        if receiver >= 0 and flat_channel[receiver]:
            has_channel_donor[receiver] = True
    channel_heads = flat_channel & ~has_channel_donor
    return (
        flat_channel.reshape(land_mask.shape),
        channel_heads.reshape(land_mask.shape),
    )


def strahler_stream_order(
    channel_mask: NDArray[np.bool_],
    receivers: NDArray[np.int64],
    routing_surface_m: NDArray[np.float64],
) -> NDArray[np.uint16]:
    """Return deterministic Horton-Strahler order for a routed channel tree.

    First-order reaches begin at channel heads. Equal-order tributaries raise
    the downstream order by one; a lower-order tributary joining a larger
    reach leaves the larger order unchanged.
    """

    if (
        channel_mask.ndim != 2
        or receivers.shape != channel_mask.shape
        or routing_surface_m.shape != channel_mask.shape
    ):
        raise ValueError("Channel order arrays must share an equally shaped 2D grid.")
    if np.any(channel_mask & ~np.isfinite(routing_surface_m)):
        raise ValueError("Selected-channel routing elevations must be finite.")

    flat_channel = channel_mask.ravel()
    flat_receivers = receivers.ravel()
    flat_routing_surface_m = routing_surface_m.ravel()
    channel_indices = np.flatnonzero(flat_channel)
    upstream_first = channel_indices[
        np.argsort(-flat_routing_surface_m[channel_indices], kind="stable")
    ]
    order = np.zeros(flat_channel.shape, dtype=np.uint16)
    largest_donor_order = np.zeros(flat_channel.shape, dtype=np.uint16)
    largest_donor_count = np.zeros(flat_channel.shape, dtype=np.uint16)

    for channel_index_value in upstream_first:
        channel_index = int(channel_index_value)
        donor_order = int(largest_donor_order[channel_index])
        if donor_order == 0:
            current_order = 1
        else:
            current_order = donor_order + int(largest_donor_count[channel_index] >= 2)
        if current_order > np.iinfo(np.uint16).max:
            raise OverflowError("Channel hierarchy exceeds the supported stream order.")
        order[channel_index] = current_order

        receiver = int(flat_receivers[channel_index])
        if receiver < 0:
            continue
        if receiver >= flat_channel.size:
            raise ValueError("Channel receiver index falls outside the grid.")
        if not flat_channel[receiver]:
            continue
        if flat_routing_surface_m[receiver] >= flat_routing_surface_m[channel_index]:
            raise ValueError("Channel receivers must descend on the routing surface.")
        if current_order > largest_donor_order[receiver]:
            largest_donor_order[receiver] = current_order
            largest_donor_count[receiver] = 1
        elif current_order == largest_donor_order[receiver]:
            largest_donor_count[receiver] += 1

    return order.reshape(channel_mask.shape)


def _condition_downstream_channel_floors(
    source_elevation_m: NDArray[np.float64],
    incision_m: NDArray[np.float64],
    maximum_incision_m: NDArray[np.float64],
    channel_mask: NDArray[np.bool_],
    receivers: NDArray[np.int64],
    routing_surface_m: NDArray[np.float64],
    *,
    minimum_drop_m: float = 0.01,
) -> tuple[NDArray[np.float64], NDArray[np.float64], int]:
    """Lower generated channel floors just enough to maintain downstream descent."""

    shape = source_elevation_m.shape
    if any(
        values.shape != shape
        for values in (
            incision_m,
            maximum_incision_m,
            channel_mask,
            receivers,
            routing_surface_m,
        )
    ):
        raise ValueError("Channel-floor conditioning arrays must share a shape.")
    if minimum_drop_m < 0.0:
        raise ValueError("Minimum downstream drop must not be negative.")

    conditioned = np.minimum(incision_m, maximum_incision_m).copy()
    flat_source = source_elevation_m.ravel()
    flat_conditioned = conditioned.ravel()
    flat_maximum = maximum_incision_m.ravel()
    flat_channel = channel_mask.ravel()
    flat_receivers = receivers.ravel()
    channel_indices = np.flatnonzero(flat_channel)
    order = channel_indices[
        np.argsort(-routing_surface_m.ravel()[channel_indices], kind="stable")
    ]

    for donor_value in order:
        donor = int(donor_value)
        receiver = int(flat_receivers[donor])
        if receiver < 0 or not flat_channel[receiver]:
            continue
        donor_floor_m = flat_source[donor] - flat_conditioned[donor]
        maximum_receiver_floor_m = donor_floor_m - minimum_drop_m
        receiver_floor_m = flat_source[receiver] - flat_conditioned[receiver]
        if receiver_floor_m <= maximum_receiver_floor_m:
            continue
        required_incision_m = flat_source[receiver] - maximum_receiver_floor_m
        flat_conditioned[receiver] = min(
            flat_maximum[receiver],
            max(flat_conditioned[receiver], required_incision_m),
        )

    unresolved = 0
    for donor_value in channel_indices:
        donor = int(donor_value)
        receiver = int(flat_receivers[donor])
        if receiver < 0 or not flat_channel[receiver]:
            continue
        donor_floor_m = flat_source[donor] - flat_conditioned[donor]
        receiver_floor_m = flat_source[receiver] - flat_conditioned[receiver]
        if receiver_floor_m > donor_floor_m - minimum_drop_m + 1e-9:
            unresolved += 1
    return conditioned, np.maximum(conditioned - incision_m, 0.0), unresolved


def _normalized_downstream_steepening_ratio(
    flat_floor_m: NDArray[np.float64],
    flat_accumulation_km2: NDArray[np.float64],
    donor: int,
    middle: int,
    downstream: int,
    *,
    width: int,
    x_spacing_km: float,
    y_spacing_km: float,
    reference_concavity: float,
) -> tuple[float, float, float]:
    donor_row, donor_column = divmod(donor, width)
    middle_row, middle_column = divmod(middle, width)
    downstream_row, downstream_column = divmod(downstream, width)
    upstream_distance_km = hypot(
        (donor_column - middle_column) * x_spacing_km,
        (donor_row - middle_row) * y_spacing_km,
    )
    downstream_distance_km = hypot(
        (middle_column - downstream_column) * x_spacing_km,
        (middle_row - downstream_row) * y_spacing_km,
    )
    minimum_slope = np.finfo(np.float64).eps
    upstream_slope = max(
        (flat_floor_m[donor] - flat_floor_m[middle])
        / (1_000.0 * upstream_distance_km),
        minimum_slope,
    )
    downstream_slope = max(
        (flat_floor_m[middle] - flat_floor_m[downstream])
        / (1_000.0 * downstream_distance_km),
        minimum_slope,
    )
    upstream_steepness = upstream_slope * (
        flat_accumulation_km2[donor] ** reference_concavity
    )
    downstream_steepness = downstream_slope * (
        flat_accumulation_km2[middle] ** reference_concavity
    )
    return (
        downstream_steepness / upstream_steepness,
        upstream_distance_km,
        downstream_distance_km,
    )


def condition_downstream_channel_steepness(
    source_elevation_m: NDArray[np.float64],
    incision_m: NDArray[np.float64],
    maximum_incision_m: NDArray[np.float64],
    channel_mask: NDArray[np.bool_],
    receivers: NDArray[np.int64],
    routing_surface_m: NDArray[np.float64],
    accumulation_km2: NDArray[np.float64],
    *,
    x_spacing_km: float,
    y_spacing_km: float,
    reference_concavity: float = 0.45,
    maximum_steepening_ratio: float = 8.0,
    maximum_passes: int = 16,
) -> tuple[NDArray[np.float64], NDArray[np.float64], int, float]:
    """Limit only extreme generated-channel steepening toward the outlet."""

    shape = source_elevation_m.shape
    if any(
        values.shape != shape
        for values in (
            incision_m,
            maximum_incision_m,
            channel_mask,
            receivers,
            routing_surface_m,
            accumulation_km2,
        )
    ):
        raise ValueError("Channel-steepness conditioning arrays must share a shape.")
    if x_spacing_km <= 0.0 or y_spacing_km <= 0.0:
        raise ValueError("Grid spacing must be positive.")
    if not 0.0 < reference_concavity < 1.0:
        raise ValueError("Reference concavity must be between zero and one.")
    if maximum_steepening_ratio <= 1.0 or maximum_passes < 1:
        raise ValueError("Steepening ratio and pass count must exceed one and zero.")
    if any(
        np.any(channel_mask & ~np.isfinite(values))
        for values in (
            source_elevation_m,
            incision_m,
            maximum_incision_m,
            routing_surface_m,
        )
    ):
        raise ValueError("Selected-channel profile values must be finite.")
    if np.any(
        channel_mask
        & (
            (incision_m < 0.0)
            | (maximum_incision_m + 1e-12 < incision_m)
        )
    ):
        raise ValueError("Selected-channel incision must be nonnegative and within its cap.")
    if np.any(
        channel_mask
        & (
            ~np.isfinite(accumulation_km2)
            | (accumulation_km2 <= 0.0)
        )
    ):
        raise ValueError("Selected channels must have positive finite accumulation.")

    conditioned = np.minimum(incision_m, maximum_incision_m).copy()
    flat_source = source_elevation_m.ravel()
    flat_conditioned = conditioned.ravel()
    flat_maximum = maximum_incision_m.ravel()
    flat_channel = channel_mask.ravel()
    flat_receivers = receivers.ravel()
    flat_accumulation = accumulation_km2.ravel()
    flat_floor = flat_source - flat_conditioned
    channel_indices = np.flatnonzero(flat_channel)
    upstream_first = channel_indices[
        np.argsort(-routing_surface_m.ravel()[channel_indices], kind="stable")
    ]
    width = shape[1]

    for _ in range(maximum_passes):
        changed = False
        for donor_value in upstream_first:
            donor = int(donor_value)
            middle = int(flat_receivers[donor])
            if middle < 0 or not flat_channel[middle]:
                continue
            downstream = int(flat_receivers[middle])
            if downstream < 0 or not flat_channel[downstream]:
                continue
            ratio, upstream_distance_km, downstream_distance_km = (
                _normalized_downstream_steepening_ratio(
                    flat_floor,
                    flat_accumulation,
                    donor,
                    middle,
                    downstream,
                    width=width,
                    x_spacing_km=x_spacing_km,
                    y_spacing_km=y_spacing_km,
                    reference_concavity=reference_concavity,
                )
            )
            if ratio <= maximum_steepening_ratio * (1.0 + 1e-12):
                continue
            slope_factor = maximum_steepening_ratio * (
                flat_accumulation[donor] / flat_accumulation[middle]
            ) ** reference_concavity
            maximum_middle_floor_m = (
                slope_factor * downstream_distance_km * flat_floor[donor]
                + upstream_distance_km * flat_floor[downstream]
            ) / (
                upstream_distance_km
                + slope_factor * downstream_distance_km
            )
            required_incision_m = flat_source[middle] - maximum_middle_floor_m
            revised_incision_m = min(
                flat_maximum[middle],
                max(flat_conditioned[middle], required_incision_m),
            )
            if revised_incision_m <= flat_conditioned[middle] + 1e-9:
                continue
            flat_conditioned[middle] = revised_incision_m
            flat_floor[middle] = flat_source[middle] - revised_incision_m
            changed = True
        if not changed:
            break

    unresolved = 0
    largest_ratio = 0.0
    for donor_value in channel_indices:
        donor = int(donor_value)
        middle = int(flat_receivers[donor])
        if middle < 0 or not flat_channel[middle]:
            continue
        downstream = int(flat_receivers[middle])
        if downstream < 0 or not flat_channel[downstream]:
            continue
        ratio, _upstream_distance_km, _downstream_distance_km = (
            _normalized_downstream_steepening_ratio(
                flat_floor,
                flat_accumulation,
                donor,
                middle,
                downstream,
                width=width,
                x_spacing_km=x_spacing_km,
                y_spacing_km=y_spacing_km,
                reference_concavity=reference_concavity,
            )
        )
        largest_ratio = max(largest_ratio, ratio)
        if ratio > maximum_steepening_ratio * (1.0 + 1e-6):
            unresolved += 1
    return (
        conditioned,
        np.maximum(conditioned - incision_m, 0.0),
        unresolved,
        largest_ratio,
    )


def drainage_incision(
    elevation_m: NDArray[np.float64],
    land_mask: NDArray[np.bool_],
    distance_to_coast_km: NDArray[np.float64],
    *,
    x_spacing_km: float,
    y_spacing_km: float,
    maximum_elevation_m: float,
    variability: float,
    residual_detail_m: NDArray[np.float64] | None = None,
) -> DrainageIncision:
    """Derive broad valley incision and contributing area from a terrain surface."""

    if residual_detail_m is not None:
        if residual_detail_m.shape != elevation_m.shape:
            raise ValueError("Residual detail must share the elevation grid shape.")
        if np.any(land_mask & ~np.isfinite(residual_detail_m)):
            raise ValueError("Land residual detail must be finite.")
    routing_surface = priority_flood_surface(elevation_m, land_mask)
    accumulation_km2, _mfd_slope = multiple_flow_accumulation(
        routing_surface,
        land_mask,
        x_spacing_km=x_spacing_km,
        y_spacing_km=y_spacing_km,
    )
    receivers, slope = steepest_flow_receivers(
        routing_surface,
        land_mask,
        x_spacing_km=x_spacing_km,
        y_spacing_km=y_spacing_km,
    )
    cell_area_km2 = x_spacing_km * y_spacing_km
    tree_accumulation_km2 = _accumulate_steepest_receivers(
        routing_surface,
        land_mask,
        receivers,
        cell_area_km2=cell_area_km2,
    )
    land_area_km2 = float(np.count_nonzero(land_mask)) * cell_area_km2
    channel_threshold_km2 = max(12.0 * cell_area_km2, 0.0015 * land_area_km2)
    minimum_source_area_km2 = max(4.0 * cell_area_km2, 0.00025 * land_area_km2)
    initiation_slope = _masked_smooth(slope, land_mask, iterations=1)
    initiation_sample = (
        land_mask
        & (tree_accumulation_km2 >= minimum_source_area_km2)
        & (initiation_slope > 0.0)
    )
    initiation_reference_slope = (
        max(float(np.percentile(initiation_slope[initiation_sample], 65.0)), 0.001)
        if np.any(initiation_sample)
        else 0.001
    )
    local_threshold_km2 = channel_threshold_km2 * np.clip(
        np.square(
            initiation_reference_slope
            / np.maximum(initiation_slope, np.finfo(np.float64).eps)
        ),
        0.35,
        4.0,
    )
    initiation_index = tree_accumulation_km2 / local_threshold_km2
    initiation_mask = initiation_sample & (initiation_index >= 1.0)
    channel, channel_heads = _connected_channel_network(
        initiation_mask,
        receivers,
        land_mask,
    )
    stream_order = strahler_stream_order(channel, receivers, routing_surface)
    largest_area_km2 = max(
        float(np.max(tree_accumulation_km2, initial=channel_threshold_km2)),
        channel_threshold_km2 * 1.01,
    )
    established_progress = np.clip(
        np.log(
            np.maximum(tree_accumulation_km2, channel_threshold_km2)
            / channel_threshold_km2
        )
        / np.log(largest_area_km2 / channel_threshold_km2),
        0.0,
        1.0,
    )
    headwater_progress = 0.08 * np.clip(
        np.log(
            np.maximum(tree_accumulation_km2, minimum_source_area_km2)
            / minimum_source_area_km2
        )
        / np.log(channel_threshold_km2 / minimum_source_area_km2),
        0.0,
        1.0,
    )
    log_progress = np.maximum(established_progress, headwater_progress)
    channel_slopes = slope[channel]
    reference_slope = (
        max(float(np.percentile(channel_slopes, 90.0)), 0.001)
        if channel_slopes.size
        else 0.001
    )
    slope_factor = np.sqrt(np.clip(slope / reference_slope, 0.0, 1.0))
    stream_power_shape = np.where(
        channel,
        log_progress * (0.45 + 0.55 * slope_factor),
        0.0,
    )
    largest_mfd_area_km2 = max(
        float(np.max(accumulation_km2, initial=channel_threshold_km2)),
        channel_threshold_km2 * 1.01,
    )
    mfd_progress = np.clip(
        np.log(
            np.maximum(accumulation_km2, channel_threshold_km2)
            / channel_threshold_km2
        )
        / np.log(largest_mfd_area_km2 / channel_threshold_km2),
        0.0,
        1.0,
    )
    convergence_shape = np.power(mfd_progress, 2.5) * (
        0.45
        + 0.55 * np.sqrt(np.clip(_mfd_slope / reference_slope, 0.0, 1.0))
    )
    near_shoulders = _masked_smooth(stream_power_shape, land_mask, iterations=2)
    trunk_source = stream_power_shape * np.power(log_progress, 1.4)
    trunk_shoulders = _masked_smooth(trunk_source, land_mask, iterations=7)
    valley_shape = np.clip(
        0.56 * stream_power_shape
        + 0.30 * near_shoulders
        + 0.28 * trunk_shoulders
        + 0.04 * convergence_shape,
        0.0,
        1.0,
    )
    maximum_depth_m = maximum_elevation_m * (0.035 + 0.085 * variability)
    incision_m = maximum_depth_m * valley_shape
    coastal_gate = np.clip(
        distance_to_coast_km / max(2.0 * max(x_spacing_km, y_spacing_km), 1e-9),
        0.0,
        1.0,
    )
    incision_m *= coastal_gate
    incision_m = np.minimum(incision_m, 0.55 * np.maximum(elevation_m, 0.0))
    floor_control = np.where(channel, 0.35 + 0.60 * log_progress, 0.0)
    floor_shoulders = _masked_smooth(floor_control, land_mask, iterations=2)
    detail_suppression = np.clip(
        0.68 * floor_control
        + 0.22 * floor_shoulders
        + 0.22 * trunk_shoulders,
        0.0,
        0.92,
    )
    detail_suppression *= coastal_gate
    retained_detail_m = (
        np.zeros_like(elevation_m)
        if residual_detail_m is None
        else residual_detail_m * (1.0 - detail_suppression)
    )
    source_elevation_m = elevation_m + retained_detail_m
    maximum_incision_m = np.maximum(
        incision_m,
        np.minimum(
            0.60 * np.maximum(source_elevation_m, 0.0),
            incision_m + 0.02 * maximum_elevation_m,
        ),
    )
    incision_m, floor_correction_m, unresolved_uphill_edges = (
        _condition_downstream_channel_floors(
            source_elevation_m,
            incision_m,
            maximum_incision_m,
            channel,
            receivers,
            routing_surface,
        )
    )
    (
        incision_m,
        steepness_correction_m,
        unresolved_steepening_edges,
        maximum_downstream_steepening_ratio,
    ) = condition_downstream_channel_steepness(
        source_elevation_m,
        incision_m,
        maximum_incision_m,
        channel,
        receivers,
        routing_surface,
        tree_accumulation_km2,
        x_spacing_km=x_spacing_km,
        y_spacing_km=y_spacing_km,
    )
    floor_correction_m += steepness_correction_m
    return DrainageIncision(
        incision_m=np.where(land_mask, incision_m, 0.0),
        accumulation_km2=accumulation_km2,
        detail_suppression=np.where(land_mask, detail_suppression, 0.0),
        channel_mask=channel,
        channel_head_mask=channel_heads,
        stream_order=stream_order,
        floor_correction_m=np.where(land_mask, floor_correction_m, 0.0),
        steepness_correction_m=np.where(land_mask, steepness_correction_m, 0.0),
        unresolved_uphill_channel_edge_count=unresolved_uphill_edges,
        unresolved_steepening_edge_count=unresolved_steepening_edges,
        maximum_downstream_steepening_ratio=maximum_downstream_steepening_ratio,
    )
