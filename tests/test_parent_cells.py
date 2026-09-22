"""Independent invariants for the all-land parent-cell projection experiment."""

from typing import cast

import numpy as np
import pytest
from numpy.typing import NDArray

from benchmarks.parent_cells import (
    parent_cell_means,
    project_parent_cells,
    restrict_cell_means,
)
from benchmarks.parent_detail import sample_grid


def _proposal(factor: int, height: int = 3, width: int = 4) -> NDArray[np.float64]:
    x, y = np.meshgrid(np.arange((width-1)*factor+1)/factor,
                       np.arange((height-1)*factor+1)/factor)
    return 2000. + 1700.*np.sin(4.3*x+.7)*np.cos(5.1*y) + 25.*x*y


@pytest.mark.parametrize("factor", [4, 8, 16, 32, 64])
@pytest.mark.parametrize("seed", [7, 42, 104729])
def test_delivered_float32_preserves_nodes_cell_means_and_bounds(factor: int, seed: int) -> None:
    parent = np.random.default_rng(seed).uniform(20., 5980., (3, 4)).astype(np.float32)
    proposal = _proposal(factor)
    originals = parent.copy(), proposal.copy()
    result = project_parent_cells(parent, proposal, factor, maximum_elevation_m=6000.)
    values = result.elevation_m
    np.testing.assert_array_equal(values[::factor, ::factor], parent)
    assert values.dtype == np.float32 and np.isfinite(values).all()
    assert values.min() >= 0 and values.max() <= 6000.
    assert np.all((result.detail_scale >= 0) & (result.detail_scale <= 1))
    for row, col in np.ndindex(2, 3):
        child = values[row*factor:(row+1)*factor+1, col*factor:(col+1)*factor+1]
        mean = np.trapezoid(np.trapezoid(child.astype(np.float64), dx=1/factor, axis=1),
                           dx=1/factor)
        expected = float(parent[row:row+2, col:col+2].astype(np.float64).mean())
        assert abs(mean-expected) <= result.quantization_tolerance_m
    np.testing.assert_array_equal(parent, originals[0])
    np.testing.assert_array_equal(proposal, originals[1])
    for array in (values, result.detail_scale, result.weighted_bias_m):
        assert not array.flags.writeable
    frozen = values.copy()
    parent[:] = 0.
    proposal[:] = 0.
    np.testing.assert_array_equal(values, frozen)


@pytest.mark.parametrize("factor", [4, 16, 64])
def test_whole_cells_agree_across_overlapping_windows_and_repeated_order(factor: int) -> None:
    parent = (1000. + np.arange(20).reshape(4, 5)*30.).astype(np.float32)
    proposal = _proposal(factor, 4, 5)
    complete = project_parent_cells(parent, proposal, factor, maximum_elevation_m=6000.)
    for top, left, bottom, right in ((0, 0, 3, 3), (1, 1, 3, 4), (0, 0, 3, 3)):
        ys, xs = slice(top*factor, bottom*factor+1), slice(left*factor, right*factor+1)
        part = project_parent_cells(parent[top:bottom+1, left:right+1], proposal[ys, xs], factor,
                                    maximum_elevation_m=6000.)
        np.testing.assert_array_equal(part.elevation_m, complete.elevation_m[ys, xs])
        np.testing.assert_array_equal(part.detail_scale,
                                       complete.detail_scale[top:bottom, left:right])
    t = np.arange(factor+1)/factor
    for row, col in np.ndindex(3, 4):
        edge = parent[row, col].astype(np.float64) + t*float(parent[row+1, col]-parent[row, col])
        np.testing.assert_array_equal(
            complete.elevation_m[row*factor:(row+1)*factor+1, col*factor], edge.astype(np.float32))


def test_constant_offset_is_removed_while_zero_mean_structure_survives() -> None:
    parent = np.full((2, 2), 800., dtype=np.float32)
    flat = project_parent_cells(parent, np.full((17, 17), 1800.), 16, maximum_elevation_m=6000.)
    np.testing.assert_array_equal(flat.elevation_m, 800.)
    candidate = _proposal(16, 2, 2)
    result = project_parent_cells(parent, candidate, 16, maximum_elevation_m=6000.)
    assert result.elevation_m.max()-result.elevation_m.min() > 100.
    assert result.maximum_cell_mean_error_m <= result.quantization_tolerance_m


@pytest.mark.parametrize("height", [0., 6000.])
def test_extreme_flat_parent_cannot_gain_zero_mean_detail_within_bounds(height: float) -> None:
    parent = np.full((2, 2), height, dtype=np.float32)
    candidate = _proposal(8, 2, 2)
    result = project_parent_cells(parent, candidate, 8, maximum_elevation_m=6000.)
    np.testing.assert_array_equal(result.elevation_m, height)
    np.testing.assert_array_equal(result.detail_scale, 0.)


