"""Command-line entry point for DM Tools."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from dmtools import __version__


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dmtools",
        description="Local-first worldbuilding and tabletop utilities.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    commands = parser.add_subparsers(dest="tool", title="tools")
    terrain = commands.add_parser(
        "terrain",
        help="Build and inspect deterministic terrain projects.",
        description="Build and inspect deterministic terrain projects.",
    )
    terrain.set_defaults(_command_parser=terrain)
    terrain_commands = terrain.add_subparsers(dest="terrain_command", title="terrain commands")
    gui = terrain_commands.add_parser(
        "gui",
        help="Open the local land-geometry terrain workbench.",
        description="Import closed SVG land shapes and generate a colour height map.",
    )
    gui.add_argument("--project", type=Path, help="Open a saved terrain project on startup.")
    gui.set_defaults(_handler=_run_terrain_gui)
    build = terrain_commands.add_parser(
        "build",
        help="Build numeric terrain, previews and a provenance manifest from a saved project.",
    )
    build.add_argument("project", type=Path, help="Saved .dmterrain.json project.")
    build.add_argument(
        "--output", type=Path, required=True, help="New build directory (must not exist)."
    )
    build.set_defaults(_handler=_run_terrain_build)
    budget = terrain_commands.add_parser(
        "water-budget",
        help="Forecast shoreline and potential internal-network sampling before a build.",
        description=("Count water profile demand using canonical terrain, without raster export "
                     "or fine ground review. Internal networks are conditional; external outlet "
                     "routes and contacts are not included."),
    )
    budget.add_argument("project", type=Path, help="Saved .dmterrain.json project (read only).")
    budget.set_defaults(_handler=_run_terrain_water_budget)
    region = terrain_commands.add_parser(
        "sample-region",
        help="Sample a bounded region more densely from the unchanged terrain field.",
        description=("Sample a saved project's unchanged field on a finer regional grid. "
                     "Preserves global constraints and routing; "
                     "adds no detail bands or fine rivers."),
    )
    region.add_argument("project", type=Path, help="Saved .dmterrain.json project (read only).")
    region.add_argument("--output", type=Path, required=True,
                        help="New regional result directory (must not exist).")
    region.add_argument("--bounds-km", type=float, nargs=4, required=True,
                        metavar=("X0", "Y0", "X1", "Y1"),
                        help="Source-local bounds in kilometres, x right and y down.")
    region.add_argument("--refine", type=int, required=True,
                        help="Power-of-two subdivision of reference intervals; 1 through 65536.")
    region.set_defaults(_handler=_run_terrain_region)
    return parser


def _run_terrain_gui(arguments: argparse.Namespace) -> int:
    from dmtools.terrain.ui import run

    run(arguments.project)
    return 0


def _run_terrain_build(arguments: argparse.Namespace) -> int:
    from dmtools.terrain.application.build import build_terrain_project

    try:
        manifest = build_terrain_project(arguments.project, arguments.output)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Terrain build failed: {error}", file=sys.stderr)
        return 1
    print(f"Terrain build complete: {manifest}")
    return 0


def _run_terrain_region(arguments: argparse.Namespace) -> int:
    from dmtools.terrain.application.regional import sample_terrain_region

    try:
        x0, y0, x1, y1 = arguments.bounds_km
        manifest = sample_terrain_region(arguments.project, arguments.output,
                                         (x0, y0, x1, y1), arguments.refine)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Regional sampling failed: {error}", file=sys.stderr)
        return 1
    print(f"Regional samples complete: {manifest}")
    print("Denser unchanged-field samples; no new detail bands or refined hydrology.")
    return 0


def _run_terrain_water_budget(arguments: argparse.Namespace) -> int:
    from dmtools.terrain.application.water_budget import forecast_project_water_budget
    from dmtools.terrain.pipeline.water_budget import SamplingDemand

    try:
        result = forecast_project_water_budget(arguments.project)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Water budget forecast failed: {error}", file=sys.stderr)
        return 1
    budget = result.budget
    print(f"Water sampling budget: {result.project_path}")
    print(f"Canonical grid: {budget.grid_width} x {budget.grid_height}; "
          f"sampler: {budget.sampling_algorithm_id}")
    print(f"Limits: {budget.profile_sample_limit:,} stations/profile; "
          f"{budget.wet_network_sample_limit:,}/wet network; "
          f"{budget.dry_network_sample_limit:,}/dry network.")
    print("Counts include repeated stations. Budget failures are lower bounds.")
    print("Potential networks depend on outlet, shoreline and wet-connectivity checks. "
          "External routes/contacts and terrain clearance are not evaluated.")

    def show_demand(label: str, demand: SamplingDemand) -> None:
        count = f"{demand.requested_sample_count:,}"
        count = f"{count} (exact)" if demand.count_is_exact else f"at least {count}"
        status = ("within budget" if demand.status == "within_budget" else
                  f"EXCEEDS {demand.limiting_budget} budget")
        print(f"  {label}: {count} stations; {status}; "
              f"{demand.candidate_profile_count:,} profiles, "
              f"{demand.visited_profile_count:,} visited; "
              f"baseline {demand.baseline_sample_count:,}.")

    if not budget.basins:
        print("No authored basins; no shoreline or internal-network demand.")
    for basin in budget.basins:
        outlet = ", authored outlet" if basin.has_outlet else ""
        kind = basin.kind.replace("_", " ")
        print(f"Basin {basin.intent_id} ({kind}{outlet}): "
              f"{basin.footprint_cell_count:,} canonical nodes, {basin.wet_cell_count:,} wet.")
        if not basin.footprint_cell_count:
            print("  Footprint unresolved on the canonical grid; full review is required.")
        if basin.shoreline is not None:
            show_demand("Shoreline", basin.shoreline)
        if basin.wet_links is not None:
            show_demand("Potential wet network", basin.wet_links)
        if basin.dry_links is not None:
            show_demand("Potential dry network", basin.dry_links)
        if basin.wet_links is None:
            print("  No internal outlet network for this basin.")
    print(f"Project SHA-256: {result.project_sha256}")
    print(f"Coastline SHA-256: {result.coastline_sha256}")
    print(f"Generator source SHA-256: {result.runtime['package_source_sha256']}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    arguments = parser.parse_args(argv)

    handler = getattr(arguments, "_handler", None)
    if handler is not None:
        return handler(arguments)
    command_parser: argparse.ArgumentParser | None = getattr(arguments, "_command_parser", None)
    if command_parser is not None:
        command_parser.print_help()
    else:
        parser.print_help()
    return 0
