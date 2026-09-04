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
    return parser


def _run_terrain_gui(_arguments: argparse.Namespace) -> int:
    from dmtools.terrain.ui import run

    run()
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
