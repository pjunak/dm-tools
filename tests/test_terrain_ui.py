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
from dmtools.terrain.adapters import load_terrain_project
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
    workbench._events.put(ui._ResultEvent(inputs, terrain, Image.new("RGBA", (65, 65)), None))
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
    app._events.put(ui._ResultEvent(request, terrain, image, app._water_display))
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
    app._events.put(ui._ProjectSavedEvent(Path("test.dmterrain.json"), app._generation_inputs()))
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


def _show_canvas(app: ui.TerrainApp) -> None:
    app.root.deiconify()
    app.root.geometry("1280x840")
    app.root.update()


def _map_event(app: ui.TerrainApp, position: tuple[float, float]) -> tk.Event[tk.Misc]:
    event: tk.Event[tk.Misc] = tk.Event()
    x, y = app._normalized_to_canvas(position)
    event.x, event.y = round(x), round(y)
    event.state = 0
    return event


def _wait_for_operation(app: ui.TerrainApp) -> None:
    deadline = time.monotonic() + 20
    while app._busy and time.monotonic() < deadline:
        app.root.update()
        time.sleep(0.01)
    assert not app._busy


def test_view_navigation_preserves_inputs_and_reference_and_probe_uses_dem(
    app: ui.TerrainApp,
) -> None:
    _show_canvas(app)
    inputs, terrain, image = app._generation_inputs(), app._terrain, app._image
    assert terrain is not None
    app._saved_inputs = inputs
    app._zoom_view(4, (app.preview.winfo_width() / 2, app.preview.winfo_height() / 2))
    event = _map_event(app, (0.5, 0.5))
    app._begin_pan(event)
    event.x += 20
    app._pan_view(event)
    app._end_pan(event)
    position = (0.53, 0.47)
    canvas = app._normalized_to_canvas(position)
    assert app._canvas_to_normalized(*canvas) == pytest.approx(position)
    app._inspect_position(*app._normalized_to_canvas((0.5, 0.5)))
    assert "1,200 m ground" in str(app.cursor_label["text"])
    assert app._viewport.zoom == 4 and app._viewport.centre != (0.5, 0.5)
    assert app._generation_inputs() == inputs and app._reference_is_current()
    assert not app._document_is_dirty() and app._terrain is terrain and app._image is image
    app._fit_view()
    assert app._viewport.centre == (0.5, 0.5) and app._viewport.zoom == 1


def test_drag_commits_once_and_undo_restores_the_reference(app: ui.TerrainApp) -> None:
    _show_canvas(app)
    original = app._constraints
    terrain = app._terrain
    app._select_instruction(0)
    app.root.update()
    app._zoom_view(2)
    app._on_map_press(_map_event(app, (0.5, 0.5)))
    for x in (0.52, 0.54, 0.55):
        app._on_map_drag(_map_event(app, (x, 0.5)))
        assert app._constraints == original and not app._history.can_undo
    app._on_map_release(_map_event(app, (0.55, 0.5)))
    point = app._constraints[0]
    assert isinstance(point, ElevationPoint)
    assert point.position[0] == pytest.approx(0.55, abs=0.003)
    assert app._history.can_undo and not app._reference_is_current()
    app._undo_constraint()
    assert app._constraints == original and not app._history.can_undo
    assert app._reference_is_current() and app._terrain is terrain


def test_crossed_region_drag_is_rejected_and_escape_cancels_preview(app: ui.TerrainApp) -> None:
    _show_canvas(app)
    ring = ((0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8), (0.2, 0.2))
    app._history.reset((TerrainRegion(ring),))
    app._select_instruction(0)
    app._on_map_press(_map_event(app, ring[1]))
    app._on_map_drag(_map_event(app, (0.35, 0.9)))
    app._on_map_release(_map_event(app, (0.35, 0.9)))
    assert app._constraints == (TerrainRegion(ring),) and not app._history.can_undo
    assert "rejected" in str(app.status_label["text"])
    app._on_map_press(_map_event(app, ring[1]))
    app._on_map_drag(_map_event(app, (0.6, 0.3)))
    app._cancel_edit()
    app._on_map_release(_map_event(app, (0.6, 0.3)))
    assert app._constraints == (TerrainRegion(ring),) and not app._has_pending_instruction()


