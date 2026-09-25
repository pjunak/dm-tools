"""Portable context products with a last-published, hash-addressed manifest."""

import os
from collections.abc import Callable
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

import numpy as np

from dmtools.terrain.adapters.build import canonical_json, file_sha256
from dmtools.terrain.adapters.world_context_render import CONTEXT_LAYERS, context_image
from dmtools.terrain.adapters.world_project import world_project_document
from dmtools.terrain.adapters.world_svg import WORLD_IMPORTER
from dmtools.terrain.domain.world import WORLD_PREPARATION
from dmtools.terrain.domain.world_context import WORLD_CONTEXT_ALGORITHM
from dmtools.terrain.pipeline.world_context import WorldContext

CONTEXT_SCHEMA = "dmtools.world-context"
CONTEXT_VERSION = 1


def context_input_sha256(context: WorldContext) -> str:
    return sha256(
        canonical_json(
            {
                "world": world_project_document(context.world.project),
                "settings": asdict(context.grid.settings),
                "algorithm": WORLD_CONTEXT_ALGORITHM,
            }
        )
    ).hexdigest()


def write_world_context(
    context: WorldContext,
    runtime: dict[str, object],
    destination: Path,
    *,
    verify: Callable[[], None],
) -> Path:
    """Reserve a new directory. A failed/cancelled export has no completion manifest."""
    verify()
    target = destination.absolute()
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"Context destination already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir()
    snapshot = canonical_json(world_project_document(context.world.project))
    (target / "world.dmworld.json").write_bytes(snapshot)
    verify()
    rows, columns = context.grid.shape
    np.savez_compressed(
        target / "geography.npz",
        land_fraction=context.land_fraction,
        water_body=context.water_body,
        support_flags=context.support_flags,
        cell_area_km2=context.cell_area_km2,
        latitude_deg=np.array([context.grid.latitude_deg(r) for r in range(rows)]),
        longitude_deg=np.array([context.grid.longitude_deg(c) for c in range(columns)]),
    )
    names = ["world.dmworld.json", "geography.npz"]
    for layer, name in zip(CONTEXT_LAYERS, ("land.png", "water.png", "support.png"), strict=True):
        verify()
        with context_image(context, layer) as image:
            image.save(target / name)
        names.append(name)
    outputs = {
        name: {"sha256": file_sha256(target / name), "bytes": (target / name).stat().st_size}
        for name in names
    }
    frame = context.grid.frame
    manifest: dict[str, object] = {
        "schema": CONTEXT_SCHEMA,
        "version": CONTEXT_VERSION,
        "algorithm": WORLD_CONTEXT_ALGORITHM,
        "importer": WORLD_IMPORTER,
        "preparation": WORLD_PREPARATION,
        "input_sha256": context_input_sha256(context),
        "runtime": runtime,
        "settings": asdict(context.grid.settings),
        "grid": {
            "rows": rows,
            "columns": columns,
            "registration": "cell-centre",
            "projection": "spherical-plate-carree",
            "longitude_periodic": True,
            "pole_policy": "finite-edge-gateways; no point-contact water links",
            "angular_step_deg": context.grid.angular_step_deg,
            "north_south_spacing_km": context.grid.north_south_spacing_km,
            "frame": asdict(frame),
        },
        "areas_km2": {
            "sphere": frame.surface_area_km2,
            "land": context.land_area_km2,
            "water": sum(b.area_km2 for b in context.water_bodies),
            "land_conservation_error": context.area_error_km2,
        },
        "support": {
            "mixed_cells": context.mixed_cells,
            "split_water_cells": context.split_water_cells,
            "land_without_centre": context.subcell_land_cells,
            "water_without_centre": context.subcell_water_cells,
        },
        "water_bodies": [asdict(body) for body in context.water_bodies],
        "outputs": outputs,
    }
    verify()
    pending = target / "manifest.pending"
    with pending.open("xb") as stream:
        stream.write(canonical_json(manifest))
        stream.flush()
        os.fsync(stream.fileno())
    verify()
    complete = target / "context.json"
    pending.replace(complete)
    return complete
