"""Bounded finished-ground evidence between canonical water-review nodes."""

from collections.abc import Callable
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import pairwise
from math import ceil, hypot, isfinite
from typing import TYPE_CHECKING, Literal, cast

import numpy as np
from numpy.typing import NDArray
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import nearest_points

if TYPE_CHECKING:
    from dmtools.terrain.pipeline.water import MetricBasin

type GroundSampler = Callable[[NDArray[np.float64], NDArray[np.float64]], NDArray[np.float32]]

WATER_SAMPLING_ALGORITHM_ID = "feature-guided-float32-water-checks@2"
MAX_PROFILE_SAMPLES = 65_536
SAMPLE_BATCH_SIZE = 4_096
FEATURE_RADIUS_DIVISOR = 4


@dataclass(frozen=True, slots=True)
class SamplingFeature:
    """Prepared terrain geometry and its nominal and narrowest core radii."""

    geometry: Point | LineString
    influence_radius_km: float
    minimum_radius_km: float

    def __post_init__(self) -> None:
        if (self.geometry.is_empty or not self.geometry.is_valid
                or not all(isfinite(v) for point in self.geometry.coords for v in point)
                or not 0 < self.minimum_radius_km <= self.influence_radius_km
                or not isfinite(self.influence_radius_km)):
            raise ValueError("Water sampling features require finite geometry and positive radii.")


@dataclass(frozen=True, slots=True)
class _FeatureWindow:
    start: float
    end: float
    spacing_km: float
    anchors: tuple[float, ...]


def _feature_windows(
    segment: LineString, features: tuple[SamplingFeature, ...], spacing_km: float,
) -> list[_FeatureWindow]:
    """Clip conservative core corridors; split polylines to retain every crossing.

    Square end caps contain the round influence corridor. Their extra corner
    area can add probes, but cannot omit a nearby core through polygonal circle
    approximation. The corridor is a sampling choice, not a hydraulic boundary.
    """
    windows: list[_FeatureWindow] = []
    for feature in features:
        step = feature.minimum_radius_km / FEATURE_RADIUS_DIVISOR
        if step >= spacing_km:
            continue
        geometry = feature.geometry.normalize()
        parts = ((geometry,) if isinstance(geometry, Point) else
                 tuple(LineString((a, b)) for a, b in pairwise(geometry.coords) if a != b))
        radius = 2 * feature.influence_radius_km
        for part in parts:
            if segment.distance(part) > radius:
                continue
            corridor = (box(part.x - radius, part.y - radius, part.x + radius, part.y + radius)
                        if isinstance(part, Point) else part.buffer(radius, cap_style="square"))
            intersection = segment.intersection(corridor)
            if intersection.is_empty:
                continue
            if not isinstance(intersection, (Point, LineString)):
                raise ValueError("Water sampling requires a single convex feature corridor.")
            bounds = tuple(float(segment.project(Point(p), normalized=True))
                           for p in intersection.coords)
            start, end = min(bounds), max(bounds)
            closest = float(segment.project(nearest_points(segment, part)[0], normalized=True))
            projected = (float(segment.project(Point(p), normalized=True)) for p in part.coords)
            anchors = tuple(t for t in (closest, *projected) if start <= t <= end)
            windows.append(_FeatureWindow(start, end, step, anchors))
    return windows


def _refined_spans(
    steps: int, length_km: float, windows: list[_FeatureWindow], spacing_km: float,
) -> list[tuple[float, float, int]]:
    """Merge overlapping corridors before counting samples; preserve baseline stations."""
    knots = {i / steps for i in range(steps + 1)}
    for window in windows:
        knots.update((window.start, window.end, *window.anchors))
    pending = sorted(windows, key=lambda window: (window.start, window.end, window.spacing_km))
    active: list[tuple[float, float]] = []
    index = 0
    spans: list[tuple[float, float, int]] = []
    for start, end in pairwise(sorted(knots)):
        while index < len(pending) and pending[index].start <= start:
            window = pending[index]
            heappush(active, (window.spacing_km, window.end))
            index += 1
        while active and active[0][1] <= start:
            heappop(active)
        step = active[0][0] if active else spacing_km
        # Keep round-off at a nominal spacing from doubling a baseline interval.
        count = max(1, ceil((end - start) * length_km / step - 1e-12))
        spans.append((start, end, count))
    return spans


@dataclass(frozen=True, slots=True)
class GroundProfile:
    status: Literal["sampled", "budget_exceeded"]
    spacing_limit_km: float
    requested_sample_count: int
    feature_sample_count: int | None
    feature_spacing_limit_km: float | None
    positions_km: tuple[tuple[float, float], ...]
    ground_m: tuple[float, ...]
    minimum_ground_m: float | None
    maximum_ground_m: float | None
    maximum_position_km: tuple[float, float] | None


