# pyright: reportUnknownMemberType=false
"""First deterministic coastline-conditioned terrain pipeline."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from itertools import pairwise
from typing import Any, cast

import numpy as np
import shapely
from numpy.typing import NDArray
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import unary_union

from dmtools.terrain.domain import (
    Coastline,
    ElevationMode,
    ElevationPoint,
    TerrainBrushStroke,
    TerrainConstraint,
    TerrainSettings,
)
from dmtools.terrain.pipeline.noise import fractal_value_noise
from dmtools.terrain.pipeline.profile import shape_preserving_profile

type ProgressCallback = Callable[[float, str], None]


@dataclass(frozen=True, slots=True)
class GeneratedTerrain:
    """Authoritative numeric result of one in-memory terrain generation."""

    elevation_m: NDArray[np.float32]
    land_mask: NDArray[np.bool_]
    x_km: NDArray[np.float64]
    y_km: NDArray[np.float64]
    settings: TerrainSettings
    constraints: tuple[TerrainConstraint, ...]
    source_name: str

    @property
    def width(self) -> int:
        return int(self.elevation_m.shape[1])

    @property
    def height(self) -> int:
        return int(self.elevation_m.shape[0])


def _report(callback: ProgressCallback | None, fraction: float, message: str) -> None:
    if callback is not None:
        callback(fraction, message)


type LandGeometry = Polygon | MultiPolygon


def _metric_polygon(
    coastline: Coastline, object_scale_km: float
) -> tuple[LandGeometry, float, float]:
    min_x, min_y, max_x, max_y = coastline.bounds
    span_x = max_x - min_x
    span_y = max_y - min_y
    longest_span = max(span_x, span_y)
    if longest_span <= 0:
        raise ValueError("The coastline has no measurable extent.")
    km_per_source_unit = object_scale_km / longest_span
    def metric_ring(
        ring: tuple[tuple[float, float], ...],
    ) -> list[tuple[float, float]]:
        return [
            ((x - min_x) * km_per_source_unit, (y - min_y) * km_per_source_unit)
            for x, y in ring
        ]

    polygons = [
        Polygon(
            metric_ring(component.exterior),
            holes=[metric_ring(hole) for hole in component.holes],
        )
        for component in coastline.components
    ]
    polygon = unary_union(polygons)
    if not isinstance(polygon, (Polygon, MultiPolygon)):
        raise ValueError("The coastlines do not form polygonal land geometry.")
    if not polygon.is_valid or polygon.area <= 0:
        raise ValueError("The coastline does not form a valid land polygon.")
    return polygon, span_x * km_per_source_unit, span_y * km_per_source_unit


@dataclass(frozen=True, slots=True)
class _MetricConstraint:
    kind: str
    geometry: Point | LineString
    elevation_m: float
    influence_radius_km: float
    elevation_mode: ElevationMode
    intensity: float = 1.0
    profile_anchors: tuple[tuple[float, float, float], ...] = ()
    attached_to_structure: bool = False


def _smooth_structure_points(
    points: list[tuple[float, float]], iterations: int = 3
) -> list[tuple[float, float]]:
    """Round authored polyline corners while preserving its two endpoints."""

    if len(points) <= 2:
        return points
    smoothed = points
    for _ in range(iterations):
        refined = [smoothed[0]]
        for first, second in pairwise(smoothed):
            refined.append(
                (
                    0.75 * first[0] + 0.25 * second[0],
                    0.75 * first[1] + 0.25 * second[1],
                )
            )
            refined.append(
                (
                    0.25 * first[0] + 0.75 * second[0],
                    0.25 * first[1] + 0.75 * second[1],
                )
            )
        refined.append(smoothed[-1])
        smoothed = refined
    return smoothed


def _metric_constraints(
    constraints: Sequence[TerrainConstraint],
    polygon: LandGeometry,
    width_km: float,
    height_km: float,
    maximum_elevation_m: float,
) -> tuple[_MetricConstraint, ...]:
    converted: list[_MetricConstraint] = []
    for constraint in constraints:
        if (
            constraint.elevation_mode == "absolute"
            and constraint.elevation_m > maximum_elevation_m
        ):
            raise ValueError(
                f"Authored elevation {constraint.elevation_m:,.0f} m exceeds the "
                f"{maximum_elevation_m:,.0f} m elevation ceiling."
            )
        if isinstance(constraint, ElevationPoint):
            x, y = constraint.position
            geometry: Point | LineString = Point(x * width_km, y * height_km)
            kind = "point"
            intensity = 1.0
        elif isinstance(constraint, TerrainBrushStroke):
            metric_points = [(x * width_km, y * height_km) for x, y in constraint.points]
            geometry = (
                Point(metric_points[0])
                if len(metric_points) == 1
                else LineString(metric_points)
            )
            kind = "brush"
            intensity = constraint.intensity
        else:
            metric_points = [(x * width_km, y * height_km) for x, y in constraint.points]
            geometry = LineString(_smooth_structure_points(metric_points))
            kind = constraint.kind
            intensity = 1.0
        if not polygon.covers(geometry):
            if kind == "point":
                label = "Elevation point"
            elif kind == "brush":
                label = "Terrain brush stroke"
            else:
                label = kind.capitalize()
            raise ValueError(f"{label} constraint extends outside the coastline.")
        converted.append(
            _MetricConstraint(
                kind=kind,
                geometry=geometry,
                elevation_m=constraint.elevation_m,
                influence_radius_km=constraint.influence_radius_km,
                elevation_mode=constraint.elevation_mode,
                intensity=intensity,
            )
        )
    structure_indices = [
        index
        for index, constraint in enumerate(converted)
        if constraint.kind in ("ridge", "valley")
    ]
    anchors: dict[int, list[tuple[float, float, float]]] = {
        index: [] for index in structure_indices
    }
    for point_index, point_constraint in enumerate(converted):
        if point_constraint.kind != "point":
            continue
        compatible: list[tuple[float, int]] = []
        for structure_index in structure_indices:
            structure = converted[structure_index]
            if structure.elevation_mode != point_constraint.elevation_mode:
                continue
            attachment_distance = max(
                point_constraint.influence_radius_km,
                structure.influence_radius_km,
            )
            distance = float(structure.geometry.distance(point_constraint.geometry))
            if distance > attachment_distance:
                continue
            compatible.append((distance, structure_index))

        if point_constraint.elevation_mode == "relative" and compatible:
            compatible.sort()
            if len(compatible) > 1 and abs(compatible[0][0] - compatible[1][0]) <= 1e-6:
                compatible = []
            else:
                compatible = compatible[:1]

        attached = False
        for _distance, structure_index in compatible:
            structure = converted[structure_index]
            project_line = cast(Any, structure.geometry)
            along_km = float(project_line.project(point_constraint.geometry))
            along_radius_km = max(
                2.0 * point_constraint.influence_radius_km,
                structure.influence_radius_km,
            )
            if point_constraint.elevation_mode == "absolute":
                profile_target_m = point_constraint.elevation_m
            elif structure.kind == "ridge":
                profile_target_m = structure.elevation_m + point_constraint.elevation_m
            else:
                profile_target_m = structure.elevation_m - point_constraint.elevation_m
            if profile_target_m < 0.0:
                raise ValueError(
                    f"Relative point would reverse the {structure.kind} at its profile anchor."
                )
            anchors[structure_index].append(
                (along_km, profile_target_m, along_radius_km)
            )
            attached = True
        if attached:
            converted[point_index] = replace(point_constraint, attached_to_structure=True)
    for structure_index, structure_anchors in anchors.items():
        if structure_anchors:
            converted[structure_index] = replace(
                converted[structure_index],
                profile_anchors=tuple(sorted(structure_anchors)),
            )
    return tuple(converted)


def _constraint_weight(
    distance_km: NDArray[np.float64],
    radius_km: float | NDArray[np.float64],
    largest_feature_km: float,
    *,
    is_structure: bool,
    is_brush: bool = False,
    attached_point: bool = False,
) -> NDArray[np.float64]:
    """Blend a defined landform core into a broader geological context."""

    if is_structure:
        context_radius_km = np.maximum(3.0 * radius_km, 0.8 * largest_feature_km)
        context_share = 0.32
    elif is_brush:
        context_radius_km = np.maximum(1.75 * radius_km, 0.3 * largest_feature_km)
        context_share = 0.18
    elif attached_point:
        context_radius_km = max(1.25 * float(radius_km), 0.15 * largest_feature_km)
        context_share = 0.04
    else:
        context_radius_km = max(2.0 * float(radius_km), 0.35 * largest_feature_km)
        context_share = 0.12
    core = np.exp(-np.log(2.0) * np.square(distance_km / radius_km))
    context = np.exp(-np.log(2.0) * np.square(distance_km / context_radius_km))
    return (1.0 - context_share) * core + context_share * context


def _coast_conditioned_weight(
    weight: NDArray[np.float64],
    distance_to_constraint_km: NDArray[np.float64],
    distance_to_coast_km: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Keep sea level hard while allowing an inland feature to reach its target."""

    denominator = distance_to_coast_km + distance_to_constraint_km
    coast_gate = np.divide(
        distance_to_coast_km,
        denominator,
        out=np.zeros_like(distance_to_coast_km),
        where=denominator > 0.0,
    )
    return weight * coast_gate


