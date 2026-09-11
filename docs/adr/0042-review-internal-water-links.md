# ADR-0042: Review internal water links

- Status: Accepted
- Date: 2026-09-11
- Extends: ADR-0036 and ADR-0041; replaces build v14 and water/outflow identities

## Context

A clear shoreline and external outlet do not establish internal pool connectivity.
Two canonical wet nodes can straddle a narrow above-water feature. The current
single-pool rule then collects water across a barrier it never sampled.

## Decision

For a lake that passes existing outlet, shoreline and coarse-component checks,
inspect every vector-contained undirected D8 wet-to-wet link once. Preserve the
selected water contact. Reuse quarter-grid and feature-guided Float32 sampling,
and require exact canonical endpoint agreement. Remove links whose maximum
sample exceeds the imposed water level plus 0.01 m. Submerged crests remain
passable; this is level containment, not the external non-rising-ground rule.

Traverse the remaining wet graph from the selected contact. Clear alternate
paths can avoid a rejected link. Preserve the existing requirement that all wet
nodes reach this contact: otherwise retain all captured area and keep the outlet
blocked. Do not pick another contact, drain one newly separated pool or bridge
through dry nodes. Dry collection and integer-flat routing remain unchanged.

Separate existing profile planning, position construction and ground evaluation
without changing the sampling algorithm. Share 4,096-sample evaluation batches
across links. Limit the whole lake network to 65,536 requested samples, counting
repeated endpoints. Reject excessive baseline or refinement counts before any
positions or ground evaluation. A failed count is a required lower bound and
exports no per-link evidence or contact-reach result. A one-node wet component
has no links and needs no additional probes.

Export each link's canonical endpoint indices, sample counts, refinement limit,
maximum ground and first maximum location, plus the blocked flag. The complete
network exports candidate/blocked counts, selected-contact reach and budget state.
Do not duplicate complete ground profiles for every clear link in diagnostics.
Null network evidence means prior eligibility checks prevented review, not clearance.
The original coarse wet-component count remains separately identified.

Show internal barrier maxima as red diamonds and explain blocked links, alternate
paths, contact reach and unresolved budgets in Basin details. Preserve the DEM,
water surface, authored constraints, incision limits and incoming MFD capture.

Record build v15, `authored-basin-water-review@9` and
`captured-mfd-reviewed-d8-outlets@7`. Remove the v14 schema. Project v5,
`feature-guided-float32-water-checks@2` and numeric archive layouts stay current.
No dependency or language change is introduced.

## Consequences and validation

The public internal-water-barrier fixture remains canonically connected but
separates under finer sampling. Its captured area stays retained without changing
ground. A second position and a small graph fixture demonstrate that alternate
wet paths still work. Repeated/ordered/resolution tests, exact endpoints, budgets,
exported link summaries, UI checks and serial benchmarks validate the change.

These are bounded sampled connectivity checks at an imposed level, not storage,
discharge or equilibrium calculations. Dry-to-dry and dry-to-water links still
use canonical heights. Unresolved large networks need an explicit refinement or
budget strategy; the current cap bounds samples, not feature count or geometry
work. The [research rundown](../research/2026-09-11-internal-water-links.md)
records measured cost and the next implementation priorities.