def test_geometry_guard_rejects_basins_touching_and_lines_crossing_water(
    app: ui.TerrainApp,
) -> None:
    ring = ((0.2, 0.2), (0.4, 0.2), (0.4, 0.4), (0.2, 0.4), (0.2, 0.2))
    basin = TerrainBasin(ring, "lake", 200, ring[0])
    app._history.reset((basin,))
    app._validate_instruction_geometry(basin, excluding=0)
    with pytest.raises(ValueError, match="overlap or touch"):
        app._validate_instruction_geometry(basin)
    outer = ((0., 0.), (1., 0.), (1., 1.), (0., 1.), (0., 0.))
    app._coast_polygon = ui.Polygon(
        [app._normalized_to_source(p) for p in outer],
        holes=[[app._normalized_to_source(p) for p in ring]],
    )
    for instruction in (ElevationPoint((0.3, 0.3), 100, 20),
                        TerrainStructure("ridge", ((0.1, 0.3), (0.7, 0.3)), 200, 30)):
        with pytest.raises(ValueError, match="water holes"):
            app._validate_instruction_geometry(instruction)


def test_review_cache_is_reused_on_navigation_and_hidden_inputs_cannot_be_selected(
    app: ui.TerrainApp,
) -> None:
    _show_canvas(app)
    app._show_drainage.set(True)
    app._draw_preview()
    overlay = app._review_image
    assert overlay is not None
    app._zoom_view(32)
    assert app._review_image is overlay
    photo = app._review_photo
    assert photo is not None
    assert (photo.width(), photo.height()) == (app.preview.winfo_width(),
                                               app.preview.winfo_height())
    app._show_instructions.set(False)
    app._draw_preview()
    assert app._instruction_at(*app._normalized_to_canvas((0.5, 0.5))) is None
    app._show_catchments.set(True)
    app._draw_preview()
    assert app._review_image is not overlay


def test_input_shortcuts_leave_typing_alone_and_busy_workers_lock_inputs(
    app: ui.TerrainApp,
) -> None:
    _show_canvas(app)
    calls: list[str] = []
    app.root.focus_force()
    app.value_input.focus_set()
    app.root.update()
    assert app._shortcut(lambda: calls.append("delete"), editing=True) is None
    assert not calls
    app._set_busy(True)
    app._shortcut(lambda: calls.append("generate"))
    assert not calls
    assert all(str(widget["state"]) == "disabled" for widget in app._settings_widgets)
    app._set_busy(False)


