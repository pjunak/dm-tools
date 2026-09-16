# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
"""Real Tk input-editing flow; skipped only where no desktop display is available."""

import time
import tkinter as tk
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from benchmarks.terrain import fixture
from dmtools.terrain import ui
from dmtools.terrain.domain import (
    ElevationPoint,
    TerrainBasin,
    TerrainBrushStroke,
    TerrainRegion,
    TerrainStructure,
    landform_preset,
)
from dmtools.terrain.pipeline import GeneratedTerrain, generate_terrain
from dmtools.terrain.workbench import GenerationInputs


@pytest.fixture(scope="module")
def generated() -> tuple[GenerationInputs, GeneratedTerrain]:
    coast, settings, _ = fixture("square", 65, 42)
    inputs = GenerationInputs(coast, settings, (ElevationPoint((0.5, 0.5), 1200, 80),))
    return inputs, generate_terrain(coast, settings, constraints=inputs.constraints)


@pytest.fixture
def app(generated: tuple[GenerationInputs, GeneratedTerrain]) -> Iterator[ui.TerrainApp]:
    try:
        root = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tk display unavailable: {error}")
    root.withdraw()
    workbench = ui.TerrainApp(root)
    inputs, terrain = generated
    workbench._accept_coastline(inputs.coastline)
    workbench._apply_settings(inputs.settings)
    workbench._history.reset(inputs.constraints)
    workbench._events.put(ui._ResultEvent(inputs, terrain, Image.new("RGB", (65, 65))))
    workbench._poll_events()
    yield workbench
    for callback in root.tk.splitlist(root.tk.call("after", "info")):
        root.after_cancel(str(callback))
    root.destroy()


def test_edit_keeps_readonly_reference_and_undo_restores_freshness(app: ui.TerrainApp) -> None:
    terrain, image = app._terrain, app._image
    assert terrain is not None
    original = terrain.elevation_m.copy()
    app._select_instruction(0)
    app._tool_elevations["height"].set(2300)
    assert app._has_pending_instruction()
    point = app._constraints[0]
    assert isinstance(point, ElevationPoint) and point.elevation_m == 1200
    app._apply_instruction()
    assert not app._has_pending_instruction()
    assert not app._reference_is_current()
    assert "Previous generation" in str(app.reference_label["text"])
    assert str(app.export_button["state"]) == "disabled"
    assert app._terrain is terrain and app._image is image
    np.testing.assert_array_equal(terrain.elevation_m, original)
    app._undo_constraint()
    assert app._reference_is_current()
    assert str(app.export_button["state"]) == "normal"
    app._redo_constraint()
    assert not app._reference_is_current()


def test_settings_and_late_results_use_exact_snapshot(app: ui.TerrainApp) -> None:
    request = app._generation_inputs()
    terrain, image = app._terrain, app._image
    assert terrain is not None and image is not None
    app._variables["seed"].set(1234)
    assert not app._reference_is_current()
    app._events.put(ui._ResultEvent(request, terrain, image))
    app._poll_events()
    assert not app._reference_is_current()
    assert str(app.export_button["state"]) == "disabled"
    app._variables["seed"].set(request.settings.seed)
    assert app._reference_is_current()
    app.root.setvar(str(app._variables["seed"]), "")
    assert not app._reference_is_current()


