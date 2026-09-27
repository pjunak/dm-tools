# Hard-target-aware valley layout

Measured 2026-09-26 from baseline `b5dbe27` plus this change. Model
`hard-target-guide-layout@1`, using `connected-valley-patches@1` without changing
its numerical construction. **Automatic guide relocation fixes the 250 m test's
remaining capture and guide-profile failure. Bank shape and coarse delivery still
fail, so this is an experimental component, not an application generator.**

This follows the [connected-patch comparison](2026-09-26-connected-valley-patches.md).
Its original fixed/native and fresh fixed-guide controls are rerun and retained.
The [strategy](../strategy/terrain-quality.md#b-make-a-river-path-and-its-terrain-agree)
owns the remaining acceptance gates.

## What changed

The original generated guide passed about 460 m from a hard-height target. A new
bounded layout stage inserts a detour around that target while preserving every
original network vertex, including all four heads, both mouths and all junctions.
No authored height, source relief, protected divide or coast is moved. The
explicit fresh-construction envelope remains 600 m maximum cut, 120 km3 total
composition cut and no fill. The native fixed-source control remains unchanged.

The implementation requires an explicit boolean mask identifying automatic edges.
A conflicting fixed guide is never silently reclassified. A conservative 1,000 m
clearance around hard-height points is a layout policy for this experiment, not a
new geological exclusion zone or a user-editable project setting.

For each conflicting automatic edge, the candidate family is a quadratic transverse
bump, `p + t*(q-p) + side*A*4*t*(1-t)*normal`, sampled into the actual polyline.
The search tries amplitudes in 100 m steps, up to the declared 1,500 m corridor,
and rejects more than 25% reach-length growth. Stations use at most 250 m along
the original straight-reach parameter; curved-segment lengths can be larger.
The existing patch preparation independently subdivides physical lengths at 250 m.

Whole polyline segments are checked for pin clearance, the metric domain,
protected-divide intersection and river crossings. Original reach ownership is
carried through every inserted node. Tests and reports match the same original
head-to-mouth routes and original vertices, rather than comparing new edge counts
as if they were unchanged physical paths. Search is deterministic and bounded to
64 original edges, 32 amplitudes per side and 256 final nodes. Greedy finite-search
exhaustion is explicitly **not** proof that all possible layouts are infeasible.

The admitted detour changes only original reach 0: maximum displacement 800 m,
minimum pin clearance 1,037.636 m, length 3,807.887 to 4,216.281 m. The network has
32 nodes instead of 17, retaining all original nodes and all 15 original reaches
through ownership mappings. Unique physical network length increases from
60.324 to 60.732 km. No random bending, lowered hard targets or higher cut ceiling is used.

## Reproduce and inspect

Run from the repository root in the existing base environment:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.evolution.layout_comparison --output artifacts/my-valley-layout
.\.venv\Scripts\python.exe -m pytest tests/test_valley_layout.py tests/test_valley_patches.py
```

The measured output is `artifacts/valley-layout-evidence-20260926`; use a fresh
folder for another run. These are ignored local results, not committed terrain.
`index.html` links candidate figures and the nested `fixed-guides/index.html`
control gallery. Both levels have completion-last manifests; failed execution
writes `incomplete.json` and cannot publish a completed parent comparison.

The benchmark source hash is
`35384fa401b323cf26429d748b41eb18ecdff1acb0ec646ed2f2ed58294318de`.
The run used CPython 3.14.7, NumPy 2.5.2 and SciPy 1.18.1. It needs no private
world or isolated history-engine environment. Source/runtime identities, original
and relocated geometry, role masks, reach ownership, hard inputs, Float32 arrays,
settings, complete profiles and artifact hashes are retained. The parent manifest
hashes the complete control manifest as well.

## Measured result

The cohort reruns the eight previous fixed/native and fresh fixed-guide controls,
then four relocated cases: 1,000/500/250 m and a 90-degree rotation at 250 m.
Every field is checked at the same physical 125 m grid, with raw D8 receivers,
no depression filling and no imposed channel receivers. Capture uses the same
nearest-node head sampling and 1 km mouth tolerance as the control. Full guide
profiles use both 100 m and 25 m stations, including vertices.

| Process spacing | Fixed-guide raster: heads / 4, sinks | Relocated raster: heads / 4, sinks | Fixed-guide / relocated unresolved routes (25 m) | Fixed-guide / relocated interior samples missing the coast |
|---|---|---|---|---|
| 1,000 m | 0, 15 | 0, 15 | 4 / 4 | 15,947 / 15,947 |
| 500 m | 0, 18 | 0, 16 | 4 / 4 | 12,540 / 12,500 |
| 250 m | 3, 1 | **4, 0** | **1 / 0** | **1,115 / 0** |

There are 48,705 interior evaluation samples. At 250 m all now reach a zero-height
coast, and none crosses the protected divide under the existing diagnostic.
This is broader evidence than checking four heads alone, but it is not a prescribed
catchment-area or continuous-flow proof. The quarter-turn reproduces the 250 m
counts. Delivered rotate-back heights are exactly equal; maximum transformed
geometry difference is 3.64e-12 m. Repeat construction is exactly Float32-equal.
General oblique rotations, held-out landscapes and cross-platform identity remain
untested here.

Relocated local fields capture all four heads with no sinks and zero unresolved
guide routes at every process spacing. Previously those local fields had one
unresolved route. The 250 m delivered field now passes capture, sinks, both guide
sampling densities, hard heights, protected divide, no fill, cut caps and the
composition envelope. None of the hard-input gates was relaxed.

Bank acceptance remains open. Original support has 525 probes; the longer,
subdivided candidate has 575, because the existing policy includes segment
vertices. Counts below are not matched-pair improvements or equal denominators.

| Field | Inward uphill sections | Bank endpoint failures |
|---|---|---|
| Fixed-guide local | 29 / 525 | 6 / 525 |
| Relocated local | 21 / 575 | 5 / 575 |
| Fixed-guide raster, 250 m | 209 / 525 | 14 / 525 |
| Relocated raster, 250 m | 222 / 575 | 11 / 575 |
| Relocated raster, 500 m | 240 / 575 | 14 / 575 |
| Relocated raster, 1,000 m | 261 / 575 | 90 / 575 |

Composition cut is 30.881 km3 locally and 26.120 / 29.074 / 30.154 km3 in the three
raster deliveries (125 m trapezoid quadrature). These quantities are differences
from initial generated relief, not an erosion or sediment ledger. At 250 m the
maximum pin-projection correction is still 126.313 m, versus the control's
121.756 m: the successful change places the channel away from that correction;
it does not remove the correction or soften the hard target.

The before/after renderer now uses each panel's actual guide geometry and marks
the unchanged hard heights. It cannot show relocated guides over the control and
claim a matched comparison. Both `dx250/before-after.png` and
`dx250/local-delivery.png` were visually inspected; they also show the remaining
D8 trace shape and raster-dependent banks.

## Failed alternatives and interpretation

- A sine-squared detour with the same endpoints, clearance and 1,500 m corridor
  did not clear the target: its endpoint tangent returned too close to the pin.
  The quadratic family admits the 800 m detour within the original envelope. A
  failure of one finite curve family is not an authored-input contradiction.
- An exploratory bed-lifting rule sampled the source-minus-cap envelope at
  0/250/500 m radii, deducted the rounded cross-section height and propagated a
  downstream monotonic height majorant. It reduced some endpoint errors but
  increased local inward failures from 21 to 25, with unchanged capture. It is
  not retained. Radial bound samples and monotonic guide heights do not constrain
  the entire bank after minimum unions, compact blending and cap clipping.
- Moving the guide does not repair 500/1,000 m delivery. Neither increasing cut
  limits nor calling those failures hidden groundwater is justified.
- The unchanged native fixed-source cases remain rejected. Success under the
  separate fresh-construction policy does not retrofit a pass to the native case.

The two exploratory scripts are retained locally under `artifacts/valley-layout-probe-20260926.py`
and `artifacts/valley-envelope-probe-20260926.py`. They are exploratory observations,
not a second controlled acceptance cohort; the committed comparator and final
manifest own the reproducible result. These rejected recipes are not product
fallbacks or compatibility paths.

## Validation, cost and next gate

Sixteen new regression cases cover ownership, fixed input protection, all original
route identities, actual segment clearance/corridors, crossing rejection and
alternate placement, process-spacing/rotation independence, finite search/work
limits, restored delivered capture, preserved bank rejection and artifact/failure
publication. The full base-environment suite passes **1,726 tests**, with the
expected single isolated scientific-reference skip, in 507.76 s. Ruff and Pyright
pass. All eight control cases retain the previous cohort's numerical hashes;
41 artifact hashes and the parent/control manifest link were verified. The 641
local links in changed documents and the complete 193-document inventory pass,
with 11 separately listed supporting contracts. No private-world regeneration or
isolated history-engine run was required for this change.

The complete standalone run, including the eight controls, four new cases,
repetition, profiles, routing and 29 figures, took 47.529 s and peaked at
212.39 MiB resident memory. This is one bounded-fixture measurement, not a
continental performance forecast. No new dependency or application setting was added.

Retain automatic guide relocation as a useful construction component. The next
bounded comparison must resolve complete bank shape at heads/junctions and cap
transitions, with original probes retained and physical reach/length accounting
when segmentation changes. Then isolate local-field success from raster delivery:
if the local banks pass but delivery fails, compare one bounded channel-conforming
reconstruction. Do not re-run ever-larger point-penalty fits or uniform global
refinement. Keep hard targets, fixed/native controls and prospective envelopes.

History coupling, broader landforms, LE3/WC2 and normal workbench generation still
require the complete construction/delivery gates. Groundwater and canyon erosion
remain separate mechanism experiments. See [T10](terrain-method-decisions.md#t10---move-automatic-guides-around-hard-height-targets)
for the retained component and revisit conditions.
