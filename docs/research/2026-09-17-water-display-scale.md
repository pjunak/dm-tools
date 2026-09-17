# Water display scale check — 2026-09-17

## Scope

Implement the author's scale-aware water requirement first for existing sampled
lake products, with small rivers gated on future local terrain/hydrology detail.
[ADR-0057](../adr/0057-display-water-at-the-appropriate-scale.md) owns the behavior
and remaining generation gates. This is display work on top of `0a47218`; it
changes cartographic PNGs and navigation, not terrain or numeric water.

## Behavioral evidence

`tests/test_water_display.py` covers separate wet pools, dry islands, corner
contacts, exact hidden/opaque thresholds and intermediate fading. Visibility
uses both axis scales and each whole pool's area before viewport clipping.
Equivalent replicated source masks give the same screen result; this is a
renderer check, not a claim that different generated grids resolve identical
shorelines. Source water, land masks, ground and routing remain unchanged.
Scientific ground stays identical with or without a water product. PNG metadata
records the policy, and export is independent of prior navigation.

Real Tk tests cover layer reuse while zooming, style switches, native-size
export and a stale reference after changing authored scale. The workbench's
scale readout now stays attached to the displayed generation and explicitly
separates display km/px from ground km/sample. A minimum-window check found
that a single longer navigation line clipped the Instructions control; ground
spacing now occupies a second line, with regression coverage for all navigation
controls remaining visible at 1040-by-700. Existing tests retain all-scale
drainage/catchment diagnostics.

## Public visual check

Generated the public square coastline at 1025 samples, seed 42, with three
non-overlapping closed square lake footprints. Centres and normalized widths:
`(0.33, 0.34, 0.18)`, `(0.55, 0.51, 0.012)`, `(0.5, 0.5, 0.003)`.
Each level equals the generation ceiling to expose the footprint sizes. These
are deliberately simple display fixtures, not examples of physical equilibrium.
No private map or authored campaign file was changed.

Inspected images read directly from the Tk preview image at Fit and 8x zoom,
and the scientific view. The smallest central pool is absent in the overview
and blue when zoomed; the large and medium pools remain visible when on screen.
The readout changes from 5.78 to 0.72 km/display pixel while ground stays at
3.91 km/sample. The close view is visibly magnified existing terrain. Square
shorelines are expected from these inputs; smooth or refined shorelines were
not generated. Diagnostics were exercised by tests; a separately rendered
review layer is not part of the captured base-image visual check.

## Local rendering cost

CPython 3.14.7, Windows 11 build 26200, existing project environment. Three
preparations per case, followed by three 800-by-800 render calls at each of Fit
and 10x display scale per preparation (18 viewport observations for each wet
case). No test suite ran concurrently. Results below are medians in milliseconds;
they measure the water layer only, excluding hillshade, Tk upload, total pan
latency and full-process peak memory.

| Source side | Mask | Pools | Prepare ms | Viewport ms | Persistent cache MiB |
|---|---|---:|---:|---:|---:|
| 1025 | dry | 0 | 0.30 | not needed | 0.00 |
| 1025 | large pool | 1 | 10.49 | 6.03 | 4.01 |
| 1025 | fragmented | 1,156 | 24.82 | 6.02 | 4.01 |
| 2049 | dry | 0 | 1.16 | not needed | 0.00 |
| 2049 | large pool | 1 | 35.35 | 6.13 | 16.02 |
| 2049 | fragmented | 4,624 | 94.89 | 6.14 | 16.02 |

The large mask occupies the central half of each axis with one 32-by-32 dry
island. Fragmented masks place 5-by-5 wet blocks every 30 source pixels starting
at index 10 and stopping 10 pixels before the boundary. Water is 2000 m, dry
samples NaN, and the land mask is all true. These deterministic masks isolate
classification and navigation cost without terrain generation noise.

Preparation uses the existing Rasterio/Shapely adapters. Runtime classification
is never repeated on a pan or wheel event; only the canvas-sized water image is
created. Persistent storage is four bytes per source pixel for a wet result and
zero for a dry one. This snapshot does not establish 4096-output, worst-case
one-pool-per-pixel, native peak-memory or whole-UI latency budgets. Polygonization
cost depends on boundary complexity, as documented by
[Rasterio](https://rasterio.readthedocs.io/en/stable/api/rasterio.features.html#rasterio.features.shapes).

Ignored local evidence is under `artifacts/water-display-2026-09-17/`:
`check.py`, `results.json`, overview/local/scientific map images and native export.
The retained script captures the workbench's own preview image only. The test
suite is the durable behavioral reproduction; timings above are observations,
not fragile timing assertions.

## Remaining work

The 9-to-36-pixel fade is an initial cartographic choice requiring broader visual
acceptance. It measures sampled footprint area, not surveyed lake area; a coarse
single wet sample can still cover a large screen area when magnified. Shoreline
refinement, actual local enrichment and a resolved small-river network remain
unimplemented. Planned river selection must preserve connected trunks, inherit
upstream context and only reveal smaller reaches after adequate local terrain
and hydrology resolution is available. Blue/red planned channels and teal outlet
paths remain complete diagnostics rather than a cartographic river layer.

## Final validation

The complete final regression suite passed: 873 tests in 263.92 seconds,
including 25 real-Tk workbench tests. Ruff and strict Pyright passed. All 609
local Markdown targets resolve and the diff has no whitespace errors.
The public base-image visual check and layer-only measurements above remain
separate from scientific river, private-map and large-project acceptance.
