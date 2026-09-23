# pyright: reportUnknownMemberType=false
"""Experimental additive cell detail on a verified, unchanged reference field.

The added smooth basis has zero analytic integral per parent cell. Preparation
uses a fixed lattice, never the output density. This is a bounded experiment,
not accepted local hydrology or a certified bound on unseen terrain extrema.
"""

from dataclasses import dataclass, replace
from dataclasses import field as dataclass_field
from hashlib import sha256
from typing import Any, cast

import numpy as np
import shapely
from numpy.typing import NDArray
from shapely.geometry import LineString, Point, box
from shapely.strtree import STRtree

from dmtools.terrain.domain.regional import (
    DETAIL_CELL_LIMIT,
    DETAIL_PROBE_INTERVALS,
    RegionalDetailSettings,
    RegionalSamplingRequest,
    detail_cell_window,
)
from dmtools.terrain.domain.seeds import LOCAL_DETAIL_STAGE_ID, stage_seed
from dmtools.terrain.pipeline.detail_cache import (
    CellDetailSupport,
    DetailCacheInfo,
    DetailSupportCache,
)
from dmtools.terrain.pipeline.generate import ProgressCallback
from dmtools.terrain.pipeline.parent import VerifiedTerrainParent
from dmtools.terrain.pipeline.regional import RegionalTerrainSamples

LOCAL_DETAIL_ALGORITHM_ID = "protected-cell-residual-experiment@1"


def cell_coefficients(
    columns: NDArray[np.int64], rows: NDArray[np.int64], seed: int
) -> NDArray[np.float64]:
    coefficients = np.empty((columns.size, 3), dtype=np.float64)
    for i, (column, row) in enumerate(zip(columns.flat, rows.flat, strict=True)):
        payload = (
            b"dmtools.local-detail-cell@1\0"
            + seed.to_bytes(4, "big")
            + int(column).to_bytes(8, "big")
            + int(row).to_bytes(8, "big")
        )
        digest = sha256(payload).digest()
        for mode in range(3):
            unit = int.from_bytes(digest[mode * 4 : mode * 4 + 4], "big") / 0xFFFFFFFF
            coefficients[i, mode] = (2 * unit - 1) / 3
    return coefficients