def test_save_as_then_save_uses_known_path_and_roundtrips_edits(
    app: ui.TerrainApp, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    source = Path("examples/terrain/landform-regions.dmterrain.json")
    source_bytes = source.read_bytes()
    app._accept_project(load_terrain_project(source))
    assert not app._document_is_dirty()
    app._set_resolution(257)
    assert app._document_is_dirty() and app.root.title().startswith("* ")
    destination = tmp_path / "edited.dmterrain.json"
    dialogs: list[str] = []
    def save_dialog(**_kwargs: object) -> str:
        dialogs.append("save as")
        return str(destination)
    monkeypatch.setattr(ui.filedialog, "asksaveasfilename", save_dialog)
    app._save_project(save_as=True)
    _wait_for_operation(app)
    assert not app._document_is_dirty() and app._project_path == destination
    app._variables["seed"].set(18)
    app._save_project()
    _wait_for_operation(app)
    assert dialogs == ["save as"] and not app._document_is_dirty()
    loaded = load_terrain_project(destination)
    assert loaded.project.settings.seed == 18 and loaded.project.settings.resolution_px == 257
    assert source.read_bytes() == source_bytes


@pytest.mark.parametrize("answer, expected", [(None, []), (False, ["continued"])])
def test_unsaved_guard_can_cancel_or_discard(
    app: ui.TerrainApp, monkeypatch: pytest.MonkeyPatch,
    answer: bool | None, expected: list[str],
) -> None:
    calls: list[str] = []
    def ask(*_args: object, **_kwargs: object) -> bool | None:
        return answer
    monkeypatch.setattr(ui.messagebox, "askyesnocancel", ask)
    app._guard_unsaved(lambda: calls.append("continued"))
    assert calls == expected


def test_save_guard_waits_for_success_and_cancelled_dialog_keeps_document_open(
    app: ui.TerrainApp, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    app._accept_project(load_terrain_project(Path("examples/terrain/landform-regions.dmterrain.json")))
    app._project_path = None
    app._variables["seed"].set(24)
    calls: list[str] = []
    def ask(*_args: object, **_kwargs: object) -> bool:
        return True
    destination = ""
    def save_dialog(**_kwargs: object) -> str:
        return destination
    monkeypatch.setattr(ui.messagebox, "askyesnocancel", ask)
    monkeypatch.setattr(ui.filedialog, "asksaveasfilename", save_dialog)
    app._guard_unsaved(lambda: calls.append("continued"))
    assert not calls and not app._busy and app._document_is_dirty()
    destination = str(tmp_path / "saved.dmterrain.json")
    app._guard_unsaved(lambda: calls.append("continued"))
    assert not calls and app._busy
    _wait_for_operation(app)
    assert calls == ["continued"] and not app._document_is_dirty()


def test_failed_or_outdated_save_never_runs_destructive_continuation(
    app: ui.TerrainApp, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    app._accept_project(load_terrain_project(Path("examples/terrain/landform-regions.dmterrain.json")))
    app._project_path = tmp_path / "saved.dmterrain.json"
    app._variables["seed"].set(42)
    calls: list[str] = []
    errors: list[object] = []
    def showerror(*args: object, **_kwargs: object) -> None:
        errors.extend(args)
    monkeypatch.setattr(ui.messagebox, "showerror", showerror)
    app._save_project(after_save=lambda: calls.append("continued"))
    # Programmatic changes can still arrive while widgets are disabled.
    app._variables["seed"].set(43)
    _wait_for_operation(app)
    assert not calls and app._document_is_dirty()
    assert load_terrain_project(app._project_path).project.settings.seed == 42
    def fail(*_args: object, **_kwargs: object) -> None:
        raise OSError("Simulated write failure")
    monkeypatch.setattr(ui, "save_terrain_project", fail)
    app._save_project(after_save=lambda: calls.append("continued"))
    _wait_for_operation(app)
    assert errors and not calls and app._after_save is None and app._document_is_dirty()


def test_select_click_cannot_move_an_instruction_when_the_properties_change_layout(
    app: ui.TerrainApp,
) -> None:
    _show_canvas(app)
    app._set_selection_mode()
    app.root.update()
    original = app._constraints
    event = _map_event(app, (0.5, 0.5))
    app._on_map_press(event)
    app.root.update()
    app._on_map_release(event)
    assert app._constraints == original and not app._history.can_undo


def test_water_visibility_tracks_zoom_and_style_without_changing_or_exporting_viewport(
    app: ui.TerrainApp, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    from dmtools.terrain.adapters.render import render_height_map, render_height_map_layers
    from dmtools.terrain.adapters.water_display import WATER_COLOUR, WATER_DISPLAY_ID

    terrain = app._terrain
    assert terrain is not None
    surface = np.full_like(terrain.water.surface_m, np.nan)
    surface[32, 32] = 2000.
    terrain = replace(terrain, water=replace(terrain.water, surface_m=surface))
    image, water = render_height_map_layers(terrain)
    app._events.put(ui._ResultEvent(app._generation_inputs(), terrain, image, water))
    app._poll_events()
    _show_canvas(app)
    app._show_instructions.set(False)
    before = terrain.elevation_m.copy(), terrain.water.surface_m.copy()
    assert app._water_display is water and water is not None
    app._zoom_view(4)
    assert app._water_display is water
    assert "km/sample" in str(app.zoom_label["text"])
    assert app._reference_is_current()
    photo = app._preview_photo
    assert photo is not None
    centre = (photo.width() // 2, photo.height() // 2)
    assert app.root.tk.call(str(photo), "get", *centre) == WATER_COLOUR
    export = tmp_path / "water.png"
    def choose_export(**_kwargs: object) -> str:
        return str(export)
    monkeypatch.setattr(ui.filedialog, "asksaveasfilename", choose_export)
    app._export()
    with Image.open(export) as exported, render_height_map(terrain) as expected:
        assert exported.size == image.size
        assert exported.tobytes() == expected.tobytes()
        assert exported.info["dmtools.water_visibility"] == WATER_DISPLAY_ID
    app._render_style_label.set("Scientific elevation")
    app._on_render_style_changed()
    assert app._water_display is None
    app._render_style_label.set("Cartographic relief")
    app._on_render_style_changed()
    assert app._water_display is not None
    for actual, expected in zip((terrain.elevation_m, terrain.water.surface_m),
                                 before, strict=True):
        np.testing.assert_array_equal(actual, expected)
    # Pending scale edits do not relabel the old generated map with the new scale.
    label = str(app.zoom_label["text"])
    app._inspect_position(*app._normalized_to_canvas((0.5, 0.5)))
    probe = str(app.cursor_label["text"])
    app._variables["object_scale_km"].set(terrain.settings.object_scale_km * 2)
    assert str(app.zoom_label["text"]) == label
    app._inspect_position(*app._normalized_to_canvas((0.5, 0.5)))
    assert str(app.cursor_label["text"]) == probe
    assert not app._reference_is_current()


def test_resolution_readout_keeps_navigation_available_in_small_window(app: ui.TerrainApp) -> None:
    _show_canvas(app)
    app.root.geometry("1040x700")
    app.root.update()
    app._draw_preview()
    app.root.update()
    for widget in app.zoom_label.master.winfo_children():
        assert widget.winfo_ismapped()
        assert widget.winfo_width() >= widget.winfo_reqwidth()
