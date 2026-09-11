"""Bounded finished-ground evidence between canonical water-review nodes."""

from collections.abc import Callable
from dataclasses import dataclass
from itertools import pairwise
from math import ceil, hypot, isfinite
from typing import TYPE_CHECKING, Literal, cast

import numpy as np
from numpy.typing import NDArray
from shapely.geometry import Polygon

if TYPE_CHECKING:
    from dmtools.terrain.pipeline.water import MetricBasin

type GroundSampler = Callable[[NDArray[np.float64], NDArray[np.float64]], NDArray[np.float32]]

WATER_SAMPLING_ALGORITHM_ID = "quarter-grid-float32-water-checks@1"
MAX_PROFILE_SAMPLES = 65_536
SAMPLE_BATCH_SIZE = 4_096


@dataclass(frozen=True, slots=True)
class GroundProfile:
    status: Literal["sampled", "budget_exceeded"]
    spacing_limit_km: float
    requested_sample_count: int
    positions_km: tuple[tuple[float, float], ...]
    ground_m: tuple[float, ...]
    minimum_ground_m: float | None
    maximum_ground_m: float | None
    maximum_position_km: tuple[float, float] | None


def sample_ground_profile(
    vertices_km: tuple[tuple[float, float], ...], spacing_limit_km: float,
    sample_ground: GroundSampler,
) -> GroundProfile:
    """Include every vertex and bounded intervening samples; never silently coarsen.

    A closed polyline repeats its first point at the end. Duplicate consecutive
    vertices add no samples. Failed budgets retain the requested count but no
    partial evidence, so callers cannot mistake an inspected prefix for clearance.
    """
    if (not vertices_km or not isfinite(spacing_limit_km) or spacing_limit_km <= 0
            or not all(isfinite(v) for point in vertices_km for v in point)):
        raise ValueError("Water sampling requires finite vertices and positive spacing.")
    spans = tuple(max(2, ceil(length / spacing_limit_km)) if length else 0
                  for a, b in pairwise(vertices_km)
                  for length in (hypot(b[0] - a[0], b[1] - a[1]),))
    count = 1 + sum(spans)
    if count > MAX_PROFILE_SAMPLES:
        return GroundProfile("budget_exceeded", spacing_limit_km, count, (), (), None, None, None)
    positions = np.empty((count, 2), dtype=np.float64)
    positions[0] = vertices_km[0]
    offset = 1
    for (a, b), steps in zip(pairwise(vertices_km), spans, strict=True):
        if not steps:
            continue
        fraction = np.arange(1, steps + 1, dtype=np.float64) / steps
        positions[offset:offset + steps] = (np.asarray(a) + fraction[:, None]
                                            * (np.asarray(b) - a))
        positions[offset + steps - 1] = b  # Preserve each exact authored vertex.
        offset += steps
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
    return GroundProfile("sampled", spacing_limit_km, count,
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
    sample_ground: GroundSampler,
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
        profile = sample_ground_profile(vertices, spacing_limit_km, sample_ground)
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
