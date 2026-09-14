"""Measure conservative component bounds against independent finite noise probes."""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from benchmarks import noise_intervals, noise_profiles
from benchmarks.noise_intervals import (
    MAX_CELLS,
    METHOD_ID,
    METHODS,
    BoundMethod,
    NoiseParameters,
    enclose_noise,
)
from benchmarks.noise_profiles import (
    MAX_SLABS,
    PROFILE_METHOD_ID,
    NoisePath,
    enclose_noise_profile,
    ordered_rise_upper_bound,
)
from benchmarks.terrain import ROOT, peak_resident_bytes
from dmtools.terrain.adapters.build import canonical_json, file_sha256, runtime_identity
from dmtools.terrain.pipeline.noise import fractal_value_noise

type ComparisonMethod = BoundMethod | Literal["profile_slabs"]
COMPARISON_METHODS: tuple[ComparisonMethod, ...] = (*METHODS, "profile_slabs")

DIRECTIONS = {"horizontal": 0.0, "diagonal": 1.0, "oblique": 0.37}
REFERENCE_INTERVALS = 65_536
AMPLITUDE_M, OFFSET_M = 1000.0, 2000.0


def source_identity() -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): file_sha256(path)
        for path in (Path(__file__), Path(noise_intervals.__file__), Path(noise_profiles.__file__))
    }


def validate_controls(
    divisions: tuple[int, ...], max_cells: int, repeats: int, max_slabs: int = MAX_SLABS
) -> None:
    if (
        not divisions
        or tuple(sorted(set(divisions))) != divisions
        or any(type(n) is not int or not 1 <= n <= 8192 or n & (n - 1) for n in divisions)
    ):
        raise ValueError("Noise divisions must be increasing powers of two up to 8192.")
    if type(max_cells) is not int or not 1 <= max_cells <= MAX_CELLS:
        raise ValueError("Noise cell budget must be an integer from 1 to 262144.")
    if type(max_slabs) is not int or not 1 <= max_slabs <= MAX_SLABS:
        raise ValueError("Noise slab budget must be an integer from 1 to 262144.")
    if type(repeats) is not int or not 1 <= repeats <= 10:
        raise ValueError("Noise repeats must be an integer from 1 to 10.")


def _field(positions: NDArray[np.float64], parameters: NoiseParameters) -> NDArray[np.float32]:
    values = fractal_value_noise(positions[:, 0], positions[:, 1], **asdict(parameters))
    return (OFFSET_M + AMPLITUDE_M * values).astype(np.float32)


