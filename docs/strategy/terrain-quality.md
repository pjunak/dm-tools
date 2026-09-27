# Terrain quality and specialized feature reference

Updated 2026-09-28. The [implementation plan](README.md) owns the only execution
order. A-F below are retained topic identifiers, not a sequence to finish before
context and aging can be connected. These detailed controls support M1-M4 when a
specific defect blocks an interpretable experiment, and govern M5 adoption or the
later feature named in each section. Historical measurements retain their dates.

Keep hard geography, authored-intent, unit, numerical and execution-budget checks
at every stage. Failed visual/physical-quality controls must remain reported;
they prevent stronger acceptance claims, not all experimental application work.
The [research catalog](../research/decision-catalog.md) records technology choices;
the [method register](../research/terrain-method-decisions.md) owns failed methods.

## A. Make quality differences easy to see and measure

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
broader descriptors and interface additions must not delay M1-M4 integration.
Select a small public bare-earth analogue set with provenance and matched scale;
Earth distributions are comparison ranges, not mandatory fictional geology.

Add paired map comparison and a selected-channel longitudinal profile to the
workbench, with source/result identity, resolution and conflict status visible.
Surface feature-resolution warnings using already recorded output/process
spacing. Support these inspection actions before automatic preview generation;
smaller output rasters still pay fixed routing/water preparation cost.

**Deferred routing comparison (M5, or a demonstrated M1-M4 blocker):** global convergent flat routing versus
current Priority-Flood tie handling, using the existing basin primitive where
appropriate. Check topological order, barriers, retention terminals and both D8
and MFD accounting. Keep an unchanged algorithm control; do not combine this
with a new density default or curve renderer.

**Exit:** one reproducible paired report, known failure locations, explicit metric
units/denominators and a reasoned accept/reject result for the flat experiment.
Do not spend several batches perfecting the dashboard. A useful minimal report
supports the integrated comparison; the analogue atlas can grow in M5.

## B. Make a river path and its terrain agree

R48's quality outcome for M5 remains: terrain
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

**Deferred quality batch (B1 / M5):** add held-out bends, short tributaries, junctions,
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

**Replacement decision (B2 / M5):** compare a construction and delivery pair in
the existing two-epoch reference so relief and the automatic network can evolve
together before publication. A local capture count alone is insufficient; require
the bank/guide and hard-target gates as well. Do not immediately rewrite the
whole backend. Use held-out seeds, oblique orientation, process spacing, hard
constraints and actual-ground inspection. M1-M4 can integrate the existing reference
experimentally; these controls govern replacing the default or claiming an
accepted capability. More endpoint penalties, hidden fill, larger undeclared cuts and uniform whole-world refinement are not the next strategy.

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
remain rejected. Use integrated M3-M4 results to select which local or delivered
geometry failure to address in M5; additional successful point constraints alone do not accept it.
For changed automatic networks, match authored source/outlet routes and spatial
catchment coverage as specified in LE3; D8 edge counts are not comparable.
D-infinity can be an accumulation comparator; it is not a substitute for channel
geometry. A full irregular/TIN backend requires separate evidence.

## C. Generate one convincing range-to-lowland system

Build on R08/R09/R14/R32/R40/R43: peaks and saddles, subordinate spurs, tributaries,
confined upper valleys and broader lower valleys should describe one landscape.
Keep surface ridges, drainage divides and active channels distinct. Add explicit
pass/per-vertex controls where the fixture requires them; avoid a large new preset
catalogue before one connected system works. [Line-owned profiles](../terrain-structure-profiles.md)
now supply explicit ridge/pass/spur/floor guidance and a public connected example.
[Shared absolute crests](../research/2026-09-27-shared-ridge-crests.md) now preserve
contacts through smoothing and reject incompatible junction heights. Generated
branching, junction-aware editing, tangents and cross-sections are deferred to M5;
the examples do not accept the full structural realism milestone.

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

## D. Complete local enrichment, then connect it to zoom

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

## E. Add water quantity and richer landform processes

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

## F. Derive ecological layers and evaluate richer world processes

World placement, ocean context and seasonal climate/runoff are now W/WC0-WC4
inputs introduced in M1-M4, not deferred until this phase. WC6 uses
their accepted fields for climate/life-zone views, biome suitability and separate
wetland/substrate layers. Retain uncertainty and classification-version metadata.
A bog can occur on a tundra plain; a field is a human land-use decision.

Advanced ocean circulation, plate reconstructions and geological carbon/weathering
cycles remain optional research. The [new world-context review](../research/2026-09-24-world-context-enrichment.md)
compares established and newer tools, including ExoPlaSim and the 2026 Generic-PCM
reduced ocean model. None is an application dependency or a required full-planet
simulation. Select one external comparison only when it answers a measured gap.
The [earlier world-systems inventory](../research/2026-09-04-technology-and-world-systems.md)
remains historical background; the [main plan](README.md) owns execution order.
