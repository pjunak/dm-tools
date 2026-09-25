"""Validate, inspect and save authored geology without mutating a world or build."""

from dataclasses import dataclass, replace
from pathlib import Path

from dmtools.terrain.adapters.world_geology import read_geology, world_fingerprint, write_geology
from dmtools.terrain.adapters.world_svg import parse_world_svg
from dmtools.terrain.pipeline.control import CancellationToken, check_cancelled
from dmtools.terrain.pipeline.world import WorldMap, prepare_world_map
from dmtools.terrain.pipeline.world_geology import GeologyCoverage, resolve_geology


@dataclass(frozen=True, slots=True)
class GeologyFile:
    coverage: GeologyCoverage
    path: Path
    sha256: str


def open_geology(
    path: Path,
    world: WorldMap | None = None,
    cancellation: CancellationToken | None = None,
) -> GeologyFile:
    recipe, digest = read_geology(path)
    check_cancelled(cancellation)
    if world is None:
        world = prepare_world_map(recipe.world)
    elif world_fingerprint(world.project) != world_fingerprint(recipe.world):
        raise ValueError(
            "Recipe uses a different world source, frame or ownership; open its world."
        )
    recipe = replace(recipe, world=world.project)
    return GeologyFile(resolve_geology(world, recipe, cancellation), path, digest)


def save_geology(
    coverage: GeologyCoverage,
    path: Path,
    expected_hash: str | None = None,
) -> GeologyFile:
    recipe = coverage.recipe
    if parse_world_svg(recipe.world.source.svg, recipe.world.source.name) != recipe.world.source:
        raise ValueError("Geology source snapshot and retained geometry disagree; import again.")
    verified = resolve_geology(prepare_world_map(recipe.world), recipe)
    return GeologyFile(verified, path, write_geology(recipe, path, expected_hash))
