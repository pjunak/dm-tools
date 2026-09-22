"""Strict current-build loading, hashes and bounded numeric decoding for regional reuse."""

import io
import json
from dataclasses import dataclass
from hashlib import sha256
from math import prod
from pathlib import Path
from typing import Any, cast
from zipfile import BadZipFile, ZipFile

import numpy as np
from numpy.typing import NDArray

from dmtools.terrain.adapters.build import BUILD_SCHEMA_VERSION, canonical_json, file_sha256
from dmtools.terrain.adapters.geotiff import geotiff_metadata
from dmtools.terrain.adapters.project import (
    INPUT_SNAPSHOT_VERSION,
    PROJECT_SCHEMA_VERSION,
    project_snapshot_from_json,
    settings_to_json,
)
from dmtools.terrain.domain import EndpointGrid, LocalMetricFrame
from dmtools.terrain.domain.seeds import (
    LANDFORM_STAGE_ID,
    RELIEF_STAGE_ID,
    SEED_POLICY_ID,
    stage_seed,
)
from dmtools.terrain.pipeline.diagnostics import DRAINAGE_DIAGNOSTICS_ALGORITHM_ID
from dmtools.terrain.pipeline.generate import (
    AUTOMATIC_VALLEY_ALGORITHM_ID,
    GENERATOR_ALGORITHM_ID,
    NOISE_ALGORITHM_ID,
)
from dmtools.terrain.pipeline.landforms import LANDFORM_ALGORITHM_ID
from dmtools.terrain.pipeline.parent import ParentRouting, ParentTerrainData

PRODUCT_ROLES = {
    **dict.fromkeys(
        ("elevation.npy", "land-mask.npy", "x-km.npy", "y-km.npy", "elevation.tif"), "authoritative"
    ),
    **dict.fromkeys(
        (
            "routing.npz",
            "water.npz",
            "basin-flow.npz",
            "diagnostics.json",
            "drainage.png",
            "cartographic.png",
            "scientific.png",
        ),
        "derived",
    ),
    "inputs.json": "input-snapshot",
}
_MAX_PRODUCT_BYTES = 512 * 1024 * 1024


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Parent {label} must be an object.")
    return cast(dict[str, Any], value)


def _digest(value: object) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(c not in "0123456789abcdef" for c in value)
    ):
        raise ValueError("Parent identity must be a lowercase SHA-256 digest.")
    return value


def _read(path: Path, limit: int) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError(f"Parent file missing, linked or oversized: {path.name}")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"Parent file grew beyond its limit: {path.name}")
    return data


def _array(data: bytes, shape: tuple[int, ...], dtype: str, label: str) -> NDArray[Any]:
    """Validate the NPY header and exact payload length before NumPy allocates."""
    stream = io.BytesIO(data)
    try:
        version = np.lib.format.read_magic(stream)
        if version != (1, 0):
            raise ValueError("Only current NPY v1 numeric payloads are supported.")
        actual_shape, fortran, actual_dtype = np.lib.format.read_array_header_1_0(stream)
        expected = np.dtype(dtype)
        if (
            actual_shape != shape
            or fortran
            or actual_dtype != expected
            or len(data) - stream.tell() != prod(shape) * expected.itemsize
        ):
            raise ValueError("Array shape, dtype, order or payload length mismatch.")
        stream.seek(0)
        result = cast(NDArray[Any], np.load(stream, allow_pickle=False))
        result.setflags(write=False)
        return result
    except (OSError, ValueError, EOFError) as error:
        raise ValueError(f"Invalid parent array {label}: {error}") from error


