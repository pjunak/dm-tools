"""Bounded network-led bilinear surface fit with explicit inequalities.

This is a candidate generation construction, not a repair of a completed DEM.
Channel descent is constrained on both ends of every cell-crossing segment:
a bilinear field restricted to a straight line is quadratic, so its derivative
is affine. Nodal bounds also bound the interpolated field by convexity.
"""

from dataclasses import dataclass
from importlib import import_module
from itertools import pairwise
from math import isfinite
from time import perf_counter
from typing import Any

import numpy as np
from numpy.typing import NDArray

from benchmarks.evolution.metrics import sample_grid
from benchmarks.evolution.network import RiverNetwork
from benchmarks.evolution.paths import FloatArray
from dmtools.terrain.domain.evolution import EvolutionGrid

# SciPy currently has no installed type stubs in the base environment. Keep its
# dynamic API at this numeric boundary; validate all incoming and delivered arrays.
sparse: Any = import_module("scipy.sparse")
optimize: Any = import_module("scipy.optimize")

CONSTRAINED_MODEL_ID = "network-constrained-bilinear@1"


class InfeasibleSurface(ValueError):
    """No admitted solution; hard constraints are never softened automatically."""


@dataclass(frozen=True, slots=True)
class HardHeights:
    points_m: FloatArray
    heights_m: FloatArray

    def __post_init__(self) -> None:
        xy, z = (
            np.array(self.points_m, dtype=np.float64),
            np.array(self.heights_m, dtype=np.float64),
        )
        if (
            z.ndim != 1
            or xy.shape != (len(z), 2)
            or len(z) > 4096
            or not np.all(np.isfinite(xy))
            or not np.all(np.isfinite(z))
        ):
            raise ValueError(
                "Hard heights need bounded, finite matching coordinates and elevations."
            )
        for name, value in (("points_m", xy), ("heights_m", z)):
            value.flags.writeable = False
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class FittedSurface:
    grid: EvolutionGrid
    ground_m: NDArray[np.float32]
    diagnostics: dict[str, Any]

    def __post_init__(self) -> None:
        values = np.array(self.ground_m, copy=True)
        if (
            values.shape != self.grid.shape
            or values.dtype != np.float32
            or not np.all(np.isfinite(values))
        ):
            raise ValueError("A fitted surface needs finite Float32 grid elevations.")
        values.flags.writeable = False
        object.__setattr__(self, "ground_m", values)

    def sample(self, x: FloatArray, y: FloatArray) -> NDArray[np.float32]:
        return sample_grid(self.ground_m.astype(np.float64), self.grid, x, y)


def weights(grid: EvolutionGrid, xy: FloatArray) -> Any:
    if (
        xy.ndim != 2
        or xy.shape[1] != 2
        or not np.all(np.isfinite(xy))
        or np.any(xy < 0)
        or np.any(xy[:, 0] > grid.width_m)
        or np.any(xy[:, 1] > grid.height_m)
    ):
        raise ValueError("Surface constraint points must lie inside the metric domain.")
    uv = xy / grid.spacing_m
    c = np.minimum(uv[:, 0].astype(np.int64), grid.shape[1] - 2)
    r = np.minimum(uv[:, 1].astype(np.int64), grid.shape[0] - 2)
    u, v = uv[:, 0] - c, uv[:, 1] - r
    ids = r * grid.shape[1] + c
    columns = np.stack((ids, ids + 1, ids + grid.shape[1], ids + grid.shape[1] + 1), axis=-1)
    values = np.stack(((1 - u) * (1 - v), u * (1 - v), (1 - u) * v, u * v), axis=-1)
    return sparse.csr_matrix(
        (values.ravel(), (np.repeat(np.arange(len(xy)), 4), columns.ravel())),
        shape=(len(xy), grid.shape[0] * grid.shape[1]),
    )


