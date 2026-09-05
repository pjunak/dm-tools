"""Numeric build products and a manifest for the existing local coordinate plane."""

import json
import os
import platform
import sys
from dataclasses import asdict
from hashlib import file_digest, sha256
from importlib.metadata import version
from pathlib import Path

import numpy as np
import shapely

import dmtools
from dmtools.terrain.adapters.project import PROJECT_SCHEMA_VERSION
from dmtools.terrain.adapters.render import render_height_map, save_height_map
from dmtools.terrain.domain import LocalMetricFrame, TerrainProject
from dmtools.terrain.pipeline.generate import (
    AUTOMATIC_VALLEY_ALGORITHM_ID,
    GENERATOR_ALGORITHM_ID,
    NOISE_ALGORITHM_ID,
    GeneratedTerrain,
)
from dmtools.terrain.pipeline.quality import TerrainQuality


def file_sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def runtime_identity() -> dict[str, object]:
    """Fingerprint installed source, including editable changes, without Git."""
    package = Path(dmtools.__file__).parent
    sources = {
        path.relative_to(package).as_posix(): file_sha256(path)
        for path in sorted(package.rglob("*.py"))
    }
    return {
        "dmtools_version": dmtools.__version__,
        "package_source_sha256": sha256(canonical_json(sources)).hexdigest(),
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "byteorder": sys.byteorder,
        "dependencies": {
            name: version(name) for name in ("numpy", "Pillow", "shapely", "svgelements")
        },
        "geos": shapely.geos_version_string,
    }


def _write_json(path: Path, value: object) -> None:
    data = canonical_json(value)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def write_build_products(
    terrain: GeneratedTerrain,
    project: TerrainProject,
    quality: TerrainQuality,
    destination: Path,
) -> dict[str, object]:
    """Write to an exclusively reserved build directory; return file identities."""
    paths: list[tuple[str, str]] = []
    for name, array in (
        ("elevation.npy", terrain.elevation_m.astype("<f4", copy=False)),
        ("land-mask.npy", terrain.land_mask),
        ("x-km.npy", terrain.x_km.astype("<f8", copy=False)),
        ("y-km.npy", terrain.y_km.astype("<f8", copy=False)),
    ):
        with (destination / name).open("xb") as stream:
            np.save(stream, array, allow_pickle=False)
            stream.flush()
            os.fsync(stream.fileno())
        paths.append((name, "authoritative"))
    _write_json(destination / "inputs.json", asdict(project))
    paths.append(("inputs.json", "input-snapshot"))
    _write_json(
        destination / "diagnostics.json",
        {
            "delivered_surface_quality": asdict(quality),
            "canonical_drainage": asdict(terrain.drainage),
            "elevation_sha256": file_sha256(destination / "elevation.npy"),
        },
    )
    paths.append(("diagnostics.json", "derived"))
    for style in ("cartographic", "scientific"):
        name = f"{style}.png"
        with render_height_map(terrain, style=style) as image:
            save_height_map(image, terrain, destination / name)
        paths.append((name, "derived"))
    return {
        name: {
            "sha256": file_sha256(destination / name),
            "bytes": (destination / name).stat().st_size,
            "role": role,
        }
        for name, role in paths
    }


def publish_build_manifest(
    terrain: GeneratedTerrain,
    project: TerrainProject,
    destination: Path,
    *,
    project_sha256: str,
    svg_sha256: str,
    runtime: dict[str, object],
    outputs: dict[str, object],
) -> Path:
    """Publish completion last, after inputs and all products have been checked."""
    frame = LocalMetricFrame(project.coastline.bounds, project.settings.object_scale_km)
    grid, routing_grid = terrain.grid, terrain.routing_grid
    document: dict[str, object] = {
        "schema": "dmtools.terrain-build",
        "schema_version": 1,
        "status": "complete",
        "inputs": {
            "project_sha256": project_sha256,
            "svg_sha256": svg_sha256,
            "project_schema_version": PROJECT_SCHEMA_VERSION,
        },
        "settings": asdict(project.settings),
        "runtime": runtime,
        "algorithms": {
            "generator": GENERATOR_ALGORITHM_ID,
            "automatic_valleys": AUTOMATIC_VALLEY_ALGORITHM_ID,
            "noise": NOISE_ALGORITHM_ID,
            "drainage_diagnostics": terrain.drainage.algorithm_id,
            "seed_policy": "legacy-shared-coordinate-seed@1",
            "full_detail_seed": project.settings.seed,
            "macro_detail_seed": project.settings.seed,
        },
        "coordinates": {
            "model": frame.model_id,
            "world_crs": None,
            "planetary_radius_m": None,
            "source_bounds": frame.source_bounds,
            "km_per_source_unit": frame.km_per_source_unit,
            "origin": "minimum source x and y",
            "x_direction": "source-right",
            "y_direction": "source-down",
            "registration": grid.registration,
            "horizontal_units": "km",
            "elevation_units": "m",
            "elevation_dtype": "float32",
            "nodata": "NaN outside land mask",
            "extent_km": list(grid.extent_km),
            "width": terrain.width,
            "height": terrain.height,
            "x_spacing_km": grid.x_spacing_km,
            "y_spacing_km": grid.y_spacing_km,
        },
        "routing_grid": {
            "width": routing_grid.width,
            "height": routing_grid.height,
            "x_spacing_km": routing_grid.x_spacing_km,
            "y_spacing_km": routing_grid.y_spacing_km,
        },
        "outputs": outputs,
        "warnings": [
            "Local SVG plane only; world georeferencing and planetary scale are unspecified.",
            "Canonical drainage diagnostics use a separate grid, not the exported DEM grid.",
            "Existing macro and detail noise share a seed; independent stage seeds are deferred.",
        ],
    }
    document["build_id"] = sha256(canonical_json(document)).hexdigest()
    pending = destination / ".manifest.pending"
    _write_json(pending, document)
    manifest = destination / "manifest.json"
    os.replace(pending, manifest)
    return manifest
