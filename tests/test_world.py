"""World source ownership, coordinates, topology and portable current-format contracts."""

import json
from dataclasses import replace
from math import pi, sin
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from shapely.geometry import Point, Polygon

from dmtools.cli import main
from dmtools.terrain.adapters.world_project import read_world_project, world_project_document
from dmtools.terrain.adapters.world_render import OCEAN, render_world_source
from dmtools.terrain.adapters.world_svg import parse_world_svg
from dmtools.terrain.application.world import open_world, propose_group_assignments, save_world
from dmtools.terrain.domain.models import LandComponent
from dmtools.terrain.domain.world import WorldAssignment, WorldContinent, WorldFrame, WorldProject
from dmtools.terrain.pipeline.world import component_area_km2, prepare_world_map
from dmtools.terrain.viewport import MapViewport

ROOT = Path(__file__).parents[1]
EXAMPLE = ROOT / "examples/world/four-shores.dmworld.json"


def source(body: str, *, width: int = 360) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="180" '
        f'viewBox="0 0 360 180">{body}</svg>'
    )


def world(body: str) -> WorldProject:
    imported = parse_world_svg(source(body), "test.svg")
    return WorldProject(
        "Test world",
        imported,
        WorldFrame((0, 0, 360, 180), 1000),
        (WorldContinent("c", "Continent"),),
        tuple(WorldAssignment(f.id, "c", "mainland") for f in imported.features),
    )


def test_explicit_frame_roundtrips_offset_radius_and_central_meridian() -> None:
    frame = WorldFrame((17, 11, 2897, 1451), 4321, 35)
    for point in ((17.0, 11.0), (2897.0, 1451.0), (1457.0, 731.0), (45.0, 400.0)):
        assert frame.lonlat_to_source(frame.source_to_lonlat(point, wrap=False), wrap=False) == (
            pytest.approx(point)
        )
    assert frame.source_to_lonlat((1457, 731)) == (35, 0)
    assert frame.distance_km((0, 0), (90, 0)) == pytest.approx(pi * 4321 / 2)
    assert frame.distance_km((179, 0), (-179, 0)) == pytest.approx(pi * 4321 / 90)
    assert frame.distance_km((10, 90), (150, 90)) == pytest.approx(0, abs=1e-9)


@pytest.mark.parametrize("radius", [0, -1, float("nan"), float("inf"), 1e300, 1e-300])
def test_world_frame_rejects_unusable_numeric_scale(radius: float) -> None:
    with pytest.raises(ValueError):
        WorldFrame((0, 0, 360, 180), radius)


def test_custom_sphere_area_uses_latitude_and_holes() -> None:
    frame = WorldFrame((0, 0, 360, 180), 2000)
    rectangle = LandComponent(((0, 0), (360, 0), (360, 180), (0, 180), (0, 0)))
    assert component_area_km2(rectangle, frame) == pytest.approx(frame.surface_area_km2)
    cap = replace(rectangle, exterior=((0, 0), (360, 0), (360, 30), (0, 30), (0, 0)))
    assert component_area_km2(cap, frame) == pytest.approx(
        2 * pi * frame.radius_km**2 * (1 - sin(pi / 3))
    )
    equator = LandComponent(((10, 80), (20, 80), (20, 90), (10, 90), (10, 80)))
    poleward = replace(equator, exterior=tuple((x, y - 60) for x, y in equator.exterior))
    assert component_area_km2(equator, frame) > component_area_km2(poleward, frame)


def test_svg_display_size_does_not_rescale_source_and_nested_transforms() -> None:
    body = (
        '<g id="A" transform="translate(10,20)"><g transform="scale(2)">'
        '<path id="land" d="M0 0 H10 V10 H0 Z"/></g></g>'
    )
    small = parse_world_svg(source(body), "world.svg")
    large = parse_world_svg(source(body, width=1440), "world.svg")
    assert small.features == large.features
    assert Polygon(small.features[0].components[0].exterior).bounds == (10, 20, 30, 40)
    assert small.svg == source(body)


@pytest.mark.parametrize(
    "fill_rule,inner,holes",
    [
        ("evenodd", "M 5 5 H 15 V 15 H 5 Z", 1),
        ("nonzero", "M 5 5 H 15 V 15 H 5 Z", 0),
        ("nonzero", "M 5 5 V 15 H 15 V 5 Z", 1),
    ],
)
def test_compound_paths_retain_svg_fill_semantics(fill_rule: str, inner: str, holes: int) -> None:
    parsed = parse_world_svg(
        source(f'<path id="a" fill-rule="{fill_rule}" d="M0 0 H20 V20 H0 Z {inner}"/>'), "world.svg"
    )
    feature = parsed.features[0]
    assert not feature.issue
    assert len(feature.components[0].holes) == holes
    polygon = Polygon(feature.components[0].exterior, feature.components[0].holes)
    assert polygon.covers(Point(10, 10)) == (holes == 0)


