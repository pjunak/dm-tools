"""Render and export colour-graded terrain previews."""

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
from PIL import Image, PngImagePlugin

from dmtools.terrain.pipeline import GeneratedTerrain

_COLOUR_STOPS = np.array([0.0, 0.08, 0.30, 0.55, 0.75, 0.90, 1.0])
_COLOURS = np.array(
    [
        (214, 196, 145),
        (126, 155, 101),
        (80, 116, 78),
        (166, 135, 82),
        (111, 91, 69),
        (169, 164, 151),
        (244, 242, 235),
    ],
    dtype=np.float64,
)


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
    """Create an RGBA elevation tint with subtle fixed hillshade."""

    normalized = np.clip(
        np.nan_to_num(terrain.elevation_m, nan=0.0) / terrain.settings.maximum_elevation_m,
        0.0,
        1.0,
    )
    rgb = np.empty((*normalized.shape, 3), dtype=np.float64)
    for channel in range(3):
        rgb[..., channel] = np.interp(normalized, _COLOUR_STOPS, _COLOURS[:, channel])
    rgb *= _hillshade(terrain)[..., np.newaxis]
    rgb_uint8 = np.clip(rgb, 0, 255).astype(np.uint8)
    alpha = np.where(terrain.land_mask, 255, 0).astype(np.uint8)
    rgba = np.dstack((rgb_uint8, alpha))
    return Image.fromarray(rgba, mode="RGBA")


def save_height_map(image: Image.Image, terrain: GeneratedTerrain, destination: Path) -> None:
    """Save the rendered PNG with reproducibility settings in text metadata."""

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("dmtools.source", terrain.source_name)
    metadata.add_text("dmtools.settings", json.dumps(asdict(terrain.settings), sort_keys=True))
    metadata.add_text(
        "dmtools.note",
        "Colour relief preview; the authoritative in-memory values are Float32 metres.",
    )
    image.save(destination, format="PNG", pnginfo=metadata)
