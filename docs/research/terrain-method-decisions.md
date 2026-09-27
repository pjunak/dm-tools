# Terrain method decisions and failed experiments

Updated 2026-09-27 through the geological landform guidance batch against baseline
`4b691d8`, following world-to-terrain integration. This is the living record of
material generation approaches that were rejected, constrained or retained only
as references. A failed method does not remove its desired feature from the plan.
The [strategy](../strategy/README.md) owns execution order; dated reports own the
original measurements, source identities, commands and validation boundaries.
Supporting sampling/convergence and performance rejections remain indexed in
[research status](status.md), including the slower
[coast-index candidate](2026-09-05-selective-terrain-sampling.md). This register
concentrates on methods that change the generation-quality decision.
The [groundwater and architecture reassessment](2026-09-25-groundwater-and-terrain-architecture.md)
explains the replacement proposals. Groundwater, karst and lateral erosion remain
untested here; T09-T13 measure valley construction, automatic placement, bounded
raster delivery and exploratory feature preservation.

## How to maintain this record

For each substantive numerical experiment, update this register, its dated report,
[status](status.md) and the affected [TODO](../../TODO.md) checkpoint together.
Record the hypothesis, unchanged control, input roles, measured outcome, diagnosed
cause versus unresolved explanation, reusable work, disposition and revisit gate.
Keep stable IDs below. Add later evidence to the disposition; never rewrite a
historical report to imply a failed candidate was accepted.

Distinguish unsupported input, a proven constraint conflict, solver failure,
budget exhaustion and a completed candidate failing quality. Only a verified
conflict witness establishes infeasibility. Tests passing means the experiment
behaves as specified, not that its terrain is realistic. New methods need new
identities and prospective gates; a changed fixture is not a repair of an old result.

## T01 - Replace D8 valley shoulders with flow signals

**Tried:** fully flow-connected D8 shoulders and full MFD replacement. The
[algorithm report](2026-09-03-terrain-algorithm-options.md) records retained D8 gaps
for the former and worse finished-surface drainage diagnostics for the latter.

**Why / boundary:** a better accumulation signal did not establish a connected
continuous valley. This evidence rejects those replacements, not MFD accumulation
as a hydrological tool. A small, major-trunk-gated MFD correction was retained.

**Replacement / revisit:** construct shared bed, bank and junction geometry (B/R48),
using accumulation as an input. Compare contributing-area accuracy separately from
surface capture; merely increasing the MFD blend is not the next experiment.

## T02 - Use stream order or lower density as the main quality fix

**Tried:** direct Horton-Strahler width and 3%/1% depth adjustments in the
[algorithm report](2026-09-03-terrain-algorithm-options.md). Width violated the
synthetic downstream-width invariant; depth increased coarse diagnostic fill on
Tharkeniss. A later default density of 0.75 failed the existing shoulder-width
control in the [connected-review batch](2026-09-24-connected-drainage-review.md).

**Why / boundary:** topology alone is not a material/confinement/flow model;
changing initiation also changes actual incision. Fewer visible lines cannot
establish better ground. These results do not reject authored density controls.

**Retained:** order as a descriptor, explicit density with default 1.0, connected
scale-aware inspection. **Replacement:** discharge, material and confinement for
width; recharge/transmissivity as a separate drainage-density hypothesis (R18/R24).
Revisit against the original invariants plus complete-network coverage and actual
terrain, rather than accepting a less crowded screenshot.

## T03 - Preserve parent means with bilinear bubble detail

The [parent-cell experiment](2026-09-23-parent-cell-preservation.md) preserved nodes,
bilinear boundaries and cell means to Float32 rounding, with exact same-density
overlaps. It nevertheless lost source structure, moved authored heights by up to
29.161 m, changed shared samples across densities and worsened eight sampled
channel edges. Rejected for runtime use.

