"""File-format and rendering adapters for terrain generation."""

from dmtools.terrain.adapters.project import (
    PROJECT_EXTENSION,
    LoadedTerrainProject,
    TerrainProjectInputError,
    load_terrain_project,
    save_terrain_project,
)
from dmtools.terrain.adapters.render import render_height_map, save_height_map
from dmtools.terrain.adapters.svg import (
    CoastlineInputError,
    CoastlineSource,
    load_svg_coastline,
    load_svg_coastline_source,
)

__all__ = [
    "PROJECT_EXTENSION",
    "CoastlineInputError",
    "CoastlineSource",
    "LoadedTerrainProject",
    "TerrainProjectInputError",
    "load_svg_coastline",
    "load_svg_coastline_source",
    "load_terrain_project",
    "render_height_map",
    "save_height_map",
    "save_terrain_project",
]
