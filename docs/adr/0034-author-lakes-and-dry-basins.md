# ADR-0034: Author lakes and dry-basin retention

**Status:** Accepted
**Date:** 2026-09-10

## Decision

Add a typed `TerrainBasin` constraint: a closed normalized footprint, lake or
dry-basin kind, nullable water level and nullable explicit boundary outlet.
No generated depression ID is saved as authored identity. The new `water.py`
pipeline module owns metric validation, retention membership, water products
and conflict review. Existing shaping constraints remain independently authoritative.

Exclude automatic incision within every footprint by both a zero canonical
budget and exact vector membership during continuous sampling. Also exclude
automatic detail suppression there. This prevents interpolation from spending a
neighbor's cut allowance inside retained terrain. All generated flow candidates
remain inspectable; a planned exit from a closed basin is a conflict, not a
silently permitted hydrological exception.

Store ground and water surfaces separately. The drawn footprint bounds the
potential lake; only ground more than 0.01 m below its authored level is wet.
Do not excavate ground, flatten a lake bed or overwrite exact elevation anchors
merely to satisfy an inconsistent polygon or level. Surface containment, outlet
height and planned-flow findings are visible in Basin details and numeric exports.
Full downstream outlet validation and river repair are the next slice.

## Current contracts

Project v5 persists the constraint and lake-tool defaults; build v7 requires
`water.npz` and references project v5. Remove the old schemas and update public
examples and consumers; no old-format loader or migration is provided.
Generator identity becomes `coastline-constraint-terrain@6`; automatic valleys
become `regional-budget-mfd-d8-valleys@5`. Water review is
`authored-basin-water-review@1`. The no-basin path retains existing numerical
behavior; the new identities describe optional retention authority.

The [water guide](../terrain-water.md) specifies units, nodata, flags, IDs,
geometry rules and validation boundaries. Standard scientific elevation remains
a view of bathymetry, while cartographic relief shows authored water in blue.

## Alternatives and limits

Automatic filling of all depression candidates would decide water intent and
change terrain without author input. Saving candidate rank as identity would
attach authored choices to different depressions after regeneration. Treating
water level as ground elevation would destroy bathymetry and conflict with height
anchors. These approaches are rejected.

This is footprint retention and explicit water authoring, not a full hydrological
solver. Planned D8/MFD outflow is still reviewed rather than reconciled. Raster
shoreline checks cannot certify sub-grid banks. Authored regions do not yet
classify enclosed SVG holes or define ocean levels.

## Validation

Analytical tests cover separate water/ground values, retained cuts, exact height
anchors, nested sampling, changing water level without changing ground, dry-basin
outflow, low boundaries, exposed anchors, disconnected pools and high outlets.
Project round trips and numeric build tests verify current schemas and repeatable
water products. Final gates, public example inspection, hidden Tk smoke and
isolated representative benchmarks are recorded in the
[implementation rundown](../research/2026-09-10-authored-water.md).