def residual_basis(
    u: NDArray[np.float64], v: NDArray[np.float64], coefficients: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Each odd factor integrates to zero; values and first derivatives vanish at edges."""
    bu, bv = np.sin(np.pi * u) ** 2, np.sin(np.pi * v) ** 2
    value = (
        bu
        * bv
        * (
            coefficients[..., 0] * np.sin(2 * np.pi * u)
            + coefficients[..., 1] * np.sin(2 * np.pi * v)
            + coefficients[..., 2] * np.sin(4 * np.pi * u) * np.sin(4 * np.pi * v)
        )
    )
    # sin(pi) is not exactly zero in binary floating point.
    return np.where((u == 0) | (u == 1) | (v == 0) | (v == 1), 0.0, value)


@dataclass(frozen=True, slots=True)
class DetailEvidence:
    parent_cells: int
    protected_cells: int
    active_cells: int
    probe_samples: int
    maximum_cell_mean_error_m: float
    maximum_added_height_m: float
    changed_samples: int


@dataclass(frozen=True, slots=True)
class DetailedRegion:
    samples: RegionalTerrainSamples
    reference_elevation_m: NDArray[np.float32]
    added_detail_m: NDArray[np.float32]
    cell_columns: NDArray[np.int64]
    cell_rows: NDArray[np.int64]
    cell_amplitude_m: NDArray[np.float64]
    reference_cell_mean_m: NDArray[np.float64]
    detailed_cell_mean_m: NDArray[np.float64]
    evidence: DetailEvidence


@dataclass(frozen=True, slots=True)
class PreparedRegionalDetail:
    """One immutable parent/settings context with a private, serial-use support cache."""

    parent: VerifiedTerrainParent
    settings: RegionalDetailSettings
    protections: STRtree
    cache_cells: int = DETAIL_CELL_LIMIT
    _cache: DetailSupportCache = dataclass_field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        # init=False also gives dataclasses.replace a fresh cache when any context changes.
        object.__setattr__(self, "_cache", DetailSupportCache(self.cache_cells))

    def cache_info(self) -> DetailCacheInfo:
        """Operational counts only; never include request history in artifact identity."""
        return self._cache.info()

    def clear_cache(self) -> None:
        """Release retained support and reset operational counts, preserving the parent."""
        self._cache.clear()

    def sample(
        self, request: RegionalSamplingRequest, progress: ProgressCallback | None = None
    ) -> DetailedRegion:
        sampler = self.parent.sampler
        if (
            request.source_id != sampler.source_id
            or request.reference_grid != sampler.reference_grid
        ):
            raise ValueError("Detail request belongs to a different parent or grid.")
        left, top, right, bottom = detail_cell_window(request)
        cc, rr = np.meshgrid(
            np.arange(left, right + 1, dtype=np.int64), np.arange(top, bottom + 1, dtype=np.int64)
        )
        columns, rows = cc.ravel(), rr.ravel()
        x, y = self.parent.data.x_km, self.parent.data.y_km
        field = sampler.prepared_field
        # The authoritative parent already stores its ceiling rounded to Float32.
        ceiling_m = float(np.float32(field.settings.maximum_elevation_m))
        if not np.isfinite(ceiling_m):
            raise ValueError("Local detail requires a finite Float32 terrain ceiling.")
        protected = np.zeros(columns.size, dtype=np.bool_)
        amplitude = np.zeros(columns.size, dtype=np.float64)
        reference_means = np.full(columns.size, np.nan, dtype=np.float64)
        detailed_means = reference_means.copy()
        missing: list[int] = []
        for index, (column, row) in enumerate(zip(columns, rows, strict=True)):
            support = self._cache.get(int(column), int(row))
            if support is None:
                missing.append(index)
            else:
                protected[index] = support.protected
                amplitude[index] = support.amplitude_m
                reference_means[index] = support.reference_mean_m
                detailed_means[index] = support.detailed_mean_m
        pending = np.asarray(missing, dtype=np.int64)
        if pending.size:
            pc, pr = columns[pending], rows[pending]
            cells = cast(Any, shapely.box(x[pc], y[pr], x[pc + 1], y[pr + 1]))
            guard = min(sampler.reference_grid.x_spacing_km, sampler.reference_grid.y_spacing_km)
            inland = cast(
                NDArray[np.bool_], np.asarray(cast(Any, shapely.covers(field.polygon, cells)))
            )
            inland &= np.asarray(cast(Any, shapely.distance(cells, field.boundary))) > guard
            intersections = self.protections.query(cells, predicate="intersects")
            protected[pending] = ~inland
            if intersections.size:
                protected[pending[np.unique(intersections[0])]] = True
            for index in pending[protected[pending]]:
                self._cache.put(
                    int(columns[index]), int(rows[index]),
                    CellDetailSupport(True, 0.0, float("nan"), float("nan")),
                )
            pending = pending[~protected[pending]]
        seed = stage_seed(field.settings.seed, LOCAL_DETAIL_STAGE_ID)
        coefficients = cell_coefficients(columns, rows, seed)
        n = DETAIL_PROBE_INTERVALS
        uv = np.linspace(0.0, 1.0, n + 1)
        u, v = np.meshgrid(uv, uv)
        u, v = u.ravel(), v.ravel()
        weights = np.ones((n + 1, n + 1), dtype=np.float64)
        weights[[0, -1], :] *= 0.5
        weights[:, [0, -1]] *= 0.5
        weights = weights.ravel() / (n * n)
        active = np.flatnonzero(~protected)
        for start in range(0, pending.size, 64):
            ids = pending[start : start + 64]
            px = x[columns[ids], None] + (x[columns[ids] + 1] - x[columns[ids]])[:, None] * u
            py = y[rows[ids], None] + (y[rows[ids] + 1] - y[rows[ids]])[:, None] * v
            reference = field.sample_ground(px, py).astype(np.float64)
            if not np.isfinite(reference).all():
                raise RuntimeError("Detail preparation encountered invalid interior ground.")
            margin = np.min(np.minimum(reference, ceiling_m - reference), axis=1)
            amplitude[ids] = np.minimum(self.settings.amplitude_m, np.maximum(margin, 0.0) * 0.5)
            # Use the same coordinate-to-cell arithmetic as delivered samples.
            pu = (px - x[columns[ids], None]) / (x[columns[ids] + 1] - x[columns[ids]])[:, None]
            pv = (py - y[rows[ids], None]) / (y[rows[ids] + 1] - y[rows[ids]])[:, None]
            residual = residual_basis(pu, pv, coefficients[ids, None, :]) * amplitude[ids, None]
            detailed = (reference + residual).astype(np.float32).astype(np.float64)
            reference_means[ids] = np.sum(reference * weights, axis=1)
            detailed_means[ids] = np.sum(detailed * weights, axis=1)
            for index in ids:
                self._cache.put(
                    int(columns[index]), int(rows[index]),
                    CellDetailSupport(
                        False, float(amplitude[index]), float(reference_means[index]),
                        float(detailed_means[index]),
                    ),
                )
            if progress is not None:
                progress(
                    0.1 + 0.4 * min(start + 64, pending.size) / pending.size,
                    "Preparing fixed parent-cell detail support",
                )
        samples = sampler.sample(request, progress)
        elevation = samples.elevation_m.copy()
        _height, width = elevation.shape
        for start in range(0, elevation.size, 65_536):
            stop = min(start + 65_536, elevation.size)
            indices = np.arange(start, stop, dtype=np.int64)
            px, py = samples.x_km[indices % width], samples.y_km[indices // width]
            column = np.clip(np.searchsorted(x, px, side="right") - 1, left, right)
            row = np.clip(np.searchsorted(y, py, side="right") - 1, top, bottom)
            local = (row - top) * (right - left + 1) + column - left
            u = (px - x[column]) / (x[column + 1] - x[column])
            v = (py - y[row]) / (y[row + 1] - y[row])
            residual = residual_basis(u, v, coefficients[local]) * amplitude[local]
            ground = elevation.ravel()[start:stop].astype(np.float64) + residual
            mask = samples.land_mask.ravel()[start:stop]
            if (
                np.any(ground[mask] < 0)
                or np.any(ground[mask] > ceiling_m)
                or not np.isfinite(ground[mask]).all()
            ):
                raise ValueError(
                    "Detail exceeds terrain bounds between fixed probes; "
                    "reduce its amplitude or choose another region."
                )
            elevation.ravel()[start:stop] = ground.astype(np.float32)
        added = np.where(samples.land_mask, elevation - samples.elevation_m, 0.0).astype(np.float32)
        errors = np.abs(detailed_means[active] - reference_means[active])
        evidence = DetailEvidence(
            columns.size,
            int(protected.sum()),
            int(np.count_nonzero(amplitude)),
            int(active.size * (n + 1) ** 2),
            float(errors.max(initial=0)),
            float(np.abs(added).max(initial=0)),
            int(np.count_nonzero(added)),
        )
        for array in (elevation, added, columns, rows, amplitude, reference_means, detailed_means):
            array.setflags(write=False)
        return DetailedRegion(
            replace(samples, elevation_m=elevation),
            samples.elevation_m,
            added,
            columns,
            rows,
            amplitude,
            reference_means,
            detailed_means,
            evidence,
        )


def prepare_regional_detail(
    parent: VerifiedTerrainParent, settings: RegionalDetailSettings, *,
    cache_cells: int = DETAIL_CELL_LIMIT,
) -> PreparedRegionalDetail:
    """Protect complete cells intersecting authored cores, basins and planned channel corridors."""
    field = parent.sampler.prepared_field
    grid = parent.sampler.reference_grid
    guard = min(grid.x_spacing_km, grid.y_spacing_km)
    geometries: list[Any] = [basin.geometry.buffer(guard) for basin in field.basins]
    for constraint in field.constraints:
        geometries.append(constraint.geometry.buffer(max(guard, constraint.influence_radius_km)))
    routing = parent.data.routing
    width = routing.x_km.size
    sources = np.flatnonzero(routing.channel_mask & routing.land_mask)
    radius = max(guard, np.diff(routing.x_km).max(), np.diff(routing.y_km).max())
    for source in sources:
        row, column = divmod(int(source), width)
        start = (routing.x_km[column], routing.y_km[row])
        target = int(routing.receivers.flat[source])
        if target >= 0:
            tr, tc = divmod(target, width)
            geometry = LineString([start, (routing.x_km[tc], routing.y_km[tr])])
        else:
            geometry = Point(start)
        geometries.append(geometry.buffer(float(radius)))
    # An empty tree is supported, but keep a harmless outside-frame box explicit.
    if not geometries:
        geometries.append(box(-2 * guard, -2 * guard, -guard, -guard))
    return PreparedRegionalDetail(parent, settings, STRtree(geometries), cache_cells)
