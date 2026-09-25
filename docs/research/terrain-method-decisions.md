# Terrain method decisions and failed experiments

Updated 2026-09-25 against implementation `97ae47a`. This is the living record of
material generation approaches that were rejected, constrained or retained only
as references. A failed method does not remove its desired feature from the plan.
The [strategy](../strategy/README.md) owns execution order; dated reports own the
original measurements, source identities, commands and validation boundaries.
Supporting sampling/convergence and performance rejections remain indexed in
[research status](status.md), including the slower
[coast-index candidate](2026-09-05-selective-terrain-sampling.md). This register
concentrates on methods that change the generation-quality decision.
The [groundwater and architecture reassessment](2026-09-25-groundwater-and-terrain-architecture.md)
explains the replacement proposals. Those proposals have not been simulated here.

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

## What the failures change

Preserve the feature goals: believable rivers, geological aging, useful zoom detail
and varied valleys. Change the construction method when an experiment isolates a
representation or input-policy restriction. Separate authored requirements from
procedural guesses before fitting; test coupled relief and network evolution before
freezing a final DEM. Keep the application and Python implementation boundaries.

Groundwater, karst and lateral erosion are **new, untested hypotheses here**, not
explanations established by T01-T08. They need independent controls and budgets.
The [reassessment's staged experiments](2026-09-25-groundwater-and-terrain-architecture.md#implementation-sequence-and-stop-rules)
define the next comparisons and when a larger structural change is justified.