def _line_positions_km(
    line: LineString, sample_points: Any
) -> NDArray[np.float64]:
    raw_positions = cast(Any, shapely.line_locate_point(line, sample_points))
    return cast(NDArray[np.float64], np.asarray(raw_positions, dtype=np.float64))


def _structure_profile(
    constraint: _MetricConstraint,
    line_positions_km: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return a shape-preserving target and its authored longitudinal control."""

    target = np.full_like(line_positions_km, constraint.elevation_m)
    if not constraint.profile_anchors:
        return target, np.zeros_like(line_positions_km)

    coalesced: list[tuple[float, float, float]] = []
    for anchor in constraint.profile_anchors:
        if coalesced and abs(anchor[0] - coalesced[-1][0]) <= 1e-6:
            previous = coalesced[-1]
            if abs(anchor[1] - previous[1]) > 1e-6:
                raise ValueError(
                    "Conflicting height points project to the same structure position."
                )
            coalesced[-1] = (previous[0], previous[1], max(previous[2], anchor[2]))
        else:
            coalesced.append(anchor)

    line = cast(LineString, constraint.geometry)
    line_length = float(line.length)
    first_position, _first_elevation, first_radius = coalesced[0]
    last_position, _last_elevation, last_radius = coalesced[-1]
    first_shoulder = max(0.0, first_position - 2.0 * first_radius)
    last_shoulder = min(line_length, last_position + 2.0 * last_radius)
    knot_positions: list[float] = []
    knot_elevations: list[float] = []

    if first_position > 1e-6:
        knot_positions.append(0.0)
        knot_elevations.append(constraint.elevation_m)
        if first_shoulder > 1e-6:
            knot_positions.append(first_shoulder)
            knot_elevations.append(constraint.elevation_m)
    for along_km, elevation_m, _radius_km in coalesced:
        knot_positions.append(along_km)
        knot_elevations.append(elevation_m)
    if last_position < line_length - 1e-6:
        if last_shoulder < line_length - 1e-6:
            knot_positions.append(last_shoulder)
            knot_elevations.append(constraint.elevation_m)
        knot_positions.append(line_length)
        knot_elevations.append(constraint.elevation_m)

    target = shape_preserving_profile(
        np.asarray(knot_positions, dtype=np.float64),
        np.asarray(knot_elevations, dtype=np.float64),
        line_positions_km,
    )
    authored_control = np.ones_like(line_positions_km)
    if first_position > first_shoulder:
        left_progress = np.clip(
            (line_positions_km - first_shoulder) / (first_position - first_shoulder),
            0.0,
            1.0,
        )
        authored_control = left_progress * left_progress * (3.0 - 2.0 * left_progress)
    if last_position < last_shoulder:
        right_progress = np.clip(
            (last_shoulder - line_positions_km) / (last_shoulder - last_position),
            0.0,
            1.0,
        )
        right_control = right_progress * right_progress * (3.0 - 2.0 * right_progress)
        authored_control = np.minimum(authored_control, right_control)
    between_anchors = (line_positions_km >= first_position) & (
        line_positions_km <= last_position
    )
    authored_control = np.where(between_anchors, 1.0, authored_control)
    return target, np.clip(authored_control, 0.0, 1.0)


def _structure_response(
    constraint: _MetricConstraint,
    sample_points: Any,
    distance_to_coast_km: NDArray[np.float64],
    largest_feature_km: float,
    detail_driver: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return a tapered structure weight and distance along its centreline."""

    raw_distance = cast(Any, shapely.distance(sample_points, constraint.geometry))
    distance = cast(NDArray[np.float64], np.asarray(raw_distance, dtype=np.float64))
    line = cast(LineString, constraint.geometry)
    line_positions = _line_positions_km(line, sample_points)
    distance_to_end = np.minimum(line_positions, line.length - line_positions)
    taper_length = max(2.0 * constraint.influence_radius_km, 0.12 * line.length)
    taper_progress = np.clip(distance_to_end / taper_length, 0.0, 1.0)
    taper = taper_progress * taper_progress * (3.0 - 2.0 * taper_progress)
    width_variation = 0.82 + 0.36 * (0.5 + 0.5 * detail_driver)
    effective_radius = constraint.influence_radius_km * (0.35 + 0.65 * taper)
    effective_radius *= width_variation
    weight = _constraint_weight(
        distance,
        effective_radius,
        largest_feature_km,
        is_structure=True,
    )
    return (
        _coast_conditioned_weight(weight, distance, distance_to_coast_km),
        line_positions,
    )


def _apply_constraints(
    base_elevation: NDArray[np.float64],
    sample_points: Any,
    distance_to_coast_km: NDArray[np.float64],
    constraints: tuple[_MetricConstraint, ...],
    largest_feature_km: float,
    maximum_elevation_m: float,
    detail_driver: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Condition a broad base surface and report where fine detail should fade."""

    elevation = base_elevation.copy()
    detail_suppression = np.zeros_like(elevation)

    brush_weight = np.zeros_like(elevation)
    brush_targets = np.zeros_like(elevation)
    for constraint in constraints:
        if constraint.kind != "brush" or constraint.elevation_mode != "absolute":
            continue
        raw_distance = cast(Any, shapely.distance(sample_points, constraint.geometry))
        distance = cast(NDArray[np.float64], np.asarray(raw_distance, dtype=np.float64))
        weight = constraint.intensity * _constraint_weight(
            distance,
            constraint.influence_radius_km,
            largest_feature_km,
            is_structure=False,
            is_brush=True,
        )
        weight = _coast_conditioned_weight(weight, distance, distance_to_coast_km)
        brush_weight += weight
        brush_targets += weight * constraint.elevation_m
    brush_affected = brush_weight > 0.0
    if np.any(brush_affected):
        brush_target = np.divide(
            brush_targets,
            brush_weight,
            out=np.zeros_like(brush_targets),
            where=brush_affected,
        )
        brush_blend = np.clip(brush_weight, 0.0, 1.0)
        elevation = elevation * (1.0 - brush_blend) + brush_target * brush_blend
        detail_suppression = np.maximum(detail_suppression, brush_blend)

    relative_brush_delta = np.zeros_like(elevation)
    for constraint in constraints:
        if constraint.kind != "brush" or constraint.elevation_mode != "relative":
            continue
        raw_distance = cast(Any, shapely.distance(sample_points, constraint.geometry))
        distance = cast(NDArray[np.float64], np.asarray(raw_distance, dtype=np.float64))
        weight = constraint.intensity * _constraint_weight(
            distance,
            constraint.influence_radius_km,
            largest_feature_km,
            is_structure=False,
            is_brush=True,
        )
        weight = _coast_conditioned_weight(weight, distance, distance_to_coast_km)
        relative_brush_delta += weight * constraint.elevation_m
    elevation += relative_brush_delta

    ridge_raise = np.zeros_like(elevation)
    ridge_profile_weight = np.zeros_like(elevation)
    ridge_profile_targets = np.zeros_like(elevation)
    for constraint in constraints:
        if constraint.kind != "ridge" or constraint.elevation_mode != "absolute":
            continue
        weight, line_positions = _structure_response(
            constraint,
            sample_points,
            distance_to_coast_km,
            largest_feature_km,
            detail_driver,
        )
        detail_suppression = np.maximum(detail_suppression, weight)
        target, authored_control = _structure_profile(constraint, line_positions)
        generated_relief = np.minimum(
            0.10 * target,
            0.22 * np.maximum(maximum_elevation_m - target, 0.0),
        )
        target += (
            generated_relief
            * np.clip(0.5 + 0.5 * detail_driver, 0.0, 1.0)
            * (1.0 - authored_control)
        )
        ridge_raise = np.maximum(
            ridge_raise,
            weight * (1.0 - authored_control) * np.maximum(target - elevation, 0.0),
        )
        profile_weight = weight * authored_control
        ridge_profile_weight += profile_weight
        ridge_profile_targets += profile_weight * target
    elevation += ridge_raise
    ridge_profile_affected = ridge_profile_weight > 0.0
    if np.any(ridge_profile_affected):
        ridge_profile_target = np.divide(
            ridge_profile_targets,
            ridge_profile_weight,
            out=np.zeros_like(ridge_profile_targets),
            where=ridge_profile_affected,
        )
        ridge_profile_blend = np.clip(ridge_profile_weight, 0.0, 1.0)
        elevation = elevation * (1.0 - ridge_profile_blend) + (
            ridge_profile_target * ridge_profile_blend
        )

    relative_ridge_raise = np.zeros_like(elevation)
    for constraint in constraints:
        if constraint.kind != "ridge" or constraint.elevation_mode != "relative":
            continue
        weight, line_positions = _structure_response(
            constraint,
            sample_points,
            distance_to_coast_km,
            largest_feature_km,
            detail_driver,
        )
        profile_target, authored_control = _structure_profile(
            constraint, line_positions
        )
        profiled_relief = (
            constraint.elevation_m * (1.0 - authored_control)
            + profile_target * authored_control
        )
        relative_ridge_raise = np.maximum(
            relative_ridge_raise,
            weight * profiled_relief,
        )
    elevation += relative_ridge_raise

    valley_cut = np.zeros_like(elevation)
    valley_profile_weight = np.zeros_like(elevation)
    valley_profile_targets = np.zeros_like(elevation)
    for constraint in constraints:
        if constraint.kind != "valley" or constraint.elevation_mode != "absolute":
            continue
        weight, line_positions = _structure_response(
            constraint,
            sample_points,
            distance_to_coast_km,
            largest_feature_km,
            detail_driver,
        )
        detail_suppression = np.maximum(detail_suppression, weight)
        target, authored_control = _structure_profile(constraint, line_positions)
        generated_incision = np.minimum(0.15 * target, 300.0)
        target -= (
            generated_incision
            * np.clip(0.5 + 0.5 * detail_driver, 0.0, 1.0)
            * (1.0 - authored_control)
        )
        valley_cut = np.maximum(
            valley_cut,
            weight * (1.0 - authored_control) * np.maximum(elevation - target, 0.0),
        )
        profile_weight = weight * authored_control
        valley_profile_weight += profile_weight
        valley_profile_targets += profile_weight * target
    elevation -= valley_cut
    valley_profile_affected = valley_profile_weight > 0.0
    if np.any(valley_profile_affected):
        valley_profile_target = np.divide(
            valley_profile_targets,
            valley_profile_weight,
            out=np.zeros_like(valley_profile_targets),
            where=valley_profile_affected,
        )
        valley_profile_blend = np.clip(valley_profile_weight, 0.0, 1.0)
        elevation = elevation * (1.0 - valley_profile_blend) + (
            valley_profile_target * valley_profile_blend
        )

    relative_valley_cut = np.zeros_like(elevation)
    for constraint in constraints:
        if constraint.kind != "valley" or constraint.elevation_mode != "relative":
            continue
        weight, line_positions = _structure_response(
            constraint,
            sample_points,
            distance_to_coast_km,
            largest_feature_km,
            detail_driver,
        )
        profile_target, authored_control = _structure_profile(
            constraint, line_positions
        )
        profiled_depth = (
            constraint.elevation_m * (1.0 - authored_control)
            + profile_target * authored_control
        )
        relative_valley_cut = np.maximum(
            relative_valley_cut,
            weight * profiled_depth,
        )
    elevation -= relative_valley_cut

    relative_point_delta = np.zeros_like(elevation)
    for constraint in constraints:
        if (
            constraint.kind != "point"
            or constraint.elevation_mode != "relative"
            or constraint.attached_to_structure
        ):
            continue
        raw_distance = cast(Any, shapely.distance(sample_points, constraint.geometry))
        distance = cast(NDArray[np.float64], np.asarray(raw_distance, dtype=np.float64))
        weight = _constraint_weight(
            distance,
            constraint.influence_radius_km,
            largest_feature_km,
            is_structure=False,
        )
        weight = _coast_conditioned_weight(weight, distance, distance_to_coast_km)
        relative_point_delta += weight * constraint.elevation_m
    elevation += relative_point_delta

    point_weight = np.zeros_like(elevation)
    point_targets = np.zeros_like(elevation)
    for constraint in constraints:
        if constraint.kind != "point" or constraint.elevation_mode != "absolute":
            continue
        raw_distance = cast(Any, shapely.distance(sample_points, constraint.geometry))
        distance = cast(NDArray[np.float64], np.asarray(raw_distance, dtype=np.float64))
        weight = _constraint_weight(
            distance,
            (
                0.45 * constraint.influence_radius_km
                if constraint.attached_to_structure
                else constraint.influence_radius_km
            ),
            largest_feature_km,
            is_structure=False,
            attached_point=constraint.attached_to_structure,
        )
        weight = _coast_conditioned_weight(weight, distance, distance_to_coast_km)
        detail_suppression = np.maximum(detail_suppression, weight)
        point_weight += weight
        point_targets += weight * constraint.elevation_m
    affected = point_weight > 0.0
    if np.any(affected):
        target = np.divide(
            point_targets,
            point_weight,
            out=np.zeros_like(point_targets),
            where=affected,
        )
        blend = np.clip(point_weight, 0.0, 1.0)
        elevation = elevation * (1.0 - blend) + target * blend

    return elevation, np.clip(detail_suppression, 0.0, 1.0)


def generate_terrain(
    coastline: Coastline,
    settings: TerrainSettings,
    progress: ProgressCallback | None = None,
    *,
    constraints: Sequence[TerrainConstraint] = (),
) -> GeneratedTerrain:
    """Generate a deterministic Float32 elevation grid inside a coastline."""

    _report(progress, 0.02, "Preparing metric grid")
    polygon, width_km, height_km = _metric_polygon(coastline, settings.object_scale_km)
    authored_constraints = tuple(constraints)
    metric_constraints = _metric_constraints(
        authored_constraints,
        polygon,
        width_km,
        height_km,
        settings.maximum_elevation_m,
    )
    longest_km = max(width_km, height_km)
    width = max(2, round(settings.resolution_px * width_km / longest_km))
    height = max(2, round(settings.resolution_px * height_km / longest_km))
    x_km = np.linspace(0.0, width_km, width, dtype=np.float64)
    y_km = np.linspace(0.0, height_km, height, dtype=np.float64)
    elevation = np.full((height, width), np.nan, dtype=np.float32)
    mask = np.zeros((height, width), dtype=np.bool_)
    boundary = polygon.boundary

    chunk_rows = 128
    for start in range(0, height, chunk_rows):
        stop = min(start + chunk_rows, height)
        x_grid, y_grid = np.meshgrid(x_km, y_km[start:stop])
        chunk_mask = shapely.intersects_xy(polygon, x_grid, y_grid)
        points: Any = shapely.points(x_grid, y_grid)
        raw_distance_to_coast = cast(Any, shapely.distance(points, boundary))
        distance_to_coast = cast(
            NDArray[np.float64], np.asarray(raw_distance_to_coast, dtype=np.float64)
        )
        relief_noise = fractal_value_noise(
            x_grid,
            y_grid,
            seed=settings.seed,
            largest_feature_km=settings.largest_feature_km,
            detail_levels=settings.detail_levels,
            roughness=settings.roughness,
        )

        coastal_envelope = 1.0 - np.exp(-distance_to_coast / settings.coastal_rise_km)
        shaped_noise = np.power(np.clip(0.5 + 0.5 * relief_noise, 0.0, 1.0), 1.35)
        relief = (1.0 - settings.variability) * 0.72 + settings.variability * shaped_noise
        unconditioned_elevation = settings.maximum_elevation_m * coastal_envelope * relief
        if metric_constraints:
            macro_noise = fractal_value_noise(
                x_grid,
                y_grid,
                seed=settings.seed,
                largest_feature_km=settings.largest_feature_km,
                detail_levels=min(2, settings.detail_levels),
                roughness=settings.roughness,
            )
            shaped_macro = np.power(np.clip(0.5 + 0.5 * macro_noise, 0.0, 1.0), 1.35)
            macro_relief = (
                (1.0 - settings.variability) * 0.72
                + settings.variability * shaped_macro
            )
            macro_elevation = (
                settings.maximum_elevation_m * coastal_envelope * macro_relief
            )
            conditioned_elevation, constraint_influence = _apply_constraints(
                macro_elevation,
                points,
                distance_to_coast,
                metric_constraints,
                settings.largest_feature_km,
                settings.maximum_elevation_m,
                relief_noise,
            )
            residual_detail = unconditioned_elevation - macro_elevation
            chunk_elevation = conditioned_elevation + residual_detail * (
                1.0 - constraint_influence
            )
            chunk_elevation = np.clip(chunk_elevation, 0.0, settings.maximum_elevation_m)
        else:
            chunk_elevation = unconditioned_elevation
        chunk_elevation = np.where(chunk_mask, chunk_elevation, np.nan)

        elevation[start:stop] = chunk_elevation.astype(np.float32)
        mask[start:stop] = chunk_mask
        completed = stop / height
        _report(progress, 0.08 + 0.82 * completed, "Building elevation field")

    _report(progress, 0.94, "Validating terrain")
    if not np.any(mask):
        raise ValueError("The coastline does not cover any output pixels.")
    if not np.all(np.isfinite(elevation[mask])):
        raise RuntimeError("Terrain generation produced non-finite land elevations.")
    if np.any(elevation[mask] < 0):
        raise RuntimeError("Terrain generation produced land below sea level.")

    _report(progress, 1.0, "Terrain ready")
    return GeneratedTerrain(
        elevation_m=elevation,
        land_mask=mask,
        x_km=x_km,
        y_km=y_km,
        settings=settings,
        constraints=authored_constraints,
        source_name=coastline.source_name,
    )
