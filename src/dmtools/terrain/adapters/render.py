"""Render and export colour-graded terrain previews."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw, PngImagePlugin

from dmtools.terrain.adapters.palettes import (
    CARTOGRAPHIC_RELIEF_MAX_ELEVATION_M,
    CARTOGRAPHIC_RELIEF_PALETTE_ID,
    CARTOGRAPHIC_RELIEF_RGB,
    CARTOGRAPHIC_RELIEF_STOPS,
    OLERON_LAND_RGB,
    SCIENTIFIC_ELEVATION_PALETTE_ID,
)
from dmtools.terrain.domain import (
    ElevationPoint,
    TerrainBrushStroke,
    TerrainConstraint,
    TerrainRegion,
)
from dmtools.terrain.pipeline import GeneratedTerrain
from dmtools.terrain.pipeline.hydrology import channel_edge_rise

type RenderStyle = Literal["cartographic", "scientific"]

_SCIENTIFIC_COLOUR_STOPS = np.linspace(0.0, 1.0, len(OLERON_LAND_RGB))


def _palette(style: RenderStyle) -> tuple[np.ndarray, np.ndarray, str]:
    if style == "cartographic":
        return (
            CARTOGRAPHIC_RELIEF_STOPS,
            CARTOGRAPHIC_RELIEF_RGB,
            CARTOGRAPHIC_RELIEF_PALETTE_ID,
        )
    return (
        _SCIENTIFIC_COLOUR_STOPS,
        OLERON_LAND_RGB,
        SCIENTIFIC_ELEVATION_PALETTE_ID,
    )


def elevation_palette_rgb(
    normalized: np.ndarray,
    *,
    style: RenderStyle = "cartographic",
) -> np.ndarray:
    """Map normalized elevations to the selected display palette in sRGB."""

    values = np.clip(np.asarray(normalized, dtype=np.float64), 0.0, 1.0)
    stops, colours, _palette_id = _palette(style)
    rgb = np.empty((*values.shape, 3), dtype=np.float64)
    for channel in range(3):
        rgb[..., channel] = np.interp(
            values,
            stops,
            colours[:, channel],
        )
    return rgb


def elevation_legend_colours(
    sample_count: int = 7,
    *,
    style: RenderStyle = "cartographic",
) -> tuple[str, ...]:
    """Return high-to-low hex samples matching the rendered elevation palette."""

    if sample_count < 2:
        raise ValueError("The elevation legend needs at least two colour samples.")
    normalized = np.linspace(1.0, 0.0, sample_count)
    rgb = np.rint(elevation_palette_rgb(normalized, style=style) * 255.0).astype(np.uint8)
    return tuple(f"#{red:02x}{green:02x}{blue:02x}" for red, green, blue in rgb)


def _illumination(terrain: GeneratedTerrain, vertical_exaggeration: float) -> np.ndarray:
    elevation_km = np.nan_to_num(terrain.elevation_m, nan=0.0).astype(np.float64) / 1_000.0
    grid = terrain.grid
    y_spacing = grid.y_spacing_km
    x_spacing = grid.x_spacing_km
    gradient_y, gradient_x = np.gradient(elevation_km, y_spacing, x_spacing)

    normal_x = -gradient_x * vertical_exaggeration
    normal_y = -gradient_y * vertical_exaggeration
    normal_z = np.ones_like(elevation_km)
    magnitude = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
    normal_x /= magnitude
    normal_y /= magnitude
    normal_z /= magnitude

    azimuth = np.deg2rad(315.0)
    altitude = np.deg2rad(42.0)
    light_x = np.cos(altitude) * np.sin(azimuth)
    light_y = -np.cos(altitude) * np.cos(azimuth)
    light_z = np.sin(altitude)
    return normal_x * light_x + normal_y * light_y + normal_z * light_z


def _hillshade(terrain: GeneratedTerrain, style: RenderStyle) -> np.ndarray:
    if style == "cartographic":
        illumination = _illumination(terrain, vertical_exaggeration=18.0)
        return np.clip(0.52 + 0.72 * illumination, 0.22, 1.20)
    illumination = _illumination(terrain, vertical_exaggeration=1.0)
    return np.clip(0.72 + 0.38 * illumination, 0.55, 1.08)


def render_height_map(
    terrain: GeneratedTerrain,
    *,
    style: RenderStyle = "cartographic",
) -> Image.Image:
    """Create a cartographic or scientific elevation tint with fixed hillshade."""

    colour_scale_maximum_m = (
        CARTOGRAPHIC_RELIEF_MAX_ELEVATION_M
        if style == "cartographic"
        else terrain.settings.maximum_elevation_m
    )
    normalized = np.clip(
        np.nan_to_num(terrain.elevation_m, nan=0.0) / colour_scale_maximum_m,
        0.0,
        1.0,
    )
    rgb = elevation_palette_rgb(normalized, style=style) * 255.0
    rgb *= _hillshade(terrain, style)[..., np.newaxis]
    rgb_uint8 = np.clip(rgb, 0, 255).astype(np.uint8)
    alpha = np.where(terrain.land_mask, 255, 0).astype(np.uint8)
    rgba = np.dstack((rgb_uint8, alpha))
    image = Image.fromarray(rgba, mode="RGBA")
    _stops, _colours, palette_id = _palette(style)
    image.info["dmtools.render_style"] = style
    image.info["dmtools.colour_palette"] = palette_id
    image.info["dmtools.colour_scale_maximum_m"] = f"{colour_scale_maximum_m:g}"
    return image


def _constraint_payload(constraint: TerrainConstraint) -> dict[str, object]:
    payload = asdict(constraint)
    if isinstance(constraint, ElevationPoint):
        payload["type"] = "elevation_point"
    elif isinstance(constraint, TerrainBrushStroke):
        payload["type"] = "terrain_brush"
    elif isinstance(constraint, TerrainRegion):
        payload["type"] = "terrain_region"
    else:
        payload["type"] = constraint.kind
    return payload


def save_height_map(image: Image.Image, terrain: GeneratedTerrain, destination: Path) -> None:
    """Save the rendered PNG with reproducibility settings in text metadata."""

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("dmtools.source", terrain.source_name)
    metadata.add_text("dmtools.settings", json.dumps(asdict(terrain.settings), sort_keys=True))
    metadata.add_text(
        "dmtools.drainage_diagnostics",
        json.dumps(asdict(terrain.drainage), sort_keys=True),
    )
    metadata.add_text(
        "dmtools.render_style",
        str(image.info.get("dmtools.render_style", "cartographic")),
    )
    metadata.add_text(
        "dmtools.colour_palette",
        str(image.info.get("dmtools.colour_palette", CARTOGRAPHIC_RELIEF_PALETTE_ID)),
    )
    metadata.add_text(
        "dmtools.colour_scale_maximum_m",
        str(
            image.info.get(
                "dmtools.colour_scale_maximum_m",
                f"{CARTOGRAPHIC_RELIEF_MAX_ELEVATION_M:g}",
            )
        ),
    )
    metadata.add_text(
        "dmtools.constraints",
        json.dumps(
            [_constraint_payload(constraint) for constraint in terrain.constraints],
            sort_keys=True,
        ),
    )
    metadata.add_text(
        "dmtools.note",
        "Colour relief preview; the authoritative in-memory values are Float32 metres.",
    )
    image.save(destination, format="PNG", pnginfo=metadata)


def render_drainage_review(terrain: GeneratedTerrain) -> Image.Image:
    """Compare the planning surface with final-field channel conflicts."""
    routing = terrain.routing
    mask = terrain.routing_land_mask
    width, height = terrain.routing_grid.width, terrain.routing_grid.height
    scale = max(1, 640 // width)
    panel_width, panel_height = width * scale, height * scale
    image = Image.new("RGB", (panel_width * 2 + 24, panel_height + 80), "#18212b")
    draw = ImageDraw.Draw(image)
    draw.text((8, 8), "Authored routing surface", fill="white")
    draw.text((panel_width + 16, 8), "Finished terrain: planned channels", fill="white")
    rises = channel_edge_rise(routing, terrain.routing_final_elevation_m)
    conflicts = rises > terrain.routing_agreement.elevation_tolerance_m
    for index, field in enumerate((routing.source_elevation_m, terrain.routing_final_elevation_m)):
        grey = np.rint(45 + 150 * np.clip(field / terrain.settings.maximum_elevation_m, 0, 1))
        rgb = np.repeat(grey[..., None], 3, axis=2).astype(np.uint8)
        rgb[~mask] = (24, 33, 43)
        rgb[routing.channel_mask] = (45, 185, 255)
        if index == 1:
            rgb[conflicts] = (255, 95, 65)
        with Image.fromarray(rgb) as panel:
            resized = panel.resize((panel_width, panel_height), Image.Resampling.NEAREST)
            image.paste(resized, (8 + index * (panel_width + 8), 28))
            resized.close()
    draw.text((8, panel_height + 36), "Blue: planned channels. Red: uphill on finished terrain.",
              fill="white")
    draw.text((8, panel_height + 54),
              f"Canonical grid: {width} x {height}. Review guidance; not validated rivers.",
              fill="white")
    return image


def render_drainage_overlay(
    terrain: GeneratedTerrain, size: tuple[int, int] | None = None,
) -> Image.Image:
    """Transparent planned D8 edges; red marks rises on the final field."""
    grid = terrain.routing_grid
    routing = terrain.routing
    width, height = size or (grid.width, grid.height)
    image = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(image)
    x_scale, y_scale = (width - 1) / (grid.width - 1), (height - 1) / (grid.height - 1)
    rises = channel_edge_rise(routing, terrain.routing_final_elevation_m)
    edges = routing.channel_mask & (routing.receivers >= 0)
    for uphill in (False, True):
        selected = edges & ((rises > terrain.routing_agreement.elevation_tolerance_m) == uphill)
        for row, column in np.argwhere(selected):
            target_row, target_column = divmod(int(routing.receivers[row, column]), grid.width)
            draw.line((int(column) * x_scale, int(row) * y_scale,
                       target_column * x_scale, target_row * y_scale),
                      width=1,
                      fill=(255, 95, 65, 255) if uphill else (45, 185, 255, 230))
    return image
