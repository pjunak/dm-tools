# Bound-driven noise-profile refinement - 2026-09-16

Status: implemented research comparison. This follows the
[rounded strip experiment](2026-09-14-noise-profile-bounds.md), adding cheap
rectangle selection on short spans and refinement driven by enclosing bounds.
The complete terrain field and runtime water-clearance policy remain outside
this experiment. It does not change generated maps or introduce dependencies.

## Geometry selection

[noise_profiles.py](../../benchmarks/noise_profiles.py) adds `profile_hybrid`.
For each parameter interval and octave, use its rounded coordinate rectangle
when the minor axis intersects at most two cells. Otherwise use the existing
major-strip clipping. The major axis is still the one with the larger absolute
path delta. A broad horizontal/vertical path therefore avoids strip overhead,
and a long diagonal still avoids enumerating its surrounding rectangle.

This selection uses geometry only. It does not inspect noise heights, predict
convergence from slopes or drop possible cells. Both paths feed the same
rounded lattice/fade/bilinear kernel, with the original affine expression
`start + fraction * delta`. Coordinate bounds use the monotonicity of that
binary64 expression; clipping uses the outward inverse operations documented
in the preceding report. The hybrid result may be wider than the clipped
result, because a short rectangle can contain positions outside the path.
It is a work/tightness tradeoff, not an assumption that their bounds are equal.

All selected strip candidates are counted before strip-array construction;
all cells are counted before lattice evaluation. Profile-policy counts also
distinguish the number of rectangle versus clipped interval/octave plans. Zero remaining
budgets are supported: they can reject a full request, while a hybrid plan
that requires no strips can still run with a zero strip allowance.

## Refinement and the acceptance contract

[noise_refinement.py](../../benchmarks/noise_refinement.py) starts with the
complete parameter span `[0,1]`. It bisects selected spans at global dyadic
fractions, retains the other spans and their bounds, and evaluates only new
midpoint samples. It never reconstructs a subpath by interpolating rounded
spatial anchors. A complete current partition always covers the original path
in order. An independent reference is evaluated by the harness, never read by
the refinement routine.

For interval `i`, let `[L_i,U_i]` enclose all rounded-path field values, and
`a_i,b_i` be its endpoint Float32 samples. The local extrema gap is

`max(0, min(a_i,b_i) - L_i, U_i - max(a_i,b_i))`.

This bounds how far an unseen trough or peak can fall outside that interval's
endpoint height envelope. It is not a pointwise linear-interpolation error or
the total elevation change within a span. A long monotone slope may have a
small local gap and a large true height range.

The complete profile also retains the ordered-rise bound from the preceding
experiment:

`R_upper = max(0, max_j(U_j - min_{i <= j}(L_i)))`.

The sampled rise gives a lower bound `R_lower` on the actual maximum
later-minus-earlier rise. Sample differences are rounded downward, while
upper bounds and their gaps are rounded upward. The result is accepted only
when both the maximum local gap and `R_upper - R_lower` are at most the
requested tolerance. The local condition also bounds the discrepancy between
sampled and global extrema. A Float32/interval-rounding floor can prevent a
small requested tolerance from being met.

When the ordered gap is too large, prefix minima identify possible high
intervals and suffix maxima identify their possible earlier low intervals.
Refine both contributors, as well as every interval with an excessive local
gap. For example, lower uncertainty of .75 m and upper uncertainty of .75 m
can each pass a 1 m local threshold while leaving a 1.5 m uphill gap. Refining
only the high interval would keep the loose earlier lower bound in place.
Possible rise within a single interval remains included.

`adaptive` refines only this selected set. The `uniform` control bisects the
whole current partition if the same acceptance test fails. Both start from
the same root and use the same tolerance, arithmetic and complete-work limits.
The independent 65,537-point reference checks inclusion, shared sample bytes,
local extrema misses and ordered-rise misses only after a result is accepted.
Finite-reference agreement tests the implementation; the enclosure argument
and outward arithmetic establish the stated bound under their assumptions.

## Cumulative work and unresolved outcomes

Each refinement trial has independent cumulative caps:

- 262,144 evaluated enclosure-cell visits, including every superseded parent wave;
- 262,144 allocated major-strip candidates, including preparation of a final
  wave that later fails its cell budget;
- 65,536 sampled parameter positions, retaining prior samples;
- depth 16 from the original parameter span.

The new sample count is checked before bound evaluation. The complete strip
request must fit before strip arrays are built, and the complete cell request
must fit before any new lattice values or midpoint heights are evaluated.
No partial pending wave is installed. These are research budgets, not
production water-network or shoreline caps. A one-shot uniform subdivision
uses its own per-request budgets and must not be treated as an equal-total-work
adaptive comparison; the uniform-refinement control accounts for parent work.

