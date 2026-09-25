# Current development strategy

Re-evaluated 2026-09-24; WC0/WC1 geography checkpoint 2026-09-25. DM Tools is a usable terrain research workbench with
strong numeric/build foundations; believable drainage and connected landform
structure are the next product milestone. See the
[assessment and primary-source research](../research/2026-09-24-progress-and-generation-strategy.md)
for current measurements, alternatives and platform checks. The subsequent
[landscape-evolution research](../research/2026-09-24-landscape-evolution-models.md)
and [detailed implementation plan](landscape-evolution.md) promote a bounded
uplift/erosion history comparison into the generation decision. The
[first implementation](../research/2026-09-24-landscape-evolution-reference.md)
now runs that comparison. The [frozen reconstruction follow-up](../research/2026-09-24-frozen-channel-reconstruction.md)
removes measured interpolation humps on descending paths while preserving their
coverage; direction, authoring and grid-sensitivity gates remain open. No external
engine has been adopted into the application.

The subsequent [world-context research](../research/2026-09-24-world-context-enrichment.md)
and [WC0-WC6 plan](world-context.md) advance retained world import and shared
context from the former final climate phase. [WC0 is now implemented](../terrain-worlds.md):
retained source, explicit spherical placement, continent/island mapping and a
portable World workspace. [WC1 geographic context](../world-context.md) now adds
fractional coverage, connected water and support inspection/export. Exposure and
province inputs are the next foundation.
Physical path/landform acceptance remains a prerequisite for world-informed
production terrain; ecological classifications remain downstream.

This is the authoritative execution order. [TODO](../../TODO.md) remains the
complete grouped backlog; P0 there can mean a prerequisite within a later
feature, not a second concurrent critical path. The
[research status](../research/status.md) distinguishes implemented, experimental
and untested work. Code, schemas, tests and accepted ADRs own current contracts;
contradictions require investigation, not automatic acceptance of a defect.
Dated reports and accepted ADRs remain historical evidence.

## Product boundary

- The editor changes pre-generation instructions over a read-only generated
  reference. A new build applies them. Post-generation modification remains only
  a possible separate tool/module, outside this implementation plan.
- Zoom-driven regional enrichment is a core generation capability. It must
  preserve immutable parent context, overlaps and inherited hydrology; zooming
  the existing image is not that capability.
- Authored geography and a build's Float32 DEM in metres are authoritative.
  Terrain measures, rendered maps, water classifications and GIS products are
  derived and identify their source. Inputs, named seeds, coordinates, algorithms
  and runtime together define reproduction.
- Keep Python and the current local desktop/CLI. Introduce scientific packages
  only for a concrete measured use with platform and license checks. No Rust,
  GPU, web or general plugin rewrite is a prerequisite for better terrain.
- Improve the current implementation without legacy-save support or compatibility
  branches. Intentional algorithm changes can change outputs; retain current
  reproducibility and hard constraints, not old pictures at any cost.

## Development checkpoints

| Milestone | Position on 2026-09-25 | Next exit condition |
|---|---|---|
| Usable authoring and reproducible build | Implemented | Maintain it while changing generation |
| Measured quality baseline | Partial: eight-case profile probe plus paired evolution/control gallery completed | One comparable gallery and structural scorecard, including known failures |
| Terrain-aligned drainage | Frozen-graph reconstruction measured; production not accepted | Shared physical paths, lower grid bias, hard constraints and resolution acceptance |
| Coherent landform families | Partial recipes; two-epoch reference implemented and measured, quality gate open | Related range/pass/tributary/lowland structure that survives multiple seeds and scales |
| Useful zoom enrichment | Experimental | Accepted regional shape, transition and inherited-flow behavior; then viewport scheduling |
| World import and shared context | WC0 plus WC1 geographic coverage, water topology and preview/export implemented | Verified context consumption, geodesic exposure, finite gateways and province inputs |
| World-informed rough terrain and history | Planned, dependent on physical terrain acceptance | WC2/WC3 coarse relief, seasonal runoff and bounded feedback; WC4 reviewed parent |
| Hydrological water and ecology | Later dependent work | Flux/storage/river-size evidence and WC6 ecological layers; shared world context comes earlier |

Do not turn this into one percentage or count passed tests as realism progress.

## Next implementation order

### A. Make quality differences easy to see and measure

Use the existing benchmark modules, not another framework. Extend R25/R27/R41/R43
and the terrain-quality fixtures with:

- the example/regional/authored/outlet cases at seeds 42, 7 and 20260902;
- controlled oblique valleys and flat basins, narrow coasts/islands, a two-peak
  pass, a branching range and a broad lowland reach;
