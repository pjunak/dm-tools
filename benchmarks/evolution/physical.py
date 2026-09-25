"""Experimental channel/ground deformation; never a completed-DEM editor.

A fixed-boundary, positive-area mesh maps the frozen triangle control and its
entire channel graph together. This guarantees embedded graph topology, not
physical erosion, fixed geographic divides, or compliance with cut/fill budgets.
"""

from dataclasses import dataclass
from hashlib import sha256
from math import isfinite
from typing import Any

import numpy as np
from numpy.typing import NDArray

from benchmarks.evolution.paths import ChannelPaths, FloatArray, Sampler, anchor_residuals
from benchmarks.evolution.surface import FlowAlignedSurface

PHYSICAL_PATH_ID = "terrain-guided-channel-mesh@1"


@dataclass(frozen=True, slots=True)
class PathSettings:
    displacement_m: float = 125.0
    terrain_scale_m: float = 25.0
    iterations: int = 8

    def __post_init__(self) -> None:
        for value in (self.displacement_m, self.terrain_scale_m):
            if isinstance(value, bool) or not isfinite(value) or value <= 0:
                raise ValueError("Path scales must be finite positive metres.")
        if type(self.iterations) is not int or not 1 <= self.iterations <= 32:
            raise ValueError("Path preparation requires 1-32 iterations.")


@dataclass(frozen=True, slots=True)
class PhysicalPaths(ChannelPaths):
    coordinates_m: FloatArray

    def __post_init__(self) -> None:
        ChannelPaths.__post_init__(self)
        coordinates = np.array(self.coordinates_m, dtype=np.float64, copy=True)
        if coordinates.shape != (*self.grid.shape, 2) or not np.all(np.isfinite(coordinates)):
            raise ValueError("Physical paths require finite xy coordinates for every node.")
        coordinates.flags.writeable = False
        object.__setattr__(self, "coordinates_m", coordinates)

    def points(self, nodes: NDArray[np.int64]) -> tuple[FloatArray, FloatArray]:
        points = self.coordinates_m.reshape(-1, 2)[nodes]
        return points[:, 0], points[:, 1]

    def identity(self) -> str:
        return sha256(
            ChannelPaths.identity(self).encode() + self.coordinates_m.astype("<f8").tobytes()
        ).hexdigest()


def grid_points(field: FlowAlignedSurface) -> FloatArray:
    y, x = np.indices(field.grid.shape, dtype=np.float64) * field.grid.spacing_m
    return np.stack((x, y), axis=-1)


def _corners(points: FloatArray) -> FloatArray:
    return np.stack((points[:-1, :-1], points[:-1, 1:], points[1:, 1:], points[1:, :-1]), axis=-2)


def _centres(corners: FloatArray, diagonals: NDArray[np.int8]) -> FloatArray:
    # Four fans avoid an arbitrary diagonal in untouched bilinear cells. In
    # required cells their centre lies exactly on the required channel edge.
    centre = corners.mean(axis=-2)
    for code, first, second in ((1, 0, 2), (-1, 1, 3)):
        selected = diagonals == code
        centre[selected] = (corners[selected, first] + corners[selected, second]) * 0.5
    return centre


def _cross(a: FloatArray, b: FloatArray) -> FloatArray:
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


