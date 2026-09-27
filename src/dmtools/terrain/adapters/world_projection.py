# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false
"""Project retained spherical land through PROJ; never run terrain in page degrees."""

from math import atan2, degrees, hypot, pi

import numpy as np
from numpy.typing import NDArray
from rasterio.warp import transform
from shapely import make_valid, normalize
from shapely.affinity import translate
from shapely.geometry import Polygon
from shapely.ops import unary_union

from dmtools.terrain.domain.models import Coastline, LandComponent
from dmtools.terrain.domain.world import WorldFrame
from dmtools.terrain.domain.world_terrain import (
    MAX_PROJECTED_POINTS,
    MAX_PROJECTION_ANGLE_DEG,
    WorldTerrainProjection,
    WorldTerrainSource,
)
from dmtools.terrain.pipeline.control import CancellationToken, check_cancelled
from dmtools.terrain.pipeline.world import WorldMap, component_area_km2, components_from_geometry
from dmtools.terrain.pipeline.world_landmass import WorldLandmass


def _centre(parts: tuple[LandComponent, ...], frame: WorldFrame) -> tuple[float, float]:
    vectors = []
    for part in parts:
        centroid = Polygon(part.exterior, part.holes).centroid
        lon, lat = np.radians(frame.source_to_lonlat((centroid.x, centroid.y)))
        area = component_area_km2(part, frame)
        vectors.append(
            area * np.array([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])
        )
    vector = np.sum(vectors, axis=0)
    if not np.all(np.isfinite(vector)) or np.linalg.norm(vector) < 1e-8:
        raise ValueError("This land selection needs separate regional projection domains.")
    lon = (degrees(atan2(vector[1], vector[0])) + 180) % 360 - 180
    lat = degrees(atan2(vector[2], hypot(vector[0], vector[1])))
    return lon, lat


