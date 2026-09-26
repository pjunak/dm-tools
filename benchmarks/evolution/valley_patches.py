"""Bounded connected valley patches; an experiment, not a product terrain stage."""

from dataclasses import dataclass, replace
from math import isfinite
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from benchmarks.evolution.constrained import (
    FittedSurface,
    HardHeights,
    InfeasibleSurface,
    float32_bounds,
    weights,
)
from benchmarks.evolution.network_fixture import NetworkFixture
from benchmarks.evolution.paths import FloatArray
from benchmarks.evolution.valley_boundaries import (
    BOUNDARY_MODEL_ID,
    HeadTransition,
    head_transitions,
)

PATCH_MODEL_ID = "connected-valley-patches@1"
type ConstructionMode = Literal["fixed", "fresh"]


@dataclass(frozen=True, slots=True)
class PatchSettings:
    profile_spacing_m: float = 250.0
    support_m: float = 2400.0
    floor_radius_m: float = 500.0
    bank_rise_m: float = 10.0
    initial_grade: float = 0.014
    mouth_taper_m: float = 7000.0
    fresh_cut_limit_m: float = 600.0
    fresh_cut_volume_m3: float = 120.0e9
    anchor_radius_m: float = 500.0
    cross_section: Literal["rounded", "sharp"] = "rounded"
    boundary_model: Literal["coastal-plane", "head-mouth"] = "coastal-plane"

    def __post_init__(self) -> None:
        for value in (
            self.profile_spacing_m,
            self.support_m,
            self.floor_radius_m,
            self.bank_rise_m,
            self.initial_grade,
            self.fresh_cut_limit_m,
            self.fresh_cut_volume_m3,
            self.anchor_radius_m,
        ):
            if isinstance(value, bool) or not isfinite(value) or value <= 0:
                raise ValueError("Patch scales and envelopes must be finite and positive.")
        if (
            isinstance(self.mouth_taper_m, bool)
            or not isfinite(self.mouth_taper_m)
            or self.mouth_taper_m < 0
            or self.floor_radius_m >= self.support_m
            or self.cross_section not in ("rounded", "sharp")
            or self.boundary_model not in ("coastal-plane", "head-mouth")
            or (self.boundary_model == "head-mouth" and self.cross_section != "rounded")
        ):
            raise ValueError("Patch floor, support, mouth taper or cross-section is invalid.")


def swept_profile(
    xy: FloatArray,
    start: FloatArray,
    stop: FloatArray,
    heights: FloatArray,
    settings: PatchSettings,
) -> tuple[FloatArray, FloatArray]:
    """Minimum of a linear bed plus a radial section swept along one segment.

    Minimize in physical arclength, including both endpoint caps. Taking the
    minimum across incident pieces gives one shared junction, not independent
    banks imposed through a tributary. Compact support is applied by the caller.
    """
    direction = stop - start
    length = float(np.hypot(*direction))
    tangent = direction / length
    along = (xy - start) @ tangent
    slope = float(heights[1] - heights[0]) / length
    if settings.cross_section == "rounded":
        curvature = settings.bank_rise_m / settings.floor_radius_m**2
        station = np.clip(along - slope / (2.0 * curvature), 0.0, length)
    else:
        lateral = settings.bank_rise_m / settings.floor_radius_m
        perpendicular = np.linalg.norm(xy - start - along[:, None] * tangent, axis=1)
        if abs(slope) >= lateral:
            station = np.full(len(xy), length if slope < 0 else 0.0)
        else:
            station = np.clip(
                along - slope * perpendicular / np.sqrt(lateral**2 - slope**2), 0.0, length
            )
    distance = np.linalg.norm(xy - start - station[:, None] * tangent, axis=1)
    exponent = 2 if settings.cross_section == "rounded" else 1
    elevation = heights[0] + slope * station
    elevation += settings.bank_rise_m * (distance / settings.floor_radius_m) ** exponent
    return elevation, distance


