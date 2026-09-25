"""Generate geographic context from an immutable source snapshot; export separately."""

from dataclasses import dataclass
from pathlib import Path

from dmtools.terrain.adapters.build import file_sha256, runtime_identity
from dmtools.terrain.adapters.world_context import write_world_context
from dmtools.terrain.adapters.world_svg import parse_world_svg
from dmtools.terrain.application.world import open_world
from dmtools.terrain.domain.world import WorldProject
from dmtools.terrain.domain.world_context import WorldContextSettings
from dmtools.terrain.pipeline.control import CancellationToken, ProgressCallback, check_cancelled
from dmtools.terrain.pipeline.world import prepare_world_map
from dmtools.terrain.pipeline.world_context import WorldContext, generate_world_context


@dataclass(frozen=True, slots=True)
class WorldContextRun:
    context: WorldContext
    runtime: dict[str, object]


def generate_context(
    project: WorldProject,
    settings: WorldContextSettings | None = None,
    progress: ProgressCallback | None = None,
    *,
    cancellation: CancellationToken | None = None,
) -> WorldContextRun:
    check_cancelled(cancellation)
    runtime = runtime_identity()
    if parse_world_svg(project.source.svg, project.source.name) != project.source:
        raise ValueError("World source snapshot and geometry disagree; import again.")
    context = generate_world_context(
        prepare_world_map(project), settings, progress, cancellation=cancellation
    )
    if runtime_identity() != runtime:
        raise ValueError("Software changed during context generation; generate again.")
    check_cancelled(cancellation)
    return WorldContextRun(context, runtime)


def export_context(
    run: WorldContextRun,
    destination: Path,
    *,
    cancellation: CancellationToken | None = None,
) -> Path:
    def verify() -> None:
        check_cancelled(cancellation)
        if runtime_identity() != run.runtime:
            raise ValueError("Software changed after context generation; generate again.")

    verify()
    return write_world_context(run.context, run.runtime, destination, verify=verify)


def build_world_context(
    source: Path,
    destination: Path,
    settings: WorldContextSettings | None = None,
    *,
    cancellation: CancellationToken | None = None,
) -> Path:
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Context destination already exists: {destination}")
    check_cancelled(cancellation)
    source_hash = file_sha256(source)
    run = generate_context(open_world(source).project, settings, cancellation=cancellation)

    def verify() -> None:
        check_cancelled(cancellation)
        if file_sha256(source) != source_hash:
            raise ValueError("World project changed during context generation; start again.")
        if runtime_identity() != run.runtime:
            raise ValueError("Software changed during context generation; start again.")

    verify()
    return write_world_context(run.context, run.runtime, destination, verify=verify)