def test_inward_float32_ceiling_and_strong_attenuation_preserve_means() -> None:
    parent = np.array([[.01, 20.], [30., 1000.]], dtype=np.float32)
    result = project_parent_cells(parent, _proposal(16, 2, 2)*1e6, 16,
                                   maximum_elevation_m=1000.12345)
    assert result.detail_scale[0, 0] < .01
    assert float(result.elevation_m.max()) <= 1000.12345
    assert result.maximum_cell_mean_error_m <= result.quantization_tolerance_m


def test_restriction_is_trapezoidal_rather_than_pixel_average() -> None:
    x, y = np.meshgrid(np.linspace(0., 2., 9), np.linspace(0., 1., 5))
    z = 10. + x*y + x*x
    expected = np.array([[10. + .25 + .34375, 10. + .75 + 2.34375]])
    np.testing.assert_allclose(restrict_cell_means(z, 4), expected, rtol=0, atol=1e-14)
    assert abs(float(z[:, :5].mean())-expected[0, 0]) > .03
    np.testing.assert_array_equal(parent_cell_means(np.array([[0., 2.], [4., 6.]])), [[3.]])


@pytest.mark.parametrize("factor", [0, 2, 3, 5, 128, True, 4.0])
def test_invalid_refinement_is_rejected(factor: object) -> None:
    with pytest.raises(ValueError, match="refinement"):
        project_parent_cells(np.ones((2, 2), np.float32), np.ones((5, 5)),
                             cast(int, factor), maximum_elevation_m=6000.)


@pytest.mark.parametrize("case", ["nan", "inf", "negative_parent", "above_ceiling", "shape",
                                  "partial_cell", "parent_dtype", "integer", "one_dimensional",
                                  "out_of_range"])
def test_invalid_or_partial_cells_are_rejected(case: str) -> None:
    parent, proposal = np.full((2, 2), 500., dtype=np.float32), np.ones((5, 5))
    if case == "nan":
        proposal[2, 2] = np.nan
    elif case == "inf":
        parent[0, 0] = np.inf
    elif case == "negative_parent":
        parent[0, 0] = -1.
    elif case == "above_ceiling":
        parent[0, 0] = 6001.
    elif case == "out_of_range":
        proposal[2, 2] = 1e100
    elif case == "shape":
        proposal = np.ones((9, 9))
    elif case == "partial_cell":
        with pytest.raises(ValueError, match="complete parent-cell"):
            restrict_cell_means(np.ones((6, 5)), 4)
        return
    elif case == "parent_dtype":
        parent = cast(NDArray[np.float32], parent.astype(np.float64))
    elif case == "integer":
        proposal = cast(NDArray[np.float64], np.ones((5, 5), dtype=np.int64))
    else:
        proposal = np.ones(5)
    with pytest.raises(ValueError):
        project_parent_cells(parent, proposal, 4, maximum_elevation_m=6000.)


@pytest.mark.parametrize("ceiling", [0., -1., float("nan"), float("inf"), True])
def test_invalid_ceiling_is_rejected(ceiling: float) -> None:
    with pytest.raises(ValueError, match="ceiling"):
        project_parent_cells(np.ones((2, 2), np.float32), np.ones((5, 5)), 4,
                             maximum_elevation_m=ceiling)


def test_budget_rejection_happens_before_projection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("benchmarks.parent_cells.REGIONAL_SAMPLE_LIMIT", 24)
    with pytest.raises(ValueError, match="sample limit"):
        project_parent_cells(np.ones((2, 2), np.float32), np.ones((5, 5)), 4,
                             maximum_elevation_m=6000.)



def test_profile_sampling_reconstructs_bilinear_values_on_nonuniform_axes() -> None:
    x, y = np.array([0., 2., 5., 9.]), np.array([-3., 1., 7.])
    xx, yy = np.meshgrid(x, y)
    values = (100. + 2.*xx - 3.*yy + .5*xx*yy).astype(np.float32)
    qx = np.array([[0., 9., 5., 1.25], [2., 8.5, 0., 9.]])
    qy = np.array([[-3., 7., 1., 2.5], [0., -1.25, 7., -3.]])
    expected = (100. + 2.*qx - 3.*qy + .5*qx*qy).astype(np.float32)
    np.testing.assert_array_equal(sample_grid(x, y, values, qx, qy), expected)


@pytest.mark.parametrize('case', ['outside_x', 'outside_y', 'nonfinite', 'shape'])
def test_profile_sampling_rejects_invalid_queries(case: str) -> None:
    axis = np.array([0., 1.])
    qx, qy = np.array([.5]), np.array([.5])
    if case == 'outside_x':
        qx[0] = 1.01
    elif case == 'outside_y':
        qy[0] = -.01
    elif case == 'nonfinite':
        qx[0] = np.nan
    else:
        qy = np.array([.5, .5])
    with pytest.raises(ValueError, match='inside the measured child'):
        sample_grid(axis, axis, np.ones((2, 2), dtype=np.float32), qx, qy)
