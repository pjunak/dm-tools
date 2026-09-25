# Constrained network-led terrain: bounds pass, drainage capture fails

Date: 2026-09-25. Status: **implemented and measured research construction;
rejected for production use**. This completes the bounded B/C comparison selected
after the [physical-path experiment](2026-09-25-physical-channel-paths.md).
The [main strategy](../strategy/README.md) owns the next implementation;
[benchmark instructions](../../benchmarks/evolution/README.md#constrained-network-led-terrain)
own the runnable command. No editor setting, saved project or completed DEM is changed.

## Decision

A surface can be constructed with downhill physical river guides, hard off-grid
heights, a protected divide and the existing regional cut/no-fill limits. That
solves a real limitation of the previous unconstrained deformation. It does
**not** establish that those guides are valley bottoms or that water reaches their
mouths. Independently rerouting the delivered ground reveals new interior sinks
and missed outlets. The comparison records both successful constraints and failed
hydrology; a completed experiment is not an accepted terrain generator.

Retain this bounded solver and fixture as the next construction base. Next test
**lateral valley capture and whole-route feasibility under the same limits**.
Do not add erosion duration, silently deepen cuts, fill depressions, smooth the
displayed lines or promote this candidate to hide the failed capture.

## Basis and construction

[Génevaux et al. (2013)](https://doi.org/10.1145/2461912.2461996) motivate creating
terrain from drainage structure and river/terrain patches. This is a small
project-specific constrained bilinear experiment, not a reproduction of their
algorithm, a hydraulic model or a geological-history simulation.

The immutable physical network has distinct nodes, explicit confluences, directed
acyclic receivers and fixed mouths. Undeclared crossings and overlaps fail.
One shared geometry drives fitting, profiles and map overlays. Coordinates and
widths are metric and independent of viewport pixels.

Let `z` be fitted nodal heights, `s` the fixed broad source, `c` the conservative
native cut envelope and `t` a valley-shaped target. Minimize
`0.5 * sum((z - t)^2)` subject to:

- `s - c <= z <= s`: lower bounds on cuts and upper bounds forbidding fill;
- bilinear interpolation at each hard point equals its target height;
- the directional derivative along every required reach is at most `-0.0005`
  metres per metre; and
- zero cut throughout the protected divide footprint and at the zero-height coast.

A straight reach is split at all cell crossings. Bilinear ground restricted to
one such segment is quadratic, so its derivative is affine. Constraining both
ends bounds the derivative across the entire segment, including humps that
endpoint heights alone miss. Nonnegative bilinear weights likewise extend nodal
height bounds to the continuous field. These are properties of this representation,
not proof that its whole surface drains along the prescribed network.

The native `regional_incision_limit` now has one source owner used by both the
existing regional blend and this fixture. For each cell, take the smallest
full-influence limit of all intersecting region bounding boxes; give each node
the smallest bound of its incident cells. This cannot exceed the native inward
convex blend. The divide uses the same conservative protection. Bounding boxes
and incident cells can overprotect; the experiment never increases a native cap.

The target joins physical valley cross-sections with a 2,400 m support radius
and a smooth finite-support taper. Desired centre depths use 65% of the local
conservative cap. These are experimental shape parameters, not calibrated erosion
coefficients. An initial target defect let a zero-depth coastal endpoint affect
its entire downstream half-plane; compact support removes that defect and has a
regression test.

The existing SciPy dependency supplies
[HiGHS feasibility checks](https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs.html)
and a sparse [trust-constr fit](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-trustconstr.html)
with analytical gradient and identity Hessian. Fixed and unconstrained nodes are
eliminated first. The strictly convex objective gives one mathematical minimizer;
an initial L1 trial had equal-cost solutions differing by 16.33 m after rotation.
The quadratic fit removes that ambiguity in this fixture. No dependency was added.

Limits are 16,384 grid nodes, 2,048 free constrained nodes, 256 network nodes,
4,096 hard heights and 32,768 cell-derivative rows. The fit has a default 20 s
cooperative solver budget and a 500-iteration limit; one native iteration is not
forcibly interrupted. Infeasible, timed-out or incomplete solves publish no surface.
Inward-rounded Float32 bounds are used before solving. Delivered Float32 heights
are checked again: no nodal bound violation, hard-height error at most 0.01 m,
minimum-slope residual at most `1e-5`, and no positive segment derivative above
`1e-10`. Sampled profiles also retain the existing 0.01 m whole-climb tolerance.

## Public fixture and comparison scope

`two-catchment-range-lowland@1` is a 32 by 24 km domain with a broad central range,
two tributary systems, four heads, 15 edges, two coastal mouths, a 2 km protected
divide band and two off-grid hard heights. One fixed, dyadically interpolated
2 km parent supplies exactly the same source field on the nested process grids.
The source uses 1/16 m nodal quantization to avoid artificial coarse flat shelves.

Three native region recipes give full-influence cut limits of 150 m in mountains,
120 m in hills and 15 m in plains, under a 156 m global automatic limit. These are
existing heuristic automatic-cut settings, not measured erodibility. The fixture
intentionally uses them for network construction rather than inventing a larger
experimental allowance. Current product authored-valley semantics are unchanged.

Cases use 1,000, 500 and 250 m process spacing and an exact 90-degree rotation of
the 500 m problem, including source, network, regions, divide and heights. The
valley support radius stays fixed. Native-bound and protection envelopes are
conservative per cell, so their padding changes with process spacing. This is a
sensitivity comparison, not a pure solver-convergence claim.

Source, required-triangle and physical-deformation controls are sampled along the
**same fixed authored network** as the new candidate. Their own required routing
uses the earlier 25 km² threshold, giving 61/118/207 selected edges. On this
fixture those controls coincide in the measured profile and bound results; they
do not create these new off-grid valleys. These numbers are not a direct
before/after rerun of the earlier 22-state history cohort.

## Results

Every case retains all four complete routes and 15 edges. At both 100 m and 25 m
physical profile stations, candidate sampled ascent is **zero**, versus 34.7356 m
of unique-network ascent and two unresolved source routes. Every candidate passes
49,601 cut/no-fill/divide samples on a common 125 m grid and both hard targets.
Maximum pre-sampling hard-height interpolation error is 0.00000191 m. The delivered
500 m raster matches the rotated problem exactly after rotating it back; repeated
fits are byte-identical in the recorded runtime. Ninety-degree agreement is not
proof of arbitrary-angle or cross-platform invariance.

Rerouting uses the actual Float32 ground with raw D8 descent, no depression fill,
no imposed receivers and no forced mouth connections. Both process-grid routing
and a common 125 m evaluation grid are recorded. Heads use the nearest evaluation
node (all four lie exactly on the common grid); a mouth counts only when the route
reaches zero-height coast within a fixed 1,000 m tolerance of its intended outlet.

| Process spacing | Maximum sampled cut | Interior sinks at common 125 m | Interior stations not reaching coast / 48,705 | Heads reaching intended mouth / 4 |
|---|---:|---:|---:|---:|
| Source control, all cases | 0 m | 0 | 0 | 0 |
| 1,000 m | 148.29 m | 3 | 5,872 | 1 |
| 500 m | 149.81 m | 16 | 13,799 | 0 |
| 250 m | 145.90 m | 19 | 14,970 | 0 |
| 500 m, rotated 90 degrees | 149.81 m | 16 | 13,799 | 0 |

All candidates preserve the geographic divide in these checks: zero crossings
among 45,458 tested common-grid interior stations outside the protected band.
The process-grid check is less revealing: it finds only 1/7/8 interior sinks in
the unrotated candidates. Finer evaluation exposes additional between-node
problems. At 500 m all four common-grid head routes stop inland. Positive descent
along a chosen line does not force the transverse gradient toward that line.
The paired route figures make the distinction visible: blue guides, yellow
actual routes and red terminal markers over sampled ground.

The 500 m candidate compared at shared process coordinates:

| Other spacing | Shared interior stations | Changed receiver direction | Terminal shift over one coarse cell | RMS terminal shift |
|---|---:|---:|---:|---:|
| 1,000 m | 713 | 15.29% | 30.01% | 5,829.42 m |
| 250 m | 2,961 | 10.17% | 9.86% | 1,312.45 m |

These are pointwise terminal differences, including interior sinks, not changed
catchment area. A D8 reroute remains a sampled diagnostic; neither 125 m sampling
nor exact longitudinal derivatives certify continuous two-dimensional drainage.

The explicit impossible-route control sets two individually permitted hard
heights in uphill order. All cases reject it without changing either target or
raising a cut limit. Separate controls reject a protected-divide cut,
invalid/crossing/cyclic geometry and incomplete solver results; the whole-cell
derivative control detects and removes a hidden bilinear hump within its bounds.

## Cost, artifacts and validation

The recorded four-case comparison took **4.78 s** and **217.76 MiB** process-lifetime
peak on this machine. Preparation, including controls and fitting, took
0.141/0.260/0.498/0.296 s. The 500 m fit optimizes 270 nodes; the 250 m fit 553.
These observations justify keeping the bounded experiment in Python; they are not
continental-scale performance guarantees or a hard wall-time bound.

Local ignored output: `artifacts/network-surface-final-20260925/`. The HTML gallery
links ground panels, independently rerouted head traces and complete per-case
JSON. NPZ files retain source/target/fitted fields, caps, network and hard inputs.
Completion-last `comparison.json` records source/runtime identity, hashes,
constraint and profile measurements, both routing grids, repeatability, timing,
memory and an explicit **rejected** quality decision. A failed run writes an
incomplete record instead. Existing output directories are never overwritten.
The final run used NumPy 2.5.2 and SciPy 1.18.1. Private campaign maps were not used.

Validation includes three spacings, dense 3 m route probes, 10,000 off-grid native
cap samples per spacing, repeat/query partition equality, rotation, finite-support
coastal regression, fixed-only solves, incompatible requirements, timeout/failure
and complete/incomplete publication. The full base-environment suite passed
**1,674 tests**, with the one expected isolated scientific-reference skip, in
435.38 s. Ruff and Pyright pass. The final focused module passes all 15 tests;
602 changed-document local links and the complete 188-document inventory pass.
Ground and independently rerouted head-route figures were visually inspected.
The isolated history engine was not rerun; this batch does not change it.

## Next bounded implementation

1. Keep this fixture, caps, hard heights, physical network and comparison gates.
   Establish lateral bank-to-bed and confluence support at fixed physical offsets,
   and check whether those inequalities are feasible before constructing a surface.
2. Couple longitudinal and transverse valley shape. Bound transitions into the
   15 m lowland allowance and protected terrain; explicitly diagnose insufficient
   support or infeasible cuts. For automatic guidance compare rerouting/relocation;
   report conflicts for fixed authored requirements. No silent cap relaxation.
3. Require all four heads to reach their mouths, no additional unintended interior
   sinks, no divide crossing and unchanged hard constraints at the common checking
   resolution. Repeat rotation/process-spacing checks and inspect the actual ground.
   Continue to distinguish sampled routing acceptance from continuous guarantees.
4. Only after capture succeeds, extend peak/pass/spur structure and the held-out
   multi-seed/scale cohort, then assess integration with LE3 and WC2. This synthetic
   constraint fit alone cannot close the broader landform-quality milestone.
