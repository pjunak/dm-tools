# ADR-0041: Review complete downstream outlet profiles

- Status: Accepted
- Date: 2026-09-11
- Extends: ADR-0040; replaces build v13 and water/outflow review identities

## Context

The existing finer review ends at the first outward attachment. Later D8 edges
can cross narrow authored ground rises while their canonical endpoints descend.
The public downstream-barrier fixture demonstrates a 43.85 m local climb that
is below both the path's global maximum and its lake's imposed level.

## Decision

Sample the entire inspected external candidate path with the existing bounded,
feature-guided Float32 evaluator. Keep the selected attachment, receiver graph,
vector containment rules, ground DEM and incision budgets. One profile budget
covers the complete path; excessive counts return empty evidence and block
transfer. Reuse existing sampling and geometry tools without new dependencies.

Preserve every canonical vertex and export its profile index. Require exact
Float32 ground agreement at those vertices; disagreement fails generation.
Separate graph scope (`reaches_terminal`) from profile availability. A geometry
or topology failure can retain a sampled prefix; a terminal reached by the graph
can still have no evidence when over budget or an invalid boundary context.

Extend the conservative non-rising-ground rule to these finer samples. Compute
`max(h - cumulative_minimum(h))` using Float64 differences of Float32 samples.
A result greater than 0.01 m blocks transfer. This prevents gradual small steps
from hiding a larger climb. Record the first maximum excursion's crest and its
first preceding minimum, or null indices for zero rise/unresolved evidence.
The old rise/count fields continue to describe adjacent canonical steps.

Do not substitute the lake level for external ground or infer external pools.
Adverse bed slopes can carry real water under suitable hydraulic conditions;
this check does not model water surfaces, energy, discharge or storage. A
blocked profile therefore requests explicit pool/level review rather than
certifying physical impossibility. Submerged short outlet-contact crests keep
their existing water-level rule.

Basin details shows profile scope, total samples, largest climb and exceeded
budgets. Red review diamonds mark the blocked climb crest, even when it differs
from the global maximum. Captured area stays retained for blocked outlets.

Build v14 exports `outlet_route.downstream` in diagnostics; remove v13's schema.
Record `authored-basin-water-review@8` and `captured-mfd-reviewed-d8-outlets@6`.
Keep project v5, numeric archive layouts and `feature-guided-float32-water-checks@2`.

## Consequences and validation

Finer external evidence no longer stops at the attachment, but internal wet
links remain canonical. Sampling corridors are not error bounds, and terminal
reach is not an ocean-level certification. Many-lake cost, procedural extrema,
internal connectivity and hydraulic assumptions remain separate work.

Tests cover local crests below an earlier global maximum, cumulative sub-tolerance
steps, accepted small rises, complete-path budget failure, single-node/prefix
scope, canonical-height mismatch, exported vertex mapping, deterministic order
and resolution, and conserved captured area. The public generated fixture
exposes the prior false clearance and locates the crest in the actual overlay.
The [measured rundown](../research/2026-09-11-downstream-outlet-profiles.md)
records preserved numeric products, focused cost and remaining priorities.
