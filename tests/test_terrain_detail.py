# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportMissingTypeStubs=false
"""Added detail preserves reference structure independently of window/density/order."""

from dataclasses import replace
from hashlib import sha256
from itertools import pairwise
from typing import Any

import numpy as np
import pytest
import shapely
from numpy.typing import NDArray
from shapely.geometry import LineString
from shapely.strtree import STRtree

from benchmarks.terrain import fixture
from dmtools.terrain.domain import ElevationPoint, EndpointGrid, TerrainProject
from dmtools.terrain.domain.regional import (
    RegionalDetailSettings,
    RegionalSamplingRequest,
    detail_cell_window,
)
from dmtools.terrain.pipeline import regional
from dmtools.terrain.pipeline.detail import (
    DetailedRegion,
    PreparedRegionalDetail,
    cell_coefficients,
    prepare_regional_detail,
    residual_basis,
)
from dmtools.terrain.pipeline.generate import generate_terrain
from dmtools.terrain.pipeline.parent import (
    ParentRouting,
    ParentTerrainData,
    VerifiedTerrainParent,
    prepare_verified_parent,
)


def numerical_parent(project: TerrainProject) -> VerifiedTerrainParent:
    terrain = generate_terrain(project.coastline, project.settings, constraints=project.constraints)
    routing = terrain.routing
    data = ParentTerrainData(
        sha256(repr(project).encode()).hexdigest(),
        project,
        terrain.x_km,
        terrain.y_km,
        terrain.elevation_m,
        terrain.land_mask,
        terrain.water.surface_m,
        terrain.water.intent_ids,
        ParentRouting(
            np.linspace(0, terrain.grid.extent_km[2], terrain.routing_grid.width),
            np.linspace(0, terrain.grid.extent_km[3], terrain.routing_grid.height),
            terrain.routing_land_mask,
            terrain.routing_final_elevation_m,
            routing.source_elevation_m,
            routing.receivers,
            routing.channel_mask,
            routing.accumulation_km2,
            routing.incision_m,
            routing.incision_limit_m,
        ),
    )
    return prepare_verified_parent(data)


