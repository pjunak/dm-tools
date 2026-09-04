import numpy as np

from dmtools.terrain.pipeline.hydrology import (
    drainage_diagnostics,
    drainage_incision,
    multiple_flow_accumulation,
    priority_flood_surface,
    steepest_flow_accumulation,
    steepest_flow_receivers,
)


def test_drainage_diagnostics_reports_a_fully_connected_planar_slope() -> None:
    x = np.linspace(100.0, 0.0, 17, dtype=np.float64)
    elevation = np.broadcast_to(x, (11, 17)).copy()
    land = np.ones_like(elevation, dtype=np.bool_)

    diagnostics = drainage_diagnostics(
        elevation,
        land,
        x_spacing_km=2.0,
        y_spacing_km=2.0,
    )

    assert diagnostics.potential_sink_cell_count == 0
    assert diagnostics.directly_connected_land_cell_count == diagnostics.land_cell_count
    assert diagnostics.depression_cell_count == 0
    assert diagnostics.maximum_fill_depth_m < 0.01
    assert diagnostics.largest_outlet_catchment_km2 > 0.0


def test_drainage_diagnostics_quantifies_an_inland_depression_without_mutating_it() -> None:
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
    original = elevation.copy()
    land = np.ones_like(elevation, dtype=np.bool_)

    diagnostics = drainage_diagnostics(
        elevation,
        land,
        x_spacing_km=1.0,
        y_spacing_km=1.0,
    )

    np.testing.assert_array_equal(elevation, original)
    assert diagnostics.potential_sink_cell_count >= 1
    assert diagnostics.directly_connected_land_cell_count < diagnostics.land_cell_count
    assert diagnostics.depression_cell_count >= 1
    assert diagnostics.maximum_fill_depth_m >= 15.0
    assert diagnostics.depression_fill_volume_km3 > 0.0
    assert diagnostics.basin_candidate_count == 1
    assert diagnostics.flat_terminal_cell_count == 0
    candidate = diagnostics.basin_candidates[0]
    assert candidate.normalized_x == 0.5
    assert candidate.normalized_y == 0.5
    assert candidate.cell_count == 1
    assert candidate.area_km2 == 1.0
    assert candidate.floor_elevation_m == -10.0
    assert candidate.spill_elevation_m == np.nextafter(5.0, np.inf)
    assert candidate.maximum_fill_depth_m >= 15.0
    assert candidate.fill_volume_km3 >= 0.015
    assert candidate.terminal_cell_count == 1


def test_drainage_diagnostics_orders_separate_basin_candidates_by_depth() -> None:
    elevation = np.zeros((7, 9), dtype=np.float64)
    elevation[1:-1, 1:-1] = 5.0
    elevation[3, 2] = -20.0
    elevation[3, 6] = -5.0
    land = np.ones_like(elevation, dtype=np.bool_)

    diagnostics = drainage_diagnostics(
        elevation,
        land,
        x_spacing_km=2.0,
        y_spacing_km=3.0,
    )

    assert diagnostics.basin_candidate_count == 2
    deeper, shallower = diagnostics.basin_candidates
    assert deeper.maximum_fill_depth_m > shallower.maximum_fill_depth_m
    assert deeper.normalized_x == 0.25
    assert deeper.normalized_y == 0.5
    assert deeper.area_km2 == 6.0
    assert shallower.normalized_x == 0.75
    assert shallower.normalized_y == 0.5
    assert shallower.area_km2 == 6.0


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


def test_d8_tree_concentrates_each_cell_into_one_downstream_receiver() -> None:
    rows, columns = np.indices((17, 17), dtype=np.float64)
    elevation = 800.0 - 10.0 * columns + 0.8 * np.square(rows - 8.0)
    land = np.ones_like(elevation, dtype=np.bool_)

    accumulation, slope = steepest_flow_accumulation(
        elevation,
        land,
        x_spacing_km=2.0,
        y_spacing_km=2.0,
    )

    assert accumulation[8, -1] > accumulation[4, -1]
    assert accumulation[8, -1] > accumulation[8, 8]
    assert slope[8, 8] > 0.0


def test_drainage_incision_selects_convergent_channels_not_the_whole_slope() -> None:
    rows, columns = np.indices((41, 41), dtype=np.float64)
    elevation = 1_500.0 - 12.0 * columns + 0.9 * np.square(rows - 20.0)
    elevation = np.maximum(elevation, 0.0)
    land = np.ones_like(elevation, dtype=np.bool_)
    distance_to_coast = np.minimum.reduce(
        (rows, columns, 40.0 - rows, 40.0 - columns)
    )

    drainage = drainage_incision(
        elevation,
        land,
        distance_to_coast,
        x_spacing_km=4.0,
        y_spacing_km=4.0,
        maximum_elevation_m=3_000.0,
        variability=0.7,
    )

    assert np.max(drainage.incision_m) > 0.0
    assert (
        np.count_nonzero(drainage.incision_m > 0.25 * np.max(drainage.incision_m))
        < drainage.incision_m.size // 3
    )
    assert drainage.accumulation_km2[20, -1] > drainage.accumulation_km2[5, -1]
    assert drainage.incision_m[20, 30] > drainage.incision_m[5, 30]
    assert drainage.incision_m[20, 30] > 5.0
    assert drainage.detail_suppression[20, 30] > drainage.detail_suppression[5, 30]
    assert np.count_nonzero(drainage.channel_head_mask) > 0
    receivers, _slope = steepest_flow_receivers(
        priority_flood_surface(elevation, land),
        land,
        x_spacing_km=4.0,
        y_spacing_km=4.0,
    )
    flat_channel = drainage.channel_mask.ravel()
    for channel_index in np.flatnonzero(flat_channel):
        receiver = int(receivers.ravel()[channel_index])
        assert receiver < 0 or flat_channel[receiver]


