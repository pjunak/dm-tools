# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportMissingTypeStubs=false
"""Portable parent replay, bounded decoding and atomic regional publication."""

import gc
import io
import json
import shutil
import weakref
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from jsonschema import Draft202012Validator, ValidationError, validate
from referencing import Registry, Resource

from benchmarks.terrain import fixture
from dmtools.cli import main
from dmtools.terrain.adapters.build import canonical_json, file_sha256, runtime_identity
from dmtools.terrain.adapters.parent import load_terrain_parent
from dmtools.terrain.adapters.parent_region import (
    publish_parent_region_manifest,
    write_parent_region_products,
)
from dmtools.terrain.adapters.project import (
    load_terrain_project,
    project_snapshot_from_json,
    project_snapshot_to_json,
    save_terrain_project,
)
from dmtools.terrain.application import parent_region as application
from dmtools.terrain.application.build import build_terrain_project
from dmtools.terrain.domain import TerrainProject
from dmtools.terrain.domain.regional import RegionalDetailSettings, RegionalSamplingRequest
from dmtools.terrain.pipeline.detail import prepare_regional_detail
from dmtools.terrain.pipeline.parent import prepare_verified_parent
from dmtools.terrain.pipeline.regional import TerrainRegionSampler

ROOT = Path(__file__).parents[1]


def validate_schema(value: object, identity: str) -> None:
    schemas: list[dict[str, Any]] = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in (ROOT / "schemas/terrain").glob("*.schema.json")
    ]
    registry = Registry[Any]().with_resources(
        (s["$id"], Resource.from_contents(s)) for s in schemas
    )
    schema = next(s for s in schemas if s["$id"] == identity)
    validate(value, schema, cls=Draft202012Validator, registry=registry)


@pytest.mark.parametrize("case", ["example", "archipelago", "authored", "regional", "water"])
def test_portable_snapshot_round_trip(case: str) -> None:
    coast, settings, constraints = fixture(case, 65, 42)
    project = TerrainProject(coast, settings, tuple(constraints))
    document = json.loads(canonical_json(project_snapshot_to_json(project)))
    assert project_snapshot_from_json(document) == project
    validate_schema(document, "urn:dmtools:schema:terrain-input-snapshot:1")
    document["constraints"].append({"type": "mystery"})
    with pytest.raises(ValueError):
        project_snapshot_from_json(document)


@pytest.fixture(scope="module")
def saved_parent(tmp_path_factory: pytest.TempPathFactory) -> Path:
    folder = tmp_path_factory.mktemp("saved-parent")
    inputs = folder / "inputs"
    inputs.mkdir()
    for name in ("coastline.svg", "basin-water.dmterrain.json"):
        shutil.copyfile(ROOT / "examples/terrain" / name, inputs / name)
    path = inputs / "basin-water.dmterrain.json"
    loaded = load_terrain_project(path)
    project = replace(
        loaded.project,
        settings=replace(loaded.project.settings, resolution_px=65, detail_levels=2, seed=42),
    )
    save_terrain_project(project, loaded.coastline_source, path)
    build_terrain_project(path, folder / "parent")
    # A finished parent must not consult either original file again.
    path.rename(inputs / "project-moved.json")
    (inputs / "coastline.svg").rename(inputs / "coastline-moved.svg")
    return folder / "parent"


def test_parent_replays_all_nodes_and_keeps_owned_data_read_only(saved_parent: Path) -> None:
    loaded = load_terrain_parent(saved_parent, runtime_identity())
    parent = prepare_verified_parent(loaded.data)
    grid = parent.sampler.reference_grid
    request = RegionalSamplingRequest(
        loaded.data.build_id, grid, 1, (0, 0, grid.width - 1, grid.height - 1)
    )
    samples = parent.sampler.sample(request)
    np.testing.assert_array_equal(samples.elevation_m, loaded.data.elevation_m)
    np.testing.assert_array_equal(samples.water_surface_m, loaded.data.water_surface_m)
    assert parent.verified_ground_nodes == grid.width * grid.height
    assert parent.verified_routing_nodes == loaded.data.routing.land_mask.size
    assert not loaded.data.elevation_m.flags.writeable
    assert not parent.sampler.prepared_field.automatic_valleys.drainage.receivers.flags.writeable
    loaded.verify_unchanged()


def rewrite_manifest(folder: Path, document: dict[str, Any]) -> None:
    document.pop("build_id", None)
    document["build_id"] = sha256(canonical_json(document)).hexdigest()
    (folder / "manifest.json").write_bytes(canonical_json(document))


