"""Rounded slab clipping for research bounds along affine profile paths."""

from dataclasses import dataclass, replace
from math import isfinite
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from benchmarks.noise_intervals import (
    MAX_BOXES,
    MAX_CELLS,
    MAX_SCALED_COORDINATE,
    Interval,
    NoiseEnclosure,
    NoiseParameters,
    OctavePlan,
    enclose_plans,
    validate_bound_controls,
)

PROFILE_METHOD_ID = "rounded-slab-noise-profile@1"
HYBRID_METHOD_ID = "rounded-hybrid-noise-profile@1"
MAX_SLABS = 262_144
type ProfileGeometry = Literal["slabs", "hybrid"]


@dataclass(frozen=True, slots=True)
class NoisePath:
    """Exactly the binary64 operations start + fraction * delta, in that order."""

    start_km: tuple[float, float]
    delta_km: tuple[float, float]

    def __post_init__(self) -> None:
        for point in (self.start_km, self.delta_km):
            if len(point) != 2 or any(
                type(x) not in (int, float) or not isfinite(x) for x in point
            ):
                raise ValueError("Noise path coordinates must be finite pairs.")


def _axis_range(start: float, delta: float, fractions: Interval, spacing: float) -> Interval:
    # For fixed finite start/delta and positive spacing, the rounded affine
    # coordinate is monotone in the binary64 parameter. Actual endpoint
    # evaluation bounds its full range without artificial coordinate padding.
    first = (start + fractions.low * delta) / spacing
    last = (start + fractions.high * delta) / spacing
    return Interval(np.minimum(first, last), np.maximum(first, last))


def _rounding_preimage(values: Interval) -> Interval:
    # If RN(x) lies in [a,b], x lies between the adjacent floats outside [a,b].
    return Interval(np.nextafter(values.low, -np.inf), np.nextafter(values.high, np.inf))


def slab_fractions(
    start: float, delta: float, spacing: float, indices: NDArray[np.int64], original: Interval
) -> Interval:
    """Conservatively invert each rounded path/division operation for a grid slab."""
    if delta == 0.0:
        return original
    origins = indices.astype(np.float64)
    scaled = _rounding_preimage(Interval(origins, origins + 1.0))
    coordinates = scaled.multiply(Interval.point(spacing))
    product = _rounding_preimage(coordinates).subtract(Interval.point(start))
    unrounded_product = _rounding_preimage(product)
    if delta < 0.0:
        unrounded_product = Interval(-unrounded_product.high, -unrounded_product.low)
    fractions = unrounded_product.divide_positive(abs(delta))
    return Interval(
        np.maximum(original.low, fractions.low), np.minimum(original.high, fractions.high)
    )


@dataclass(frozen=True, slots=True)
class _SlabPlan:
    spacing: float
    first: NDArray[np.int64]
    last: NDArray[np.int64]
    count: int


def _cell_plan(path: NoisePath, fractions: Interval, plan: _SlabPlan, major: int) -> OctavePlan:
    owners = np.repeat(np.arange(len(plan.first), dtype=np.int64), plan.last - plan.first + 1)
    indices = np.concatenate(
        [
            np.arange(int(a), int(b) + 1, dtype=np.int64)
            for a, b in zip(plan.first, plan.last, strict=True)
        ]
    )
    clipped = slab_fractions(
        path.start_km[major],
        path.delta_km[major],
        plan.spacing,
        indices,
        Interval(fractions.low[owners], fractions.high[owners]),
    )
    active = clipped.low <= clipped.high
    clipped = Interval(clipped.low[active], clipped.high[active])
    owners, indices = owners[active], indices[active]
    x = _axis_range(path.start_km[0], path.delta_km[0], clipped, plan.spacing)
    y = _axis_range(path.start_km[1], path.delta_km[1], clipped, plan.spacing)
    low, high = np.column_stack((x.low, y.low)), np.column_stack((x.high, y.high))
    # Keep the selected major slab; minor cells cover its complete rounded path range.
    low[:, major] = np.maximum(low[:, major], indices)
    high[:, major] = np.minimum(high[:, major], indices + 1)
    active = np.all(low <= high, axis=1)
    low, high, indices, owners = low[active], high[active], indices[active], owners[active]
    if len(np.unique(owners)) != len(fractions.low):
        raise RuntimeError("Noise slab planning failed to cover every parameter interval.")
    first, last = np.floor(low).astype(np.int64), np.floor(high).astype(np.int64)
    first[:, major] = last[:, major] = indices
    count = sum(int(b[1 - major]) - int(a[1 - major]) + 1 for a, b in zip(first, last, strict=True))
    return OctavePlan(
        Interval(low[:, 0], high[:, 0]), Interval(low[:, 1], high[:, 1]), first, last, count, owners
    )