@dataclass(frozen=True, slots=True)
class LoadedTerrainParent:
    data: ParentTerrainData
    directory: Path
    manifest_sha256: str
    products: tuple[tuple[str, int, str], ...]
    runtime: dict[str, object]
    project_sha256: str
    svg_sha256: str

    def verify_unchanged(self) -> None:
        if file_sha256(self.directory / "manifest.json") != self.manifest_sha256:
            raise ValueError("Parent manifest changed during regional generation; retry.")
        for name, size, digest in self.products:
            path = self.directory / name
            if path.is_symlink() or path.stat().st_size != size or file_sha256(path) != digest:
                raise ValueError(f"Parent product changed or failed hash verification: {name}")


def load_terrain_parent(source: Path, runtime: dict[str, object]) -> LoadedTerrainParent:
    """Load only a completed current build in this exact runtime; original inputs are unneeded."""
    root = source.resolve(strict=True)
    raw_manifest = _read(root / "manifest.json", 1024 * 1024)
    document = _object(json.loads(raw_manifest), "manifest")
    required = {
        "schema",
        "schema_version",
        "status",
        "build_id",
        "inputs",
        "settings",
        "runtime",
        "algorithms",
        "coordinates",
        "routing_grid",
        "outputs",
        "warnings",
        "geotiff",
    }
    if (
        set(document) != required
        or document["schema"] != "dmtools.terrain-build"
        or type(document["schema_version"]) is not int
        or document["schema_version"] != BUILD_SCHEMA_VERSION
        or document["status"] != "complete"
    ):
        raise ValueError("Parent is not a completed current terrain build; rebuild it.")
    build_id = _digest(document["build_id"])
    if (
        sha256(canonical_json({k: v for k, v in document.items() if k != "build_id"})).hexdigest()
        != build_id
    ):
        raise ValueError("Parent build identity does not match its manifest.")
    if document["runtime"] != runtime:
        raise ValueError(
            "Parent runtime or generator source differs; rebuild with the current version."
        )
    outputs = _object(document["outputs"], "outputs")
    if set(outputs) != set(PRODUCT_ROLES):
        raise ValueError("Parent products do not match the current build contract.")
    products: list[tuple[str, int, str]] = []
    for name, role in PRODUCT_ROLES.items():
        entry = _object(outputs[name], name)
        if (
            set(entry) != {"bytes", "sha256", "role"}
            or type(entry["bytes"]) is not int
            or not 0 < entry["bytes"] <= _MAX_PRODUCT_BYTES
            or entry["role"] != role
        ):
            raise ValueError(f"Invalid parent product record: {name}")
        products.append((name, entry["bytes"], _digest(entry["sha256"])))
    inputs = _object(document["inputs"], "input provenance")
    if (
        set(inputs)
        != {"project_sha256", "svg_sha256", "project_schema_version", "snapshot_schema_version"}
        or inputs["project_schema_version"] != PROJECT_SCHEMA_VERSION
        or inputs["snapshot_schema_version"] != INPUT_SNAPSHOT_VERSION
    ):
        raise ValueError("Unsupported parent input provenance.")

    def read_product(name: str, limit: int) -> bytes:
        data = _read(root / name, limit)
        if (
            len(data) != outputs[name]["bytes"]
            or sha256(data).hexdigest() != outputs[name]["sha256"]
        ):
            raise ValueError(f"Parent product failed hash verification: {name}")
        return data

    project = project_snapshot_from_json(json.loads(read_product("inputs.json", 16 * 1024 * 1024)))
    settings = project.settings
    frame = LocalMetricFrame(project.coastline.bounds, settings.object_scale_km)
    grid = EndpointGrid.for_extent(frame.extent_km, settings.resolution_px)
    canonical = EndpointGrid.for_extent(frame.extent_km, 257, minimum_samples=3)
    expected_coordinates = {
        "model": frame.model_id,
        "world_crs": None,
        "planetary_radius_m": None,
        "source_bounds": list(frame.source_bounds),
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
        "width": grid.width,
        "height": grid.height,
        "x_spacing_km": grid.x_spacing_km,
        "y_spacing_km": grid.y_spacing_km,
    }
    algorithms = _object(document["algorithms"], "algorithms")
    expected_algorithms = {
        "generator": GENERATOR_ALGORITHM_ID,
        "drainage_diagnostics": DRAINAGE_DIAGNOSTICS_ALGORITHM_ID,
        "automatic_valleys": AUTOMATIC_VALLEY_ALGORITHM_ID,
        "noise": NOISE_ALGORITHM_ID,
        "landforms": LANDFORM_ALGORITHM_ID,
        "seed_policy": SEED_POLICY_ID,
        "stage_seeds": {
            stage: stage_seed(settings.seed, stage)
            for stage in (RELIEF_STAGE_ID, LANDFORM_STAGE_ID)
        },
    }
    if (
        document["settings"] != settings_to_json(settings)
        or document["coordinates"] != expected_coordinates
        or canonical_json(document["geotiff"]) != canonical_json(geotiff_metadata(grid))
        or document["routing_grid"]
        != {
            "width": canonical.width,
            "height": canonical.height,
            "x_spacing_km": canonical.x_spacing_km,
            "y_spacing_km": canonical.y_spacing_km,
        }
        or set(algorithms) != set(expected_algorithms)
        or any(algorithms[key] != value for key, value in expected_algorithms.items())
    ):
        raise ValueError("Parent settings, frame or algorithms disagree with its input snapshot.")
    shape, rshape = (grid.height, grid.width), (canonical.height, canonical.width)

    def array(name: str, shape: tuple[int, ...], dtype: str) -> NDArray[Any]:
        limit = prod(shape) * np.dtype(dtype).itemsize + 10_000
        return _array(read_product(name, limit), shape, dtype, name)

    def archive(
        name: str, specs: dict[str, tuple[tuple[int, ...], str]]
    ) -> dict[str, NDArray[Any]]:
        try:
            with ZipFile(io.BytesIO(read_product(name, _MAX_PRODUCT_BYTES))) as zipped:
                names = zipped.namelist()
                if len(names) != len(set(names)):
                    raise ValueError("Duplicate archive entries.")
                arrays: dict[str, NDArray[Any]] = {}
                for key, (shape, dtype) in specs.items():
                    info = zipped.getinfo(f"{key}.npy")
                    limit = prod(shape) * np.dtype(dtype).itemsize + 10_000
                    if info.file_size > limit:
                        raise ValueError("Oversized numeric archive entry.")
                    arrays[key] = _array(zipped.read(info), shape, dtype, f"{name}:{key}")
                return arrays
        except (BadZipFile, KeyError) as error:
            raise ValueError(f"Invalid parent archive {name}: {error}") from error

    water = archive("water.npz", {"surface_m": (shape, "<f4"), "intent_ids": (shape, "<u4")})
    routing = archive(
        "routing.npz",
        {
            "x_km": ((canonical.width,), "<f8"),
            "y_km": ((canonical.height,), "<f8"),
            "land_mask": (rshape, "bool"),
            "channel_mask": (rshape, "bool"),
            "receivers": (rshape, "<i8"),
            **{
                key: (rshape, "<f8")
                for key in (
                    "final_elevation_m",
                    "source_elevation_m",
                    "accumulation_km2",
                    "incision_m",
                    "incision_limit_m",
                )
            },
        },
    )
    data = ParentTerrainData(
        build_id,
        project,
        array("x-km.npy", (grid.width,), "<f8"),
        array("y-km.npy", (grid.height,), "<f8"),
        array("elevation.npy", shape, "<f4"),
        array("land-mask.npy", shape, "bool"),
        water["surface_m"],
        water["intent_ids"],
        ParentRouting(**routing),
    )
    loaded = LoadedTerrainParent(
        data,
        root,
        sha256(raw_manifest).hexdigest(),
        tuple(products),
        runtime,
        _digest(inputs["project_sha256"]),
        _digest(inputs["svg_sha256"]),
    )
    loaded.verify_unchanged()
    return loaded
