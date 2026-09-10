# Authored water implementation and measurements, 2026-09-10

**Status:** implementation evidence. [ADR-0034](../adr/0034-author-lakes-and-dry-basins.md)
and the [water contract](../terrain-water.md) define current behavior.

## Delivered

- Lake and dry-basin polygon tools, saved water-level/outlet controls and readable
  per-area conflict details. An optional lake outlet is the first drawn vertex.
- Automatic-cut and automatic-detail protection on both the canonical grid and
  continuous field; authored terrain constraints retain their authority.
- Separate Float32 water surfaces/depths and UInt32 intent IDs in build v7.
  Scientific relief and GeoTIFF retain ground elevations beneath lake water.
- Project v5, current public examples and schema validation; old project/build
  schemas are removed, with no compatibility loader or migration.
- A public lake/dry-basin example and a water benchmark case. No new dependency
  or external solver was needed; the pipeline remains Python/NumPy/Shapely.

The earlier [depression research](2026-09-10-depressions-and-channel-conflicts.md)
and [outlet work](2026-09-10-basin-outlet-topology.md) support separating authored
retention from diagnostic filling. This slice implements that boundary rather
than a water-budget or nested fill/spill solver.

## Validation

All 269 repository tests pass. After the final toolbar/example adjustments,
all 32 water/build/project tests pass. Ruff, strict Pyright and dependency checks
pass. The public CLI build completed and cartographic output was inspected.

Hidden Tk smoke exercised lake and dry-basin polygon completion, optional outlet,
undo, saved controls, project reload, rendered overlays and Basin details. The
condensed toolbar requests 674 px within the preview pane. This is programmatic
integration coverage, not hands-on acceptance of a private campaign map.

The final public example has 1,550 wet canonical samples. It has no sampled low
boundary, exposed-anchor, disconnected-water or outlet-height finding. Its lake
and dry basin both have planned outflow conflicts; those are visible and remain
unreconciled. Authored-cut protection is already effective.

## Performance and reproducibility

CPython 3.14.7 on Windows; seed 42. Runs use fresh subprocesses, and the report
checks unchanged source/runtime and repeatable numeric products.

The new water case measured 1.879 s median generation at 768 pixels (two runs),
and 10.570 s at 2048 pixels (one run). Generation process peaks were 136 MiB and
259 MiB; peaks including quality/render work were 136 MiB and 373 MiB.
These timings exclude export I/O, PNG encoding and drainage-review rendering.
No 4096-pixel stress test was performed in this slice.

Earlier checkpoints were faster even for unchanged cases. A controlled source
comparison used commit `07c55f4` and the current implementation, with identical
fixture hashes and exact public SVG bytes. Both ran in the same Python environment:

| Case, 768 pixels | Prior source runs | Current source runs |
|---|---|---|
| Authored | 8.774 / 3.748 s | 2.870 / 2.789 s |
| Archipelago | 3.236 / 3.080 s | 2.756 / 2.718 s |
| Regional | 2.019 / 1.794 s | 1.758 / 1.789 s |

The large baseline variation prevents a reliable speedup or regression claim.
Do not turn these figures into performance guarantees. All 14 existing numeric
hashes match for these no-basin cases, as do drainage, routing agreement, channel
conflict and delivered-quality summaries. New water products repeat exactly.
Geometry-distance optimization remains separate work, and these results do not
justify a language rewrite.

Ignored local evidence:
`artifacts/authored-water-performance-20260910.json`,
`artifacts/authored-water-2048-performance-20260910.json`, and
`artifacts/authored-water-paired-{before,after}-final-20260910.json`.
The final public build is `artifacts/authored-water-final-20260910/`.
The isolated prior-source checkout was temporary and is reproducible from Git.

## Next implementation

1. Give closed lake/dry-basin intent explicit terminal behavior in the planning
   graph, preserving contributing-area accounting. Route draining lakes through
   their declared outlet only after validating the complete downstream path.
2. Compare retention, constrained breach and reroute proposals under existing
   budgets, preserving anchors and checking downstream closure before adoption.
3. Add editing of existing basin vertices/outlets, exact shoreline vectors and
   refinement checks. Measure outer retention-edge slopes before deciding whether
   exterior feathering is needed; never weaken the zero-cut interior.
4. Classify enclosed SVG water and ocean boundary levels explicitly. Retain
   hierarchy/runoff research for when actual water availability becomes a model input.
