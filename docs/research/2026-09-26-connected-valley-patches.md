# Connected valley patches and raster delivery

Measured 2026-09-26 on the public range/valley fixture, from baseline `788913d`
plus the implementation accompanying this report. Model:
`connected-valley-patches@1`. **The bounded comparison is implemented; terrain
quality is still rejected and normal generation is unchanged.** This follows the
[bank-feasibility experiment](2026-09-25-valley-bank-feasibility.md) and the
[input-role reassessment](2026-09-25-groundwater-and-terrain-architecture.md).

## Question and decision

Can an explicit connected valley surface capture water where endpoint-constrained
raster fitting failed, while preserving hard heights, the divide and declared
construction limits? Does that result survive delivery to the authoritative
Float32 raster?

A separately bounded fresh construction captures all four heads on the sampled
local field, with no interior sinks. At 250 m, raster delivery captures three and
leaves one interior sink near a hard-height correction. Coarser deliveries fail
all four. The fixed-source/native-incision control remains rejected. Even the
fresh local field still fails some guide and bank checks: capture alone is not
acceptance. Retain the local construction and explicit coastal transition as
useful components; next test hard-target-aware automatic guide placement and
reconstruction before history coupling or application integration.

## Reproduce and inspect

From the repository root, using the existing base environment:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.evolution.patch_comparison --output artifacts/my-connected-valleys
.\.venv\Scripts\python.exe -m pytest tests/test_valley_patches.py tests/test_valley_support.py tests/test_network_surface.py
```

No external evolution engine, private map or new dependency is required. The
measured run is `artifacts/valley-patches-verified-20260926`; artifacts are ignored
and must be regenerated on another checkout. Each run requires a new directory.
Open `index.html` for the paired ground/routing figures and coastal ablation.
`comparison.json` is written last and contains complete metrics, input roles,
settings, source/runtime identities, rotation and repeat results. Per-case
`fields.npz` retains source/control/delivered arrays, sampled local fields, hard
inputs and prepared geometry with numeric hashes. Failure writes `incomplete.json`
without a completion manifest; a completed quality rejection is a different state.

The final benchmark source hash is
`c635a3889e28ed6def877a708c939ee92562d1d4fb2658bf8b450be13dc08a01`.
The run used CPython 3.14.7, NumPy 2.5.2 and SciPy 1.18.1. This identifies the
numerical source; a later documentation-only commit does not change the experiment.

## Input roles and construction

The unchanged 32 by 24 km fixture has two catchments, four heads, two mouths,
a protected divide and two off-grid hard-height targets. The physical guide
network is identical in every case. Automatic guide relocation is **not yet
implemented**, and none of these runs advances geological time.

| Input | Fixed control | Separate fresh construction |
|---|---|---|
| Broad procedural relief | Fixed starting surface | Generated starting hypothesis |
| Height targets | Final hard targets | Same final hard targets |
| Divide and zero-height coast | Persistent protections | Same protections |
| Physical guides | Fixed comparison geometry | Same geometry; movement remains future work |
| Displacement | Existing native cut limits; no fill | Prospective 600 m cut ceiling, tapered at the divide; no fill |
| Volume | Existing native policy | Prospective 120 km3 construction-cut envelope |
| History | None | None; composition volume is not simulated erosion |

The fresh envelope was declared before its measured comparison and was not raised
to admit failed results. Success there cannot repair a rejection under the fixed
control's native limits. This is pre-generation composition, not modification of
a completed map.

The implementation in `benchmarks/evolution/valley_patches.py`:

1. Densifies each original reach at no more than 250 m physical spacing, producing
   249 segment pieces independently of process-grid spacing. Fixed beds come from
   the existing constrained longitudinal fit. Fresh beds use remaining distance
   to the mouth, initial grade 0.014, a 7 km smooth taper and one shared scale per
   catchment, capped against 55% of sampled initial relief.
2. Analytically minimizes a linear bed plus a rounded radial cross-section along
   each piece, including its endpoints. A 10 m rise at 500 m transverse distance
   defines the curvature. The lower envelope joins incident pieces at confluences;
   compact blending returns to the source by 2,400 m. This constructs a surface,
   rather than adding endpoint inequalities to the previous global fit.
3. Gives each last reach a coastal transition whose bed and transverse relief both
   vanish at the straight zero-height shore. The fixture and its quarter-turn are
   supported; arbitrary curved coastlines are not implemented by this experiment.
4. Applies the construction envelope before computing compact hard-height
   corrections, then checks the corrected field against the same envelope.
5. Samples process nodes and projects disjoint four-node height-pin supports within
   inward-rounded Float32 bounds. Fresh caps are conservatively lowered over each
   node's incident cells so interpolation cannot exceed the nonlinear local cap.
   Report pin, envelope and total delivery corrections separately.

Preparation is bounded to 2,048 pieces and 16 independent pins. Delivery allows
16,384 process nodes. Sampling limits points and point/segment work and streams
local pieces rather than allocating a full pairwise distance matrix. Overlapping
pin cells and unsupported coasts are explicit unsupported-input errors. A
verified pin/bound conflict is distinct from a Float32 numerical delivery failure.

## Results and their limits

The cohort contains fixed/fresh cases at 1,000, 500 and 250 m, plus a 90-degree
rotation at 250 m: eight cases. Both local patch sampling and reconstructed raster
delivery are evaluated on the same 125 m grid (49,601 points), using raw D8 with
no fill or imposed receivers. Heads use their nearest checking node and the
existing 1 km mouth tolerance. These are finite sampled diagnostics, not a proof
of continuous flow or a statistical landscape-quality study.

| Case | Local heads reaching mouth / 4 | Local interior sinks | Raster heads / 4 | Raster interior sinks | Inward uphill sections, local / raster (of 525) |
|---|---:|---:|---:|---:|---:|
| Fixed, 1,000 m | 2 | 2 | 0 | 5 | 105 / 241 |
| Fixed, 500 m | 0 | 5 | 0 | 8 | 99 / 237 |
| Fixed, 250 m | 0 | 5 | 0 | 13 | 94 / 217 |
| Fresh, 1,000 m | 4 | 0 | 0 | 15 | 29 / 239 |
| Fresh, 500 m | 4 | 0 | 0 | 18 | 29 / 222 |
| Fresh, 250 m | 4 | 0 | 3 | 1 | 29 / 209 |

The rotated 250 m cases reproduce these counts. Repeated delivery is exactly
Float32-equal. Maximum rotate-back height differences are 0.0000611 m fixed and
0 m fresh, within the 1 mm gate. A quarter-turn does not establish general-angle
or cross-platform invariance.

All final local/delivered cases pass hard-height, no-fill, protected-height and
construction-cap checks; there are zero cap violations on the common grid. The
runner rejects hard-input or envelope failure before completing a candidate.
Quality checks separately include actual capture, sinks, cross-divide routing,
complete 100/25 m longitudinal profiles, inward bank profiles and bank endpoints.
One of four fresh local guide routes still has sampled rises at 25 m, even though
all four rerouted heads reach the coast. Six local bank endpoint checks fail. At
250 m delivery, one guide route and 14 bank endpoints fail. Do not equate successful
capture along a different path with successful support of every original guide.

Sampled construction-cut volumes (125 m trapezoid quadrature) are about 30.706 km3
for fresh local fields and 25.191 / 28.603 / 29.877 km3 for the three deliveries,
within the separately declared 120 km3 envelope. Fixed local/delivery volumes range
from 6.507 to 8.759 km3. These are composition differences from the broad source,
not a sediment ledger or material removed by an erosion simulation.

### Coastal transition ablation

The 250 m fresh case also runs the same local field without its explicit mouth
transition. All four heads then stop internally: zero captured heads and four
sinks. Restoring the transition gives four captures and zero sinks. Setting the
coast itself to zero was insufficient; the approach to it matters. The paired
`fresh-dx250/mouth-ablation.png` records actual sampled ground and routes.

### Hard-height delivery diagnosis

At 250 m, pin projection changes one raster node by 121.756 m, while the separate
conservative envelope projection changes nodes by up to 93.045 m. The blocked
head stops at (12,000, 4,250) m, upstream of the pin correction neighbourhood;
the local field routes around it. At 1,000/500 m, maximum pin corrections are
519.720/468.074 m. A compact 500 m hard-target kernel is poorly represented by
those coarse nodes, and imposing its bilinear target can disrupt drainage.

The paired figure and correction diagnostics identify a concrete next comparison;
they do not prove that a raster cannot work. Layout, pin support, envelope
conservatism and reconstruction all remain possible contributors. Uniformly
raising resolution or deleting the hard target is not an accepted remedy.

## Failed attempts and corrected assumptions

- Initial sharp-section and untapered-terminal probes left pits. These exploratory
  probes changed more than one parameter and are not a controlled before/after
  result. The final analytic section tests and saved coastal ablation provide the
  reproducible evidence for retained components.
- The initial formal run, `artifacts/valley-patches-evidence-20260926`, admitted
  fresh node cuts but exceeded the nonlinear cap between nodes: 376 / 262 / 210
  common-grid samples at 1,000 / 500 / 250 m. Node bounds alone did not constrain
  interpolated cut beside the divide. The incident-cell lower envelope fixes this
  without increasing the 600 m or 120 km3 limits. A regression checks cell interiors,
  and the runner now refuses hard-envelope violations. Preserve the initial run
  as rejected evidence, not a valid candidate.
- Computing the local pin correction from an unclipped proposal could falsely
  reject a feasible target after the construction cap raised its base. Corrections
  now start from the already admitted field. A forced low-bed regression covers
  this failure, separately from genuine pin/envelope contradictions.
- Rounded local patches still fail under native fixed limits; fresh local capture
  still does not establish all guide/bank conditions. Those remaining failures
  are recorded rather than hidden by the improvements above.

## Validation and next work

Twenty new regression cases cover analytic minimization, manufactured drainage,
source ownership, physical segmentation, hard targets, cell-interior bounds,
repeat/rotation and report provenance, plus unsupported/conflicting/numeric failure
paths and incomplete publication. The final base-environment suite passes
**1,710 tests**, with the expected single isolated scientific-reference skip, in
420.35 s. Ruff and Pyright pass. No isolated history-engine run or private-world
regeneration was needed for this comparator. The 631 local links in changed
documents and the complete 192-document inventory pass, with 11 separately listed
supporting contracts.

The standalone final comparison took 30.512 s with 209.65 MiB whole-process peak
resident memory, including controls, diagnostics, repetition and rendering. This
is a bounded fixture measurement, not a world-scale forecast. The final gallery
has 17 figures; the routing and ablation figures were inspected, and all final PNG
hashes match that inspected run after the final reporting and admission-check changes.

The next bounded B1/B2 comparison should preserve the fixed control and hard targets,
move only automatic guidance within explicit corridors, and test whether valley
layout and pin support can avoid the observed delivery blockage. Measure complete
catchment/guide coverage, bank profiles, cuts, volume and actual rerouting on both
local and delivered ground. If reconstruction remains the blocker, compare one
small constraint-aligned local representation with the current raster. No general
mesh/backend rewrite is approved by this single result.

Accept the construction and delivery together before connecting the two-epoch
reference, broadening to held-out landscapes, or integrating LE3/WC2. Groundwater,
layered canyon erosion and karst remain separately gated process experiments;
they must not absorb unexplained sinks from this open-draining fixture. See
[T09](terrain-method-decisions.md#t09---construct-connected-local-valleys-then-deliver-a-raster)
and the [current strategy](../strategy/terrain-quality.md#b-make-a-river-path-and-its-terrain-agree).