**Why / boundary:** preserving statistics relative to a bilinear reconstruction
was not preservation of the actual authored field or inherited hydrology.
**Retained:** explicit restriction tests, immutable-parent identity and overlap
controls. **Replacement / revisit:** condition on accepted parent landforms,
constraints and boundary flux; preserve supported structure through a deterministic
reconstruction and test coarse-scale agreement and channels together (D/R34/LE6).
The implemented residual-detail tools remain experimental, not accepted history replay.

## T04 - Evolve a landscape, then deliver its D8 nodes bilinearly

The [first history comparison](2026-09-24-landscape-evolution-reference.md) completed
22 cases and demonstrated useful chronology, uplift and resistance response.
Endpoint-descending diagonal channels still had internal rises of 37.51-45.48 m
in the 625 m examples; a 312.5 m case retained a 24.64 m rise. Cardinal controls
were clean. A 156.25 m, 197,505-node run stopped at the 60 s solver budget and
has no accepted final state.

**Why / boundary:** delivered interpolation and grid-direction sensitivity remain
problems even when solver controls pass. Float32 rounding was much smaller than
these rises. The budget stop is a cost observation, not proof the physical model
is wrong or that additional resolution would pass.

**Retained:** isolated Landlab reference, chronological forcing, analytic tests,
material accounting and complete/incomplete publication. **Replacement / revisit:**
co-evolving terrain/network plus hydrologically supported reconstruction; separate
process scale from export resolution. Revisit on fixed quality/cost gates. Do not
respond only by globally refining the grid or raising the runtime ceiling.

## T05 - Require routing diagonals in a triangle reconstruction

The [frozen comparison](2026-09-24-frozen-channel-reconstruction.md) retained all
1,183 full routes across 22 states. All 1,030 nodally nonascending routes had zero
sampled ascent at 100 m and 25 m station spacing. The 153 routes with nodal climbs
remained unresolved. This uses saved Float64-snapshot routing, not the first
history report's rerouted delivery graph; those totals are not a direct before/after.

**Why not adopted:** unchanged D8 directions, slope creases, off-grid target errors
and reconstruction-volume changes. Exact nodes are insufficient to preserve a
continuous authored height field. **Retained:** numerical control and full-route
accounting. **Replacement / revisit:** shared physical valley geometry with explicit
hard-target evaluation and a separate composition-volume ledger (B/R32/R48).

## T06 - Deform paths and ground together on a bounded mesh

The [physical-path comparison](2026-09-25-physical-channel-paths.md) retained all
1,183 routes without new uphill routes and reduced D8-aligned length to 56.99%.
All 22 cases failed sampled no-fill admission; 17 exceeded the diagnostic 30 m cut
limit. That limit was not the later native regional-cap implementation. Spacing
changes also moved many receivers/outlets at shared physical locations.

**Why / boundary:** geometry improvement required inadmissible surface changes;
native authoring/divide acceptance was not established. Long straight pieces and
creases remained. **Retained:** coupled geometry and receiver/outlet diagnostics.
**Replacement / revisit:** constrained construction before freezing the surface,
with generated relief distinguished from authored hard targets. Preserve this
fixed-state comparison rather than relabeling its cuts as geological erosion.

## T07 - Fit a downhill network into a fixed raster under native caps

The [network-led fit](2026-09-25-constrained-network-surface.md) preserved native
cut/no-fill bounds, protected heights and divide, and removed 34.7356 m of sampled
network ascent. Independent routing on a common 125 m grid still found 16 interior
sinks at 500 m process spacing and 19 at 250 m; zero of four heads reached their
intended mouths. The source had zero interior sinks.

**Why / boundary:** a descending guide is not necessarily a transverse minimum,
nor a connected valley that surrounding water reaches. More samples on that guide
cannot by themselves address the missing surface geometry. An ambiguous L1 fit
was replaced by a unique quadratic objective; fixing optimization ambiguity did
not fix capture.