Results distinguish cell, strip and sample exhaustion, depth exhaustion,
unsupported coordinates and coordinate/parameter precision exhaustion. Equal
rounded spatial endpoints imply a constant coordinate range; a required split
there cannot improve this interval kernel and is reported unresolved. Depth 16
keeps all fractions on the independent reference grid and is an explicit
experimental resolution limit, not a claim of physical convergence.

Only `tolerance_met` returns an accepted complete profile. Failure returns
`accepted: null`, cumulative work and diagnostic metrics from completed waves.
A requested count is unknown when the corresponding later planning stage was
not reached; for example, sample exhaustion does not invent a cell estimate.
Unresolved outcomes must not be interpreted as no barrier or no uphill segment.

## Comparison and measurements

The matrix contains 72 input configurations, each repeated in a fresh process:
seeds 42/20260913, 1/6/12 octaves, roughness .55/.9, X extents .25/2 times the
2 km largest feature, and horizontal/diagonal/oblique directions. Diagonal Y
extent equals X; oblique Y extent is .37 X. Roughness has no effect on the
one-octave field. Unlike the preceding matrix, this one omits roughness .25;
its aggregate extrema statistics therefore describe a different distribution.
The comparison field remains `Float32(2000 + 1000 * noise)` metres.

Each of 144 workers runs all four one-shot policies at 1/16/256/4096 subdivisions,
then the three refinement controls at 1/.1 m tolerance. This produces 2,304
one-shot trials and 864 refinement trials. The 1,728 retained natural/rectangle/
strip trials match every pre-existing evidence field in the preceding matrix,
including bound/sample hashes and cell counts. All repeated input/evidence
hashes match.

### Geometry cost at 4096 subdivisions

Medians over this matrix, in milliseconds per one-shot enclosure:

| Octaves | Monotone rectangle | Strips | Hybrid |
|---:|---:|---:|---:|
| 1 | 6.65 | 9.01 | 6.62 |
| 6 | 39.43 | 53.46 | 39.46 |
| 12 | 91.39 | 125.90 | 91.80 |

Hybrid removes roughly 26-27% of the strip-policy time at this subdivision and
runs close to the rectangle control. Both strip and hybrid policies fit every
one-shot request; each rectangle policy still rejects 40 of its 576 requests.
Hybrid is not universally tighter: its short rectangles trade some path
correlation for less planning. In accepted adaptive pairs, hybrid and strips
have median cell/sample ratios of 1.0, while the median hybrid/strip time ratio
is .814, about 19% less time. Their accepted sets coincide in this matrix.

### Acceptance under equal cumulative budgets

The following counts use distinct input/tolerance combinations, excluding the
second repeat. Each row has 24 input configurations.

| Octaves | Tolerance, m | Uniform hybrid accepted | Adaptive strips accepted | Adaptive hybrid accepted |
|---:|---:|---:|---:|---:|
| 1 | 1 | 24 / 24 | 24 / 24 | 24 / 24 |
| 1 | .1 | 20 / 24 | 24 / 24 | 24 / 24 |
| 6 | 1 | 22 / 24 | 24 / 24 | 24 / 24 |
| 6 | .1 | 8 / 24 | 14 / 24 | 14 / 24 |
| 12 | 1 | 6 / 24 | 10 / 24 | 10 / 24 |
| 12 | .1 | 0 / 24 | 3 / 24 | 3 / 24 |
| **Total** | | **80 / 144** | **99 / 144** | **99 / 144** |

Adaptive hybrid accepts 19 additional input/tolerance combinations without
losing any accepted uniform case. All accepted results enclose the finite
reference and satisfy both local and ordered checks. Including repeats, the
288 trials per policy have these outcomes:

| Policy | Tolerance met | Cell limit | Strip limit | Sample limit |
|---|---:|---:|---:|---:|
| Uniform hybrid | 160 | 120 | 0 | 8 |
| Adaptive strips | 198 | 18 | 72 | 0 |
| Adaptive hybrid | 198 | 90 | 0 | 0 |

Removing strip overhead does not by itself rescue the remaining high-detail
cases: they subsequently hit the cell cap. Depth/precision exhaustion are
covered by regressions but did not occur in this matrix.

### Paired work and timing

Compare only cases where both adaptive hybrid and uniform hybrid met the same
tolerance. Median adaptive/uniform ratios are:

| Octaves | Tolerance, m | Cell visits | Sample positions | Total refinement time |
|---:|---:|---:|---:|---:|
| 1 | 1 | .532 | .535 | .827 |
| 1 | .1 | .649 | .649 | .870 |
| 6 | 1 | .282 | .276 | .484 |
| 6 | .1 | .298 | .296 | .404 |
| 12 | 1 | .472 | .367 | .642 |

