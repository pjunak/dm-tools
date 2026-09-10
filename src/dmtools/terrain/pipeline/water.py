"""Authored retention footprints, water products and explicit terrain conflicts."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from shapely import intersects_xy
from shapely.geometry import MultiPolygon, Point, Polygon

from dmtools.terrain.domain import ElevationPoint, TerrainBasin, TerrainConstraint
from dmtools.terrain.pipeline.basins import connected_components
from dmtools.terrain.pipeline.hydrology import D8_NEIGHBOURS, DrainageIncision
from dmtools.terrain.pipeline.outlets import OutletRouteReview

WATER_ALGORITHM_ID = "authored-basin-water-review@2"


@dataclass(frozen=True, slots=True)
class MetricBasin:
    source: TerrainBasin
    geometry: Polygon
    outlet_km: tuple[float, float] | None


def prepare_basins(
    constraints: tuple[TerrainConstraint, ...], width_km: float, height_km: float,
    land: Polygon | MultiPolygon, maximum_elevation_m: float,
) -> tuple[MetricBasin, ...]:
    """Reject ambiguous footprints before either cutting or water evaluation."""
    sources = [item for item in constraints if isinstance(item, TerrainBasin)]
    sources.sort(key=lambda item: (item.kind, item.water_level_m or 0.,
                                  item.outlet or (-1., -1.), item.points))
    basins: list[MetricBasin] = []
    for source in sources:
        geometry = Polygon([(x * width_km, y * height_km) for x, y in source.points])
        if not geometry.is_valid or geometry.area <= 0:
            raise ValueError("Basin footprints must be simple polygons with positive area.")
        if not land.covers(geometry):
            raise ValueError("Basin footprints must lie on land and exclude SVG water holes.")
        if any(geometry.intersects(other.geometry) for other in basins):
            raise ValueError("Basin footprints must not overlap or touch each other.")
        if source.water_level_m is not None and source.water_level_m > maximum_elevation_m:
            raise ValueError("Lake water level exceeds the elevation ceiling.")
        outlet = None
        if source.outlet is not None:
            outlet = source.outlet[0] * width_km, source.outlet[1] * height_km
            if geometry.boundary.distance(Point(outlet)) > 1e-9 * max(width_km, height_km):
                raise ValueError("The authored lake outlet must lie on its footprint boundary.")
        basins.append(MetricBasin(source, geometry, outlet))
    return tuple(basins)


def basin_intent_ids(
    x_km: NDArray[np.float64], y_km: NDArray[np.float64], basins: tuple[MetricBasin, ...],
) -> NDArray[np.uint32]:
    labels = np.zeros(x_km.shape, dtype=np.uint32)
    for basin_id, basin in enumerate(basins, start=1):
        inside = np.asarray(intersects_xy(basin.geometry, x_km, y_km), dtype=np.bool_)
        labels[inside] = basin_id
    return labels


@dataclass(frozen=True, slots=True)
class BasinIntentReview:
    intent_id: int
    source: TerrainBasin
    footprint_cell_count: int
    wet_cell_count: int
    dry_cell_count: int
    wet_component_count: int
    low_boundary_cell_count: int
    planned_exit_edge_count: int
    exposed_height_anchor_count: int
    outlet_elevation_m: float | None
    retained_contributing_area_km2: float
    outlet_route: OutletRouteReview | None
    issues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WaterReview:
    algorithm_id: str
    grid_width: int
    grid_height: int
    elevation_tolerance_m: float
    basins: tuple[BasinIntentReview, ...]


@dataclass(frozen=True, slots=True)
class WaterProducts:
    surface_m: NDArray[np.float32]
    intent_ids: NDArray[np.uint32]
    routing_intent_ids: NDArray[np.uint32]
    review: WaterReview


def review_water(
    basins: tuple[MetricBasin, ...], intent_ids: NDArray[np.uint32],
    elevation_m: NDArray[np.float64], routing: DrainageIncision,
    constraints: tuple[TerrainConstraint, ...], outlet_elevations_m: tuple[float | None, ...],
    outlet_routes: tuple[OutletRouteReview | None, ...],
) -> WaterReview:
    """Report sampled shoreline and planned-flow conflicts without inventing repairs."""
    records: list[BasinIntentReview] = []
    tolerance = .01
    height, width = elevation_m.shape
    for basin_id, (basin, outlet_elevation, outlet_route) in enumerate(
        zip(basins, outlet_elevations_m, outlet_routes, strict=True), start=1,
    ):
        source = basin.source
        inside = intent_ids == basin_id
        count = int(np.count_nonzero(inside))
        edges = inside & routing.channel_mask & (routing.receivers >= 0)
        exit_count = int(np.count_nonzero(intent_ids.ravel()[routing.receivers[edges]] != basin_id))
        issues: list[str] = []
        if not count:
            issues.append("unresolved_footprint")
        wet_count = components = low_count = exposed = 0
        if source.kind == "lake":
            assert source.water_level_m is not None
            below = elevation_m < source.water_level_m - tolerance
            wet = inside & below
            wet_count = int(np.count_nonzero(wet))
            components = len(connected_components(wet))
            low_boundary = np.zeros_like(inside)
            for dr, dc in D8_NEIGHBOURS:
                rows = slice(max(0, -dr), min(height, height - dr))
                columns = slice(max(0, -dc), min(width, width - dc))
                outside = ~inside[max(0, dr):min(height, height + dr),
                                  max(0, dc):min(width, width + dc)]
                low = below[max(0, dr):min(height, height + dr),
                            max(0, dc):min(width, width + dc)]
                low_boundary[rows, columns] |= wet[rows, columns] & outside & low
            low_boundary[[0, -1], :] |= wet[[0, -1], :]
            low_boundary[:, [0, -1]] |= wet[:, [0, -1]]
            low_count = int(np.count_nonzero(low_boundary))
            normalized = Polygon(source.points)
            exposed = sum(isinstance(item, ElevationPoint) and item.elevation_mode == "absolute"
                          and item.elevation_m >= source.water_level_m - tolerance
                          and normalized.covers(Point(item.position)) for item in constraints)
            if not wet_count:
                issues.append("no_water_at_level")
            if components > 1:
                issues.append("disconnected_water")
            if low_count:
                issues.append("low_boundary")
            if exposed:
                issues.append("exposed_height_anchor")
            if outlet_elevation is not None and outlet_elevation > source.water_level_m + tolerance:
                issues.append("outlet_above_water")
            if source.outlet is not None:
                issues.append("outlet_connection_pending")
        if exit_count:
            issues.append("unexpected_planned_basin_exit")
        records.append(BasinIntentReview(
            basin_id, source, count, wet_count, count - wet_count, components,
            low_count, exit_count, exposed, outlet_elevation,
            float(np.sum(routing.accumulation_km2[inside & routing.retention_terminal_mask])),
            outlet_route, tuple(issues),
        ))
    return WaterReview(WATER_ALGORITHM_ID, width, height, tolerance, tuple(records))


def water_products(
    elevation_m: NDArray[np.float32], x_km: NDArray[np.float64], y_km: NDArray[np.float64],
    basins: tuple[MetricBasin, ...], routing_ids: NDArray[np.uint32], review: WaterReview,
) -> WaterProducts:
    """Keep water level separate from bathymetry; evaluate footprints in bounded chunks."""
    surface = np.full(elevation_m.shape, np.nan, dtype=np.float32)
    labels = np.zeros(elevation_m.shape, dtype=np.uint32)
    if basins:
        for start in range(0, y_km.size, 128):
            rows = slice(start, start + 128)
            x, y = np.meshgrid(x_km, y_km[rows])
            chunk = basin_intent_ids(x, y, basins)
            labels[rows] = chunk
            for basin_id, basin in enumerate(basins, start=1):
                level = basin.source.water_level_m
                if level is not None:
                    wet = (chunk == basin_id) & (elevation_m[rows] < level - .01)
                    surface[rows][wet] = level
    return WaterProducts(surface, labels, routing_ids, review)
