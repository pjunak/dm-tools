"""Bound-driven noise refinement must earn tolerance and preserve full budgets."""

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from benchmarks.noise_intervals import Interval, NoiseParameters
from benchmarks.noise_profiles import NoisePath, enclose_noise_profile
from benchmarks.noise_refinement import (
    RefinedProfile,
    RefinementControls,
    path_positions,
    profile_uncertainty,
    refine_noise_profile,
    sample_path,
)
from benchmarks.terrain import ROOT

PATH = NoisePath((-0.542, 0.386), (4.0, 4.0))


@pytest.mark.parametrize("detail", [1, 6, 12])
@pytest.mark.parametrize(
    "path",
    [
        PATH,
        NoisePath((3.458, 4.386), (-4.0, -4.0)),
        NoisePath((-2.0, 1.0), (4.0, 0.0)),
        NoisePath((-1.0, -2.0), (0.0, 4.0)),
        NoisePath((1.0, 1.0), (2.0**-52, -(2.0**-53))),
        NoisePath((2.0**30, -(2.0**30)), (0.001, -0.01)),
    ],
)
def test_hybrid_geometry_covers_rounded_path_positions(path: NoisePath, detail: int) -> None:
    parameters = NoiseParameters(detail_levels=detail, roughness=0.9)
    knots = np.asarray((0.0, 0.25, 0.2501, 0.5, 1.0))
    spans = np.column_stack((knots[:-1], knots[1:]))
    before = spans.tobytes()
    result = enclose_noise_profile(path, spans, parameters, geometry="hybrid")
    assert result.status == "bounded" and result.field_m is not None
    fractions = np.linspace(0.0, 1.0, 8193)
    values = sample_path(path, fractions, parameters, amplitude_m=1000.0, offset_m=2000.0)
    owners = np.minimum(np.searchsorted(knots, fractions, side="right") - 1, len(spans) - 1)
    assert np.all(result.field_m.low[owners] <= values)
    assert np.all(values <= result.field_m.high[owners])
    assert spans.tobytes() == before
    reverse = enclose_noise_profile(path, spans[::-1], parameters, geometry="hybrid")
    assert reverse.field_m is not None
    assert reverse.field_m.low[::-1].tobytes() == result.field_m.low.tobytes()
    assert reverse.field_m.high[::-1].tobytes() == result.field_m.high.tobytes()


def test_short_spans_do_not_allocate_strips_and_zero_remaining_budget_is_honest() -> None:
    knots = np.linspace(0.0, 1.0, 257)
    spans = np.column_stack((knots[:-1], knots[1:]))
    parameters = NoiseParameters(detail_levels=6)
    with patch("benchmarks.noise_profiles._cell_plan", side_effect=AssertionError("clipped")):
        result = enclose_noise_profile(PATH, spans, parameters, geometry="hybrid", max_slabs=0)
    assert result.status == "bounded" and result.requested_slab_count == 0
    assert result.clipped_plan_count == 0 and result.rectangle_plan_count == 256 * 6
    with patch(
        "benchmarks.noise_intervals._lattice_values", side_effect=AssertionError("evaluated")
    ):
        failed = enclose_noise_profile(
            PATH, spans, parameters, geometry="hybrid", max_slabs=0, max_cells=0
        )
    assert failed.status == "cell_budget_exceeded" and failed.evaluated_cell_count == 0
    assert failed.requested_cell_count == result.requested_cell_count
    assert failed.field_m is None


def test_mixed_geometry_counts_the_whole_request_before_evaluation() -> None:
    spans = np.asarray(((0.0, 0.5), (0.5, 0.5001), (0.5001, 1.0)))
    parameters = NoiseParameters(detail_levels=6)
    result = enclose_noise_profile(PATH, spans, parameters, geometry="hybrid")
    assert result.requested_cell_count is not None and result.requested_slab_count is not None
    assert result.rectangle_plan_count and result.clipped_plan_count
    with patch(
        "benchmarks.noise_intervals._lattice_values", side_effect=AssertionError("evaluated")
    ):
        failed = enclose_noise_profile(
            PATH, spans, parameters, geometry="hybrid", max_cells=result.requested_cell_count - 1
        )
    assert failed.evaluated_cell_count == 0 and failed.field_m is None
    assert failed.requested_cell_count == result.requested_cell_count
    with patch(
        "benchmarks.noise_profiles._geometry_cells", side_effect=AssertionError("allocated")
    ):
        failed = enclose_noise_profile(
            PATH, spans, parameters, geometry="hybrid", max_slabs=result.requested_slab_count - 1
        )
    assert failed.status == "slab_budget_exceeded" and failed.requested_cell_count is None


