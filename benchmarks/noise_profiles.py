"""Rounded slab clipping for research bounds along affine profile paths."""

from dataclasses import dataclass, replace
from math import isfinite

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
MAX_SLABS = 262_144


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


def enclose_noise_profile(
    path: NoisePath,
    spans: NDArray[np.float64],
    parameters: NoiseParameters,
    *,
    amplitude_m: float = 1000.0,
    offset_m: float = 2000.0,
    max_cells: int = MAX_CELLS,
    max_slabs: int = MAX_SLABS,
) -> NoiseEnclosure:
    """Bound each supplied parameter span on a rounded affine path, not its full box.

    All slab work is counted before slab arrays, and all cell work before lattice
    evaluation. Arithmetic assumes binary64 round-to-nearest with gradual underflow.
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
    validate_bound_controls(amplitude_m, offset_m, max_cells)
    if type(max_slabs) is not int or not 1 <= max_slabs <= MAX_SLABS:
        raise ValueError("Noise slab budget must be an integer from 1 to 262144.")
    fractions = Interval(intervals[:, 0], intervals[:, 1])
    major = 0 if abs(path.delta_km[0]) >= abs(path.delta_km[1]) else 1
    slabs: list[_SlabPlan] = []
    with np.errstate(over="ignore", under="ignore"):
        for octave in range(parameters.detail_levels):
            spacing = parameters.largest_feature_km / float(1 << octave)
            axes = tuple(
                _axis_range(path.start_km[axis], path.delta_km[axis], fractions, spacing)
                for axis in (0, 1)
            )
            extrema = np.column_stack((axes[0].low, axes[1].low, axes[0].high, axes[1].high))
            if not np.all(np.isfinite(extrema)) or np.any(np.abs(extrema) > MAX_SCALED_COORDINATE):
                return NoiseEnclosure("coordinate_range_exceeded", None, 0)
            first = np.floor(axes[major].low).astype(np.int64)
            last = np.floor(axes[major].high).astype(np.int64)
            count = sum(int(b) - int(a) + 1 for a, b in zip(first, last, strict=True))
            slabs.append(_SlabPlan(spacing, first, last, count))
    requested_slabs = sum(plan.count for plan in slabs)
    if requested_slabs > max_slabs:
        return NoiseEnclosure("slab_budget_exceeded", None, 0, requested_slab_count=requested_slabs)
    # Wide inverse preimages can overflow before intersection with [0,1].
    with np.errstate(over="ignore", under="ignore"):
        plans = [_cell_plan(path, fractions, plan, major) for plan in slabs]
    result = enclose_plans(
        plans,
        parameters,
        len(intervals),
        amplitude_m=amplitude_m,
        offset_m=offset_m,
        max_cells=max_cells,
    )
    return replace(result, requested_slab_count=requested_slabs)


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
