"""Render and export colour-graded terrain previews."""

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
from PIL import Image, PngImagePlugin

from dmtools.terrain.adapters.palettes import ELEVATION_PALETTE_ID, OLERON_LAND_RGB
from dmtools.terrain.domain import ElevationPoint, TerrainBrushStroke, TerrainConstraint
from dmtools.terrain.pipeline import GeneratedTerrain

_COLOUR_STOPS = np.linspace(0.0, 1.0, len(OLERON_LAND_RGB))


def elevation_palette_rgb(normalized: np.ndarray) -> np.ndarray:
    """Map normalized elevations to the ordered Oleron land sequence in sRGB."""

    values = np.clip(np.asarray(normalized, dtype=np.float64), 0.0, 1.0)
    rgb = np.empty((*values.shape, 3), dtype=np.float64)
    for channel in range(3):
        rgb[..., channel] = np.interp(
            values,
            _COLOUR_STOPS,
            OLERON_LAND_RGB[:, channel],
        )
    return rgb


def elevation_legend_colours(sample_count: int = 7) -> tuple[str, ...]:
    """Return high-to-low hex samples matching the rendered elevation palette."""

    if sample_count < 2:
        raise ValueError("The elevation legend needs at least two colour samples.")
    normalized = np.linspace(1.0, 0.0, sample_count)
    rgb = np.rint(elevation_palette_rgb(normalized) * 255.0).astype(np.uint8)
    return tuple(f"#{red:02x}{green:02x}{blue:02x}" for red, green, blue in rgb)


def _hillshade(terrain: GeneratedTerrain) -> np.ndarray:
    elevation_km = np.nan_to_num(terrain.elevation_m, nan=0.0).astype(np.float64) / 1_000.0
    y_spacing = float(terrain.y_km[-1] - terrain.y_km[0]) / max(1, terrain.height - 1)
    x_spacing = float(terrain.x_km[-1] - terrain.x_km[0]) / max(1, terrain.width - 1)
    gradient_y, gradient_x = np.gradient(elevation_km, y_spacing, x_spacing)

    normal_x = -gradient_x
    normal_y = -gradient_y
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
    illumination = normal_x * light_x + normal_y * light_y + normal_z * light_z
    return np.clip(0.72 + 0.38 * illumination, 0.55, 1.08)


def render_height_map(terrain: GeneratedTerrain) -> Image.Image:
    """Create an ordered, colour-vision-deficiency-safe tint with fixed hillshade."""

    normalized = np.clip(
        np.nan_to_num(terrain.elevation_m, nan=0.0) / terrain.settings.maximum_elevation_m,
        0.0,
        1.0,
    )
    rgb = elevation_palette_rgb(normalized) * 255.0
    rgb *= _hillshade(terrain)[..., np.newaxis]
    rgb_uint8 = np.clip(rgb, 0, 255).astype(np.uint8)
    alpha = np.where(terrain.land_mask, 255, 0).astype(np.uint8)
    rgba = np.dstack((rgb_uint8, alpha))
    return Image.fromarray(rgba, mode="RGBA")


def _constraint_payload(constraint: TerrainConstraint) -> dict[str, object]:
    payload = asdict(constraint)
    if isinstance(constraint, ElevationPoint):
        payload["type"] = "elevation_point"
    elif isinstance(constraint, TerrainBrushStroke):
        payload["type"] = "terrain_brush"
    else:
        payload["type"] = constraint.kind
    return payload


def save_height_map(image: Image.Image, terrain: GeneratedTerrain, destination: Path) -> None:
    """Save the rendered PNG with reproducibility settings in text metadata."""

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("dmtools.source", terrain.source_name)
    metadata.add_text("dmtools.settings", json.dumps(asdict(terrain.settings), sort_keys=True))
    metadata.add_text("dmtools.colour_palette", ELEVATION_PALETTE_ID)
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
