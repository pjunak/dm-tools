# ADR-0054: Refine observed mountain crests

- Status: Accepted and implemented
- Date: 2026-09-17
- Extends: ADR-0053; no project or build-schema change

## Context

Endpoint signs alone miss a carrier that crosses zero twice or approaches zero
and turns back. Seven regular interior observations can also lie below a sharp
crest even when the edge was selected correctly. Both omissions understate the
barriers used by the shared drainage graph. Increasing every edge's macro
sampling density would repeat expensive coastline, region and constraint work.

## Decision

Retain the canonical 257-longest-side metric grid and the existing mountain
recipe. For each positive-relief mountain region, stream its two-octave carrier
into shared candidate masks and symmetric edge barriers.

Always retain edges with a sign change or zero at an endpoint. Also admit
same-sign pairs whose sum of endpoint magnitudes is no greater than a
source-scale variation estimate. The ideal carrier's quintic fade derivative
is at most 15/8; lattice values differ by at most 2. Normalizing the two octaves
with weights 1 and 1/2 gives a directional variation limit
`5 / feature_size_km * (abs(delta_u) + abs(delta_v))`, using the same rotated,
stretched regional coordinates. Add a floating-point margin for candidate
selection. This is not the rounded full-field bound required for certified
clearance. Keep the buffered-region and land-land eligibility rules.

Evaluate the inexpensive carrier at the seven regular interior stations, then:

- refine each observed nonzero sign bracket with twelve bisection rounds;
- refine each observed same-sign local minimum of absolute carrier with sixteen
  golden-section rounds, retaining the best evaluated position; and
- keep exact sampled zeros and every original endpoint crossing eligible.

The local minimization does not establish that a bracket is unimodal. Several
extrema inside an unsampled interval can remain unseen. The fixed iteration
counts bound work; a small residual is not an adaptive clearance decision.

Evaluate the **full authored macro** at the refined positions and at all seven
regular interiors of the union of observed candidate edges. Maxima accumulate
with both endpoints; duplicate roots on one edge cannot overwrite a higher
observation. Reverse D8 directions share exactly the same barrier. Regions
with the same polygon, carrier scale and orientation reuse candidate/refinement
work even when their elevation or relief controls differ: every macro query
still evaluates the complete composition of all authored regions.

Process at most 4096 candidate edges at a time and at most 28672 full macro
positions per call. Grid storage does not retain one carrier per region; search
arrays remain batch bounded. Region metadata and total evaluation work still
scale with the authored input. Non-finite or malformed macro samples remain
errors. No raised observation means no barrier array is needed downstream.

Priority-Flood, D8, MFD, retention and automatic-cut budget formulas are unchanged.
The additional observations can change routing, channel selection, nodal cut
ceilings and delivered shaping. Authored geography and input authority remain
unchanged. Record generator `coastline-constraint-terrain@13` and automatic
valleys `regional-budget-mfd-d8-valleys@11`; preserve named seeds, landform/noise
identities, schemas and settings. No dependency or compatibility path is added.

## Validation and limits

Test off-station crossings, paired roots, tangent approaches, root coverage,
symmetric reuse, batch independence, duplicate carriers, input immutability,
invalid samples and streamed carrier lifetimes. Compare old and new observations
against dense finite profiles on public regional fixtures, separately from
finished-ground channel profiles and fresh-process generation cost. See the
[measured comparison](../research/2026-09-17-refined-mountain-crests.md).

Better barrier observations do not imply every river metric improves. Routing
on a temporarily filled surface can still select paths whose final ground has
budget-limited climbs. Other recipes, authored narrow features, regional blends,
crest-height modulation and procedural detail need separate coverage. Features
smaller than the probe spacing, multiple extrema within one probe interval,
whole-route conditioning, rounded D8 turns and zoom enrichment remain open.
