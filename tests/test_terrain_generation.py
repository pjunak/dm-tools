import json
from dataclasses import replace
from pathlib import Path

import numpy as np
from PIL import Image

from dmtools.terrain.adapters import render_height_map, save_height_map
from dmtools.terrain.domain import (
    Coastline,
    ElevationPoint,
    TerrainBrushStroke,
    TerrainSettings,
    TerrainStructure,
)
from dmtools.terrain.pipeline import generate_terrain
from dmtools.terrain.pipeline.noise import fractal_value_noise


def _square() -> Coastline:
    return Coastline(
        points=((0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)),
        source_name="square.svg",
    )


def _settings(**changes: object) -> TerrainSettings:
    baseline = TerrainSettings(
        seed=42,
        object_scale_km=1_000.0,
        resolution_px=65,
        maximum_elevation_m=3_000.0,
        largest_feature_km=250.0,
        detail_levels=4,
        roughness=0.55,
        coastal_rise_km=80.0,
        variability=0.7,
    )
    return replace(baseline, **changes)


def test_same_inputs_produce_identical_terrain() -> None:
    first = generate_terrain(_square(), _settings())
    second = generate_terrain(_square(), _settings())

    np.testing.assert_array_equal(first.land_mask, second.land_mask)
    np.testing.assert_array_equal(first.elevation_m, second.elevation_m)


def test_seed_changes_inland_elevation() -> None:
    first = generate_terrain(_square(), _settings(seed=1))
    second = generate_terrain(_square(), _settings(seed=2))

    assert np.any(first.elevation_m[first.land_mask] != second.elevation_m[second.land_mask])


def test_nested_resolution_preserves_existing_samples() -> None:
    coarse = generate_terrain(_square(), _settings(resolution_px=65))
    fine = generate_terrain(_square(), _settings(resolution_px=129))

    np.testing.assert_array_equal(coarse.land_mask, fine.land_mask[::2, ::2])
    np.testing.assert_array_equal(coarse.elevation_m, fine.elevation_m[::2, ::2])


def test_authored_height_point_sets_its_target_elevation() -> None:
    point = ElevationPoint(
        position=(0.5, 0.5),
        elevation_m=750.0,
        influence_radius_km=120.0,
    )

    terrain = generate_terrain(_square(), _settings(), constraints=(point,))

    assert terrain.elevation_m[32, 32] == np.float32(750.0)
    assert terrain.constraints == (point,)


def test_ridges_raise_and_valleys_cut_the_base_surface() -> None:
    baseline = generate_terrain(_square(), _settings())
    ridge = TerrainStructure(
        kind="ridge",
        points=((0.25, 0.5), (0.75, 0.5)),
        elevation_m=3_000.0,
        influence_radius_km=100.0,
    )
    valley = TerrainStructure(
        kind="valley",
        points=((0.5, 0.25), (0.5, 0.75)),
        elevation_m=100.0,
        influence_radius_km=80.0,
    )

    ridged = generate_terrain(_square(), _settings(), constraints=(ridge,))
    valleyed = generate_terrain(_square(), _settings(), constraints=(valley,))

    assert ridged.elevation_m[32, 24] == np.float32(3_000.0)
    assert ridged.elevation_m[32, 24] > baseline.elevation_m[32, 24]
    assert valleyed.elevation_m[24, 32] <= np.float32(100.0)
    assert valleyed.elevation_m[24, 32] < baseline.elevation_m[24, 32]


def test_structure_response_has_a_broad_falloff_beyond_its_core_width() -> None:
    baseline = generate_terrain(_square(), _settings())
    ridge = TerrainStructure(
        kind="ridge",
        points=((0.25, 0.5), (0.75, 0.5)),
        elevation_m=3_000.0,
        influence_radius_km=50.0,
    )

    ridged = generate_terrain(_square(), _settings(), constraints=(ridge,))

    assert ridged.elevation_m[40, 32] > baseline.elevation_m[40, 32]


def test_authored_features_do_not_raise_the_coastline() -> None:
    ridge = TerrainStructure(
        kind="ridge",
        points=((0.25, 0.05), (0.75, 0.05)),
        elevation_m=3_000.0,
        influence_radius_km=200.0,
    )

    terrain = generate_terrain(_square(), _settings(), constraints=(ridge,))

    assert terrain.land_mask[0, 32]
    assert terrain.elevation_m[0, 32] == np.float32(0.0)


def test_nearby_height_point_bends_structure_profile() -> None:
    ridge = TerrainStructure(
        kind="ridge",
        points=((0.2, 0.5), (0.8, 0.5)),
        elevation_m=2_000.0,
        influence_radius_km=40.0,
    )
    peak = ElevationPoint(
        position=(0.5, 0.5),
        elevation_m=2_800.0,
        influence_radius_km=30.0,
    )

    ridge_only = generate_terrain(_square(), _settings(), constraints=(ridge,))
    anchored = generate_terrain(_square(), _settings(), constraints=(ridge, peak))

    assert anchored.elevation_m[32, 38] > ridge_only.elevation_m[32, 38]
    assert anchored.elevation_m[32, 32] == np.float32(2_800.0)


