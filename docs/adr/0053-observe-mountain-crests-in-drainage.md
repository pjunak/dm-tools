# ADR-0053: Observe mountain crests in the drainage graph

- Status: Accepted and implemented
- Date: 2026-09-16
- Extends: ADR-0052; no project or build-schema change

## Context

Node-only routing can connect two descending endpoints across an unobserved
mountain crest. The regional recipe raises ridges where its broad noise carrier
crosses zero. The previous source-aware floor fitting cannot remove these
obstacles when the required incision exceeds the cut ceiling.

Changing individual receivers within the previous filled-height ordering did
not resolve the two largest observed barriers. Observing all edge interiors in
a new graph did, but full-grid sampling was too costly relative to preparation.
See the [experiments](../research/2026-09-16-mountain-crest-routing.md).

## Decision

Keep the fixed 257-longest-side metric planning grid. Share the regional noise
basis with landform generation; no terrain-recipe or named-seed change is made.
For each positive-relief mountain region, find D8 edges whose endpoint carrier
signs differ or include zero. Consider endpoints inside the region buffered by
the longest possible grid edge. Sample seven interior positions at fractions
1/8 through 7/8 on the union of candidate edges, in batches of at most 4096 edges.
Overlapping regions and opposite directions reuse the same observations.

Evaluate the full **authored macro** at these points using the same coastal,
regional and constraint operations as routing nodes. The barrier is the maximum
of those finite observations and both endpoints. Missing/non-finite sampler
results are errors, never evidence of a clear route. Non-land interiors are sea
level observations; the node/coast topology is retained. This does not add a
land receiver or certify a connection across water.

Store a symmetric D8 barrier array only when an observed interior raises a
barrier above its endpoint maximum. Without mountains or raised observations,
use the node-only graph; this is also the appropriate primitive for DEM-only
diagnostics that have no between-node observations.

Priority-Flood includes the edge barrier in each candidate level. With edge
observations, settle nodes when popped and allow earlier candidates to improve;
first discovery can cross a higher pass than a later path. With node heights
alone, first discovery remains optimal and avoids unnecessary queue work.
The filled surface remains a temporary planning product, never the DEM.

Both MFD recipients and the steepest D8 receiver must be strictly lower in this
filled ordering and reachable over a barrier no higher than the source routing
level. Apply this rule to both models so MFD does not leak across a crest that
D8 avoids. Retention terminals remain fixed and do not distribute area. Positive
routing grades preserve acyclic accumulation and connection to a coast or
retention terminal on the sampled graph.

Recompute accumulation, channel selection and automatic shaping from that graph.
Unlike the previous reconstruction-only changes, **canonical routing, incision
and nodal incision ceilings can now change** with the network. The regional and
global budget formulas, authored inputs and constraints retain their authority;
no cut allowance is expanded to force a route through a crest.

Record generator `coastline-constraint-terrain@12` and automatic valleys
`regional-budget-mfd-d8-valleys@10`. Keep landform/noise IDs, schemas and public
settings. Add no dependency, legacy mode or output editing operation.

## Validation and limits

Test late lower-pass relaxation, D8/MFD barrier agreement, area conservation,
strictly decreasing receiver ranks, retention, input immutability, invalid
observations, symmetric edge reuse, bounded batches and regional regression
cases. Profiles and appearance are checked against the previous commit and
additional seeds. Paired fresh-process measurements cover runtime, memory and
full product hashes. The dated report records added cost, timing variation and
mixed final-ground diagnostics alongside the improved interior profiles.

This is targeted finite evidence. Endpoint signs can miss multiple crossings or
tangencies, and seven probes can miss a crest between probes. Other landforms,
authored features, regional blending and residual detail are not exhaustively
covered. Known graph barriers can still require temporary filling; downstream
cut budgets may leave final-ground climbs. This neither certifies continuous
clearance nor completes physical rivers, rounded D8 turns or zoom enrichment.