def test_rise_refinement_marks_both_ends_even_when_local_gaps_are_small() -> None:
    profile = RefinedProfile(
        np.asarray((0.0, 0.25, 0.75, 1.0)),
        np.asarray((0.0, 0.0, 10.0, 10.0), dtype=np.float32),
        Interval(np.asarray((-0.75, 0.0, 10.0)), np.asarray((0.0, 10.0, 10.75))),
        np.asarray((2, 1, 2)),
    )
    metrics, selected = profile_uncertainty(profile, 1.0)
    assert metrics.maximum_local_gap_m < 1.0 and metrics.uphill_gap_m > 1.0
    assert selected.tolist() == [True, False, True]
    hidden = RefinedProfile(
        np.asarray((0.0, 1.0)),
        np.zeros(2, dtype=np.float32),
        Interval(np.asarray((0.0,)), np.asarray((20.0,))),
        np.zeros(1, dtype=np.int64),
    )
    metrics, selected = profile_uncertainty(hidden, 1.0)
    assert metrics.maximum_local_gap_m >= 20.0 and metrics.uphill_gap_m >= 20.0
    assert selected.tolist() == [True]


@pytest.mark.parametrize("amplitude,offset", [(1000.0, 2000.0), (-500.0, 100.0), (0.0, -2.0)])
@pytest.mark.parametrize("path", [PATH, NoisePath((1.0, -1.0), (-1.2, 0.3))])
def test_accepted_profiles_cover_independent_probes_and_meet_both_tolerances(
    path: NoisePath,
    amplitude: float,
    offset: float,
) -> None:
    parameters = NoiseParameters(detail_levels=6)
    result = refine_noise_profile(
        path, parameters, RefinementControls(2.0), amplitude_m=amplitude, offset_m=offset
    )
    assert result.status == "tolerance_met" and result.profile is not None
    p = result.profile
    reference_t = np.linspace(0.0, 1.0, 65537)
    reference = sample_path(path, reference_t, parameters, amplitude_m=amplitude, offset_m=offset)
    owners = np.minimum(
        np.searchsorted(p.fractions, reference_t, side="right") - 1, len(p.depths) - 1
    )
    assert np.all((p.field_m.low[owners] <= reference) & (reference <= p.field_m.high[owners]))
    samples = sample_path(path, p.fractions, parameters, amplitude_m=amplitude, offset_m=offset)
    assert samples.tobytes() == p.samples_m.tobytes()
    # A shared boundary belongs to both closed intervals, even when the dense
    # reference assigns that point only to the following interval.
    assert np.all(p.field_m.low <= np.minimum(samples[:-1], samples[1:]))
    assert np.all(p.field_m.high >= np.maximum(samples[:-1], samples[1:]))
    assert np.all(np.diff(p.fractions) > 0.0) and p.fractions[0] == 0.0 and p.fractions[-1] == 1.0
    assert result.evaluated_sample_count == len(p.fractions)
    assert np.all(np.diff(p.fractions) == 2.0**-p.depths)
    metrics = result.waves[-1].metrics
    assert metrics.maximum_local_gap_m <= 2.0 and metrics.uphill_gap_m <= 2.0
    ref64 = reference.astype(np.float64)
    ref_rise = float(np.max(ref64 - np.minimum.accumulate(ref64)))
    assert ref_rise <= metrics.uphill_upper_bound_m
    assert ref_rise - metrics.sampled_uphill_lower_bound_m <= 2.0
    assert len(np.unique(path_positions(path, p.fractions), axis=0)) >= 2


def test_adaptive_work_is_reproducible_and_smaller_than_uniform_for_localized_uncertainty() -> None:
    parameters = NoiseParameters(detail_levels=6)
    controls = RefinementControls(1.0)
    first = refine_noise_profile(PATH, parameters, controls)
    second = refine_noise_profile(PATH, parameters, controls)
    uniform = refine_noise_profile(PATH, parameters, replace(controls, strategy="uniform"))
    assert first.status == second.status == uniform.status == "tolerance_met"
    assert first.waves == second.waves
    assert first.profile is not None and second.profile is not None
    assert first.profile.fractions.tobytes() == second.profile.fractions.tobytes()
    assert first.profile.field_m.low.tobytes() == second.profile.field_m.low.tobytes()
    assert first.evaluated_cell_count < uniform.evaluated_cell_count
    assert first.evaluated_sample_count < uniform.evaluated_sample_count
    assert len(set(first.profile.depths.tolist())) > 1


