# ADR-0033: Map basin extents and conditioned spill candidates

**Status:** Accepted
**Date:** 2026-09-10

## Decision

Replace the separate 129-node diagnostic evaluation with one typed
`DrainageAnalysis` on the existing 257-longest-side routing grid. Its summary,
filled surface, receivers, fill depths, extent labels and boundary context are
reused by channel conflict review, the workbench and numeric exports. Keep
flow primitives in `hydrology.py`, basin geometry in `basins.py`, and diagnostic
orchestration in `diagnostics.py`. No compatibility wrapper or old grid remains.

Use connected significant-fill extents and one deterministic escape from each
component's deepest node. Retain the first extent-exit edge, original-terrain
peak along the downstream route, terminal, boundary context and total exit-edge
count. Shared ascending-order downstream peak/terminal calculations avoid
walking every candidate to the boundary. Other exits remain recoverable from
the labels and conditioned receiver arrays.

Do not interpret components as a nested depression hierarchy or assign lake
levels. Exterior/enclosed non-land classification is raster diagnostic context;
it does not change the existing open-boundary routing rules or SVG geometry.
The [basin contract](../terrain-basins.md) specifies ties, units, arrays and limits.

## Consequences

Canonical drainage identity advances to `canonical-d8-priority-flood-diagnostics@4`:
its grid and Float32 sampling change, so old aggregate basin counts and fill
metrics are not comparable. Spill height now means a concrete original-terrain
node on a retained route. Generator, automatic-valley and channel-conflict
identities remain unchanged; the generated DEM and planned channels are unchanged.
Project v4 and manifest v6 structures remain current. Derived-array meaning is
bound by diagnostic identity and product hashes.

The four-panel review and optional workbench overlay expose geometry and route
candidates. Authored lakes/outlets, dry-basin policy and complete breach profiles
remain the next implementation, rather than unreviewed automatic terrain edits.
Removing duplicate sampling/flood/routing work offsets part of the higher-detail
basin analysis; representative measurements are recorded in the
[research note](../research/2026-09-10-basin-outlet-topology.md).

## Validation

Analytical tests cover a known bowl and saddle, exact-tie exits, multiple exits,
route descent and peak/terminal identity, extent accounting, enclosed water,
eight-neighbour connectivity, overlapping boundary flags, zero-height land,
sub-tolerance depressions, nodata and invalid metric inputs. Reproducibility tests
cover shared nodes across output sizes and byte-identical exported builds.
UI smoke, final gates and benchmark results are recorded with the research note.
