"""Conservative transfer of captured contributing area through authored lake outlets."""

from dataclasses import dataclass, replace
from enum import IntEnum
from math import hypot

import numpy as np
from numpy.typing import NDArray
from shapely import covers, linestrings
from shapely.geometry import MultiPolygon, Polygon

from dmtools.terrain.domain import TerrainConstraint
from dmtools.terrain.pipeline.flat_routing import (
    FLAT_ROUTING_ALGORITHM_ID,
    FlatRouting,
    route_flats,
)
from dmtools.terrain.pipeline.hydrology import D8_NEIGHBOURS, DrainageIncision
from dmtools.terrain.pipeline.outlets import review_outlet_routes
from dmtools.terrain.pipeline.water import (
    MetricBasin,
    WaterReview,
    low_boundary_cells,
    review_water,
)
from dmtools.terrain.pipeline.water_sampling import GroundSampler, review_shorelines


class BasinCatchmentClass(IntEnum):
    """Canonical footprint-node outcome, not an upstream watershed delineation."""

    OUTSIDE = 0
    RETAINED = 1
    COLLECTED_WATER = 2
    COLLECTED_DRY = 3


@dataclass(frozen=True, slots=True)
class BasinOutflowSummary:
    algorithm_id: str
    flat_routing_algorithm_id: str
    connected_outlet_count: int
    source_area_km2: float
    retained_area_km2: float
    direct_boundary_area_km2: float
    outlet_boundary_area_km2: float
    area_balance_error_km2: float


@dataclass(frozen=True, slots=True)
class BasinOutflow:
    internal_receivers: NDArray[np.int64]
    flat_rank: NDArray[np.uint32]
    catchment_class: NDArray[np.uint8]
    retained_km2: NDArray[np.float64]
    source_km2: NDArray[np.float64]
    throughput_km2: NDArray[np.float64]
    terminal_km2: NDArray[np.float64]
    summary: BasinOutflowSummary


def basin_neighbours(
    basin: MetricBasin, inside: NDArray[np.bool_],
    x_km: NDArray[np.float64], y_km: NDArray[np.float64],
) -> tuple[NDArray[np.int64], NDArray[np.int64]]:
    """Build each undirected vector-contained link once, in bulk."""
    nodes = np.flatnonzero(inside).astype(np.int64)
    height, width = inside.shape
    rows, columns = nodes // width, nodes % width
    local = np.full(inside.size, -1, dtype=np.int64)
    local[nodes] = np.arange(nodes.size, dtype=np.int64)
    neighbours = np.full((nodes.size, 8), -1, dtype=np.int64)
    for direction, (dr, dc) in enumerate(D8_NEIGHBOURS):
        if dr < 0 or (dr == 0 and dc < 0):
            continue
        target_rows, target_columns = rows + dr, columns + dc
        valid = ((target_rows >= 0) & (target_rows < height)
                 & (target_columns >= 0) & (target_columns < width))
        sources = np.flatnonzero(valid)
        targets = local[target_rows[valid] * width + target_columns[valid]]
        present = targets >= 0
        sources, targets = sources[present], targets[present]
        if not sources.size:
            continue
        first = np.column_stack((x_km[columns[sources]], y_km[rows[sources]]))
        second = np.column_stack((x_km[columns[targets]], y_km[rows[targets]]))
        segments = linestrings(np.stack((first, second), axis=1))
        allowed = np.asarray(covers(basin.geometry, segments), dtype=np.bool_)
        sources, targets = sources[allowed], targets[allowed]
        neighbours[sources, direction] = targets
        neighbours[targets, 7 - direction] = sources
    return nodes, neighbours


@dataclass(frozen=True, slots=True)
class _BasinCollection:
    nodes: NDArray[np.int64]
    connected: NDArray[np.bool_]
    routing: FlatRouting