- identical extent, scale, colour limits, lighting and crop for candidate pairs;
- profiles of final ground, terminal/connectivity failures, unresolved routes,
  constraint residuals, incision limits, relief/slope/curvature, peak/pass
  structure and grid-direction bias; and
- generation, review, draw and export time plus process peak, measured separately.

The current eight-case 65-station profile run is the starting evidence, not a
complete acceptance suite. Measure path shape at multiple physical strides and
rotate synthetic terrain relative to the grid. A naturally straight valley must
remain straight. Preserve reference coverage when comparing density choices.
Deliver the paired images, channel profiles and controlled direction tests first;
broader descriptors and interface additions must not delay the first B prototype.
Select a small public bare-earth analogue set with provenance and matched scale;
Earth distributions are comparison ranges, not mandatory fictional geology.

Add paired map comparison and a selected-channel longitudinal profile to the
workbench, with source/result identity, resolution and conflict status visible.
Surface feature-resolution warnings using already recorded output/process
spacing. Support these inspection actions before automatic preview generation;
smaller output rasters still pay fixed routing/water preparation cost.

**First bounded algorithm comparison:** global convergent flat routing versus
current Priority-Flood tie handling, using the existing basin primitive where
appropriate. Check topological order, barriers, retention terminals and both D8
and MFD accounting. Keep an unchanged algorithm control; do not combine this
with a new density default or curve renderer.

**Exit:** one reproducible paired report, known failure locations, explicit metric
units/denominators and a reasoned accept/reject result for the flat experiment.
Do not spend several batches perfecting the dashboard. A useful minimal report
unblocks B; the analogue atlas can grow alongside later quality work.

### W. Establish world inputs, then couple shared context to rough terrain

The [world-context plan](world-context.md) is the detailed R49 feature contract.
**WC0 delivered:** source-preserving SVG import, explicit spherical frame/radius,
continent/island assignment, portable saves and a source preview. The
[implementation report](../research/2026-09-25-world-source-workspace.md) records
validation and limits. The local terrain importer remains a separate operation.
**WC1 geography delivered:** spherical coverage and vector-derived periodic water,
with narrow-strait/island controls, support previews and hashed exports. Next add
verified context consumption, finite gateway support, geodesic exposure and
inspectable province/history hypotheses. Do not infer ocean depth
from width or introduce climate fields without their budgets. These bounded
contracts precede the remaining B/C quality work and require no erosion engine
or private-map import.

After B/C and the relevant LE2/LE3 gates, WC2 supplies rough world relief and
bathymetric context using a tested physical process/domain representation. WC3
updates seasonal climate/runoff against that relief and runs bounded coarse
history feedback. WC4 freezes a reviewed world parent before world-linked regional
jobs. A/C comparison fixtures remain the quality controls for these stages.

This splits the former F phase: geographic placement and shared forcing move
earlier; ecological interpretation stays later. Product sequence is import →
provisional context → rough terrain → climate/history feedback → selected world
parent → detailed continents/regions. Build order is not seven parallel workstreams:
finish WC1 after delivered WC0, resolve B/C acceptance, then WC2-WC4 and D/WC5.

**Exit:** preserved authored vectors and semantic membership, validated spherical
coordinates/topology, explicit hypotheses and one bounded world candidate with
reproducible climate/water budgets. See WC0-WC4 for the separate stage gates;
coordinate success alone does not accept climate or terrain quality.

### B. Make a river path and its terrain agree

R48's required outcome remains the largest immediate generation gain: terrain
and channel paths must agree. Preserve authored constraints and coarse catchment
context, but stop treating every raster edge as the final physical centreline.
One prepared path representation must be shared by source sampling, bed profiles,
actual valley shaping, diagnostics and rendering.