**Replacement / revisit:** river-aligned cross-sections, confluences and coastal
transitions, checked in both the local field and delivered raster. Keep this hard
fixture as a control; use a separately identified fresh-construction case to test
movable automatic guides. Native limits are not silently widened (B/R48).

## T08 - Add bank endpoint inequalities to the fixed surface

The [bank experiment](2026-09-25-valley-bank-feasibility.md) added 525 physical
probes, nearest-reach junction ownership and a sea-level mouth taper. All endpoint
checks passed in feasible 500/250 m cases, but 255/273 inward cross-sections still
climbed and no head reached its mouth. Sinks changed from 16 to 15 at 500 m and
19 to 30 at 250 m. At 1,000 m, six bank pairs were locally infeasible under the
conservative bounds. A separate pinned-bed conflict had a verified shortfall.

**Why / boundary:** bank endpoint drops do not constrain the intervening surface.
The report's limited bilinear-cell argument explains a representation restriction
for exact straight oblique minima; it does not prove that rasters or other valley
representations cannot work. Conservative incident-cell bounds can over-restrict a
candidate; local infeasibility is not geological impossibility.

**Assumptions corrected:** constant positive bank drop at a zero-height mouth
contradicted the no-fill/nonnegative constraints; tapering removed that conflict.
Junction probes needed ownership by the nearest network reach. A solver returning
invalid ground is an execution failure, not evidence that authored inputs conflict.

**Retained / replacement:** keep conflict diagnostics and the manufactured positive
control. Stop expanding endpoint inequalities as the main strategy. Test connected
local patches, then bounded alternate representation if delivery itself remains
the blocker. An open-draining control still needs four captured heads and zero new
sinks; groundwater is not an exemption for this fixture.

## T09 - Construct connected local valleys then deliver a raster

**Tried:** analytic rounded valley unions, explicit coastal transitions and compact
hard-height support, followed by bounded Float32 raster projection. The
[report](2026-09-26-connected-valley-patches.md) keeps the fixed/native control and
a separately declared 600 m / 120 km3 fresh-construction envelope. The same guides
are retained; automatic relocation and history evolution are not yet tested.

**Measured:** fresh local routing on the common 125 m grid captures 4/4 heads with
zero interior sinks. At 250 m, raster delivery captures 3/4 with one sink; at
500/1,000 m it captures none. Fixed/native quality remains rejected. One fresh
local guide route, 29/525 inward sections and six bank endpoints still fail, so
successful capture does not accept the complete local field. Removing only the
mouth transition changes fresh local capture to 0/4 with four sinks. Repeat and
quarter-turn checks pass; no general-angle or world-scale result is claimed.

**Why / boundary:** coastal approach geometry affects actual capture. The remaining
250 m raster blockage is near a hard-height correction of up to 121.756 m; the
local field routes around that neighbourhood. This diagnoses a layout/support/
delivery interaction, not proof that the hard target is impossible or rasters are
unsuitable. Uniform refinement does not resolve the coarse failures by itself.

**Failed assumptions corrected:** node cut bounds allowed 376/262/210 inter-node
violations of a nonlinear fresh cap. Conservative incident-cell bounds remove
them without increasing budgets. Computing pin corrections from an unclipped
proposal also falsely rejected a feasible case; use the admitted field as the
base. Regression controls and hard-admission checks cover both errors. Genuine
constraint conflicts and unsupported overlapping pin cells remain explicit.

**Retained / replacement:** retain analytic sections, shared junctions, the
coastal transition, separate composition accounting and local/delivery diagnostics.
Keep production rejection. Next compare hard-target-aware layout and bounded
automatic guide movement, then one local reconstruction if delivery still blocks
quality. Preserve the fixed control, hard targets, coast/divide and declared
envelopes. Require guide/bank/capture acceptance on actual delivery before coupling
history, expanding the cohort or adopting LE3/WC2. Groundwater cannot hide this
open-drainage failure.

