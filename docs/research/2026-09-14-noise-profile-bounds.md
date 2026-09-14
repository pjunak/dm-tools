# Rounded profile bounds through grid strips - 2026-09-14

Status: implemented research comparison. This continues the
[noise-component experiment](2026-09-13-noise-component-bounds.md) by reducing
irrelevant cell work along a path and bounding ordered uphill excursions.
The terrain generator, water sampler, public formats and dependencies are unchanged.
A profile bound for noise still does not bound the complete terrain field.

## Implementation and geometric contract

[noise_profiles.py](../../benchmarks/noise_profiles.py) adds `profile_slabs`,
using the same lattice/fade/interpolation/rounding kernel as `monotone_cell`.
The retained rectangle policies remain useful comparison controls. The new
policy covers the rounded affine coordinate expression
`start + fraction * delta`, with binary64 parameters in supplied closed spans
inside `[0,1]`. It does not substitute interpolation between rounded sample
anchors for the original expression. Coordinates are kilometres; the comparison
field remains `Float32(2000 + 1000 * noise)` metres.

The path is split into grid strips along the axis with the larger absolute delta.
Each strip narrows the possible parameter interval, and its other coordinate
then selects the minor-axis cells. This avoids visiting the whole rectangle
around a long diagonal. Negative/reversed directions, zero deltas, grid contacts,
subnormal movement and rounded coordinate plateaus are covered by regressions.