def project_landmass(
    world: WorldMap,
    land: WorldLandmass,
    *,
    cancellation: CancellationToken | None = None,
) -> WorldTerrainSource:
    check_cancelled(cancellation)
    frame = world.project.frame
    # Ownership partitions must not change the physical projection. Dissolve
    # before finding its centre; remove only exactly redundant collinear vertices
    # and normalize ring order so a split border cannot perturb the sampled coast.
    physical = normalize(
        unary_union([Polygon(p.exterior, p.holes) for p in land.components])
        .simplify(0.0, preserve_topology=True)
    )
    physical_parts = components_from_geometry(physical)
    total_area = sum(component_area_km2(p, frame) for p in physical_parts)
    if total_area >= 2 * pi * frame.radius_km**2:
        raise ValueError("A hemisphere-sized land selection needs separate regional domains.")
    lon, lat = _centre(physical_parts, frame)
    initial = WorldTerrainProjection(frame.radius_km, lon, lat, 0.0, 1.0)
    centre_x, _ = frame.lonlat_to_source((lon, lat))
    # Rejoin source pieces across the map seam before projecting them. Shared
    # continent borders disappear here, while real coastline holes remain.
    unwrapped = []
    for part in physical_parts:
        polygon = Polygon(part.exterior, part.holes)
        shift = round((centre_x - polygon.centroid.x) / frame.width) * frame.width
        unwrapped.append(translate(polygon, xoff=shift))
    merged = components_from_geometry(
        normalize(unary_union(unwrapped).simplify(0.0, preserve_topology=True))
    )
    maximum_angle = 0.0
    point_count = 0

    def project(xy: NDArray[np.float64]) -> NDArray[np.float64]:
        nonlocal maximum_angle
        longitude = (
            frame.central_meridian_deg + (xy[:, 0] - frame.bounds[0]) / frame.width * 360 - 180
        )
        longitude = (longitude + 180) % 360 - 180
        latitude = 90 - (xy[:, 1] - frame.bounds[1]) / frame.height * 180
        longitude[np.abs(latitude) == 90] = 0.0
        a, b = np.radians(longitude - lon), np.radians(latitude)
        centre_lat = np.radians(lat)
        angle = np.arccos(
            np.clip(
                np.sin(b) * np.sin(centre_lat) + np.cos(b) * np.cos(centre_lat) * np.cos(a), -1, 1
            )
        )
        maximum_angle = max(maximum_angle, float(np.max(angle, initial=0)))
        if maximum_angle > np.radians(MAX_PROJECTION_ANGLE_DEG):
            raise ValueError(
                "This land selection extends beyond the supported 80-degree projection radius. "
                "It needs separate regional domains; changing the planet scale is not a fix."
            )
        transformed = transform(
            initial.geographic_crs, initial.projected_crs, longitude.tolist(), latitude.tolist()
        )
        east, north = transformed[0], transformed[1]
        result = np.column_stack((east, -np.asarray(north, dtype=np.float64)))
        if not np.all(np.isfinite(result)):
            raise ValueError("World projection produced nonfinite coordinates.")
        return result

    def ring(points: tuple[tuple[float, float], ...]) -> tuple[tuple[float, float], ...]:
        nonlocal point_count
        check_cancelled(cancellation)
        source = np.asarray(points, dtype=np.float64)
        span = np.abs(np.diff(source, axis=0)) * (360 / frame.width, 180 / frame.height)
        counts = np.maximum(1, np.ceil(span.max(axis=1) / initial.source_step_deg)).astype(int)
        if point_count + int(counts.sum()) + 1 > MAX_PROJECTED_POINTS:
            raise ValueError("Projected coastline exceeds 500,000 points; select a smaller domain.")
        pieces = [
            a + np.arange(n)[:, None] / n * (b - a)
            for a, b, n in zip(source[:-1], source[1:], counts, strict=True)
        ]
        source = np.vstack((*pieces, source[-1:]))
        for _ in range(16):
            check_cancelled(cancellation)
            projected = project(source)
            fractions = np.array([0.25, 0.5, 0.75])
            probes = (
                source[:-1, None, :] + fractions[None, :, None] * np.diff(source, axis=0)[:, None]
            )
            actual = project(probes.reshape(-1, 2)).reshape(-1, 3, 2)
            chords = (
                projected[:-1, None, :]
                + fractions[None, :, None] * np.diff(projected, axis=0)[:, None]
            )
            refine = np.any(
                np.linalg.norm(actual - chords, axis=2) > initial.curve_tolerance_m, axis=1
            )
            if not np.any(refine):
                break
            if point_count + len(source) + int(refine.sum()) > MAX_PROJECTED_POINTS:
                raise ValueError("Projection curve refinement exceeds 500,000 points.")
            source = np.vstack(
                [
                    p
                    for i, p in enumerate(source)
                    for p in (
                        [p, (p + source[i + 1]) / 2] if i < len(refine) and refine[i] else [p]
                    )
                ]
            )
        else:
            raise ValueError("Projection curves need more than the bounded refinement depth.")
        point_count += len(projected)
        # Every longitude at a pole is the same point. Remove only exact duplicate
        # consecutive coordinates, including the duplicate closing-pole case.
        keep = np.concatenate(([True], np.any(np.diff(projected, axis=0) != 0, axis=1)))
        values = [(float(p[0]), float(p[1])) for p in projected[keep]]
        if values[-1] != values[0]:
            values.append(values[0])
        return tuple(values)

    polygons = []
    for part in merged:
        candidate = Polygon(ring(part.exterior), [ring(h) for h in part.holes])
        if not candidate.is_valid:
            # Pole/seam collapse can leave a zero-area spike. Refuse any repair
            # that changes area materially instead of inventing new coastline.
            repaired = make_valid(candidate)
            if abs(repaired.area - candidate.area) > max(1.0, abs(candidate.area) * 1e-9):
                raise ValueError("Projected coastline folds over itself; use a smaller domain.")
            candidate = repaired
        polygons.append(candidate)
    components = components_from_geometry(unary_union(polygons))
    if not components:
        raise ValueError("Selected land has no usable projected area.")
    components = tuple(sorted(components, key=lambda p: -Polygon(p.exterior, p.holes).area))
    first = components[0]
    name = next(c.name for c in world.project.continents if c.id == land.requested_continent_id)
    coastline = Coastline(first.exterior, name, first.holes, components[1:])
    projection = WorldTerrainProjection(
        frame.radius_km,
        lon,
        lat,
        degrees(maximum_angle),
        float(maximum_angle / np.sin(maximum_angle)) if maximum_angle > 1e-12 else 1.0,
    )
    return WorldTerrainSource(
        world.project,
        land.requested_continent_id,
        land.continent_ids,
        land.feature_ids,
        coastline,
        projection,
    )
