# Basin extent and outlet research, 2026-09-10

**Status:** working research and implementation evidence. The accepted behavior
is [ADR-0033](../adr/0033-map-basin-spill-candidates.md).

## Evidence and choice

[Barnes, Callaghan and Wickert (2021), Fill-Spill-Merge](https://esurf.copernicus.org/articles/9/105/2021/)
models retained depressions using a nested hierarchy and available runoff.
Depressions can hold water or remain dry; connected fill regions alone cannot
represent every nested fill/spill/merge event. We therefore expose current
geometry and escape candidates without claiming a water simulation or lake level.

[Landlab's DepressionFinderAndRouter documentation](https://landlab.readthedocs.io/en/latest/generated/api/landlab.components.depression_finder.lake_mapper.html)
provides a mature reference for depression depth, mapped lake IDs, outlets,
areas and volumes. It motivates inspectable numeric products rather than marker
counts alone. This slice does not install Landlab, copy its implementation or
claim equivalent routing; optional-adapter benchmarking remains on TODO.

Our implementation inference is to use the existing conditioned D8 graph as a
reviewable first step. A component's deepest node provides a deterministic route;
its first extent exit and downstream terrain peak are distinct locations.
Retaining all receivers lets later work inspect alternative exits and compare
full breach length/depth. Neither a route peak nor local cut deficit supplies a
complete breach proposal, lake shoreline or nested basin relationship.

## Foundation improvement

The old aggregate basin check sampled 129 nodes on the longest axis, while
channel conflict review sampled 257. Their basin locations could disagree.
Both now use the same finished Float32 field on the existing 257-node grid.
The separate terrain evaluation, flood pass and redundant receiver computation
are removed. The DEM, source routing surface and planned channels are unaffected.

Non-land connected to a raster boundary is labelled exterior; enclosed gaps get
a distinct class. Both retain current boundary behavior. Topology at this grid
resolution cannot establish authored water intent or preserve every thin inlet.

## Follow-up priorities

1. Author explicit lake level, footprint, outlet and closed/dry-basin intent;
   report shoreline and anchor conflicts before applying an edit.
2. Compare retention, constrained breach and reroute proposals using complete
   downstream paths, cut depths/lengths, incision budgets and preserved anchors.
3. Add a real nested depression hierarchy when water-budget/fill-spill behavior
   needs it; do not relabel connected components as hierarchy nodes.
4. Compare the optional Landlab adapter on the analytical fixtures, including
   boundary definitions and resolution, before adopting an external solver.
5. Keep geometry-distance optimization separate from hydrology work; measure
   complex coasts before changing libraries or moving kernels to Rust.

## Validation and measurements

On Windows/CPython 3.14.7, all 255 tests, Ruff, strict Pyright and dependency
checks passed. The final review enlargement also passed all nine build tests.
The public four-region CLI build completed; the four-panel PNG was inspected.
Hidden Tk smoke covered result handling, both overlays and toggling review off.
This checks integration, not hands-on acceptance of editing a private map.

Isolated seed-42 runs at 768 output pixels, two fresh processes per case:

| Case | Previous median generation | Current median generation | Current basin candidates |
|---|---:|---:|---:|
| Authored | 2.331 s | 2.202 s | 768 |
| Archipelago | 2.624 s | 2.493 s | 297 |
| Regional | 1.610 s | 1.549 s | 112 |

Every prior numeric hash matched in all three cases: DEM, land mask, axes,
planned receivers/channels/incision/limits, finished routing field and conflict
flags. Delivered quality, routing agreement and conflict summaries also match.
New basin labels, conditioned receivers, boundary classes and candidate records
repeat exactly. Aggregate basin statistics intentionally change with the unified
higher-resolution grid and algorithm identity.

The new review costs did not regress these generation medians. Two repetitions
are evidence for this workload, not a statistically established speedup. These
measurements exclude build I/O, PNG encoding and drainage-review rendering.
Generation peak process memory was 105-130 MiB and products peak 130-146 MiB
for these 768-pixel runs. No new 2048/4096 stress or external-GIS validation was
performed in this slice.

Ignored local reports: `artifacts/channel-context-performance-20260910.json`
(before) and `artifacts/basin-outlet-performance-20260910.json` (after). The final
public build is `artifacts/basin-outlets-final-20260910/`; its default saved seed
produces 152 basin candidates, distinct from the seed-42 regional benchmark.
