# Source-aware channel floor reconstruction

Date: 2026-09-16. Implemented decision: [ADR-0052](../adr/0052-fit-channel-cuts-to-sampled-terrain.md).

## Question and diagnosis

After bounded cubic reconstruction and diagonal connection shaping, can the
remaining channel interiors improve without moving canonical nodes or expanding
cut budgets? The previous [comparison](2026-09-16-connected-diagonal-valleys.md)
left cardinal interiors unchanged and recorded large regional outliers.

The diagnosis evaluates the actual Float32 ground along selected D8 edges, then
separates macro height, residual detail, suppression, incision and its bilinear
ceiling. At 257 stations, two regional outliers lie wholly inside a mountain
region (weight exactly one). The mountain carrier crosses zero between nodes,
creating the crest of the ridged recipe. These are hidden source crests, not
regional-transition or coastline artifacts:

| Regional seed / edge | Interior uphill excursion | Required cut at sampled crest to reach linear floor | Existing cut ceiling there |
|---|---:|---:|---:|
| 104729 / 8109 to 7853 | 383.26 m | 563.40 m | 150.61 m |
| 20260902 / 16628 to 16884 | 213.71 m | 380.73 m | 165.92 m |

The 65-station result for the second edge is 212.05 m; the denser stations
resolve a higher crest. Neither sampling density certifies the true maximum.
The existing cut already reaches the ceiling at both reported crest samples.
Further smoothing within that ceiling cannot remove these obstacles.

Smaller cardinal cases have different causes. Regional seed 104729, edge
19126 to 19383, has a 20.42 m hump driven by residual detail; its crest needs a
41.56 m cut while the ceiling allows 100.87 m. Example seed 42, edge 18349 to
18606, has a 16.84 m climb *out of a dip*. Increasing cuts only deepens that dip.
Exploratory one-sided correction reduced average cardinal excursions less than
fitting cuts in both directions. These were development probes, not independent
validation cases or complete-path hydrologic tests.

## Implemented change

Prepare the pre-constraint floor at existing canonical nodes. Inside compact
corridors around explicitly selected cardinal and diagonal connections, compute
the cut required for a linear floor between the two nodes, using each query's
actual macro height and retained residual. Blend toward that cut, with endpoint
and lateral tapers. Reduce excessive cuts as well as increasing insufficient
ones; never add height above the uncut source with its retained detail.

Overlap uses a weighted mean and smooth union coverage. The original bilinear
nodal cut ceiling, exact retention masks, coastline zero, authored constraints
and final height ceiling remain authoritative. Canonical values and topology
are unchanged. The final cut can leave the initial corner *cut-value* range,
but cannot leave `[0, original interpolated cut ceiling]`.

This adds no random stream, schema, dependency or user setting. Algorithm IDs
become `coastline-constraint-terrain@11` and `regional-budget-mfd-d8-valleys@9`.

## Reproducible comparison

Baseline is commit `0c5bed0`, imported from an isolated source archive. Use the
same maintained `benchmarks.channel_profiles` and `benchmarks.terrain` harnesses,
fixtures, interpreter and dependencies for both versions. Profile reports retain
input/source/runtime identity, canonical-array hashes, station counts, Float32
profile hashes and explicit non-finite counts. No runtime source changed during
measurements. Generated evidence is local and ignored under
`artifacts/channel-diagnosis-2026-09-16/`.

Run the channel harness at 65 stations for example/regional/authored/outlet and
seeds 42/20260902, then at 257 stations for archipelago/square/regional and seed
104729. The latter cases were already inspected during development; they are
additional dense checks, not an unseen holdout set.

```powershell
.\.venv\Scripts\python.exe -m benchmarks.channel_profiles --output artifacts/floors-main.json
.\.venv\Scripts\python.exe -m benchmarks.channel_profiles --case archipelago square regional --seed 104729 --stations 257 --output artifacts/floors-dense.json
```

Only finite edges with endpoint drop greater than 0.01 m enter the following
summaries. Uphill excursion is the largest rise above an earlier running minimum
within an edge, measured after promoting Float32 ground to Float64. Means include
zero-excursion edges. An edge remains flagged above 0.01 m.

## Main profile results

| Case / seed | Uphill interiors before / after | Mean excursion m before / after | Cardinal mean m before / after | P95 m before / after |
|---|---:|---:|---:|---:|
| example / 42 | 470 / 452 | 1.477 / 0.909 | 0.611 / 0.140 | 8.94 / 4.82 |
| example / 20260902 | 530 / 524 | 1.802 / 1.113 | 0.711 / 0.156 | 10.35 / 6.03 |
| regional / 42 | 503 / 494 | 1.227 / 0.723 | 0.610 / 0.150 | 7.88 / 3.61 |
| regional / 20260902 | 628 / 601 | 1.435 / 0.913 | 0.643 / 0.155 | 7.64 / 3.80 |
| authored / 42 | 745 / 747 | 2.401 / 1.451 | 1.034 / 0.241 | 12.28 / 7.78 |
| authored / 20260902 | 736 / 723 | 1.817 / 1.086 | 0.736 / 0.197 | 10.74 / 6.21 |
| outlet / 42 | 142 / 153 | 0.416 / 0.275 | 0.104 / 0.025 | 2.43 / 1.27 |
| outlet / 20260902 | 179 / 174 | 0.544 / 0.384 | 0.100 / 0.021 | 4.01 / 2.55 |

