# Landscape-evolution implementation plan

Updated 2026-09-28. **LE1 implemented; LE2 history, frozen reconstruction,
physical-path, receiver/outlet, constrained-network, bank-feasibility and
connected-patch construction, layout, head/mouth and cell-safe delivery comparisons measured.
Production-quality acceptance and application integration remain open.** The
[method register](../research/terrain-method-decisions.md) preserves the failed
approaches and revisit gates. The [groundwater/canyon reassessment](../research/2026-09-25-groundwater-and-terrain-architecture.md)
motivates the construction comparison and adds untested process alternatives.
The [primary-source review](../research/2026-09-24-landscape-evolution-models.md)
records the scientific basis, tool comparison and dependency probe.
The [main strategy](README.md) remains the authoritative project order; this
plan specifies its bounded geological-history experiment and conditional rollout.

## First implementation checkpoint

The [reference implementation and results](../research/2026-09-24-landscape-evolution-reference.md)
and [runnable guide](../../benchmarks/evolution/README.md) now provide typed epoch,
process-grid and budget inputs; an isolated Landlab adapter; deterministic
forcing fields; adaptive time stepping with rollback; water/material checks;
Float32 measurements; fresh-process comparisons and a local visual report.

LE1's zero/uplift/one-link/runoff/diffusion, steady slope-area and moving-knickpoint
controls pass. LE2 now covers two epochs, matched constant forcing, reverse
chronology, process ablations, resistance, seeds 42/7/20260902, orientation,
extent and process-spacing probes. The held-out seed uses the frozen coefficients.
This is an implemented research path, not a replacement for normal builds.

**Decision:** retain the history model as a useful experimental candidate, but
do not adopt this D8/bilinear surface as default output. Good node-level drainage does not
prevent internal rises on reconstructed diagonal channels. Grid direction and
whole-landscape resolution sensitivity also remain acceptance questions.
Follow the report's measured limits rather than counting analytic tests as realism.
The bounded B/R48 reconstruction comparison is now measured, as recorded below.
Physical path geometry, grid/capture sensitivity and hard authoring constraints
still gate full/default LE3 adoption in M5 and an accepted parent for later detail.
M3-M4 may expose basic experimental history controls under the hard input/numeric
contracts below; they do not wait for full quality acceptance. Sediment and zoom
scheduling follow the main plan. Keep one eventual production path.

## Frozen reconstruction checkpoint

The [follow-up implementation and evidence](../research/2026-09-24-frozen-channel-reconstruction.md)
compare a required-diagonal triangle surface with bilinear reconstruction of the
same delivered Float32 nodes and saved final Float64-snapshot routing. The saved
graph is not the previous report's separately rerouted Float32 delivery graph.
The comparison runs in the base environment without the scientific engine.

All 22 completed source cases retain all 19,228 selected edges and 1,183 full
head-to-terminal routes. On the 1,030 nodally nonascending routes, candidate
ascent is zero at both 100 m and 25 m stations; 689 of those routes had control
rises. The other 153 routes remain unresolved because their input graph climbs.
The failed 156.25 m history remains an explicit missing result. These coverage
totals include the original repeated case, not independent statistical samples.

This experiment is complete, but its surface is not accepted for integration.
It keeps D8 geometry, has C0 slope creases, can violate off-grid targets and
changes reconstructed volume independently of the solver's material ledger.
Explicit crossing rejection, anchor residual controls, paired actual-ground
figures and whole-route metrics now make those limits testable. Uphill affected
length uses a whole-climb tolerance so dense sampling cannot hide gentle rises.

## Physical-path checkpoint

The [coupled physical-path comparison](../research/2026-09-25-physical-channel-paths.md)
retains complete routing and zero ascent on all nodally nonascending routes while
reducing D8-aligned length to 56.99%. Cut/fill admission fails across the cohort;
off-grid targets, geographic divides and native regional constraints still need
a different construction. Frozen grid/time diagnostics now quantify receiver and
outlet changes at identical physical coordinates, without claiming area capture
or convergence from pointwise samples.

## Constrained-network checkpoint

The [bounded network-led fit](../research/2026-09-25-constrained-network-surface.md)
now preserves native regional bounds, hard off-grid heights, a protected divide
and descending physical guides at three process spacings. Repeated fits and a
90-degree rotation pass. Actual Float32 rerouting still misses mouths and creates
interior sinks, including at a common finer checking resolution. It remains
research-only; this is not a history-model result or an accepted hydrological field.

## Valley-bank checkpoint

The [bank-feasibility comparison](../research/2026-09-25-valley-bank-feasibility.md)
now adds physical banks, nearest-reach junction ownership, coastal taper and
local/joint constraint witnesses. Feasible cases preserve bank endpoint drops,
native bounds and hard heights, but cross-sections still rise and head capture
remains zero. At 250 m sinks worsen from 19 to 30; the 1,000 m bank conditions
are locally infeasible. No relaxed ground is published.

