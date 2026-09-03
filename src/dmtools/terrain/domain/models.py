"""Core input models for deterministic terrain generation."""

from dataclasses import dataclass
from math import isfinite
from typing import Literal

type Point2D = tuple[float, float]
type StructureKind = Literal["ridge", "valley"]
type ElevationMode = Literal["absolute", "relative"]


def _validate_ring(points: tuple[Point2D, ...], label: str) -> None:
    if len(points) < 4:
        raise ValueError(f"{label} needs at least three vertices and a closing vertex.")
    if points[0] != points[-1]:
        raise ValueError(f"{label} must be closed.")
    if any(not isfinite(value) for point in points for value in point):
        raise ValueError(f"{label} coordinates must be finite.")


@dataclass(frozen=True, slots=True)
class LandComponent:
    """One connected land polygon with optional enclosed water holes."""

    exterior: tuple[Point2D, ...]
    holes: tuple[tuple[Point2D, ...], ...] = ()

    def __post_init__(self) -> None:
        _validate_ring(self.exterior, "Land-component exterior")
        for index, hole in enumerate(self.holes, start=1):
            _validate_ring(hole, f"Land-component hole {index}")


@dataclass(frozen=True, slots=True)
class Coastline:
    """Dissolved land geometry expressed as closed source-vector coastlines."""

    points: tuple[Point2D, ...]
    source_name: str
    holes: tuple[tuple[Point2D, ...], ...] = ()
    additional_components: tuple[LandComponent, ...] = ()

    def __post_init__(self) -> None:
        _validate_ring(self.points, "Primary land-component exterior")
        for index, hole in enumerate(self.holes, start=1):
            _validate_ring(hole, f"Primary land-component hole {index}")

    @property
    def components(self) -> tuple[LandComponent, ...]:
        """Return the primary landmass followed by disconnected land components."""

        return (LandComponent(self.points, self.holes), *self.additional_components)

    @property
    def component_count(self) -> int:
        return 1 + len(self.additional_components)

    @property
    def boundary_point_count(self) -> int:
        return sum(
            len(component.exterior) - 1
            + sum(len(hole) - 1 for hole in component.holes)
            for component in self.components
        )

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        xs = [point[0] for component in self.components for point in component.exterior]
        ys = [point[1] for component in self.components for point in component.exterior]
        return min(xs), min(ys), max(xs), max(ys)


def _validate_normalized_point(point: Point2D) -> None:
    if any(not isfinite(value) for value in point):
        raise ValueError("Constraint coordinates must be finite.")
    if any(not 0.0 <= value <= 1.0 for value in point):
        raise ValueError("Constraint coordinates must be between 0 and 1.")


def _validate_constraint_values(
    elevation_m: float,
    influence_radius_km: float,
    elevation_mode: ElevationMode,
    *,
    allow_signed_relative: bool,
) -> None:
    if elevation_mode not in ("absolute", "relative"):
        raise ValueError("Elevation mode must be 'absolute' or 'relative'.")
    if not isfinite(elevation_m):
        raise ValueError("Constraint elevation must be finite.")
    if elevation_mode == "absolute" and elevation_m < 0:
        raise ValueError("Absolute elevation must be at or above sea level.")
    if elevation_mode == "relative" and not allow_signed_relative and elevation_m < 0:
        raise ValueError("Relative ridge relief and valley depth must not be negative.")
    if not isfinite(influence_radius_km) or influence_radius_km <= 0:
        raise ValueError("Constraint influence radius must be positive and finite.")


@dataclass(frozen=True, slots=True)
class ElevationPoint:
    """An authored target height at a normalized position inside the coastline."""

    position: Point2D
    elevation_m: float
    influence_radius_km: float
    elevation_mode: ElevationMode = "absolute"

    def __post_init__(self) -> None:
        _validate_normalized_point(self.position)
        _validate_constraint_values(
            self.elevation_m,
            self.influence_radius_km,
            self.elevation_mode,
            allow_signed_relative=True,
        )


@dataclass(frozen=True, slots=True)
class TerrainStructure:
    """An authored ridge or valley centreline in normalized coastline coordinates."""

    kind: StructureKind
    points: tuple[Point2D, ...]
    elevation_m: float
    influence_radius_km: float
    elevation_mode: ElevationMode = "absolute"

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
        _validate_constraint_values(
            self.elevation_m,
            self.influence_radius_km,
            self.elevation_mode,
            allow_signed_relative=False,
        )


@dataclass(frozen=True, slots=True)
class TerrainBrushStroke:
    """A soft target-elevation stroke painted in normalized map coordinates."""

    points: tuple[Point2D, ...]
    elevation_m: float
    influence_radius_km: float
    intensity: float
    elevation_mode: ElevationMode = "absolute"

    def __post_init__(self) -> None:
        if not self.points:
            raise ValueError("A terrain brush stroke needs at least one point.")
        for point in self.points:
            _validate_normalized_point(point)
        adjacent_pairs = zip(self.points, self.points[1:], strict=False)
        if any(first == second for first, second in adjacent_pairs):
            raise ValueError("Adjacent terrain brush points must be different.")
        _validate_constraint_values(
            self.elevation_m,
            self.influence_radius_km,
            self.elevation_mode,
            allow_signed_relative=True,
        )
        if not isfinite(self.intensity) or not 0.0 < self.intensity <= 1.0:
            raise ValueError("Terrain brush intensity must be greater than 0 and at most 1.")


type TerrainConstraint = ElevationPoint | TerrainStructure | TerrainBrushStroke


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