def _anchor_basis(xy: FloatArray, hard: HardHeights, radius: float) -> FloatArray:
    columns: list[FloatArray] = []
    for point in hard.points_m:
        offset: FloatArray = xy - point
        columns.append(
            np.maximum(1.0 - np.sum(offset * offset, axis=1) / (radius * radius), 0.0) ** 2
        )
    return np.stack(columns, axis=-1) if columns else np.empty((len(xy), 0), dtype=np.float64)


@dataclass(frozen=True, slots=True)
class ValleyPatches:
    source: FittedSurface
    cap_field: FittedSurface
    protected_bounds_m: tuple[float, float, float, float]
    hard: HardHeights
    segments_m: FloatArray
    bed_heights_m: FloatArray
    mode: ConstructionMode
    settings: PatchSettings
    anchor_corrections_m: FloatArray
    mouth_segments_m: FloatArray
    mouth_heights_m: FloatArray
    mouth_inward: FloatArray
    head_transitions: tuple[HeadTransition, ...] = ()

    @property
    def model_id(self) -> str:
        return BOUNDARY_MODEL_ID if self.settings.boundary_model == "head-mouth" else PATCH_MODEL_ID

    def caps(self, x: FloatArray, y: FloatArray, *, incident_cells: bool = False) -> FloatArray:
        if self.mode == "fixed":
            return self.cap_field.sample(x, y).astype(np.float64)
        x0, y0, x1, y1 = self.protected_bounds_m
        # A node participates in four bilinear cells. The expanded rectangle
        # gives the smallest distance to the divide anywhere in those cells;
        # its monotone cap is therefore safe throughout every incident cell.
        margin = self.source.grid.spacing_m if incident_cells else 0.0
        x0, y0, x1, y1 = x0 - margin, y0 - margin, x1 + margin, y1 + margin
        dx = np.maximum(np.maximum(x0 - x, x - x1), 0.0)
        dy = np.maximum(np.maximum(y0 - y, y - y1), 0.0)
        # A fixed physical transition protects the divide independently of pixels.
        q = np.minimum(np.hypot(dx, dy) / self.settings.support_m, 1.0)
        return self.settings.fresh_cut_limit_m * q * q * (3.0 - 2.0 * q)

    def evaluate(self, x: FloatArray, y: FloatArray, *, pins: bool) -> NDArray[np.float32]:
        x, y = np.broadcast_arrays(x, y)
        if x.size > 1_000_000 or x.size * len(self.segments_m) > 256_000_000:
            raise ValueError("Patch sampling exceeds its point/segment work budget.")
        source = self.source.sample(x, y).astype(np.float64)
        xy = np.stack((x.ravel(), y.ravel()), axis=-1)
        values = source.ravel().copy()
        radius = self.settings.support_m
        for segment, heights in zip(self.segments_m, self.bed_heights_m, strict=True):
            lower, upper = segment.min(axis=0) - radius, segment.max(axis=0) + radius
            inside = np.all((xy >= lower) & (xy <= upper), axis=1)
            if not np.any(inside):
                continue
            patch, distance = swept_profile(
                xy[inside], segment[0], segment[1], heights, self.settings
            )
            q = np.clip(
                (distance - self.settings.floor_radius_m) / (radius - self.settings.floor_radius_m),
                0.0,
                1.0,
            )
            influence = 1.0 - q * q * (3.0 - 2.0 * q)
            baseline = source.ravel()[inside]
            proposal = baseline - np.maximum(baseline - patch, 0.0) * influence
            values[inside] = np.minimum(values[inside], proposal)
        for segment, height, inward in zip(
            self.mouth_segments_m, self.mouth_heights_m, self.mouth_inward, strict=True
        ):
            p: FloatArray = segment[0]
            q: FloatArray = segment[1]
            length = float((p - q) @ inward)
            coastal_fraction = ((xy - q) @ inward) / length
            if self.settings.boundary_model == "head-mouth":
                direction = p - q
                fraction = ((xy - q) @ direction) / float(direction @ direction)
            else:
                fraction = coastal_fraction
            centre = q + fraction[:, None] * (p - q)
            offset: FloatArray = xy - centre
            distance = np.linalg.norm(offset, axis=1)
            inside = (coastal_fraction >= 0) & (fraction <= 1) & (distance < radius)
            if not np.any(inside):
                continue
            t = np.maximum(fraction[inside], 0.0)
            v = np.clip(
                (distance[inside] - self.settings.floor_radius_m)
                / (radius - self.settings.floor_radius_m),
                0.0,
                1.0,
            )
            u = np.minimum(2.0 * (1.0 - t), 1.0)
            blend = u * u * (3.0 - 2.0 * u) * (1.0 - v * v * (3.0 - 2.0 * v))
            exponent = 2 if self.settings.cross_section == "rounded" else 1
            relief = (
                self.settings.bank_rise_m
                * (distance[inside] / self.settings.floor_radius_m) ** exponent
            )
            if self.settings.boundary_model == "head-mouth":
                # Bed and banks use perpendicular river sections. Keep positive
                # transverse relief in the inland wedge beyond the mouth section;
                # clamping all of that wedge to t=0 would create a flat zero strip.
                # The unchanged source/no-fill bound owns the actual zero coast.
                mouth = height * t**3 + relief * np.maximum(t, coastal_fraction[inside]) ** 1.3
            else:
                # Retained coastal-plane control: both bed and banks vanish at sea.
                mouth = (height + relief) * t**1.3
            values[inside] = (1.0 - blend) * values[inside] + blend * mouth
        lower = np.maximum(source - self.caps(x, y), 0.0)
        values = np.clip(values, lower.ravel(), source.ravel())
        if pins and len(self.hard.heights_m):
            values += _anchor_basis(xy, self.hard, self.settings.anchor_radius_m) @ (
                self.anchor_corrections_m
            )
        return np.clip(values.reshape(x.shape), lower, source).astype(np.float32)

    def sample(self, x: FloatArray, y: FloatArray) -> NDArray[np.float32]:
        return self.evaluate(x, y, pins=True)

    def deliver(self) -> FittedSurface:
        grid = self.source.grid
        if grid.shape[0] * grid.shape[1] > 16384:
            raise ValueError("Patch delivery is limited to 16,384 process nodes.")
        y, x = np.indices(grid.shape, dtype=np.float64) * grid.spacing_m
        before = self.sample(x, y)
        lower, upper = float32_bounds(
            np.maximum(self.source.ground_m - self.caps(x, y, incident_cells=True), 0.0).ravel(),
            self.source.ground_m.astype(np.float64).ravel(),
        )
        admitted = (
            np.clip(before.astype(np.float64).ravel(), lower, upper)
            .astype(np.float32)
            .reshape(grid.shape)
        )
        delivered = project_hard_heights(self.source, admitted, lower, upper, self.hard)
        pin_delta = delivered.astype(np.float64) - admitted
        row, col = np.unravel_index(int(np.argmax(np.abs(pin_delta))), grid.shape)
        return FittedSurface(
            grid,
            delivered,
            {
                "model_id": self.model_id,
                "mode": self.mode,
                "maximum_delivery_pin_correction_m": float(np.max(np.abs(pin_delta))),
                "maximum_delivery_envelope_correction_m": float(
                    np.max(np.abs(admitted.astype(np.float64) - before))
                ),
                "maximum_delivery_total_correction_m": float(
                    np.max(np.abs(delivered.astype(np.float64) - before))
                ),
                "worst_pin_correction_point_m": [
                    float(col * grid.spacing_m),
                    float(row * grid.spacing_m),
                ],
                "worst_pin_correction_signed_m": float(pin_delta[row, col]),
            },
        )


