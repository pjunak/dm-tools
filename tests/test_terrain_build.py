# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportMissingTypeStubs=false
import json
import shutil
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest
import rasterio
from jsonschema import Draft202012Validator, ValidationError, validate
from PIL import Image
from referencing import Registry, Resource

from dmtools.cli import main
from dmtools.terrain.adapters.build import canonical_json, file_sha256
from dmtools.terrain.adapters.project import load_terrain_project, save_terrain_project
from dmtools.terrain.application import build as build_module
from dmtools.terrain.domain.seeds import RELIEF_STAGE_ID, SEED_POLICY_ID, stage_seed
from dmtools.terrain.pipeline.generate import generate_terrain

EXAMPLES = Path(__file__).parents[1] / "examples" / "terrain"


@pytest.fixture
def project_path(tmp_path: Path) -> Path:
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in ("coastline.svg", "example.dmterrain.json"):
        shutil.copyfile(EXAMPLES / name, inputs / name)
    path = inputs / "example.dmterrain.json"
    loaded = load_terrain_project(path)
    project = replace(
        loaded.project,
        settings=replace(loaded.project.settings, resolution_px=64),
    )
    save_terrain_project(project, loaded.coastline_source, path)
    return path


def test_headless_build_preserves_dem_and_has_repeatable_verified_products(
    project_path: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    original_project = project_path.read_bytes()
    loaded = load_terrain_project(project_path)
    original_svg = loaded.coastline_source.path.read_bytes()
    expected = generate_terrain(
        loaded.project.coastline, loaded.project.settings, constraints=loaded.project.constraints
    )
    first, second = tmp_path / "first", tmp_path / "second"
    assert main(["terrain", "build", str(project_path), "--output", str(first)]) == 0
    assert "Terrain build complete" in capsys.readouterr().out
    build_module.build_terrain_project(project_path, second)
    document: dict[str, Any] = json.loads((first / "manifest.json").read_text())
    schema_dir = EXAMPLES.parents[1] / "schemas" / "terrain"
    assert document["schema_version"] == 6
    assert document["inputs"]["project_schema_version"] == 4
    assert document["algorithms"]["seed_policy"] == SEED_POLICY_ID
    resolved_seed = stage_seed(loaded.project.settings.seed, RELIEF_STAGE_ID)
    assert document["algorithms"]["stage_seeds"] == {
        RELIEF_STAGE_ID: resolved_seed,
        "terrain.landforms": stage_seed(loaded.project.settings.seed, "terrain.landforms"),
    }
    schemas: list[dict[str, Any]] = [
        json.loads(path.read_text()) for path in sorted(schema_dir.glob("*.schema.json"))
    ]
    for item in schemas:
        Draft202012Validator.check_schema(item)
    registry = Registry[Any]().with_resources(
        (item["$id"], Resource.from_contents(item)) for item in schemas
    )
    schema = next(
        item for item in schemas
        if item["$id"] == "urn:dmtools:schema:terrain-build:6"
    )
    validate(document, schema, cls=Draft202012Validator, registry=registry)
    invalid = {**document, "coordinates": {**document["coordinates"], "world_crs": "EPSG:4326"}}
    with pytest.raises(ValidationError):
        validate(invalid, schema, cls=Draft202012Validator, registry=registry)
    missing_dem = {
        **document,
        "outputs": {
            key: value for key, value in document["outputs"].items() if key != "elevation.npy"
        },
    }
    with pytest.raises(ValidationError):
        validate(missing_dem, schema, cls=Draft202012Validator, registry=registry)
    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()
    build_id = document.pop("build_id")
    assert sha256(canonical_json(document)).hexdigest() == build_id
    assert document["status"] == "complete"
    for name, product in document["outputs"].items():
        assert file_sha256(first / name) == product["sha256"]
        assert (first / name).stat().st_size == product["bytes"]
        assert (first / name).read_bytes() == (second / name).read_bytes()
    elevation = np.load(first / "elevation.npy", allow_pickle=False)
    assert elevation.dtype == np.dtype("<f4")
    assert np.array_equal(elevation, expected.elevation_m, equal_nan=True)
    assert np.array_equal(np.load(first / "land-mask.npy"), expected.land_mask)
    assert np.array_equal(np.load(first / "x-km.npy"), expected.x_km)
    assert np.array_equal(np.load(first / "y-km.npy"), expected.y_km)
    assert np.isnan(elevation[~expected.land_mask]).all()
    with cast(Any, rasterio.open(first / "elevation.tif")) as raster:
        assert raster.read(1).tobytes() == elevation.tobytes()
        assert raster.tags()["numeric_source_sha256"] == file_sha256(first / "elevation.npy")
        assert document["geotiff"]["affine_m"] == list(raster.transform)[:6]
        assert document["geotiff"]["bounds_m"] == list(raster.bounds)
    assert document["runtime"]["gdal"]
    assert document["runtime"]["proj"]
    missing_tiff = {
        **document,
        "outputs": {key: value for key, value in document["outputs"].items()
                    if key != "elevation.tif"},
    }
    with pytest.raises(ValidationError):
        validate(missing_tiff, schema, cls=Draft202012Validator, registry=registry)

    assert document["coordinates"]["world_crs"] is None
    assert document["coordinates"]["registration"] == "endpoint-nodes"
    assert document["routing_grid"]["width"] == expected.routing_grid_shape[1]
    assert document["routing_grid"]["width"] != document["coordinates"]["width"]
    diagnostics: dict[str, Any] = json.loads((first / "diagnostics.json").read_text())
    assert diagnostics["elevation_sha256"] == file_sha256(first / "elevation.npy")
    assert diagnostics["delivered_surface_quality"]["land_sample_count"] == int(
        expected.land_mask.sum()
    )
    with np.load(first / "routing.npz", allow_pickle=False) as routing:
        np.testing.assert_array_equal(routing["receivers"], expected.routing.receivers)
        np.testing.assert_array_equal(routing["source_elevation_m"],
                                      expected.routing.source_elevation_m)
        np.testing.assert_array_equal(routing["final_elevation_m"],
                                      expected.routing_final_elevation_m)
        np.testing.assert_array_equal(routing["land_mask"], expected.routing_land_mask)
        assert routing["x_km"].size == expected.routing_grid.width
    assert diagnostics["routing_sha256"] == file_sha256(first / "routing.npz")
    assert diagnostics["routing_agreement"]["algorithm_id"] == "planned-final-d8-agreement@1"
    for missing_name in ("routing.npz", "drainage.png"):
        incomplete = {**document, "outputs": {
            key: value for key, value in document["outputs"].items() if key != missing_name
        }}
        with pytest.raises(ValidationError):
            validate(incomplete, schema, cls=Draft202012Validator, registry=registry)
    with Image.open(first / "drainage.png") as review:
        assert review.width > 2 * expected.routing_grid.width
        assert review.height > expected.routing_grid.height
    with Image.open(first / "scientific.png") as preview:
        assert preview.size == (expected.width, expected.height)
        assert preview.info["dmtools.render_style"] == "scientific"
    assert project_path.read_bytes() == original_project
    assert loaded.coastline_source.path.read_bytes() == original_svg


def test_existing_destination_is_rejected_without_generation_or_changes(
    project_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "authored.txt"
    sentinel.write_text("keep")

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Existing output should be rejected before generation.")

    monkeypatch.setattr(build_module, "generate_terrain", forbidden)
    with pytest.raises(FileExistsError):
        build_module.build_terrain_project(project_path, output)
    assert sentinel.read_text() == "keep"
    assert list(output.iterdir()) == [sentinel]


def test_failed_export_never_publishes_completion(
    project_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_export(*args: object, **kwargs: object) -> None:
        raise OSError("simulated disk failure")

    monkeypatch.setattr(build_module, "write_build_products", fail_export)
    output = tmp_path / "failed"
    with pytest.raises(OSError, match="simulated disk failure"):
        build_module.build_terrain_project(project_path, output)
    assert output.is_dir()
    assert not (output / "manifest.json").exists()


@pytest.mark.parametrize("edited_input", ["project", "svg"])
def test_mid_build_input_edit_rejects_completion(
    project_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    edited_input: str,
) -> None:
    original_writer = build_module.write_build_products
    edited_path = (
        project_path
        if edited_input == "project"
        else load_terrain_project(project_path).coastline_source.path
    )

    def mutate(*args: Any, **kwargs: Any) -> dict[str, object]:
        result = original_writer(*args, **kwargs)
        with edited_path.open("a") as stream:
            stream.write("\n")
        return result

    monkeypatch.setattr(build_module, "write_build_products", mutate)
    output = tmp_path / "changed"
    with pytest.raises(ValueError, match="changed during the build"):
        build_module.build_terrain_project(project_path, output)
    assert not (output / "manifest.json").exists()


def test_source_identity_change_rejects_completion(
    project_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def identity() -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"source_revision": calls}

    monkeypatch.setattr(build_module, "runtime_identity", identity)
    output = tmp_path / "source-changed"
    with pytest.raises(ValueError, match="Generator source or runtime changed"):
        build_module.build_terrain_project(project_path, output)
    assert not (output / "manifest.json").exists()


def test_manifest_publication_failure_leaves_only_pending_manifest(
    project_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dmtools.terrain.adapters import build as artifact_module

    def fail_publish(source: Path, target: Path) -> None:
        raise OSError("simulated publication failure")

    monkeypatch.setattr(artifact_module.os, "replace", fail_publish)
    output = tmp_path / "publication-failed"
    with pytest.raises(OSError, match="simulated publication failure"):
        build_module.build_terrain_project(project_path, output)
    assert (output / ".manifest.pending").is_file()
    assert not (output / "manifest.json").exists()


def test_cli_build_reports_missing_input_without_completion(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "output"
    assert main(["terrain", "build", str(tmp_path / "missing.json"), "--output", str(output)]) == 1
    assert "Terrain build failed" in capsys.readouterr().err
    assert not output.exists()


def test_geotiff_failure_cannot_publish_a_completed_build(
    project_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dmtools.terrain.adapters import build as artifact_module

    def fail_geotiff(*args: object, **kwargs: object) -> None:
        raise OSError("simulated GeoTIFF failure")

    monkeypatch.setattr(artifact_module, "write_terrain_geotiff", fail_geotiff)
    output = tmp_path / "failed-tiff"
    with pytest.raises(OSError, match="simulated GeoTIFF failure"):
        build_module.build_terrain_project(project_path, output)
    assert (output / "elevation.npy").exists()
    assert not (output / "manifest.json").exists()
