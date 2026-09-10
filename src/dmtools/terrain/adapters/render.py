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
from dmtools.terrain.pipeline.diagnostics import (
    CUT_LIMIT,
    DEPRESSION,
    FINAL_ADJUSTMENT,
    REGION_TRANSITION,
)

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
    if style == "cartographic":
        rgb_uint8[np.isfinite(terrain.water.surface_m)] = (49, 133, 175)
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
        json.dumps(asdict(terrain.drainage.summary), sort_keys=True),
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


def render_basin_overlay(
    terrain: GeneratedTerrain, size: tuple[int, int] | None = None,
) -> Image.Image:
    """Tint depression extents and trace the top eight representative spill routes."""
    analysis, grid = terrain.drainage, terrain.routing_grid
    width, height = size or (grid.width, grid.height)
    labels = analysis.basin_labels
    rgba = np.zeros((*labels.shape, 4), dtype=np.uint8)
    rgba[labels > 0] = (165, 112, 230, 65)
    padded = np.pad(labels, 1)
    edge = np.zeros(labels.shape, dtype=np.bool_)
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        edge |= labels != padded[1 + dr:1 + dr + grid.height,
                                 1 + dc:1 + dc + grid.width]
    rgba[edge & (labels > 0)] = (200, 148, 255, 170)
    with Image.fromarray(rgba) as source:
        image = source.resize((width, height), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(image)
    x_scale = (width - 1) / max(1, grid.width - 1)
    y_scale = (height - 1) / max(1, grid.height - 1)

    def position(flat_index: int) -> tuple[float, float]:
        row, column = divmod(flat_index, grid.width)
        return column * x_scale, row * y_scale

    for basin in analysis.summary.basin_candidates[:8]:
        index = basin.deepest_flat_index
        path = [position(index)]
        while index != basin.outlet.spill_flat_index:
            index = int(analysis.receivers.flat[index])
            if index < 0:
                raise RuntimeError("The basin spill must lie on its conditioned route.")
            path.append(position(index))
        if len(path) > 1:
            draw.line(path, fill=(255, 216, 90, 240), width=1)
        x, y = path[0]
        draw.ellipse((x - 2, y - 2, x + 2, y + 2), outline="white", width=1)
        x, y = path[-1]
        draw.polygon(((x, y - 4), (x + 4, y), (x, y + 4), (x - 4, y)),
                     outline=(255, 216, 90, 255))
        text = f"B{basin.basin_id}"
        box = draw.textbbox((0, 0), text)
        label_width = box[2] - box[0]
        label_height = box[3] - box[1]
        tx = max(0., min(x + 6, width - label_width - 2))
        ty = max(0., min(y - 12, height - label_height - 4))
        draw.text((tx, ty), text, fill=(255, 234, 167, 255),
                  stroke_width=1, stroke_fill=(24, 33, 43, 255))
    return image


def render_drainage_review(terrain: GeneratedTerrain) -> Image.Image:
    """Show channel context and basin geometry on the same canonical nodes."""
    routing = terrain.routing
    mask = terrain.routing_land_mask
    width, height = terrain.routing_grid.width, terrain.routing_grid.height
    scale = max(1, 640 // max(width, height))
    map_width, map_height = width * scale, height * scale
    panel_width, panel_height = max(512, map_width), map_height + 32
    image = Image.new("RGB", (panel_width * 2 + 24, panel_height * 2 + 108), "#18212b")
    draw = ImageDraw.Draw(image)
    context = terrain.routing_conflicts
    summary = context.summary
    titles = ("Authored routing surface", "Finished terrain: uphill channels", "Conflict context",
              "Depression extents and spill candidates")
    fields = (routing.source_elevation_m, terrain.routing_final_elevation_m,
              terrain.routing_final_elevation_m, terrain.routing_final_elevation_m)
    for index, field in enumerate(fields):
        left = 8 + (index % 2) * (panel_width + 8)
        top = (index // 2) * panel_height
        draw.text((left, top + 8), titles[index], fill="white")
        grey = np.rint(45 + 150 * np.clip(field / terrain.settings.maximum_elevation_m, 0, 1))
        rgb = np.repeat(grey[..., None], 3, axis=2).astype(np.uint8)
        rgb[~mask] = (24, 33, 43)
        if index < 3:
            rgb[routing.channel_mask] = (45, 185, 255)
            if index:
                rgb[context.flags != 0] = (255, 95, 65)
        if index == 2:
            # Later colours win visually; the numeric archive retains every bit.
            for bit, colour in ((CUT_LIMIT, (240, 80, 190)),
                                (DEPRESSION, (170, 130, 255)),
                                (FINAL_ADJUSTMENT, (255, 150, 65)),
                                (REGION_TRANSITION, (255, 215, 80))):
                rgb[(context.flags & bit) != 0] = colour
        with Image.fromarray(rgb) as panel:
            resized = panel.resize((map_width, map_height), Image.Resampling.NEAREST)
            image.paste(resized, (left, top + 28))
            resized.close()
        if index == 3:
            with render_basin_overlay(terrain, (map_width, map_height)) as overlay:
                image.paste(overlay, (left, top + 28), overlay)
    lines = (
        "Blue: planned. Red: uphill. Context priority: yellow transition > orange final "
        "adjustment > purple depression > pink cut limit.",
        f"{summary.uphill_edge_count} uphill edges; overlapping contexts: "
        f"{summary.insufficient_cut_edge_count} cut limit, "
        f"{summary.final_adjustment_edge_count} final adjustment, "
        f"{summary.region_transition_edge_count} transition, "
        f"{summary.depression_edge_count} depression; {summary.unclassified_edge_count} other.",
        "Basins: purple extents; white deepest nodes; yellow routes and spill diamonds (top 8). "
        "IDs match diagnostics.json.",
        f"Shared review grid: {width} x {height}. Conditioned escape routes are candidates; "
        "water levels and authored lakes are not assigned.",
    )
    for row, line in enumerate(lines):
        draw.text((8, panel_height * 2 + 10 + 21 * row), line, fill="white")
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
    rises = terrain.routing_conflicts.rise_m
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