The next construction comparison has now run, as recorded below. The fixed-state
failure remains a control rather than being erased by a different envelope.

## Connected-valley checkpoint

The [local-patch comparison](../research/2026-09-26-connected-valley-patches.md) now
constructs rounded valley unions and explicit confluence/coastal transitions.
Input roles separate native fixed-source cuts from fresh composition under a
600 m / 120 km3 envelope; final hard heights, divide and coast remain fixed. Local
fresh routing captures all four heads with no interior sinks, but 250 m Float32
raster delivery captures three with one sink. Some guide/bank conditions still
fail locally; fixed/native capture remains rejected. That comparator held guides
fixed; the layout follow-up is below. Terrain/network co-evolution remains unimplemented.

The coastal ablation supports the explicit mouth transition. Conservative
incident-cell caps fix an initial between-node cut violation without increasing
budgets. The automatic-layout follow-up below now isolates the hard-target blockage.

## Hard-target layout checkpoint

The [automatic guide comparison](../research/2026-09-26-hard-target-valley-layout.md)
preserves all original vertices, heads, junctions, mouths, hard heights and the
same fresh envelope. An 800 m detour within a declared corridor restores all four
captured heads, zero sinks and descending guide profiles in the 250 m raster.
All interior checking samples reach the coast; repeat/quarter-turn checks pass.
Local and delivered banks still fail, as does coarse delivery. The native fixed
control remains rejected. No time evolution or application integration is added.

The next head/mouth comparison is now measured below; this layout remains its
unchanged control.

## Head and mouth construction checkpoint

The [matched-bank comparison](../research/2026-09-26-valley-heads-and-mouths.md) now
passes all 575 local inward/endpoint sections at 25 m and <=2.5 m sampling, with
unchanged 1 cm inward tolerance. Cap-aware head profiles and perpendicular coastal
sections retain the same graph, source, targets and envelopes. Local capture is
4/4 with no sinks; 250 m raster capture stays 4/4, but banks and coarser delivery
remain rejected. Repeat/quarter-turn checks pass. Rejected tapers and between-
station defects remain in the method register.

## Cell-safe delivery checkpoint

The [paired bound comparison](../research/2026-09-27-cell-safe-terrain-delivery.md)
now limits bilinear interpolation excess using one-sided curvature bounds and
constant capacity in cells needing protection from negative estimates. The worst
250 m raster inward rise falls from 54.062 to 0.316 m without losing hard-input
or cell-interior protection. Dense failures remain 238/575, endpoints two, while
capture remains 4/4. Independent corner/thin-area controls pass; coarse grids
still fail. No method is adopted into normal generation.

## Feature-preserving delivery checkpoint

The [short representation probes](../research/2026-09-27-feature-preserving-terrain-delivery.md)
now distinguish topology from elevation error: river-aligned analytic samples
avoid the world-grid bank defects. Generic quadratic/cubic interpolation fails
network capture and bounds. Saving/reopening the prepared local field preserves
all 575 profiles and common Float32 samples; reducing it to a bilinear raster
reintroduces the existing defects at every tested spacing.

The [prepared snapshot implementation](../research/2026-09-27-prepared-feature-snapshots.md)
now provides guarded reopening, complete network identity and deterministic
queries. All 575 dense banks and original metrics survive reopening; same-field
query-order and adjacent-tile/halo checks pass. This does not establish newly
generated detail or filtered parent means. Keep bilinear feasibility as a small
diagnostic before a larger solve. Next test held-out/general-angle quality and
parent/downsample behavior before proposing an ADR to change generated-surface
authority and its consumers. The product Float32 DEM contract remains unchanged.
Any changed interpolator needs its own interior protection. Accepted delivery
is required for a new product surface authority or default adoption, not all
M3-M4 history integration. Consult before longer tests as specified in the main
plan. This snapshot work itself added no time evolution or application path.

## Outcome and decision

Generate connected ranges, passes, valleys and lowlands by evolving a broad
starting landscape through authored epochs. Rivers and terrain must respond to
each other. Keep generation reproducible, preserve author intent, and make the
result practical to inspect in the existing local workbench.

**Reference now tested:** Landlab as an isolated reference for prescribed uplift,
effective runoff, implicit stream-power incision and linear hillslope transport.
Use two epochs and two rock-resistance regions. Compare against the current
recipe/incision output before deciding whether to integrate an existing component
or implement a narrow project kernel. Keep Python and existing application layers.

**Sequence:** M1-M2 bind world/rough relief and effective runoff; M3-M4 bring the
existing reference into a bounded application experiment with the necessary LE3
input roles and basic LE5 controls. M5 completes LE2/LE3 physical/authoring quality
before default adoption or a WC4 parent. LE6 follows in M6; selected LE4 materials
follow in M7. LE IDs are work packages, not a second execution order.
Keep the baseline and research reference as comparisons while selecting the new
path; remove superseded generation once replacement is accepted. A quality
failure remains evidence, not a ban on every application integration experiment.