The [PBRT ray/bounds discussion](https://www.pbr-book.org/4ed/Shapes/Basic_Shape_Interface#RayBoundsIntersections)
provides the geometric slab-intersection reference and explains the need to
account for floating-point error at intersections. This experiment derives its
own outward preimages for the repository's rounded coordinate expression; it
does not adopt PBRT's ray-test implementation or its rendering timings.

## Rounding and inclusion argument

The arithmetic assumptions remain binary64 round-to-nearest with gradual
underflow, followed by the existing Float32 field conversion. Scaled coordinates
must have magnitude at most `2**50`, so grid origins and their next integers are
exactly representable. Larger or nonfinite ranges return an unresolved result.

For a fixed finite start/delta and positive octave spacing, every elementary
rounded operation in the affine coordinate is monotone. Evaluating the two
parameter endpoints with the actual expression therefore bounds the scaled
coordinate for every binary64 parameter in that span. This avoids padding an
already known endpoint value through repeated interval operations. The sign of
the delta determines which endpoint is smaller.

Strip clipping must still invert rounding conservatively. For a rounded value in
`[a,b]`, its unrounded preimage lies between the adjacent floats outside `[a,b]`.
Let `expand` take those adjacent endpoints. For a selected major grid strip
`[j,j+1]`, the sequence is:

1. Expand the scaled strip and multiply by the known positive octave spacing,
   bounding coordinates whose rounded division could land in the strip.
2. Expand that coordinate interval and subtract the known start, bounding the
   rounded product before coordinate addition.
3. Expand the product interval and divide by the signed delta, reversing endpoints
   for negative motion; intersect with the original parameter span.
4. Evaluate both scaled-coordinate ranges over this narrowed span, intersect the
   major coordinate with the selected strip and enumerate the minor cells.

Every arithmetic interval operation rounds outward. A zero delta needs no inverse;
the unchanged parameter span remains eligible. Wide inverse preimages may overflow
to infinity before they are intersected with `[0,1]`; those enclosing intermediates
are allowed and do not become accepted infinite field bounds. Empty intersections
are discarded. The runtime floor convention selects cells at exact contacts;
no interior path position is rejected based on sampled noise heights.

Each actual rounded path point has a major cell in the initial range. Its parameter
survives that cell's inverse strip operations, and its minor cell is in the forward
range of the narrowed span. The existing rounded cell kernel therefore includes its
noise value. Per-strip ranges are unioned back to each original parameter interval
before octave accumulation. The fade, bilinear and Float32 rounding allowances
remain those derived in the preceding report. The inclusion argument is separate
from the finite-reference checks used to find implementation mistakes.

## Complete work limits

Two independent research caps are enforced:

- At most 262,144 major-strip candidates across all parameter intervals and octaves.
  The full count is calculated before strip arrays are allocated. Exceeding it gives
  `slab_budget_exceeded`, the complete requested strip count and unknown cell demand.
- At most 262,144 cell visits after clipping. All cell plans are counted before any
  lattice evaluation. Exceeding it gives `cell_budget_exceeded`, complete strip/cell
  counts and no accepted interval result.

Both failures have zero evaluated cells and no accepted prefix. Counts use Python
integers for large rejected requests. At most 65,536 input spans are accepted.
The limits govern different operations and are not added into a fictitious sample
count. Neither changes production water-profile or wet/dry-network budgets.

## Ordered uphill bounds

Global maxima/minima alone do not describe the direction of a water path.
For complete, contiguous intervals in path order, with field ranges `[low_i,high_i]`,
the maximum later-minus-earlier rise is bounded above by:

`max(0, max_j(high_j - min_{i <= j}(low_i)))`.

The current interval's own lower bound participates because an earlier low point
and a later high point may both lie between its endpoints. Differences are rounded
outward. This permits false positives when an interval's maximum actually precedes
its minimum, but does not exclude a possible rise. Reversing the path changes the
bound. The helper requires complete interval coverage in the supplied path order;
it does not infer that order from a spatial graph.

The harness now reports sampled/reference ordered rise, an upper bound, the gap
above sampled rise and excess over the finite reference. A small global-extremum
gap does not replace these ordered checks. Exhausted trials expose no uphill bound.
These measures are still component evidence, not lake storage, discharge or a
physical outlet decision.

## Experiment and measurements

The comparison uses 108 configurations, each repeated in a fresh process:
seeds 42/20260913; 1/6/12 octaves; roughness .25/.55/.9; X extents .25/2 times the
2 km largest feature; and horizontal, diagonal and oblique directions. Diagonal
Y extent equals X; oblique Y extent is .37 X. Each run compares 1/16/256/4096
subdivisions, all three policies and an independent 65,537-point reference.
The fixed field transform is specified above. Every policy receives the same
endpoint positions and Float32 samples.

| Policy | Trials with bounds | Cell-budget failures | Strip-budget failures |
|---|---:|---:|---:|
| Natural rectangles | 804 | 60 | not applicable |
| Monotone rectangles | 804 | 60 | not applicable |
| Rounded profile strips | 864 | 0 | 0 |

Across 2,592 trials, 2,472 returned bounds. Every completed bound included its
finite reference and every ordered upper bound included the reference rise.
The profile policy used at most 57,342 strip candidates and 65,532 cell visits.
No budget was enlarged. On paired completed trials, profile extrema gaps,
maximum interval widths and uphill gaps were no worse than monotone rectangles
in this matrix; that observation is not a universal strict-improvement claim.

### A broad rough diagonal

For seed 42, 12 octaves, roughness .9 and a 4 km X / 4 km Y diagonal:

| Subdivisions | Rectangle cells requested | Profile strips / cells | Rectangle / profile bound time, ms |
|---:|---:|---:|---:|
| 1 | 22,386,012; rejected | 8,202 / 16,392 | rejected / 44.53 |
| 16 | 1,414,680; rejected | 8,382 / 16,572 | rejected / 39.37 |
| 256 | 106,748 | 11,262 / 19,452 | 221.86 / 45.48 |
| 4096 | 69,628 | 57,342 / 65,532 | 114.27 / 141.29 |

Rectangle timing here means `monotone_cell`; times are medians of the two repeats.
The one-interval request falls from 22.4 million possible rectangle cells to
16,392 clipped visits, a factor of about 1,366. A rejected request performs no
lattice work, so its quick preflight is not an evaluated-baseline timing.

Fitting a coarse request does not make it accurate enough. Profile extrema gaps
at 1/16/256/4096 subdivisions are 868.20/555.50/189.29/28.40 m; ordered uphill
gaps are 1843.27/977.43/378.36/44.71 m. These gaps are upper bounds minus sampled
extrema/rise, not observed errors. At 4096 the maximum local width remains
192.09 m. Clipping removes irrelevant spatial cells, but not the dependence
lost between coordinates inside a cell or between octave extrema.

### Fine-profile uncertainty and cost

At 4096 subdivisions, medians over all seeds/roughness/spans/directions are:

| Octaves | Profile extrema gap, m | Maximum local width, m | Ordered uphill gap, m | Monotone rectangle / profile time, ms |
|---:|---:|---:|---:|---:|
| 1 | 0.00964 | 0.27539 | 0.03259 | 7.07 / 9.36 |
| 6 | 0.19421 | 0.89233 | 0.36530 | 41.38 / 56.07 |
| 12 | 0.68719 | 3.78784 | 1.63654 | 90.39 / 124.04 |

The median gap/width values equal the monotone-rectangle medians at this fine
subdivision. Extra strip planning costs roughly 32-37% in the ratio of these
median timings. It is therefore not a universal faster replacement for box
bounds. At fine scales, many spans already occupy a small rectangle.

The worst profile extrema gap at 4096 is still 44.81 m, for seed 20260913,
12 octaves, roughness .9 and the long diagonal. Its maximum interval width is
193.79 m, and its uphill upper bound of 820.38 m exceeds sampled uphill rise
by 66.43 m and the finite reference rise by 58.88 m. A small median extrema gap
would hide this case. Local widths also contain genuine within-interval relief;
they are not pure numerical error estimates.

Policy timings are measured inside each fresh worker, including bound planning
and enclosure work. The order is fixed natural/rectangle/profile, not randomized,
so initialization/cache/order effects remain. Point samples, ordered-rise
summarization and reference checks are outside the bound timer. This is an
isolated component comparison, not generation or export latency. Process peak
resident memory across whole workers is 72.48 MiB median / 129.91 MiB maximum;
it cannot be attributed to one policy.

## Validation and provenance

The new regressions cover rounded grid contacts, reversed/vertical/constant
paths, adjacent-float and subnormal movement, large-origin cancellation,
independent dense/random inclusion, input immutability, batching/order invariance,
complete slab/cell preflight, unsupported coordinates, ordered rise within one
interval and real policy dispatch through the subprocess runner. The combined
noise suites pass 119 checks, including the earlier exact-rational kernel tests.

The full repository suite passes: **642 tests in 286.13 seconds**.
Ruff and strict Pyright pass. There are no runtime changes, dependency additions,
format migrations, private project edits or visible workbench changes.

The matrix completed 216 fresh-process runs with identical evidence hashes for
each repeated input. Against the corrected 2026-09-13 matrix, all 1,728 retained
rectangle trials match every pre-existing evidence field, including sample/bound
hashes, cell counts and extrema. The additional ordered metrics and schema fields
are intentionally excluded from that old-field comparison. This verifies that
extracting the shared plan evaluator did not change the controls.

Reproduce with the command in the [benchmark guide](../../benchmarks/README.md#procedural-noise-component-and-profile-bounds).
Report schema is version 2, with `rounded-cell-value-noise@1` and
`rounded-slab-noise-profile@1`. The environment is Windows 11 / AMD64,
CPython 3.14.7 and NumPy 2.5.2. Runtime package fingerprint remains
`f85b589b7da950e4e78994c6905fae708ad332ab6298e65fa96abe0765b20b44`.

Local evidence under ignored `artifacts/`:

| Artifact | SHA-256 |
|---|---|
| `noise-profiles-matrix-20260914.json` | `5b5c70e564789e56b53d14ee2d4e71a83e5eec597227b9e7a922661f1bcbc98b` |
| `noise-profiles-summary-20260914.json` | `a370e93000ebadb69f2dee042f789bdbf240f09cd6fa33e2cbc89afad29f2924` |
| `analyze-noise-profiles-20260914.py` | `49880394149b126256a3d10eea740cc5d32830fda75cf3c25cead5230f770640` |

The matrix also records SHA-256 values for all three benchmark modules and checks
source identity again before marking completion. The earlier one-case profile
pilot preceded the final monotone endpoint-range calculation and is not the
measurement source for this report. The previous report's mislabeled initial
matrix remains invalid; only its corrected final matrix supplies the controls.

## Decision and next work

Retain the strip method as a bounded research option for broad paths. It resolves
this comparison's rectangle-work exhaustion, but pays overhead on fine spans and
does not sufficiently tighten rough-field bounds by itself. Runtime water
sampling therefore keeps its present policy and budgets.

The next experiment should compare cheap rectangles on short spans with clipped
strips on broad spans, then refine only where conservative local/ordered bounds
remain too wide. Keep the original rounded path expression, account for every
pending interval before evaluating a refinement wave, and report budget or
precision exhaustion explicitly. Compare work, memory and uncertainty against
these uniform controls before selecting a stopping rule.

Keep the full-field contract open in [TODO](../../TODO.md): correlated octave
ranges, within-cell path correlation and complete coast/region/constraint/profile/
incision composition remain. The next stopping-rule experiment must account for
local interval and ordered-rise uncertainty, complete work limits and coordinate
rounding. A conservative bound that is too loose can remain unresolved; it must
not turn into permission to clear an unchecked path.

Larger authored water projects, export/scratch costs, controlling-sill/storage
semantics and lake chains remain in the broader implementation plan. No private
Tharkeniss Veld project or workbench flow was changed in this research slice.
