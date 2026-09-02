# pyright: reportUnknownMemberType=false
"""First deterministic coastline-conditioned terrain pipeline."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import shapely
from numpy.typing import NDArray
from shapely.geometry import Polygon

from dmtools.terrain.domain import Coastline, TerrainSettings
from dmtools.terrain.pipeline.noise import fractal_value_noise

type ProgressCallback = Callable[[float, str], None]


@dataclass(frozen=True, slots=True)
class GeneratedTerrain:
    """Authoritative numeric result of one in-memory terrain generation."""

    elevation_m: NDArray[np.float32]
    land_mask: NDArray[np.bool_]
    x_km: NDArray[np.float64]
    y_km: NDArray[np.float64]
    settings: TerrainSettings
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


def _metric_polygon(coastline: Coastline, object_scale_km: float) -> tuple[Polygon, float, float]:
    min_x, min_y, max_x, max_y = coastline.bounds
    span_x = max_x - min_x
    span_y = max_y - min_y
    longest_span = max(span_x, span_y)
    if longest_span <= 0:
        raise ValueError("The coastline has no measurable extent.")
    km_per_source_unit = object_scale_km / longest_span
    points_km = [
        ((x - min_x) * km_per_source_unit, (y - min_y) * km_per_source_unit)
        for x, y in coastline.points
    ]
    polygon = Polygon(points_km)
    if not polygon.is_valid or polygon.area <= 0:
        raise ValueError("The coastline does not form a valid land polygon.")
    return polygon, span_x * km_per_source_unit, span_y * km_per_source_unit


def generate_terrain(
    coastline: Coastline,
    settings: TerrainSettings,
    progress: ProgressCallback | None = None,
) -> GeneratedTerrain:
    """Generate a deterministic Float32 elevation grid inside a coastline."""

    _report(progress, 0.02, "Preparing metric grid")
    polygon, width_km, height_km = _metric_polygon(coastline, settings.object_scale_km)
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
        points = shapely.points(x_grid, y_grid)
        distance_to_coast = shapely.distance(points, boundary)
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
        chunk_elevation = settings.maximum_elevation_m * coastal_envelope * relief
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
        source_name=coastline.source_name,
    )
