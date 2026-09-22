# pyright: reportUnknownMemberType=false
"""Regional macro composition before authored constraints and drainage planning."""

from collections.abc import Iterator
from dataclasses import astuple, dataclass
from typing import Any, cast

import numpy as np
import shapely
from numpy.typing import NDArray
from shapely.geometry import MultiPolygon, Polygon

from dmtools.terrain.domain import LandformSettings, TerrainRegion, TerrainSettings
from dmtools.terrain.domain.seeds import LANDFORM_STAGE_ID, stage_seed
from dmtools.terrain.pipeline.noise import fractal_value_noise

LANDFORM_ALGORITHM_ID = "regional-landforms@2"


@dataclass(frozen=True, slots=True)
class MetricRegion:
    geometry: Polygon
    source: TerrainRegion


def prepare_regions(
    regions: tuple[TerrainRegion, ...], width_km: float, height_km: float,
    land: Polygon | MultiPolygon, maximum_elevation_m: float,
) -> tuple[MetricRegion, ...]:
    prepared: list[MetricRegion] = []
    # Stable ordering makes overlap blending independent of authoring order.
    for region in sorted(regions, key=lambda item: (astuple(item.settings), item.points)):
        geometry = Polygon([(x * width_km, y * height_km) for x, y in region.points])
        if not geometry.is_valid or geometry.area <= 0:
            raise ValueError("Terrain region must be a simple polygon with positive area.")
        if not geometry.intersects(land) or geometry.intersection(land).area <= 0:
            raise ValueError("Terrain region must cover some land.")
        if region.settings.elevation_m > maximum_elevation_m:
            raise ValueError("Regional elevation exceeds the elevation ceiling.")
        prepared.append(MetricRegion(geometry, region))
    return tuple(prepared)


def _broad_noise(
    x: NDArray[np.float64], y: NDArray[np.float64], seed: int, feature_size_km: float,
) -> NDArray[np.float64]:
    # The fixed two-band shape carrier uses its full scale. It is not a growing
    # detail prefix: its weights stay 2/3 and 1/3 at every selected detail count.
    return fractal_value_noise(x, y, seed=seed, largest_feature_km=feature_size_km,
                               detail_levels=2, roughness=0.5) / 0.75


def regional_noise_basis(
    x: NDArray[np.float64], y: NDArray[np.float64], controls: LandformSettings, seed: int,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Shared coordinates/carrier for regional relief and mountain-crest detection."""
    angle = np.deg2rad(controls.orientation_deg)
    u = np.cos(angle) * x + np.sin(angle) * y
    v = -np.sin(angle) * x + np.cos(angle) * y
    if controls.character == "mountains":
        u = u / 3.0
    broad = _broad_noise(u, v, seed, controls.feature_size_km)
    return u, v, broad


def regional_elevation_fields(
    x: NDArray[np.float64], y: NDArray[np.float64], coast_distance: NDArray[np.float64],
    full: NDArray[np.float64], macro: NDArray[np.float64],
    settings: TerrainSettings, regions: tuple[MetricRegion, ...],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    if not regions:
        return full, macro
    total = np.zeros_like(full)
    target_macro = np.zeros_like(full)
    target_full = np.zeros_like(full)
    seed = stage_seed(settings.seed, LANDFORM_STAGE_ID)
    coastal_gate = -np.expm1(-coast_distance / settings.coastal_rise_km)
    for region, inside, weight in _regional_weights(x, y, regions):
        controls = region.source.settings
        u, v, broad = regional_noise_basis(x[inside], y[inside], controls, seed)
        detail = fractal_value_noise(u, v, seed=seed,
            largest_feature_km=controls.feature_size_km,
            detail_levels=max(2, settings.detail_levels),
            roughness=settings.roughness, start_band=2)
        if controls.character == "mountains":
            # A second coordinate window varies summit heights along the belt;
            # a single ridged carrier would give every crest the same height.
            crest = _broad_noise(u + 5 * controls.feature_size_km, v - 7 * controls.feature_size_km,
                                 seed, 1.8 * controls.feature_size_km)
            shape = np.power(1 - np.abs(broad), 3) * (0.25 + 0.75 * (0.5 + 0.5 * crest))
            texture = 0.45 * detail * (0.3 + 0.7 * shape)
        elif controls.character == "plateau":
            shape, texture = 0.1 * broad, 0.03 * detail
        elif controls.character == "plain":
            shape, texture = 0.5 * broad, 0.05 * detail
        else:
            shape, texture = 0.5 * broad, 0.3 * detail
        local_macro = np.maximum(controls.elevation_m + controls.relief_m * shape, 0)
        local_full = np.maximum(local_macro + controls.relief_m * texture, 0)
        target_macro[inside] += weight * local_macro * coastal_gate[inside]
        target_full[inside] += weight * local_full * coastal_gate[inside]
        total[inside] += weight
    influence = np.minimum(total, 1)
    denominator = np.maximum(total, np.finfo(np.float64).tiny)
    return (
        full * (1 - influence) + target_full / denominator * influence,
        macro * (1 - influence) + target_macro / denominator * influence,
    )


def _regional_weights(
    x: NDArray[np.float64], y: NDArray[np.float64], regions: tuple[MetricRegion, ...],
) -> Iterator[tuple[MetricRegion, NDArray[np.bool_], NDArray[np.float64]]]:
    """Share the inward transition between landform shape and process budgets."""
    if not regions:
        return
    points: Any = shapely.points(x, y)
    for region in regions:
        inside = np.asarray(shapely.intersects_xy(region.geometry, x, y), dtype=np.bool_)
        if not inside.any():
            continue
        distance = cast(NDArray[np.float64], np.asarray(
            cast(Any, shapely.distance(points[inside], region.geometry.boundary)),
            dtype=np.float64,
        ))
        fade = np.clip(distance / region.source.settings.transition_km, 0, 1)
        yield region, inside, fade * fade * (3 - 2 * fade)


def regional_incision_budget(
    x: NDArray[np.float64], y: NDArray[np.float64], background_budget_m: float,
    regions: tuple[MetricRegion, ...],
) -> NDArray[np.float64]:
    """Blend heuristic automatic-cut limits; authored valleys are separate."""
    relief_fraction = {"plain": 0.15, "hills": 0.40, "plateau": 0.25, "mountains": 0.25}
    total = np.zeros_like(x)
    target = np.zeros_like(x)
    for region, inside, weight in _regional_weights(x, y, regions):
        controls = region.source.settings
        local_budget = min(background_budget_m,
                           relief_fraction[controls.character] * controls.relief_m)
        target[inside] += weight * local_budget
        total[inside] += weight
    influence = np.minimum(total, 1)
    denominator = np.maximum(total, np.finfo(np.float64).tiny)
    return background_budget_m * (1 - influence) + target / denominator * influence


def regional_transition_mask(
    x: NDArray[np.float64], y: NDArray[np.float64], regions: tuple[MetricRegion, ...],
) -> NDArray[np.bool_]:
    """Nodes inside at least one region's inward boundary transition."""
    transition = np.zeros(x.shape, dtype=np.bool_)
    for _region, inside, weight in _regional_weights(x, y, regions):
        transition[inside] |= weight < 1.0
    return transition