@dataclass(frozen=True, slots=True, init=False)
class PhysicalSurface:
    reference: FlowAlignedSurface
    paths: PhysicalPaths
    active: NDArray[np.bool_]
    corners_m: FloatArray
    centres_m: FloatArray
    determinants_m2: FloatArray

    def __init__(self, reference: FlowAlignedSurface, coordinates_m: FloatArray) -> None:
        origin = grid_points(reference)
        paths = PhysicalPaths(
            reference.grid, reference.receivers, reference.required, coordinates_m
        )
        displacement = paths.coordinates_m - origin
        spacing = reference.grid.spacing_m
        incoming = np.bincount(
            reference.receivers[reference.required], minlength=reference.receivers.size
        ).reshape(reference.grid.shape)
        movable = reference.required & (incoming == 1)
        if np.any(displacement[~movable]):
            raise ValueError("Only degree-two channel nodes may move; endpoints stay fixed.")
        if np.max(np.linalg.norm(displacement, axis=-1)) > spacing * 0.24 + 1.0e-9:
            raise ValueError("Physical nodes exceed the bounded 0.24-cell corridor.")
        if np.any(displacement[[0, -1]]) or np.any(displacement[:, [0, -1]]):
            raise ValueError("The physical surface boundary must remain fixed.")
        corners = _corners(paths.coordinates_m)
        centres = _centres(corners, reference.diagonals)
        vectors = corners - centres[..., None, :]
        determinants = _cross(vectors, np.roll(vectors, -1, axis=-2))
        if np.any(determinants <= spacing**2 * 1.0e-8):
            raise ValueError("The physical mesh folds or degenerates.")
        active = np.any(_corners(displacement) != 0.0, axis=(-2, -1))
        for value in (corners, centres, determinants, active):
            value.flags.writeable = False
        for name, value in (
            ("reference", reference),
            ("paths", paths),
            ("active", active),
            ("corners_m", corners),
            ("centres_m", centres),
            ("determinants_m2", determinants),
        ):
            object.__setattr__(self, name, value)

    def sample(self, x_m: FloatArray, y_m: FloatArray) -> NDArray[np.float32]:
        x, y = np.broadcast_arrays(
            np.asarray(x_m, dtype=np.float64), np.asarray(y_m, dtype=np.float64)
        )
        shape = x.shape
        x, y = x.ravel(), y.ravel()
        grid = self.reference.grid
        if (
            not np.all(np.isfinite(x))
            or not np.all(np.isfinite(y))
            or np.any(x < 0)
            or np.any(y < 0)
            or np.any(x > grid.width_m)
            or np.any(y > grid.height_m)
        ):
            raise ValueError("Physical queries must be finite and inside the frozen domain.")
        spacing = grid.spacing_m
        cols, rows = grid.shape[1] - 1, grid.shape[0] - 1
        c = np.minimum((x / spacing).astype(np.int64), cols - 1)
        r = np.minimum((y / spacing).astype(np.int64), rows - 1)
        original_x, original_y = x.copy(), y.copy()
        remaining = self.active[r, c].copy()
        # A moved node cannot leave its local neighbourhood. Active cells have
        # fixed outer boundaries, so their union is unchanged by the mapping.
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                valid = remaining & (rr >= 0) & (rr < rows) & (cc >= 0) & (cc < cols)
                ids = np.flatnonzero(valid)
                ids = ids[self.active[rr[ids], cc[ids]]]
                if not ids.size:
                    continue
                cr, cl = rr[ids], cc[ids]
                centres = self.centres_m[cr, cl]
                corners = self.corners_m[cr, cl]
                delta = np.stack((x[ids], y[ids]), axis=-1) - centres
                for edge, (a, b) in enumerate(((0, 1), (1, 2), (2, 3), (3, 0))):
                    v1, v2 = corners[:, a] - centres, corners[:, b] - centres
                    determinant = self.determinants_m2[cr, cl, edge]
                    u, v = _cross(delta, v2) / determinant, _cross(v1, delta) / determinant
                    inside = remaining[ids] & (u >= -1.0e-12) & (v >= -1.0e-12)
                    inside &= u + v <= 1.0 + 1.0e-12
                    found = ids[inside]
                    # Reference fans have the same square corners and centre.
                    offsets = ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5))
                    original_x[found] = (
                        cl[inside] + 0.5 + u[inside] * offsets[a][0] + v[inside] * offsets[b][0]
                    ) * spacing
                    original_y[found] = (
                        cr[inside] + 0.5 + u[inside] * offsets[a][1] + v[inside] * offsets[b][1]
                    ) * spacing
                    remaining[found] = False
        if np.any(remaining):
            raise ValueError("Physical mesh did not cover an active query.")
        return self.reference.sample(
            np.clip(original_x, 0, grid.width_m).reshape(shape),
            np.clip(original_y, 0, grid.height_m).reshape(shape),
        )


