# Landscape-evolution implementation plan

Updated 2026-09-24. **Proposed, not implemented.**
The [primary-source review](../research/2026-09-24-landscape-evolution-models.md)
records the scientific basis, tool comparison and dependency probe.
The [main strategy](README.md) remains the authoritative project order; this
plan specifies its bounded geological-history experiment and conditional rollout.

## Outcome and decision

Generate connected ranges, passes, valleys and lowlands by evolving a broad
starting landscape through authored epochs. Rivers and terrain must respond to
each other. Keep generation reproducible, preserve author intent, and make the
result practical to inspect in the existing local workbench.

**First choice to test:** Landlab as an isolated reference for prescribed uplift,
effective runoff, implicit stream-power incision and linear hillslope transport.
Use two epochs and two rock-resistance regions. Compare against the current
recipe/incision output before deciding whether to integrate an existing component
or implement a narrow project kernel. Keep Python and existing application layers.

**Sequence change:** finish a minimal batch-A comparison, then run LE1/LE2 before
committing to a large R48 path-refinement implementation. R48 remains a required
outcome: terrain, channel paths, probes and display must agree. LE3 determines
whether an evolved surface can satisfy it. If LE2 fails, return to the bounded
terrain-guided path prototype in batch B; do not pursue both as permanent backends.
LE4/LE5 and the later features below depend on a measured acceptance decision.

LE numbers identify work packages, not a competing execution order. The critical
path is minimal A → LE1 → LE2 → LE3 → basic LE5 delivery, consolidating the
range-to-lowland result in C. Strategy D then owns LE6 local enrichment; E owns
LE4 sediment and the corresponding LE5 controls. An export-only erosion result
can reach the workbench before sediment support. Change that order only with
recorded evidence from the preceding comparison.

The first release need not simulate plate motion, changing coastlines, glaciers,
weather events, meanders, sediment grain classes or planetary climate. Keep these
as separate, evidence-driven extensions. Low runoff can be an authored historical
forcing; a desert biome requires moisture/climate evidence, not erosion age alone.

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

Zoom enrichment follows later. Its first model should condition finer generation
on the immutable **final** parent terrain, substrate/cover and boundary flow,
with the existing overlap/downsample requirements. Independently evolving each
viewport from ancient terrain would change shared catchments. Replaying local
geological history would additionally require time-varying boundary levels,
water and sediment fluxes; final parent discharge alone cannot supply that.
Keep this distinction explicit rather than promising complete geological replay.

## Work packages and decision gates

### LE0 — Research and scoped plan

Completed for planning: primary papers/tool capabilities compared, mathematical
scope selected, Windows wheel-only dependency resolution recorded, and this plan
linked into strategy/TODO. No runtime adoption or quality improvement is claimed.

### LE1 — Reference environment and controlled fixtures

Depends on minimal strategy A evidence, not a completed UI comparison dashboard.

1. Create a disposable Python 3.14 research environment outside application
   dependencies. Pin the Landlab/reference stack and record hashes/licenses,
   including transitive prereleases. Import and run tiny official-equivalent
   examples. If the stack fails, record the failure and evaluate an isolated
   supported reference environment; keep the application Python version fixed.
2. Add a narrow benchmark entry point beside the existing terrain benchmarks.
   Share fixture identity, seed, coordinates, runtime hashing and artifact
   conventions. Its command/options do not exist until this package lands.
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

Depends on LE1. This is the next substantial generation experiment.

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

LE2 success justifies LE3; it is not permission to make the prototype the default.
No promise of realistic depositional plains, meanders or physical lakes is made.

### LE3 — Constraints, shared paths and final-surface acceptance

Depends on LE2 evidence. This is the highest integration risk.

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

**Gate:** satisfy strategy B's constraint, coverage, direction and sampled-profile
gates. Use fixed authored source/outlet routes and spatial catchment coverage
when a new network has different automatic branches; do not compare counts per
D8 edge or erase hard routes to improve the score. Report natural automatic
network changes separately. The initial ≥50% sampled-ascent reduction target
applies to the frozen comparable feasible cohort, not unrelated new branches.
No new >10 m rise on a previously feasible matched route; controlled gravity-bed
fixtures must be descending within declared Float32 tolerance. Lakes/backwater
are separate model cases. Finite sampling remains finite evidence.

Select an ADR and production dependency/implementation only now. If a reference
library is selected, audit the complete shipped stack and test the real packaged
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

Depends on LE3 acceptance; LE4 is required only for sediment controls/products.

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
resolution and screen scale support them. Full historical replay, if later chosen,
requires the additional boundary-time data described above and a separate gate.

## Integration map

These are proposed responsibility boundaries, not new files already present.
Avoid extracting a generic framework while implementing one experiment.

| Area | Planned responsibility |
|---|---|
| `benchmarks/` | First reference runner, scenario fixtures, convergence/ablation comparisons and paired reports; external engine imports stay here initially |
| `domain/evolution.py` (proposed) | Typed epochs, units, boundary/material settings, validation and result identity; no Landlab or filesystem imports |
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
and at most 4,096 accepted steps. This is a proposed stop/review budget, not a
measured capability or final product promise. Calibrate before larger grids.
Report complete build time separately; a fast erosion kernel is insufficient if
preparation, reconstruction or validation dominates. Add control-workspace,
reference-engine and rollback arrays to admission estimates; do not assume the
current terrain memory estimate covers them.

Prefer mature compiled scientific primitives when they fit the selected model.
Profile before Numba/Rust/GPU work. Independent ensemble runs may be parallelized
within a measured memory budget; the inner solver must retain a defined reduction
order if exact repeatability is promised. Cross-platform comparisons may use
explicit tolerances rather than unsupported bitwise guarantees.

For runtime implementation commits run the repository's pytest, Ruff and Pyright
gates plus the relevant numerical/quality evidence. For this documentation-only
planning change, check claims, links and the diff; it does not warrant rerunning
unchanged runtime tests or claiming new terrain-quality validation.

## Deferred questions with an owner

- R10/R11: depth-dependent strata, subsidence, spatially varying history and
  geological-event reconstruction; start with two-dimensional resistance/forcing.
- R14: analytical erosion if sequential cost is the blocker; do not equate an
  independent age query with a temporally continuous history.
- R16/R18: lake storage, sediment sizes, lateral erosion, fans, meanders, braids
  and deltas; each needs appropriate scale and conservation evidence.
- R15/R34: conditional finer detail versus actual local history replay.
- R17/R31/R45–R47: stochastic transport, GPU/native kernels and eventual Rust;
  measured model/workload benefit must precede adoption.
- R01/R33 and strategy F: world placement, climate/runoff feedback, aridity and
  ecological layers; separate authored wetness from inferred planetary climate.

The immediate deliverable is a visible, measured LE1/LE2 comparison. It should
answer whether a small history model is worth integrating, with enough evidence
to stop or change direction before a large rewrite.
