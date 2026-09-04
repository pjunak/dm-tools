import numpy as np

from dmtools.terrain.pipeline.hydrology import (
    drainage_incision,
    multiple_flow_accumulation,
    priority_flood_surface,
)


def test_priority_flood_gives_an_accidental_depression_a_downhill_route() -> None:
    elevation = np.array(
        [
            [0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 5.0, 5.0, 5.0, 0.0],
            [0.0, 5.0, -10.0, 5.0, 0.0],
            [0.0, 5.0, 5.0, 5.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0],
        ],
        dtype=np.float64,
    )
    land = np.ones_like(elevation, dtype=np.bool_)

    routed = priority_flood_surface(elevation, land)

    assert routed[2, 2] > 5.0
    assert np.min(routed[1:4, 1:4]) >= 5.0
    np.testing.assert_array_equal(routed[[0, -1]], elevation[[0, -1]])


def test_mfd_accumulation_grows_downstream_on_a_planar_slope() -> None:
    x = np.linspace(100.0, 0.0, 17, dtype=np.float64)
    elevation = np.broadcast_to(x, (11, 17)).copy()
    land = np.ones_like(elevation, dtype=np.bool_)

    accumulation, slope = multiple_flow_accumulation(
        elevation,
        land,
        x_spacing_km=1.0,
        y_spacing_km=1.0,
    )

    assert accumulation[5, -1] > accumulation[5, 8] > accumulation[5, 0]
    assert np.all(slope[:, :-1] > 0.0)
    assert np.all(slope[:, -1] == 0.0)


def test_mfd_accumulation_rotates_with_the_terrain() -> None:
    rows, columns = np.indices((13, 13), dtype=np.float64)
    elevation = 400.0 - 7.0 * rows - 11.0 * columns + 0.013 * rows * columns
    land = np.ones_like(elevation, dtype=np.bool_)

    accumulation, _slope = multiple_flow_accumulation(
        elevation,
        land,
        x_spacing_km=2.0,
        y_spacing_km=2.0,
    )
    rotated_accumulation, _rotated_slope = multiple_flow_accumulation(
        np.rot90(elevation),
        np.rot90(land),
        x_spacing_km=2.0,
        y_spacing_km=2.0,
    )

    np.testing.assert_allclose(rotated_accumulation, np.rot90(accumulation), rtol=1e-12)


def test_drainage_incision_selects_convergent_channels_not_the_whole_slope() -> None:
    rows, columns = np.indices((41, 41), dtype=np.float64)
    elevation = 1_500.0 - 12.0 * columns + 0.9 * np.square(rows - 20.0)
    elevation = np.maximum(elevation, 0.0)
    land = np.ones_like(elevation, dtype=np.bool_)
    distance_to_coast = np.minimum.reduce(
        (rows, columns, 40.0 - rows, 40.0 - columns)
    )

    incision, accumulation = drainage_incision(
        elevation,
        land,
        distance_to_coast,
        x_spacing_km=4.0,
        y_spacing_km=4.0,
        maximum_elevation_m=3_000.0,
        variability=0.7,
    )

    assert np.max(incision) > 0.0
    assert np.count_nonzero(incision > 0.25 * np.max(incision)) < incision.size // 3
    assert accumulation[20, -1] > accumulation[5, -1]
    assert incision[20, 30] > incision[5, 30]