def prepare(field: FlowAlignedSurface, settings: PathSettings | None = None) -> PhysicalSurface:
    """Relax only degree-two channel nodes; all heads/junctions/terminals stay fixed.

    The objective penalizes squared reach lengths and the sampled source height
    difference from the retained bed elevation. It is a geometric experiment,
    not an optimization of erosion energy. Fixed iterations and local candidates
    are independent of the requested output resolution and query order.
    """
    settings = settings or PathSettings()
    points = grid_points(field)
    flat = points.reshape(-1, 2)
    required = np.flatnonzero(field.required)
    receivers = field.receivers.ravel()
    incoming = np.bincount(receivers[required], minlength=receivers.size)
    nodes = required[incoming[required] == 1]
    # Perimeter and graph terminals are fixed even in synthetic interior-terminal cases.
    rows, cols = np.divmod(nodes, field.grid.shape[1])
    nodes = nodes[
        (rows > 0)
        & (rows < field.grid.shape[0] - 1)
        & (cols > 0)
        & (cols < field.grid.shape[1] - 1)
    ]
    if not nodes.size:
        return PhysicalSurface(field, points)
    upstream = np.full(receivers.size, -1, dtype=np.int64)
    upstream[receivers[required]] = required
    before, after = upstream[nodes], receivers[nodes]
    tangent = flat[after] - flat[before]
    tangent /= np.linalg.norm(tangent, axis=1)[:, None]
    normal = np.stack((-tangent[:, 1], tangent[:, 0]), axis=1)
    radius = min(settings.displacement_m, field.grid.spacing_m * 0.24)
    offsets = np.linspace(-radius, radius, 17)
    candidates = flat[nodes, None, :] + offsets[None, :, None] * normal[:, None, :]
    source = field.bilinear(candidates[..., 0], candidates[..., 1]).astype(np.float64)
    terrain_cost = ((source - field.ground_m.ravel()[nodes, None]) / settings.terrain_scale_m) ** 2
    original = flat.copy()
    for _ in range(settings.iterations):
        lengths = np.sum((candidates - flat[before, None, :]) ** 2, axis=-1)
        lengths += np.sum((candidates - flat[after, None, :]) ** 2, axis=-1)
        costs = lengths / field.grid.spacing_m**2 + terrain_cost
        chosen = np.argmin(costs, axis=1)
        current_source = field.bilinear(flat[nodes, 0], flat[nodes, 1]).astype(np.float64)
        current = (
            np.sum((flat[nodes] - flat[before]) ** 2, axis=-1)
            + np.sum((flat[nodes] - flat[after]) ** 2, axis=-1)
        ) / field.grid.spacing_m**2
        current += (
            (current_source - field.ground_m.ravel()[nodes]) / settings.terrain_scale_m
        ) ** 2
        improve = costs[np.arange(nodes.size), chosen] < current - 1.0e-12
        selected = nodes[improve]
        flat[selected] = 0.5 * (flat[selected] + candidates[np.arange(nodes.size), chosen][improve])
    # Non-channel nodes, junctions and endpoints were never candidates.
    if np.any(np.linalg.norm(flat - original, axis=1) > radius + 1.0e-9):
        raise ValueError("Path optimizer left its original physical corridor.")
    return PhysicalSurface(field, points)


def geometry_numbers(paths: ChannelPaths) -> dict[str, float | int]:
    sources = np.flatnonzero(paths.required)
    targets = paths.receivers.ravel()[sources]
    x0, y0 = paths.points(sources)
    x1, y1 = paths.points(targets)
    dx, dy = x1 - x0, y1 - y0
    length = np.hypot(dx, dy)
    angles = np.rad2deg(np.arctan2(dy, dx))
    deviation = np.abs((angles + 22.5) % 45.0 - 22.5)
    locked = deviation <= 0.5
    return {
        "edge_count": int(sources.size),
        "length_m": float(length.sum()),
        "length_within_half_degree_of_d8_m": float(length[locked].sum()),
        "d8_length_fraction": float(length[locked].sum() / length.sum()) if length.size else 0.0,
    }


def constraint_samples(
    candidate: Sampler,
    source: Sampler,
    points_m: FloatArray,
    *,
    maximum_cut_m: float,
    maximum_fill_m: float,
    anchors_m: FloatArray,
    anchor_heights_m: FloatArray,
) -> dict[str, Any]:
    """Necessary sampled checks; a pass is not a continuous-field admission proof."""
    for budget in (maximum_cut_m, maximum_fill_m):
        if isinstance(budget, bool) or not isfinite(budget) or budget < 0:
            raise ValueError("Cut/fill budgets must be finite nonnegative metres.")
    if points_m.ndim != 2 or points_m.shape[1] != 2 or not np.all(np.isfinite(points_m)):
        raise ValueError("Constraint samples need finite physical xy coordinates.")
    actual = candidate(points_m[:, 0], points_m[:, 1])
    original = source(points_m[:, 0], points_m[:, 1])
    if (
        actual.shape != (len(points_m),)
        or original.shape != actual.shape
        or actual.dtype != np.float32
        or original.dtype != np.float32
        or not np.all(np.isfinite(actual))
        or not np.all(np.isfinite(original))
    ):
        raise ValueError("Constraint samplers must deliver finite Float32 heights.")
    delta = actual.astype(np.float64) - original.astype(np.float64)
    anchors = anchor_residuals(candidate, anchors_m, anchor_heights_m)
    cuts, fills = delta < -maximum_cut_m - 0.01, delta > maximum_fill_m + 0.01
    return {
        "sample_count": len(points_m),
        "maximum_cut_m": maximum_cut_m,
        "maximum_fill_m": maximum_fill_m,
        "sampled_cut_m": max(0.0, -float(delta.min(initial=0))),
        "sampled_fill_m": max(0.0, float(delta.max(initial=0))),
        "cut_violations": int(cuts.sum()),
        "fill_violations": int(fills.sum()),
        "anchors": anchors,
        "anchor_count": len(anchors_m),
        "passes_sampled_constraints": not (
            cuts.any() or fills.any() or anchors["violated_indices"]
        ),
        "scope": "sampled geometric change relative to frozen bilinear ground; not erosion",
    }