def project_hard_heights(
    source: FittedSurface,
    proposal: NDArray[np.float32],
    lower: FloatArray,
    upper: FloatArray,
    hard: HardHeights,
) -> NDArray[np.float32]:
    """Bounded least-change projection for disjoint four-node pin supports.

    This small fixture does not require a general equality solver. Overlapping
    supports are explicitly unsupported, not silently processed in input order.
    Numeric delivery failure is not an infeasibility proof.
    """
    if len(hard.heights_m) > 16:
        raise ValueError("Patch comparison supports at most 16 independent height pins.")
    out = np.clip(proposal.astype(np.float64).ravel(), lower, upper)
    used: set[int] = set()
    for point, target in zip(hard.points_m, hard.heights_m, strict=True):
        row = weights(source.grid, point[None, :])
        valid = row.data > 0
        ids, w = row.indices[valid], row.data[valid]
        if used.intersection(ids.tolist()):
            raise ValueError("Patch comparison does not support overlapping height-pin cells.")
        used.update(ids.tolist())
        if target < float(w @ lower[ids]) - 1e-7 or target > float(w @ upper[ids]) + 1e-7:
            raise InfeasibleSurface("Hard height conflicts with the construction envelope.")
        initial = out[ids].copy()
        left = float(np.min((lower[ids] - initial) / w))
        right = float(np.max((upper[ids] - initial) / w))
        for _ in range(64):
            middle = 0.5 * (left + right)
            if float(w @ np.clip(initial + middle * w, lower[ids], upper[ids])) < target:
                left = middle
            else:
                right = middle
        out[ids] = np.clip(initial + 0.5 * (left + right) * w, lower[ids], upper[ids])
    result = np.clip(out, lower, upper).astype(np.float32).reshape(source.grid.shape)
    values = FittedSurface(source.grid, result, {}).sample(*hard.points_m.T)
    if np.any(np.abs(values.astype(np.float64) - hard.heights_m) > 0.0001):
        raise RuntimeError("Patch Float32 delivery failed its hard-height check.")
    return result


