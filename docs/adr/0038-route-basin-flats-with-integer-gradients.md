# ADR-0038: Route basin flats with integer gradients

- Status: Accepted
- Date: 2026-09-11
- Extends: ADR-0036 and ADR-0037; replaces strict-only internal routing and build v10

## Context

A dry plateau inside an eligible lake footprint could retain captured area
because its interior had no strictly lower neighbour, despite a valid exit at
the flat's edge. Automatically filling the DEM would change authored ground;
choosing only exits that eventually reach lake water would incorrectly redirect
contributions away from lower closed pits.

## Decision

Use a compact, symmetric D8 graph of footprint nodes. A vectorized polygon
coverage check admits each complete segment once and records both directions.
Real downhill routing selects the steepest permitted link using metric spacing.
This also permits a valid alternative when the steepest raster neighbour would
cross outside the polygon; previous routing stopped at that rejected choice.

Resolve exact equal-head components using separate integer gradients adapted
from [Barnes, Lehman and Mulla (2014)](https://arxiv.org/abs/1511.04433).
Route toward every downhill exit or equal-head water terminal, with a secondary
gradient away from higher ground. Each flat edge decreases rank, each real drop
decreases head, and fixed D8 order resolves equal slopes. The DEM is unmodified;
near-equal heights remain distinct. Unlike an open DEM boundary, a missing
basin link never supplies an exit. Components without exits remain terminal.

Wet nodes use authored water level as their head and remain internal terminals.
Following the resulting graph determines collection. A flat path ending in a
lower closed pit still retains its area. Internal routing is derived only after
the existing outlet and connected-water checks pass. Do not loosen shoreline,
regional-cut, anchor or downstream checks.

Build v11 replaces v10, retaining project v5 and removing the obsolete build
schema. Export Int64 `internal_receivers` as canonical row-major flat indices
(-1 when terminal or not derived) and UInt32 `flat_rank` (positive only at
resolved flat donors). Export both flat-donor counts and the subset reaching
water. All arrays use the canonical grid, independently of delivered resolution.

Record `masked-barnes-d8-flat-routing@1`,
`captured-mfd-reviewed-d8-outlets@3` and `authored-basin-water-review@5`.
Ground generation and the original MFD capture graph are unchanged. No legacy
loader, new dependency or external implementation is introduced.

## Consequences and validation

Flat-routing correctness can be reviewed through exported links and ranks.
The portable numerical module accepts arrays and metric spacing; polygon
preparation and area transfer remain separate. BFS flat resolution is linear
in the bounded graph size; end-to-end collection also performs geometry checks
and an O(N log N) ordering step. Do not apply the paper's runtime claims to the
whole Python pipeline.

Tests independently trace every path for cycles, climbing, rank stalls and
correct wet/pit terminals. Fixtures cover real barriers smaller than 0.01 m,
multiple exits, exact water-head contact, polygon gaps, order and resolution
independence, closure, route revalidation, unchanged ground and area conservation.
The [implementation rundown](../research/2026-09-11-basin-flat-routing.md) records
measured results and limits. Shoreline/sill refinement and explicit lake chains
remain separate work; this routing change does not establish stable water levels.
