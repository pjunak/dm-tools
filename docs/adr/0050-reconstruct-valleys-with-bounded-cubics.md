# ADR-0050: Reconstruct automatic valleys with bounded cubics

- Status: Accepted and implemented
- Date: 2026-09-16
- Extends: ADR-0031 and ADR-0035; no project or build-schema change

## Context

Automatic incision and residual-detail suppression live on a fixed canonical
routing grid. Bilinear reconstruction preserves those samples but gives each
cell a separate slope, exposing grid creases in finer output. Workbench zoom
makes these artifacts easier to inspect. Changing routing resolution, relaxing
cut limits or smoothing a completed DEM would change other terrain contracts.

## Decision

Prepare an immutable bounded bicubic Hermite surface for each canonical shaping
field. Start with shape-preserving one-dimensional nodal slopes along both axes
and symmetric mixed derivatives. Convert each corner's derivative contributions
to its three associated Bezier control offsets. Limit all three derivatives at
a node by one factor satisfying the corner range of every adjacent cell.
Shared derivatives preserve first-derivative continuity across interior cell
edges in exact arithmetic, while the Bezier convex hull bounds each patch by
its four original corner values. Keep a final range clamp for roundoff.

For incision, additionally cap each query by the existing bilinear interpolation
of canonical incision limits. This ceiling remains authoritative even when it
introduces a slope break. Exact vector basin membership still zeroes both
incision and suppression inside retention footprints. Authored constraints,
coastline zero, generation ceiling and final Float32 conversion retain their
existing authority. Prepared surfaces own read-only copies of their inputs.

Retain the canonical samples and routing topology exactly. Change only the
between-node reconstruction; do not resample or blur a finished raster. The
same coordinate-based evaluator serves generation and water review. There is
no runtime switch for the superseded interpolation and no new dependency.
The two-dimensional joint limiter is project-owned; a one-dimensional PCHIP
call alone does not supply its shared-edge and cell-range contract.

Record generator `coastline-constraint-terrain@9` and automatic valleys
`regional-budget-mfd-d8-valleys@7`. Other algorithms and public schemas retain
their identities. Rebuild results to adopt the new field.

## Validation and limits

Test analytic constant/affine/bilinear fields, exact knots, nonuniform axes,
dense cell ranges, active ceilings, shared-edge slope convergence, axis
symmetry, input ownership and chunk/order independence. Test integration with
regional budgets and basin retention, then run the complete repository checks.
The [measured comparison](../research/2026-09-16-bounded-valley-reconstruction.md)
records eight cases/seeds, preserved canonical products, fine channel profiles,
visual inspection, timing and memory.

The bound is local to these two shaping fields. It is not an outward-rounded
bound for the complete terrain, a guarantee against interior extrema, or a
certificate of downstream flow. D8 turns, cap-induced creases, authored and
retention boundaries, and unresolved channel climbs remain. Sampled channel
profiles are finite observations. Finer reconstruction does not implement
zoom-driven local enrichment, erosion, new tributaries or additional detail.
