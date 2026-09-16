# Connected diagonal valleys - 2026-09-16

Status: adopted shaping improvement, [ADR-0051](../adr/0051-connect-diagonal-valley-shaping.md).
Baseline: `8104761`, generator `coastline-constraint-terrain@9` and automatic
valleys `regional-budget-mfd-d8-valleys@7`. Adopted: generator `@10`, automatic
valleys `@8`. Public schemas and dependencies are unchanged.

## Change and experiment

The [bounded cubic field](2026-09-16-bounded-valley-reconstruction.md) softens
grid-edge creases but does not use the connectivity of its corner samples.
Along a selected diagonal, incision and suppression can both dip between its
two channel nodes. A synthetic constant-depth diagonal then develops a hump.

The adopted correction operates only in cells containing a selected D8 diagonal.
Metric projection supplies an interpolated endpoint target. A smooth positive
correction approaches that target within a compact corridor, with zero value
and first derivatives at cell edges. It never exceeds the existing corner range
or bilinear cut ceiling. Exact vector basin retention and later authored
constraints retain authority. Ambiguous crossing diagonals receive no correction.
The routing tree, canonical values and cardinal cell-edge samples are unchanged.

The ADR records the complete formula and fixed process-grid fractions. They are
heuristics for reconstructing this field, not physical width/discharge laws.
An incision-only exploratory control reduced mean sampled excursions, but
connecting suppression as well gave the larger improvement on all eight tested
cases. The adopted path evaluates both together, sharing connection geometry.
No old runtime mode or new dependency is retained.

## Finite profile method

The maintained `benchmarks.channel_profiles` harness prepares the current full
terrain field on its fixed canonical routing grid. For each selected receiver
edge, it evaluates 65 equally spaced stations including endpoints. Ground uses
the same Float32 boundary as water review; values are then promoted to Float64
for subtraction. Excursion is the maximum height above any earlier station's
running minimum. Count excursions above 0.01 m. Report all finite edges and,
separately, edges whose endpoint drop exceeds 0.01 m, split by orientation.
Non-finite/sea samples are unresolved profiles, never clear paths.

The previous report used 17 stations and Float32 arithmetic for its exploratory
threshold comparisons. Its counts are not interchangeable with this report.
Here both versions use the same new harness and input hashes. Baseline source
was extracted from `8104761` into an ignored source directory and selected with
`PYTHONPATH`; runtime fingerprints identify the actual imported package. Harness
and fixture source hashes are checked across each run, and input/profile/canonical
hashes are retained. The final metadata-complete rerun reproduced the initial
probe results. No private world map is a fixture.

Results for descending endpoints; statistics include zero-excursion edges:

| Case / seed | Edges | Uphill interiors before / after | Mean excursion m before / after | 95th percentile m before / after |
|---|---:|---:|---:|---:|
| example / 42 | 2040 | 512 / 470 | 6.464 / 1.477 | 53.81 / 8.94 |
| example / 20260902 | 2010 | 564 / 530 | 9.330 / 1.802 | 73.15 / 10.35 |
| regional / 42 | 2392 | 539 / 503 | 4.530 / 1.227 | 34.48 / 7.88 |
| regional / 20260902 | 2422 | 673 / 628 | 5.222 / 1.435 | 37.80 / 7.64 |
| authored / 42 | 2052 | 785 / 745 | 10.018 / 2.401 | 76.19 / 12.28 |
| authored / 20260902 | 2444 | 759 / 736 | 8.082 / 1.817 | 65.01 / 10.74 |
| outlet / 42 | 1245 | 188 / 142 | 3.353 / 0.416 | 21.70 / 2.43 |
| outlet / 20260902 | 1130 | 192 / 179 | 5.081 / 0.544 | 49.53 / 4.01 |

Mean excursion falls 72.5-89.3% on this matrix. Counts also fall, but many small
climbs remain. The largest after-change excursion is 212.05 m on the second
regional seed, versus 261.35 m before. Lower means do not make every channel valid.
Cardinal-profile summaries and canonical hashes match exactly. No non-finite
profiles occurred in these cases; the harness regression covers that boundary.

## Additional dense checks

Use an additional seed (104729), island/square/regional geometries, and 257
stations per edge. These were not used to choose correction constants.

| Case / seed | Edges | Uphill interiors before / after | Mean excursion m before / after | 95th percentile m before / after |
|---|---:|---:|---:|---:|
| archipelago / 104729 | 1373 | 373 / 337 | 7.495 / 1.355 | 53.39 / 7.95 |
| square / 104729 | 2359 | 1123 / 1094 | 13.024 / 3.274 | 85.91 / 14.45 |
| regional / 104729 | 2585 | 615 / 563 | 4.312 / 1.221 | 30.22 / 6.58 |

