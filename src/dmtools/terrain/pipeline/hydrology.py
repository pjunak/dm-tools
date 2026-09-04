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
    maximum_fill_depth_m: float
    depression_fill_volume_km3: float
    largest_outlet_catchment_km2: float


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

    cell_area_km2 = x_spacing_km * y_spacing_km
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

    return accumulation, receiver_slope


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

    potential_sinks = land_mask.ravel() & ~outlets.ravel() & (flat_receivers < 0)
    filled = priority_flood_surface(elevation_m, land_mask)
    fill_depth_m = np.where(land_mask, np.maximum(filled - elevation_m, 0.0), 0.0)
    significant_fill = fill_depth_m > fill_tolerance_m
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
        algorithm_id="canonical-d8-priority-flood-diagnostics@1",
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
        maximum_fill_depth_m=float(np.max(fill_depth_m, initial=0.0)),
        depression_fill_volume_km3=fill_volume_km3,
        largest_outlet_catchment_km2=float(
            np.max(conditioned_accumulation[outlets], initial=0.0)
        ),
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


def drainage_incision(
    elevation_m: NDArray[np.float64],
    land_mask: NDArray[np.bool_],
    distance_to_coast_km: NDArray[np.float64],
    *,
    x_spacing_km: float,
    y_spacing_km: float,
    maximum_elevation_m: float,
    variability: float,
) -> DrainageIncision:
    """Derive broad valley incision and contributing area from a terrain surface."""

    routing_surface = priority_flood_surface(elevation_m, land_mask)
    accumulation_km2, _mfd_slope = multiple_flow_accumulation(
        routing_surface,
        land_mask,
        x_spacing_km=x_spacing_km,
        y_spacing_km=y_spacing_km,
    )
    tree_accumulation_km2, slope = steepest_flow_accumulation(
        routing_surface,
        land_mask,
        x_spacing_km=x_spacing_km,
        y_spacing_km=y_spacing_km,
    )
    cell_area_km2 = x_spacing_km * y_spacing_km
    land_area_km2 = float(np.count_nonzero(land_mask)) * cell_area_km2
    channel_threshold_km2 = max(12.0 * cell_area_km2, 0.0015 * land_area_km2)
    largest_area_km2 = max(
        float(np.max(tree_accumulation_km2, initial=channel_threshold_km2)),
        channel_threshold_km2 * 1.01,
    )
    log_progress = np.clip(
        np.log(
            np.maximum(tree_accumulation_km2, channel_threshold_km2)
            / channel_threshold_km2
        )
        / np.log(largest_area_km2 / channel_threshold_km2),
        0.0,
        1.0,
    )
    channel = tree_accumulation_km2 >= channel_threshold_km2
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
    near_shoulders = _masked_smooth(stream_power_shape, land_mask, iterations=2)
    trunk_source = stream_power_shape * np.power(log_progress, 1.4)
    trunk_shoulders = _masked_smooth(trunk_source, land_mask, iterations=7)
    valley_shape = np.clip(
        0.56 * stream_power_shape
        + 0.30 * near_shoulders
        + 0.28 * trunk_shoulders,
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
    return DrainageIncision(
        incision_m=np.where(land_mask, incision_m, 0.0),
        accumulation_km2=accumulation_km2,
        detail_suppression=np.where(land_mask, detail_suppression, 0.0),
    )