The first release need not simulate plate motion, changing coastlines, glaciers,
weather events, meanders, sediment grain classes or planetary climate. Keep these
as separate, evidence-driven extensions. Low runoff can be an authored historical
forcing; a desert biome requires moisture/climate evidence, not erosion age alone.

## World context and shared geological time

The [WC0-WC6 world plan](world-context.md) adds an explicit parent for future
continent histories: retained global geography, ocean/geological hypotheses,
rough relief and seasonal climate/runoff. No world context exists in the current
LE1/LE2 reference, whose metric fixtures and authored runoff remain valid controls.

Continent settings are defaults, with spatial geological-province overrides.
Continents need not equal plates or catchments. Separate crust age, uplift timing
and erosion duration; all histories finish at one global present. Historical
forcing must declare fixed modern geography, authored epochs or reconstructed
inputs. Modern climate is not evidence of past climate.

WC3 feedback must restart the same initial history or continue an explicitly
identified checkpoint. It cannot age the previous final surface again. WC5/LE6
will refine regional history to the same present, with parent boundary/forcing
through time. These requirements extend existing evolution work, not create a
second history engine. Shared climate/runoff moves earlier than ecological layers.

## Experimental application integration

**Planned for M3-M4; not implemented.** Adapt the existing reference rather than
starting another erosion model. The first supported path consumes M1's initial
metric relief and M2's effective runoff, plus explicit epoch forcing. Climate
seconds, geological years and displayed Ma cross one tested unit boundary.
Crust age and time since rejuvenation do not supply a complete forcing schedule.

- `domain` owns typed history, input roles and units; `pipeline` owns preparation,
  process arrays and stage composition; an adapter owns the isolated scientific
  runtime and serialization; `application` owns cancellation, source verification,
  budgets and publication. Extract reusable reference logic without importing a
  benchmark runner into the core or adding a generic solver abstraction.
- Preserve existing absolute/final authored constraints. Add explicit initial,
  persistent or final roles where needed; reject unsupported experimental inputs
  before running. Do not silently reinterpret current ridge/point semantics.
- Start from rough initial relief without the old automatic valley incision stage.
  Evolve the automatic network with ground; derive final diagnostics from the same
  delivered surface. Authored valley guidance retains its declared role. Do not
  carve a second independent network after evolution to make the preview look better.
- Compare no-aging, zero-forcing, changed runoff/uplift/resistance and ordered versus
  reversed epochs on one public connected-land domain. Preserve original controls
  and record actual-ground/channel failures, solver residuals and correction budgets.
- Save provisional state with source/context/history/runtime identities, support
  limits and quality findings; a numerically failed or cancelled solve cannot look
  complete. The existing Float32 result contract remains authoritative unless an
  explicitly reviewed representation decision replaces it.
- Basic LE5 stage controls, preview and reopening arrive with the experiment.
  Experimental status survives saving/reopening. M5 still requires the packaged
  dependency/license review and scientific/authoring acceptance before default use
  or publication as an accepted WC4 parent.

