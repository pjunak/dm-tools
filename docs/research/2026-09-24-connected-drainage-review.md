# Connected drainage review and authored density — 2026-09-24

Status: implemented and measured on public fixtures. This improves network
inspection and generation control. It does not certify realistic river geometry.

## Findings and implementation

The workbench cached a review raster and enlarged its channel strokes during
navigation. Static exports already drew thin D8 lines at their requested size,
but the cached interactive image still became blocky at large zoom. All channels
also had equal visual weight, with no control over initiation density.

The new pipeline model partitions selected edges into connected reaches and
computes unique D8 contributing areas. A viewport renderer selects complete
reaches by downstream-monotone area, redraws thin antialiased paths and retains
every red sampled conflict. Junctions remain exact and no bends are invented.
An All channels toggle retains full review. A separate Depressions toggle keeps
coarse basin polygons from obscuring channel paths unless requested. Authored density changes initiation
before generation and retains downstream closure. See
[ADR-0069](../adr/0069-connect-and-scale-drainage-review.md) and the
[user/implementation guide](../terrain-drainage.md).

## Evidence

The public example, regional and synthetic square fixtures were measured at
513 output samples, seeds 42 and 7, densities 0.5/1.0/2.0 and four zoom levels.
The preview is 1025 pixels wide; its height follows each fixture's aspect ratio.
Each row below uses density 1.0 for inspection, with density 0.5 as the generated
network comparison. Selection counts concern the whole map at that scale,
independently of viewport cropping. Red warnings are additional to selection.

| Fixture / seed | Generated edges, density 1 | Edges, density 0.5 | Total reaches | Overview selected | 4x selected | Uphill edges retained |
|---|---:|---:|---:|---:|---:|---:|
| example / 42 | 2463 | 885 | 539 | 75 | 539 | 27 |
| example / 7 | 2361 | 903 | 469 | 62 | 469 | 36 |
| regional / 42 | 2714 | 1324 | 422 | 68 | 422 | 133 |
| regional / 7 | 2463 | 1239 | 339 | 58 | 339 | 73 |
| square / 42 | 2206 | 1144 | 182 | 71 | 182 | 81 |
| square / 7 | 2465 | 1337 | 203 | 59 | 203 | 108 |

Across all 18 runs, reach extraction covered every channel edge exactly once,
connections and area hierarchy passed, and rendering left the DEM unchanged.
Preparation took 10.7–29.1 ms. Across 72 viewport draws, observed wall times were
12.4–106.4 ms (median 59.1 ms). These are single local observations, not latency
guarantees or process-memory measurements. Tests compare different tile sizes
and cropped pans exactly; antialiasing canvases stay bounded to a haloed tile.

At density 1.0, the example/42, regional/7 and square/42 DEMs, receivers, selected
channels and incision arrays exactly matched snapshots captured before editing.
The new setting therefore retains the validated default. An attempted default
of 0.75 made the existing synthetic downstream-shoulder-width test fail (both
cross-sections exceeded its 40 m cut threshold at two nodes). The default remains 1.0
and the original invariant is unchanged. Other densities are user-controlled
alternatives; fewer channels alone is not proof of better geomorphology.

The connected-render tests also cover anisotropic cells, exact junctions,
unchannelled donors, malformed topology, nested visibility, hidden-branch red
warnings, thin strokes at zoom and bounded scratch. Real Tk tests exercise
density freshness, graph-cache reuse, zoom, independent depression visibility,
complete-network review and immutable completed ground. Scientific hillshade and canonical diagnostics are unchanged.

Final validation: 1,253 tests passed, including real Tk interaction tests; Ruff
and Pyright passed. All 857 checked local Markdown file targets resolved. The
final workbench was visually inspected at fit and 4x zoom with depressions both
hidden and enabled. No private world map was regenerated for these measurements.

### Reproduce

```powershell
.\.venv\Scripts\python.exe -m benchmarks.channel_network --output artifacts/channel-network-review
```

Use a new directory. Each case records its effective input hash. The report is
written last; engine, benchmark and fixture source identity must remain unchanged
during measurement. Generated PNGs and JSON
are ignored local artifacts. The measured run was
`artifacts/channel-network-final-20260924/report.json`, with package source SHA-256
`780b3eb721ad4f82038355c39d0a958169349fdf884c0421bfbb17d2cb3f88bc`.
Pre-change snapshots were retained locally under
`artifacts/drainage-network-baseline-20260924`; baseline package source was
`202410c9e8dda1f66baed313da4381c810db39756743236d6fddf0bbd7b7ec82`.
These paths are reproduction evidence for this workstation, not committed test fixtures.

## Research and next generation work

1. **Connected thresholding.** TauDEM documents that the threshold quantity must
   increase downstream to preserve a continuous network. Our complete-reach D8
   area hierarchy applies that principle to cartographic visibility; its 64/112
   pixel thresholds are project choices, not prescribed scientific constants.
   [TauDEM threshold documentation](https://hydrology.usu.edu/taudem/taudem5/help53/StreamDefinitionByThreshold.html).
2. **Measure sinuosity at the relevant scale.** The USGS scale-specific sinuosity
   work describes how apparent shape depends on measurement stride. We have not
   implemented its metric; use it as a candidate for evaluating future path
   geometry rather than optimizing a single smoothed screenshot.
   [USGS paper record](https://www.usgs.gov/publications/scale-specific-metrics-adaptive-generalization-and-geomorphic-classification-stream).
3. **Filled-depression convergence.** Barnes, Lehman and Mulla describe gradients
   away from higher ground and toward exits to avoid parallel flat routing.
   This project already has an integer-gradient basin-flat implementation.
   Reusing it for global filled depressions needs explicit acyclic order,
   barrier/terminal handling and MFD accumulation checks; it is not implemented
   by this batch. [Author paper](https://arxiv.org/abs/1511.04433).
4. **D-infinity as a comparison.** Tarboton's method uses a continuous downslope
   angle and apportions contributing area between neighboring cells. It is a
   candidate for reducing hillslope direction bias, not an automatic source of
   continuous river polylines or meanders. No new solver dependency was added.
   [Author/institution paper record](https://digitalcommons.usu.edu/cee_facpub/2507/).

The P0 follow-up is a terrain-guided channel path shared by source probing,
incision, longitudinal floors and rendering. Compare whole paths and turn
geometry against the current D8 baseline, preserving authored divides, exact
junctions, coastal/lake terminals, cut budgets and fixed parent context. Keep
failed source/crest feasibility visible. Runoff and regional density are separate
inputs to research; finer local hydrology must precede real small-river products.
