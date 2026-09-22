# Stable detail-band amplitudes

Date: 2026-09-22. Baseline: `d09c34a`. Implemented decision:
[ADR-0059](../adr/0059-preserve-noise-band-amplitudes.md).

## Problem and implemented slice

The former noise sum normalized every selected prefix to unit amplitude. With
roughness 0.55, choosing six bands instead of two reduced the first two band
coefficients by 28.26%. The same coordinates were deterministic at a fixed
setting, but adding finer detail also weakened the broad noise.

The generator now assigns band k the fixed coefficient `(1-r)*r^k`. The
mathematical total after N bands is `1-r^N`; uncomputed detail retains its share.
At r=0.55 the resolved budgets for 2/6/12 bands are 0.6975, 0.972319359375 and
0.999233782135. Prefix coefficients are exactly the same rounded Float64 values
at every supported count. Explicit tail sampling uses the same octave addresses
and coefficients, without rescaling.

Regional shapes need a different, fixed role: their two-band carrier retains
full-scale weights 2/3 and 1/3. Texture uses only the third and finer bands.
An intermediate candidate also shrank the shape carrier and was rejected;
`after.json` is that intermediate measurement, not the delivered implementation.
Current results are in `final.json`. Global/regional base macro arrays remain
exact across 2/6/12 bands, including plain, hill, plateau and mountain recipes.

The isolated-noise enclosure now shares the production coefficients and omits
the old normalization division. Its rounding allowances and complete work limits
remain. The experiment covers default-prefix noise, not selected tails, scaled
regional carriers, blended terrain or a continuous water-clearance guarantee.
Generator/noise/landform identities advance to @16/@2/@2. Schemas, named seeds,
lattice addresses and the canonical 257-longest-side routing policy stay fixed.
No compatibility switch, migration or external dependency was introduced.

## Finished terrain still needs a parent contract

`benchmarks.detail_bands` compares whole-map settings on four public fixtures,
seed 42, each with 257 nodes on its longest side. The two-band result is the
reference. Pointwise figures cover all land. Cell figures use the central
129x129-node window: 16x16 trapezoidal cell averages, each over 8x8 fine intervals.
All 256 cells are land-covered for each case. These are finite quadrature
measurements, not analytic integrals or an adopted restriction tolerance. This
fixed grid under-resolves the finest bands, particularly at twelve levels;
repeat at adequate physical spacing before choosing restriction tolerances.
The figures measure this sampled map's response, not converged spatial means.

| Case | Bands | Point RMS m | Point max m | Cell-mean RMS m | Cell-mean max m | Changed canonical receivers |
|---|---:|---:|---:|---:|---:|---:|
| example | 6 | 110.71 | 472.32 | 79.94 | 262.99 | 0 |
| example | 12 | 111.06 | 463.35 | 79.91 | 261.79 | 0 |
| regional | 6 | 68.17 | 396.26 | 48.63 | 181.11 | 0 |
| regional | 12 | 68.37 | 409.57 | 48.57 | 182.20 | 0 |
| authored | 6 | 105.51 | 383.78 | 88.88 | 262.86 | 1753 |
| authored | 12 | 106.64 | 398.84 | 91.29 | 276.38 | 1834 |
| water | 6 | 76.57 | 371.21 | 43.50 | 192.51 | 0 |
| water | 12 | 76.85 | 382.43 | 43.42 | 191.41 | 0 |

The raw coefficients and base macro are stable, but added noise has nonzero
local means. Nonlinear shaping, clipping, authored guidance and valley
conditioning also influence the finished surface. Authored ridge/valley width
uses the full detail driver, so its routing can change despite a fixed base
macro. Stable amplitudes therefore do not establish broad-geography preservation
for a finished parent. Coarse spectral power is still unmeasured; R34 remains
open for that comparison, a restriction operator and parent-conditioned detail.

The existing `sample-region` command continues to sample unchanged settings.
This experiment is not a regional generation job, parent DEM modification or a
small-river implementation. Finer cartographic rivers still require inherited
hydrology on genuinely finer ground.

## Before/after generation and water checks

The maintained terrain harness ran eight public cases at requested 129 px,
seed 42, one fresh process per case and version. Inputs and harness hashes match;
source/runtime identities are retained. The table reports current land-height
statistics and canonical endpoint conflicts, with values before -> after.
All height columns are metres. These networks differ, so their conflict counts
are not comparisons of an identical set of edges.

| Case | Mean height | Height deviation | Uphill endpoint edges | Maximum cut deficit |
|---|---:|---:|---:|---:|
| example | 1771.09 -> 1769.18 | 697.81 -> 691.33 | 38 -> 27 | 114.27 -> 95.25 |
| regional | 1394.76 -> 1394.28 | 776.52 -> 772.58 | 120 -> 133 | 152.63 -> 146.28 |
| authored | 1730.33 -> 1727.44 | 675.97 -> 664.62 | 381 -> 280 | 135.07 -> 110.41 |
| water | 1342.53 -> 1342.60 | 578.64 -> 575.40 | 20 -> 23 | 24.50 -> 21.60 |
| outlet | 1342.38 -> 1342.35 | 526.03 -> 522.98 | 21 -> 22 | 33.44 -> 30.77 |
| internal | 1344.55 -> 1344.52 | 524.52 -> 521.47 | 22 -> 22 | 33.46 -> 30.79 |
| dry | 1342.59 -> 1342.56 | 525.87 -> 522.82 | 21 -> 22 | 33.45 -> 30.78 |
| archipelago | 1468.16 -> 1465.89 | 729.01 -> 723.90 | 1 -> 0 | 12.48 -> 0.00 |

