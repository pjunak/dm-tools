"""Render just the visible portion of a raster, regardless of magnification."""

from PIL import Image


def render_viewport(
    image: Image.Image,
    rect: tuple[float, float, float, float],
    size: tuple[int, int],
) -> Image.Image:
    left, top, right, bottom = rect
    sx, sy = image.width / (right - left), image.height / (bottom - top)
    return image.transform(
        size, Image.Transform.AFFINE, (sx, 0., -left * sx, 0., sy, -top * sy),
        resample=Image.Resampling.BILINEAR,
        fillcolor=(0, 0, 0, 0) if image.mode == "RGBA" else (16, 25, 27),
    )