def _collect_basin(
    basin: MetricBasin, inside: NDArray[np.bool_], wet: NDArray[np.bool_], contact: int,
    elevation_m: NDArray[np.float64], x_km: NDArray[np.float64], y_km: NDArray[np.float64],
) -> _BasinCollection | None:
    nodes, neighbours = basin_neighbours(basin, inside, x_km, y_km)
    local_wet = wet.ravel()[nodes]
    connected = np.zeros(nodes.size, dtype=np.bool_)
    queue = [int(np.searchsorted(nodes, contact))]
    connected[queue[0]] = True
    while queue:
        node = queue.pop()
        for neighbour in neighbours[node]:
            target = int(neighbour)
            if target >= 0 and local_wet[target] and not connected[target]:
                connected[target] = True
                queue.append(target)
    if np.any(local_wet & ~connected):
        return None
    assert basin.source.water_level_m is not None
    head = np.where(local_wet, basin.source.water_level_m, elevation_m.ravel()[nodes])
    routing = route_flats(head, neighbours, local_wet,
        x_spacing_km=float(x_km[1] - x_km[0]), y_spacing_km=float(y_km[1] - y_km[0]))
    # Real drops sort by height; equal-head steps sort by their decreasing integer rank.
    order = np.lexsort((nodes, routing.flat_rank, head))
    for node in order:
        target = int(routing.receivers[node])
        if target >= 0:
            connected[node] = connected[target]
    return _BasinCollection(nodes, connected, routing)


