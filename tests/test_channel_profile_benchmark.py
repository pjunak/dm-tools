"""Protect finite-profile evidence, especially a climb hidden by descending endpoints."""

import numpy as np
import pytest
from numpy.typing import NDArray

from benchmarks.channel_profiles import measure_channels


def test_profiles_report_interior_rises_nonland_and_chunk_independence() -> None:
    x, y = np.array([0., 1.]), np.array([0., 1., 2.])
    receivers = np.array([[1, -1], [3, -1], [5, -1]], dtype=np.int64)
    channels = receivers >= 0
    calls: list[int] = []

    def sample(qx: NDArray[np.float64], qy: NDArray[np.float64]) -> NDArray[np.float32]:
        calls.append(qx.size)
        downhill = 10. - 5*qx
        hump = 40.*qx*(1-qx)
        values = downhill + np.where(qy == 1., hump, 0.)
        return np.where((qy == 2.) & (qx == .5), np.nan, values).astype(np.float32)

    result = measure_channels(x, y, receivers, channels, sample, stations=5, batch_edges=1)
    assert calls == [5, 5, 5]
    assert result["nonfinite_profile_count"] == 1
    assert result["descending"]["edge_count"] == 2
    assert result["descending"]["uphill_edge_count"] == 1
    assert result["descending"]["maximum_excursion_m"] == 7.5
    assert result["descending"]["excursion_threshold_counts"] == {
        "1": 1, "10": 0, "50": 0, "100": 0,
    }
    assert result["worst_descending_edges"][0]["source_flat_index"] == 2
    combined = measure_channels(x, y, receivers, channels, sample, stations=5, batch_edges=3)
    assert combined["profile_sha256"] == result["profile_sha256"]
    assert combined["descending"] == result["descending"]
    assert result["diagonal_descending"]["p95_excursion_m"] is None
    np.testing.assert_array_equal(receivers, [[1, -1], [3, -1], [5, -1]])


def test_profile_work_controls_and_empty_network() -> None:
    axis = np.array([0., 1.])
    receivers = np.full((2, 2), -1, dtype=np.int64)
    channels = np.zeros((2, 2), dtype=np.bool_)

    def unused(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray[np.float32]:
        pytest.fail("An empty network must not call the sampler")

    with pytest.raises(ValueError, match="stations"):
        measure_channels(axis, axis, receivers, channels, unused, stations=1026)
    report = measure_channels(axis, axis, receivers, channels, unused)
    assert report["selected_edge_count"] == 0
    assert report["requested_sample_count"] == 0
    assert report["descending"]["mean_excursion_m"] is None
    assert report["all_finite"]["excursion_threshold_counts"] == {
        "1": 0, "10": 0, "50": 0, "100": 0,
    }


def test_severity_counts_use_strict_metre_thresholds() -> None:
    x, y = np.array([0., 1.]), np.arange(4, dtype=np.float64)
    receivers = np.array([[1, -1], [3, -1], [5, -1], [7, -1]], dtype=np.int64)
    levels = np.array([1., 10., 50., 100.])

    def sample(qx: NDArray[np.float64], qy: NDArray[np.float64]) -> NDArray[np.float32]:
        return (levels[qy.astype(np.int64)]*(1.-np.abs(2*qx-1))).astype(np.float32)

    report = measure_channels(x, y, receivers, receivers >= 0, sample, stations=3)
    assert report["all_finite"]["excursion_threshold_counts"] == {
        "1": 3, "10": 2, "50": 1, "100": 0,
    }
