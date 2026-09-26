# Cell-interior-safe terrain delivery bounds

Measured 2026-09-27 against baseline `7d5d0de` plus this implementation.
This follows the [head/mouth construction](2026-09-26-valley-heads-and-mouths.md)
checkpoint. It changes experimental raster delivery, retaining the exact local
field, admitted automatic graph, 575 physical bank pairs and authored targets.
Normal workbench generation remains unchanged.

## Decision and outcome

Retain `curvature-bounded-bilinear-cap@1` as a useful delivery component for this
fresh rectangular-divide envelope. It removes the large bound-induced river-head
artifact without returning to node-only protection. **Production remains rejected:**
238 of 575 dense raster bank profiles still fail at 250 m, and coarser grids still
fail capture and longitudinal checks. No output sculpting, time evolution,
groundwater mechanism, dependency, save schema or product setting was added.

The same 32 x 24 km fixture retains its 32-node graph, four heads, two mouths,
two off-grid hard heights, protected divide and zero coast. The 600 m cut ceiling,
2,400 m transition, 120 km3 composition budget, no-fill rule, 1 cm inward-rise
threshold and 100/25 m longitudinal checks are unchanged. Dense banks retain
202 samples per section, at most 2.488 m apart. Routing still samples actual
Float32 delivery on the common 125 m grid, without fill or imposed receivers.

## Why the old bound distorted the terrain

Giving each node the smallest capacity in every incident cell protects the
whole bilinear cell. However, that first-order spatial loss is large. At the
250 m head witness it raises 198.722 m local ground to 253.630 m. The new method
retains the 198.722 m height. Maximum envelope projection across the grid falls
from 93.045 to 18.175 m. The separate hard-height correction remains 118.714 m;
the admitted automatic layout continues to route around that genuine target.