Mean excursions fall 29.5-41.1% on the main matrix; cardinal means fall
73.2-79.1%. All eight maximum excursions are unchanged. Small flagged climbs
increase in authored/42 (745 to 747) and outlet/42 (142 to 153), despite lower
mean and P95 excursions. This is a reduction in climb size, not a guarantee that
every edge improves.

## Additional dense results

| Case / seed | Uphill interiors before / after | Mean excursion m before / after | Cardinal mean m before / after | P95 m before / after |
|---|---:|---:|---:|---:|
| archipelago / 104729 | 337 / 341 | 1.355 / 0.877 | 0.700 / 0.207 | 7.95 / 4.35 |
| square / 104729 | 1094 / 1076 | 3.274 / 1.754 | 1.838 / 0.425 | 14.45 / 8.63 |
| regional / 104729 | 563 / 555 | 1.221 / 0.834 | 0.520 / 0.120 | 6.58 / 2.89 |

Mean excursions fall 31.7-46.4% in these cases. The archipelago has **three
non-finite profiles in both versions**, excluded and unresolved, and its count
of small flagged climbs increases by four. The previous report's contrary prose
has been corrected against its own saved artifacts. The other ten case/seed
pairs have no non-finite profiles. Maximum excursions remain unchanged here too,
including the 383.26 m regional crest.

All eleven input/canonical hash inventories match: axes, selected channels,
receivers, nodal incision, nodal limits and suppression. Descending-edge counts
also match. Tests compare actual finished Float32 ground at canonical nodes,
including an authored fixture. Finite samples do not prove continuous clearance,
and per-edge results do not describe an entire downstream route.

## Performance and numerical products

513 px, eight case/seed pairs, fresh process per run. The first before/after
batches showed substantial timing drift, so repeat the complete pair and retain
**all four repetitions per version**, 64 total runs. No concurrent test suite
or visual generation ran during those measurements. The table shows combined
medians; this is generation time, excluding file export.

| Case / seed | Before s | After s | Median change | Peak resident change MiB |
|---|---:|---:|---:|---:|
| example / 42 | 1.104 | 1.108 | +0.3% | +0.71 |
| example / 20260902 | 1.107 | 1.096 | -1.0% | +0.55 |
| regional / 42 | 1.290 | 1.294 | +0.3% | +0.73 |
| regional / 20260902 | 1.249 | 1.293 | +3.5% | +0.97 |
| authored / 42 | 1.976 | 1.979 | +0.2% | +2.71 |
| authored / 20260902 | 2.204 | 2.021 | -8.3% | +2.36 |
| outlet / 42 | 3.114 | 2.992 | -3.9% | -0.17 |
| outlet / 20260902 | 2.834 | 2.894 | +2.1% | +1.24 |

The -8.3% to +3.5% median differences are smaller than observed run-to-run
variation (example/42 before: 0.971-1.385 s; after: 0.999-1.257 s). These data do
not establish a speedup or a precise overhead. Peak memory differences are
-0.17 to +2.71 MiB. Larger resolutions and worst-case floor/sampling cost remain
separate measurements; no Rust migration conclusion follows from this run.

Repeated numeric hashes match within each version. Across versions, **only the
elevation hash changes** in all eight performance cases. Land masks, axes,
canonical routing/final ground/conflicts, basin labels, water surfaces, captured
area transfers and internal-path evidence retain their hashes. Off-grid water
review still consumes the changed surface and can differ for other inputs.

## Visual inspection

Generate both versions at 1025 px for example/42 and regional/104729, with the
same scientific rendering and crop coordinates. Inspect `floor-comparison.png`.
The visible change is subtle at this scale: local floor shading changes while
regional composition and D8 bends remain. Do not present it as a new landscape
style or a solution to the straight-channel appearance.

| Case / seed | DEM difference RMS | Maximum lowering | Maximum raising |
|---|---:|---:|---:|
| example / 42 | 1.201 m | 48.92 m | 33.14 m |
| regional / 104729 | 1.248 m | 49.65 m | 50.75 m |

Raising here restores part of an automatic cut during generation; it does not
change authored inputs or edit a completed DEM. Land masks match in both pairs.

## Validation and next work

Regression tests cover both signs of source relief in all eight directed D8
orientations, node preservation, cut ceilings, non-land endpoints, unaffected
areas, shared-edge derivatives, metric transpose/reflection symmetry, immutable
inputs, chunk/order independence and finished-field comparisons. Validation on
the final implementation: **786 pytest tests passed** in 266.97 s; Ruff passed;
strict Pyright reported zero errors and warnings; 549 local Markdown file targets
resolved; `git diff --check` passed. No editor UI code changed in this slice.

Next investigate route alternatives or finer planning around hidden mountain
crests **before** adding more floor corrections. Separate cap-limited barriers
from source depressions, endpoint-taper effects and retention boundaries. Whole
route conditioning and rounded D8 geometry remain unfinished; preserve authored
authority and cut budgets. Zoom-driven enrichment remains a separate planned
generation operation, as specified by ADR-0048.
