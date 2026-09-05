import json
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator, validate
from referencing import Registry, Resource

from dmtools.terrain.adapters import (
    CoastlineSource,
    TerrainProjectInputError,
    load_svg_coastline_source,
    load_terrain_project,
    save_terrain_project,
)
from dmtools.terrain.domain import (
    BrushToolSettings,
    ElevationPoint,
    FeatureToolSettings,
    TerrainAuthoringState,
    TerrainBrushStroke,
    TerrainProject,
    TerrainSettings,
    TerrainStructure,
)
from dmtools.terrain.domain.seeds import LEGACY_SEED_POLICY, NAMED_SEED_POLICY, SeedPolicy

FIXTURES = Path(__file__).parent / "fixtures" / "terrain"
EXAMPLES = Path(__file__).parents[1] / "examples" / "terrain"


def _source_in(tmp_path: Path) -> CoastlineSource:
    source = tmp_path / "inputs" / "coastline.svg"
    source.parent.mkdir()
    shutil.copyfile(FIXTURES / "closed-coast.svg", source)
    return load_svg_coastline_source(source)


def _project_for(source: CoastlineSource) -> TerrainProject:
    return TerrainProject(
        coastline=source.coastline,
        settings=TerrainSettings(seed=42, object_scale_km=3_850.0, resolution_px=512),
        constraints=(
            TerrainBrushStroke(
                points=((0.25, 0.4), (0.5, 0.45)),
                elevation_m=450.0,
                influence_radius_km=130.0,
                intensity=0.6,
                elevation_mode="relative",
            ),
            ElevationPoint((0.62, 0.31), 3_900.0, 75.0, "absolute"),
            TerrainStructure(
                "ridge", ((0.2, 0.3), (0.5, 0.4), (0.8, 0.35)), 1_100.0, 90.0, "relative"
            ),
            TerrainStructure(
                "valley", ((0.3, 0.7), (0.7, 0.6)), 550.0, 65.0, "absolute"
            ),
        ),
        authoring=TerrainAuthoringState(
            active_tool="valley",
            brush=BrushToolSettings("relative", -300.0, 240.0, 0.45),
            height=FeatureToolSettings("relative", 800.0, 55.0),
            ridge=FeatureToolSettings("absolute", 4_200.0, 100.0),
            valley=FeatureToolSettings("relative", 650.0, 70.0),
        ),
    )


@pytest.mark.parametrize("policy", [LEGACY_SEED_POLICY, NAMED_SEED_POLICY])
def test_project_round_trip_preserves_authored_state_and_relative_svg_path(
    tmp_path: Path,
    policy: SeedPolicy,
) -> None:
    source = _source_in(tmp_path)
    project = _project_for(source)
    project = replace(project, settings=replace(project.settings, seed_policy=policy))
    destination = tmp_path / "projects" / "continent.dmterrain.json"

    save_terrain_project(project, source, destination)

    serialized = cast(
        "dict[str, object]", json.loads(destination.read_text(encoding="utf-8"))
    )
    coastline = cast("dict[str, object]", serialized["coastline"])
    constraints = cast("list[dict[str, object]]", serialized["constraints"])
    authoring = cast("dict[str, object]", serialized["authoring"])
    tools = cast("dict[str, dict[str, object]]", authoring["tools"])
    assert serialized["schema"] == "dmtools.terrain-project"
    version = 1 if policy == LEGACY_SEED_POLICY else 2
    assert serialized["schema_version"] == version
    schema_dir = EXAMPLES.parents[1] / "schemas" / "terrain"
    schemas: list[dict[str, Any]] = [
        json.loads((schema_dir / f"project-v{number}.schema.json").read_text())
        for number in (1, 2)
    ]
    registry = Registry[Any]().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    validate(serialized, schemas[version - 1], cls=Draft202012Validator, registry=registry)
    assert coastline["path"] == "../inputs/coastline.svg"
    assert constraints[0]["type"] == "terrain_brush"
    assert tools["brush"]["width_km"] == 240.0

    loaded = load_terrain_project(destination)

    assert loaded.project == project
    assert loaded.coastline_source.path == source.path
    assert loaded.path == destination.resolve()


@pytest.mark.parametrize(
    ("name", "policy"),
    [("example.dmterrain.json", LEGACY_SEED_POLICY),
     ("named-seeds.dmterrain.json", NAMED_SEED_POLICY)],
)
def test_committed_example_project_loads(name: str, policy: SeedPolicy) -> None:
    loaded = load_terrain_project(EXAMPLES / name)

    assert loaded.project.settings == TerrainSettings(seed_policy=policy)
    assert loaded.project.authoring == TerrainAuthoringState()
    assert loaded.project.constraints == ()


def test_project_load_rejects_modified_coastline(tmp_path: Path) -> None:
    source = _source_in(tmp_path)
    destination = tmp_path / "continent.dmterrain.json"
    save_terrain_project(_project_for(source), source, destination)
    source.path.write_text(
        source.path.read_text(encoding="utf-8") + "\n<!-- changed -->\n",
        encoding="utf-8",
    )

    with pytest.raises(TerrainProjectInputError, match="does not match the SHA-256"):
        load_terrain_project(destination)


def test_project_save_rejects_coastline_changed_after_import(tmp_path: Path) -> None:
    source = _source_in(tmp_path)
    source.path.write_text(
        source.path.read_text(encoding="utf-8") + "\n<!-- changed -->\n",
        encoding="utf-8",
    )

    with pytest.raises(TerrainProjectInputError, match="changed after it was imported"):
        save_terrain_project(_project_for(source), source, tmp_path / "project.dmterrain.json")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("schema_version", 99, "Unsupported project schema version"),
        ("unexpected", True, "unknown fields"),
    ],
)
def test_project_load_rejects_incompatible_contract(
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    source = _source_in(tmp_path)
    destination = tmp_path / "continent.dmterrain.json"
    save_terrain_project(_project_for(source), source, destination)
    document = cast(
        "dict[str, object]", json.loads(destination.read_text(encoding="utf-8"))
    )
    document[field] = value
    destination.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(TerrainProjectInputError, match=message):
        load_terrain_project(destination)


@pytest.mark.parametrize(
    ("version", "policy", "message"),
    [(2, None, "missing: seed_policy"),
     (2, LEGACY_SEED_POLICY, "Version 2 requires"),
     (2, "future-policy@9", "Version 2 requires"),
     (1, NAMED_SEED_POLICY, "unknown fields: seed_policy")],
)
def test_project_rejects_ambiguous_seed_policy(
    tmp_path: Path, version: int, policy: str | None, message: str,
) -> None:
    source = _source_in(tmp_path)
    path = tmp_path / "project.dmterrain.json"
    save_terrain_project(_project_for(source), source, path)
    document: dict[str, Any] = json.loads(path.read_text())
    document["schema_version"] = version
    if policy is not None:
        document["settings"]["seed_policy"] = policy
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(TerrainProjectInputError, match=message):
        load_terrain_project(path)