@dataclass(frozen=True, slots=True)
class _GeometryPlan:
    x: Interval
    y: Interval
    first: NDArray[np.int64]
    last: NDArray[np.int64]
    clipped: NDArray[np.bool_]
    slabs: _SlabPlan


def _geometry_cells(
    path: NoisePath, fractions: Interval, plan: _GeometryPlan, major: int
) -> OctavePlan:
    clipped_owners = np.flatnonzero(plan.clipped)
    rectangle_owners = np.flatnonzero(~plan.clipped)
    parts: list[OctavePlan] = []
    if rectangle_owners.size:
        owners = rectangle_owners
        first, last = plan.first[owners], plan.last[owners]
        count = sum(
            (int(b[0]) - int(a[0]) + 1) * (int(b[1]) - int(a[1]) + 1)
            for a, b in zip(first, last, strict=True)
        )
        parts.append(
            OctavePlan(
                Interval(plan.x.low[owners], plan.x.high[owners]),
                Interval(plan.y.low[owners], plan.y.high[owners]),
                first,
                last,
                count,
                owners,
            )
        )
    if clipped_owners.size:
        clipped = _cell_plan(
            path,
            Interval(fractions.low[clipped_owners], fractions.high[clipped_owners]),
            plan.slabs,
            major,
        )
        parts.append(replace(clipped, owners=clipped_owners[clipped.owners]))
    if len(parts) == 1:
        return parts[0]
    return OctavePlan(
        Interval(
            np.concatenate([p.x.low for p in parts]), np.concatenate([p.x.high for p in parts])
        ),
        Interval(
            np.concatenate([p.y.low for p in parts]), np.concatenate([p.y.high for p in parts])
        ),
        np.concatenate([p.first for p in parts]),
        np.concatenate([p.last for p in parts]),
        sum(p.cell_count for p in parts),
        np.concatenate([p.owners for p in parts]),
    )


