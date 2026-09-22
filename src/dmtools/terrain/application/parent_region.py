"""Generate a separate regional artifact from a completed, verified parent build."""

from pathlib import Path

from dmtools.terrain.adapters.build import runtime_identity
from dmtools.terrain.adapters.parent import load_terrain_parent
from dmtools.terrain.adapters.parent_region import (
    publish_parent_region_manifest,
    write_parent_region_products,
)
from dmtools.terrain.domain.coordinates import Bounds
from dmtools.terrain.domain.regional import (
    RegionalDetailSettings,
    RegionalSamplingRequest,
    detail_cell_window,
)
from dmtools.terrain.pipeline.detail import prepare_regional_detail
from dmtools.terrain.pipeline.generate import ProgressCallback
from dmtools.terrain.pipeline.parent import prepare_verified_parent


def sample_parent_region(
    source: Path,
    destination: Path,
    bounds_km: Bounds,
    refinement: int,
    *,
    detail_settings: RegionalDetailSettings | None = None,
    progress: ProgressCallback | None = None,
) -> Path:
    target = destination.absolute()
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"Regional destination already exists: {target}")
    if target.resolve().is_relative_to(source.resolve()):
        raise ValueError("Regional output must be outside the immutable parent build directory.")
    runtime = runtime_identity()
    loaded = load_terrain_parent(source, runtime)
    request = RegionalSamplingRequest.for_bounds(
        loaded.data.build_id, loaded.data.grid, bounds_km, refinement
    )
    if detail_settings is not None:
        detail_cell_window(request)  # Reject work budgets before field preparation or output.
    parent = prepare_verified_parent(loaded.data, progress)
    detail = None
    if detail_settings is None:
        samples = parent.sampler.sample(request, progress)
    else:
        detail = prepare_regional_detail(parent, detail_settings).sample(request, progress)
        samples = detail.samples
    loaded.verify_unchanged()
    if runtime_identity() != runtime:
        raise ValueError("Generator source or runtime changed during parent replay; retry.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir()
    outputs = write_parent_region_products(samples, parent, target, detail)
    loaded.verify_unchanged()
    if runtime_identity() != runtime:
        raise ValueError("Generator source or runtime changed during regional generation; retry.")
    return publish_parent_region_manifest(
        samples,
        loaded,
        parent,
        target,
        bounds_km=bounds_km,
        runtime=runtime,
        outputs=outputs,
        detail_settings=detail_settings,
        detail=detail,
    )
