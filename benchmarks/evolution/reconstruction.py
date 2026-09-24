"""Compare reconstructions on verified frozen evolution/current-generator states.

Run with the base environment; no Landlab, SciPy or Matplotlib is required.
"""

import argparse
from pathlib import Path
from time import perf_counter
from typing import Any

from benchmarks.evolution.evidence import identity, write_json
from benchmarks.evolution.frozen import CHANNEL_AREA_M2, GRAPH_ROLE, discover, load_case
from benchmarks.evolution.paths import PROFILE_TOLERANCE_M, ChannelPaths, measure_paths
from benchmarks.evolution.surface import (
    FLOW_SURFACE_ID,
    FlowAlignedSurface,
    SurfaceTopologyConflict,
)
from benchmarks.evolution.surface_report import render_pair, write_index
from benchmarks.terrain import peak_resident_bytes

STATION_SPACINGS_M = (100.0, 25.0)


def summarize(measure: dict[str, Any]) -> dict[str, Any]:
    routes = measure["routes"]
    descending = [r for r in routes if r["nodally_nonascending"]]
    return {
        "path_identity": measure["path_identity"],
        "profile_sha256": measure["profile_sha256"],
        "sample_count": measure["sample_count"],
        "required_edges": measure["required_edge_count"],
        "unique_network": measure["unique_network"],
        "routes": len(routes),
        "unresolved_routes": sum(r["maximum_excursion_m"] > PROFILE_TOLERANCE_M for r in routes),
        "maximum_route_excursion_m": max((r["maximum_excursion_m"] for r in routes), default=0.0),
        "route_ascent_sum_m_shared_reaches_repeated": sum(r["uphill_ascent_m"] for r in routes),
        "nodally_nonascending_routes": len(descending),
        "unresolved_nodally_nonascending_routes": sum(
            r["maximum_excursion_m"] > PROFILE_TOLERANCE_M for r in descending
        ),
        "nodally_nonascending_route_ascent_m": sum(r["uphill_ascent_m"] for r in descending),
    }


def run(sources: list[Path], output: Path) -> dict[str, Any]:
    start = perf_counter()
    paths, omissions = discover(sources)
    cases = [load_case(path) for path in paths]
    original_identity = identity()
    output.mkdir(parents=True, exist_ok=False)
    rows: list[dict[str, Any]] = []
    try:
        maximum_m = max(1.0, *(float(case.ground_m.max()) for case in cases))
        for index, case in enumerate(cases):
            label = f"{case.result_path.parent.parent.name} / {case.record['id']}"
            folder = f"case-{index:02d}"
            directory = output / folder
            directory.mkdir()
            network = ChannelPaths(case.grid, case.receivers, case.required)
            result: dict[str, Any] = {
                "label": label,
                "folder": folder,
                "status": "compared",
                "model_id": FLOW_SURFACE_ID,
                "source_result": str(case.result_path),
                "source_hashes": case.hashes,
                "source_identity": case.record["identity"],
                "measurement_identity": original_identity,
                "graph_role": GRAPH_ROLE,
                "ground_role": "unchanged delivered Float32 nodes",
                "channel_area_threshold_m2": CHANNEL_AREA_M2,
                "grid": case.record["grid"],
                "selection": "all interior outgoing edges at threshold, connected to terminals",
                "path_identity": network.identity(),
                "required_edge_count": int(network.required.sum()),
                "required_head_count": int(network.heads().size),
                "summaries": {},
                "profiles": {},
                "seconds": {},
            }
            t = perf_counter()
            try:
                surface = FlowAlignedSurface(
                    case.grid, case.ground_m, case.receivers, case.required
                )
            except SurfaceTopologyConflict as exc:
                result.update(
                    status="rejected-topology", reason=str(exc), conflicting_cells=exc.cells
                )
                case.verify_unchanged()
                write_json(directory / "result.json", result)
                rows.append(
                    {k: v for k, v in result.items() if k not in ("profiles", "source_identity")}
                )
                continue
            result["seconds"]["surface_preparation"] = perf_counter() - t
            result["composition"] = surface.composition()
            for spacing in STATION_SPACINGS_M:
                key = f"{spacing:g}m"
                result["profiles"][key] = {}
                result["summaries"][key] = {}
                for name, sampler in (
                    ("bilinear", surface.bilinear),
                    ("flow_aligned", surface.sample),
                ):
                    t = perf_counter()
                    measured = measure_paths(network, sampler, case.ground_m, spacing)
                    result["seconds"][f"{name}_{key}"] = perf_counter() - t
                    result["profiles"][key][name] = measured
                    result["summaries"][key][name] = summarize(measured)
                pair = result["profiles"][key]
                if (
                    pair["bilinear"]["path_identity"] != pair["flow_aligned"]["path_identity"]
                    or pair["bilinear"]["sample_count"] != pair["flow_aligned"]["sample_count"]
                ):
                    raise ValueError(
                        "Control and candidate did not measure identical path coverage."
                    )
            t = perf_counter()
            render_pair(
                directory / "comparison.png",
                label,
                surface,
                network,
                result["profiles"]["25m"]["bilinear"],
                maximum_m,
            )
            result["seconds"]["render"] = perf_counter() - t
            case.verify_unchanged()
            write_json(directory / "result.json", result)
            rows.append(
                {k: v for k, v in result.items() if k not in ("profiles", "source_identity")}
            )
            print(f"Compared {label}", flush=True)
        for case in cases:
            case.verify_unchanged()
        if identity() != original_identity:
            raise ValueError("Source/runtime identity changed during the comparison.")
        result = {
            "status": "complete",
            "model_id": FLOW_SURFACE_ID,
            "identity": original_identity,
            "rows": rows,
            "source_workers_without_completed_states": omissions,
            "seconds": perf_counter() - start,
            "process_lifetime_peak_bytes": peak_resident_bytes(),
            "memory_scope": "whole serial comparison process including input arrays and rendering",
            "graph_role": GRAPH_ROLE,
            "station_spacings_m": STATION_SPACINGS_M,
            "acceptance": "research comparison only; not default terrain generation",
            "limits": [
                "D8 direction bias unchanged",
                "C0 surface has slope creases",
                "off-grid authored targets and cut budgets are not preserved",
                "nodal uphill and process-grid sensitivity require separate fixes",
                "no lake storage or physical water-validity claim",
                "unselected flow edges are not a reconstruction requirement",
            ],
        }
        write_index(output, rows, omissions)
        write_json(output / "comparison.json", result)
        return result
    except Exception as exc:
        write_json(
            output / "incomplete.json",
            {
                "status": "failed",
                "error": str(exc),
                "rows": rows,
                "source_workers_without_completed_states": omissions,
            },
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        nargs="+",
        required=True,
        help="Frozen cohort directories or completed worker directories",
    )
    parser.add_argument("--output", type=Path, required=True, help="New comparison directory")
    args = parser.parse_args()
    run(args.source, args.output)


if __name__ == "__main__":
    main()