def test_cumulative_cell_and_sample_budgets_do_not_reset_between_waves() -> None:
    parameters = NoiseParameters(detail_levels=1)
    original = refine_noise_profile(PATH, parameters, RefinementControls(5.0))
    assert original.status == "tolerance_met"
    exact = RefinementControls(
        5.0,
        max_cells=original.evaluated_cell_count,
        max_slabs=original.allocated_slab_count,
        max_samples=original.evaluated_sample_count,
    )
    replay = refine_noise_profile(PATH, parameters, exact)
    assert replay.status == "tolerance_met" and replay.waves == original.waves
    cells = refine_noise_profile(PATH, parameters, replace(exact, max_cells=exact.max_cells - 1))
    assert cells.status == "cell_budget_exceeded" and cells.profile is None
    assert cells.required_cell_count == exact.max_cells
    assert cells.evaluated_cell_count < exact.max_cells
    assert cells.evaluated_sample_count < exact.max_samples
    samples = refine_noise_profile(
        PATH, parameters, replace(exact, max_samples=exact.max_samples - 1)
    )
    assert samples.status == "sample_budget_exceeded" and samples.profile is None
    assert samples.required_sample_count == exact.max_samples
    assert samples.evaluated_sample_count < exact.max_samples
    assert samples.required_cell_count is None and samples.required_slab_count is None


def test_cumulative_slab_exhaustion_never_evaluates_the_pending_wave() -> None:
    parameters = NoiseParameters(detail_levels=1)
    initial = enclose_noise_profile(PATH, np.asarray(((0.0, 1.0),)), parameters)
    assert initial.requested_slab_count is not None
    with patch("benchmarks.noise_refinement.sample_path", wraps=sample_path) as sample:
        result = refine_noise_profile(
            PATH,
            parameters,
            RefinementControls(1.0, geometry="slabs", max_slabs=initial.requested_slab_count),
        )
    assert result.status == "slab_budget_exceeded" and result.profile is None
    assert len(result.waves) == 1 and sample.call_count == 1
    assert result.evaluated_sample_count == 2
    assert result.allocated_slab_count == initial.requested_slab_count
    assert (
        result.required_slab_count is not None
        and result.required_slab_count > result.allocated_slab_count
    )
    assert result.required_cell_count is None


def test_initial_cell_failure_and_terminal_depth_precision_have_no_accepted_profile() -> None:
    parameters = NoiseParameters(detail_levels=1)
    with patch("benchmarks.noise_refinement.sample_path", side_effect=AssertionError("sampled")):
        initial = refine_noise_profile(PATH, parameters, RefinementControls(1.0, max_cells=1))
    assert initial.status == "cell_budget_exceeded" and initial.profile is None
    assert initial.evaluated_sample_count == initial.evaluated_cell_count == 0
    depth = refine_noise_profile(PATH, parameters, RefinementControls(1.0, max_depth=0))
    assert depth.status == "depth_exhausted" and depth.profile is None
    assert depth.evaluated_sample_count == 2 and len(depth.waves) == 1
    precision = refine_noise_profile(
        NoisePath((1.0, 1.0), (2.0**-55, 2.0**-55)), parameters, RefinementControls(1e-8)
    )
    assert precision.status == "precision_exhausted" and precision.profile is None
    unsupported = refine_noise_profile(
        NoisePath((1e100, 0.0), (1.0, 1.0)), parameters, RefinementControls(1.0)
    )
    assert unsupported.status == "coordinate_range_exceeded" and not unsupported.waves


@pytest.mark.parametrize(
    "kwargs",
    [
        {"tolerance_m": 0.0},
        {"tolerance_m": float("inf")},
        {"tolerance_m": float("nan")},
        {"tolerance_m": True},
        {"max_cells": 0},
        {"max_cells": 262145},
        {"max_slabs": -1},
        {"max_samples": 1},
        {"max_samples": 65537},
        {"max_depth": -1},
        {"max_depth": 17},
        {"max_depth": True},
        {"geometry": "unknown"},
        {"strategy": "unknown"},
    ],
)
def test_invalid_controls_are_rejected(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        RefinementControls(**({"tolerance_m": 1.0} | kwargs))  # pyright: ignore[reportArgumentType]


def test_runner_records_replayable_acceptance_and_unresolved_limits(tmp_path: Path) -> None:
    output = tmp_path / "refinement.json"
    command = [
        sys.executable,
        "-m",
        "benchmarks.noise_bounds",
        "--detail",
        "1",
        "--span",
        "2",
        "--direction",
        "diagonal",
        "--divisions",
        "1",
        "16",
        "--adaptive-tolerance",
        "1",
        "--repeats",
        "2",
        "--output",
        str(output),
    ]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    data = json.loads(output.read_text())
    assert data["complete"] and data["schema_version"] == 3
    first, second = data["runs"]
    assert first["evidence_sha256"] == second["evidence_sha256"]
    trials = first["evidence"]["refinement_trials"]
    assert len(trials) == 3
    assert all(t["status"] == "tolerance_met" for t in trials)
    assert all(t["accepted"]["reference_outside_count"] == 0 for t in trials)
    limited = tmp_path / "limited.json"
    command[command.index(str(output))] = str(limited)
    command.extend(["--adaptive-max-samples", "2"])
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    for run in json.loads(limited.read_text())["runs"]:
        for trial in run["evidence"]["refinement_trials"]:
            assert trial["status"] == "sample_budget_exceeded" and trial["accepted"] is None
            assert trial["evaluated_sample_count"] == 2
