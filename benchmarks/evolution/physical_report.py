"""Actual-ground paired figures for the bounded physical path experiment."""

from html import escape
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from benchmarks.evolution.paths import ChannelPaths
from benchmarks.evolution.physical import PhysicalSurface, grid_points
from benchmarks.evolution.surface_report import render_panel


def render(output: Path, label: str, field: PhysicalSurface, maximum_m: float) -> None:
    reference = field.reference
    grid = reference.grid
    control = ChannelPaths(grid, reference.receivers, reference.required)
    moved = np.linalg.norm(field.paths.coordinates_m - grid_points(reference), axis=-1)
    row, col = np.unravel_index(int(moved.argmax()), moved.shape)
    size = min(8 * grid.spacing_m, grid.width_m, grid.height_m)
    x0 = min(max(0.0, (col - 4) * grid.spacing_m), grid.width_m - size)
    y0 = min(max(0.0, (row - 4) * grid.spacing_m), grid.height_m - size)
    bounds = (0.0, 0.0, grid.width_m, grid.height_m)
    crop = (x0, y0, x0 + size, y0 + size)
    samplers = ((reference.sample, control), (field.sample, field.paths))
    panels = [render_panel(s, p, bounds, maximum_m) for s, p in samplers]
    zoom = [render_panel(s, p, crop, maximum_m) for s, p in samplers]
    image = Image.new("RGB", (1280, panels[0].height + zoom[0].height + 170), "#fafafa")
    draw = ImageDraw.Draw(image)
    font, small = ImageFont.load_default(size=18), ImageFont.load_default(size=15)
    draw.text((20, 10), label, fill="#161b22", font=font)
    draw.text(
        (20, 38),
        f"Same height scale 0-{maximum_m:.0f} m; all required river edges; "
        "actual ground changes with geometry",
        fill="#161b22",
        font=small,
    )
    for index, title in enumerate(("Frozen triangle control", "Coupled physical paths and ground")):
        x = 20 + index * 640
        draw.text((x, 66), title, fill="#161b22", font=font)
        image.paste(panels[index], (x, 92))
        top = panels[0].height + 112
        draw.text((x, top), "Same crop at greatest path displacement", fill="#161b22", font=small)
        image.paste(zoom[index], (x, top + 28))
    image.save(output)


def write_index(output: Path, rows: list[dict[str, Any]]) -> None:
    content: list[str] = []
    for row in rows:
        folder = escape(row["folder"], quote=True)
        label = escape(row["label"])
        gates = escape(", ".join(row.get("failed_gates", [])) or "none at tested samples")
        content.append(
            f"<h2>{label}</h2><p>Failed measured gates: {gates}. "
            f"<a href='{folder}/result.json'>Complete evidence</a></p>"
            f"<img src='{folder}/comparison.png' loading='lazy'>"
        )
    (output / "index.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Physical river paths comparison</title>"
        "<style>body{font:16px system-ui;max-width:1300px;margin:24px auto;padding:0 16px}"
        "img{width:100%;height:auto}h2{margin-top:40px}</style>"
        "<h1>Physical river paths: experiment, not production acceptance</h1>"
        "<p>Every case retains the same graph, heads, junctions, terminals and bed node heights. "
        "Intermediate channel coordinates and the ground move together through a bounded mesh. "
        "This is geometric reconstruction, not erosion or a water simulation. "
        "Blue lines show rivers; terrain tint is elevation.</p>"
        "<p>Cut/fill checks compare with frozen bilinear ground at vertices and cell centres. "
        "Failed constraints are retained in the evidence; they are never silently relaxed. "
        "Passing finite samples does not prove whole-field feasibility. No authored anchors "
        "are present in this frozen cohort. Geographic divides and rerouted catchments are not "
        "preserved by the mapping.</p><p><a href='comparison.json'>Comparison summary</a></p>"
        + "".join(content),
        encoding="utf-8",
    )