@pytest.mark.parametrize(
    "fault",
    [
        "incomplete",
        "version",
        "identity",
        "runtime",
        "frame",
        "path",
        "missing",
        "corrupt",
        "snapshot",
        "header",
    ],
)
def test_invalid_parent_is_rejected_before_preparation_or_output(
    saved_parent: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    folder = tmp_path / "parent"
    shutil.copytree(saved_parent, folder)
    document: dict[str, Any] = json.loads((folder / "manifest.json").read_bytes())
    if fault == "incomplete":
        document["status"] = "pending"
    elif fault == "version":
        document["schema_version"] -= 1
    elif fault == "runtime":
        document["runtime"]["package_source_sha256"] = "0" * 64
    elif fault == "frame":
        document["coordinates"]["horizontal_units"] = "m"
    elif fault == "path":
        document["outputs"]["../unexpected.npy"] = document["outputs"].pop("elevation.npy")
    elif fault == "missing":
        (folder / "land-mask.npy").unlink()
    elif fault == "corrupt":
        with (folder / "scientific.png").open("ab") as stream:
            stream.write(b"broken")
    elif fault == "snapshot":
        value = json.loads((folder / "inputs.json").read_bytes())
        value["settings"]["maximum_elevation_m"] += 10
        (folder / "inputs.json").write_bytes(canonical_json(value))
        document["outputs"]["inputs.json"].update(
            sha256=file_sha256(folder / "inputs.json"),
            bytes=(folder / "inputs.json").stat().st_size,
        )
    elif fault == "header":
        stream = io.BytesIO()
        np.lib.format.write_array_header_1_0(
            stream, {"descr": "<f4", "fortran_order": False, "shape": (2**40, 2**40)}
        )
        (folder / "elevation.npy").write_bytes(stream.getvalue())
        document["outputs"]["elevation.npy"].update(
            sha256=file_sha256(folder / "elevation.npy"), bytes=len(stream.getvalue())
        )
    rewrite_manifest(folder, document)
    if fault == "identity":
        document["build_id"] = "0" * 64
        (folder / "manifest.json").write_bytes(canonical_json(document))

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Invalid files must fail before global field preparation.")

    monkeypatch.setattr(application, "prepare_verified_parent", forbidden)
    output = tmp_path / "result"
    with pytest.raises((OSError, ValueError)):
        application.sample_parent_region(folder, output, (100.0, 100.0, 200.0, 200.0), 8)
    assert not output.exists()


def test_replay_rejects_numerically_changed_parent_even_with_matching_hashes(
    saved_parent: Path,
    tmp_path: Path,
) -> None:
    folder = tmp_path / "parent"
    shutil.copytree(saved_parent, folder)
    elevation = np.load(folder / "elevation.npy", allow_pickle=False)
    elevation[20, 20] += 1
    np.save(folder / "elevation.npy", elevation, allow_pickle=False)
    document: dict[str, Any] = json.loads((folder / "manifest.json").read_bytes())
    document["outputs"]["elevation.npy"]["sha256"] = file_sha256(folder / "elevation.npy")
    rewrite_manifest(folder, document)
    loaded = load_terrain_parent(folder, runtime_identity())
    with pytest.raises(ValueError, match="replay mismatch in ground"):
        prepare_verified_parent(loaded.data)


@pytest.mark.parametrize("detail", [False, True])
def test_parent_cli_artifacts_are_repeatable_and_schema_bound(
    saved_parent: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    detail: bool,
) -> None:
    before = {p.name: file_sha256(p) for p in saved_parent.iterdir()}
    first, second = tmp_path / "first", tmp_path / "second"
    bounds = (1100.0, 1100.0, 1700.0, 1700.0)
    command = "enrich-region" if detail else "sample-parent"
    args = [
        "terrain",
        command,
        str(saved_parent),
        "--output",
        str(first),
        "--bounds-km",
        *map(str, bounds),
        "--refine",
        "8",
    ]
    if detail:
        args += ["--experimental", "--amplitude-m", "12"]
    assert main(args) == 0, capsys.readouterr().err
    assert "Parent regional result complete" in capsys.readouterr().out
    application.sample_parent_region(
        saved_parent,
        second,
        bounds,
        8,
        detail_settings=RegionalDetailSettings() if detail else None,
    )
    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()
    document: dict[str, Any] = json.loads((first / "manifest.json").read_bytes())
    validate_schema(document, "urn:dmtools:schema:terrain-parent-region:1")
    for key in ("refines_hydrology", "small_rivers_ready"):
        with pytest.raises(ValidationError):
            validate_schema(
                {**document, "capabilities": {**document["capabilities"], key: True}},
                "urn:dmtools:schema:terrain-parent-region:1",
            )
    for name, product in document["outputs"].items():
        assert file_sha256(first / name) == product["sha256"]
        assert (first / name).read_bytes() == (second / name).read_bytes()
    identity = document.pop("artifact_id")
    assert identity == sha256(canonical_json(document)).hexdigest()
    assert before == {p.name: file_sha256(p) for p in saved_parent.iterdir()}
    if detail:
        runtime = runtime_identity()
        loaded = load_terrain_parent(saved_parent, runtime)
        parent = prepare_verified_parent(loaded.data)
        settings = RegionalDetailSettings()
        context = prepare_regional_detail(parent, settings)
        request = RegionalSamplingRequest.for_bounds(
            parent.data.build_id, parent.data.grid, bounds, 8
        )
        context.sample(request)
        warmed = context.sample(request)
        assert context.cache_info().hits == warmed.evidence.parent_cells
        destination = tmp_path / "warm"
        destination.mkdir()
        outputs = write_parent_region_products(warmed.samples, parent, destination, warmed)
        publish_parent_region_manifest(
            warmed.samples, loaded, parent, destination, bounds_km=bounds, runtime=runtime,
            outputs=outputs, detail_settings=settings, detail=warmed,
        )
        for artifact in first.iterdir():
            assert artifact.read_bytes() == (destination / artifact.name).read_bytes()


def test_parent_changes_during_export_prevent_completion(
    saved_parent: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    folder = tmp_path / "parent"
    shutil.copytree(saved_parent, folder)
    original = application.write_parent_region_products

    def change(*args: Any, **kwargs: Any) -> dict[str, object]:
        result = original(*args, **kwargs)
        with (folder / "scientific.png").open("ab") as stream:
            stream.write(b"changed")
        return result

    monkeypatch.setattr(application, "write_parent_region_products", change)
    output = tmp_path / "result"
    with pytest.raises(ValueError, match="changed"):
        application.sample_parent_region(folder, output, (100.0, 100.0, 200.0, 200.0), 8)
    assert output.is_dir() and not (output / "manifest.json").exists()


def test_parent_and_existing_destinations_are_protected(saved_parent: Path, tmp_path: Path) -> None:
    for output in (saved_parent, saved_parent / "child", tmp_path):
        with pytest.raises((FileExistsError, ValueError)):
            application.sample_parent_region(saved_parent, output, (100.0, 100.0, 200.0, 200.0), 8)


def test_excessive_detail_work_is_rejected_before_preparation(
    saved_parent: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Reject invalid detail density before preparation.")

    monkeypatch.setattr(application, "prepare_verified_parent", forbidden)
    with pytest.raises(ValueError, match="at least 8"):
        application.sample_parent_region(
            saved_parent,
            tmp_path / "out",
            (100.0, 100.0, 200.0, 200.0),
            4,
            detail_settings=RegionalDetailSettings(),
        )


def test_detail_cli_requires_explicit_experimental_flag() -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "terrain",
                "enrich-region",
                "parent",
                "--output",
                "child",
                "--bounds-km",
                "1",
                "1",
                "2",
                "2",
                "--refine",
                "8",
            ]
        )


@pytest.mark.parametrize("settings", [None, RegionalDetailSettings()])
def test_session_replays_once_and_reuses_exact_artifacts(
    saved_parent: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    settings: RegionalDetailSettings | None,
) -> None:
    bounds = (1100., 1100., 1700., 1700.)
    application.sample_parent_region(
        saved_parent, tmp_path / "control", bounds, 8, detail_settings=settings,
    )
    replay = application.prepare_verified_parent
    calls = 0

    def count(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        return replay(*args, **kwargs)

    monkeypatch.setattr(application, "prepare_verified_parent", count)
    with application.ParentRegionSession(saved_parent) as session:
        session.write(tmp_path / "first", bounds, 8, detail_settings=settings)

        def forbidden(*_args: object, **_kwargs: object) -> None:
            pytest.fail("Cached requests must reuse prepared parents and complete numeric results.")

        monkeypatch.setattr(application, "prepare_verified_parent", forbidden)
        monkeypatch.setattr(TerrainRegionSampler, "sample", forbidden)
        session.write(tmp_path / "cached", bounds, 8, detail_settings=settings)
        assert calls == 1
        info = session.cache_info()
        assert (info.entries, info.hits, info.misses) == (1, 1, 1)
        assert 0 < info.retained_bytes <= info.budget_bytes
        for artifact in (tmp_path / "control").iterdir():
            for folder in ("first", "cached"):
                assert artifact.read_bytes() == (tmp_path / folder / artifact.name).read_bytes()
    assert session.cache_info().entries == session.cache_info().retained_bytes == 0
    with pytest.raises(RuntimeError, match="closed"):
        session.write(tmp_path / "closed", bounds, 8)
    assert not (tmp_path / "closed").exists()


def test_session_keys_include_mode_settings_and_density_but_preserve_requested_bounds(
    saved_parent: Path, tmp_path: Path,
) -> None:
    bounds = (1100., 1100., 1700., 1700.)
    with application.ParentRegionSession(saved_parent) as session:
        for index, (factor, settings) in enumerate((
            (8, None), (8, RegionalDetailSettings(12.)),
            (8, RegionalDetailSettings(30.)), (16, None),
        )):
            session.write(tmp_path / str(index), bounds, factor, detail_settings=settings)
            assert session.cache_info().hits == 0
        assert session.cache_info().entries == 4
        smaller = (1100.01, 1100.01, 1699.99, 1699.99)
        session.write(tmp_path / "alias", smaller, 8)
        assert session.cache_info().hits == 1
        a = json.loads((tmp_path / "0/manifest.json").read_bytes())
        b = json.loads((tmp_path / "alias/manifest.json").read_bytes())
        assert a["request"]["window_inclusive"] == b["request"]["window_inclusive"]
        assert b["request"]["requested_bounds_km"] == list(smaller)
        assert a["artifact_id"] != b["artifact_id"]
        assert (
            (tmp_path / "0/samples.npz").read_bytes()
            == (tmp_path / "alias/samples.npz").read_bytes()
        )


@pytest.mark.parametrize(
    "fault", ["product", "manifest", "runtime", "runtime-unavailable", "hit-callback"]
)
def test_session_closes_and_discards_caches_on_parent_or_runtime_drift(
    saved_parent: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str,
) -> None:
    folder = tmp_path / "parent"
    shutil.copytree(saved_parent, folder)
    bounds = (1100., 1100., 1700., 1700.)
    with application.ParentRegionSession(folder) as session:
        session.write(tmp_path / "first", bounds, 8)
        assert session.cache_info().entries == 1

        def change(_fraction: float, _label: str) -> None:
            with (folder / "scientific.png").open("ab") as stream:
                stream.write(b"changed")

        if fault == "runtime":
            monkeypatch.setattr(application, "runtime_identity", lambda: {"changed": True})
        elif fault == "runtime-unavailable":
            def unavailable() -> None:
                raise RuntimeError("Runtime identity changed or became unavailable")

            monkeypatch.setattr(application, "runtime_identity", unavailable)
        elif fault == "product":
            change(0., "")
        elif fault == "manifest":
            with (folder / "manifest.json").open("ab") as stream:
                stream.write(b" ")
        expected_error = RuntimeError if fault == "runtime-unavailable" else ValueError
        with pytest.raises(expected_error, match="changed"):
            session.write(
                tmp_path / "stale", bounds, 8,
                progress=change if fault == "hit-callback" else None,
            )
        assert not (tmp_path / "stale").exists()
        assert session.cache_info().entries == session.cache_info().retained_bytes == 0
        with pytest.raises(RuntimeError, match="closed"):
            session.write(tmp_path / "retry", bounds, 8)


@pytest.mark.parametrize("budget", [0, 1])
def test_session_bypasses_small_budgets_and_reuses_parent_after_clear(
    saved_parent: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, budget: int,
) -> None:
    bounds = (1100., 1100., 1700., 1700.)
    with application.ParentRegionSession(saved_parent, result_cache_bytes=budget) as session:
        session.write(tmp_path / "first", bounds, 8)
        assert session.cache_info().entries == 0
        assert session.cache_info().bypasses == 1
        session.clear_cache()

        def forbidden(*_args: object, **_kwargs: object) -> None:
            pytest.fail("Clearing result/cell caches must retain the verified parent.")

        monkeypatch.setattr(application, "prepare_verified_parent", forbidden)
        session.write(tmp_path / "second", bounds, 8)
        for artifact in (tmp_path / "first").iterdir():
            assert artifact.read_bytes() == (tmp_path / "second" / artifact.name).read_bytes()


def test_session_export_failure_can_retry_cached_result_to_a_new_destination(
    saved_parent: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bounds = (1100., 1100., 1700., 1700.)
    writer = application.write_parent_region_products
    with application.ParentRegionSession(saved_parent) as session:
        def fail(*_args: object, **_kwargs: object) -> None:
            raise OSError("export unavailable")

        monkeypatch.setattr(application, "write_parent_region_products", fail)
        with pytest.raises(OSError, match="export unavailable"):
            session.write(tmp_path / "partial", bounds, 8)
        assert (tmp_path / "partial").is_dir()
        assert not (tmp_path / "partial/manifest.json").exists()
        assert session.cache_info().entries == 1
        monkeypatch.setattr(application, "write_parent_region_products", writer)
        session.write(tmp_path / "retry", bounds, 8)
        assert session.cache_info().hits == 1
        assert (tmp_path / "retry/manifest.json").is_file()


def test_session_rejects_reentrant_generation_and_lifecycle_changes(
    saved_parent: Path, tmp_path: Path,
) -> None:
    bounds = (1100., 1100., 1700., 1700.)
    with application.ParentRegionSession(saved_parent) as session:
        session.write(tmp_path / "first", bounds, 8)

        def reenter(_fraction: float, _label: str) -> None:
            with pytest.raises(RuntimeError, match="serially"):
                session.write(tmp_path / "nested", bounds, 8)
            for action in (session.clear_cache, session.close):
                with pytest.raises(RuntimeError, match="during generation"):
                    action()

        session.write(tmp_path / "cached", bounds, 8, progress=reenter)
        assert not (tmp_path / "nested").exists()


def test_session_eviction_recomputes_identical_products_within_byte_budget(
    saved_parent: Path, tmp_path: Path,
) -> None:
    grid = load_terrain_parent(saved_parent, runtime_identity()).data.grid
    dx, dy = grid.x_spacing_km, grid.y_spacing_km
    first_bounds = (20 * dx, 10 * dy, 28 * dx, 18 * dy)
    other_bounds = (21 * dx, 10 * dy, 29 * dx, 18 * dy)
    with application.ParentRegionSession(saved_parent) as probe:
        probe.write(tmp_path / "control", first_bounds, 8)
        budget = probe.cache_info().retained_bytes
    with application.ParentRegionSession(saved_parent, result_cache_bytes=budget) as session:
        for index, bounds in enumerate((first_bounds, other_bounds, first_bounds)):
            session.write(tmp_path / f"evict-{index}", bounds, 8)
            info = session.cache_info()
            assert info.entries == 1 and info.retained_bytes == budget
        assert session.cache_info().evictions == 2
        assert session.cache_info().misses == 3
        for artifact in (tmp_path / "control").iterdir():
            assert artifact.read_bytes() == (tmp_path / "evict-2" / artifact.name).read_bytes()


def test_failed_sampling_is_not_cached_and_session_can_retry(
    saved_parent: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    method = TerrainRegionSampler.sample
    bounds = (1100., 1100., 1700., 1700.)
    with application.ParentRegionSession(saved_parent) as session:
        def fail(*_args: object, **_kwargs: object) -> None:
            raise ValueError("sample unavailable")

        monkeypatch.setattr(TerrainRegionSampler, "sample", fail)
        with pytest.raises(ValueError, match="sample unavailable"):
            session.write(tmp_path / "failed", bounds, 8)
        assert session.cache_info().entries == 0
        assert not (tmp_path / "failed").exists()
        monkeypatch.setattr(TerrainRegionSampler, "sample", method)
        session.write(tmp_path / "retried", bounds, 8)
        assert session.cache_info().misses == 2
        assert session.cache_info().entries == 1


def test_session_close_releases_parent_and_prepared_arrays(
    saved_parent: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    load = application.load_terrain_parent
    prepare = application.prepare_verified_parent
    references: list[weakref.ReferenceType[Any]] = []

    def record_load(*args: Any, **kwargs: Any) -> Any:
        parent = load(*args, **kwargs)
        references.append(weakref.ref(parent.data.elevation_m))
        return parent

    def record_prepare(*args: Any, **kwargs: Any) -> Any:
        parent = prepare(*args, **kwargs)
        references.append(weakref.ref(parent.sampler.prepared_field.automatic_valleys.x_km))
        return parent

    monkeypatch.setattr(application, "load_terrain_parent", record_load)
    monkeypatch.setattr(application, "prepare_verified_parent", record_prepare)
    with application.ParentRegionSession(saved_parent) as session:
        session.write(
            tmp_path / "detail", (1100., 1100., 1700., 1700.), 8,
            detail_settings=RegionalDetailSettings(),
        )
        assert len(references) == 2 and all(ref() is not None for ref in references)
    gc.collect()
    assert all(ref() is None for ref in references)