def channel_constraints(
    grid: EvolutionGrid, network: RiverNetwork, minimum_slope: float
) -> tuple[Any, FloatArray]:
    if isinstance(minimum_slope, bool) or not isfinite(minimum_slope) or minimum_slope < 0:
        raise ValueError("Minimum channel slope must be finite and nonnegative.")
    weights(grid, network.coordinates_m)
    row_indices: list[int] = []
    column_indices: list[int] = []
    coefficients: list[float] = []
    lengths: list[float] = []
    for source in np.flatnonzero(network.required):
        a, b = network.coordinates_m[[source, network.receivers[source]]]
        delta = b - a
        length = float(np.hypot(delta[0], delta[1]))
        crossings = [0.0, 1.0]
        for axis, extent in ((0, grid.width_m), (1, grid.height_m)):
            if delta[axis] != 0:
                t = (
                    np.arange(1, round(extent / grid.spacing_m)) * grid.spacing_m - a[axis]
                ) / delta[axis]
                crossings.extend(t[(t > 0) & (t < 1)].tolist())
        ts = np.unique(crossings)
        for start, stop in pairwise(ts):
            span = (stop - start) * length
            if span < 1.0e-7:
                continue  # Coincident grid crossings at floating-point roundoff scale.
            midpoint = (a + 0.5 * (start + stop) * delta) / grid.spacing_m
            c = min(int(midpoint[0]), grid.shape[1] - 2)
            r = min(int(midpoint[1]), grid.shape[0] - 2)
            ids = (
                r * grid.shape[1] + c,
                r * grid.shape[1] + c + 1,
                (r + 1) * grid.shape[1] + c,
                (r + 1) * grid.shape[1] + c + 1,
            )
            du, dv = delta * (stop - start) / grid.spacing_m
            if len(lengths) + 2 > 32768:
                raise ValueError("Network exceeds 32,768 cell derivative constraints.")
            for t in (start, stop):
                u, v = (a + t * delta) / grid.spacing_m - (c, r)
                derivative = (
                    -du * (1 - v) - dv * (1 - u),
                    du * (1 - v) - dv * u,
                    -du * v + dv * (1 - u),
                    du * v + dv * u,
                )
                row_indices.extend([len(lengths)] * 4)
                column_indices.extend(ids)
                coefficients.extend(float(value) for value in derivative)
                lengths.append(span)
    matrix = sparse.csr_matrix(
        (coefficients, (row_indices, column_indices)),
        shape=(len(lengths), grid.shape[0] * grid.shape[1]),
    )
    return matrix, np.asarray(lengths, dtype=np.float64)


def _float32_bounds(lower: FloatArray, upper: FloatArray) -> tuple[FloatArray, FloatArray]:
    lo, hi = lower.astype(np.float32), upper.astype(np.float32)
    lo = np.where(lo.astype(np.float64) < lower, np.nextafter(lo, np.float32(np.inf)), lo)
    hi = np.where(hi.astype(np.float64) > upper, np.nextafter(hi, np.float32(-np.inf)), hi)
    if np.any(lo > hi):
        raise InfeasibleSurface("No Float32 value satisfies one or more height bounds.")
    return lo.astype(np.float64), hi.astype(np.float64)