M4 adds the [bounded feedback rules](world-context.md#rough-relief-and-feedback).
No replay starts from a previous final state unless it is a specifically identified
continuation checkpoint. Production acceptance below is retained; only the former
requirement to finish it before trying application integration is superseded.

## Mathematical model and units

### First model: evolving elevation

Use metres horizontally and vertically, years for geological time, and Float64
working arrays. Let `z` be ground elevation, `U` uplift rate (m/year), `D` hillslope
transport coefficient (m²/year), and `E` river incision rate (m/year):

```text
∂z/∂t = U - E + ∇·(D ∇z)
E = K_e (Q / Q_ref)^m S^n
Q_i = R_i a_i + Σ Q_donor
S_i = max((z_i - z_receiver) / L_i, 0)
```

`R` is effective runoff depth (m/year), not raw precipitation. `a_i` is the
contributing control area (m²), `Q` is volumetric discharge (m³/year), `Q_ref` is
one fixed declared discharge scale, and `S` is dimensionless. Normalizing `Q`
makes `K_e` m/year; changing `Q_ref` requires rescaling the coefficient. The
exponents and coefficient are model parameters, not universal rock constants.
Constant runoff allows an equivalent drainage-area formulation, but variable
runoff must be accumulated before applying the power.

Use `n = 1` initially. For a fixed receiver graph and flow during one incision
substep, solve downstream to upstream:

```text
c_i = Δt K_e,i (Q_i / Q_ref)^m / L_i
z_new,i = (z_predictor,i + c_i z_new,receiver) / (1 + c_i)
```

`z_predictor` already includes that step's uplift. Do not add it a second time.
This is the simple project specialization of the
[Braun–Willett implicit method](https://doi.org/10.1016/j.geomorph.2012.10.008).
It applies to erosional reaches with valid lower receivers, not flooded nodes,
self-receivers or arbitrary lake water surfaces. Define those cases separately.

The adapter to an unnormalized `K Q^m S` implementation uses
`K = K_e / Q_ref^m` with the same discharge/time units. Test this explicitly with
constant and doubled runoff. Do not pass area, volumetric discharge or discharge
per channel width interchangeably. Time conversions belong in one unit boundary.

Hillslope flux is `q_h = -D ∇z`; update terrain from its conservative divergence.
With spatially varying `D`, using `D ∇²z` alone is incorrect. Start with constant
`D` and a tested implicit linear solve or the reference component's documented
stable stepping. Record boundary flux. This first model removes incised rock to
an explicit export sink; it does not simulate where that rock deposits.

### Later extension: bedrock and mobile sediment

Use [SPACE](https://gmd.copernicus.org/articles/10/4577/2017/) as the comparison:
`z = b + h`, where `b` is bedrock elevation and `h >= 0` is mobile-cover thickness.
For constant cover porosity `φ` and zero bedrock porosity:

```text
∂b/∂t = U - E_r
(1 - φ) ∂h/∂t = D_s - E_s
stored mobile solid volume = Σ (1 - φ) h_i a_i
```

`E_r`, `E_s` and `D_s` are solid-volume rates per ground area. Internal transfers
must cancel in a domain ledger; explicitly include boundary export/import,
uplift, permanently suspended fines and any author-constraint corrections.
Account for hillslope transfer in the same ledger when coupling it. Retain
positive thickness without silently discarding negative-volume errors.
This remains a long-term surface-process approximation, not flood hydraulics.

### Numerical controls

- Stop exactly at each epoch boundary. Forcings change between accepted states;
  changing an epoch must not regenerate unrelated random fields.
- For each trial: apply uplift to a predictor, enforce persistent boundaries,
  route/accumulate its flow, solve incision, then update hillslope flux and check
  the resulting terrain/routing. The solver must not raise a bed to follow an
  adverse receiver; use the declared non-erosional/depression case or reject the
  trial. Record the operator order and test its splitting error.
- Recompute receivers and discharge after accepted terrain changes. Recompute
  within both half-steps when checking a full step against two half-steps.
- Use bounded deterministic step reduction for height/flux error, excessive
  change, failed solves or unresolved routing. Keep rollback copies in the memory
  estimate. Do not accept a step merely because the implicit solver is stable.
- Receiver changes can be real river capture. Log changed area/outlets and check
  convergence; do not forbid every graph change or require identical topology at
  different resolutions. Materially different outcomes under refinement remain
  an unresolved numerical sensitivity.
- Limit step count, retries, elapsed research budget and working memory. Exhaustion
  produces an incomplete experiment, never a completed build at the wrong age.
- Use no new stochastic perturbation per iteration. Initialization and spatial
  material fields use named seeds in global coordinates; step splitting cannot
  change the landscape by drawing a different random history.

## Authored intent and geographic boundaries

Keep these meanings distinct in types, validation and eventual UI:

| Input kind | Meaning | Handling |
|---|---|---|
| Initial surface | Broad terrain at the beginning of the experiment | May evolve; not a present-day spot-height promise |
| Epoch forcing | Uplift, effective runoff, resistance and duration | Drives evolution; region overlap/composition is explicit |
| Persistent boundary | Fixed base level, closed boundary or deliberately protected history boundary | Enforced throughout that declared interval; record external flux/work |
| Final hard target | Existing authored height, coastline or other present-day requirement | Preserve existing meaning; never reinterpret it silently as initial relief or a permanent historical pin |
| Soft terrain guidance | Desired character or approximate structure | Fit subject to the hard constraints; report residuals |

Keep the current coastline/land mask and base level fixed in the first product
integration. Natural coast migration would conflict with authored geography and
needs its own explicit future mode. Source/world scale remains unchanged.
Prototype first on a rectangular metric catchment; then cover multipart coasts,
islands and clipped control volumes. Rainfall area and material volume must use
the same declared land/control-area policy, not `node_count * spacing²` by habit.

For final targets, compare one bounded, constraint-aware reconstruction of the
evolved surface and shared channel geometry. Measure the correction separately
from geological erosion/deposition, then reroute/check the composed result. Do
not restore heights after hydrology and call the result valid. If exact targets
cannot coexist with protected divides, cut limits and outlet reachability,
return a specific conflict. A small correction can be accepted as authored
terrain composition; a large correction is evidence the proposed history is not
compatible with the requested map.

Existing automatic-incision ceilings remain in force for that mechanism.
Geological uplift and erosion need a separately declared history envelope; do
not bypass protections by labelling unlimited cuts as age. Record initial/final
heights and cumulative uplift, incision and imposed corrections. Thresholds for
acceptable correction area/volume must be fixed on fixtures before tuning.

Retained lakes and dry basins are legitimate terminals. Distinguish a routing
surface from ground, and a spill assumption from finite stored water. LE1/LE2
support an open-draining domain without authored retention; reject unsupported
basin inputs explicitly. LE3 must test the current basin/constraint contract
before a general application rollout. Physical lake chains/storage belong to
LE4 and batch E; they cannot be inferred from a filled routing raster.

## Groundwater and canyon extensions - proposed

The [new research and staged tests](../research/2026-09-25-groundwater-and-terrain-architecture.md#implementation-sequence-and-stop-rules)
add G1 for groundwater capture/density, C1 for layered and lateral canyon erosion,
and K1 for an explicit karst connection. None is implemented in the reference.
Use the existing isolated Landlab environment; component import checks only
establish availability. No new product engine or mandatory dependency is selected.

After B chooses a surface path, test a small analytic aquifer before coupling
recharge/stream exchange to incision. Close the combined storage/flux balance and
resolve seconds versus geological years. C1 can proceed after surface acceptance
without waiting for caves or karst; mechanical erosion, dissolved mass and
composition corrections remain separate. Existing LE4 owns mobile sediment.

Surface and subsurface catchments need not match. Declare geological aquifer
boundaries independently of topographic divides, and model head/capacity for
underground links. The existing open-draining fixture retains its no-extra-sinks
gate; basin/karst fixtures require explicitly different terminal/storage semantics.
A heightfield cannot represent cave roofs and floors. Keep any eventual cave
geometry in a separate representation rather than hiding it in DEM exceptions.

## Scale, prepared fields and local enrichment

Define process spacing in metres and derive a fixed grid origin, dimensions and
actual spacing from the declared extent. Store those values in experiment/build
identity. An output image size must never select the evolution history or its
routing grid. The present 257-node routing limit is a baseline, not an adequate
resolution for every continental feature.

At preparation time evolve a complete bounded domain, then freeze a state and a
deterministic reconstruction. Arbitrary coordinate queries sample that state;
they never advance time or rerun a local history. Adjacent/overlapping outputs
must agree exactly at shared coordinates for the same prepared state/runtime.
Do not replace the current field with naive bilinear interpolation: off-grid
hard targets, coastlines and full channel profiles require explicit support.

The delivery DEM remains Float32. Validate the composed/quantized surface and
its channel paths, not just the Float64 solver nodes. Any procedural residual
must respect protected ground and channel corridors and be revalidated after
composition. Evolution replaces the accepted automatic shaping stage; do not
apply both the old automatic incision and the new incision unknowingly.

Zoom enrichment follows later. Its first model conditions finer generation on
the immutable **final** parent terrain, substrate/cover and boundary flow, with
the existing overlap/downsample requirements. This is present-state detail.
The world workflow also commits to a separately gated historical-refinement
milestone in WC5/LE6: replay to the same global present using parent boundary
levels and water/material fluxes through time. Final discharge alone is
insufficient. Independent viewport histories would change shared catchments;
use deterministic shared support and test restriction, flux and exact overlaps.
Neither increasing zoom nor refining resolution advances the world's age.

## Work packages and decision gates

### LE0 — Research and scoped plan

Completed for planning: primary papers/tool capabilities compared, mathematical
scope selected, Windows wheel-only dependency resolution recorded, and this plan
linked into strategy/TODO. No runtime adoption or quality improvement is claimed.

### LE1 — Reference environment and controlled fixtures

**Implemented.** The executable controls and locked environment are linked above.
The following list records the scope they establish, not unfinished setup work.

Depends on minimal strategy A evidence, not a completed UI comparison dashboard.

1. Create a disposable Python 3.14 research environment outside application
   dependencies. Pin the Landlab/reference stack and record hashes/licenses,
   including transitive prereleases. Import and run tiny official-equivalent
   examples. If the stack fails, record the failure and evaluate an isolated
   supported reference environment; keep the application Python version fixed.
2. Add a narrow benchmark entry point beside the existing terrain benchmarks.
   Share fixture identity, seed, coordinates, runtime hashing and artifact
   conventions. The command is `python -m benchmarks.evolution`; see its guide for options.
3. Establish unit/boundary controls: zero forcing leaves a flat surface unchanged;
   uplift-only height equals integrated uplift away from fixed boundaries;
   a one-receiver incision problem matches its implicit update; conservative
   diffusion balances storage and boundary flux; doubled runoff has the specified
   effect on `Q` and incision coefficient.
4. Add a steady channel slope-area control and a retreating-step/knickpoint test.
   Measure error under smaller time steps and finer spacing, not just execution
   without exceptions. This responds to the
   [TTLEM numerical-accuracy evidence](https://esurf.copernicus.org/articles/5/47/2017/).
5. Fix the baseline cohort, render settings, tolerances and performance reporting
   before tuning the two-epoch experiment.

**Exit:** a reproducible executable reference with checked units, boundaries and
numerical controls. Dependency resolution alone does not pass. Failure stops
integration but should not delay unrelated baseline-quality reporting.

### LE2 — Two-epoch mountain-to-lowland proof

**History and frozen reconstruction comparisons implemented; acceptance not
passed.** See the linked reports for completed cases, resource limits, profile
gains and remaining morphology/authoring/grid gates. Preserve that cohort when
testing improvements.

Depends on LE1. The first experiment is executed; the requirements below
continue to govern acceptance and follow-up comparisons.

Use an 80 × 60 km public synthetic domain, a broad oblique uplift belt, a lowland
outlet and two resistance regions. Initial exploratory epochs: 2 Myr of active
uplift, then 4 Myr of weaker uplift. An illustrative belt rate of 0.5 then
0.05 mm/year integrates to 1,200 m before erosion; these are test forcings, not
a reconstruction of Tharkeniss Veld. Record full spatial forcing and edge taper.
Calibrate runoff, incision and diffusion on the unit/analytic fixtures, then
freeze a small parameter set before testing the held-out seed.

Compare current recipe/incision terrain, an evolution run with constant forcing,
and the two-epoch run. Give the constant-forcing control the same integrated
uplift and runoff over the same total duration; hold initial relief and material
fields fixed. On one small fixture also swap epoch order, to separate chronology
from merely applying more uplift or water. Keep coastline/extent, authored final
intent where supported, colour limits, lighting and output spacing identical. The initial
process field is a separately identified hypothesis; do not claim pixelwise
algorithm equivalence to a current map with different hard constraints.
Use mechanism ablations on the same initial state to distinguish erosion from
simple smoothing or different initial noise.

Start at 625 m process spacing (129 × 97 nodes), then 312.5 m (257 × 193).
Use 156.25 m (513 × 385) only for finalists and convergence checks. Start with
seeds 42 and 7; keep 20260902 held out. Rotate the synthetic forcing relative to
the grid and repeat the same physical domain at another extent to expose scale
and direction artifacts. Do not run a huge full-factorial sweep initially.

Produce initial/end-of-epoch hillshade/elevation pairs, erosion/uplift change maps,
channel profiles and a compact numerical report. Include relief/slope, drainage
density by physical contributing area, long straight segments, direction bias,
peak/pass structure, outlet reachability and unresolved depressions. A naturally
straight valley is a control, not an error to bend decoratively.

**Early go/no-go:** demonstrate coherent related valleys/divides and meaningful
epoch/resistance response on the held-out case, converging numeric controls,
no hidden clipping or removed required routes, and measured time/memory.
Review worst cases as well as aggregate scores. If the result merely smooths the
map, has persistent grid grooves, or cannot approach the intended desktop budget,
reject it and return to batch B's terrain-guided shared paths. If chronology is
the dominant cost, one analytical-method comparison may replace further tuning.

LE2 evidence guides M3-M4 integration; completing its quality controls is part
of M5 acceptance and is not permission by itself to make the prototype the default.
No promise of realistic depositional plains, meanders or physical lakes is made.

### LE3 — Constraints, shared paths and final-surface acceptance

Uses LE2 evidence. Minimum input/constraint interfaces enter in M3-M4; the full
acceptance gate below governs M5. This is the highest integration risk.

- Prepare typed history inputs and an immutable result; carry process masks,
  boundary policy, forcing, stage identities and warnings explicitly.
- Implement the chosen global surface reconstruction and a single physical
  channel-path representation shared by sampling, shaping, diagnostics and draw.
  Preserve exact junctions/terminals and authored divides; check whole profiles.
- Exercise off-grid/coincident heights, coast-boundary conflicts, multipart land,
  authored ridges/valleys, region overlaps, basins and every currently supported
  constraint kind. Preserve actual input semantics, not only the experiment's
  easiest features. Conflicts and unsupported experimental cases must be visible.
- Compare route alternatives, retained sinks and automatic-head choices under
  protected-ground/cut budgets. A large final constraint correction triggers
  rejection or a new history proposal rather than silent geological claims.
- Freeze and serialize the prepared state only after shared-coordinate,
  Float32, input, routing and final-profile tests pass. Test repeated runs and
  changed output sizes against the same prepared state.

**M5 adoption gate:** satisfy [quality B](terrain-quality.md#b-make-a-river-path-and-its-terrain-agree)'s constraint, coverage, direction and sampled-profile
gates. Use fixed authored source/outlet routes and spatial catchment coverage
when a new network has different automatic branches; do not compare counts per
D8 edge or erase hard routes to improve the score. Report natural automatic
network changes separately. The initial ≥50% sampled-ascent reduction target
applies to the frozen comparable feasible cohort, not unrelated new branches.
No new >10 m rise on a previously feasible matched route; controlled gravity-bed
fixtures must be descending within declared Float32 tolerance. Lakes/backwater
are separate model cases. Finite sampling remains finite evidence.

Select the default-generation ADR and production dependency/implementation at M5.
A bounded research adapter can connect the existing reference in M3-M4 earlier.
If a reference library is selected, audit the complete shipped stack and test the real packaged
Windows application. If a narrow local implementation is selected, compare it
against the pinned reference and analytic fixtures; do not copy an entire solver
framework into the project. Remove superseded automatic shaping after acceptance.

### LE4 — Bedrock, cover and deposition comparison

Depends on accepted LE3 interfaces and the strategy-E milestone. It maps to
R16 and is not a prerequisite for basic erosion controls in LE5. Keep it isolated
from the application until its material/quality gate passes.

Use a channel leaving resistant upland for a gentler plain, then a retained-basin
case. Compare a SPACE reference, explicit single-receiver discharge and known
sediment input/output. Pin and test flooded-node behavior, dry cells, no-cover
limits, porosity and settling parameters. Current MFD arrays are not compatible
with the reference component's single-receiver requirement.

Add a solid-volume ledger, nonnegative cover, zero-flow controls, boundary-export
and step-refinement checks. Start with one sediment class and fixed porosity.
The first depositional result is a coupled bedrock/alluvium landscape; a realistic
fan, braid or migrating river needs additional resolved geometry/process evidence.
Do not bolt arbitrary post-erosion smoothing onto a mass-conservation claim.

**Exit:** balanced material exchange and improved upland-to-lowland morphology on
held-out fixtures, with declared numerical error and incremental cost. If rejected,
retain the explicitly export-only incision model and keep deposition experimental.

### LE5 — Application, persistence and pre-generation editor

Basic experimental delivery is part of M3-M4 and requires supported LE3 input
interfaces; default use and an accepted WC4 parent require full LE3 acceptance
in M5. LE4 is required only for sediment controls/products. All world-linked
history controls share the same time/dependency contract from their first use;
they do not need an already accepted whole-world parent to test a bounded domain.
Continent defaults and province overrides bind to one context/history revision, with crust age separate from uplift timing and erosion
duration.

- Add current-format history settings, epoch ordering and validation; update
  schemas, examples, build identity and saved-parent replay together. Reject old
  unsupported formats clearly; do not build a compatibility/migration subsystem.
- Show a short epoch list with duration, uplift and wetness, spatial resistance
  regions, actual process spacing and predicted work. Offer a few measured
  starting profiles with inspectable values. Keep advanced coefficients in an
  advanced view. Profile names are design aids, not calibrated geological ages.
- Edit only pre-generation inputs over the retained read-only map. Regeneration
  applies the changed history. Show stale/current identity, progress by epoch,
  cancellation, error/conflict state and before/after inspection.
- Reuse completion-last build publication and memory admission. Save only the
  state needed for deterministic reconstruction/replay and optional review
  snapshots; do not retain every solver iteration by default.

**Exit:** saved project → build → inspect → change history → regenerate → reopen
works in CLI and desktop, with preserved inputs and verifiable outputs. Cancellation
and resource exhaustion leave no apparently complete build. No post-generation
sculpting controls are introduced.

### LE6 — Parent-conditioned local evolution/detail

Depends on accepted global results and strategy D's parent contracts. Keep the
existing regional workflow until its replacement passes the same gates.

Carry immutable parent height/material state, channel junctions, lake identity,
boundary inflow/outflow and explicit flux units into regional generation. Test
adjoining windows, arbitrary crops, overlaps, repeated visits and request order.
Measure downsampled height, coarse spectral leakage, seams and added tributary
water balance independently. Subgrid terrain and channels must use sufficiently
fine physical spacing before small rivers can be displayed as real hydrology.

Connect accepted results to zoom scheduling only after numeric/visual acceptance.
Large water remains visible remotely; small streams appear when both local process
resolution and screen scale support them.

**Required planned extension for world-linked aging (WC5):** retain sufficient
parent trajectory/checkpoints, define temporal boundary interpolation and replay
refined initial conditions through the selected epochs to the same present.
Account for correction volume separately; test history truncation, water/material
boundary flux, child restriction, exact overlaps and request-order independence.
This is a separate acceptance gate from present-state detail, not an optional
meaning of that command. A final DEM plus an age number cannot pass it. Keep the
current exact parent/authoring contract; incompatibility requires an explicit
contract decision rather than silently relaxing it.

## Integration map

The benchmark package and dependency-light domain inputs below now exist. Other
boundaries are conditional integration work. Avoid a generic simulation framework.

| Area | Planned responsibility |
|---|---|
| `benchmarks/evolution/` (implemented) | Reference adapter/runner, frozen-state reconstruction and whole-route comparison, public controls and paired reports; optional engine imports stay here |
| `domain/evolution.py` (implemented) | Typed epochs, physical grid, history and budgets with validation; no Landlab/filesystem dependency, no saved-project fields yet |
| `pipeline/evolution.py` (proposed) | Accepted deterministic orchestration and model-state transitions; numeric primitives only where justified |
| `pipeline/evolution_surface.py` (proposed if needed) | Frozen-state reconstruction and constraint/path composition, separated from time stepping |
| `pipeline/generate.py` | Integrate at `prepare_terrain_field`; `PreparedTerrainField` keeps coordinate-query semantics and Float32 delivery |
| `pipeline/hydrology.py`, `pipeline/channel_profiles.py` | Shared drainage/path and profile operations; distinguish process graph from final physical paths |
| `pipeline/profile.py`, project domain/adapters, `schemas/terrain/` | Effective current profile/history serialization and validation, only when promoted to product |
| `application/build.py`, `adapters/build.py` | Reproduction identity, owned output publication, state snapshots and hashes |
| `pipeline/parent.py`, `pipeline/regional.py`, parent adapters | Verified immutable evolved parents and conditional detail, after LE3/LE6 gates |
| `workbench.py` and CLI interfaces | Pre-generation controls and result inspection; no simulation logic in UI callbacks |

An adopted external engine would live behind an adapter using plain typed arrays
and boundary/units contracts. The integration must respect existing dependency
direction; a domain object must not retain a Landlab grid. Export/build modules
must not silently rerun evolution during metadata collection or rendering.

## Acceptance and performance evidence

Use small deterministic tests for laws/contracts and a separate quality/benchmark
report for realistic examples. Freeze tolerances before fitting candidates.

| Evidence | Required result |
|---|---|
| Units and analytic controls | Correct uplift integral, one-link update, runoff scaling and diffusion balance; declared Float64 tolerances |
| Temporal/spatial refinement | Stable headline outcomes with shrinking numerical error; explicitly report sensitive captures/knickpoints |
| Hard authoring | Existing height/coast/structure contracts and bounded corrections hold after Float32 composition |
| Water and material | Correct terminals, no duplicated area/flux, nonnegative cover when enabled; explain all storage/import/export/correction residuals |
| Shared queries | Exact same-state shared-coordinate samples across output grids, crops and request orders |
| Quality | Matched physical-scale gallery, profile/coverage gains, direction controls and hold-out cases; no colour/noise-only improvement |
| Resources | Cold/warm timings, accepted/rejected step counts, routing/solve/reconstruction/review/export stages and peak resident memory |
| Product workflow | Saved inputs unchanged, current schema/provenance, clean incomplete/cancelled runs and usable inspection |

For ledger checks use `abs_error <= absolute_tolerance + relative_tolerance *
throughput`, with a documented nonzero reference scale for zero-flux cases.
Separate Float64 solver balance from Float32 publication error. Record residuals
both in physical volume and normalized form; do not conceal cancellation of large
terms behind a relative percentage of total mountain volume.

Set an initial experimental ceiling of 60 seconds for a ~50,000-node basic run
on the recorded local hardware, excluding separate final water review/export,
and at most 4,096 accepted steps. This remains a stop/review budget, not a final
product promise. The first
measured ~50,000-node run completes inside it; the finest-grid probe and complete
worker times are recorded separately in the report. Recheck after model changes.
Report complete build time separately; a fast erosion kernel is insufficient if
preparation, reconstruction or validation dominates. Add control-workspace,
reference-engine and rollback arrays to admission estimates; do not assume the
current terrain memory estimate covers them.

Prefer mature compiled scientific primitives when they fit the selected model.
Profile before Numba/Rust/GPU work. Independent ensemble runs may be parallelized
within a measured memory budget; the inner solver must retain a defined reduction
order if exact repeatability is promised. Cross-platform comparisons may use
explicit tolerances rather than unsupported bitwise guarantees.

For implementation commits run the repository's pytest, Ruff and Pyright gates
plus the isolated reference tests and relevant numerical/quality evidence.
Prose-only follow-ups need link/claim/diff checks; reuse unchanged runtime evidence.

## Deferred questions with an owner

- R10/R11: depth-dependent strata, subsidence, spatially varying history and
  geological-event reconstruction; start with two-dimensional resistance/forcing.
- R14: analytical erosion if sequential cost is the blocker; do not equate an
  independent age query with a temporally continuous history.
- R16/R18: lake storage, sediment sizes, lateral erosion, fans, meanders, braids
  and deltas; each needs appropriate scale and conservation evidence.
- R15/R34/R49: accepted present-state detail, then WC5/LE6 historical refinement
  with boundary trajectories and one shared present.
- R17/R31/R45–R47: stochastic transport, GPU/native kernels and eventual Rust;
  measured model/workload benefit must precede adoption.
- R01/R33/R49: broader world/climate coupling beyond the supported M1-M4
  domains and first climate/runoff model; distinguish authored wetness from
  inferred climate. Stronger planetary models and ecology remain M8/F/WC6 work.

The history, reconstruction and later physical-path comparisons are recorded
above. When M5 resumes physical-quality work, choose the valley/channel approach
from failures observed in the integrated M3-M4 candidate, using the existing
comparisons to test authoring, path/ground agreement and grid/capture sensitivity.
The next implementation is M2 climate/runoff; isolated quality work leads only when it
blocks a hard integration contract. Default adoption still requires acceptance.