## T10 - Move automatic guides around hard height targets

**Tried:** explicitly automatic-edge relocation within a 1,500 m corridor, with
1,000 m pin clearance and at most 25% reach-length growth. The
[report](2026-09-26-hard-target-valley-layout.md) preserves every original vertex,
head, junction, mouth and reach ownership, the same broad source, all hard targets
and the previous fresh envelope. Fixed/native controls are rerun unchanged.

**Measured:** an 800 m detour changes 250 m raster capture from 3/4 to 4/4, interior
sinks from one to zero, unresolved guide routes from one to zero and interior
samples missing the coast from 1,115 to zero. Repeat and quarter-turn checks pass.
All hard-input gates remain intact. Local banks still have 21/575 inward failures;
the raster has 222/575, and coarser delivery still fails. The control's 525 bank
probes and candidate's 575 are different denominators, not matched-pair counts.

**Why / boundary:** a generated guide need not intersect the neighbourhood used
to represent a genuine height target. The correction remains large (126.313 m at
250 m), but the relocated channel avoids it. No target was lowered, and no river
outlet was dropped. Four-head capture and coast coverage do not establish bank
shape, prescribed basin areas or realism on unseen landscapes.

**Rejected alternatives:** a sine-squared candidate family could not clear the
pin within the same corridor; this was search exhaustion, not global infeasibility.
A sampled-envelope bed lift worsened local inward failures from 21 to 25 despite
fewer endpoint errors. It is not retained. The dated report preserves these
exploratory observations separately from the controlled final cohort.

**Retained / replacement:** retain bounded automatic placement and original-route
matching. Finish bank construction at heads/junctions/cap transitions; compare a
bounded channel-conforming reconstruction only after separating local shape from
delivery loss. Keep coarse failures and native-control rejection visible. Require
complete bank/guide/capture and held-out evidence before application/history
integration; this result does not justify a whole backend rewrite.

## T11 - Construct head and mouth sections before raster delivery

**Tried:** a cap-aware generated head adjustment ending at its first confluence,
perpendicular mouth sections and an explicit inland outlet wedge. The
[report](2026-09-26-valley-heads-and-mouths.md) keeps the same 575 bank pairs,
60.732 km graph, source, hard heights and 600 m / 120 km3 fresh envelope.

**Measured:** ordinary local inward/endpoint failures change from 21/5 to 0/0.
An added <=2.5 m bank check also passes the existing 1 cm tolerance; maximum local
rise is 0.006195 m. Local capture and the 250 m raster capture remain 4/4, with zero
sinks. All hard-input gates pass. Raster banks still fail: at 250 m, 217/575
ordinary and 241/575 dense inward sections, plus five endpoints. Coarser raster
capture remains zero. Twelve control cases retain their previous numeric hashes.

**Why / boundary:** the source-minus-cut floor tilted one clipped head bank
uphill; the coastal-plane taper tilted oblique sections away from the channel.
Changing the generated profile/section geometry fixes those local cases without
moving a hard target. Raster delivery still combines conservative cap projection
and interpolation loss. Sampled success is not a continuous or world-scale proof.

**Rejected alternatives:** local radial-envelope lifts remove the main head
failure but create new bend defects. A whole-tributary cubic taper passes 25 m
stations but fails three sections when sampled more densely. Quintic and
straight-tail-only tapers also leave defects. A linear taper adds constant grade
without the cubic's steeper middle. The first perpendicular-mouth trial left an
outlet-plane edge defect; preserving relief in the inland wedge removes it. Do
not restore any of these recipes as hidden fallbacks or loosen the dense check.

**Retained / replacement:** retain the local head/mouth component, matched bank
profiles, dense guard and original capture controls. T12 now isolates and reduces
cap-projection loss while preserving whole-cell protection. T13 subsequently
isolates representation loss and prioritizes a feature-preserving query boundary.
Keep production rejection until complete delivered bank/guide/capture, held-out
and broader orientation gates pass. No history, groundwater or product engine
was added by this experiment.