def fit(
    grid: EvolutionGrid,
    network: RiverNetwork,
    source_m: FloatArray,
    cut_limit_m: FloatArray,
    target_m: FloatArray,
    hard: HardHeights,
    *,
    minimum_slope: float = 0.0005,
    maximum_seconds: float = 20.0,
) -> FittedSurface:
    n = grid.shape[0] * grid.shape[1]
    if n > 16384:
        raise ValueError("Constrained comparison is limited to 16,384 physical grid nodes.")
    for value in (source_m, cut_limit_m, target_m):
        if (
            value.shape != grid.shape
            or not np.all(np.isfinite(value))
            or np.any(np.abs(value) > 1.0e6)
        ):
            raise ValueError("Surface arrays must be finite, bounded and match the process grid.")
    if (
        np.any(cut_limit_m < 0)
        or isinstance(maximum_seconds, bool)
        or not isfinite(maximum_seconds)
        or not 0 < maximum_seconds <= 120
    ):
        raise ValueError("Surface cut limits and solver time budget are invalid.")
    lower, upper = _float32_bounds((source_m - cut_limit_m).ravel(), source_m.ravel())
    equality = weights(grid, hard.points_m)
    required_low = np.asarray(equality @ lower).ravel()
    required_high = np.asarray(equality @ upper).ravel()
    conflicts = np.flatnonzero(
        (hard.heights_m < required_low - 1.0e-7) | (hard.heights_m > required_high + 1.0e-7)
    )
    if conflicts.size:
        raise InfeasibleSurface(
            f"Hard height indices outside local cut/no-fill bounds: {conflicts.tolist()}"
        )
    descent, lengths = channel_constraints(grid, network, minimum_slope)
    # Only nodes participating in a hard constraint need numerical optimization.
    # Other nodes have the exact minimizer: the target clipped to their bounds.
    active = np.asarray(abs(descent).sum(axis=0) + abs(equality).sum(axis=0)).ravel() > 0
    active &= lower < upper
    if np.count_nonzero(active) > 2048:
        raise ValueError("Constrained comparison is limited to 2,048 free constrained nodes.")
    solution = np.clip(target_m.ravel(), lower, upper)
    solution[active] = 0.0
    a = descent[:, active]
    b = -minimum_slope * lengths - descent @ solution
    eq = equality[:, active]
    rhs = hard.heights_m - equality @ solution
    moving = np.asarray(abs(a).sum(axis=1)).ravel() > 0
    moving_eq = np.asarray(abs(eq).sum(axis=1)).ravel() > 0
    if np.any(b[~moving] < -1.0e-8) or np.any(np.abs(rhs[~moving_eq]) > 1.0e-8):
        raise InfeasibleSurface("Fixed ground and required channel heights are incompatible.")
    a, b = a[moving], b[moving]
    eq, rhs = eq[moving_eq], rhs[moving_eq]
    started = perf_counter()
    iterations, message = 0, "All constrained heights are fixed."
    if np.any(active):
        # Establish feasibility separately. An impossible hard constraint is not
        # an invitation to change a height, enlarge a cut limit or add fill.
        admitted: Any = optimize.linprog(
            np.zeros(np.count_nonzero(active)),
            A_ub=a,
            b_ub=b,
            A_eq=eq,
            b_eq=rhs,
            bounds=np.column_stack((lower[active], upper[active])),
            method="highs",
            options={
                "time_limit": maximum_seconds,
                "primal_feasibility_tolerance": 1.0e-8,
                "dual_feasibility_tolerance": 1.0e-8,
            },
        )
        if admitted.status == 2:
            raise InfeasibleSurface(
                "Channel descent, hard heights and local cut bounds are incompatible."
            )
        if not admitted.success:
            raise RuntimeError(f"Surface fit did not complete: {admitted.message}")
        wanted = target_m.ravel()[active]

        def time_limit(*args: Any) -> None:
            if perf_counter() - started > maximum_seconds:
                raise RuntimeError("Surface fit did not complete: solver time budget reached.")

        time_limit()
        constraints: list[Any] = []
        if len(b):
            constraints.append(optimize.LinearConstraint(a, -np.inf, b))
        if len(rhs):
            constraints.append(optimize.LinearConstraint(eq, rhs, rhs))

        # A strictly convex objective has one minimizer. L1 fitting admits
        # several different grounds for the same problem, breaking rotation
        # equivariance through the solver's choice among equal-cost vertices.
        def objective(z: FloatArray) -> float:
            return 0.5 * float(np.sum((z - wanted) ** 2))

        def gradient(z: FloatArray) -> FloatArray:
            return z - wanted

        def hessian(z: FloatArray) -> Any:
            return sparse.eye(len(z), format="csr")

        result: Any = optimize.minimize(
            objective,
            admitted.x,
            jac=gradient,
            hess=hessian,
            method="trust-constr",
            bounds=optimize.Bounds(lower[active], upper[active]),
            constraints=constraints,
            callback=time_limit,
            options={
                "sparse_jacobian": True,
                "gtol": 1.0e-9,
                "xtol": 1.0e-11,
                "barrier_tol": 1.0e-10,
                "maxiter": 500,
            },
        )
        time_limit()
        if not result.success:
            raise RuntimeError(f"Surface fit did not complete: {result.message}")
        solution[active] = result.x
        iterations, message = int(result.nit), str(result.message)
    # Quantization is explicit and still subject to every delivered constraint.
    ground = np.asarray(solution, dtype=np.float32).reshape(grid.shape)
    z = ground.ravel().astype(np.float64)
    anchor_error = np.asarray(equality @ z).ravel() - hard.heights_m
    delivered_slopes = np.asarray(descent @ z).ravel() / lengths
    downhill_residual = delivered_slopes + minimum_slope
    if (
        np.any(z < lower)
        or np.any(z > upper)
        or np.max(np.abs(anchor_error), initial=0) > 0.01
        or np.max(downhill_residual, initial=0) > 1.0e-5
        or np.max(delivered_slopes, initial=0) > 1.0e-10
    ):
        raise InfeasibleSurface("Float32 delivery violates the admitted constraints.")
    return FittedSurface(
        grid,
        ground,
        {
            "model_id": CONSTRAINED_MODEL_ID,
            "node_count": n,
            "descent_constraints": descent.shape[0],
            "hard_height_count": len(hard.heights_m),
            "maximum_anchor_residual_m": float(np.max(np.abs(anchor_error), initial=0)),
            "maximum_slope_residual": float(np.max(downhill_residual, initial=0)),
            "minimum_required_slope": minimum_slope,
            "solver_iterations": iterations,
            "target_squared_residual_m2": float(np.sum((z - target_m.ravel()) ** 2)),
            "solver_message": message,
            "free_constrained_node_count": int(np.count_nonzero(active)),
            "solver": "HiGHS feasibility, then strictly convex trust-constr fit",
            "solver_seconds_limit": maximum_seconds,
            "continuous_bound_scope": (
                "bilinear source-minus-cut to source; Float32 rounding tolerance"
            ),
        },
    )
