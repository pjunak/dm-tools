# pyright: reportPrivateUsage=false
"""Fresh-process observations of regional admission estimates and native peak memory."""

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, fields, is_dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from benchmarks.parent_session import artifact_identity, workload
from benchmarks.terrain import peak_resident_bytes
from dmtools.terrain.adapters.build import canonical_json, file_sha256, runtime_identity
from dmtools.terrain.application.parent_region import ParentRegionSession
from dmtools.terrain.application.region_memory import RegionalMemoryBudget
from dmtools.terrain.domain import EndpointGrid
from dmtools.terrain.domain.regional import RegionalDetailSettings


def numeric_storage(*roots: object) -> int:
    """Count unique backing NumPy allocations in owned dataclass/tuple contexts."""
    seen: set[int] = set()
    buffers: dict[int, int] = {}

    def visit(value: object) -> None:
        if id(value) in seen:
            return
        seen.add(id(value))
        if isinstance(value, np.ndarray):
            array = cast(NDArray[Any], value)
            while isinstance(array.base, np.ndarray):
                array = array.base
            if not array.flags.owndata or array.dtype.hasobject:
                raise ValueError("Unexpected numeric backing store in benchmark context.")
            buffers[id(array)] = array.nbytes
        elif is_dataclass(value) and not isinstance(value, type):
            for item in fields(value):
                visit(getattr(value, item.name))
        elif isinstance(value, tuple):
            for member in cast(tuple[object, ...], value):
                visit(member)

    for root in roots:
        visit(root)
    return sum(buffers.values())


def measure(source: Path, destination: Path, factor: int, mode: str) -> dict[str, object]:
    runtime = runtime_identity()
    document: dict[str, Any] = json.loads((source / "manifest.json").read_bytes())
    frame = document["coordinates"]
    grid = EndpointGrid(tuple(frame["extent_km"]), frame["width"], frame["height"])
    bounds = workload(grid)[0][1]
    baseline = peak_resident_bytes()
    budget = RegionalMemoryBudget()
    settings = RegionalDetailSettings(40.) if mode == "detail" else None
    steps: list[dict[str, object]] = []
    identity = None
    with ParentRegionSession(source, memory_budget=budget) as session:
        retained = session.memory_info().retained
        assert retained is not None
        loaded_bytes = numeric_storage(session._loaded)
        if loaded_bytes != retained.loaded_array_bytes:
            raise RuntimeError("Loaded-array estimate disagrees with owned allocations.")
        for label in ("cold", "cached"):
            estimate = session.estimate_write(bounds, factor, detail_settings=settings)
            start = perf_counter()
            manifest = session.write(destination / label, bounds, factor, detail_settings=settings)
            seconds = perf_counter() - start
            peak = peak_resident_bytes()
            digest = artifact_identity(manifest)
            if identity is not None and identity != digest:
                raise RuntimeError("Cache reuse changed artifact bytes.")
            identity = digest
            numeric = numeric_storage(session._loaded, session._parent)
            if numeric > retained.loaded_array_bytes + retained.prepared_array_allowance_bytes:
                raise RuntimeError("Observed retained arrays exceed their admission allowance.")
            steps.append({
                "label": label, "seconds": seconds, "process_peak_bytes": peak,
                "job_estimate": asdict(estimate), "job_estimated_bytes": estimate.total_bytes,
                "parent_numeric_bytes": numeric, "cache": asdict(session.cache_info()),
                "manifest_sha256": digest,
            })
    if budget.info().reserved_bytes or budget.info().reservations:
        raise RuntimeError("Closing a session did not release admission reservations.")
    if runtime_identity() != runtime:
        raise RuntimeError("Runtime changed during the benchmark.")
    return {
        "parent_build_id": document["build_id"], "runtime": runtime, "mode": mode,
        "refinement": factor, "baseline_process_peak_bytes": baseline,
        "retained_estimate": asdict(retained), "retained_estimated_bytes": retained.total_bytes,
        "admission": asdict(budget.info()), "steps": steps,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", nargs="+", type=Path, required=True)
    parser.add_argument("--refine", nargs="+", type=int, default=[8, 128])
    parser.add_argument("--mode", nargs="+", choices=["reference", "detail"], default=["detail"])
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(measure(args.parent[0], args.output, args.refine[0], args.mode[0])))
        return 0
    output: Path = args.output
    products = output.with_suffix("")
    if output.exists() or output.is_symlink() or products.exists() or products.is_symlink():
        parser.error("Choose a new report and sibling products directory.")
    if args.repeats < 1:
        parser.error("At least one repeat is required.")
    if any(path.resolve().is_relative_to(parent.resolve())
           for path in (output, products) for parent in args.parent):
        parser.error("Benchmark output must remain outside each immutable parent.")
    runtime = runtime_identity()
    runner_hash = file_sha256(Path(__file__))
    products.mkdir(parents=True)
    runs: list[dict[str, object]] = []
    for parent_index, parent in enumerate(args.parent):
        for mode in args.mode:
            for factor in args.refine:
                for repeat in range(args.repeats):
                    label = f"{parent_index}-{mode}-{factor}-{repeat}"
                    completed = subprocess.run(
                        [sys.executable, "-m", "benchmarks.regional_memory", "--worker",
                         "--parent", str(parent), "--refine", str(factor), "--mode", mode,
                         "--output", str(products / label)],
                        check=True, capture_output=True, text=True,
                    )
                    row: dict[str, object] = json.loads(completed.stdout)
                    if row["runtime"] != runtime:
                        raise RuntimeError("Worker runtime differs from the controller.")
                    runs.append({"parent": str(parent), "repeat": repeat, **row})
                    print(f"{label}: complete, cold/cache artifacts matched", flush=True)
    if runtime_identity() != runtime or file_sha256(Path(__file__)) != runner_hash:
        raise RuntimeError("Source changed; no report published.")
    with output.open("xb") as stream:
        stream.write(canonical_json({
            "runtime": runtime, "benchmark_sha256": runner_hash, "runs": runs,
            "limits": [
                "Fresh worker per parent/mode/refinement/repeat; parent builds excluded.",
                "Resident peaks include imports, native allocations and allocator retention.",
                "Reservations estimate owned work, not an OS memory limit or total RSS.",
                "Finite fixtures do not bound arbitrary geometry or unrelated work.",
            ],
        }))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
