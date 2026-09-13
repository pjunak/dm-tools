# Prepared bounds for water-sampling guides - 2026-09-13

Status: implemented exact-query optimization. This continues the workload side
of the [adaptive refinement follow-up](2026-09-13-adaptive-water-profile-refinement.md).
It does not introduce adaptive clearance or change terrain heights. [TODO](../../TODO.md)
retains conservative elevation bounds and larger-workload experiments as open work.

## Change and research basis

Each immutable water-sampling guide now prepares an outward-rounded spatial
bounding box. A profile segment skips the guide only when the two boxes are
disjoint. Possible contacts continue through the original exact distance,
corridor, intersection and projection operations, in their original order.
A polygon guide includes its interior; local density guides include all polygon
components; global density always applies. Feature bounds include twice the
largest core/context radius. Replacing a guide rebuilds its own bounds.

This removes unnecessary geometry queries, not required probes. Gaussian terrain
tails are still evaluated by the complete field evaluator. The finite corridor
policy, station ordering/coordinates, Float32 ground, budgets and evidence remain
unchanged. Project v5, build v16 and all numeric algorithm IDs remain unchanged;
installed-source fingerprints change as usual. No index, global cache, new
package, compatibility path or native-language component was added.

[Shapely's geometry documentation](https://shapely.readthedocs.io/en/stable/manual.html#object.bounds)
defines the axis-aligned geometry bounds and minimum-distance operations used
here. Its [STRtree documentation](https://shapely.readthedocs.io/en/stable/strtree.html)
describes bounding-box candidate queries and the reduced selectivity of broad,
overlapping bounds. An index remains a candidate for larger scenes; this
experiment measures direct rejection without claiming an index crossover.

[Python's `math.nextafter`](https://docs.python.org/3.14/library/math.html#math.nextafter)
supports outward expansion. Padding is rounded outward before expansion and
bounds after addition/subtraction; strict disjoint comparisons retain grazing
contacts. Exact-rational regression checks cover cancellation and large/small
coordinates. These spatial bounds do not estimate a maximum unseen terrain
height or resolve the earlier midpoint counterexample.

## Workloads and method

The existing benchmark runner adds three opt-in fixtures. It keeps its original
13 default cases, so routine runs do not automatically include scaling workloads.

| Case | Lakes | Authored outlets | Relative points | Point radius |
|---|---:|---:|---:|---:|
| `lakes_small` | 4 | 2 | 16 | 12 km |
| `lakes` | 16 | 8 | 64 | 12 km |
| `lakes_broad` | 16 | 8 | 64 | 2000 km |

All use a 4000 km square, five detail levels, irregular 16-edge lake boundaries,
distributed alternating positive/negative points, and a 1500 m authored lake
level. These are workload probes, not proposed geography or equilibrium lake
levels. Forecast networks are potential work; full review can reject an outlet
before running those networks. The broad case deliberately makes rejection
ineffective. Existing connected-outlet, flat-outlet and dry-barrier fixtures
supply accepted/rejected path and complete network controls.

The comparison uses the tracked parent source from commit `acf5da4` in an
isolated import directory and the current source, with the same new fixture
helper. It alternates policy order between repeats; each operation starts a
fresh process. Both source trees and runtime/module paths are recorded. The
archive uses Git's stored line endings, so its package fingerprint differs from
the earlier working-directory fingerprint; the 64-pixel pilot also matched the
original checkout's numeric outputs. No authored input or setting is changed.

Generation and saved-input-equivalent forecasting run separately. Forecasting
includes normal field/canonical-grid preparation plus potential demand planning.
A single wrapper times the whole planning/review call without changing it.
Generation time excludes rendering/export. Evidence serialization separately
measures dataclass conversion and canonical JSON for forecast records or water
review/outflow summaries; numeric-array hashing follows those timings. It does
not measure all build diagnostics or disk export. Process high-water memory
includes imports and earlier allocations, not per-stage scratch usage.

A separate profiler run of the original 16-lake forecast made 626,440 geometry
object-distance calls. They consumed 2.298 s cumulative inside 3.319 s of demand
planning (4.756 s total with profiler overhead). The shared feature-window
routine accounted for 3.131 s. These instrumented numbers locate the bottleneck;
they are not interchangeable with the unprofiled measurements below.

## Paired measurements

The primary matrix contains 72 runs: six cases, two operations, two source
trees and three repeats. A separate 12-run simple-water control uses the
same method. All use seed 42 and 768-pixel output settings; the canonical
grid owns forecast demand independently of delivered resolution.

Median seconds (negative percentages mean less elapsed time):

| Case | Generation before | Generation after | Change | Forecast before | Forecast after | Change |
|---|---:|---:|---:|---:|---:|---:|
| `water` | 1.551 | 1.541 | -0.6% | 0.465 | 0.464 | -0.1% |
| `outlet` | 3.333 | 3.313 | -0.6% | 1.227 | 1.245 | +1.5% |
| `flat` | 3.208 | 3.165 | -1.3% | 1.036 | 0.939 | -9.4% |
| `dry` | 3.496 | 3.431 | -1.9% | 1.367 | 1.335 | -2.3% |
| `lakes_small` | 2.290 | 2.277 | -0.6% | 1.182 | 0.869 | -26.5% |
| `lakes` | 4.276 | 4.130 | -3.4% | 2.480 | 1.371 | -44.7% |
| `lakes_broad` | 4.392 | 4.348 | -1.0% | 4.528 | 4.555 | +0.6% |

For distributed guides, forecast planning itself falls from 0.389 to 0.072 s
on four lakes and from 1.417 to 0.225 s on sixteen lakes: about 82% and 84% less
planning time. These stages are already included in total forecast time.
The sixteen-lake generation improvement is smaller because field evaluation
and routing dominate its remaining work. All new scaling scenes have zero
connected outlets, so their full generations do not execute the potential
networks counted by forecasts; the older controls exercise actual transfer.

The sixteen-lake total forecast ranges are 2.437-2.580 s before and 1.298-1.506 s
after; its generation ranges are 4.231-4.366 s and 4.100-4.132 s. Broad-overlap
forecast ranges are 4.417-4.574 s and 4.545-4.556 s. Broad overlap shows no clear
benefit. Simple-water, connected-outlet and several small generation differences
have overlapping ranges; three repeats do not establish those small changes.
The filter is useful where bounds are selective, not a universal speedup.

The separate current profiler run reduces object-distance calls from 626,440
to 30,984 (about 95% fewer). Its demand planning takes 0.445 s under profiling;
feature-window work takes 0.327 s. The 313,216 cheap bounds comparisons account
for 0.028 s cumulative. Those counts and call sites corroborate the measured
cause; profiler times are separate from the unprofiled table.

Requested station totals across the new fixtures remain exactly equal:

| Case | Shorelines | Potential wet links | Potential dry links |
|---|---:|---:|---:|
| `lakes_small` | 1,557 | 6,053 | 23,554 |
| `lakes` | 3,221 | 3,137 | 24,754 |
| `lakes_broad` | 3,386 | 3,125 | 24,919 |

These totals summarize separate valid per-basin plans, not a new project budget.
None of these three forecasts exhausts a cap; complete-budget regressions in the
suite cover exhaustion. Flat-outlet demand remains 2,195 shoreline, 6,475 wet and
199,188 dry stations. Maximum area-balance error in the generation comparisons
is 7.5e-9 km2, equal across implementations.

Operation peak process memory ranges from 93.2-141.3 MiB before and 93.2-141.4 MiB
after, without a demonstrated material change. The measured evidence payloads
reach 9,915,010 bytes; their conversion/JSON serialization takes at most 0.102 s
across the 84 runs. These observations do not establish total build/export cost,
per-stage memory allocation, large-project limits or 4096-pixel performance.

## Verification and evidence

- Full pytest: **523 passed in 295.19 s**; the focused sampling/benchmark suite
  passed all 61 checks. Fourteen new regression cases cover mixed geometry,
  holes, grazing contacts, global/local density, edited bounds, outward rounding,
  complete-budget failure and repeatable opt-in workload fixtures.
- Ruff passed for the repository; strict Pyright reported zero errors or warnings.
- All 145 local Markdown links in changed documents resolve; whitespace checks pass.
- The fresh 768-pixel public flat-outlet build passed build-v16 schema and
  completion-ID checks. All 13 output files match the preceding verified build
  byte for byte, including diagnostics and previews. GeoTIFF heights/masks match
  the NPY products. The new build ID is
  `da3ff82b09059ea9f843abd7dbcaed64eb3414efb6abe52f82a08a69eddc5f48`.

The comparison checks identical input hashes, all 27 numeric products for
generation, complete water/outflow evidence hashes and every forecast record.
Repeats match across both implementations. Complete station counts and failures
are preserved; faster rejection does not silently lower detail, drop stations
or increase budgets. The current caps remain 65,536 per profile, 65,536 per wet
network and 262,144 per dry network, with evaluation batches of 4,096.

Ignored local evidence (not committed):

- `artifacts/water-bounds-paired-final-20260913.json`: 72-run paired generation/forecast matrix;
  SHA-256 `ff848892d7ae00c104ecd34d4cbcda20d4e109e8fc8b7a68c2b6010f7d4c7e45`.
- `artifacts/water-bounds-simple-control-20260913.json`: 12-run simple-water control;
  SHA-256 `0648955f6026006c81eb2409e2b260a02d993cd2c978f5c1a9436ce086bff561`.
- `artifacts/water-bounds-build-validation-20260913.json`: schema, completion and unchanged-product verification;
  SHA-256 `9071930ec503bd70ba921bd07fdb9be8c8a793960862bd9a152fb8f7b422e821`.
- `artifacts/measure_water_bounds.py`: paired timing/identity helper;
  SHA-256 `7f5230972f5fe039d9d7dda35580fbcf4a2e02c4704f4ab1d05068abca4401fe`.
- `artifacts/validate_water_bounds_build.py`: build verification helper;
  SHA-256 `11f7b96a7849033ac81e624677727f4739d63ce104f805351828cbbfe6324238`.

Profiler records are `artifacts/water-bounds-baseline.pstats` and
`artifacts/water-bounds-current.pstats`. The source archive and 64-pixel
pilots remain under `artifacts/water-bounds-*`. The validated build is in
`artifacts/water-bounds-build-20260913/`. Runtime: Windows 11 AMD64,
CPython 3.14.7, NumPy 2.5.2, Shapely 2.1.2 / GEOS 3.13.1, Rasterio 1.5.1 /
GDAL 3.12.4 and Pillow 12.3.0. Source fingerprints:

- Archived parent: `48a1022a5dc407e9184bc32c93c231f16b8b36212c34d8e90ade3e916c4cf4bc`.
- Current implementation: `0613e726848ad843423f057f8da56cc39171ca854fcdb9e56f021359ef535485`.

## Next work

1. Keep the full-field error-bound investigation separate from this spatial
   optimization. Derive conservative component/composition bounds, including
   rounding, before selecting a certified adaptive stopping rule.
2. Extend lake/constraint counts, long lines, regional boundaries and footprint
   complexity before selecting an index. Direct candidate checks are still
   linear in guide count, and broad overlapping extents remain weak filters.
3. Measure total export time and real scratch allocations, then define latency
   and memory targets before larger network budgets or shared-path caches.
   Potential demand is not executed review, and neither predicts physical flow.
4. Define controlling-sill/storage assumptions for lake chains, followed by
   reviewable bounded breach/reroute proposals. No Tharkeniss Veld authoring,
   private map rebuild or workbench interaction was performed in this slice.
