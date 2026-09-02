"""Core input models for deterministic terrain generation."""

from dataclasses import dataclass
from math import isfinite
from typing import Literal

type Point2D = tuple[float, float]
type StructureKind = Literal["ridge", "valley"]


@dataclass(frozen=True, slots=True)
class Coastline:
    """One closed coastline expressed in source-vector coordinates."""

    points: tuple[Point2D, ...]
    source_name: str

    def __post_init__(self) -> None:
        if len(self.points) < 4:
            raise ValueError("A coastline needs at least three vertices and a closing vertex.")
        if self.points[0] != self.points[-1]:
            raise ValueError("The coastline must be closed.")
        if any(not isfinite(value) for point in self.points for value in point):
            raise ValueError("Coastline coordinates must be finite.")

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        xs = [point[0] for point in self.points]
        ys = [point[1] for point in self.points]
        return min(xs), min(ys), max(xs), max(ys)


def _validate_normalized_point(point: Point2D) -> None:
    if any(not isfinite(value) for value in point):
        raise ValueError("Constraint coordinates must be finite.")
    if any(not 0.0 <= value <= 1.0 for value in point):
        raise ValueError("Constraint coordinates must be between 0 and 1.")


def _validate_constraint_values(elevation_m: float, influence_radius_km: float) -> None:
    if not isfinite(elevation_m) or elevation_m < 0:
        raise ValueError("Constraint elevation must be a finite value at or above sea level.")
    if not isfinite(influence_radius_km) or influence_radius_km <= 0:
        raise ValueError("Constraint influence radius must be positive and finite.")


@dataclass(frozen=True, slots=True)
class ElevationPoint:
    """An authored target height at a normalized position inside the coastline."""

    position: Point2D
    elevation_m: float
    influence_radius_km: float

    def __post_init__(self) -> None:
        _validate_normalized_point(self.position)
        _validate_constraint_values(self.elevation_m, self.influence_radius_km)


@dataclass(frozen=True, slots=True)
class TerrainStructure:
    """An authored ridge or valley centreline in normalized coastline coordinates."""

    kind: StructureKind
    points: tuple[Point2D, ...]
    elevation_m: float
    influence_radius_km: float

    def __post_init__(self) -> None:
        if self.kind not in ("ridge", "valley"):
            raise ValueError("Terrain structure kind must be 'ridge' or 'valley'.")
        if len(self.points) < 2:
            raise ValueError("A terrain structure needs at least two points.")
        for point in self.points:
            _validate_normalized_point(point)
        adjacent_pairs = zip(self.points, self.points[1:], strict=False)
        if any(first == second for first, second in adjacent_pairs):
            raise ValueError("Adjacent terrain structure points must be different.")
        _validate_constraint_values(self.elevation_m, self.influence_radius_km)


type TerrainConstraint = ElevationPoint | TerrainStructure


@dataclass(frozen=True, slots=True)
class TerrainSettings:
    """Effective settings for the first coastline-conditioned terrain model."""

    seed: int = 20_260_902
    object_scale_km: float = 4_000.0
    resolution_px: int = 768
    maximum_elevation_m: float = 4_500.0
    largest_feature_km: float = 450.0
    detail_levels: int = 6
    roughness: float = 0.55
    coastal_rise_km: float = 180.0
    variability: float = 0.75

    def __post_init__(self) -> None:
        if not 0 <= self.seed <= 4_294_967_295:
            raise ValueError("Seed must be between 0 and 4,294,967,295.")
        if self.object_scale_km <= 0:
            raise ValueError("Object scale must be positive.")
        if not 64 <= self.resolution_px <= 4_096:
            raise ValueError("Resolution must be between 64 and 4,096 pixels.")
        if self.maximum_elevation_m <= 0:
            raise ValueError("Maximum elevation must be positive.")
        if self.largest_feature_km <= 0:
            raise ValueError("Largest feature size must be positive.")
        if not 1 <= self.detail_levels <= 12:
            raise ValueError("Detail levels must be between 1 and 12.")
        if not 0 < self.roughness < 1:
            raise ValueError("Roughness must be greater than 0 and less than 1.")
        if self.coastal_rise_km <= 0:
            raise ValueError("Coastal rise distance must be positive.")
        if not 0 <= self.variability <= 1:
            raise ValueError("Variability must be between 0 and 1.")
