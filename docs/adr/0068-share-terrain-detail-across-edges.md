# ADR-0068: Share terrain detail across parent-cell edges

Date: 2026-09-23. Status: accepted for the explicit residual experiment only.
Supersedes the cell-interior formula and edge-pinning rule in
[ADR-0061](0061-verify-parents-and-isolate-local-detail.md), and extends the scalar
support records in [ADR-0062](0062-reuse-bounded-detail-cell-support.md).

## Context

The first verified-parent residual preserved reference terrain and exact cell
moments but forced the added height to zero on every parent-cell edge. Difference
images exposed isolated repeated stamps. Retaining those edge pins would prevent
connected detail across cells, although the product requires exact parent nodes
and protected context rather than an unchanged value at every intermediate edge point.

## Decision

Use `terrain-weighted-edge-residual-experiment@2`. Each globally addressed
horizontal or vertical edge has two deterministic, independently signed modes.
Both neighboring cells use the same coefficients and the smaller adjacent height
budget. Fixed 17-by-17 reference probes determine each cell's budget and its
horizontal/vertical terrain-gradient energy. Neighbor weights are averaged at
the shared edge. Protected cells have zero budgets and suppress shared edges.

Quintic normal blending joins the four edge signals inside a cell. Tangential
modes have zero integral, so each summand and the full added cell field have zero
analytic mean. The residual retains original nodes and agrees through second
derivatives at shared edges in real arithmetic. Record actual Float32 moments
and measure delivered secants separately. Preserve the original prepared parent
field, including its existing irregularities; never interpolate a replacement
from sparse parent nodes. The [report](../research/2026-09-23-shared-edge-detail.md)
contains the formulas, comparison and primary interpolation reference.

Prepare one additional parent cell on every side, clipped to the reference
frame. Count the complete rectangle against the existing 4096-cell limit before
allocating support. The output halo remains a separate fine-grid concept.
Cache only scalar protection, amplitude, directional weight and moments. A
halo-only record has no detailed moment until delivered. A temporary Float32
probe bank avoids duplicate cold terrain evaluations while adjacent budgets
become available; release it before delivery and charge it in memory admission.
`support_cells` now records this footprint; `parent_cells` still describes cells
intersecting the buffered output. `probe_samples` describes eligible fixed
support, including reuse, rather than work performed on a particular visit.

Remove the former formula and replace the current parent-region schema's
algorithm enumeration. The artifact schema remains v1 in this early development
phase; its detail evidence requires `support_cells`. Only current runtime/source
builds are accepted. No old-mode switch, migration or compatibility reader is added.
The global terrain generator and authored project schema remain unchanged.

## Consequences

Exact overlap, density and cache-order agreement continue, as do authored,
coastal, basin and inherited-channel protections. Original parent nodes remain
exact, but intermediate parent-cell edges can now carry detail. A whole-cell
crop therefore cannot be spliced directly into an unenriched parent any more
than an arbitrary partial-cell crop can. That display transition remains open.

The measured experiment connects additions and reduces quantized boundary slope
errors. It still shows horizontal/vertical direction, broad protected gaps and
some greater coarse spectral leakage. This is a bounded axis preference, not a
complete terrain-character or geological model. Neighbor preparation increases
cold work; the scalar cache preserves reuse without storing probe grids.

Keep the experimental opt-in and false hydrology/small-river readiness. Broader
physical scales, oblique support, cartographic/spectral tolerances, transition
policy, certified extrema and inherited fine flow remain required before automatic
zoom integration. Preserved means do not imply unchanged coarse spectral power.