## T12 - Protect cell interiors with tighter delivery capacities

**Tried:** one-sided curvature allowances for the smooth rectangular-divide cap,
with constant whole-cell protection where subtracting the allowance would create
negative capacities. The [report](2026-09-27-cell-safe-terrain-delivery.md) derives
the bilinear interior bound and retains the same graph, local field, 575 bank
pairs, hard targets and fresh budgets. Five separate rectangle controls exercise
unaligned corners, a thin footprint and domain boundaries.

**Measured:** worst 250 m dense bank rise falls from 54.062 to 0.316 m; ordinary /
dense failures from 217/241 to 214/238, endpoints from five to two. Capture remains
4/4, with zero sinks and descending guides. Hard-input and cap checks pass;
repeat and quarter-turn delivery match exactly. The maximum envelope correction
falls from 93.045 to 18.175 m, but the hard-height correction remains 118.714 m.
Coarse routing and complete delivered bank quality remain rejected.

**Why / boundary:** the incident-cell minimum safely overprotected large areas.
A second-order interpolation allowance removes the large artificial head rise.
Bilinear sampling still displaces many bank minima, so smaller error amplitude
is insufficient. The proof covers this cap and bilinear field, not arbitrary
geometry, another interpolator, a native-limit policy or a new landscape.

**Rejected alternatives:** nodal caps alone violate the interior limit. Clipping
negative curvature-adjusted capacities also breaks the bound beside a quadratic
zero; valid nodes do not prove valid cells. The regression retains that explicit
counterexample. Omitting cap or hard-height projection is not a delivery option.

**Retained / replacement:** retain the tighter capacities and matched evidence.
T13 supplies representation evidence before the proposed large bilinear bank
solve: analytic alignment changes bank quality at similar height error, and
preserved features retain the local field through reopening. Keep local
feasibility checks and defer larger solves until their cell layout can represent
the requirements. Establish a new interior bound for any changed interpolator.
Complete delivered and held-out acceptance still precedes normal generation,
history coupling or LE3/WC2.

## T13 - Preserve features instead of reconstructing them from nodes

**Tried:** seven analytic valley orientations, bounded single-cell bank feasibility,
quadratic/cubic interpolation of the current network, and trusted numeric storage
of prepared valley fields. The [report](2026-09-27-feature-preserving-terrain-delivery.md)
records exact settings, sources, hashes and short timings. These are exploratory
ignored scripts; no supported benchmark API or product reader was added.

**Measured:** world-bilinear analytic sampling fails 114/238 profiles, while a
river-aligned strip fails none at similar maximum height error. On the network,
quadratic interpolation reduces dense failures from 238 to 25 but raises the
worst excursion from 0.316 to 5.195 m and loses all four outlets. Cubic and
bounded hard-pin variants also fail. Prepared-field saving/reopening exactly
preserves all 575 profiles, common Float32 heights and sampled quality gates at
three background spacings plus a quarter turn. Bilinear delivery after reopening
restores 267 / 251 / 238 / 238 failures.

**Why / boundary:** scalar height accuracy does not determine whether the intended
bed remains a transverse minimum. Higher-order interpolation can overshoot and
move extrema; restoring sampled caps and pins does not restore capture. The
one-cell witness supports the existing limited bilinear restriction, not global
infeasibility. Roundtrip equality preserves an already passing local fixture;
it is not unseen-landscape, safe-reader, tile/LOD or continuous-field acceptance.