def enclose_noise_profile(
    path: NoisePath,
    spans: NDArray[np.float64],
    parameters: NoiseParameters,
    *,
    amplitude_m: float = 1000.0,
    offset_m: float = 2000.0,
    max_cells: int = MAX_CELLS,
    max_slabs: int = MAX_SLABS,
    geometry: ProfileGeometry = "slabs",
) -> NoiseEnclosure:
    """Enclose the original rounded path, with complete strip/cell preflight.

    Hybrid geometry uses a rectangle when the minor axis touches at most two
    cells; elsewhere it clips major strips. Selection uses geometry, not heights.
    Zero remaining budgets support cumulative refinement without a fresh allowance.
    """
    intervals = np.asarray(spans, dtype=np.float64)
    if (
        intervals.ndim != 2
        or intervals.shape[1] != 2
        or not 1 <= len(intervals) <= MAX_BOXES
        or not np.all(np.isfinite(intervals))
        or np.any(intervals[:, 0] > intervals[:, 1])
        or np.any(intervals < 0.0)
        or np.any(intervals > 1.0)
    ):
        raise ValueError("Noise spans must be 1-65536 ordered parameter pairs within [0,1].")
    validate_bound_controls(amplitude_m, offset_m, MAX_CELLS)
    if type(max_cells) is not int or not 0 <= max_cells <= MAX_CELLS:
        raise ValueError("Noise cell budget must be an integer from 0 to 262144.")
    if type(max_slabs) is not int or not 0 <= max_slabs <= MAX_SLABS:
        raise ValueError("Noise slab budget must be an integer from 0 to 262144.")
    if geometry not in ("slabs", "hybrid"):
        raise ValueError("Unknown noise profile geometry.")
    fractions = Interval(intervals[:, 0], intervals[:, 1])
    major = 0 if abs(path.delta_km[0]) >= abs(path.delta_km[1]) else 1
    geometry_plans: list[_GeometryPlan] = []
    with np.errstate(over="ignore", under="ignore"):
        for octave in range(parameters.detail_levels):
            spacing = parameters.largest_feature_km / float(1 << octave)
            x = _axis_range(path.start_km[0], path.delta_km[0], fractions, spacing)
            y = _axis_range(path.start_km[1], path.delta_km[1], fractions, spacing)
            extrema = np.column_stack((x.low, y.low, x.high, y.high))
            if not np.all(np.isfinite(extrema)) or np.any(np.abs(extrema) > MAX_SCALED_COORDINATE):
                return NoiseEnclosure("coordinate_range_exceeded", None, 0)
            first = np.floor(extrema[:, :2]).astype(np.int64)
            last = np.floor(extrema[:, 2:]).astype(np.int64)
            clipped = (
                np.ones(len(intervals), dtype=np.bool_)
                if geometry == "slabs"
                else last[:, 1 - major] - first[:, 1 - major] > 1
            )
            a, b = first[clipped, major], last[clipped, major]
            count = sum(int(hi) - int(lo) + 1 for lo, hi in zip(a, b, strict=True))
            geometry_plans.append(
                _GeometryPlan(x, y, first, last, clipped, _SlabPlan(spacing, a, b, count))
            )
    requested_slabs = sum(p.slabs.count for p in geometry_plans)
    clipped_count = sum(int(np.count_nonzero(p.clipped)) for p in geometry_plans)
    rectangle_count = len(intervals) * parameters.detail_levels - clipped_count
    if requested_slabs > max_slabs:
        return NoiseEnclosure(
            "slab_budget_exceeded",
            None,
            0,
            requested_slab_count=requested_slabs,
            rectangle_plan_count=rectangle_count,
            clipped_plan_count=clipped_count,
        )
    # Wide inverse preimages can overflow before intersection with [0,1].
    with np.errstate(over="ignore", under="ignore"):
        plans = [_geometry_cells(path, fractions, plan, major) for plan in geometry_plans]
    result = enclose_plans(
        plans,
        parameters,
        len(intervals),
        amplitude_m=amplitude_m,
        offset_m=offset_m,
        max_cells=max_cells,
    )
    return replace(
        result,
        requested_slab_count=requested_slabs,
        rectangle_plan_count=rectangle_count,
        clipped_plan_count=clipped_count,
    )


def ordered_rise_upper_bound(field: Interval) -> float:
    """Bound later-minus-earlier height over complete intervals in path order.

    Rows must cover the path in order without gaps; extrema within each row
    remain unordered, so its own minimum must participate in the prefix bound.
    """
    if (
        field.low.ndim != 1
        or field.low.shape != field.high.shape
        or not field.low.size
        or not np.all(np.isfinite(field.low))
        or not np.all(np.isfinite(field.high))
        or np.any(field.low > field.high)
    ):
        raise ValueError("Ordered rise needs finite ordered field intervals.")
    # Including this interval's minimum covers unsampled earlier positions in it.
    rises = np.nextafter(field.high - np.minimum.accumulate(field.low), np.inf)
    return max(0.0, float(np.max(rises)))