def prepare_patches(
    f: NetworkFixture,
    control: FittedSurface,
    *,
    mode: ConstructionMode = "fixed",
    settings: PatchSettings | None = None,
) -> ValleyPatches:
    settings = settings or PatchSettings()
    if mode not in ("fixed", "fresh") or control.grid != f.source.grid:
        raise ValueError("Patch preparation needs a known mode and matching control grid.")
    if settings.boundary_model == "head-mouth" and mode != "fresh":
        raise ValueError("Head/mouth construction requires a generated fresh relief hypothesis.")
    if len(f.hard.heights_m) > 16:
        raise ValueError("Patch comparison supports at most 16 independent height pins.")
    segment_edges: list[int] = []
    segments: list[FloatArray] = []
    heights: list[FloatArray] = []
    remaining: list[FloatArray] = []
    terminals: list[int] = []
    mouth_starts: list[int] = []
    mouth_segments: list[FloatArray] = []
    normals: list[FloatArray] = []
    network = f.network
    for edge in np.flatnonzero(network.required):
        route = network.route(int(edge))
        path = network.coordinates_m[route]
        lengths = np.linalg.norm(np.diff(path, axis=0), axis=1)
        capacity = 2048 - len(segments)
        if capacity <= 0 or settings.profile_spacing_m < lengths[0] / capacity:
            raise ValueError("Patch preparation exceeds 2,048 physical profile segments.")
        count = int(np.ceil(lengths[0] / settings.profile_spacing_m))
        if len(route) == 2:
            q = path[-1]
            normal = np.zeros(2, dtype=np.float64)
            if q[0] == 0 and np.all(f.source.ground_m[:, 0] == 0):
                normal[0] = 1.0
            elif q[1] == f.source.grid.height_m and np.all(f.source.ground_m[-1] == 0):
                normal[1] = -1.0
            else:
                raise ValueError("Patch mouth needs the fixture's straight zero-height coast.")
            if float((path[0] - q) @ normal) <= 0:
                raise ValueError("Patch mouth must approach the coast from inland.")
            mouth_starts.append(len(segments))
            mouth_segments.append(path.copy())
            normals.append(normal)
        t = np.linspace(0.0, 1.0, count + 1)
        xy = path[0] + t[:, None] * (path[1] - path[0])
        z = control.sample(*xy.T).astype(np.float64)
        for i in range(count):
            segment_edges.append(int(edge))
            segments.append(xy[i : i + 2])
            heights.append(z[i : i + 2])
            remaining.append(np.maximum(0.0, lengths.sum() - t[i : i + 2] * lengths[0]))
            terminals.append(int(route[-1]))
    geometry = np.array(segments, dtype=np.float64)
    bed = np.array(heights, dtype=np.float64)
    if mode == "fresh":
        distances = np.array(remaining, dtype=np.float64)
        fade = np.ones_like(distances)
        if settings.mouth_taper_m:
            q = np.minimum(distances / settings.mouth_taper_m, 1.0)
            fade = q * q * (3.0 - 2.0 * q)
        desired = settings.initial_grade * distances * fade
        sampled_source = f.source.sample(geometry[:, :, 0], geometry[:, :, 1])
        for terminal in np.unique(terminals):
            selected = np.asarray(terminals) == terminal
            positive = selected[:, None] & (desired > 0)
            # A single scale per catchment keeps shared beds identical and the
            # profile descending, while respecting this generated initial relief.
            scale = min(1.0, float(np.min(0.55 * sampled_source[positive] / desired[positive])))
            bed[selected] = desired[selected] * scale
    bounds = tuple(float(v) * 1000 for v in f.protected_divide_km.bounds)
    assert len(bounds) == 4
    mouths = np.array(mouth_segments, dtype=np.float64)
    mouth_heights = bed[np.array(mouth_starts), 0].copy()
    inward = np.array(normals, dtype=np.float64)
    provisional = ValleyPatches(
        f.source,
        FittedSurface(f.source.grid, f.limits_m.astype(np.float32), {}),
        bounds,
        f.hard,
        geometry,
        bed,
        mode,
        settings,
        np.zeros(len(f.hard.heights_m)),
        mouths,
        mouth_heights,
        inward,
    )
    if settings.boundary_model == "head-mouth":
        heads = network.coordinates_m[network.heads()]
        lower = np.maximum(
            f.source.sample(*heads.T).astype(np.float64) - provisional.caps(*heads.T), 0.0
        )
        bed, transitions = head_transitions(
            network,
            np.asarray(segment_edges, dtype=np.int64),
            geometry,
            bed,
            lower,
            settings.bank_rise_m,
        )
        mouth_heights = bed[np.array(mouth_starts), 0].copy()
        provisional = replace(
            provisional,
            bed_heights_m=bed,
            mouth_heights_m=mouth_heights,
            head_transitions=transitions,
        )
    coefficients = np.empty(0, dtype=np.float64)
    if len(f.hard.heights_m):
        basis = _anchor_basis(f.hard.points_m, f.hard, settings.anchor_radius_m)
        if np.linalg.cond(basis) > 1e8:
            raise ValueError("Patch height-pin kernels are not independently supported.")
        coefficients = np.linalg.solve(
            basis, f.hard.heights_m - provisional.evaluate(*f.hard.points_m.T, pins=False)
        )
    for array in (geometry, bed, coefficients, mouths, mouth_heights, inward):
        array.flags.writeable = False
    result = replace(provisional, anchor_corrections_m=coefficients)
    if np.any(np.abs(result.sample(*f.hard.points_m.T) - f.hard.heights_m) > 0.0001):
        raise InfeasibleSurface("Local patch height conflicts with the construction envelope.")
    return result