There is no paired successful twelve-octave/.1 m group: uniform never met that
target. Do not compare medians of different accepted subsets as if they were
paired speedups. At six octaves, the paired comparison saves about 70-72% of
cell work and 52-60% of refinement time for these inputs.

For the concrete seed-42, six-octave, roughness-.55, 4 km X / 4 km Y diagonal
at 1 m tolerance, uniform hybrid uses 200,616 cell visits, 16,385 samples and
365.48 ms. Adaptive hybrid uses 50,615 cell visits, 3,942 samples and 116.20 ms.
Adaptive strips uses 50,381 visits and the same sample count, but 48,859 strip
allocations instead of hybrid's 762, taking 144.16 ms. Times are medians of the
two repeats, not a production generation-speed claim.

At twelve octaves on the same case, adaptive hybrid has spent 249,902 cell
visits with 2,049 samples when its next full wave would require 319,497 total
visits. It stops at the 262,144 cap. The last complete partition still has an
8.16 m local gap and a 10.39 m uphill gap; it is diagnostic only. Coarse waves
repeat many high-frequency cell visits before the bounds become selective.
This motivates reuse/tighter correlation, not a larger hidden allowance.

Timing order is fixed, not randomized: natural/rectangle/strips/hybrid for
one-shot bounds, then uniform hybrid/adaptive strips/adaptive hybrid per
tolerance. Initialization/cache/order effects remain. Refinement timers include
planning, all enclosure work, new samples, partition updates and stopping
checks; independent reference checks are outside them. One-shot timers include
only planning/enclosure and must not be equated with total refinement latency.
Worker peak resident memory is 98.38 MiB median / 131.04 MiB maximum across the
whole comparison; it is not a per-policy memory attribution. No full terrain
build, export or workbench latency is measured here.

## Validation and provenance

The focused noise suites pass **165 tests**, including 46 new regressions.
They cover geometry dispatch, mixed-plan preflight, rounded/reversed/nearby-float
paths, negative/zero field amplitude, dense inclusion and both sides of shared
interval boundaries, original
parameter preservation, both contributors to a hidden rise, complete cumulative
cell/strip/sample failure, exact-budget replay, depth/precision failures and
CLI acceptance/unresolved evidence. Ruff and strict Pyright pass.

The full repository suite passes **688 tests in 433.68 seconds**. The 46-test
new suite was also rerun after tightening shared-boundary checks. All 164 local
Markdown links in changed files resolve; the final diff has no whitespace errors.

The completed matrix confirms all old control fields remain unchanged and all
source fingerprints still match. Research report schema is version 3, adding
`rounded-hybrid-noise-profile@1` and `bounded-noise-profile-refinement@1`.
Runtime algorithms and public project/build formats remain unchanged. The
runtime package fingerprint is still
`f85b589b7da950e4e78994c6905fae708ad332ab6298e65fa96abe0765b20b44`.
The environment is Windows 11 / AMD64, CPython 3.14.7 and NumPy 2.5.2.

Reproduce with the command in the [benchmark guide](../../benchmarks/README.md#bound-driven-noise-refinement).
Local evidence is stored under ignored `artifacts/`:

| Artifact | SHA-256 |
|---|---|
| `noise-refinement-matrix-20260916.json` | `a6e336c2106a3077132297d4dcbb45fe2df7061864a41aaedae45c89c9402533` |
| `noise-refinement-summary-20260916.json` | `321c852bcf62bef0915ea3c570a081028bdecd0a643a5f582fd8e6a00917d628` |
| `analyze-noise-refinement-20260916.py` | `ce975ab9cb1cfffbc357a44264642ce7238ac1461137025387385c69f1357e16` |

The matrix records SHA-256 identities for all four research modules and checks
them again before marking completion. Its retained controls are compared with
the completed 2026-09-14 profile matrix, not an informal pilot. No private
Tharkeniss Veld data, runtime map output or external dependency was changed.

## Decision and next work

Keep hybrid geometry and bound-driven refinement as the preferred next research
baseline. They remove most fine-strip overhead and solve more of the measured
accuracy requests within the same cumulative limits. They do not solve the
remaining rough/high-detail cases or constitute a runtime water-clearance rule.

Next, measure retaining useful parent/octave/lattice work across waves and
intersecting child bounds with retained parent bounds. Compare that reuse with
tighter within-cell and cross-octave correlation; count all preparation and
retain explicit unresolved results. Exact constant-coordinate cases and the
Float32 rounding floor also need deliberate treatment before requesting smaller
tolerances. These are logged in [TODO](../../TODO.md).

Compose coast weights, regional/constraint blends, longitudinal profiles and
incision before adopting a full-field stopping rule. Distance/exponential
rounding and whole-network cost still need their own evidence. The broader
[implementation plan](../strategy/README.md) retains sill/storage semantics,
reviewable river networks and richer authored ridge/valley controls.
