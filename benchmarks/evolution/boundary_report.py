"""Bank witnesses with matched coordinates and labelled physical scales."""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageDraw, ImageFont

from benchmarks.evolution.valley_support import ValleySupport


def render_sections(
    output: Path,
    support: ValleySupport,
    indices: list[int],
    profiles: dict[str, NDArray[np.float32]],
    *,
    title: str = "Matched bank sections: control-worst head and mouth witnesses",
) -> None:
    image = Image.new("RGB", (1100, 90 + 280 * len(indices)), "#fafafa")
    draw = ImageDraw.Draw(image)
    font, small = ImageFont.load_default(size=18), ImageFont.load_default(size=15)
    draw.text((20, 12), title, "#161b22", font)
    palette = ("#b34515", "#0669a3", "#626a72")
    for j, name in enumerate(profiles):
        draw.text((20 + 350 * j, 46), name, palette[j], small)
    for i, index in enumerate(indices):
        top = 90 + 280 * i
        draw.text(
            (20, top),
            f"Support {index} / reach {support.bed_edges[index]} / "
            f"bank to bed: {support.distances_m[index]:.1f} m",
            "#161b22",
            font,
        )
        low = min(float(a[index].min()) for a in profiles.values())
        high = max(float(a[index].max()) for a in profiles.values())
        high = max(high, low + 0.001)
        draw.rectangle((90, top + 36, 1060, top + 206), outline="#999999")
        for j, values in enumerate(profiles.values()):
            line = values[index].astype(np.float64)
            points = list(
                zip(
                    np.linspace(90, 1060, len(line)),
                    top + 206 - (line - low) / (high - low) * 170,
                    strict=True,
                )
            )
            draw.line(points, fill=palette[j], width=2)
        draw.text((12, top + 32), f"{high:.3f} m", "#161b22", small)
        draw.text((12, top + 190), f"{low:.3f} m", "#161b22", small)
        draw.text((90, top + 216), "0 m (bank)", "#161b22", small)
        draw.text((925, top + 216), f"{support.distances_m[index]:.1f} m (bed)", "#161b22", small)
    image.save(output)