**Disposition / replacement:** reject the tested generic spline substitutions.
The [guarded snapshot follow-up](2026-09-27-prepared-feature-snapshots.md) now
retains geometry and background parameters in a formal benchmark artifact, with
complete network reopening, deterministic identity and bounded validation. All
575 dense profiles and original metrics remain exact; query order, batches and
same-field tile/halo agreement pass. A returned-metadata ownership issue was
fixed and covered by a regression. Keep held-out geometry, irregular mouths and
real parent/detail filtering as the next gates. These overlap results do not
certify newly generated detail or replace raster authority. Prefer local analytic
patches, with channel-aligned strips or constrained triangles as measured
fallbacks. Defer the full bilinear solve behind representability checks. Current
Float32 DEM authority remains in force; any richer source requires an ADR and
coherent schema/consumer changes. Keep history and world integration gated.
Consult the user before longer tests; the completed probes took 0.855 / 20.625 s.

### T13 follow-up: wider geometry and product priority

The [world-to-terrain report](2026-09-27-world-to-terrain-workflow.md) records a
12.07 s exploratory probe of four modified layouts. Capture, hard controls and
bounds passed; 1–4 inward sections failed per case, with 0.106–0.606 m excursions
and no endpoint failures. The cause of each small excursion remains unisolated.
This is evidence against general acceptance of the current patch family, not
proof that the underlying feature is impossible. Retain analytic patches with
aligned strips or constrained triangles as fallback candidates.

The user chose a usable world-to-terrain workflow next. Further small bank tuning
is deferred behind major features; it remains required when adopting the new
construction model. The handoff uses the existing terrain engine and preserves
the Float32 authority contract.

## T14 - Treat semantic continent pieces as separate physical terrain

The [world handoff report](2026-09-27-world-to-terrain-workflow.md) records a
projection-centre change caused solely by splitting identical physical land
into unequal ownership pieces. Separate selection would additionally make an
internal border a coastline. Dissolve connected physical land before both
projection-centre selection and terrain generation. Exact mask and Float32
equality now guard equivalent ownership partitions.

Source offsets are a distinct cause: matching native border curves displaced
by 0.0015-0.0101 map units retained false coastal grooves even after connected
components were selected. Confirmed source repairs remove those slivers.
Globally buffering or closing every narrow water gap was rejected because it
would alter genuine straits. The native export API was unavailable; a precise
SVG segment correction preserved all other imported features. Private source
repair is not an automatic importer heuristic or a new erosion model.

The same batch replaced a false continental-area subtraction check with direct
MultiPolygon topology validation; its 0.05078125 m² roundoff was not overlap.
Retain these workflow fixes while keeping regional projection support and
physical generation acceptance as separate next gates.

## T15 - Use inward region fades as a complete geological partition

The [landform transfer report](2026-09-27-geological-landform-guidance.md) records
a 5.088 s public paired build with the same world, coast and mask. Explicit controls
reach the terrain and preserve nested overrides, but visible polygon-shaped rims
remain. Every inward weight reaches zero at a shared recipe boundary, exposing
the generic background; equal settings avoid this after dissolving.

Retain the input/transfer feature. Do not accept broad terrain realism from this
comparison. Test continuous shared-boundary blending next, with fixed coast,
priorities, blank holes, hard heights and sampling checks. This is separate from
calibrated geological forcing or physical aging.

Triangulation and implicit category/age conversion were rejected design shortcuts,
not executed failed experiments. Triangulation would introduce artificial fade
edges under the current rule; age conversion would invent unreviewed coefficients.

## What the failures change

Preserve the feature goals: believable rivers, geological aging, useful zoom detail
and varied valleys. Change the construction method when an experiment isolates a
representation or input-policy restriction. Separate authored requirements from
procedural guesses before fitting; test coupled relief and network evolution before
freezing a final DEM. Keep the application and Python implementation boundaries.

Groundwater, karst and lateral erosion are **new, untested hypotheses here**, not
explanations established by T01-T13. They need independent controls and budgets.
The [reassessment's staged experiments](2026-09-25-groundwater-and-terrain-architecture.md#implementation-sequence-and-stop-rules)
define the next comparisons and when a larger structural change is justified.
