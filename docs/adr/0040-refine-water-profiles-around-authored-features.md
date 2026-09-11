# ADR-0040: Refine water profiles around authored features

- Status: Accepted
- Date: 2026-09-11
- Extends: ADR-0039; replaces build v12 and water/outflow review identities

## Context

A regular finer profile still misses sufficiently narrow terrain. Reducing the
public shoreline-gap point's influence radius from 2 km to 200 m makes its low
opening disappear from every quarter-grid probe. The outlet then connects even
though the authored point is near sea level under a 750 m lake. Increasing the
entire profile's density is expensive and remains sensitive to sample alignment.

## Decision

Preserve canonical routing, ground, source constraints and every existing
quarter-grid station. Pass typed prepared geometry and nominal/minimum core
radii from the finished-field evaluator to the water sampler. Use the actual
smoothed structure geometry and the evaluator's minimum taper/width factors;
attached absolute points use their narrower core. Attached relative points
have no independent local core.

A feature whose minimum core radius/4 is finer than the baseline requests
local intervals. Split line features into straight segments, intersect
conservative two-nominal-radius corridors with each profile segment, and
include closest approaches and projected endpoints. Square end caps contain
the circular endpoint influence area. Merge overlapping interval requirements
with the smallest active spacing; add stations at no more than minimum core
radius/4 inside those intervals. Normalize feature geometry and preserve
station order so constraint order, equivalent line direction and duplicate
guidance do not change evidence. Reuse mature Shapely geometry operations.

Count the complete merged plan before allocating refined positions or sampling
ground. Keep the 65,536-sample and 4,096-batch limits. Over-budget evidence is
empty and blocks transfer. If the baseline itself is excessive, its count is
a required lower bound and refinement planning is skipped. A sampled profile
reports exact total and added-feature counts plus its smallest local spacing
limit. Failed profiles have no added-feature count; their local spacing is
known only if refinement planning ran. No profile failure is silently coarsened.

Keep existing low-shoreline and above-water-contact gates and visible markers.
Details also shows the added sample count and smallest local spacing limit.
Build v13 records these fields in diagnostics; remove the superseded schema.
Project v5 and numeric archive layouts remain unchanged. Record
`feature-guided-float32-water-checks@2`, `authored-basin-water-review@7` and
`captured-mfd-reviewed-d8-outlets@5`. Add no dependency or solver.

## Consequences and validation

Narrow known cores and repeated crossings receive deliberate probes. These
corridors are sampling guidance, not hydraulic walls or a finite support bound
for the terrain field. Blended extrema, Gaussian context tails, procedural
features and regional transitions still need broader convergence evidence.
Internal wet links and external routes beyond the first attachment remain
canonical. Lake levels remain imposed; no controlling-sill or storage solver is
introduced. Small radii along a long parallel feature can exhaust the budget.

Tests cover shifted/off-line points, parallel/collinear/oblique segments,
multiple crossings, duplicate guidance, preserved baseline stations, exact
budget boundaries, empty failed evidence and inner/outer contact barriers.
The public 200 m opening fixture proves the decision change on the real field;
a controlled ablation retains identical DEM, canonical ground and captured area.
Resolution/order checks, conservation, exported profiles, UI details and
serial benchmarks complete validation. The
[research rundown](../research/2026-09-11-feature-guided-water-sampling.md)
records measured convergence and remaining limits.