def test_area_slope_initiation_starts_steep_headwaters_before_gentle_ones() -> None:
    height, width = 15, 41
    rows, columns = np.indices((height, width), dtype=np.float64)
    land = np.zeros((height, width), dtype=np.bool_)
    land[1:7, :] = True
    land[8:14, :] = True
    elevation = np.zeros((height, width), dtype=np.float64)
    elevation[1:7, :] = (
        2_000.0
        - 25.0 * columns[1:7, :]
        + 4.0 * np.square(rows[1:7, :] - 3.5)
    )
    elevation[8:14, :] = (
        500.0
        - 3.0 * columns[8:14, :]
        + 4.0 * np.square(rows[8:14, :] - 10.5)
    )
    distance_to_coast = np.where(land, 50.0, 0.0)

    drainage = drainage_incision(
        elevation,
        land,
        distance_to_coast,
        x_spacing_km=2.0,
        y_spacing_km=2.0,
        maximum_elevation_m=3_000.0,
        variability=0.7,
    )

    steep_heads = np.argwhere(drainage.channel_head_mask[1:7, :])
    gentle_heads = np.argwhere(drainage.channel_head_mask[8:14, :])
    assert steep_heads.size > 0
    assert gentle_heads.size > 0
    assert int(np.min(steep_heads[:, 1])) < int(np.min(gentle_heads[:, 1]))
    assert np.all(drainage.incision_m[drainage.channel_head_mask] > 0.0)


def test_retained_detail_cannot_make_generated_channel_floors_climb() -> None:
    rows, columns = np.indices((41, 41), dtype=np.float64)
    elevation = 1_500.0 - 12.0 * columns + 0.9 * np.square(rows - 20.0)
    elevation = np.maximum(elevation, 0.0)
    land = np.ones_like(elevation, dtype=np.bool_)
    distance_to_coast = np.full_like(elevation, 50.0)
    residual_detail = np.zeros_like(elevation)
    residual_detail[17, 25] = 100.0

    drainage = drainage_incision(
        elevation,
        land,
        distance_to_coast,
        x_spacing_km=4.0,
        y_spacing_km=4.0,
        maximum_elevation_m=3_000.0,
        variability=0.7,
        residual_detail_m=residual_detail,
    )

    final_surface = (
        elevation
        - drainage.incision_m
        + residual_detail * (1.0 - drainage.detail_suppression)
    )
    receivers, _slope = steepest_flow_receivers(
        priority_flood_surface(elevation, land),
        land,
        x_spacing_km=4.0,
        y_spacing_km=4.0,
    )
    flat_channel = drainage.channel_mask.ravel()
    flat_surface = final_surface.ravel()
    for donor_value in np.flatnonzero(flat_channel):
        donor = int(donor_value)
        receiver = int(receivers.ravel()[donor])
        if receiver < 0 or not flat_channel[receiver]:
            continue
        assert flat_surface[receiver] <= flat_surface[donor] - 0.01 + 1e-9

    assert drainage.floor_correction_m[17, 25] > 0.0
    assert drainage.unresolved_uphill_channel_edge_count == 0


def test_large_downstream_valley_has_broader_shoulders_than_its_headwaters() -> None:
    rows, columns = np.indices((61, 61), dtype=np.float64)
    elevation = 2_000.0 - 15.0 * columns + 1.2 * np.square(rows - 30.0)
    land = np.ones_like(elevation, dtype=np.bool_)
    distance_to_coast = np.minimum.reduce(
        (rows, columns, 60.0 - rows, 60.0 - columns)
    )

    drainage = drainage_incision(
        elevation,
        land,
        distance_to_coast,
        x_spacing_km=4.0,
        y_spacing_km=4.0,
        maximum_elevation_m=4_000.0,
        variability=0.7,
    )

    upstream = drainage.incision_m[:, 24]
    downstream = drainage.incision_m[:, 46]
    fixed_relief_threshold_m = 0.01 * 4_000.0
    upstream_width = np.count_nonzero(upstream > fixed_relief_threshold_m)
    downstream_width = np.count_nonzero(downstream > fixed_relief_threshold_m)

    assert downstream_width > upstream_width
    assert drainage.detail_suppression[30, 46] > drainage.detail_suppression[30, 24]


def test_mfd_valley_shoulders_do_not_blur_across_a_drainage_divide() -> None:
    rows, columns = np.indices((61, 61), dtype=np.float64)
    two_valley_cross_section = np.minimum(
        1.8 * np.square(rows - 18.0),
        1.8 * np.square(rows - 42.0),
    )
    elevation = np.maximum(
        2_400.0 - 14.0 * columns + two_valley_cross_section,
        0.0,
    )
    land = np.ones_like(elevation, dtype=np.bool_)
    distance_to_coast = np.full_like(elevation, 100.0)

    drainage = drainage_incision(
        elevation,
        land,
        distance_to_coast,
        x_spacing_km=4.0,
        y_spacing_km=4.0,
        maximum_elevation_m=4_000.0,
        variability=0.7,
    )

    assert drainage.incision_m[18, 40] > 15.0
    assert drainage.incision_m[42, 40] > 15.0
    assert drainage.incision_m[30, 40] == 0.0
    assert drainage.detail_suppression[30, 40] == 0.0