def sample_ground_profile(
    vertices_km: tuple[tuple[float, float], ...], spacing_limit_km: float,
    sample_ground: GroundSampler, features: tuple[SamplingFeature, ...] = (),
) -> GroundProfile:
    """Include every vertex and bounded intervening samples; never silently coarsen.

    A closed polyline repeats its first point at the end. Duplicate consecutive
    vertices add no samples. Failed budgets retain the requested count but no
    partial evidence, so callers cannot mistake an inspected prefix for clearance.
    """
    if (not vertices_km or not isfinite(spacing_limit_km) or spacing_limit_km <= 0
            or not all(isfinite(v) for point in vertices_km for v in point)):
        raise ValueError("Water sampling requires finite vertices and positive spacing.")
    lengths = tuple(hypot(b[0] - a[0], b[1] - a[1]) for a, b in pairwise(vertices_km))
    spans = tuple(max(2, ceil(length / spacing_limit_km)) if length else 0 for length in lengths)
    baseline_count = 1 + sum(spans)
    if baseline_count > MAX_PROFILE_SAMPLES:
        return GroundProfile("budget_exceeded", spacing_limit_km, baseline_count,
                             None, None, (), (), None, None, None)
    plans: list[list[tuple[float, float, int]]] = []
    feature_spacing: float | None = None
    for (a, b), steps, length in zip(pairwise(vertices_km), spans, lengths, strict=True):
        if not steps:
            plans.append([])
            continue
        windows = _feature_windows(LineString((a, b)), features, spacing_limit_km)
        if windows:
            minimum = min(window.spacing_km for window in windows)
            feature_spacing = minimum if feature_spacing is None else min(feature_spacing, minimum)
        plans.append(_refined_spans(steps, length, windows, spacing_limit_km) if windows else
                     [(0., 1., steps)])
    count = 1 + sum(steps for plan in plans for _, _, steps in plan)
    if count > MAX_PROFILE_SAMPLES:
        return GroundProfile("budget_exceeded", spacing_limit_km, count,
                             None, feature_spacing, (), (), None, None, None)
    positions = np.empty((count, 2), dtype=np.float64)
    positions[0] = vertices_km[0]
    offset = 1
    for (a, b), plan in zip(pairwise(vertices_km), plans, strict=True):
        # Generate each segment as one vectorized block, including every original station.
        fractions = [np.asarray([end]) if steps == 1 else
                     start + (end - start) * np.arange(1, steps + 1, dtype=np.float64) / steps
                     for start, end, steps in plan]
        if not fractions:
            continue
        for fraction, (_, end, _) in zip(fractions, plan, strict=True):
            fraction[-1] = end
        combined = np.concatenate(fractions)
        positions[offset:offset + combined.size] = (np.asarray(a) + combined[:, None]
                                                   * (np.asarray(b) - a))
        positions[offset + combined.size - 1] = b
        offset += combined.size
    ground = np.empty(count, dtype=np.float32)
    for start in range(0, count, SAMPLE_BATCH_SIZE):
        part = positions[start:start + SAMPLE_BATCH_SIZE]
        values = sample_ground(part[:, 0], part[:, 1])
        if values.shape != (len(part),) or not np.all(np.isfinite(values)):
            raise ValueError("Water sampling requires finite ground at every requested point.")
        ground[start:start + len(part)] = values
    if not np.all(np.isfinite(ground)):
        raise ValueError("Water sampling requires finite Float32 ground.")
    maximum = int(np.argmax(ground))
    return GroundProfile(
        "sampled", spacing_limit_km, count, count - baseline_count, feature_spacing,
        tuple((float(x), float(y)) for x, y in positions), tuple(float(v) for v in ground),
        float(np.min(ground)), float(ground[maximum]),
        (float(positions[maximum, 0]), float(positions[maximum, 1])))


@dataclass(frozen=True, slots=True)
class ShorelineReview:
    profile: GroundProfile
    opening_radius_km: float
    low_sample_count: int
    uncontrolled_low_sample_count: int
    uncontrolled_low_sample_indices: tuple[int, ...]


def review_shorelines(
    basins: tuple[MetricBasin, ...], spacing_limit_km: float, opening_radius_km: float,
    sample_ground: GroundSampler, features: tuple[SamplingFeature, ...] = (),
) -> tuple[ShorelineReview | None, ...]:
    """Review lake polygon boundaries, including low ground missed by coarse wet nodes."""
    reviews: list[ShorelineReview | None] = []
    for basin in basins:
        level = basin.source.water_level_m
        if level is None:
            reviews.append(None)
            continue
        # Canonical ring orientation/start avoid shifting samples when equivalent rings are redrawn.
        normalized = cast(Polygon, basin.geometry.normalize())
        vertices = tuple((float(x), float(y)) for x, y in normalized.exterior.coords)
        profile = sample_ground_profile(vertices, spacing_limit_km, sample_ground, features)
        low = np.asarray(profile.ground_m, dtype=np.float64) < level - .01
        allowed = np.zeros(low.size, dtype=np.bool_)
        radius = 0. if basin.outlet_km is None else opening_radius_km
        if basin.outlet_km is not None and low.size:
            points = np.asarray(profile.positions_km)
            # Round-off at the declared radius must not turn an endpoint into a new opening.
            allowed = np.hypot(points[:, 0] - basin.outlet_km[0],
                               points[:, 1] - basin.outlet_km[1]) <= radius + 1e-9 * radius
        uncontrolled = tuple(int(index) for index in np.flatnonzero(low & ~allowed))
        reviews.append(ShorelineReview(profile, radius, int(np.count_nonzero(low)),
                                       len(uncontrolled), uncontrolled))
    return tuple(reviews)
