"""Standalone scientific figures and a local, self-contained comparison page."""

import html
import json
from importlib import import_module
from pathlib import Path
from typing import Any

import numpy as np


def render_report(output: Path, rows: list[dict[str, Any]]) -> None:
    mpl = import_module("matplotlib")
    mpl.use("Agg")
    plt = import_module("matplotlib.pyplot")
    colors = import_module("matplotlib.colors")
    successful = [r for r in rows if r["status"] == "complete"]
    if not successful:
        raise RuntimeError("No complete histories are available to render.")
    limit = max(float(r["final_metrics"]["height_max_m"]) for r in successful)
    light = colors.LightSource(azdeg=315., altdeg=45.)
    cmap = plt.get_cmap("terrain")
    columns = min(3, len(successful))
    count = (len(successful) + columns-1)//columns
    figure, axes = plt.subplots(count, columns, figsize=(6*columns, 4.6*count), squeeze=False)
    for axis in axes.ravel():
        axis.set_visible(False)
    cards: list[str] = []
    for axis, row in zip(axes.ravel(), successful, strict=False):
        directory = output / row["id"]
        with np.load(directory / "states.npz", allow_pickle=False) as archive:
            z = np.array(archive["delivered_elevation_m"], dtype=np.float64)
            snapshots = [np.array(archive[f"elevation_{i}_m"], dtype=np.float64)
                         for i in range(len(row["snapshots"]))]
            incision = (np.array(archive["incision_m"], dtype=np.float64)
                        if "incision_m" in archive else np.zeros_like(z))
            resistance = np.array(archive["resistance"], dtype=np.float64)
        grid = row["grid"]
        extent = (0., grid["width_m"]/1000., grid["height_m"]/1000., 0.)
        kwargs = {"cmap": cmap, "vmin": 0., "vmax": limit, "vert_exag": 1.,
                  "dx": grid["spacing_m"], "dy": grid["spacing_m"], "blend_mode": "soft"}
        rgb = light.shade(z, **kwargs)
        axis.set_visible(True)
        axis.imshow(rgb, extent=extent, origin="upper")
        title = f'{row["case"]} | seed {row["seed"]} | {grid["spacing_m"]:g} m'
        axis.set_title(title)
        axis.set_xlabel("x (km)")
        axis.set_ylabel("y (km)")
        detail, panels = plt.subplots(2, 3, figsize=(15, 8.4))
        for index, panel in enumerate(panels[0]):
            j = min(index, len(snapshots)-1)
            panel.imshow(light.shade(snapshots[j], **kwargs), extent=extent, origin="upper")
            panel.set_title(f'{row["snapshots"][j]["name"]} / '
                            f'{row["snapshots"][j]["time_years"]/1.e6:g} Myr')
        im = panels[1, 0].imshow(incision, extent=extent, origin="upper", cmap="magma", vmin=0.)
        panels[1, 0].set_title("Cumulative fluvial incision (m)")
        detail.colorbar(im, ax=panels[1, 0], shrink=.75)
        im = panels[1, 1].imshow(resistance, extent=extent, origin="upper", cmap="viridis",
                               vmin=1., vmax=4.)
        panels[1, 1].set_title("Relative resistance / evolved cases only")
        detail.colorbar(im, ax=panels[1, 1], shrink=.75)
        for s in row["snapshots"]:
            profile = s["main_profile"]
            panels[1, 2].plot(profile["distance_from_outlet_km"], profile["ground_m"],
                              label=s["name"])
        panels[1, 2].legend(fontsize=8)
        panels[1, 2].set_title("Largest outlet, largest-donor ground profile")
        panels[1, 2].set_xlabel("Distance upstream (km)")
        panels[1, 2].set_ylabel("Ground elevation (m)")
        detail.suptitle(title + " / research comparison")
        detail.tight_layout()
        detail.savefig(directory / "history.png", dpi=120)
        plt.close(detail)
        m = row["final_metrics"]
        cards.append(f'<article><h2>{html.escape(title)}</h2>'
                     f'<p>{row["solver_seconds"]:.2f} s solver; '
                     f'{row["accepted_steps"]} accepted steps; '
                     f'{row["rejected_trials"]} retries. '
                     f'Height {m["height_max_m"]:.1f} m; '
                     f'channel density {m["selected_channel_density_km_per_km2"]:.3f} km/km².</p>'
                     f'<a href="{row["id"]}/history.png"><img src="{row["id"]}/history.png" '
                     f'alt="Epoch terrain, cumulative incision and longitudinal profiles"></a>'
                     f'<details><summary>Measurements and identity</summary><pre>'
                     f'{html.escape(json.dumps(row, indent=2))}</pre></details></article>')
    figure.suptitle(f"Landscape evolution / common 0-{limit:.0f} m colour range"
                    " / physical hillshade")
    figure.tight_layout()
    figure.savefig(output / "comparison.png", dpi=120)
    plt.close(figure)
    failures = [f'<li>{html.escape(r["id"])}: {html.escape(r["error"])}</li>'
                for r in rows if r["status"] != "complete"]
    page = ("<!doctype html><html lang='en'><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>Landscape evolution comparison</title><style>"
            "body{font:16px/1.5 system-ui;margin:2rem auto;max-width:1500px;padding:0 1rem;"
            "background:#111b20;color:#e7eeef}img{max-width:100%;height:auto}"
            "article{margin:2rem 0;padding:1rem;background:#1b2930;border-radius:8px}"
            "a{color:#9cdbff}pre{overflow:auto;max-height:30rem;font-size:12px}"
            "</style><h1>Terrain through geological epochs</h1>"
            "<p>Public synthetic rectangle. Uplift → route runoff → implicit incision → "
            "conservative hillslope transport. Fixed perimeter, no coastal migration or mobile "
            "sediment. Research model, not a completed map build. Blue terrain tint denotes "
            "low elevation, not water.</p>"
            "<p>Evolution cases share starting relief and integrated uplift. The current generator "
            "uses a present-day ridge and plain: it is a visual reference, not equal physical "
            "forcing. All final DEMs are measured with the same routing policy and 25 km² channel "
            "threshold. D8 direction bias and bilinear reconstruction remain visible limitations. "
            "Profiles follow each snapshot's own largest outlet, "
            "not a fixed channel through time.</p>"
            + ("<p>Some requested runs are incomplete; this comparison is partial.</p><ul>"
               + "".join(failures) + "</ul>" if failures else "")
            + "<a href='comparison.png'><img src='comparison.png' "
            "alt='Final terrain comparison'></a>"
            + "".join(cards) + "</html>")
    (output / "index.html").write_text(page, encoding="utf-8")
