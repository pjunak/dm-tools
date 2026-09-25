"""Actual ground and independently rerouted head traces for the network fixture."""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageDraw, ImageFont

from benchmarks.evolution.constrained import FittedSurface
from benchmarks.evolution.network_fixture import NetworkFixture
from benchmarks.evolution.paths import Sampler
from benchmarks.evolution.surface_report import render_panel
from benchmarks.evolution.valley_support import ValleySupport


def render(output: Path, f: NetworkFixture, samplers: dict[str, Sampler], label: str) -> None:
    grid = f.source.grid
    bounds = (0.0, 0.0, grid.width_m, grid.height_m)
    panels = [
        (name, render_panel(sampler, f.network, bounds, 1000.0))
        for name, sampler in samplers.items()
    ]
    height = max(p.height for _, p in panels)
    image = Image.new("RGB", (1280, 100 + 2 * (height + 45)), "#fafafa")
    draw, font = ImageDraw.Draw(image), ImageFont.load_default(size=18)
    draw.text((20, 10), label, fill="#161b22", font=font)
    draw.text(
        (20, 38),
        "Same physical river guides; actual ground; shared 0-1000 m scale",
        fill="#161b22",
        font=ImageFont.load_default(size=16),
    )
    for i, (name, panel) in enumerate(panels):
        x, y = 20 + (i % 2) * 640, 75 + (i // 2) * (height + 45)
        draw.text((x, y), name, fill="#161b22", font=font)
        image.paste(panel, (x, y + 30))
    image.save(output)


def render_routes(
    output: Path,
    f: NetworkFixture,
    fields: dict[str, tuple[FittedSurface, NDArray[np.int64]]],
    label: str,
) -> None:
    panels: list[tuple[str, Image.Image]] = []
    bounds = (0.0, 0.0, f.source.grid.width_m, f.source.grid.height_m)
    for name, (field, receivers) in fields.items():
        panel = render_panel(field.sample, f.network, bounds, 1000.0)
        draw = ImageDraw.Draw(panel)
        scale = (panel.width - 1) / field.grid.width_m
        for head in f.network.heads():
            col, row = np.rint(f.network.coordinates_m[head] / field.grid.spacing_m).astype(int)
            node = int(row * field.grid.shape[1] + col)
            path = [node]
            while receivers.flat[node] >= 0:
                node = int(receivers.flat[node])
                path.append(node)
                if len(path) > receivers.size:
                    raise ValueError("Cannot render a cyclic routing graph.")
            y, x = np.divmod(path, field.grid.shape[1])
            points = list(
                zip(x * field.grid.spacing_m * scale, y * field.grid.spacing_m * scale, strict=True)
            )
            if len(points) > 1:
                draw.line(points, fill="#222222", width=4)
                draw.line(points, fill="#ffff66", width=2)
            px, py = points[-1]
            draw.line((px - 4, py - 4, px + 4, py + 4), fill="#e80046", width=2)
            draw.line((px + 4, py - 4, px - 4, py + 4), fill="#e80046", width=2)
        panels.append((name, panel))
    image = Image.new("RGB", (1280, 110 + max(p.height for _, p in panels)), "#fafafa")
    draw = ImageDraw.Draw(image)
    draw.text(
        (20, 10),
        label + " / actual routing at common 125 m spacing",
        fill="#161b22",
        font=ImageFont.load_default(size=18),
    )
    draw.text(
        (20, 40),
        "Blue: fixed guides. Yellow: raw ground routes from four heads. Red: stops.",
        fill="#161b22",
        font=ImageFont.load_default(size=16),
    )
    for i, (name, panel) in enumerate(panels):
        x = 20 + i * 640
        draw.text((x, 70), name, fill="#161b22", font=ImageFont.load_default(size=18))
        image.paste(panel, (x, 100))
    image.save(output)


def render_banks(
    output: Path,
    f: NetworkFixture,
    support: ValleySupport,
    fields: dict[str, FittedSurface],
    conflicts: list[int],
    label: str,
) -> None:
    bounds = (0.0, 0.0, f.source.grid.width_m, f.source.grid.height_m)
    panels: list[tuple[str, Image.Image]] = []
    for name, field in fields.items():
        panel = render_panel(field.sample, f.network, bounds, 1000.0)
        draw = ImageDraw.Draw(panel)
        scale = (panel.width - 1) / field.grid.width_m
        for i, (bank, bed) in enumerate(zip(support.banks_m, support.beds_m, strict=True)):
            colour = "#da143e" if i in conflicts else "#77939b"
            points = [tuple(float(v) for v in point * scale) for point in (bank, bed)]
            draw.line(points, fill=colour, width=2 if i in conflicts else 1)
            if i in conflicts:
                x, y = points[0]
                draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=colour)
        panels.append((name, panel))
    height = max(panel.height for _, panel in panels)
    image = Image.new("RGB", (1280, height + 115), "#fafafa")
    draw = ImageDraw.Draw(image)
    draw.text((20, 10), label, fill="#161b22", font=ImageFont.load_default(size=18))
    draw.text(
        (20, 40),
        "Grey: bank-to-nearest-reach support. Red: reported conflict probes.",
        fill="#161b22",
        font=ImageFont.load_default(size=16),
    )
    for i, (name, panel) in enumerate(panels):
        x = 20 + 640 * i
        draw.text((x, 75), name, fill="#161b22", font=ImageFont.load_default(size=16))
        image.paste(panel, (x, 100))
    image.save(output)
