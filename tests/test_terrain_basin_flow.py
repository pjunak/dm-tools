"""Connected lake outflow conserves captured area and leaves unresolved pockets intact."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from shapely.geometry import Polygon

from dmtools.terrain.adapters import load_terrain_project
from dmtools.terrain.adapters.render import (
    render_basin_catchment_overlay,
    render_basin_outflow_overlay,
)
from dmtools.terrain.domain import TerrainBasin, TerrainStructure
from dmtools.terrain.pipeline import GeneratedTerrain, generate_terrain
from dmtools.terrain.pipeline.basin_flow import BasinCatchmentClass, resolve_basin_outflow
from dmtools.terrain.pipeline.hydrology import drainage_incision
from dmtools.terrain.pipeline.water import MetricBasin, basin_intent_ids, prepare_basins
from dmtools.terrain.pipeline.water_sampling import GroundSampler


def _connection_sampler(
    basins: tuple[MetricBasin, ...], ground: NDArray[np.float64],
    heights: tuple[float | None, ...],
) -> GroundSampler:
    """Explicit high rims and low openings supplement these unit-spaced grid fixtures."""
    def sample(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float32]:
        values = np.full(x.shape, 20., dtype=np.float32)
        for basin, height in zip(basins, heights, strict=True):
            if basin.outlet_km is None:
                continue
            ox, oy = basin.outlet_km
            values[np.hypot(x - ox, y - oy) <= np.sqrt(2)] = 2
            # Preserve canonical values wherever the analytic profile visits a grid node.
            grid = (x == np.rint(x)) & (y == np.rint(y))
            values[grid] = ground[y[grid].astype(int), x[grid].astype(int)]
            assert height is not None
            values[(x == ox) & (y == oy)] = height
        return values
    return sample


def _check_internal_paths(terrain: GeneratedTerrain) -> float:
    """Trace exported global indices independently and measure area needing a flat step."""
    flow = terrain.basin_outflow
    ids = terrain.water.routing_intent_ids.ravel()
    classes = flow.catchment_class.ravel()
    receivers, ranks = flow.internal_receivers.ravel(), flow.flat_rank.ravel()
    heads = terrain.routing_final_elevation_m.ravel().astype(np.float64)
    for basin in terrain.water.review.basins:
        water = (ids == basin.intent_id) & (classes == BasinCatchmentClass.COLLECTED_WATER)
        if water.any():
            assert basin.source.water_level_m is not None
            heads[water] = basin.source.water_level_m
    dependent_area = 0.
    for source in np.flatnonzero(ids):
        node = int(source)
        visited: set[int] = set()
        uses_flat = False
        while receivers[node] >= 0:
            assert node not in visited
            visited.add(node)
            target = int(receivers[node])
            assert ids[target] == ids[source]
            assert classes[target] == classes[source] or (
                classes[source] == BasinCatchmentClass.COLLECTED_DRY
                and classes[target] == BasinCatchmentClass.COLLECTED_WATER)
            assert heads[target] <= heads[node]
            if heads[target] == heads[node]:
                assert ranks[node] > ranks[target]
                uses_flat = True
            else:
                assert ranks[node] == 0
            node = target
        if classes[source] >= BasinCatchmentClass.COLLECTED_WATER:
            assert classes[node] == BasinCatchmentClass.COLLECTED_WATER
            if uses_flat:
                dependent_area += float(flow.source_km2.ravel()[source])
        else:
            assert classes[node] == BasinCatchmentClass.RETAINED
    return dependent_area


@pytest.mark.parametrize("case", ["connected", "closed", "dry", "uphill", "shoreline",
                                  "split", "pocket", "reentry", "contact_only",
                                  "head_deep", "head_shallow", "submerged_outlet",
                                  "subgrid_inner_barrier", "subgrid_outer_barrier",
                                  "subgrid_leak", "subgrid_budget", "subgrid_submerged",
                                  "subgrid_tolerated"])
def test_basin_connection_and_conservation(case: str, monkeypatch: pytest.MonkeyPatch) -> None:
    axis = np.arange(13, dtype=np.float64)
    x, y = np.meshgrid(axis, axis)
    land = (x >= 1) & (x <= 11) & (y >= 1) & (y <= 11)
    polygon = Polygon(((1, 1), (11, 1), (11, 11), (1, 11)))
    lake = TerrainBasin(((.2, .2), (.6, .2), (.6, .8), (.2, .8), (.2, .2)),
                        "lake", 10, (.6, .5))
    if case == "closed":
        lake = replace(lake, outlet=None)
    elif case == "dry":
        lake = replace(lake, kind="dry_basin", water_level_m=None, outlet=None)
    basins = prepare_basins((lake,), 12, 12, polygon, 100)
    ids = basin_intent_ids(x, y, basins)
    ground = np.full((13, 13), 20., dtype=np.float64)
    ground[ids > 0] = 2
    ground[6, 8:12] = [9, 8, 7, 6]
    receivers = np.full(ground.shape, -1, dtype=np.int64)
    receivers[6, 8:11] = [87, 88, 89]
    flags = np.zeros(ground.shape, dtype=np.uint8)
    flags[6, 11] = 2
    if case == "uphill":
        ground[6, 9] = 15
    elif case == "shoreline":
        ground[4, 2] = 1
    elif case == "split":
        ground[3:10, 5] = 20
    elif case == "pocket":
        ground[5:8, 4:7] = 12
        ground[6, 5] = 11
    elif case == "reentry":
        receivers[6, 8] = 85
    elif case in ("contact_only", "head_deep", "head_shallow"):
        ground[ids > 0] = 20
        ground[6, 7] = 9.9 if case == "head_shallow" else 2
        if case != "contact_only":
            # Against water head 10, the axial dry pit is steeper than the diagonal lake.
            # Using the deep bed instead would incorrectly collect this donor.
            ground[5, 6] = 11
            ground[5, 5] = 10.1
    original = ground.copy()
    routing = drainage_incision(ground, land, np.ones_like(ground), x_spacing_km=1,
        y_spacing_km=1, maximum_elevation_m=100, variability=.5, retention_terminal_mask=ids > 0)
    old_area = routing.accumulation_km2.copy()
    outlet_height = (2. if case in ("submerged_outlet", "subgrid_submerged") else
                     10. if lake.outlet is not None else None)
    base_sampler = _connection_sampler(basins, ground, (outlet_height,))

    def sampler(xx: NDArray[np.float64], yy: NDArray[np.float64]) -> NDArray[np.float32]:
        values = base_sampler(xx, yy)
        if case in ("subgrid_inner_barrier", "subgrid_outer_barrier", "subgrid_submerged",
                    "subgrid_tolerated"):
            center = 7.6 if case == "subgrid_outer_barrier" else 7.1
            selected = (np.abs(xx - center) < .03) & (np.abs(yy - 6) < .03)
            values[selected] = (9. if case == "subgrid_submerged" else
                                10.005 if case == "subgrid_tolerated" else 20.)
        elif case == "subgrid_leak":
            values[(np.abs(xx - 4.8) < .03) & (np.abs(yy - 2.4) < .03)] = 2
        return values

    if case.startswith("subgrid_"):
        # Every existing grid height is identical: only finer evidence changes the decision.
        np.testing.assert_array_equal(sampler(x, y), ground.astype(np.float32))
    if case == "subgrid_budget":
        monkeypatch.setattr("dmtools.terrain.pipeline.water_sampling.MAX_PROFILE_SAMPLES", 10)
    review, flow = resolve_basin_outflow(basins, ids, ground, routing, land, receivers,
        flags, axis, axis, polygon, (lake,), (outlet_height,), sampler)
    record = review.basins[0]
    connected = case in ("connected", "pocket", "contact_only", "head_deep", "head_shallow",
                         "submerged_outlet", "subgrid_submerged", "subgrid_tolerated")
    assert record.outlet_connection == ("connected" if connected else
                                        "closed" if case in ("closed", "dry") else "blocked")
    assert flow.summary.source_area_km2 == 121
    assert flow.summary.area_balance_error_km2 == pytest.approx(0, abs=1e-10)
    assert flow.source_km2.sum() == pytest.approx(flow.terminal_km2.sum())
    assert record.captured_contributing_area_km2 == pytest.approx(
        record.retained_contributing_area_km2 + record.outlet_contributing_area_km2)
    assert np.all(flow.source_km2[ids == 0] == 0)
    assert np.all(flow.throughput_km2[ids > 0] == 0)
    classes = flow.catchment_class
    assert classes.dtype == np.uint8
    np.testing.assert_array_equal(classes != BasinCatchmentClass.OUTSIDE, ids > 0)
    np.testing.assert_array_equal(flow.retained_km2 + flow.source_km2,
                                  np.where(ids > 0, old_area, 0.))
    np.testing.assert_array_equal(flow.retained_km2 > 0, classes == BasinCatchmentClass.RETAINED)
    np.testing.assert_array_equal(flow.source_km2 > 0,
                                  classes >= BasinCatchmentClass.COLLECTED_WATER)
    assert flow.retained_km2.sum() == pytest.approx(record.retained_contributing_area_km2)
    assert record.collected_wet_cell_count == np.count_nonzero(
        classes == BasinCatchmentClass.COLLECTED_WATER)
    assert record.collected_dry_cell_count == np.count_nonzero(
        classes == BasinCatchmentClass.COLLECTED_DRY)
    assert record.retained_cell_count == np.count_nonzero(classes == BasinCatchmentClass.RETAINED)
    assert record.flat_routed_cell_count == np.count_nonzero(flow.flat_rank)
    assert record.collected_flat_cell_count == np.count_nonzero(
        (flow.flat_rank > 0) & (classes == BasinCatchmentClass.COLLECTED_DRY))
    assert record.footprint_cell_count == (record.collected_wet_cell_count
        + record.collected_dry_cell_count + record.retained_cell_count)
    if connected:
        amount = record.outlet_contributing_area_km2
        assert amount > 0
        np.testing.assert_array_equal(flow.throughput_km2[6, 8:12], amount)
        assert flow.terminal_km2[6, 11] == amount
        assert record.uncontrolled_low_boundary_cell_count == 0
    else:
        assert not flow.source_km2.any()
        assert not flow.throughput_km2.any()
    if case == "pocket":
        assert record.retained_contributing_area_km2 > 0
        assert flow.source_km2[6, 5] == 0
        assert "outlet_partial_catchment" in record.issues
    if case in ("head_deep", "head_shallow"):
        assert classes[5, 6] == classes[5, 5] == BasinCatchmentClass.RETAINED
        assert classes[6, 7] == BasinCatchmentClass.COLLECTED_WATER
    if case == "contact_only":
        assert classes[3, 3] == BasinCatchmentClass.COLLECTED_DRY
        assert record.collected_flat_cell_count > 0
        assert record.retained_cell_count == 0
        assert classes[6, 6] == BasinCatchmentClass.COLLECTED_DRY
    if case == "submerged_outlet":
        assert record.outlet_ground_minus_water_m == -8
        assert "outlet_below_water" in record.issues
    if case == "shoreline":
        assert "outlet_shoreline_uncontained" in record.issues
    if case in ("subgrid_inner_barrier", "subgrid_outer_barrier"):
        assert record.outlet_route is not None
        assert "outlet_connection_above_water" in record.outlet_route.issues
        assert record.outlet_route.connection_profile is not None
        assert record.outlet_route.connection_profile.maximum_ground_m == 20
        assert record.outlet_route.maximum_height_above_water_m == 10
    if case == "subgrid_submerged":
        assert record.outlet_route is not None
        assert record.outlet_route.connection_profile is not None
        assert record.outlet_route.connection_profile.maximum_ground_m == 9
        assert record.outlet_ground_minus_water_m == -8
    if case == "subgrid_leak":
        assert record.low_boundary_cell_count == 3
        assert record.uncontrolled_low_boundary_cell_count == 0
        assert record.shoreline is not None and record.shoreline.uncontrolled_low_sample_count > 0
        assert "shoreline_low_ground" in record.issues
    if case == "subgrid_budget":
        assert "shoreline_sampling_unresolved" in record.issues
        assert record.shoreline is not None
        assert record.shoreline.profile.positions_km == ()
    if case == "connected":
        assert record.retained_contributing_area_km2 == 0
        assert record.issues == ()
    np.testing.assert_array_equal(ground, original)
    np.testing.assert_array_equal(routing.accumulation_km2, old_area)
    repeated, again = resolve_basin_outflow(basins, ids, ground, routing, land, receivers,
        flags, axis, axis, polygon, (lake,), (outlet_height,), sampler)
    assert repeated == review
    np.testing.assert_array_equal(again.internal_receivers, flow.internal_receivers)
    np.testing.assert_array_equal(again.flat_rank, flow.flat_rank)
    np.testing.assert_array_equal(again.catchment_class, flow.catchment_class)
    np.testing.assert_array_equal(again.retained_km2, flow.retained_km2)
    np.testing.assert_array_equal(again.source_km2, flow.source_km2)
    np.testing.assert_array_equal(again.throughput_km2, flow.throughput_km2)


def test_two_outlets_share_a_trunk_without_double_counting_or_order_dependence() -> None:
    axis = np.arange(13, dtype=np.float64)
    x, y = np.meshgrid(axis, axis)
    land = (x >= 1) & (x <= 11) & (y >= 1) & (y <= 11)
    polygon = Polygon(((1, 1), (11, 1), (11, 11), (1, 11)))
    lakes = tuple(TerrainBasin(tuple((px / 12, py / 12) for px, py in
        ((2.4, row-.6), (7.2, row-.6), (7.2, row+.6), (2.4, row+.6), (2.4, row-.6))),
        "lake", 10, (.6, row / 12)) for row in (4, 8))
    basins = prepare_basins(lakes, 12, 12, polygon, 100)
    ids = basin_intent_ids(x, y, basins)
    ground = np.full((13, 13), 20., dtype=np.float64)
    ground[ids > 0] = 2
    receivers = np.full(ground.shape, -1, dtype=np.int64)
    for path in (((4, 8), (5, 9), (6, 10), (6, 11)),
                 ((8, 8), (7, 9), (6, 10), (6, 11))):
        for i, (row, col) in enumerate(path):
            ground[row, col] = 9 - i
            if i < len(path)-1:
                r, c = path[i+1]
                receivers[row, col] = r*13+c
    flags = np.zeros(ground.shape, dtype=np.uint8)
    flags[6, 11] = 2
    routing = drainage_incision(ground, land, np.ones_like(ground), x_spacing_km=1,
        y_spacing_km=1, maximum_elevation_m=100, variability=.5, retention_terminal_mask=ids > 0)
    sampler = _connection_sampler(basins, ground, (10., 10.))
    review, flow = resolve_basin_outflow(basins, ids, ground, routing, land, receivers,
                                        flags, axis, axis, polygon, lakes, (10., 10.), sampler)
    assert all(record.outlet_connection == "connected" for record in review.basins)
    total = sum(record.outlet_contributing_area_km2 for record in review.basins)
    assert flow.throughput_km2[6, 10] == pytest.approx(total)
    assert flow.terminal_km2.sum() == pytest.approx(total)
    assert flow.summary.area_balance_error_km2 == pytest.approx(0, abs=1e-10)
    reversed_basins = prepare_basins(tuple(reversed(lakes)), 12, 12, polygon, 100)
    other, result = resolve_basin_outflow(reversed_basins, ids, ground, routing, land, receivers,
        flags, axis, axis, polygon, tuple(reversed(lakes)), (10., 10.), sampler)
    assert other == review
    np.testing.assert_array_equal(result.throughput_km2, flow.throughput_km2)


@pytest.mark.parametrize("example", ["connected-outlet", "flat-outlet"])
def test_real_outlet_revalidates_and_preserves_ground_across_resolution_and_closure(
    example: str,
) -> None:
    project = load_terrain_project(Path(__file__).parents[1] /
                                  f"examples/terrain/{example}.dmterrain.json").project
    settings = replace(project.settings, resolution_px=65)
    terrain = generate_terrain(project.coastline, settings, constraints=project.constraints)
    refined = generate_terrain(project.coastline, replace(settings, resolution_px=129),
                               constraints=tuple(reversed(project.constraints)))
    assert terrain.basin_outflow.summary.connected_outlet_count == 1
    grid = terrain.routing_grid
    with render_basin_catchment_overlay(terrain, (grid.width, grid.height)) as native:
        pixels = np.asarray(native)
        np.testing.assert_array_equal(pixels[..., 3] > 0, terrain.water.routing_intent_ids > 0)
        assert len(np.unique(pixels.reshape(-1, 4), axis=0)) == 4
        with render_basin_catchment_overlay(
            terrain, (3 * (grid.width - 1) + 1, 3 * (grid.height - 1) + 1),
        ) as enlarged:
            np.testing.assert_array_equal(np.asarray(enlarged)[::3, ::3], pixels)
    assert terrain.water.review == refined.water.review
    area_needing_flat_routes = _check_internal_paths(terrain)
    if example == "flat-outlet":
        assert area_needing_flat_routes > 0
        assert np.count_nonzero(terrain.basin_outflow.flat_rank) > 100
        assert np.any((terrain.basin_outflow.flat_rank > 0)
                      & (terrain.basin_outflow.catchment_class == BasinCatchmentClass.RETAINED))
    np.testing.assert_array_equal(terrain.basin_outflow.internal_receivers,
                                  refined.basin_outflow.internal_receivers)
    np.testing.assert_array_equal(terrain.basin_outflow.flat_rank, refined.basin_outflow.flat_rank)
    np.testing.assert_array_equal(terrain.basin_outflow.catchment_class,
                                  refined.basin_outflow.catchment_class)
    np.testing.assert_array_equal(terrain.basin_outflow.retained_km2,
                                  refined.basin_outflow.retained_km2)
    np.testing.assert_array_equal(terrain.basin_outflow.source_km2,
                                  refined.basin_outflow.source_km2)
    np.testing.assert_array_equal(terrain.basin_outflow.throughput_km2,
                                  refined.basin_outflow.throughput_km2)
    # The public coast has unequal axis lengths: nested resolutions can round its short
    # dimension differently. Compare the canonical finished field instead.
    np.testing.assert_array_equal(terrain.routing_final_elevation_m,
                                  refined.routing_final_elevation_m)
    closed = tuple(replace(c, outlet=None) if isinstance(c, TerrainBasin) else c
                   for c in project.constraints)
    closure = generate_terrain(project.coastline, settings, constraints=closed)
    np.testing.assert_array_equal(terrain.elevation_m, closure.elevation_m)
    np.testing.assert_array_equal(terrain.routing.accumulation_km2,
                                  closure.routing.accumulation_km2)
    assert not closure.basin_outflow.source_km2.any()
    # Stopping the explicit valley short of the coastline leaves a real barrier.
    shortened = tuple(replace(c, points=(*c.points[:-1], (.01, c.points[-1][1])))
                      if isinstance(c, TerrainStructure) and c.kind == "valley" else c
                      for c in project.constraints)
    blocked = generate_terrain(project.coastline, settings, constraints=shortened)
    assert blocked.basin_outflow.summary.connected_outlet_count == 0
    record = next(r for r in blocked.water.review.basins if r.source.kind == "lake")
    assert record.outlet_route is not None
    assert "outlet_route_uphill" in record.outlet_route.issues


def test_public_subgrid_shoreline_opening_is_rejected_and_marked_across_resolutions() -> None:
    project = load_terrain_project(Path(__file__).parents[1] /
                                  "examples/terrain/shoreline-gap.dmterrain.json").project
    terrain = generate_terrain(project.coastline, replace(project.settings, resolution_px=65),
                               constraints=project.constraints)
    refined = generate_terrain(project.coastline, replace(project.settings, resolution_px=129),
                               constraints=tuple(reversed(project.constraints)))
    assert terrain.water.review == refined.water.review
    assert terrain.basin_outflow.summary.connected_outlet_count == 0
    assert not terrain.basin_outflow.source_km2.any()
    assert not terrain.basin_outflow.flat_rank.any()
    np.testing.assert_array_equal(terrain.basin_outflow.internal_receivers, -1)
    assert terrain.basin_outflow.summary.area_balance_error_km2 == pytest.approx(0, abs=1e-6)
    lake = next(r for r in terrain.water.review.basins if r.source.kind == "lake")
    assert lake.outlet_connection == "blocked"
    assert lake.outlet_route is not None and lake.outlet_route.status == "sampled_clear"
    assert lake.uncontrolled_low_boundary_cell_count == 0
    assert lake.shoreline is not None and lake.shoreline.uncontrolled_low_sample_count == 2
    assert "shoreline_low_ground" in lake.issues
    with render_basin_outflow_overlay(terrain, (513, 303)) as overlay:
        pixels = np.asarray(overlay)
        for index in lake.shoreline.uncontrolled_low_sample_indices:
            x, y = lake.shoreline.profile.positions_km[index]
            col = round(x * 512 / terrain.x_km[-1])
            row = round(y * 302 / terrain.y_km[-1])
            assert np.any(np.all(pixels[row-2:row+3, col-2:col+3] == (255, 160, 60, 255), axis=-1))
