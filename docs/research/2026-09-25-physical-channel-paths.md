# Coupled physical channel paths and frozen-grid sensitivity

Date: 2026-09-25. Status: **implemented and measured research prototype; rejected
for production promotion**. This advances B/R48/R32/R02 after the WC1 foundation.
The [main strategy](../strategy/README.md) owns the next decision; the
[benchmark guide](../../benchmarks/evolution/README.md#physical-channel-path-comparison)
owns commands. No normal-generation stage, project format, authored map or
completed build is changed by this experiment.

## Decision

A shared physical representation can reduce grid-direction alignment without
breaking the existing downhill profiles. It cannot, by itself, deliver a
convincing or admissible landscape. All 22 cases still fail the experimental
no-fill policy; 17 also exceed the 30 m sampled cut limit. Long straight reaches,
coarse bends, C0 slope creases and unstable process-grid capture remain.

Keep this implementation as a bounded geometric comparator. Next compare **one
catchment/network-led terrain construction with explicit authoring constraints**;
do not add another floor patch, silently increase cuts, rerun the failed finer
history with a larger budget, or promote this deformation to the editor.

The direction is consistent with the primary
[Génevaux et al. hydrology-based terrain paper](https://doi.org/10.1145/2461912.2461996),
which builds terrain from drainage structure and terrain/river patches. This
prototype is our own mesh-deformation control, not an implementation of that
paper and not a geological or hydraulic simulation. The paper motivates the
next comparison; it does not validate the measurements below.

## Implemented method and boundaries

- Reuse the verified frozen inputs, required-diagonal triangle control, physical
  station sampling, whole-climb metrics and ground rendering from the
  [previous experiment](2026-09-24-frozen-channel-reconstruction.md).
- Keep the entire receiver graph, required edges, heads, junctions, terminals and
  logical-node bed elevations. Only degree-two channel coordinates may move.
  Coast/domain boundaries and graph endpoints remain exactly fixed.
- At each movable node, consider 17 lateral candidates in a fixed original
  corridor. Eight half-relaxed iterations penalize squared adjacent reach lengths
  and squared bilinear source-height departure from the retained bed height.
  The source-height scale is 25 m; displacement is at most 125 m, additionally
  bounded to 0.24 process cells. These are frozen experimental parameters, not
  calibrated erosion coefficients or production regional incision settings.
- Map both terrain and river geometry through the same continuous mesh. Four
  triangle fans per cell avoid a gratuitous diagonal in bilinear cells; in a
  required diagonal cell their centre lies on the required edge. All fan areas
  must remain positive. Fixed outer boundaries and shared triangle edges preserve
  the embedded graph's connectivity and prevent new graph crossings.
- Inverse-map physical queries before sampling the triangle control. Moved channel
  edges therefore retain their linear bed profile, rather than merely displaying
  a smoother line over unrelated ground. Every returned elevation is Float32.
  Preparation and shared-coordinate results are independent of view resolution,
  query order and query partition.
- Preserve geometric topology, **not fixed geographic divides or rerouted
  catchments**. Unselected receiver edges are not enforced channel geometry.
  Signed volume changes from deformation have no erosion/material ledger.
- Keep hard-anchor and cut/fill failures explicit. The cohort has no authored
  anchors; separate synthetic controls demonstrate off-grid anchor rejection.
  Budget checks use all original vertices, original cell centres and displaced
  required vertices against frozen bilinear ground. Their 0.01 m tolerance and
  30 m cut / 0 m fill policy are diagnostic. Passing these samples would still
  not establish a continuous bound or satisfy native regional constraints.

## Frozen-cohort results

All 22 completed states retain all **19,228 required edges and 1,183 complete
head-to-terminal routes** at both 100 m and 25 m physical station spacing plus
vertices. The original repeat remains included; these are not 22 independent
statistical samples. The failed 156.25 m source remains explicitly omitted.
Path lengths and station counts may change; matched edge identities and
head/terminal pairs, not sample counts alone, establish the retained coverage.

| Measure at 25 m stations | Bilinear control | Triangle control | Physical candidate |
|---|---:|---:|---:|
| Unresolved full routes | 842 | 153 | 153 |
| Unresolved among 1,030 nodally nonascending routes | 689 | 0 | 0 |
| Ascent on those 1,030 routes, shared reaches repeated (m) | 40,012.39 | 0 | 0 |
| Unique-network ascent (m) | 36,359.27 | 1,032.47 | 1,032.47 |
| Unique-network length (km) | 14,086.98 | 14,086.98 | 13,893.26 |
| Length within 0.5 degrees of a D8 direction | 100% | 100% | 56.99% |

There are **no newly uphill routes** relative to the triangle control at either
sampling density. The other 153 routes retain their pre-existing nodal climbs;
150 come from current-generator cases and three from the uplift-only control.
Maximum route excursion remains 27.26 m. Reconstructed paths cannot solve that
input-graph infeasibility by changing interpolation alone.

The reduced D8 alignment is a geometric observation, not proof of natural river
shape. Actual-ground images show rounded transitions between some directions,
while long straight reaches and coarse corners remain obvious. The exact 90-degree
rotation control passes for a rotated copy of a synthetic problem. The frozen
70-degree uplift scenario is a different forcing orientation within the same
rectangle, not an exact rotation-equivalence test of the whole landscape.

### Per-case limits

The following cut/fill values are sampled **relative to the original bilinear
field**, not extra incision attributed solely to the path movement. The triangle
control already reaches 89.16 m cut and 0.79 m fill in this cohort. The physical
candidate reaches 89.16 m cut and 14.61 m fill. Both stages need admissibility;
keeping bed nodes does not preserve all the ground between them.

| Case (source cohort / worker) | D8-aligned length | Sampled cut / fill (m) | Unresolved routes |
|---|---:|---:|---:|
| ablations / diffusion-only-seed42-dx625 | 80.8% | 0.48 / 0.34 | 0 / 29 |
| ablations / incision-only-seed42-dx625 | 55.0% | 67.74 / 10.40 | 0 / 50 |
| ablations / uniform-rock-seed42-dx625 | 55.4% | 53.88 / 13.16 | 0 / 46 |
| ablations / uplift-only-seed42-dx625 | 51.6% | 0.96 / 0.87 | 3 / 23 |
| cohort / constant-seed20260902-dx625 | 58.1% | 85.41 / 14.16 | 0 / 51 |
| cohort / constant-seed42-dx625 | 59.7% | 71.32 / 10.35 | 0 / 48 |
| cohort / constant-seed7-dx625 | 65.0% | 68.76 / 10.36 | 0 / 53 |
| cohort / current-generator-seed20260902-dx625 | 68.7% | 8.91 / 4.15 | 52 / 52 |
| cohort / current-generator-seed42-dx625 | 62.2% | 9.60 / 5.30 | 45 / 45 |
| cohort / current-generator-seed7-dx625 | 65.3% | 8.34 / 5.13 | 53 / 53 |
| cohort / reversed-seed20260902-dx625 | 59.4% | 89.16 / 13.01 | 0 / 47 |
| cohort / reversed-seed42-dx625 | 62.6% | 75.58 / 10.91 | 0 / 47 |
| cohort / reversed-seed7-dx625 | 68.1% | 78.39 / 10.57 | 0 / 50 |
| cohort / two-epoch-seed20260902-dx625 | 56.3% | 70.19 / 11.66 | 0 / 54 |
| cohort / two-epoch-seed42-dx625 | 55.5% | 53.16 / 12.48 | 0 / 46 |
| cohort / two-epoch-seed7-dx625 | 63.4% | 48.47 / 13.63 | 0 / 52 |
| extent / two-epoch-seed7-dx1250 | 41.9% | 62.92 / 9.68 | 0 / 205 |
| repeat / two-epoch-seed42-dx625 | 55.5% | 53.16 / 12.48 | 0 / 46 |
| rotated / two-epoch-seed7-dx625 | 46.2% | 41.31 / 14.61 | 0 / 43 |
| spacing / two-epoch-seed42-dx1250 | 52.0% | 72.75 / 9.25 | 0 / 50 |
| spacing / two-epoch-seed42-dx312.5 | 63.9% | 33.07 / 13.11 | 0 / 48 |
| timestep / two-epoch-seed42-dx625 | 54.7% | 53.28 / 12.44 | 0 / 45 |

The smallest fan area ratio is 0.5982 relative to an undeformed fan; no mesh folds
were accepted. Measured maximum movement is 124.51 m in the ordinary/coarse grids
and 74.71 m at 312.5 m spacing because the topology corridor bound activates.
That change in support is recorded rather than hidden as output-resolution detail.
The repeated seed-42 state produces identical geometry and complete profile hashes.

## Receiver/outlet sensitivity

The new diagnostic compares **original frozen receiver graphs**, not a reroute
of the deformed candidate. It selects identical interior coordinates on nested
grids with the same extents, history, seed and forcing orientation. There is no
nearest-node snapping. Terminal shifts are pointwise outlet-location differences,
not an estimate of changed catchment area or a continuous-divide comparison.

Seed 42, two-epoch baseline at 625 m:

| Comparison | Shared stations | Changed downstream direction | Outlet shift over one coarse cell | Changed rectangle exit side | RMS outlet shift |
|---|---:|---:|---:|---:|---:|
| Exact repeat | 12,065 | 0% | 0% | 0% | 0 m |
| 1,250 m process spacing | 2,961 | 53.23% | 14.56% | 3.82% | 6,419.70 m |
| 312.5 m process spacing | 12,065 | 52.84% | 16.90% | 1.43% | 5,199.89 m |
| Finer time/error controls | 12,065 | 1.94% | 0.90% | 0.0083% | 600.08 m |

The time comparison changes **both** maximum step (25,000 to 12,500 years) and
local error tolerance (0.5 to 0.25 m); it is not an isolated timestep-convergence
proof. Large maximum shifts also remain (up to 67.36 km in the spacing pairs).
The algorithm checks compatible domains and nested station grids and rejects
incompatible requests. Rotated forcing and enlarged domains are kept out of the
same-geography pair table; their full path results remain in the cohort above.

## Cost, artifacts and validation

The final measured run completed in 27.20 seconds with 190.41 MiB
process-lifetime peak, including input verification, three samplers at two
station densities, stored per-route measurements, sensitivity and rendering.
Preparation took 0.010–0.116 seconds per case. These are local observations,
not portable limits; the previous full comparison was about 27.4 seconds.

Ignored local results are under `artifacts/physical-paths-final-20260925/`.
`index.html` links paired ground images and case results; completion-last
`comparison.json` contains the source/runtime identity, source hashes, every
summary, measured gates and ten compatible sensitivity pairs. Each case retains
`geometry.npz` with a numeric hash, per-edge/full-route profiles and figure hashes.
Neither source DEMs nor original benchmark artifacts were overwritten. The final
source subsequently received a line-wrap-only lint correction; numerical behavior
and parameters are unchanged. The artifact preserves its actual measured identity.

Regression coverage includes fixed endpoints/junctions, unchanged routing,
monotonicity at 100/25/3 m, retained nodal failures, 90-degree rotation, mesh/query
bounds, continuity, immutable preparation, terrain response, repeated/partitioned
queries, cut/fill and off-grid anchor rejection, exact coverage identities,
artifact publication/repeatability and shared-coordinate sensitivity.
Validation: the full base-environment suite passed **1,659 tests**, with the one
expected isolated-scientific-reference skip, in 362.04 seconds. Full Ruff and
strict Pyright checks passed. The strengthened off-grid anchor test also passed
separately after the full run had already exercised its earlier form. The
187-document inventory and all changed-document local links pass. Paired actual
ground figures were visually inspected; no application UI changed in this batch.

## Next bounded implementation

1. Freeze one public range/valley/lowland fixture with a coast, confluences,
   a protected divide and off-grid height targets. Include a feasible network and
   an intentionally incompatible route. Carry actual native regional cut limits;
   do not substitute the experiment's uniform 30 m policy.
2. Compare one catchment/network-led surface against the frozen triangle and
   physical controls. Construct connected valley cross sections and surrounding
   slopes from a shared network with hard equalities and cut/no-fill inequalities.
   An incompatible route must be rejected or rerouted before fitting ground.
3. Give ridge/divide geography and minimum valley width physical support independent
   of raster output density. Repeat the existing spacing/time diagnostics before
   running a finer history. Explicitly measure rerouted catchment/terminal changes.
4. Accept only after paired landform images, hard constraints, complete route
   coverage, rotation controls, sparse/dense profiles and bounded cost pass.
   Until then keep LE3/WC2 integration, sediment, history controls and zoom jobs
   behind the existing gate. Do not add another production path or compatibility mode.
