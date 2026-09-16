"""Finite mountain-crest probes for the canonical drainage graph."""

from collections.abc import Callable

import numpy as np
import shapely
from numpy.typing import NDArray

from dmtools.terrain.domain.seeds import LANDFORM_STAGE_ID, stage_seed
from dmtools.terrain.pipeline.hydrology import D8_NEIGHBOURS
from dmtools.terrain.pipeline.landforms import MetricRegion, regional_noise_basis

type FloatArray = NDArray[np.float64]
type MacroSampler = Callable[[FloatArray, FloatArray], FloatArray]


def sample_mountain_barriers(
    x: FloatArray, y: FloatArray, elevation_m: FloatArray, land: NDArray[np.bool_],
    regions: tuple[MetricRegion, ...], master_seed: int, sample_macro: MacroSampler,
    *, batch_edges: int = 4096,
) -> FloatArray | None:
    """Sample seven interiors where a mountain carrier changes sign.

    The ridged recipe crests at a carrier zero. Endpoint signs select candidate
    crossings near each region, not all possible hidden maxima. Multiple roots,
    other terrain terms and the complete blended field remain uncertified.
    Opposite D8 directions share exactly the same sampled crest.
    """
    if (x.ndim != 1 or y.ndim != 1 or min(x.size, y.size) < 2
            or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y))
            or np.any(np.diff(x) <= 0.) or np.any(np.diff(y) <= 0.)
            or elevation_m.shape != (y.size, x.size) or land.shape != elevation_m.shape
            or np.any(~np.isfinite(elevation_m[land])) or not 1 <= batch_edges <= 4096):
        raise ValueError("Crest sampling needs finite axes, a shared grid and bounded batches.")
    mountains = tuple(region for region in regions
                      if region.source.settings.character == "mountains"
                      and region.source.settings.relief_m > 0.)
    if not mountains:
        return None
    xx, yy = np.meshgrid(x, y)
    radius = float(np.hypot(np.max(np.diff(x)), np.max(np.diff(y))))
    carriers: list[tuple[FloatArray, NDArray[np.bool_]]] = []
    for region in mountains:
        _u, _v, broad = regional_noise_basis(
            xx, yy, region.source.settings, stage_seed(master_seed, LANDFORM_STAGE_ID))
        nearby = np.asarray(shapely.intersects_xy(region.geometry.buffer(radius), xx, yy),
                            dtype=np.bool_)
        carriers.append((broad, nearby))
    ny, nx = land.shape
    rows, columns = np.indices(land.shape, dtype=np.int64)
    barriers = np.full((8, ny, nx), np.inf)
    fractions = np.arange(1, 8, dtype=np.float64)[None, :]/8.
    raised = False
    # Each undirected connection is sampled once. Reverse D8 indices are 7-i.
    for index in range(4, 8):
        dy, dx = D8_NEIGHBOURS[index]
        rr, cc = rows+dy, columns+dx
        valid = land & (rr >= 0) & (rr < ny) & (cc >= 0) & (cc < nx)
        r, c = np.where(valid)
        tr, tc = r+dy, c+dx
        on_land = land[tr, tc]
        r, c, tr, tc = r[on_land], c[on_land], tr[on_land], tc[on_land]
        endpoints = np.maximum(elevation_m[r, c], elevation_m[tr, tc])
        barriers[index, r, c] = endpoints
        barriers[7-index, tr, tc] = endpoints
        selected = np.zeros(r.size, dtype=np.bool_)
        for broad, nearby in carriers:
            first, last = broad[r, c], broad[tr, tc]
            selected |= ((np.signbit(first) != np.signbit(last)) | (first == 0.) | (last == 0.)) & (
                nearby[r, c] | nearby[tr, tc])
        r, c, tr, tc = r[selected], c[selected], tr[selected], tc[selected]
        for start in range(0, r.size, batch_edges):
            part = slice(start, start+batch_edges)
            a, b, d, e = r[part], c[part], tr[part], tc[part]
            qx = x[b, None]*(1-fractions) + x[e, None]*fractions
            qy = y[a, None]*(1-fractions) + y[d, None]*fractions
            samples = sample_macro(qx, qy)
            if samples.shape != qx.shape or not np.all(np.isfinite(samples)):
                raise ValueError("Crest sampler returned non-finite heights or the wrong shape.")
            original = barriers[index, a, b]
            peaks = np.maximum(original, np.max(samples, axis=1))
            raised |= bool(np.any(peaks > original))
            barriers[index, a, b] = peaks
            barriers[7-index, d, e] = peaks
    if not raised:
        return None
    barriers.flags.writeable = False
    return barriers
