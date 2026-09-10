"""Conservative transfer of captured contributing area through authored lake outlets."""

from dataclasses import dataclass, replace
from math import hypot

import numpy as np
from numpy.typing import NDArray
from shapely.geometry import LineString, MultiPolygon, Polygon

from dmtools.terrain.domain import TerrainConstraint
from dmtools.terrain.pipeline.hydrology import (
    D8_NEIGHBOURS,
    DrainageIncision,
    steepest_flow_receivers,
)
from dmtools.terrain.pipeline.outlets import review_outlet_routes
from dmtools.terrain.pipeline.water import (
    MetricBasin,
    WaterReview,
    low_boundary_cells,
    review_water,
)


@dataclass(frozen=True, slots=True)
class BasinOutflowSummary:
    algorithm_id: str
    connected_outlet_count: int
    source_area_km2: float
    retained_area_km2: float
    direct_boundary_area_km2: float
    outlet_boundary_area_km2: float
    area_balance_error_km2: float


@dataclass(frozen=True, slots=True)
class BasinOutflow:
    source_km2: NDArray[np.float64]
    throughput_km2: NDArray[np.float64]
    terminal_km2: NDArray[np.float64]
    summary: BasinOutflowSummary


def _reaches_lake(
    basin: MetricBasin, inside: NDArray[np.bool_], wet: NDArray[np.bool_], contact: int,
    elevation_m: NDArray[np.float64], x_km: NDArray[np.float64], y_km: NDArray[np.float64],
) -> NDArray[np.bool_]:
    """Collect connected water, then only dry nodes that actually descend into it."""
    height, width = inside.shape
    reachable = np.zeros_like(inside)

    def covered(first: int, second: int) -> bool:
        r1, c1 = divmod(first, width)
        r2, c2 = divmod(second, width)
        return bool(basin.geometry.covers(LineString(((x_km[c1], y_km[r1]),
                                                      (x_km[c2], y_km[r2])))))

    queue = [contact]
    reachable.ravel()[contact] = True
    while queue:
        node = queue.pop()
        row, col = divmod(node, width)
        for dr, dc in D8_NEIGHBOURS:
            r, c = row + dr, col + dc
            if (0 <= r < height and 0 <= c < width and wet[r, c] and not reachable[r, c]
                    and covered(node, r * width + c)):
                reachable[r, c] = True
                queue.append(r * width + c)
    if np.any(wet & ~reachable):
        return reachable
    # Dry ground drains toward the water surface, never toward submerged bed depths.
    assert basin.source.water_level_m is not None
    head = np.where(wet, basin.source.water_level_m, elevation_m)
    receivers, _ = steepest_flow_receivers(
        head, inside, x_spacing_km=float(x_km[1] - x_km[0]),
        y_spacing_km=float(y_km[1] - y_km[0]), terminal_mask=wet,
    )
    dry = np.flatnonzero(inside & ~wet)
    for node in dry[np.argsort(elevation_m.ravel()[dry], kind="stable")]:
        target = int(receivers.ravel()[node])
        if target >= 0 and reachable.ravel()[target] and covered(int(node), target):
            reachable.ravel()[node] = True
    return reachable


def resolve_basin_outflow(
    basins: tuple[MetricBasin, ...], intent_ids: NDArray[np.uint32],
    elevation_m: NDArray[np.float64], routing: DrainageIncision, land_mask: NDArray[np.bool_],
    final_receivers: NDArray[np.int64], boundary_flags: NDArray[np.uint8],
    x_km: NDArray[np.float64], y_km: NDArray[np.float64], land: Polygon | MultiPolygon,
    constraints: tuple[TerrainConstraint, ...], outlet_heights: tuple[float | None, ...],
) -> tuple[WaterReview, BasinOutflow]:
    """Review current ground, connect eligible outlets, and account for every source once.

    The original MFD graph captures incoming area at footprint nodes. This
    post-terrain layer transfers the eligible portion along reviewed D8 paths;
    it neither adds local rainfall again nor feeds unvalidated cuts into ground.
    Paths must avoid every basin, so no connection can feed its own source.
    """
    routes = review_outlet_routes(basins, intent_ids, elevation_m, land_mask,
                                  final_receivers, boundary_flags, x_km, y_km, land, outlet_heights)
    review = review_water(
        basins, intent_ids, elevation_m, routing, constraints, outlet_heights, routes)
    source = np.zeros_like(elevation_m)
    throughput = np.zeros_like(elevation_m)
    terminal = np.zeros_like(elevation_m)
    records = list(review.basins)
    x, y = np.meshgrid(x_km, y_km)
    dx, dy = float(x_km[1] - x_km[0]), float(y_km[1] - y_km[0])
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
                or record.wet_component_count != 1 or not record.footprint_cell_count):
            continue
        assert route.water_contact_flat_index is not None
        assert route.terminal_flat_index is not None
        connected = _reaches_lake(basin, inside, wet, route.water_contact_flat_index,
                                  elevation_m, x_km, y_km)
        if np.any(wet & ~connected):
            records[index] = replace(records[index], issues=(*issues, "outlet_water_disconnected"))
            continue
        captured = np.where(connected & routing.retention_terminal_mask,
                            routing.accumulation_km2, 0.)
        amount = float(np.sum(captured))
        remaining = max(0., record.captured_contributing_area_km2 - amount)
        source += captured
        throughput.ravel()[np.asarray(route.path_flat_indices, dtype=np.int64)] += amount
        terminal.ravel()[route.terminal_flat_index] += amount
        if remaining > 1e-8:
            issues.append("outlet_partial_catchment")
        records[index] = replace(records[index], outlet_connection="connected",
            retained_contributing_area_km2=remaining, outlet_contributing_area_km2=amount,
            issues=tuple(issues))
    source_area = float(np.count_nonzero(land_mask)) * dx * dy
    retained_area = sum(record.retained_contributing_area_km2 for record in records)
    direct_area = float(np.sum(routing.accumulation_km2[routing.outlet_mask & (intent_ids == 0)]))
    delivered_area = float(np.sum(terminal))
    error = source_area - (retained_area + direct_area + delivered_area)
    if not np.isclose(error, 0., rtol=0., atol=max(1e-8, source_area * 1e-10)):
        raise RuntimeError("Basin outlet transfer did not conserve contributing area.")
    summary = BasinOutflowSummary("captured-mfd-reviewed-d8-outlets@1",
        sum(record.outlet_connection == "connected" for record in records),
        source_area, retained_area, direct_area, delivered_area, error)
    return (replace(review, basins=tuple(records)),
            BasinOutflow(source, throughput, terminal, summary))