def test_tiny_holes_and_gaps_are_not_repaired_by_world_import() -> None:
    project = world(
        '<path id="a" fill-rule="evenodd" '
        'd="M0 0 H20 V20 H0 Z M5 5 H5.0001 V5.0001 H5 Z"/>'
        '<path id="b" d="M20.00001 0 H30 V20 H20.00001 Z"/>'
    )
    result = prepare_world_map(project)
    first = result.land[0].components[0]
    assert len(first.holes) == 1
    assert len(result.land) == 2
    assert Polygon(first.exterior, first.holes).area < 400


def test_touching_named_continents_keep_ownership_and_islands() -> None:
    result = open_world(EXAMPLE)
    assert len(result.continents) == 4
    assert {c.name for c in result.continents} == {
        "Westreach",
        "Eastreach",
        "Southmere",
        "Seam Isles",
    }
    assert sum(c.island_shapes for c in result.continents) == 3
    assert "scale-bar" not in {f.feature_id for f in result.land}
    assert len(next(f for f in result.land if f.feature_id == "seam-island").components) == 2
    assert 0 < result.land_fraction < 1


def test_seam_wrapping_does_not_duplicate_land_area() -> None:
    crossing = prepare_world_map(world('<path id="a" d="M355 80 H365 V100 H355 Z"/>'))
    middle = prepare_world_map(world('<path id="a" d="M175 80 H185 V100 H175 Z"/>'))
    assert len(crossing.land[0].components) == 2
    assert crossing.land_area_km2 == pytest.approx(middle.land_area_km2)
    assert max(x for x, _ in crossing.project.source.features[0].components[0].exterior) == 365


def test_seam_and_ordinary_overlaps_are_explicit_errors() -> None:
    for paths in (
        '<path id="a" d="M0 0 H20 V20 H0 Z"/><path id="b" d="M10 0 H30 V20 H10 Z"/>',
        '<path id="a" d="M355 80 H365 V100 H355 Z"/><path id="b" d="M0 80 H10 V100 H0 Z"/>',
    ):
        with pytest.raises(ValueError, match="overlap"):
            prepare_world_map(world(paths))


def test_source_order_does_not_change_stable_feature_identity_or_area() -> None:
    first = '<g id="North"><path id="a" d="M10 10 H30 V30 H10 Z"/></g>'
    second = '<g id="South"><path id="b" d="M50 50 H70 V70 H50 Z"/></g>'
    a, b = world(first + second), world(second + first)
    assert {f.id: f for f in a.source.features} == {f.id: f for f in b.source.features}
    assert prepare_world_map(a).land == prepare_world_map(b).land
    assert prepare_world_map(a).land_area_km2 == prepare_world_map(b).land_area_km2


