"""Pixel-faithful context previews; zoom never invents geographic resolution."""

from colorsys import hls_to_rgb
from typing import Literal

import numpy as np
from PIL import Image

from dmtools.terrain.adapters.world_render import OCEAN
from dmtools.terrain.domain.world_context import (
    MIXED_COAST,
    SPLIT_WATER,
    SUBCELL_LAND,
    SUBCELL_WATER,
)
from dmtools.terrain.pipeline.world_context import WorldContext
from dmtools.terrain.viewport import MapViewport

type ContextLayer = Literal["Land coverage", "Connected water", "Resolution support"]
CONTEXT_LAYERS: tuple[ContextLayer, ...] = (
    "Land coverage",
    "Connected water",
    "Resolution support",
)


def context_image(context: WorldContext, layer: ContextLayer) -> Image.Image:
    land = np.array((157, 177, 119), dtype=np.float64)
    water = np.array((24, 70, 89), dtype=np.float64)
    fraction = context.land_fraction[..., None]
    rgb = water * (1 - fraction) + land * fraction
    if layer == "Connected water":
        palette = np.zeros((len(context.water_bodies) + 1, 3), dtype=np.float64)
        palette[0] = water
        for body in context.water_bodies:
            palette[body.id] = (
                np.array(hls_to_rgb((0.54 + (body.id - 1) * 0.618034) % 1, 0.5, 0.5)) * 255
            )
        rgb = palette[context.water_body] * (1 - fraction) + land * fraction
    elif layer == "Resolution support":
        flags = context.support_flags
        rgb[(flags & MIXED_COAST) != 0] = (231, 181, 83)
        rgb[(flags & SUBCELL_LAND) != 0] = (221, 135, 82)
        rgb[(flags & SUBCELL_WATER) != 0] = (110, 200, 224)
        rgb[(flags & SPLIT_WATER) != 0] = (201, 130, 203)
    return Image.fromarray(np.rint(rgb).astype(np.uint8))


def render_world_context(
    context: WorldContext,
    viewport: MapViewport,
    size: tuple[int, int],
    layer: ContextLayer,
) -> Image.Image:
    if min(size) <= 0 or size[0] * size[1] > 16_777_216:
        raise ValueError("World preview must contain 1-16,777,216 pixels.")
    frame = context.grid.frame
    left, top, right, bottom = viewport.rect(size, (frame.width, frame.height))
    rows, columns = context.grid.shape
    sx, sy = columns / (right - left), rows / (bottom - top)
    with context_image(context, layer) as source:
        return source.transform(
            size,
            Image.Transform.AFFINE,
            (sx, 0, -left * sx, 0, sy, -top * sy),
            resample=Image.Resampling.NEAREST,
            fillcolor=OCEAN,
        )