**Implemented comparison:** [LE1/LE2](landscape-evolution.md#first-implementation-checkpoint)
now have an isolated executable reference, analytic controls, paired history
figures and measured public cohorts. Chronology and resistance influence terrain;
conservation alone does not make its continuous river paths acceptable. The
[first report](../research/2026-09-24-landscape-evolution-reference.md) rejects
promotion of the current D8/bilinear reconstruction and records remaining grid
sensitivity. Keep the useful history candidate, not its artifacts as defaults.

**Reconstruction checkpoint:** the [frozen-state comparison](../research/2026-09-24-frozen-channel-reconstruction.md)
now tests identical ground nodes and required graphs across all 22 completed
history/current-generator states. A required-diagonal triangle surface has zero
sampled ascent on all 1,030 nodally nonascending full routes at 100 m and 25 m
stations. All 153 routes with nodal climbs remain unresolved; no route is removed.
This is a numerical control, not an accepted physical river model. Grid directions
stay unchanged, slope creases remain and off-grid authored targets can be violated.
Reconstruction volume changes are recorded separately from erosion.

**Next bounded terrain-quality batch, after WC0/WC1 foundations:** compare the
physical valley/path prototype below against
that monotonic-profile control, and diagnose receiver/outlet sensitivity using
the existing spacing/time states. Preserve the same coverage and native hard
constraint controls. Fix the physical process policy before another expensive
finer simulation or full LE3 integration. The history engine and paired report
already exist; do not build another erosion/report framework or add sediment,
history UI or zoom jobs to avoid this gate. There will be one accepted production
path.

For the path prototype, compare the current D8 control against terrain-guided
subgrid paths inside allowed corridors. Keep exact junctions and coastal/lake
terminals, prohibit unintended crossings/divide violations, and choose a deterministic path from
fixed preparation inputs. Path refinement must not depend on viewport pixels.
Define physical process spacing independently of output resolution (R02), with
explicit minimum feature support and bounded preparation cost. Raising all grids
to the maximum is not the default solution.

Classify whole-route feasibility under existing cut budgets and hard anchors.
Compare rerouting, retention and automatic-head relocation before adding cuts.
Report incompatible authored requirements. Do not repair the finished DEM in
place or silently flatten a protected ridge. An accepted generation stage can
replace obsolete preparation/reconstruction code; it must not leave permanent
parallel legacy paths.

**Exit and decision gate:**

- Synthetic routes declared gravity-drained by this model have no sampled rise
  beyond the declared Float32 tolerance at sparse and dense reference stations;
  all hard anchors, budgets, junctions and terminals pass.
- Compare matched source-to-terminal routes at fixed physical station spacing,
  plus the complete selected network. Report integrated uphill ascent, affected
  length, maximum rise, coverage and unresolved count. Counts per D8 edge cease
  to be comparable when path segmentation changes.
- Target at least a 50% reduction in total sampled uphill ascent on the fixed
  matched feasible cohort, with no new >10 m rise on a formerly feasible route
  and no loss of required catchment coverage. Freeze the cohort and tolerances
  in A before tuning; these are initial project goals, not scientific constants.
- Rotation controls and paired images must show less grid dependence without
  adding arbitrary bends. Document every material per-case regression rather
  than concealing it in an aggregate score.
- Check stage cost, memory and deterministic overlap. Finite profile success
  remains sampled evidence, never continuous-water certification.

If flat handling plus the selected evolution/reconstruction or shared-path
prototype cannot meet the gate, record the failed assumption and compare one
catchment/network-led surface construction before adding another local floor
patch. For changed automatic networks, match authored source/outlet routes and
spatial catchment coverage as specified in LE3; D8 edge counts are not comparable.
D-infinity can be an accumulation comparator; it is not a substitute for channel
geometry. A full irregular/TIN backend requires separate evidence.

### C. Generate one convincing range-to-lowland system

Build on R08/R09/R14/R32/R40/R43: peaks and saddles, subordinate spurs, tributaries,
confined upper valleys and broader lower valleys should describe one landscape.
Keep surface ridges, drainage divides and active channels distinct. Add explicit
pass/per-vertex controls where the fixture requires them; avoid a large new preset
catalogue before one connected system works.

Use LE2/LE3's evolution comparison as the first process-informed shaping
alternative; do not start a duplicate erosion experiment here. Sequential epochs
are preferred for history, with analytical erosion a conditional speed/maturity
alternative. If surface fitting is the constraint, compare a sparse constrained
solve with the current response model and local RBF control. Carry hard equalities,
soft guidance and inequalities separately; recheck routing after any constraint restoration.

**Exit:** a paired public range/valley/lowland gallery across the fixed seeds and
physical scales, preserved inputs, improved peak/pass and drainage structure,
reported slope/relief distributions and measured cost. Reject improvements that
only change tint or high-frequency noise. Select an ADR and dependency only when
one tested candidate wins; do not implement all alternatives simultaneously.

### D. Complete local enrichment, then connect it to zoom

R15/R34 retain the current saved-parent/session foundation. The
[LE6 plan](landscape-evolution.md#le6--parent-conditioned-local-evolutiondetail)
extends it if evolved parents are accepted. First compare oblique
terrain-conditioned detail with a bounded multiscale erosion candidate. Keep
original parent nodes and protected ground, exact shared-coordinate overlap,
request-order independence and bounded working storage. Evaluate downsampled
height change, coarse spectral leakage and slope separately from those exact
properties. Define tolerances before accepting a candidate; the current residual
is still experimental.

Add parent boundary/inflow/outlet context, lake identity and a finer regional
routing stage. Preserving an old channel corridor alone does not establish new
tributary runoff. Use area accounting when no runoff model exists and label it
accordingly. Test adjoining and overlapping windows, whole/partial-cell crops,
coasts, protected areas and revisits. Choose transitions between enriched and
unenriched views without modifying the immutable parent.

**Exit:** numerically and visually accepted regional results plus conserved
inherited flow context. Then add a bounded viewport scheduler with cancellation,
freshness checks and reusable verified sessions. Small physical rivers appear
only when local hydrology is adequately resolved and display scale supports them;
large water survives distant views. Diagnostic tributary visibility already exists
and must keep its different meaning. Recursive child-parent detail is a later gate.
For world-linked regional aging, [WC5](world-context.md) and LE6 additionally
require time-dependent parent boundary/forcing and refinement to the same world
present. Current final-state residual detail does not satisfy historical replay;
never apply the complete history again to an already aged parent.

### E. Add water quantity and richer landform processes

R16/R18/R33 extend contributing area with explicit runoff and the shared WC3
climate adapter when available. Define discharge units and boundary flux before
physical river widths, seasonal/dry channels, braided reaches or deltas. A simple
authored runoff input does not require a complete climate simulation.

Complete controlling-sill/storage and nested lake/outlet semantics before lake
chains. Use the [LE4 comparison](landscape-evolution.md#le4--bedrock-cover-and-deposition-comparison)
for bedrock/mobile sediment with a material ledger before accepting
floodplains/fans; erosion, storage, deposition and export must be accounted for.
Selective geological recipes can follow: resistant caps/escarpments, glacial
valleys, volcanic families, dunes and karst, with their own scales and assumptions.
These remain choices from TODO, not a requirement to simulate every process.

### F. Derive ecological layers and evaluate richer world processes

World placement, ocean context and seasonal climate/runoff are now W/WC0-WC4
prerequisites to world-informed terrain, not deferred until this phase. WC6 uses
their accepted fields for climate/life-zone views, biome suitability and separate
wetland/substrate layers. Retain uncertainty and classification-version metadata.
A bog can occur on a tundra plain; a field is a human land-use decision.

Advanced ocean circulation, plate reconstructions and geological carbon/weathering
cycles remain optional research. The [new world-context review](../research/2026-09-24-world-context-enrichment.md)
compares established and newer tools, including ExoPlaSim and the 2026 Generic-PCM
reduced ocean model. None is an application dependency or a required full-planet
simulation. Select one external comparison only when it answers a measured gap.
The [earlier world-systems inventory](../research/2026-09-04-technology-and-world-systems.md)
remains historical background; current scope and execution order live here.

## How to keep development focused

- Maintain one active product milestone and at most one directly relevant
  comparison. Every experiment names a decision, control, acceptance criteria
  and stopping point. Source inspection is not runtime validation.
- Deliver a visible result with a numerical check. Pair maps at fixed physical
  scale and inspect worst cases, not only a seed average or passing test count.
- Keep finite-water evidence and unresolved budgets explicit. Full composed-field
  bounds remain a separate research track required for stronger certification
  claims, not the universal gate for all generator/editor work.
- Profile the changed workload before more caching, native kernels or GPU work.
  Measure cold/warm latency and total process memory; existing reservations are
  not an OS memory limit. Retain current authored/runtime contracts.
- Extract profile/path preparation from generation and comparison/inspection
  responsibilities from the large UI module when those features change them.
  Avoid a general framework or cosmetic reorganization.
- Remove superseded runtime approaches once a new one is accepted. Keep dated
  reports and ADR history. Add new provenance only for an actual new product.
- End each milestone with an honest result: accepted, rejected, or still
  experimental. Failed candidates should change the next decision, not produce
  an endless sequence of slightly different repairs.

## Technology position

Python remains the iteration language. NumPy, Shapely, Pillow, SVG parsing and
Rasterio/affine are adopted; the [dependency register](../DEPENDENCIES.md) owns
runtime versions/licenses. The [2026-09-24 platform audit](../research/2026-09-24-progress-and-generation-strategy.md#current-tool-and-platform-check)
found compatible Python 3.14 Windows wheels for SciPy and Numba. The subsequent
[reference implementation](../research/2026-09-24-landscape-evolution-reference.md)
installs and executes Landlab/SciPy in a separate research environment, with a
53-wheel hash lock, explicit GPL `py-richdem` and two prereleases. The application
dependency set is unchanged; Numba and Fastscapelib remain uninstalled here.
Fastscapelib lacked a matching wheel in the recorded audit. C++/GPU reference
tools are experiments, not mandatory runtime changes.

R45–R47 govern future native work: identify a dominant kernel, compare complete
workload benefit and Windows packaging, and explicitly choose a kernel bridge or
full Rust migration. Keep array/graph/surface boundaries clear now to limit later
rewrite cost. The [language assessment](../research/2026-09-05-language-and-performance.md)
is historical rationale, not proof that migration is presently worthwhile.
