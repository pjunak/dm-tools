# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false
"""Screen-scale visibility of sampled lake pools, independent of hydrology."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from PIL import Image
from rasterio.features import rasterize, shapes
from shapely.geometry import shape

from dmtools.terrain.adapters.viewport import render_viewport

WATER_DISPLAY_ID = "sampled-pool-screen-area@1"
WATER_COLOUR = (49, 133, 175)
# Cartographic thresholds in output pixels, not physical water-size estimates.
HIDDEN_AREA_PX2 = 9.0
OPAQUE_AREA_PX2 = 36.0


@dataclass(frozen=True, slots=True)
class WaterDisplay:
    """Cached whole-pool areas in source pixels; never cropped before classification."""

    pool_area: Image.Image

    def render(
        self,
        rect: tuple[float, float, float, float],
        size: tuple[int, int],
    ) -> Image.Image:
        """Allocate only the viewport, with visibility independent of pan position."""
        left, top, right, bottom = rect
        pixel_area_scale = ((right - left) / self.pool_area.width
                            * (bottom - top) / self.pool_area.height)
        # Areas are categories: interpolating them would blend adjacent pools or
        # fabricate partially wet source samples at a dry shoreline.
        with render_viewport(self.pool_area, rect, size,
                             resample=Image.Resampling.NEAREST) as areas:
            area_px2 = np.asarray(areas) * pixel_area_scale
            fade = np.clip((area_px2 - HIDDEN_AREA_PX2)
                           / (OPAQUE_AREA_PX2 - HIDDEN_AREA_PX2), 0., 1.)
            alpha = np.rint(255 * fade * fade * (3 - 2 * fade)).astype(np.uint8)
        rgba = np.empty((size[1], size[0], 4), dtype=np.uint8)
        rgba[..., :3] = WATER_COLOUR
        rgba[..., 3] = alpha
        return Image.fromarray(rgba)


def prepare_water_display(
    surface_m: NDArray[np.float32], land_mask: NDArray[np.bool_],
) -> WaterDisplay | None:
    """Classify connected wet pixels once per result, not on wheel/pan events.

    Four-neighbour connectivity is a display convention, not a claim of water
    exchange: corner contact does not combine the visibility of separate pools.
    Rasterio and Shapely are existing adapters, used only on a binary wet mask.
    """
    if surface_m.ndim != 2 or surface_m.shape != land_mask.shape:
        raise ValueError("Water display requires matching two-dimensional water and land arrays.")
    wet = np.isfinite(surface_m) & land_mask
    if not np.any(wet):
        return None
    components = [(polygon, shape(polygon).area)
                  for polygon, _value in shapes(wet.astype(np.uint8), mask=wet, connectivity=4)]
    areas = rasterize(components, out_shape=wet.shape, fill=0, dtype="float32",
                      skip_invalid=False)
    return WaterDisplay(Image.fromarray(areas))
