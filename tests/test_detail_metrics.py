# pyright: reportPrivateUsage=false
"""Spectral diagnostics separate broad wavelengths from local detail and zero fields."""

import numpy as np
import pytest

from benchmarks.detail_metrics import _power


def test_coarse_power_band_distinguishes_known_wavelengths() -> None:
    factor = 32
    axis = np.arange(8 * factor + 1, dtype=np.float64) / factor
    for cycles, expected in ((0.25, 0.99), (2.0, 0.00001)):
        values = np.broadcast_to(np.sin(2 * np.pi * cycles * axis), (axis.size, axis.size))
        total, coarse = _power(values, factor)
        assert total > 0
        if cycles < 0.5:
            assert coarse / total > expected
        else:
            assert coarse / total < expected
    assert _power(np.full((257, 257), 1500.0), factor) == (0.0, 0.0)


def test_power_scales_quadratically_with_height() -> None:
    axis = np.linspace(0, 8, 257)
    values = np.sin(2 * np.pi * 0.25 * axis)[None, :] * np.ones((257, 1))
    total, coarse = _power(values, 32)
    doubled_total, doubled_coarse = _power(2 * values, 32)
    assert doubled_total == pytest.approx(4 * total)
    assert doubled_coarse == pytest.approx(4 * coarse)
