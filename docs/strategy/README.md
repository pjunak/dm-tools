# Current development strategy

Re-evaluated 2026-09-25 after the failed bank-support comparison and the
[groundwater/canyon and architecture review](../research/2026-09-25-groundwater-and-terrain-architecture.md).
DM Tools is a usable terrain research workbench with strong numeric/build
foundations; believable drainage and connected landforms remain the next milestone.
The [method decision register](../research/terrain-method-decisions.md) now records
failed approaches, causes, retained work and replacement gates. The next batch
separates authored requirements from generated guesses and constructs connected
local valleys, then tests terrain/network co-evolution. Groundwater is a bounded
mechanism experiment, not a remedy for unexplained surface sinks. No external
erosion or groundwater engine has been adopted into application generation.

The [world-context research](../research/2026-09-24-world-context-enrichment.md)
and [WC0-WC6 plan](world-context.md) advance retained world import and shared
context from the former final climate phase. [WC0 is now implemented](../terrain-worlds.md):
retained source, explicit spherical placement, continent/island mapping and a
portable World workspace. [WC1 geographic context](../world-context.md) now adds
fractional coverage, connected water, shared-edge openings, shore distance and
directional water exposure with verified inspection/export/reopening. Authored
[province/default hypotheses](../world-geology.md) now have their own portable
recipe and editor. [Bathymetry](../world-bathymetry.md) now supplies an explicit
shelf/slope/basin hypothesis with its own generation, error/support views and
verified products. Water-piece face incidence, source verification and explicit
precision support are now implemented. Return to B/C physical paths and landforms.
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
| Terrain-aligned drainage | Native bounds, hard heights and bank endpoints pass in feasible cases; cross-sections and capture fail | Input-role audit, connected local patches and separately bounded co-evolution; actual capture and process-grid stability |
| Coherent landform families | Partial recipes; two-epoch reference implemented and measured, quality gate open | Related range/pass/tributary/lowland structure that survives multiple seeds and scales |
| Useful zoom enrichment | Experimental | Accepted regional shape, transition and inherited-flow behavior; then viewport scheduling |
| World import and shared context | WC0 plus WC1 geographic coverage, water topology, edge widths, shore distance, directional exposure, verified products, authored geology recipes, bathymetric hypotheses and water-piece incidence implemented | B/C terrain acceptance; later physical forcing and conservative transport |
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
with narrow-strait/island controls, support previews, hashed exports, verified
reopening, shared-edge measurements, shoreline distance with an error bound and
eight-direction water exposure with mixed-cell support. **WC1 geology inputs
also delivered:** a separate recipe/editor with cross-label and seam provinces,
explicit overlap/priority and independent ages/duration at one common present.
**WC1 bathymetry also delivered:** explicit ocean selection, shelf/slope/basin
inputs, conservative depth/error fields and independent editor/result contracts.
**WC1 water-piece incidence also delivered:** separate pieces and finite shared
intervals, source-verified context v4 and unresolved-connectivity support. Return
now to B/C physical-path and landform acceptance for rough terrain. Later transport
must admit that support and establish conservative capacity/flux contracts.
Do not infer ocean depth from width or introduce climate fields without budgets. These bounded
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