The new bound limits the interpolation error using curvature. Standard linear
interpolation has an error controlled by second derivatives and squared cell
width; see [Patera and Yano's MIT interpolation notes](https://ocw.mit.edu/courses/2-086-numerical-computation-for-mechanical-engineers-fall-2014/fbffccb918511874abd8fd8b3f256688_MIT2_086F14_Interpolation.pdf)
and [Bindel's interpolation/error analysis](https://www.cs.cornell.edu/courses/cs6241/2025sp/lec/2025-03-20.html).
The one-sided construction below is derived for this project's particular cap;
those sources do not establish terrain quality or validate this implementation.

## Interior bound and its scope

Let `d` be distance to the closed protected rectangle, `q = min(d/R, 1)` and
`C = L q^2 (3 - 2q)`, with `L = 600 m` and `R = 2,400 m`. For each cell, calculate
the exact minimum rectangle distance `d_min` and `q_min = min(d_min/R, 1)`.
The radial curvature is bounded above by `6L/R^2 max(1 - 2q_min, 0)`; tangential
curvature by `6L/R^2 max(1 - q_min, 0)`. A coordinate entirely inside its rectangle
slab contributes zero. When the other coordinate is entirely inside its slab,
use the sharper radial bound; otherwise use the tangential upper bound. Call the
two resulting nonnegative bounds `M_x` and `M_y`.

These bounds also hold almost everywhere across the cap's continuously
differentiable rectangle and saturation joins. Along each coordinate, subtracting
`M_i t^2/2` produces a concave function. Its linear interpolant lies below it,
so the one-sided interpolation excess is at most `M_i h^2/8`. Applying the two
positive linear interpolation operators in sequence bounds the bilinear excess:

```text
I(C) - C <= E,       E = h^2 (M_x + M_y) / 8.
```

Subtract `E` from each of the four nodal capacities of that cell. If any resulting
capacity would be negative, replace all four with the cell's true constant minimum
instead. Do not clip negative capacities individually. Finally give each shared
node the minimum of its incident proposals. Bilinear weights are nonnegative, so
these further reductions preserve each cell's bound. These are sufficient safe
bounds; they are not an optimization for the largest possible admitted cut.

Both source and delivered ground share the same bilinear grid. Therefore the
interpolated difference is the interpolation of their nodal differences. Inward
Float32 height bounds ensure every delivered nodal cut is nonnegative and no larger
than its admitted capacity. Hard-height projection retains those same bounds.
Consequently the mathematical bilinear cut respects the cap throughout the cell.
Returning sampled Float32 heights adds rounding; existing terrain tolerances still
apply. This proof does not certify another interpolator, a curved protected shape,
a rotated rectangle within the grid, a native-region envelope or erosion budgets.
The implementation explicitly rejects applying this envelope to fixed-source mode.

The production fixture's maximum interpolation allowance is 78.125 / 19.531 /
4.883 m at 1,000 / 500 / 250 m spacing. Constant handling is needed in 48 / 96 /
192 cells next to the divide. A two-dimensional corner can need a larger allowance;
the separate corner controls exercise that branch.

## Matched measurements

All rows retain the same 575 sections; control is the previous incident-cell
method. Worst rise uses the dense cumulative-excursion definition.

| Spacing | Method | Ordinary failures | Dense failures | Worst inward rise | Endpoint failures | Captured heads | Sinks |
|---|---|---:|---:|---:|---:|---:|---:|
| 1,000 m | Control | 261 | 269 | 180.491 m | 87 | 0/4 | 13 |
| 1,000 m | Curvature bound | 259 | 267 | 180.491 m | 70 | 0/4 | 13 |
| 500 m | Control | 238 | 253 | 105.267 m | 10 | 0/4 | 14 |
| 500 m | Curvature bound | 236 | 251 | 1.361 m | 2 | 0/4 | 14 |
| 250 m | Control | 217 | 241 | 54.062 m | 5 | 4/4 | 0 |
| 250 m | Curvature bound | 214 | 238 | 0.316 m | 2 | 4/4 | 0 |
| Rotated 250 m | Curvature bound | 214 | 238 | 0.316 m | 2 | 4/4 | 0 |

The unchanged local field passes every gate at all spacings. The candidate
preserves all hard-height, divide, coast, no-fill, cap and composition-volume gates.
At 250 m, guides still descend and all 48,705 interior checking samples reach the
coast. Coarse routing remains poor: at 500 m the number missing the coast actually
changes from 12,500 to 12,501. The bound improvement is not a general routing fix.
Quarter-turn delivery matches exactly; this is not arbitrary-angle acceptance.

Candidate composition cuts are 27.587 / 29.848 / 30.314 km3, versus 30.376 km3
locally. These are 125 m trapezoidal differences from initial generated relief,
not sediment conservation or simulated erosion. Repetition matches exactly.

The four paired controls' source, graph, bank coordinates, Float32 raster,
common local ground and local/delivered dense profiles match the previous
`valley-boundaries-evidence-20260926` arrays exactly. Existing fixed/native control
code remains unchanged; the new comparator directly pairs the four relevant cases
rather than nesting and re-running every historical cohort. The full regression
suite still exercises those earlier comparisons.

## Rejected alternatives and remaining defects

- **Nodal cap samples alone:** nodes obey the limit, but interpolation can exceed
  the nonlinear cap between them. The previous ablation counted 196 violations
  at the common 125 m checking locations. It remains a rejected diagnostic.
- **Curvature subtraction followed by clipping negatives to zero:** the linear
  interpolant then rises faster than the quadratic allowance next to a protected
  boundary. A separate regression shows both legal nodes and illegal interiors.
  The whole-cell constant treatment preserves the bound in this situation.
- **Calling tighter bounds sufficient:** rejected by all raster bank cohorts.
  At 250 m the 0.316 m worst rise equals the earlier unprojected-nodes ablation;
  many remaining minima lie away from the intended bed. Smaller amplitude does
  not excuse the 238 failed sections or the two endpoint failures.

Matched before/after profiles and a separate zoomed residual plot were visually
inspected, along with actual routing. They show the severe head defect removed
and the smaller residual rises retained in the evidence. The routing figure
still shows raster direction effects; it is not acceptance of natural landforms.
No dense threshold, denominator, coast tolerance or quality gate was relaxed.

## Reproduction, provenance and validation

Run in the repository's existing Python 3.14 environment:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.evolution.envelope_comparison --output artifacts/my-valley-envelopes
.\.venv\Scripts\python.exe -m pytest tests/test_valley_envelope.py
```

Measured output: `artifacts/valley-envelope-evidence-20260927`. The standalone
comparison took **16.761 s**, peaking at **169.91 MiB** resident memory, with no
concurrent test run. Single candidate deliveries took 0.013 / 0.021 / 0.090 s;
these are bounded-fixture measurements, not world-scale forecasts. Twelve figures,
per-case numeric arrays, matched profiles and saved capacities are included.
The benchmark-source SHA-256 is
`26784d38ef1c622c0a7658b15db0f89db32dbf8a9a7df7f0090a50d4a922512f`.

Capacity checks include 277,248 / 1,108,992 / 4,435,968 samples at the three
spacings, plus the rotated case. They use 19 fractions per axis, including points
very close to cell edges. Five additional geometry controls cover aligned and
unaligned corners, a domain-spanning slab, a partly external footprint and a
2 m thin footprint. Each adds 92,416 samples; no bound violations were found.
Maximum numerical excess is 1.137e-13 m versus the 1e-9 m roundoff guard. These
samples supplement the analytic bound; they are not its proof or extra landscape
acceptance cases.

All 17 saved artifact hashes and 85 array hashes, previous paired controls and
current source/runtime identity were checked. Completion is written last; a
hard-input/execution failure produces `incomplete.json` without completion.
Quality rejection remains a completed, inspectable result.

Sixteen new regression cases pass, covering cell interiors, rotation, the clipped
negative counterexample, exact flat capacity, quadratic allowance convergence,
invalid/work-limited inputs, unchanged hard targets, the actual raster gain,
repeatability, saved evidence and failed publication. Ruff and Pyright pass.
The full repository suite passes **1,750 tests**, with one expected isolated
scientific-reference skip, in 610.90 s. No Tk finalization warnings were reported.
All 713 local links in the 11 changed/new Markdown documents and the complete
195-document inventory pass. No private-world regeneration or isolated history
engine run was needed for this research delivery change.

## Next bounded implementation

Carry forward this admitted local field, the tighter cap, all hard targets and
matched control profiles. Compare one least-change bilinear raster reconstruction
using the existing constrained-surface machinery: add inward-bank derivative
inequalities on each bank-to-bed segment at its cell crossings, alongside the
existing downstream and hard-height conditions. Bilinear height restricted to a
straight line is quadratic; checking its affine derivative at both ends of each
within-cell segment constrains the whole segment, unlike endpoint-only penalties.
Apply the new nodal capacity bounds throughout the solve and recheck the actual
Float32 result, dense banks, guide descent, routing, repeat and rotation.

Keep the solve bounded and distinguish numerical/time exhaustion from verified
infeasibility. If bank/guide inequalities conflict in a cell, retain a localized
conflict witness and use it to decide whether local channel-aligned representation
is needed. Do not loosen the tolerance or introduce another penalty-weight sweep.
A different interpolation rule must re-establish its own whole-cell protection;
it cannot inherit this bilinear proof merely by using the same nodal capacities.
Require held-out landscapes, general orientations and full delivery acceptance
before history coupling, LE3/WC2 or application integration. The authoritative
Float32 DEM contract and Python iteration path remain unchanged.
