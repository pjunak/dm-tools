"""Read-only basin and planned-channel diagnostics, separate from terrain shaping."""

from dataclasses import dataclass
from math import isfinite

import numpy as np
from numpy.typing import NDArray

from dmtools.terrain.pipeline.hydrology import (
    D8_NEIGHBOURS,
    DrainageIncision,
    land_outlet_mask,
    priority_flood_surface,
    steepest_flow_accumulation,
    steepest_flow_receivers,
)


@dataclass(frozen=True, slots=True)
class RoutingAgreement:
    """Planned D8 channels checked against the finished field on the same grid."""

    algorithm_id: str
    elevation_tolerance_m: float
    channel_edge_count: int
    changed_channel_receiver_count: int
    uphill_channel_edge_count: int
    maximum_channel_rise_m: float



def channel_edge_rise(
    drainage: DrainageIncision,
    final_elevation_m: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Positive rise along each planned channel edge; zero at terminals and sea."""
    edges = drainage.channel_mask & (drainage.receivers >= 0)
    rise = np.zeros_like(final_elevation_m)
    rise[edges] = np.maximum(
        final_elevation_m.ravel()[drainage.receivers[edges]] - final_elevation_m[edges], 0.0,
    )
    return rise



# Donor-node bit flags; contexts overlap and do not assign a physical cause.
UPHILL = 1
DEPRESSION = 2
CUT_LIMIT = 4
FINAL_ADJUSTMENT = 8
REGION_TRANSITION = 16


@dataclass(frozen=True, slots=True)
class ChannelConflictSummary:
    algorithm_id: str
    elevation_tolerance_m: float
    depression_tolerance_m: float
    uphill_edge_count: int
    depression_edge_count: int
    insufficient_cut_edge_count: int
    final_adjustment_edge_count: int
    region_transition_edge_count: int
    unclassified_edge_count: int
    maximum_cut_deficit_m: float


@dataclass(frozen=True, slots=True)
class ChannelConflicts:
    summary: ChannelConflictSummary
    flags: NDArray[np.uint8]
    rise_m: NDArray[np.float64]
    receiver_cut_deficit_m: NDArray[np.float64]
    final_adjustment_rise_m: NDArray[np.float64]
    final_fill_depth_m: NDArray[np.float64]


def review_drainage_routing(
    drainage: DrainageIncision,
    final_elevation_m: NDArray[np.float64],
    land_mask: NDArray[np.bool_],
    *,
    x_spacing_km: float,
    y_spacing_km: float,
    region_transition_mask: NDArray[np.bool_] | None = None,
) -> tuple[RoutingAgreement, ChannelConflicts]:
    """Inspect finished channels without modifying the DEM or planned receivers.

    Remaining automatic cut is an optimistic local allowance: an authored
    constraint can prevent using it. Deficits are edge-local, not breach depths
    for an entire route. Flags describe evidence and may overlap.
    """
    shape = final_elevation_m.shape
    arrays = (drainage.source_elevation_m, drainage.incision_m, drainage.incision_limit_m)
    if (final_elevation_m.ndim != 2 or land_mask.shape != shape
            or drainage.receivers.shape != shape or drainage.channel_mask.shape != shape
            or any(array.shape != shape for array in arrays)):
        raise ValueError("Routing review requires equally shaped 2D arrays.")
    if any(not isfinite(value) or value <= 0 for value in (x_spacing_km, y_spacing_km)):
        raise ValueError("Routing review spacing must be positive and finite.")
    if any(np.any(land_mask & ~np.isfinite(array)) for array in (final_elevation_m, *arrays)):
        raise ValueError("Routing review land values must be finite.")
    if np.any(land_mask & ((drainage.incision_m < 0)
                         | (drainage.incision_limit_m < drainage.incision_m))):
        raise ValueError("Routing incision must be non-negative and within its limit.")
    receivers = drainage.receivers
    if np.any((receivers < -1) | (receivers >= final_elevation_m.size)):
        raise ValueError("Routing receivers must be valid flat indices or -1.")
    routed = land_mask & (receivers >= 0)
    if np.any(~land_mask.ravel()[receivers[routed]]):
        raise ValueError("Routing receivers must point to land.")
    if region_transition_mask is None:
        region_transition_mask = np.zeros(shape, dtype=np.bool_)
    elif region_transition_mask.shape != shape:
        raise ValueError("Regional transitions must share the routing grid shape.")
    final_routing = priority_flood_surface(final_elevation_m, land_mask)
    final_receivers, _slope = steepest_flow_receivers(
        final_routing, land_mask, x_spacing_km=x_spacing_km, y_spacing_km=y_spacing_km,
    )
    edges = drainage.channel_mask & routed
    rise = channel_edge_rise(drainage, final_elevation_m)
    rise = np.where(edges, rise, 0.0)
    tolerance_m, depression_tolerance_m = 0.001, 0.01
    uphill = rise > tolerance_m
    targets = receivers[uphill]
    fill_depth = np.where(land_mask, np.maximum(final_routing - final_elevation_m, 0), 0.0)
    depression = fill_depth > depression_tolerance_m
    flags = np.zeros(shape, dtype=np.uint8)
    flags[uphill] = UPHILL
    flags[uphill] |= np.where(depression[uphill] | depression.ravel()[targets],
                             DEPRESSION, 0).astype(np.uint8)
    remaining = np.maximum(drainage.incision_limit_m - drainage.incision_m, 0)
    deficit = np.zeros(shape, dtype=np.float64)
    deficit[uphill] = np.maximum(rise[uphill] - remaining.ravel()[targets], 0)
    flags[deficit > tolerance_m] |= CUT_LIMIT
    macro_floor = drainage.source_elevation_m - drainage.incision_m
    macro_edge_delta = macro_floor.ravel()[targets] - macro_floor[uphill]
    adjustment = np.zeros(shape, dtype=np.float64)
    adjustment[uphill] = np.maximum(rise[uphill] - macro_edge_delta, 0)
    flags[adjustment > tolerance_m] |= FINAL_ADJUSTMENT
    flags[uphill] |= np.where(
        region_transition_mask[uphill] | region_transition_mask.ravel()[targets],
        REGION_TRANSITION, 0,
    ).astype(np.uint8)
    count = int(np.count_nonzero(uphill))
    agreement = RoutingAgreement(
        algorithm_id="planned-final-d8-agreement@2",
        elevation_tolerance_m=tolerance_m,
        channel_edge_count=int(np.count_nonzero(edges)),
        changed_channel_receiver_count=int(np.count_nonzero(
            edges & (receivers != final_receivers),
        )),
        uphill_channel_edge_count=count,
        maximum_channel_rise_m=float(np.max(rise, initial=0.0)),
    )
    summary = ChannelConflictSummary(
        algorithm_id="planned-channel-context@1",
        elevation_tolerance_m=tolerance_m,
        depression_tolerance_m=depression_tolerance_m,
        uphill_edge_count=count,
        depression_edge_count=int(np.count_nonzero(flags & DEPRESSION)),
        insufficient_cut_edge_count=int(np.count_nonzero(flags & CUT_LIMIT)),
        final_adjustment_edge_count=int(np.count_nonzero(flags & FINAL_ADJUSTMENT)),
        region_transition_edge_count=int(np.count_nonzero(flags & REGION_TRANSITION)),
        unclassified_edge_count=int(np.count_nonzero(flags == UPHILL)),
        maximum_cut_deficit_m=float(np.max(deficit, initial=0.0)),
    )
    return agreement, ChannelConflicts(summary, flags, rise, deficit, adjustment, fill_depth)


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
            for row_offset, column_offset in D8_NEIGHBOURS:
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

    outlets = land_outlet_mask(land_mask)
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
        algorithm_id="canonical-d8-priority-flood-diagnostics@3",
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
