"""Command-line entry point for DM Tools."""

import argparse
from collections.abc import Sequence

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
        description="Terrain generation commands are the first planned DM Tools feature.",
    )
    terrain.set_defaults(_command_parser=terrain)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    arguments = parser.parse_args(argv)

    command_parser: argparse.ArgumentParser | None = getattr(arguments, "_command_parser", None)
    if command_parser is not None:
        command_parser.print_help()
    else:
        parser.print_help()
    return 0
