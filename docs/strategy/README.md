# Current development strategy

Re-evaluated 2026-09-27 after the
[cell-safe delivery comparison](../research/2026-09-27-cell-safe-terrain-delivery.md),
following the [groundwater/canyon and architecture review](../research/2026-09-25-groundwater-and-terrain-architecture.md).
DM Tools is a usable terrain research workbench with strong numeric/build
foundations; believable drainage and connected landforms remain the next milestone.
The [method decision register](../research/terrain-method-decisions.md) now records
failed approaches, causes, retained work and replacement gates. Bounded automatic
guide relocation now gives 4/4 capture and descending guide profiles in the 250 m
raster while retaining hard targets. Local head/mouth banks now pass both ordinary
and dense checks. Tighter bounds remove the large 250 m delivery artifact while
protecting cell interiors. Raster bank shape and coarse delivery still fail;
retain these failures before adopting terrain/network co-evolution.
Product feature delivery now leads as described below. Groundwater is a bounded
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
precision support are now implemented. A standalone world-to-terrain handoff
now connects those sources to the existing local generation workflow.
Physical path/landform acceptance remains a prerequisite for world-informed
production terrain; ecological classifications remain downstream.

This is the authoritative execution order. [TODO](../../TODO.md) remains the
complete grouped backlog; P0 there can mean a prerequisite within a later
feature, not a second concurrent critical path. The
[research status](../research/status.md) distinguishes implemented, experimental
and untested work. Code, schemas, tests and accepted ADRs own current contracts;
contradictions require investigation, not automatic acceptance of a defect.
Dated reports and accepted ADRs remain historical evidence.

## Feature delivery priority

The user selected **world-to-terrain workflow** over further small numerical or
efficiency refinements. The [first handoff is implemented](../research/2026-09-27-world-to-terrain-workflow.md):
choose a continent, retain connected land and world scale, create a portable
terrain project and open it for authoring/generation. This uses the current
generator and does not claim the experimental history model is accepted.

Next prioritize visible broad landform effects from authored geological inputs,
followed by shared rough-world relief and useful regional generation. Keep
selection, projection, source formats, orchestration and UI in separate modules.
The unresolved river-bank and representation findings remain adoption gates;
they do not make every usable editor/world feature wait for research completion.
Consult before tests expected to exceed roughly two minutes or of uncertain long
duration, with purpose, estimate and a stop condition.

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

| Milestone | Position on 2026-09-27 | Next exit condition |
|---|---|---|
| Usable authoring and reproducible build | Implemented | Maintain it while changing generation |
| Measured quality baseline | Partial: eight-case profile probe plus paired evolution/control gallery completed | One comparable gallery and structural scorecard, including known failures |
| Terrain-aligned drainage | Automatic layout gives 4/4 capture, no sinks and descending routes at 250 m; bank, coarse-delivery and fixed-control quality remain rejected | Complete bank shape and delivery; retain capture, hard inputs and physical-scale checks before co-evolution |
| Coherent landform families | Partial recipes; two-epoch reference implemented and measured, quality gate open | Related range/pass/tributary/lowland structure that survives multiple seeds and scales |
| Useful zoom enrichment | Experimental | Accepted regional shape, transition and inherited-flow behavior; then viewport scheduling |
| World import and shared context | WC0 plus WC1 geographic coverage, water topology, edge widths, shore distance, directional exposure, verified products, authored geology recipes, bathymetric hypotheses and water-piece incidence implemented | B/C terrain acceptance; later physical forcing and conservative transport |
| World-to-terrain handoff | Implemented: connected land, retained source/projection, fixed scale, CLI and editor | Geological landform inputs, result correspondence and wide regional domains |
| World-informed rough terrain and history | Planned, dependent on physical terrain acceptance | WC2/WC3 coarse relief, seasonal runoff and bounded feedback; WC4 reviewed parent |
| Hydrological water and ecology | Later dependent work | Flux/storage/river-size evidence and WC6 ecological layers; shared world context comes earlier |

Do not turn this into one percentage or count passed tests as realism progress.

## Next implementation order

