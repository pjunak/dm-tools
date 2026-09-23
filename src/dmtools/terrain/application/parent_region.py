"""Generate a separate regional artifact from a completed, verified parent build."""

from dataclasses import replace
from pathlib import Path
from typing import Self

from dmtools.terrain.adapters.build import runtime_identity
from dmtools.terrain.adapters.parent import LoadedTerrainParent, load_terrain_parent
from dmtools.terrain.adapters.parent_region import (
    publish_parent_region_manifest,
    write_parent_region_products,
)
from dmtools.terrain.application.region_cache import (
    DEFAULT_RESULT_CACHE_BYTES,
    ParentRegionResult,
    RegionResultCache,
    RegionResultCacheInfo,
)
from dmtools.terrain.domain.coordinates import Bounds
from dmtools.terrain.domain.regional import (
    RegionalDetailSettings,
    RegionalSamplingRequest,
    detail_cell_window,
)
from dmtools.terrain.pipeline.detail import PreparedRegionalDetail, prepare_regional_detail
from dmtools.terrain.pipeline.generate import ProgressCallback
from dmtools.terrain.pipeline.parent import VerifiedTerrainParent, prepare_verified_parent


def _destination(source: Path, destination: Path) -> Path:
    target = destination.absolute()
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"Regional destination already exists: {target}")
    if target.resolve().is_relative_to(source.resolve()):
        raise ValueError("Regional output must be outside the immutable parent build directory.")
    return target


class ParentRegionSession:
    """Serial artifact generation with one parent, one detail context and bounded results.

    Loading validates files immediately; numerical replay waits for the first valid
    request. File/runtime drift closes the session. Cache arrays stay private.
    """

    def __init__(
        self, source: Path, *, result_cache_bytes: int = DEFAULT_RESULT_CACHE_BYTES,
    ) -> None:
        self._results = RegionResultCache(result_cache_bytes)
        self._runtime = runtime_identity()
        self._loaded: LoadedTerrainParent | None = load_terrain_parent(source, self._runtime)
        self._parent: VerifiedTerrainParent | None = None
        self._detail: PreparedRegionalDetail | None = None
        self._writing = False

    def _require_open(self) -> LoadedTerrainParent:
        if self._loaded is None:
            raise RuntimeError("Parent regional session is closed; open a new session.")
        return self._loaded

    def _verify_current(self) -> None:
        loaded = self._require_open()
        try:
            if runtime_identity() != self._runtime:
                raise ValueError("Generator source or runtime changed during regional generation.")
            loaded.verify_unchanged()
        except Exception:
            # Missing distribution metadata and unexpected verification errors
            # also make the saved runtime unsuitable for reuse.
            self._release()
            raise

    def cache_info(self) -> RegionResultCacheInfo:
        """Inspect retained numeric bytes and entries; excludes parent/geometry and scratch."""
        return self._results.info()

    def clear_cache(self) -> None:
        """Discard results and cell support while retaining the verified parent."""
        if self._writing:
            raise RuntimeError("Cannot clear a parent regional session during generation.")
        self._results.clear()
        if self._detail is not None:
            self._detail.clear_cache()

    def _release(self) -> None:
        self._results.clear()
        self._detail = None
        self._parent = None
        self._loaded = None

    def close(self) -> None:
        if self._writing:
            raise RuntimeError("Cannot close a parent regional session during generation.")
        self._release()

    def __enter__(self) -> Self:
        self._require_open()
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.close()

    def write(
        self, destination: Path, bounds_km: Bounds, refinement: int, *,
        detail_settings: RegionalDetailSettings | None = None,
        progress: ProgressCallback | None = None,
    ) -> Path:
        """Publish a new artifact, reusing exact requests only after freshness checks."""
        if self._writing:
            raise RuntimeError("Parent regional session is already generating; use it serially.")
        loaded = self._require_open()
        target = _destination(loaded.directory, destination)
        request = RegionalSamplingRequest.for_bounds(
            loaded.data.build_id, loaded.data.grid, bounds_km, refinement
        )
        if detail_settings is not None:
            detail_cell_window(request)
        self._writing = True
        try:
            self._verify_current()
            if self._parent is None:
                self._parent = prepare_verified_parent(loaded.data, progress)
            parent = self._parent
            key = request, detail_settings
            result = self._results.get(key)
            if result is None:
                if detail_settings is None:
                    result = ParentRegionResult(parent.sampler.sample(request, progress))
                else:
                    if self._detail is None:
                        self._detail = prepare_regional_detail(parent, detail_settings)
                    elif self._detail.settings != detail_settings:
                        self._detail = replace(self._detail, settings=detail_settings)
                    detail = self._detail.sample(request, progress)
                    result = ParentRegionResult(detail.samples, detail)
                self._verify_current()
                self._results.put(key, result)
            else:
                if progress is not None:
                    progress(1.0, "Reusing verified regional samples")
                # A callback can change files even on a cache hit.
                self._verify_current()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.mkdir()
            outputs = write_parent_region_products(result.samples, parent, target, result.detail)
            self._verify_current()
            return publish_parent_region_manifest(
                result.samples, loaded, parent, target, bounds_km=bounds_km,
                runtime=self._runtime, outputs=outputs, detail_settings=detail_settings,
                detail=result.detail,
            )
        finally:
            self._writing = False


def sample_parent_region(
    source: Path,
    destination: Path,
    bounds_km: Bounds,
    refinement: int,
    *,
    detail_settings: RegionalDetailSettings | None = None,
    progress: ProgressCallback | None = None,
) -> Path:
    target = _destination(source, destination)
    with ParentRegionSession(source, result_cache_bytes=0) as session:
        return session.write(
            target, bounds_km, refinement, detail_settings=detail_settings, progress=progress
        )
