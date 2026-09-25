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
        help="Open the world-map and terrain workbench.",
        description="Import a full world map with retained continents, or import closed SVG land "
                    "shapes and generate a local colour height map.",
    )
    startup = gui.add_mutually_exclusive_group()
    startup.add_argument("--project", type=Path, help="Open a saved local terrain project.")
    startup.add_argument("--world", type=Path, help="Open a portable .dmworld.json world project.")
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
    for command in ("sample-parent", "enrich-region"):
        experimental = command == "enrich-region"
        parent = terrain_commands.add_parser(
            command, help=("Generate experimental protected detail from a verified parent build."
                           if experimental else "Sample a verified completed parent build."),
        )
        parent.add_argument("parent", type=Path, help="Completed current terrain build directory.")
        parent.add_argument("--output", type=Path, required=True, help="New independent directory.")
        parent.add_argument("--bounds-km", type=float, nargs=4, required=True,
                            metavar=("X0", "Y0", "X1", "Y1"))
        parent.add_argument("--refine", type=int, required=True,
                            help="Power of two; experimental detail needs at least 8.")
        parent.add_argument("--memory-mib", type=int, default=None,
                            help="Regional admission budget in MiB (default 1024); estimated "
                                 "allocations, not a process memory limit.")
        if experimental:
            parent.add_argument("--experimental", action="store_true", required=True,
                                help="Acknowledge detail is experimental and hydrology unreviewed.")
            parent.add_argument("--amplitude-m", type=float, default=12.,
                                help="Maximum residual budget in metres, (0, 100], default 12.")
        parent.set_defaults(_handler=_run_parent_region, _experimental_detail=experimental)
    world = commands.add_parser(
        "world", help="Inspect retained world maps and continent ownership.")
    world.set_defaults(_command_parser=world)
    world_commands = world.add_subparsers(dest="world_command", title="world commands")
    inspect = world_commands.add_parser("inspect", help="Validate and summarize a saved world map.")
    inspect.add_argument("project", type=Path, help="Portable .dmworld.json project.")
    inspect.set_defaults(_handler=_run_world_inspect)
    context = world_commands.add_parser("context", help="Generate spherical geographic context.")
    context.add_argument("project", type=Path, help="Portable .dmworld.json project.")
    context.add_argument("--output", type=Path, required=True,
                         help="New context directory (must not exist).")
    context.add_argument("--latitude-cells", type=int, default=180,
                         help="Latitude rows, 4-360; twice as many longitude columns; default 180.")
    context.set_defaults(_handler=_run_world_context)
    verify_context = world_commands.add_parser(
        "inspect-context", help="Verify and inspect a completed geographic context.")
    verify_context.add_argument("context", type=Path, help="Context directory or context.json.")
    verify_context.set_defaults(_handler=_run_world_context_inspect)
    return parser


def _run_world_context_inspect(arguments: argparse.Namespace) -> int:
    from dmtools.terrain.adapters.build import runtime_identity
    from dmtools.terrain.application.world_context import open_context
    try:
        run = open_context(arguments.context)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Context inspection failed: {error}", file=sys.stderr)
        return 1
    result = run.context
    rows, columns = result.grid.shape
    print(f"Verified context: {result.world.project.name}; {columns} x {rows} cells")
    print(f"{len(result.water_bodies)} water regions; land {result.land_area_km2:,.0f} km²")
    print("Shared-edge water openings in km; no depth or transport capacity inferred.")
    print(f"Shore distance: {result.shore_sampling.sample_count:,} samples; "
          f"maximum overestimate {result.shore_sampling.max_error_km:.3f} km.")
    print("Water exposure in 8 look directions; mixed-cell support recorded. Not rainfall.")
    print("Producer matches current runtime." if run.runtime == runtime_identity()
          else "Saved producer differs; viewing is supported, regenerate before exporting.")
    return 0


def _run_world_context(arguments: argparse.Namespace) -> int:
    from dmtools.terrain.application.world_context import build_world_context
    from dmtools.terrain.domain.world_context import WorldContextSettings
    try:
        path = build_world_context(arguments.project, arguments.output,
                                   WorldContextSettings(arguments.latitude_cells))
    except (OSError, ValueError, RuntimeError) as error:
        print(f"World context failed: {error}", file=sys.stderr)
        return 1
    print(f"Geographic context complete: {path}")
    print("Geography, shoreline distance and water exposure; climate and terrain follow later.")
    return 0


def _run_world_inspect(arguments: argparse.Namespace) -> int:
    from dmtools.terrain.application.world import open_world
    try:
        result = open_world(arguments.project)
    except (OSError, ValueError) as error:
        print(f"World inspection failed: {error}", file=sys.stderr)
        return 1
    print(f"World: {result.project.name}")
    print(f"Spherical Plate Carree, radius {result.project.frame.radius_km:g} km")
    print(f"Continents: {len(result.continents)}; land coverage: {result.land_fraction:.2%}")
    for continent in result.continents:
        print(f"  {continent.name}: {continent.area_km2:,.0f} km²; "
              f"{continent.land_shapes} shapes, {continent.island_shapes} island shapes")
    print(f"Import adjustments: {len(result.adjustments)}; original SVG retained.")
    for adjustment in result.adjustments:
        print(f"  {adjustment.message} ({adjustment.area_source_units2:.6g} square source units)")
    print("Source map only: world climate and terrain generation are not implemented yet.")
    return 0


def _run_terrain_gui(arguments: argparse.Namespace) -> int:
    from dmtools.terrain.ui import run

    if arguments.world is not None:
        run(world=arguments.world)
    else:
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


def _run_parent_region(arguments: argparse.Namespace) -> int:
    from dmtools.terrain.application.parent_region import sample_parent_region
    from dmtools.terrain.application.region_memory import MIB, RegionalMemoryBudget
    from dmtools.terrain.domain.regional import RegionalDetailSettings

    try:
        x0, y0, x1, y1 = arguments.bounds_km
        detail = (RegionalDetailSettings(arguments.amplitude_m)
                  if arguments._experimental_detail else None)
        budget = (RegionalMemoryBudget(arguments.memory_mib * MIB)
                  if arguments.memory_mib is not None else None)
        manifest = sample_parent_region(
            arguments.parent, arguments.output, (x0, y0, x1, y1), arguments.refine,
            detail_settings=detail, memory_budget=budget,
        )
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Parent regional generation failed: {error}", file=sys.stderr)
        return 1
    print(f"Parent regional result complete: {manifest}")
    print("Experimental added detail; hydrology unreviewed, small rivers unavailable."
          if detail else "Verified parent field; no new detail or refined hydrology.")
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
