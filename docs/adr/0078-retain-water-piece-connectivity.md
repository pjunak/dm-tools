# ADR-0078: Retain water-piece connectivity through coastal cells

- Status: Accepted
- Date: 2026-09-25
- Extends [ADR-0074](0074-verify-context-and-measure-water-openings.md) and
  [ADR-0075](0075-measure-spherical-geographic-exposure.md).

## Decision

Context v4, algorithm `spherical-geography-v4`, includes a source-derived graph
of individual water pieces per cell. A dominant water ID and one longest opening
per face cannot establish which openings connect inside a split cell. Keep
positive-area pieces, their vector water identities and spherical areas. Link
pieces only across a common positive-length water interval; retain distinct
intervals even when they connect the same pair. Store each undirected link once,
including periodic east links, and never connect through corners or poles.

Use existing Shapely clipping/indexing and SciPy sparse connected components.
Only two rows of face traces are live; full-water cells use analytic areas and
full intervals. The [guide](../world-context.md) owns array registration, physical
units, area tolerances and explicit piece/link/vertex/face admission limits.
Interior inspection sites are not flow paths; face length is not a sill,
conductance, discharge, volume or heat-storage coefficient.

Retain and expose finite-precision limitations. If a positive-area source sliver
loses a representable open face when clipped, its source ID appears in
`fragmented_bodies`; keep the isolated pieces and reject transport use for that
region. Never repair it by an inferred link, snap the authored coast or silently
drop its area. Invalid body crossings, unsupported nonpositive area and exceeded
area/complexity budgets still reject generation. This support is inspectable in
the manifest, CLI and pink preview cells.

Export `connectivity.npz` with bounded current-only numeric members and a derived
preview. Before accepting a saved graph, reconstruct source incidence and compare
all ordered arrays, in addition to hashes and metadata. This increases reopening
cost; exact reconstruction may require regeneration under a changed geometry
runtime. Producer identity remains the saved producer and exporting still requires
the producing runtime. Context v3 is removed, and bathymetry's geography identity
moves to v4; no compatibility loader or conversion is provided.

## Alternatives and consequences

One raster node per cell introduces false crossings through land. Combining all
open gaps into one width loses individual incidence. An unstructured global mesh
would require a new discretization and transfer contract before a concrete solver
needs it. This bounded graph preserves the current grid while making coastal
connectivity and unresolved support explicit. It is not yet a validated transport
or circulation model.

## Validation

Analytic and synthetic controls cover barriers within one ocean, lake/ocean
separation, multiple intervals, subcell straits, corner contacts, seam overlap,
closed poles, radius/page-scale changes, areas, immutable deterministic arrays,
precision-limited slivers and cancellation/complexity admission. Rehashed invalid
links and malformed numeric counts/headers reject. Real Tk checks cover inspection
and scrollable details. The [implementation report](../research/2026-09-25-water-piece-connectivity.md)
records private-world support, performance and final gates.