**Measured checkpoint:** LE1/LE2 chronology is useful, but interpolation and grid
sensitivity prevented acceptance. Frozen triangles removed sampled humps on
nodally descending routes without resolving D8 shape or general authoring. The
coupled path/ground deformation then improved direction alignment but failed
cut/fill admission. The constrained network fit and bank support preserve native
limits and hard targets in feasible cases, yet actual drainage still fails: zero
of four heads reaches its mouth, and at 250 m bank support increases sinks from
19 to 30. These are rejected methods, not rejected terrain features. Full evidence
and the different comparison denominators are in
[T04-T08](../research/terrain-method-decisions.md#t04---evolve-a-landscape-then-deliver-its-d8-nodes-bilinearly).

**Next bounded batch (B1):** first label fixture inputs as authored hard targets,
persistent boundaries, initial relief, forcing or soft/generated guidance. The
[existing role contract](landscape-evolution.md#authored-intent-and-geographic-boundaries)
already requires this distinction. Keep the current fixed-source/native-cap fixture
unchanged as a control. Construct river-aligned local patches with continuous
cross-sections, explicit confluences and sea-level mouth transitions. Test both
the local field and its actual Float32 delivery using the current reports.
For admitted feasible cases require all four heads to reach their mouths and zero
new unintended interior sinks relative to the original source, at common 125 m
checking. Keep hard heights, divide, cut/no-fill limits, repeat, rotation and
process-spacing checks. Proven conflicts stay visible; solver failure is not an
infeasibility proof.

Add a separately identified **fresh-construction comparison**: initial procedural
relief and automatic guides may evolve inside declared corridors/envelopes while
genuinely authored requirements remain fixed. Native automatic-incision ceilings
remain unchanged for that mechanism; a construction/history envelope must be
specified before running or tuning the new case. Report composition displacement
and volume separately from simulated erosion. Do not call a changed fixture a pass
on the old one. Compare bounded rerouting/relocation where automatic guidance is
incompatible, retaining catchment coverage and intended terminals.

**Following decision (B2):** connect a successful local construction to the existing
two-epoch reference so relief and the automatic network can evolve together before
publication. If the local field passes but raster delivery alone fails, compare one
bounded channel-conforming mesh/reconstruction; do not immediately rewrite the
whole backend. Use held-out seeds, oblique orientation, process spacing, hard
constraints and actual-ground inspection. Broaden landforms or integrate LE3/WC2
only for an accepted capability. More endpoint penalties, hidden fill, larger
undeclared cuts and uniform whole-world refinement are not the next strategy.

The [reassessment](../research/2026-09-25-groundwater-and-terrain-architecture.md#implementation-sequence-and-stop-rules)
also specifies G1 groundwater capture and C1 layered/laterally eroded canyons after
this surface decision. These small mechanism comparisons do not require full karst,
chemistry, a history UI or global groundwater. Keep authored inputs, evolving
process state and frozen delivery as separate responsibilities inside the current
Python layers. The authoritative DEM and editor workflow remain unchanged.

The physical-path comparator now supplies terrain-guided subgrid paths inside
bounded corridors. A production candidate must additionally satisfy the native
constraints and fixed geographic divide policy. Keep exact junctions and
coastal/lake terminals, prohibit unintended crossings/divide violations, and
choose a deterministic path from fixed preparation inputs. Path refinement must not depend on viewport pixels.
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

The failed evolution/reconstruction and shared-path gates activated the bounded
network-led construction above. Longitudinal and bank-endpoint constraints now
pass in feasible cases; the next local representation must establish inward
cross-sections and actual capture, not just more successful point constraints.
For changed automatic networks, match authored source/outlet routes and spatial
catchment coverage as specified in LE3; D8 edge counts are not comparable.
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

R16/R18/R24/R33 extend contributing area with explicit runoff and the shared WC3
climate adapter when available. Define discharge units and boundary flux before
physical river widths, seasonal/dry channels, braided reaches or deltas. A simple
authored runoff input does not require a complete climate simulation. The G1
reference tests recharge, storage, stream exchange and groundwater capture after
B's surface decision. Its small analytic/density experiment can precede this
production phase; physical adoption still needs the combined water ledger.
Surface and subsurface divides are separate. K1 later tests explicit losing-stream
and spring connections in suitable substrate, preserving real closed basins.
These mechanisms cannot excuse failed open-draining controls.

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
- Update the [method register](../research/terrain-method-decisions.md), dated
  evidence, status and TODO whenever a substantial candidate is tested. Preserve
  why it failed, the control, reusable parts and the next decision.
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
53-wheel hash lock, explicit GPL `py-richdem` and two prereleases. SciPy is now also
an application dependency for spherical shoreline queries;
that adoption does not include Landlab or the reference stack. Groundwater,
lateral erosion, lithology and SPACE component imports were checked in the
existing reference environment on 2026-09-25; no new simulations were run.
Numba and Fastscapelib remain uninstalled here.
Fastscapelib lacked a matching wheel in the recorded audit. C++/GPU reference
tools are experiments, not mandatory runtime changes.

R45–R47 govern future native work: identify a dominant kernel, compare complete
workload benefit and Windows packaging, and explicitly choose a kernel bridge or
full Rust migration. Keep array/graph/surface boundaries clear now to limit later
rewrite cost. The [language assessment](../research/2026-09-05-language-and-performance.md)
is historical rationale, not proof that migration is presently worthwhile.