@pytest.mark.parametrize(
    "body,match",
    [
        ('<path id="a"/><path id="a"/>', "Duplicate SVG ID"),
        ('<use href="#a"/>', "Unsupported SVG use"),
        ('<image href="external.png"/>', "Unsupported SVG image"),
    ],
)
def test_ambiguous_or_external_svg_features_are_rejected(body: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        parse_world_svg(source(body), "world.svg")


def test_open_shapes_must_be_explicitly_excluded() -> None:
    parsed = parse_world_svg(
        source('<path id="land" d="M0 0 H10 V10 H0 Z"/><path id="line" d="M20 20 L30 30"/>'),
        "world.svg",
    )
    assert parsed.features[1].issue
    with pytest.raises(ValueError, match="every source shape"):
        WorldProject(
            "Map",
            parsed,
            WorldFrame((0, 0, 360, 180), 1000),
            (WorldContinent("a", "A"),),
            (WorldAssignment("land", "a", "mainland"),),
        )
    project = WorldProject(
        "Map",
        parsed,
        WorldFrame((0, 0, 360, 180), 1000),
        (WorldContinent("a", "A"),),
        (WorldAssignment("land", "a", "mainland"), WorldAssignment("line", None, "exclude")),
    )
    assert len(prepare_world_map(project).land) == 1


def test_group_suggestions_are_explicit_and_do_not_change_source() -> None:
    project = read_world_project(EXAMPLE)
    original = project.source
    continents, assignments = propose_group_assignments(original)
    assert {c.name for c in continents} == {c.name for c in project.continents}
    assert next(a for a in assignments if a.feature_id == "scale-bar").role == "exclude"
    assert next(a for a in assignments if a.feature_id == "west-island").role == "island"
    assert project.source is original


def test_portable_roundtrip_needs_no_original_svg(tmp_path: Path) -> None:
    project = read_world_project(EXAMPLE)
    output = tmp_path / "portable.dmworld.json"
    save_world(project, output)
    loaded = open_world(output)
    assert loaded.project.source == project.source
    assert loaded.project.frame == project.frame
    assert set(loaded.project.assignments) == set(project.assignments)
    schema = json.loads((ROOT / "schemas/world/project-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(  # pyright: ignore[reportUnknownMemberType]
        json.loads(output.read_text(encoding="utf-8"))
    )


@pytest.mark.parametrize("change", ["hash", "projection", "version", "extra", "duplicate"])
def test_bad_world_files_fail_without_fallback(tmp_path: Path, change: str) -> None:
    document = world_project_document(read_world_project(EXAMPLE))
    raw = json.dumps(document)
    if change == "hash":
        raw = raw.replace(read_world_project(EXAMPLE).source.sha256, "0" * 64)
    elif change == "projection":
        raw = raw.replace('"plate-carree"', '"mercator"')
    elif change == "version":
        raw = raw.replace('"version": 1', '"version": true')
    elif change == "extra":
        raw = raw[:-1] + ', "unknown": 1}'
    else:
        raw = raw[:-1] + ', "name": "duplicate"}'
    path = tmp_path / "bad.dmworld.json"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ValueError):
        open_world(path)


def test_invalid_world_save_leaves_existing_file_untouched(tmp_path: Path) -> None:
    path = tmp_path / "world.dmworld.json"
    project = read_world_project(EXAMPLE)
    save_world(project, path)
    original = path.read_bytes()
    invalid = replace(project, frame=WorldFrame((0, 0, 100, 50), 6500))
    with pytest.raises(ValueError, match="outside"):
        save_world(invalid, path)
    assert path.read_bytes() == original
    with pytest.raises(ValueError, match="extension"):
        save_world(project, tmp_path / "source.svg")
    with pytest.raises(ValueError, match="snapshot"):
        save_world(replace(project, source=replace(project.source, sha256="0" * 64)), path)
    assert path.read_bytes() == original


def test_world_preview_does_not_fill_holes_or_change_authored_geometry() -> None:
    project = world(
        '<path id="a" fill-rule="evenodd" d="M80 40 H280 V140 H80 Z M150 75 H210 V105 H150 Z"/>'
    )
    original = project.source.features
    with render_world_source(
        project.source, project.frame.bounds, project.assignments, MapViewport(), (396, 216)
    ) as image:
        assert image.getpixel((198, 108)) == tuple(bytes.fromhex(OCEAN[1:]))
        assert image.getpixel((130, 108)) != tuple(bytes.fromhex(OCEAN[1:]))
    assert project.source.features == original


def test_world_cli_inspects_saved_project(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["world", "inspect", str(EXAMPLE)]) == 0
    output = capsys.readouterr().out
    assert "Four Shores" in output and "Continents: 4" in output and "6500 km" in output
    assert "not implemented" in output


def test_startup_world_and_terrain_are_mutually_exclusive() -> None:
    with pytest.raises(SystemExit) as error:
        main(["terrain", "gui", "--world", str(EXAMPLE), "--project", "other.json"])
    assert error.value.code == 2


@pytest.mark.parametrize(
    "style", ['clip-path="url(#clip)"', 'style="clip-path:url(#clip)"', 'style="mask:url(#mask)"']
)
def test_clipped_and_masked_land_is_not_silently_imported(style: str) -> None:
    parsed = parse_world_svg(
        source(f'<g {style}><path id="a" d="M10 10 H30 V30 H10 Z"/></g>'), "world.svg"
    )
    assert parsed.features[0].issue.startswith("Clipped/masked")
    assert not parsed.features[0].components


def test_world_preview_clips_seam_outlines_to_declared_frame() -> None:
    project = world('<path id="a" d="M350 70 H370 V110 H350 Z"/>')
    viewport = MapViewport()
    size = (396, 216)
    left, top, right, bottom = viewport.rect(size, (360, 180))
    ocean = tuple(bytes.fromhex(OCEAN[1:]))
    with render_world_source(
        project.source, project.frame.bounds, project.assignments, viewport, size
    ) as image:
        for x, y in (
            (int(left) - 2, 108),
            (int(right) + 2, 108),
            (198, int(top) - 2),
            (198, int(bottom) + 2),
        ):
            assert image.getpixel((x, y)) == ocean


@pytest.mark.parametrize("name", ["", "   ", "x" * 257])
def test_world_source_name_matches_public_contract(name: str) -> None:
    with pytest.raises(ValueError, match="source name"):
        parse_world_svg(source('<path id="a" d="M10 10 H30 V30 H10 Z"/>'), name)


def test_failed_atomic_world_replace_preserves_original(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dmtools.terrain.adapters import world_project

    project = read_world_project(EXAMPLE)
    path = tmp_path / "world.dmworld.json"
    save_world(project, path)
    original = path.read_bytes()

    def reject_replace(*_args: object) -> None:
        raise OSError("Simulated replace failure")

    monkeypatch.setattr(world_project.os, "replace", reject_replace)
    with pytest.raises(OSError, match="Simulated"):
        save_world(replace(project, name="Changed"), path)
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]