**Active product sequence:** the standalone world handoff is delivered. Next add
substantial geological/landform input effects, then shared rough relief and
regional workflows. The A–F sections below retain dependencies and scientific
acceptance criteria; their historical lettering does not put small dashboard or
bank refinements ahead of that selected product sequence.

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
validation and limits. The new World → Terrain action additionally creates a
prepared projected SVG and ordinary terrain project without generic SVG repair.
Connected neighbours prevent false internal coasts. The source retains the full
world and fixed metric scale. Explicit landform guidance now transfers from
geology recipes; climate and physical geological forcing are not applied yet.
**WC1 geography delivered:** spherical coverage and vector-derived periodic water,
with narrow-strait/island controls, support previews, hashed exports, verified
reopening, shared-edge measurements, shoreline distance with an error bound and
eight-direction water exposure with mixed-cell support. **WC1 geology inputs
also delivered:** a separate recipe/editor with cross-label and seam provinces,
explicit overlap/priority and independent ages/duration at one common present.
**WC1 bathymetry also delivered:** explicit ocean selection, shelf/slope/basin
inputs, conservative depth/error fields and independent editor/result contracts.
**WC1 water-piece incidence also delivered:** separate pieces and finite shared
intervals, source-verified context v4 and unresolved-connectivity support.
The standalone handoff and explicit geological landform guidance are delivered.
Next improve the shared transitions exposed by the paired landform preview:
adjacent recipes currently fade inward to the generic background and can produce
polygon-shaped rims. Compare continuous cross-boundary guidance while preserving
priority holes, blank overrides, hard heights and the physical coast. B/C physical-path acceptance still
gates adoption of the new coupled rough-terrain model. Later transport
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
use the delivered WC0/WC1 and handoff for product testing, add broad landform
guidance, resolve B/C acceptance for model adoption, then WC2-WC4 and D/WC5.

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