def resolve_basin_outflow(
    basins: tuple[MetricBasin, ...], intent_ids: NDArray[np.uint32],
    elevation_m: NDArray[np.float64], routing: DrainageIncision, land_mask: NDArray[np.bool_],
    final_receivers: NDArray[np.int64], boundary_flags: NDArray[np.uint8],
    x_km: NDArray[np.float64], y_km: NDArray[np.float64], land: Polygon | MultiPolygon,
    constraints: tuple[TerrainConstraint, ...], outlet_heights: tuple[float | None, ...],
    sample_ground: GroundSampler,
) -> tuple[WaterReview, BasinOutflow]:
    """Review current ground, connect eligible outlets, and account for every source once.

    The original MFD graph captures incoming area at footprint nodes. This
    post-terrain layer transfers the eligible portion along reviewed D8 paths;
    it neither adds local rainfall again nor feeds unvalidated cuts into ground.
    Paths must avoid every basin, so no connection can feed its own source.
    """
    routes = review_outlet_routes(basins, intent_ids, elevation_m, land_mask,
                                  final_receivers, boundary_flags, x_km, y_km, land,
                                  outlet_heights, sample_ground)
    dx, dy = float(x_km[1] - x_km[0]), float(y_km[1] - y_km[0])
    shorelines = review_shorelines(basins, min(dx, dy) / 4, hypot(dx, dy), sample_ground)
    review = review_water(
        basins, intent_ids, elevation_m, routing, constraints, outlet_heights, routes, shorelines)
    catchment_class = np.where(intent_ids > 0, BasinCatchmentClass.RETAINED,
                                BasinCatchmentClass.OUTSIDE).astype(np.uint8)
    retained = np.where((intent_ids > 0) & routing.retention_terminal_mask,
                        routing.accumulation_km2, 0.)
    internal_receivers = np.full(elevation_m.shape, -1, dtype=np.int64)
    flat_rank = np.zeros(elevation_m.shape, dtype=np.uint32)
    source = np.zeros_like(elevation_m)
    throughput = np.zeros_like(elevation_m)
    terminal = np.zeros_like(elevation_m)
    records = list(review.basins)
    x, y = np.meshgrid(x_km, y_km)
    for index, (basin, record) in enumerate(zip(basins, records, strict=True)):
        route = record.outlet_route
        if basin.outlet_km is None:
            continue
        inside = intent_ids == record.intent_id
        assert basin.source.water_level_m is not None
        below = elevation_m < basin.source.water_level_m - review.elevation_tolerance_m
        wet = inside & below
        opening = np.hypot(x - basin.outlet_km[0], y - basin.outlet_km[1]) <= hypot(dx, dy)
        uncontrolled = int(np.count_nonzero(low_boundary_cells(inside, wet, below, opening)))
        issues = list(record.issues)
        if uncontrolled:
            issues.append("outlet_shoreline_uncontained")
        elif "low_boundary" in issues:
            issues.remove("low_boundary")
        records[index] = replace(record, uncontrolled_low_boundary_cell_count=uncontrolled,
                                  issues=tuple(issues))
        if (route is None or route.status != "sampled_clear" or uncontrolled
                or record.shoreline is None or record.shoreline.profile.status != "sampled"
                or record.shoreline.uncontrolled_low_sample_count
                or record.wet_component_count != 1 or not record.footprint_cell_count):
            continue
        assert route.water_contact_flat_index is not None
        assert route.terminal_flat_index is not None
        collection = _collect_basin(basin, inside, wet, route.water_contact_flat_index,
                                    elevation_m, x_km, y_km)
        if collection is None:
            records[index] = replace(records[index], issues=(*issues, "outlet_water_disconnected"))
            continue
        nodes, internal = collection.nodes, collection.routing
        has_receiver = internal.receivers >= 0
        internal_receivers.ravel()[nodes[has_receiver]] = nodes[internal.receivers[has_receiver]]
        flat_rank.ravel()[nodes] = internal.flat_rank
        connected = np.zeros_like(inside)
        connected.ravel()[nodes] = collection.connected
        captured = np.where(connected & routing.retention_terminal_mask,
                            routing.accumulation_km2, 0.)
        amount = float(np.sum(captured))
        remaining = max(0., record.captured_contributing_area_km2 - amount)
        source += captured
        retained[connected] = 0.
        catchment_class[connected & wet] = BasinCatchmentClass.COLLECTED_WATER
        catchment_class[connected & ~wet] = BasinCatchmentClass.COLLECTED_DRY
        throughput.ravel()[np.asarray(route.path_flat_indices, dtype=np.int64)] += amount
        terminal.ravel()[route.terminal_flat_index] += amount
        if remaining > 1e-8:
            issues.append("outlet_partial_catchment")
        records[index] = replace(records[index], outlet_connection="connected",
            retained_contributing_area_km2=remaining, outlet_contributing_area_km2=amount,
            flat_routed_cell_count=int(np.count_nonzero(internal.flat_rank)),
            collected_flat_cell_count=int(np.count_nonzero(
                (internal.flat_rank > 0) & collection.connected)),
            collected_wet_cell_count=int(np.count_nonzero(connected & wet)),
            collected_dry_cell_count=int(np.count_nonzero(connected & ~wet)),
            retained_cell_count=int(np.count_nonzero(inside & ~connected)),
            issues=tuple(issues))
    source_area = float(np.count_nonzero(land_mask)) * dx * dy
    retained_area = sum(record.retained_contributing_area_km2 for record in records)
    direct_area = float(np.sum(routing.accumulation_km2[routing.outlet_mask & (intent_ids == 0)]))
    delivered_area = float(np.sum(terminal))
    error = source_area - (retained_area + direct_area + delivered_area)
    if not np.isclose(error, 0., rtol=0., atol=max(1e-8, source_area * 1e-10)):
        raise RuntimeError("Basin outlet transfer did not conserve contributing area.")
    summary = BasinOutflowSummary("captured-mfd-reviewed-d8-outlets@4",
        FLAT_ROUTING_ALGORITHM_ID,
        sum(record.outlet_connection == "connected" for record in records),
        source_area, retained_area, direct_area, delivered_area, error)
    return (replace(review, basins=tuple(records)),
            BasinOutflow(internal_receivers, flat_rank, catchment_class, retained,
                         source, throughput, terminal, summary))