Land masks match in all eight cases. Lake/dry-basin outlet states and issue sets
also match, but water surfaces, captured areas and dry/wet collection counts can
change with the new ground. For example, the connected outlet case collects
1,370 -> 1,422 dry cells and 276 -> 271 wet cells; retained cells fall
2,794 -> 2,747. Maximum absolute area-balance error is 1.87e-8 km2 across these
runs. The narrow dry barrier still changes the selected link when its extra
feature observations are enabled, without changing terrain or captured area.

Generation wall times span 0.624-2.782 s before and 0.620-2.371 s after. These
single-run checks exclude file export and do not establish a performance gain
or regression. No tests or other terrain workloads ran alongside these timings.
The change adds no octave evaluations; regional texture now skips its two broad
bands. Larger projects and repeated timing comparisons remain unmeasured here.

## Dense channel evidence and an explicit regression

The channel harness sampled 257 stations on every selected regional edge for
seeds 7 and 42, using baseline code extracted from `d09c34a` and current code in
separate processes. All profiles were finite. Excursion is the largest rise
above a preceding minimum, measured from Float32 ground promoted to Float64.
These selected populations change between implementations.

| Seed | Finite edges | Mean excursion m | Maximum excursion m | Above 10 m | Above 50 m |
|---|---:|---:|---:|---:|---:|
| 7 | 2368 -> 2463 | 2.010 -> 2.045 | 149.83 -> 133.64 | 99 -> 114 | 20 -> 23 |
| 42 | 2585 -> 2714 | 2.671 -> 2.927 | 152.63 -> 146.28 | 118 -> 142 | 49 -> 64 |

The known seed-7 edge 9958 -> 9702 remains selected. A separate 1025-station
check measures **50.839 -> 133.892 m** of uphill excursion. This is a regression
on that route even though the all-edge maximum decreases. The existing profile
reconstruction still releases unnecessary cuts without increasing this edge's
excursion relative to its unprofiled current-source control, and preserves its
canonical endpoints. It does not fix the larger obstruction.

At those 1025 stations, the current source/cut envelope requires an interior
height of at least 2327.199 m while the fixed upstream ground is 2193.307 m:
the resulting 133.89176 m lower-bound rise agrees with the Float32 ground
measurement. Releasing its entire upstream cut could raise that node only to
2314.253 m, leaving a sampled 12.947 m obstruction. Joint nodal/interior
conditioning can address unnecessary upstream depth; complete path alternatives
are still needed for the remaining source/cut conflict. These are finite
observations on this edge, not continuous profile certification.

Its regression test now checks those reconstruction invariants against the
current source, rather than retaining a 52 m threshold tied to the old generated
field or replacing it with a looser unexplained height. Synthetic profile tests
still require actual improvement in all eight receiver directions and enforce
source/cut limits. Path alternatives and joint nodal/interior conditioning remain
necessary; this band-policy change is not a drainage-quality milestone.

## Visual inspection and reproducibility

Generated 1025-longest-side cartographic and scientific public regional previews
before/after, seed 42. Inspected compact cartographic renders: broad plateaus,
plains and mountain-belt placement remain similar, while fine texture and cuts
change. Straight D8 channels and repeating mountain lobes remain conspicuous.
No interactive editor or private-map acceptance was performed.

Evidence is under ignored `artifacts/detail-bands-2026-09-22/`: before/final
terrain reports, baseline source snapshot, detail-growth report, dense profiles,
known-edge checks and public PNGs. Runtime is CPython 3.14.7 on Windows 11 AMD64,
NumPy 2.5.2 and Shapely 2.1.2; JSON retains complete native-library and source
identities. Reproduction commands are documented in the
[benchmark guide](../../benchmarks/README.md). Dated earlier measurements retain
their original noise implementation and are not current performance claims.

## Validation and next work

The complete suite passes: **942 tests in 240.87 s**, including 30 new band,
tail and macro-field cases. Repository-wide Ruff and strict Pyright pass.
Existing component-bound, shared-coordinate, regional-sampling, hard-height,
water-barrier and area-conservation tests remain active. Changed current guides,
TODO and research status distinguish this delivered slice from parent enrichment;
older dated evidence is preserved. All 658 local Markdown file targets resolve,
all 19 changed text files decode as UTF-8, and `git diff --check` passes.

Next: define a parent restriction rule with height/slope tolerances and test
conditioned residuals on the existing 65/129/257 regional windows. Preserve
inherited channels and upstream context rather than rerouting each window in
isolation. Compare complete candidate paths around unresolved crests before
rendering the planned graph as physical rivers. No completed DEM editing is
introduced or planned by this increment.
