"""Bounded bicubic reconstruction of fixed canonical shaping fields.

Shared nodal derivatives remove interpolation creases. Bernstein control bounds
limit each patch to its corner range; optional bilinear ceilings remain authoritative.
This reconstructs a field, not a new flow network or additional procedural detail.
"""

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

type FloatArray = NDArray[np.float64]


def _monotone_slopes(values: FloatArray, positions: FloatArray, axis: int) -> FloatArray:
    data = np.moveaxis(values, axis, 0)
    spans = np.diff(positions).reshape((-1, 1))
    gradients = np.diff(data, axis=0) / spans
    slopes = np.zeros_like(data)
    if data.shape[0] == 2:
        slopes[:] = gradients[0]
    else:
        before, after = gradients[:-1], gradients[1:]
        same_sign = (np.sign(before) == np.sign(after)) & (before != 0) & (after != 0)
        # Fritsch-Butland harmonic slopes, evaluated without dividing by zero.
        w1, w2 = 2 * spans[1:] + spans[:-1], spans[1:] + 2 * spans[:-1]
        numerator = (w1 + w2) * before * after
        denominator = w1 * after + w2 * before
        np.divide(numerator, denominator, out=slopes[1:-1], where=same_sign)
        for index, first, second, h0, h1 in (
            (0, gradients[0], gradients[1], spans[0], spans[1]),
            (-1, gradients[-1], gradients[-2], spans[-1], spans[-2]),
        ):
            end = ((2 * h0 + h1) * first - h0 * second) / (h0 + h1)
            end = np.where(np.sign(end) == np.sign(first), end, 0.)
            slopes[index] = np.sign(end) * np.minimum(np.abs(end), 3 * np.abs(first))
    return np.moveaxis(slopes, 0, axis)


def _basis(t: FloatArray) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    t2, t3 = t * t, t * t * t
    return 2*t3 - 3*t2 + 1, -2*t3 + 3*t2, t3 - 2*t2 + t, t3 - t2


