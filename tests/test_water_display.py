"""Lake visibility changes with display scale without changing generated water."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from benchmarks.terrain import fixture
from dmtools.terrain.adapters.render import (
    compose_height_map,
    render_height_map,
    render_height_map_layers,
    save_height_map,
)
from dmtools.terrain.adapters.water_display import (
    WATER_COLOUR,
    WATER_DISPLAY_ID,
    WaterDisplay,
    prepare_water_display,
)
from dmtools.terrain.pipeline import generate_terrain


def _display(wet: np.ndarray) -> WaterDisplay:
    surface = np.where(wet, 100., np.nan).astype(np.float32)
    display = prepare_water_display(surface, np.ones_like(wet, dtype=np.bool_))
    assert display is not None
    return display


def test_separate_pools_keep_individual_areas_and_dry_islands() -> None:
    wet = np.zeros((20, 24), dtype=np.bool_)
    wet[2:12, 2:12] = True
    wet[5:8, 5:8] = False
    wet[14:16, 14:16] = True
    wet[16, 16] = True  # Corner contact must not merge their display importance.
    display = _display(wet)
    areas = np.asarray(display.pool_area)
    assert areas[2, 2] == 91 and areas[14, 14] == 4 and areas[16, 16] == 1
    assert areas[6, 6] == 0
    np.testing.assert_array_equal(areas > 0, wet)
    with display.render((0., 0., 24., 20.), (24, 20)) as image:
        assert image.getpixel((3, 3)) == (*WATER_COLOUR, 255)
        assert image.getpixel((6, 6)) == (*WATER_COLOUR, 0)
        assert image.getpixel((14, 14)) == (*WATER_COLOUR, 0)


def test_small_pool_appears_monotonically_only_as_it_grows_on_screen() -> None:
    display = _display(np.ones((2, 2), dtype=np.bool_))
    alphas: list[int] = []
    for side in (2, 3, 4, 5, 6, 12):
        with display.render((0., 0., float(side), float(side)), (side, side)) as image:
            pixel = image.getpixel((side // 2, side // 2))
            assert isinstance(pixel, tuple)
            alphas.append(pixel[3])
    assert alphas[0:2] == [0, 0]
    assert 0 < alphas[2] < alphas[3] < 255
    assert alphas[-2:] == [255, 255]
    assert alphas == sorted(alphas)


def test_pan_does_not_reclassify_a_partially_visible_lake() -> None:
    display = _display(np.ones((10, 10), dtype=np.bool_))
    with (
        display.render((0., 0., 10., 10.), (10, 10)) as whole,
        display.render((-9., 0., 1., 10.), (10, 10)) as sliver,
    ):
        # Just one column remains on screen, but the whole 100-pixel pool counts.
        assert whole.getpixel((0, 4)) == sliver.getpixel((0, 4)) == (*WATER_COLOUR, 255)
        assert sliver.getpixel((1, 4)) == (*WATER_COLOUR, 0)


def test_area_uses_both_axes_and_visibility_is_independent_of_canvas_size() -> None:
    display = _display(np.ones((4, 4), dtype=np.bool_))
    rect = (0., 0., 2., 8.)  # 16 px squared, even with anisotropic scaling.
    with (
        display.render(rect, (4, 10)) as first,
        display.render(rect, (24, 15)) as wider,
    ):
        pixel = first.getpixel((1, 4))
        assert isinstance(pixel, tuple) and 0 < pixel[3] < 255
        assert pixel == wider.getpixel((1, 4))


def test_render_allocation_and_cached_areas_do_not_grow_with_zoom() -> None:
    display = _display(np.ones((10, 10), dtype=np.bool_))
    before = display.pool_area.tobytes()
    with display.render((-100000., -100000., 100000., 100000.), (80, 60)) as image:
        assert image.size == (80, 60) and image.getpixel((40, 30)) == (*WATER_COLOUR, 255)
    assert display.pool_area.tobytes() == before


def test_source_resolution_does_not_change_visibility_for_the_same_sampled_extent() -> None:
    wet = np.zeros((8, 16), dtype=np.bool_)
    wet[2:4, 5:8] = True
    fine = np.repeat(np.repeat(wet, 2, axis=0), 2, axis=1)
    with (
        _display(wet).render((0., 0., 32., 16.), (32, 16)) as coarse,
        _display(fine).render((0., 0., 32., 16.), (32, 16)) as detailed,
    ):
        assert coarse.tobytes() == detailed.tobytes()


def test_nonland_infinity_and_missing_water_are_never_displayed_or_mutated() -> None:
    surface = np.array([[100., np.inf], [np.nan, 100.]], dtype=np.float32)
    land = np.array([[True, True], [True, False]])
    original_surface, original_land = surface.copy(), land.copy()
    display = prepare_water_display(surface, land)
    assert display is not None
    np.testing.assert_array_equal(np.asarray(display.pool_area), [[1., 0.], [0., 0.]])
    np.testing.assert_array_equal(surface, original_surface)
    np.testing.assert_array_equal(land, original_land)
    assert prepare_water_display(surface, np.zeros_like(land)) is None


@pytest.mark.parametrize("surface,land", [
    (np.zeros(3, dtype=np.float32), np.ones(3, dtype=np.bool_)),
    (np.zeros((3, 3), dtype=np.float32), np.ones((2, 3), dtype=np.bool_)),
])
def test_incompatible_water_arrays_are_rejected(surface: np.ndarray, land: np.ndarray) -> None:
    with pytest.raises(ValueError, match="matching two-dimensional"):
        prepare_water_display(surface, land)


def test_export_scale_metadata_and_scientific_ground_are_separate(tmp_path: Path) -> None:
    coast, settings, constraints = fixture("square", 65, 42)
    dry = generate_terrain(coast, settings, constraints=constraints)
    surface = np.full(dry.elevation_m.shape, np.nan, dtype=np.float32)
    surface[20:30, 20:30] = 2000
    surface[40:42, 40:42] = 2000
    terrain = replace(dry, water=replace(dry.water, surface_m=surface))
    before = (terrain.elevation_m.copy(), terrain.water.surface_m.copy(),
              terrain.routing.receivers.copy())
    image, water = render_height_map_layers(terrain)
    assert water is not None
    with (
        compose_height_map(image, water) as composed,
        render_height_map(terrain) as cartographic,
        render_height_map(terrain, style="scientific") as scientific,
        render_height_map(dry, style="scientific") as dry_scientific,
    ):
        assert composed.tobytes() == cartographic.tobytes()
        assert cartographic.getpixel((25, 25)) == (*WATER_COLOUR, 255)
        assert cartographic.getpixel((40, 40)) == image.getpixel((40, 40))
        assert scientific.tobytes() == dry_scientific.tobytes()
        assert scientific.info["dmtools.water_visibility"] == "none"
        destination = tmp_path / "water.png"
        save_height_map(composed, terrain, destination)
        with Image.open(destination) as saved:
            assert saved.info["dmtools.water_visibility"] == WATER_DISPLAY_ID
            assert saved.tobytes() == cartographic.tobytes()
        # View rendering must not affect a later full-map export.
        with water.render((-100., -100., 500., 500.), (80, 60)):
            pass
        with compose_height_map(image, water) as after_zoom:
            assert after_zoom.tobytes() == cartographic.tobytes()
    for actual, expected in zip((terrain.elevation_m, terrain.water.surface_m,
                                 terrain.routing.receivers), before, strict=True):
        np.testing.assert_array_equal(actual, expected)