**B1 comparison implemented:** the
[connected-patch report](../research/2026-09-26-connected-valley-patches.md) separates
fixed-source/native incision from fresh construction with a prospective 600 m cut
ceiling and 120 km3 composition envelope. Both preserve final hard heights, the
divide and coast. Rounded local valleys, confluences and a coastal transition
capture all four fresh heads on the 125 m checking grid, with zero interior sinks.
At 250 m, Float32 raster delivery captures three and leaves one sink near a
hard-height correction; coarser delivery and the fixed control fail. Some fresh
local guide/bank checks also fail. Automatic guides were not moved, and no history
was simulated. Input roles, bounds corrections, ablation and failures are recorded
in [T09](../research/terrain-method-decisions.md#t09---construct-connected-local-valleys-then-deliver-a-raster).

**Automatic layout follow-up implemented:** the
[hard-target comparison](../research/2026-09-26-hard-target-valley-layout.md) moves
only explicitly automatic guides within a 1,500 m corridor, keeping all original
vertices, junctions, terminals and hard heights. An 800 m detour restores 4/4
capture, zero sinks and descending guide profiles in the 250 m Float32 raster.
All 48,705 interior checking samples reach the coast. Repeat and quarter-turn
checks pass. The 600 m / 120 km3 fresh envelope and native controls are unchanged.
The pin correction remains large; layout avoids it instead of lowering the target.

That layout comparison retains 21/575 local inward failures and 222/575 in the
250 m raster; capture alone did not establish construction acceptance. The original 525 probes
are a different denominator. Coarser delivery still fails. The bounded sine-squared
family and a sampled-envelope bed-lifting attempt were rejected; see
[T10](../research/terrain-method-decisions.md#t10---move-automatic-guides-around-hard-height-targets).

**Head/mouth follow-up implemented:** the
[matched-bank comparison](../research/2026-09-26-valley-heads-and-mouths.md) keeps the
same layout, 575 bank pairs and bounds. A constant-grade head adjustment ends at
the first confluence; perpendicular mouth sections keep the actual zero coast.
Local inward/endpoint failures fall from 21/5 to 0/0. An added <=2.5 m check also
passes at the original 1 cm tolerance. All four heads and all interior checking
samples reach the coast. Local construction passes this fixture's gates; this is
sampled evidence, not a continuous or unseen-landscape guarantee.

At that checkpoint the 250 m raster had 217 ordinary and 241 dense inward failures,
with five endpoint failures, despite 4/4 capture and zero sinks. Coarser grids failed.
Hard targets and the fresh 600 m / 120 km3 policy are unchanged; all numeric
arrays of the twelve prior control cases still match. See [T11](../research/terrain-method-decisions.md#t11---construct-head-and-mouth-sections-before-raster-delivery)
for the rejected smooth/local head lifts and the coastal-wedge correction.

**Cell-safe delivery follow-up implemented:** the
[paired comparison](../research/2026-09-27-cell-safe-terrain-delivery.md) uses a
one-sided curvature allowance, with whole-cell constant protection when subtracting
that allowance would make capacities negative. A documented interior bound and
five independent rectangle controls cover corners, off-grid and thin footprints.
The maximum 250 m envelope correction falls from 93.045 to 18.175 m, and the worst
dense bank rise from 54.062 to 0.316 m. Dense failures change from 241 to 238 of
575; endpoints from five to two. Capture remains 4/4, with no sinks or uphill
guides, but bank and coarse quality remain rejected. The four paired previous
controls match exactly. See [T12](../research/terrain-method-decisions.md#t12---protect-cell-interiors-with-tighter-delivery-capacities).

**Short representation probes completed:** the
[new evidence](../research/2026-09-27-feature-preserving-terrain-delivery.md) separates
height error from bank shape. A river-aligned analytic strip avoids all 114
failures seen in 238 world-bilinear profiles, with similar maximum height error.
Generic quadratic/cubic network interpolation loses outlets and breaks bounds.
A trusted prepared-field roundtrip preserves all 575 local sections and common
ground exactly at three background spacings plus a quarter turn; reducing it to
bilinear nodes restores the old failures. This is a storage experiment, not a
supported artifact or independent held-out landscape acceptance. See
[T13](../research/terrain-method-decisions.md#t13---preserve-features-instead-of-reconstructing-them-from-nodes).

**Guarded feature snapshot batch implemented (B1):** the
[repeatable comparison](../research/2026-09-27-prepared-feature-snapshots.md) retains
source, prepared geometry, complete graph, hard targets, metric frame and identities.
Bounded current-format loading rejects malformed or inconsistent data. All 575
banks, common heights and original quality metrics match after reopening in four
matched cases. Queries agree across order, batches and overlapping tiles/halos.
These tiles sample one frozen field; they are not independently generated detail.
The raster control remains rejected and product DEM authority is unchanged.

**Next bounded batch (B1):** add held-out bends, short tributaries, junctions,
hard-target proximity and oblique layouts within explicit supported domains.
Measure irregular-mouth support separately; current construction still needs a
straight zero coast. Then compare parent/detail filtering, means, retained terrain
and inherited flow. Do not mistake shared-point agreement for downsample or LOD
acceptance. Keep the complete bank/guide/capture/no-sink and physical-bound gates.
A channel-aligned strip or constrained mesh is a fallback for measured patch
limitations. Defer the large bilinear solve behind local representability checks.
A changed interpolator must establish its own interior safety. Do not loosen
tolerances, raise cut budgets or uniformly refine the world. The
[role contract](landscape-evolution.md#authored-intent-and-geographic-boundaries)
keeps authored targets distinct from generated hypotheses.

**Authority decision remains separate:** add held-out bends/junctions, arbitrary
orientations, real coastline geometry, tile/LOD and parent/downsample checks.
If a richer surface passes, record an ADR and update build/schema identities and
all numeric consumers together, defining raster exports/caches explicitly. The
current Float32 DEM stays authoritative until that change. Preserve distinctions
between unsupported input, finite search exhaustion, verified conflict and
numerical failure. Composition differences are not geological erosion.
Consult the user before tests expected to exceed roughly two minutes or with
uncertain longer cost, including the full suite; give an estimate and stop rule.
Consultation is required before the full regression suite; short focused checks
and evidence comparisons can proceed within the agreed time boundary.

**Following decision (B2):** connect an accepted construction and delivery pair to
the existing two-epoch reference so relief and the automatic network can evolve
together before publication. A local capture count alone is insufficient; require
the bank/guide and hard-target gates as well. Do not immediately rewrite the
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
network-led construction above. Connected local patches now improve sampled
capture in a separately bounded fresh case. Automatic layout now fixes the
250 m capture/guide failure; bank shape, coarse delivery and fixed-state capture
remain rejected. Complete the local and delivered geometry, not just additional
successful point constraints.
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
