from dataclasses import replace
from pathlib import Path

import numpy as np
from PIL import Image

from dmtools.terrain.adapters import render_height_map, save_height_map
from dmtools.terrain.domain import Coastline, TerrainSettings
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
    terrain = generate_terrain(_square(), _settings())
    image = render_height_map(terrain)
    alpha = np.asarray(image)[..., 3]

    np.testing.assert_array_equal(alpha > 0, terrain.land_mask)
    destination = tmp_path / "terrain.png"
    save_height_map(image, terrain, destination)

    with Image.open(destination) as exported:
        assert exported.mode == "RGBA"
        assert exported.info["dmtools.source"] == "square.svg"
        assert '"seed": 42' in exported.info["dmtools.settings"]