def probe(
    parameters: NoiseParameters,
    span: float,
    direction: str,
    divisions: tuple[int, ...],
    max_cells: int,
    max_slabs: int = MAX_SLABS,
) -> dict[str, Any]:
    validate_controls(divisions, max_cells, 1, max_slabs)
    if direction not in DIRECTIONS or not np.isfinite(span) or not 0 < span <= 16:
        raise ValueError("Noise profile direction/span is unsupported.")
    start = np.asarray((-0.271, 0.193)) * parameters.largest_feature_km
    vector = np.asarray((1.0, DIRECTIONS[direction])) * (span * parameters.largest_feature_km)
    fractions = np.linspace(0.0, 1.0, REFERENCE_INTERVALS + 1)
    path = NoisePath((float(start[0]), float(start[1])), (float(vector[0]), float(vector[1])))
    positions = start + fractions[:, None] * vector
    reference_start = perf_counter()
    reference = _field(positions, parameters)
    reference_seconds = perf_counter() - reference_start
    reference_values = reference.astype(np.float64)
    reference_rise = float(np.max(reference_values - np.minimum.accumulate(reference_values)))
    trials: list[dict[str, Any]] = []
    timings: list[dict[str, Any]] = []
    for count in divisions:
        # Fixed dyadic stations, chosen without inspecting any reference heights.
        indices = np.arange(count + 1) * (REFERENCE_INTERVALS // count)
        anchors = positions[indices]
        boxes = np.column_stack(
            (np.minimum(anchors[:-1], anchors[1:]), np.maximum(anchors[:-1], anchors[1:]))
        )
        sample_start = perf_counter()
        samples = _field(anchors, parameters)
        sample_seconds = perf_counter() - sample_start
        if samples.tobytes() != reference[indices].tobytes():
            raise RuntimeError("Noise component changed at shared binary64 positions.")
        sample_values = samples.astype(np.float64)
        sample_rise = float(np.max(sample_values - np.minimum.accumulate(sample_values)))
        spans = np.column_stack((fractions[indices[:-1]], fractions[indices[1:]]))
        for method in COMPARISON_METHODS:
            bound_start = perf_counter()
            if method == "profile_slabs":
                result = enclose_noise_profile(
                    path,
                    spans,
                    parameters,
                    amplitude_m=AMPLITUDE_M,
                    offset_m=OFFSET_M,
                    max_cells=max_cells,
                    max_slabs=max_slabs,
                )
            else:
                result = enclose_noise(
                    boxes,
                    parameters,
                    amplitude_m=AMPLITUDE_M,
                    offset_m=OFFSET_M,
                    max_cells=max_cells,
                    method=method,
                )
            bound_seconds = perf_counter() - bound_start
            trial: dict[str, Any] = {
                "method": method,
                "divisions": count,
                "box_count": len(boxes),
                "status": result.status,
                "requested_cell_count": result.requested_cell_count,
                "requested_slab_count": result.requested_slab_count,
                "evaluated_cell_count": result.evaluated_cell_count,
                "sample_count": len(samples),
                "positions_sha256": sha256(anchors.tobytes()).hexdigest(),
                "samples_sha256": sha256(samples.tobytes()).hexdigest(),
                "sampled_uphill_m": sample_rise,
                "missed_reference_uphill_m": reference_rise - sample_rise,
                "sampled_minimum_m": float(np.min(samples)),
                "sampled_maximum_m": float(np.max(samples)),
                "missed_reference_peak_m": float(np.max(reference)) - float(np.max(samples)),
                "missed_reference_trough_m": float(np.min(samples)) - float(np.min(reference)),
                "enclosure": None,
            }
            if result.field_m is not None and result.noise is not None:
                field = result.field_m
                owners = np.minimum(
                    np.arange(REFERENCE_INTERVALS + 1) * count // REFERENCE_INTERVALS, count - 1
                )
                if not np.all((field.low[owners] <= reference) & (reference <= field.high[owners])):
                    raise RuntimeError("A component bound excluded an independent finite probe.")
                rise_bound = ordered_rise_upper_bound(field)
                if rise_bound < reference_rise:
                    raise RuntimeError(
                        "An ordered-rise bound excluded a finite reference excursion."
                    )
                trial["enclosure"] = {
                    "maximum_uphill_upper_bound_m": rise_bound,
                    "uphill_gap_m": rise_bound - sample_rise,
                    "uphill_excess_over_finite_reference_m": rise_bound - reference_rise,
                    "minimum_lower_bound_m": float(np.min(field.low)),
                    "maximum_upper_bound_m": float(np.max(field.high)),
                    "maximum_interval_width_m": float(np.max(field.high - field.low)),
                    "maximum_extremum_gap_m": max(
                        float(np.max(field.high) - np.max(samples)),
                        float(np.min(samples) - np.min(field.low)),
                    ),
                    "upper_excess_over_finite_reference_m": float(
                        np.max(field.high) - np.max(reference)
                    ),
                    "lower_excess_over_finite_reference_m": float(
                        np.min(reference) - np.min(field.low)
                    ),
                    "bounds_sha256": sha256(
                        b"".join(
                            a.tobytes()
                            for a in (result.noise.low, result.noise.high, field.low, field.high)
                        )
                    ).hexdigest(),
                    "reference_outside_count": 0,
                }
            trials.append(trial)
            timings.append(
                {
                    "method": method,
                    "divisions": count,
                    "bound_seconds": bound_seconds,
                    "point_sample_seconds": sample_seconds,
                }
            )
    inputs = {
        "noise": asdict(parameters),
        "span_in_largest_features": span,
        "direction": direction,
        "start_km": start.tolist(),
        "vector_km": vector.tolist(),
        "amplitude_m": AMPLITUDE_M,
        "offset_m": OFFSET_M,
        "divisions": divisions,
        "max_cells": max_cells,
        "methods": COMPARISON_METHODS,
        "max_slabs": max_slabs,
    }
    evidence = {
        "reference_count": len(reference),
        "reference_positions_sha256": sha256(positions.tobytes()).hexdigest(),
        "reference_values_sha256": sha256(reference.tobytes()).hexdigest(),
        "reference_uphill_m": reference_rise,
        "reference_minimum_m": float(np.min(reference)),
        "reference_maximum_m": float(np.max(reference)),
        "trials": trials,
    }
    return {
        "input": inputs,
        "input_sha256": sha256(canonical_json(inputs)).hexdigest(),
        "evidence": evidence,
        "evidence_sha256": sha256(canonical_json(evidence)).hexdigest(),
        "timing": {"reference_seconds": reference_seconds, "trials": timings},
        "peak_resident_bytes": peak_resident_bytes(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", nargs="+", type=int, default=[42])
    parser.add_argument("--detail", nargs="+", type=int, default=[1, 6, 12])
    parser.add_argument("--roughness", nargs="+", type=float, default=[0.55])
    parser.add_argument("--span", nargs="+", type=float, default=[0.25, 2.0])
    parser.add_argument(
        "--direction", nargs="+", choices=DIRECTIONS, default=["horizontal", "oblique"]
    )
    parser.add_argument("--divisions", nargs="+", type=int, default=[1, 16, 256])
    parser.add_argument("--max-cells", type=int, default=MAX_CELLS)
    parser.add_argument("--max-slabs", type=int, default=MAX_SLABS)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        validate_controls(tuple(args.divisions), args.max_cells, args.repeats, args.max_slabs)
        for seed in args.seed:
            for detail in args.detail:
                for roughness in args.roughness:
                    NoiseParameters(seed=seed, detail_levels=detail, roughness=roughness)
        if any(not np.isfinite(s) or not 0 < s <= 16 for s in args.span):
            raise ValueError(
                "Noise spans must be finite, positive and at most 16 largest features."
            )
    except ValueError as error:
        parser.error(str(error))
    if args.worker:
        result = probe(
            NoiseParameters(
                seed=args.seed[0], detail_levels=args.detail[0], roughness=args.roughness[0]
            ),
            args.span[0],
            args.direction[0],
            tuple(args.divisions),
            args.max_cells,
            args.max_slabs,
        )
        print(canonical_json(result).decode())
        return
    if args.output is None:
        parser.error("--output is required.")
    runtime, sources = runtime_identity(), source_identity()
    runs: list[dict[str, Any]] = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        for seed in args.seed:
            for detail in args.detail:
                for roughness in args.roughness:
                    for span in args.span:
                        for direction in args.direction:
                            previous: dict[str, Any] | None = None
                            for _ in range(args.repeats):
                                command = [
                                    sys.executable,
                                    "-m",
                                    "benchmarks.noise_bounds",
                                    "--worker",
                                    "--seed",
                                    str(seed),
                                    "--detail",
                                    str(detail),
                                    "--roughness",
                                    str(roughness),
                                    "--span",
                                    str(span),
                                    "--direction",
                                    direction,
                                    "--max-cells",
                                    str(args.max_cells),
                                    "--max-slabs",
                                    str(args.max_slabs),
                                    "--divisions",
                                    *(str(n) for n in args.divisions),
                                ]
                                done = subprocess.run(
                                    command, cwd=ROOT, capture_output=True, text=True, check=True
                                )
                                run = json.loads(done.stdout)
                                if previous and any(
                                    run[key] != previous[key]
                                    for key in ("input_sha256", "evidence_sha256")
                                ):
                                    raise RuntimeError(
                                        "Identical noise inputs produced different bounds."
                                    )
                                previous = run
                                runs.append(run)
                            print(
                                f"seed={seed} detail={detail} roughness={roughness} "
                                f"span={span} {direction}: compared",
                                flush=True,
                            )
        if runtime != runtime_identity() or sources != source_identity():
            raise RuntimeError("Generator, runtime or bound source changed during inspection.")
        report = {
            "schema": "dmtools.noise-component-bounds",
            "schema_version": 2,
            "complete": True,
            "runtime": runtime,
            "comparison_source_sha256": sources,
            "method": {
                "method_id": METHOD_ID,
                "policies": COMPARISON_METHODS,
                "profile_method_id": PROFILE_METHOD_ID,
                "slab_budget": args.max_slabs,
                "fresh_process_per_run": True,
                "changes_terrain": False,
                "complete_terrain_bound": False,
                "scope": "Float32(offset + amplitude * existing fractal value noise)",
                "reference": "65537 independent finite probes; not an inclusion proof",
                "rounding": "outward binary64 elementary operations and final binary32 conversion",
                "cell_budget": args.max_cells,
            },
            "runs": runs,
        }
        stream.write(canonical_json(report).decode())
        stream.flush()
        os.fsync(stream.fileno())


if __name__ == "__main__":
    main()