@dataclass(frozen=True, slots=True)
class BoundedBicubicGrid:
    """Immutable, pointwise reconstruction on an increasing rectilinear node grid.

    The unlimited-ceiling surface is C1 at shared cell edges in exact arithmetic.
    Bounding derivatives is shared by adjacent patches, not a per-query limiter.
    Range/ceiling clipping also contains floating-point roundoff. An active ceiling
    can retain its own slope discontinuity. Queries outside the frame clamp to it.
    """

    x: FloatArray
    y: FloatArray
    values: FloatArray
    ceiling: FloatArray | None = None
    _dx: FloatArray = field(init=False, repr=False)
    _dy: FloatArray = field(init=False, repr=False)
    _dxy: FloatArray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if (self.x.ndim != 1 or self.y.ndim != 1 or min(self.x.size, self.y.size) < 2
                or not np.all(np.isfinite(self.x)) or not np.all(np.isfinite(self.y))
                or np.any(np.diff(self.x) <= 0) or np.any(np.diff(self.y) <= 0)):
            raise ValueError("Reconstruction axes must be finite and strictly increasing.")
        if self.values.shape != (self.y.size, self.x.size) or not np.all(np.isfinite(self.values)):
            raise ValueError("Reconstruction needs finite values at every grid node.")
        if self.ceiling is not None and (
            self.ceiling.shape != self.values.shape or not np.all(np.isfinite(self.ceiling))
            or np.any(self.values > self.ceiling)
        ):
            raise ValueError("Reconstruction ceiling must cover every nodal value.")
        # Own the prepared inputs so later caller mutations cannot stale the derivatives.
        for name in ("x", "y", "values", "ceiling"):
            original = getattr(self, name)
            if original is not None:
                copied = np.array(original, dtype=np.float64, copy=True)
                copied.flags.writeable = False
                object.__setattr__(self, name, copied)
        dx = _monotone_slopes(self.values, self.x, axis=1)
        dy = _monotone_slopes(self.values, self.y, axis=0)
        dxy = (np.gradient(dx, self.y, axis=0) + np.gradient(dy, self.x, axis=1)) * .5
        scale = np.ones_like(self.values)
        hx, hy = np.diff(self.x)[None, :], np.diff(self.y)[:, None]
        corners = (self.values[:-1, :-1], self.values[:-1, 1:],
                   self.values[1:, :-1], self.values[1:, 1:])
        lower = np.minimum(np.minimum(corners[0], corners[1]),
                           np.minimum(corners[2], corners[3]))
        upper = np.maximum(np.maximum(corners[0], corners[1]),
                           np.maximum(corners[2], corners[3]))
        height, width = self.values.shape
        for row in (0, 1):
            for column in (0, 1):
                part = (slice(row, height - 1 + row), slice(column, width - 1 + column))
                centre = self.values[part]
                sx, sy = (1 - 2*column) * hx / 3, (1 - 2*row) * hy / 3
                bx, by = dx[part] * sx, dy[part] * sy
                # Every non-corner Bezier coefficient belongs to one corner:
                # two edge controls and one interior control. Scale all derivatives
                # at that node by the strictest requirement of ALL adjacent cells.
                for offset in (bx, by, bx + by + dxy[part] * sx * sy):
                    margin = np.where(offset >= 0, upper - centre, centre - lower)
                    allowed = np.divide(margin, np.abs(offset), out=np.ones_like(offset),
                                        where=offset != 0)
                    np.minimum(scale[part], allowed, out=scale[part])
        scale = np.clip(scale, 0., 1.)
        for name, derivative in (("_dx", dx), ("_dy", dy), ("_dxy", dxy)):
            derivative *= scale
            derivative.flags.writeable = False
            object.__setattr__(self, name, derivative)

    def sample(self, x: FloatArray, y: FloatArray) -> FloatArray:
        if x.shape != y.shape or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
            raise ValueError("Reconstruction queries must be finite and equally shaped.")
        x, y = np.clip(x, self.x[0], self.x[-1]), np.clip(y, self.y[0], self.y[-1])
        columns = np.clip(np.searchsorted(self.x, x, side="right") - 1, 0, self.x.size - 2)
        rows = np.clip(np.searchsorted(self.y, y, side="right") - 1, 0, self.y.size - 2)
        hx, hy = self.x[columns + 1] - self.x[columns], self.y[rows + 1] - self.y[rows]
        tx, ty = (x - self.x[columns]) / hx, (y - self.y[rows]) / hy
        ax, bx, cx, dx = _basis(tx)
        ay, by, cy, dy = _basis(ty)
        v00, v01 = self.values[rows, columns], self.values[rows, columns + 1]
        v10, v11 = self.values[rows + 1, columns], self.values[rows + 1, columns + 1]
        top = ax*v00 + bx*v01 + hx*(cx*self._dx[rows, columns]
                                   + dx*self._dx[rows, columns + 1])
        bottom = ax*v10 + bx*v11 + hx*(cx*self._dx[rows + 1, columns]
                                      + dx*self._dx[rows + 1, columns + 1])
        top_dy = (ax*self._dy[rows, columns] + bx*self._dy[rows, columns + 1]
                  + hx*(cx*self._dxy[rows, columns] + dx*self._dxy[rows, columns + 1]))
        bottom_dy = (ax*self._dy[rows + 1, columns] + bx*self._dy[rows + 1, columns + 1]
                     + hx*(cx*self._dxy[rows + 1, columns] + dx*self._dxy[rows + 1, columns + 1]))
        result = ay*top + by*bottom + hy*(cy*top_dy + dy*bottom_dy)
        lower = np.minimum(np.minimum(v00, v01), np.minimum(v10, v11))
        upper = np.maximum(np.maximum(v00, v01), np.maximum(v10, v11))
        result = np.clip(result, lower, upper)
        if self.ceiling is not None:
            ceiling = self.ceiling
            top_limit = ceiling[rows, columns]*(1-tx) + ceiling[rows, columns + 1]*tx
            bottom_limit = ceiling[rows + 1, columns]*(1-tx) + ceiling[rows + 1, columns + 1]*tx
            result = np.minimum(result, top_limit*(1-ty) + bottom_limit*ty)
        return result