def test_terrain_brush_softly_guides_the_base_surface() -> None:
    baseline = generate_terrain(_square(), _settings())
    weak_brush = TerrainBrushStroke(
        points=((0.3, 0.5), (0.7, 0.5)),
        elevation_m=3_000.0,
        influence_radius_km=100.0,
        intensity=0.25,
    )
    strong_brush = replace(weak_brush, intensity=0.75)

    weak = generate_terrain(_square(), _settings(), constraints=(weak_brush,))
    strong = generate_terrain(_square(), _settings(), constraints=(strong_brush,))

    assert baseline.elevation_m[32, 32] < weak.elevation_m[32, 32]
    assert weak.elevation_m[32, 32] < strong.elevation_m[32, 32]
    assert strong.elevation_m[32, 32] < np.float32(3_000.0)


def test_terrain_brush_can_lower_terrain_without_moving_the_coastline() -> None:
    baseline = generate_terrain(_square(), _settings())
    brush = TerrainBrushStroke(
        points=((0.3, 0.5), (0.7, 0.5)),
        elevation_m=100.0,
        influence_radius_km=120.0,
        intensity=0.8,
    )

    painted = generate_terrain(_square(), _settings(), constraints=(brush,))

    assert painted.elevation_m[32, 32] < baseline.elevation_m[32, 32]
    assert painted.elevation_m[0, 32] == np.float32(0.0)


def test_overlapping_terrain_brushes_are_order_independent() -> None:
    high = TerrainBrushStroke(((0.25, 0.5), (0.6, 0.5)), 2_500.0, 90.0, 0.4)
    low = TerrainBrushStroke(((0.4, 0.5), (0.75, 0.5)), 500.0, 110.0, 0.6)

    first = generate_terrain(_square(), _settings(), constraints=(high, low))
    second = generate_terrain(_square(), _settings(), constraints=(low, high))

    np.testing.assert_array_equal(first.elevation_m, second.elevation_m)


def test_authored_constraints_preserve_nested_resolution_samples() -> None:
    constraints = (
        TerrainBrushStroke(((0.3, 0.4), (0.7, 0.4)), 1_800.0, 100.0, 0.5),
        ElevationPoint((0.5, 0.5), 1_250.0, 130.0),
        TerrainStructure("ridge", ((0.2, 0.7), (0.8, 0.7)), 2_600.0, 90.0),
    )

    coarse = generate_terrain(_square(), _settings(resolution_px=65), constraints=constraints)
    fine = generate_terrain(_square(), _settings(resolution_px=129), constraints=constraints)

    np.testing.assert_array_equal(coarse.land_mask, fine.land_mask[::2, ::2])
    np.testing.assert_array_equal(coarse.elevation_m, fine.elevation_m[::2, ::2])


def test_noise_is_independent_of_query_shape_and_order() -> None:
    x = np.array([12.5, 98.0, 301.25], dtype=np.float64)
    y = np.array([44.0, 72.5, 19.0], dtype=np.float64)
    together = fractal_value_noise(
        x,
        y,
        seed=99,
        largest_feature_km=300.0,
        detail_levels=6,
        roughness=0.6,
    )
    separately = np.array(
        [
            fractal_value_noise(
                np.array([x_value]),
                np.array([y_value]),
                seed=99,
                largest_feature_km=300.0,
                detail_levels=6,
                roughness=0.6,
            )[0]
            for x_value, y_value in zip(x, y, strict=True)
        ]
    )

    np.testing.assert_array_equal(together, separately)


def test_render_is_transparent_outside_and_png_records_settings(tmp_path: Path) -> None:
    point = ElevationPoint((0.5, 0.5), 1_200.0, 75.0)
    brush = TerrainBrushStroke(((0.3, 0.6), (0.7, 0.6)), 900.0, 60.0, 0.4)
    terrain = generate_terrain(_square(), _settings(), constraints=(point, brush))
    image = render_height_map(terrain)
    alpha = np.asarray(image)[..., 3]

    np.testing.assert_array_equal(alpha > 0, terrain.land_mask)
    destination = tmp_path / "terrain.png"
    save_height_map(image, terrain, destination)

    with Image.open(destination) as exported:
        assert exported.mode == "RGBA"
        assert exported.info["dmtools.source"] == "square.svg"
        assert '"seed": 42' in exported.info["dmtools.settings"]
        constraints = json.loads(exported.info["dmtools.constraints"])
        assert constraints == [
            {
                "elevation_m": 1_200.0,
                "influence_radius_km": 75.0,
                "position": [0.5, 0.5],
                "type": "elevation_point",
            },
            {
                "elevation_m": 900.0,
                "influence_radius_km": 60.0,
                "intensity": 0.4,
                "points": [[0.3, 0.6], [0.7, 0.6]],
                "type": "terrain_brush",
            },
        ]