Mean excursions fall 71.7-81.9%. Cardinal summaries and canonical hashes still
match, with no non-finite profiles. The regional maximum remains 383.26 m
(before: 408.06 m). This outlier and hundreds of residual climbs need separate
classification and conditioning. These denser finite checks are not certified
continuous bounds, whole-route guarantees or a physical hydrology model.

## Visual and numerical preservation

Inspect regenerated 1025-sample public `regional` and `example` maps, seed 42,
using identical enlarged crops. Diagonal floors show less scalloping. Long
straight paths and sharp D8 turns remain, and the global terrain composition
is unchanged. This improves existing geography without generating new local
terrain on zoom.

Compared with the baseline, full-map RMS height changes are 2.32 m and 2.94 m
respectively. Maximum lowering is 155.80 m and 151.31 m; maximum raising is
32.23 m and 31.21 m. Incision never decreases, but increased suppression can
remove a negative residual and therefore raise local ground. The canonical
land mask, incision, suppression, cut limits, receivers and finished heights
are exactly equal. Authored constraints and generation limits still apply.

## Cost and water checks

Four cases, two seeds, two fresh-process repetitions per version: 32 timed
runs at longest-side resolution 513. Runs were sequential before/after, without
concurrent heavy work or engine/benchmark edits. Windows 11 AMD64, CPython
3.14.7, NumPy 2.5.2, Shapely 2.1.2. Generation excludes rendering/export; memory
is process high-water through generation, including imports. Medians:

| Case / seed | Seconds before / after | Change | Peak MiB before / after |
|---|---:|---:|---:|
| example / 42 | 0.971 / 0.983 | +1.3% | 102.1 / 102.3 |
| example / 20260902 | 0.968 / 0.983 | +1.6% | 102.1 / 102.2 |
| regional / 42 | 1.135 / 1.143 | +0.8% | 109.8 / 110.1 |
| regional / 20260902 | 1.142 / 1.152 | +0.9% | 110.1 / 110.2 |
| authored / 42 | 1.771 / 1.737 | -1.9% | 108.8 / 110.0 |
| authored / 20260902 | 1.760 / 1.744 | -0.9% | 108.6 / 110.1 |
| outlet / 42 | 2.797 / 2.777 | -0.7% | 117.1 / 116.8 |
| outlet / 20260902 | 2.729 / 2.746 | +0.6% | 116.9 / 116.9 |

Observed generation time differs by -1.9% to +1.6%; memory by -0.3 to +1.5 MiB.
Two sequential repetitions are a cost check, not evidence of a speedup or a
4096-pixel budget. Only elevation hashes change in these benchmark products;
canonical diagnostics, retained water evidence and basin-outflow summaries
match. Other off-grid water decisions are allowed to change with the new field.

## Reproduction and remaining work

The [benchmark guide](../../benchmarks/README.md#channel-interior-profiles) gives
commands for 65-station and additional 257-station runs. Use the same current
harness with source-isolated baseline and adopted packages, then require matching
input hashes before comparison. Performance uses the existing harness:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.terrain --case example regional authored outlet --resolution 513 --seed 42 20260902 --repeats 2 --output artifacts/connection-performance.json
```

This run's ignored artifacts are under `artifacts/channel-connections-2026-09-16/`:
`before/after-profiles-final.json`, `before/after-holdout-final.json`,
`before/after-performance.json`, `visual-measurements.json`, the two rendered maps
and `channel-comparison.png`. All reports use new output paths; generated maps
and temporary baseline source are not committed fixtures.

Regressions cover both diagonal orientations, reduced synthetic scalloping,
exact knots/edges and first-derivative continuity, caps, untouched cells/divides,
already deeper cuts, metric symmetry, input ownership and chunk independence.
A field-level comparison requires improved public-channel means while preserving
cardinal profiles. Benchmark tests cover hidden interior humps, unresolved
non-land samples, empty groups and bounded batch allocation. Final validation:
763 tests passed; Ruff and strict Pyright passed; 540 local Markdown file links
resolved; the diff whitespace check passed.

[TODO](../../TODO.md) keeps cardinal/interior climbs, large outlier classification,
turn geometry, full-path repair and conservative complete-field bounds open.
The next improvement should use these measurements while preserving cut budgets,
retention and authored authority. No generated-DEM editing or zoom-detail claim
is introduced.