def test_save_and_failure_do_not_relabel_stale_reference(
    app: ui.TerrainApp, monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors: list[object] = []
    def showerror(*args: object, **kwargs: object) -> None:
        errors.extend(args)
    monkeypatch.setattr(ui.messagebox, "showerror", showerror)
    app._variables["seed"].set(99)
    image = app._image
    app._events.put(ui._ProjectSavedEvent(Path("test.dmterrain.json")))
    app._poll_events()
    assert str(app.export_button["state"]) == "disabled"
    app._events.put(ui._ErrorEvent("Failed", "Generation failed", ValueError("test")))
    app._poll_events()
    assert errors and app._image is image
    assert str(app.export_button["state"]) == "disabled"


def test_all_instruction_kinds_edit_properties_without_moving_geometry(app: ui.TerrainApp) -> None:
    ring = ((0.2, 0.2), (0.4, 0.2), (0.4, 0.4), (0.2, 0.2))
    constraints = (
        TerrainRegion(ring),
        TerrainBrushStroke(((0.3, 0.3),), 400, 90, 0.5, "relative"),
        TerrainStructure("ridge", ((0.3, 0.3), (0.4, 0.4)), 900, 40, "relative"),
        TerrainStructure("valley", ((0.6, 0.3), (0.7, 0.4)), 150, 40, "absolute"),
        TerrainBasin(ring, "lake", 200, (0.4, 0.3)),
        TerrainBasin(ring, "dry_basin"),
    )
    app._history.reset(constraints)
    app._select_instruction(0)
    app._region_character.set("mountains")
    app._region_values["relief_m"].set(3500)
    app._apply_instruction()
    region = app._constraints[0]
    assert isinstance(region, TerrainRegion)
    assert region.settings.character == "mountains" and region.settings.relief_m == 3500
    for index, tool in ((1, "brush"), (2, "ridge"), (3, "valley")):
        app._select_instruction(index)
        app._tool_elevations[tool].set(700)
        app._tool_sizes[tool].set(120)
        app._apply_instruction()
        feature = app._constraints[index]
        assert isinstance(feature, (TerrainBrushStroke, TerrainStructure))
        assert feature.elevation_m == 700
        assert feature.influence_radius_km == (60 if tool == "brush" else 120)
    app._select_instruction(4)
    app._lake_level.set(250)
    app._apply_instruction()
    lake = app._constraints[4]
    assert isinstance(lake, TerrainBasin) and lake.water_level_m == 250
    assert lake.outlet == (0.4, 0.3)
    app._select_instruction(5)
    assert not app._has_pending_instruction()
    for before, after in zip(constraints, app._constraints, strict=True):
        assert not isinstance(after, ElevationPoint)
        assert before.points == after.points


def test_delete_and_clear_are_reversible(app: ui.TerrainApp) -> None:
    original = app._constraints
    app._select_instruction(0)
    app._delete_instruction()
    assert not app._constraints
    app._undo_constraint()
    assert app._constraints == original
    app._clear_constraints()
    app._undo_constraint()
    assert app._constraints == original and app._reference_is_current()


def test_invalid_property_edit_is_atomic(
    app: ui.TerrainApp, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def showerror(*args: object, **kwargs: object) -> None:
        pass
    monkeypatch.setattr(ui.messagebox, "showerror", showerror)
    original = app._constraints
    app._select_instruction(0)
    app._tool_sizes["height"].set(-1)
    app._apply_instruction()
    assert app._constraints == original and not app._history.can_undo
    assert app._has_pending_instruction()


def test_new_coastline_drops_incompatible_reference_and_history(app: ui.TerrainApp) -> None:
    app._clear_constraints()
    assert app._coastline is not None
    app._accept_coastline(replace(app._coastline, source_name="another.svg"))
    assert app._image is None and app._terrain is None and app._generated_inputs is None
    assert not app._history.can_undo and not app._history.can_redo
    assert not app._reference_is_current()


def test_selection_by_canvas_and_list_never_paints(app: ui.TerrainApp) -> None:
    event: tk.Event[tk.Misc] = tk.Event()
    x, y = app._normalized_to_canvas((0.5, 0.5))
    event.x, event.y = round(x), round(y)
    assert app._select_on_map(event) == "break"
    assert app._selected_instruction == 0
    app._on_map_press(event)
    assert len(app._constraints) == 1 and not app._draft_points
    app._set_authoring_tool("height")
    assert app._selected_instruction is None
    app.instruction_input.current(1)
    app._on_instruction_selected(event)
    assert app._selected_instruction == 0


def test_regeneration_uses_changed_inputs_and_leaves_previous_dem_untouched(
    app: ui.TerrainApp,
) -> None:
    previous = app._terrain
    assert previous is not None
    original = previous.elevation_m.copy()
    app._history.append(TerrainRegion(
        ((0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8), (0.2, 0.2)),
        landform_preset("mountains"),
    ))
    app._instructions_changed("Mountains added")
    inputs = app._generation_inputs()
    app._generate()
    deadline = time.monotonic() + 30
    while not app._authoring_enabled and time.monotonic() < deadline:
        app.root.update()
        time.sleep(0.01)
    assert app._reference_is_current() and app._generated_inputs == inputs
    assert app._terrain is not None and app._terrain is not previous
    assert np.any(app._terrain.elevation_m != original)
    np.testing.assert_array_equal(previous.elevation_m, original)


def test_generation_requires_applied_properties_or_completed_draft(
    app: ui.TerrainApp, monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages: list[object] = []
    def showinfo(*args: object, **kwargs: object) -> None:
        messages.extend(args)
    monkeypatch.setattr(ui.messagebox, "showinfo", showinfo)
    app._select_instruction(0)
    app._tool_elevations["height"].set(3000)
    original = app._terrain
    app._generate()
    assert messages and app._terrain is original and app._authoring_enabled
    messages.clear()
    app._set_authoring_tool("ridge")
    app._draft_points.append((0.3, 0.3))
    app._generate()
    assert messages and app._terrain is original and app._authoring_enabled


def test_new_instruction_cancels_an_unfinished_draft(app: ui.TerrainApp) -> None:
    app._set_authoring_tool("ridge")
    app._draft_points.extend(((0.2, 0.2), (0.4, 0.4)))
    app.instruction_input.current(0)
    event: tk.Event[tk.Misc] = tk.Event()
    app._on_instruction_selected(event)
    assert not app._draft_points and not app._has_pending_instruction()
