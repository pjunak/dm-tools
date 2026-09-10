"""Connected lake outflow conserves captured area and leaves unresolved pockets intact."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import Polygon

from dmtools.terrain.adapters import load_terrain_project
from dmtools.terrain.domain import TerrainBasin, TerrainStructure
from dmtools.terrain.pipeline import generate_terrain
from dmtools.terrain.pipeline.basin_flow import resolve_basin_outflow
from dmtools.terrain.pipeline.hydrology import drainage_incision
from dmtools.terrain.pipeline.water import basin_intent_ids, prepare_basins


@pytest.mark.parametrize("case", ["connected", "closed", "dry", "uphill", "shoreline",
                                  "split", "pocket", "reentry", "contact_only"])
def test_basin_connection_and_conservation(case: str) -> None:
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
    elif case == "contact_only":
        ground[ids > 0] = 20
        ground[6, 7] = 2
    original = ground.copy()
    routing = drainage_incision(ground, land, np.ones_like(ground), x_spacing_km=1,
        y_spacing_km=1, maximum_elevation_m=100, variability=.5, retention_terminal_mask=ids > 0)
    old_area = routing.accumulation_km2.copy()
    review, flow = resolve_basin_outflow(basins, ids, ground, routing, land, receivers,
        flags, axis, axis, polygon, (lake,), (10. if lake.outlet is not None else None,))
    record = review.basins[0]
    connected = case in ("connected", "pocket", "contact_only")
    assert record.outlet_connection == ("connected" if connected else
                                        "closed" if case in ("closed", "dry") else "blocked")
    assert flow.summary.source_area_km2 == 121
    assert flow.summary.area_balance_error_km2 == pytest.approx(0, abs=1e-10)
    assert flow.source_km2.sum() == pytest.approx(flow.terminal_km2.sum())
    assert record.captured_contributing_area_km2 == pytest.approx(
        record.retained_contributing_area_km2 + record.outlet_contributing_area_km2)
    assert np.all(flow.source_km2[ids == 0] == 0)
    assert np.all(flow.throughput_km2[ids > 0] == 0)
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
    if case == "shoreline":
        assert "outlet_shoreline_uncontained" in record.issues
    if case == "connected":
        assert record.retained_contributing_area_km2 == 0
        assert record.issues == ()
    np.testing.assert_array_equal(ground, original)
    np.testing.assert_array_equal(routing.accumulation_km2, old_area)
    repeated, again = resolve_basin_outflow(basins, ids, ground, routing, land, receivers,
        flags, axis, axis, polygon, (lake,), (10. if lake.outlet is not None else None,))
    assert repeated == review
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
    review, flow = resolve_basin_outflow(basins, ids, ground, routing, land, receivers,
                                        flags, axis, axis, polygon, lakes, (10., 10.))
    assert all(record.outlet_connection == "connected" for record in review.basins)
    total = sum(record.outlet_contributing_area_km2 for record in review.basins)
    assert flow.throughput_km2[6, 10] == pytest.approx(total)
    assert flow.terminal_km2.sum() == pytest.approx(total)
    assert flow.summary.area_balance_error_km2 == pytest.approx(0, abs=1e-10)
    reversed_basins = prepare_basins(tuple(reversed(lakes)), 12, 12, polygon, 100)
    other, result = resolve_basin_outflow(reversed_basins, ids, ground, routing, land, receivers,
        flags, axis, axis, polygon, tuple(reversed(lakes)), (10., 10.))
    assert other == review
    np.testing.assert_array_equal(result.throughput_km2, flow.throughput_km2)


def test_real_outlet_revalidates_and_preserves_ground_across_resolution_and_closure() -> None:
    project = load_terrain_project(Path(__file__).parents[1] /
                                  "examples/terrain/connected-outlet.dmterrain.json").project
    settings = replace(project.settings, resolution_px=65)
    terrain = generate_terrain(project.coastline, settings, constraints=project.constraints)
    refined = generate_terrain(project.coastline, replace(settings, resolution_px=129),
                               constraints=tuple(reversed(project.constraints)))
    assert terrain.basin_outflow.summary.connected_outlet_count == 1
    assert terrain.water.review == refined.water.review
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
