# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false
"""Read-only spherical world inspection; no terrain or climate is generated here."""

from dataclasses import dataclass
from itertools import pairwise
from math import pi, sin

from shapely.affinity import translate
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, box
from shapely.ops import unary_union

from dmtools.terrain.domain.models import LandComponent, Point2D
from dmtools.terrain.domain.world import WorldFrame, WorldProject, WorldRole


@dataclass(frozen=True, slots=True)
class WorldLandView:
    feature_id: str
    continent_id: str
    role: WorldRole
    components: tuple[LandComponent, ...]


@dataclass(frozen=True, slots=True)
class ContinentSummary:
    id: str
    name: str
    area_km2: float
    land_shapes: int
    island_shapes: int


@dataclass(frozen=True, slots=True)
class WorldMap:
    project: WorldProject
    land: tuple[WorldLandView, ...]
    continents: tuple[ContinentSummary, ...]
    land_area_km2: float

    @property
    def land_fraction(self) -> float:
        return self.land_area_km2 / self.project.frame.surface_area_km2


def _polygons(geometry: Polygon | MultiPolygon | GeometryCollection) -> list[Polygon]:
    if isinstance(geometry, Polygon):
        return [] if geometry.is_empty or geometry.area <= 0 else [geometry]
    return [
        p
        for g in geometry.geoms
        if isinstance(g, (Polygon, MultiPolygon, GeometryCollection))
        for p in _polygons(g)
    ]


def _ring_area(ring: tuple[Point2D, ...], frame: WorldFrame) -> float:
    # Integrate sin(latitude) d(longitude) along source-linear segments. This
    # measures the sampled Plate Carree boundary, not geodesic chords between it.
    integral = 0.0
    for (x0, y0), (x1, y1) in pairwise(ring):
        a = pi / 2 - (y0 - frame.bounds[1]) / frame.height * pi
        b = pi / 2 - (y1 - frame.bounds[1]) / frame.height * pi
        half_delta = (b - a) / 2
        sinc = sin(half_delta) / half_delta if half_delta else 1.0
        integral += (x1 - x0) / frame.width * 2 * pi * sin((a + b) / 2) * sinc
    return abs(integral) * frame.radius_km**2


def component_area_km2(component: LandComponent, frame: WorldFrame) -> float:
    return max(
        0.0,
        _ring_area(component.exterior, frame)
        - sum(_ring_area(hole, frame) for hole in component.holes),
    )


def prepare_world_map(project: WorldProject) -> WorldMap:
    """Validate assignments/topology and wrap views at the declared world seam."""
    frame = project.frame
    frame_polygon = box(*frame.bounds)
    features = {f.id: f for f in project.source.features}
    land: list[WorldLandView] = []
    all_polygons: list[Polygon] = []
    for assignment in sorted(project.assignments, key=lambda a: a.feature_id):
        if assignment.continent_id is None:
            continue
        feature = features[assignment.feature_id]
        parts: list[Polygon] = []
        for component in feature.components:
            polygon = Polygon(component.exterior, component.holes)
            x0, y0, x1, y1 = polygon.bounds
            if (
                y0 < frame.bounds[1]
                or y1 > frame.bounds[3]
                or x1 - x0 > frame.width
                or x0 < frame.bounds[0] - frame.width
                or x1 > frame.bounds[2] + frame.width
            ):
                raise ValueError(f"{feature.label}: land is outside the full-world frame.")
            for offset in (-frame.width, 0.0, frame.width):
                clipped = translate(polygon, xoff=offset).intersection(frame_polygon)
                if isinstance(clipped, (Polygon, MultiPolygon, GeometryCollection)):
                    parts.extend(_polygons(clipped))
        if not parts:
            raise ValueError(f"{feature.label}: no land lies inside the world frame.")
        all_polygons.extend(parts)
        components = tuple(
            LandComponent(
                tuple((float(x), float(y)) for x, y in polygon.exterior.coords),
                tuple(
                    tuple((float(x), float(y)) for x, y in hole.coords)
                    for hole in polygon.interiors
                ),
            )
            for polygon in sorted(parts, key=lambda p: (*p.bounds, p.area))
        )
        land.append(WorldLandView(feature.id, assignment.continent_id, assignment.role, components))
    merged = unary_union(all_polygons)
    if sum(p.area for p in all_polygons) - merged.area > frame.width * frame.height * 1e-12:
        raise ValueError(
            "Assigned land shapes overlap in area, including across the world seam. "
            "Exclude duplicate layers or resolve their outlines in the source."
        )
    summaries = tuple(
        ContinentSummary(
            continent.id,
            continent.name,
            sum(
                component_area_km2(c, frame)
                for f in land
                if f.continent_id == continent.id
                for c in f.components
            ),
            sum(f.continent_id == continent.id for f in land),
            sum(f.continent_id == continent.id and f.role == "island" for f in land),
        )
        for continent in sorted(project.continents, key=lambda c: (c.name.casefold(), c.id))
    )
    return WorldMap(project, tuple(land), summaries, sum(s.area_km2 for s in summaries))
