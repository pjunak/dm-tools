# ADR-0037: Expose basin catchment outcomes and outlet-level evidence

- Status: Accepted
- Date: 2026-09-11
- Extends: ADR-0036; supersedes its build v9 export layout and review identities

## Context

A connected outlet can collect only part of a lake footprint. Aggregate area
alone cannot show which dry nodes remain trapped. The exact outlet height was
sampled, but submerged outlets had no explicit height-difference finding. A
sampled downstream path does not establish an equilibrium lake level.

## Decision

Retain the existing area-transfer and terrain algorithms. Export their canonical
footprint-node outcomes as UInt8 `catchment_class`: 0 outside, 1 retained,
2 collected water, 3 collected dry ground. Closed lakes, dry basins and blocked
outlets remain entirely retained. Never infer successful collection merely from
membership in the drawn polygon or from a clear candidate route alone.

Export Float64 `retained_km2` alongside the existing source, throughput and
terminal arrays. At every footprint terminal, retained plus source equals its
captured MFD area. Record wet/dry collected and retained sample counts separately
from contributing areas. These classes describe footprint nodes, not complete
upstream watersheds. No additional receiver graph or lake-storage model is added.

Expose the same classifications in a separate workbench toggle and the finished
terrain drainage-review panel. Use nearest-node endpoint scaling to preserve
categorical values. Ordinary terrain and water rendering remain independent.

Report `outlet_ground_minus_water_m`, signed ground elevation minus authored
water level, or null without an evaluated outlet. Reuse the 0.01 m tolerance for
above/below findings. Above-water outlets remain blocked; below-water outlets
receive an informational finding and retain the existing connection checks.
Never equate exact outlet ground with a surveyed controlling sill or silently
change authored water level to match it. The workbench states that lake level
is imposed and stability is unmodeled.

Build v10 replaces v9, adding the two basin-flow arrays and diagnostic fields.
Remove the old schema; keep project v5. Water review is
`authored-basin-water-review@4`; area transfer is
`captured-mfd-reviewed-d8-outlets@2`. Ground generation, automatic incision,
source capture and route-selection algorithms are unchanged.

## Consequences and validation

Reviewers can locate retained pockets and inspect their captured contributions.
Pits, unresolved flats and rejected polygon-crossing links still retain area;
this change does not choose repairs or classify each internal obstruction.

Regression coverage verifies class/area partition, sample counts, closure and
blocking, deep versus shallow bed routing against water head, signed outlet
height findings and tolerance, endpoint rendering, resolution/order independence,
repeated exports and unchanged ground. Runtime measurements and the current
implementation boundary are recorded in the linked research rundown.