@pytest.fixture(
    scope="module", params=[("example", 42), ("authored", 7), ("regional", 42), ("water", 42)]
)
def detail_field(request: pytest.FixtureRequest) -> tuple[PreparedRegionalDetail, tuple[int, int]]:
    case, seed = request.param
    coast, settings, constraints = fixture(case, 65, seed)
    settings = replace(settings, detail_levels=2)
    parent = numerical_parent(TerrainProject(coast, settings, tuple(constraints)))
    data = parent.data
    field = prepare_regional_detail(parent, RegionalDetailSettings(40.0))
    grid = data.grid
    survey = field.sample(
        RegionalSamplingRequest(
            data.build_id,
            grid,
            8,
            (8 * 8, 8 * 8, (grid.width - 9) * 8, (grid.height - 9) * 8),
            halo_cells=0,
        )
    )
    candidates = np.flatnonzero(survey.cell_amplitude_m > 0)
    assert candidates.size, "The public fixture should contain some eligible interior land."
    chosen = int(candidates[candidates.size // 2])
    left = int(np.clip(survey.cell_columns[chosen] - 4, 1, grid.width - 10))
    top = int(np.clip(survey.cell_rows[chosen] - 4, 1, grid.height - 10))
    return field, (left, top)


def sample(
    field: PreparedRegionalDetail, origin: tuple[int, int], refinement: int, halo: int = 0
) -> DetailedRegion:
    x, y = origin
    parent = field.parent
    request = RegionalSamplingRequest(
        parent.data.build_id,
        parent.data.grid,
        refinement,
        (x * refinement, y * refinement, (x + 8) * refinement, (y + 8) * refinement),
        halo,
    )
    return field.sample(request)


def test_65_129_257_windows_preserve_common_samples_and_parent_nodes(
    detail_field: tuple[PreparedRegionalDetail, tuple[int, int]],
) -> None:
    field, origin = detail_field
    results = [sample(field, origin, factor) for factor in (8, 16, 32)]
    assert [r.samples.elevation_m.shape for r in results] == [(65, 65), (129, 129), (257, 257)]
    for coarse, fine in pairwise(results):
        for name in ("elevation_m", "land_mask", "water_surface_m", "basin_intent_ids"):
            np.testing.assert_array_equal(
                getattr(coarse.samples, name), getattr(fine.samples, name)[::2, ::2]
            )
        np.testing.assert_array_equal(coarse.cell_amplitude_m, fine.cell_amplitude_m)
        np.testing.assert_array_equal(coarse.reference_cell_mean_m, fine.reference_cell_mean_m)
        np.testing.assert_array_equal(coarse.detailed_cell_mean_m, fine.detailed_cell_mean_m)
    x, y = origin
    expected = field.parent.data.elevation_m[y : y + 9, x : x + 9]
    for factor, result in zip((8, 16, 32), results, strict=True):
        np.testing.assert_array_equal(result.samples.elevation_m[::factor, ::factor], expected)
        assert np.count_nonzero(result.added_detail_m) > 0
        assert np.max(np.abs(result.added_detail_m)) <= field.settings.amplitude_m + 0.001
        assert result.evidence.maximum_cell_mean_error_m < 0.00025
        assert result.evidence.parent_cells == 64
        assert not result.samples.elevation_m.flags.writeable
        np.testing.assert_array_equal(
            result.samples.elevation_m[::factor, :], result.reference_elevation_m[::factor, :]
        )
        np.testing.assert_array_equal(
            result.samples.elevation_m[:, ::factor], result.reference_elevation_m[:, ::factor]
        )


def test_overlap_repeat_visit_halo_and_batch_size_do_not_change_ground(
    detail_field: tuple[PreparedRegionalDetail, tuple[int, int]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    field, origin = detail_field
    first = sample(field, origin, 8, 1)
    shifted = sample(field, (origin[0] + 1, origin[1] + 1), 8, 3)
    _xs, x1, x2 = np.intersect1d(first.samples.x_km, shifted.samples.x_km, return_indices=True)
    _ys, y1, y2 = np.intersect1d(first.samples.y_km, shifted.samples.y_km, return_indices=True)
    np.testing.assert_array_equal(
        first.samples.elevation_m[np.ix_(y1, x1)], shifted.samples.elevation_m[np.ix_(y2, x2)]
    )
    monkeypatch.setattr(regional, "REGIONAL_CHUNK_SAMPLES", 127)
    repeated = sample(field, origin, 8, 1)
    np.testing.assert_array_equal(first.samples.elevation_m, repeated.samples.elevation_m)
    np.testing.assert_array_equal(first.reference_elevation_m, repeated.reference_elevation_m)


def test_water_authored_cores_and_channel_corridors_keep_reference_ground(
    detail_field: tuple[PreparedRegionalDetail, tuple[int, int]],
) -> None:
    field, origin = detail_field
    result = sample(field, origin, 16)
    samples = result.samples
    xx, yy = np.meshgrid(samples.x_km, samples.y_km)
    protected = samples.basin_intent_ids > 0
    parent = field.parent
    for constraint in parent.data.project.constraints:
        if isinstance(constraint, ElevationPoint):
            x = constraint.position[0] * parent.data.grid.extent_km[2]
            y = constraint.position[1] * parent.data.grid.extent_km[3]
            protected |= np.hypot(xx - x, yy - y) <= constraint.influence_radius_km
    routing = parent.data.routing
    lines: list[LineString] = []
    for source in np.flatnonzero(routing.channel_mask):
        target = int(routing.receivers.flat[source])
        if target < 0:
            continue
        row, col = divmod(int(source), routing.x_km.size)
        tr, tc = divmod(target, routing.x_km.size)
        lines.append(
            LineString(
                [(routing.x_km[col], routing.y_km[row]), (routing.x_km[tc], routing.y_km[tr])]
            )
        )
    if lines:
        guard = min(parent.data.grid.x_spacing_km, parent.data.grid.y_spacing_km)
        pairs = STRtree(lines).query(
            shapely.points(xx.ravel(), yy.ravel()), predicate="dwithin", distance=guard * 0.99
        )
        protected.ravel()[np.unique(pairs[0])] = True
    np.testing.assert_array_equal(
        samples.elevation_m[protected], result.reference_elevation_m[protected]
    )
    reference = parent.sampler.sample(samples.request)
    np.testing.assert_array_equal(samples.water_surface_m, reference.water_surface_m)
    np.testing.assert_array_equal(samples.basin_intent_ids, reference.basin_intent_ids)


def test_cell_basis_has_zero_moment_and_vanishing_boundary_slopes() -> None:
    coefficients = cell_coefficients(
        np.array([9, 10], dtype=np.int64), np.array([7, 8], dtype=np.int64), 2026
    )
    for n in (16, 32, 64):
        axis = np.linspace(0.0, 1.0, n + 1)
        u, v = np.meshgrid(axis, axis)
        values = residual_basis(u[..., None], v[..., None], coefficients)
        means = np.trapezoid(np.trapezoid(values, axis, axis=0), axis, axis=0)
        assert np.max(np.abs(means)) < 1e-15
        assert np.count_nonzero(values[[0, -1], :]) == 0
        assert np.count_nonzero(values[:, [0, -1]]) == 0
    v = np.linspace(0.0, 1.0, 51)[:, None]
    for edge in (0.0, 1.0):
        epsilon = 1e-6 if edge == 0 else -1e-6
        difference = residual_basis(np.full_like(v, edge + epsilon), v, coefficients)
        assert np.max(np.abs(difference / epsilon)) < 1e-5
    np.testing.assert_array_equal(
        coefficients,
        cell_coefficients(
            np.array([10, 9], dtype=np.int64), np.array([8, 7], dtype=np.int64), 2026
        )[::-1],
    )


@pytest.mark.parametrize("value", [0.0, -1.0, float("nan"), float("inf"), 101.0, True])
def test_invalid_detail_amplitude_is_rejected(value: float) -> None:
    with pytest.raises(ValueError):
        RegionalDetailSettings(value)


def test_cell_budget_is_separate_from_delivered_sample_budget() -> None:
    grid = EndpointGrid((0.0, 0.0, 1000.0, 1000.0), 129, 129)
    request = RegionalSamplingRequest("a" * 64, grid, 8, (0, 0, 1024, 1024))
    with pytest.raises(ValueError, match="parent cells"):
        detail_cell_window(request)


def test_mismatched_parent_request_fails(
    detail_field: tuple[PreparedRegionalDetail, tuple[int, int]],
) -> None:
    field, origin = detail_field
    request = sample(field, origin, 8).samples.request
    with pytest.raises(ValueError, match="different parent"):
        field.sample(replace(request, source_id="0" * 64))


def test_finer_bound_violation_fails_instead_of_clipping(
    detail_field: tuple[PreparedRegionalDetail, tuple[int, int]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    field, origin = detail_field
    original = sample(field, origin, 8)
    positive = np.flatnonzero(original.added_detail_m > 0)
    assert positive.size
    index = int(positive[0])
    method = regional.TerrainRegionSampler.sample

    def corrupt(
        self: regional.TerrainRegionSampler, *args: Any, **kwargs: Any
    ) -> regional.RegionalTerrainSamples:
        baseline = method(self, *args, **kwargs)
        ground: NDArray[np.float32] = baseline.elevation_m.copy()
        ground.flat[index] = field.parent.data.project.settings.maximum_elevation_m
        return replace(baseline, elevation_m=ground)

    monkeypatch.setattr(regional.TerrainRegionSampler, "sample", corrupt)
    with pytest.raises(ValueError, match="between fixed probes"):
        sample(field, origin, 8)


def test_protected_ground_can_equal_the_rounded_float32_height_ceiling() -> None:
    coast, settings, _constraints = fixture("square", 65, 42)
    ceiling = 1234.56
    settings = replace(settings, maximum_elevation_m=ceiling, detail_levels=2)
    project = TerrainProject(coast, settings, (ElevationPoint((0.5, 0.5), ceiling, 50.0),))
    parent = numerical_parent(project)
    assert parent.data.elevation_m[32, 32] == np.float32(ceiling)
    assert float(np.float32(ceiling)) > ceiling
    field = prepare_regional_detail(parent, RegionalDetailSettings())
    result = sample(field, (28, 28), 8)
    assert result.samples.elevation_m[32, 32] == np.float32(ceiling)
    assert result.added_detail_m[32, 32] == 0


def test_recorded_moments_match_the_actual_fixed_probe_grid(
    detail_field: tuple[PreparedRegionalDetail, tuple[int, int]],
) -> None:
    field, origin = detail_field
    detail = sample(field, origin, 16)
    weights = np.ones((17, 17), dtype=np.float64)
    weights[[0, -1], :] *= 0.5
    weights[:, [0, -1]] *= 0.5
    weights /= 256
    for index in np.flatnonzero(np.isfinite(detail.reference_cell_mean_m)):
        x = (int(detail.cell_columns[index]) - origin[0]) * 16
        y = (int(detail.cell_rows[index]) - origin[1]) * 16
        reference = detail.reference_elevation_m[y : y + 17, x : x + 17].astype(np.float64)
        actual = detail.samples.elevation_m[y : y + 17, x : x + 17].astype(np.float64)
        assert np.sum(reference * weights) == pytest.approx(
            detail.reference_cell_mean_m[index], abs=1e-10, rel=0
        )
        assert np.sum(actual * weights) == pytest.approx(
            detail.detailed_cell_mean_m[index], abs=1e-10, rel=0
        )
