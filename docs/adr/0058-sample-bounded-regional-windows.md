# ADR-0058: Sample bounded regional windows

- Status: Accepted; unchanged-field regional sampling implemented
- Date: 2026-09-22
- Extends: [ADR-0048](0048-keep-zoom-driven-detail-generation.md) and
  [ADR-0057](0057-display-water-at-the-appropriate-scale.md)

## Context

Coordinate-addressed generation already supports arbitrary point queries and
shared-node equality, but a caller cannot request a bounded finer rectangle as
an explicit operation. Local detail and small rivers need a reproducible request
foundation before parent-conditioned enrichment and finer hydrology can be built.
The normalized detail-band amplitude issue R34 still prevents blindly raising
the detail setting while promising to preserve the parent surface.

## Decision

Introduce `RegionalSamplingRequest` in the dependency-light domain. Bind a full
source-field identity and reference endpoint grid to power-of-two refinement,
inclusive global grid addresses and a clipped halo. Anchor all new coordinates
to original intervals; reuse original nodes exactly. Metric requests round
outwards. Validate precision and the two-million-node halo-inclusive limit before
preparing the full field or creating output.

Expose the existing preparation as `PreparedTerrainField` and
`prepare_terrain_field`. `TerrainRegionSampler` reuses its complete-source
constraints, regions, basins, profiles and canonical drainage. It evaluates
regional points in batches of at most 65,536 and returns read-only arrays.
Do not crop away upstream or authored context before preparation or run
independent routing inside the request rectangle.

Publish regional samples through a saved-project application operation and
`terrain sample-region`. Use a dedicated v1 artifact schema, input and runtime
verification, exclusive new directories, numeric archive hashes and a
completion-last manifest. Include full reference/canonical grids alongside the
window and buffered grids. The ground preview shades with the halo, then crops.
Sampled authored lake levels and basin IDs remain separate numeric products;
local water flow and cartographic river acceptance are not provided.

The source is an input-defined field, not an immutable finished parent build.
Record that distinction and explicit false capability flags for parent-DEM
conditioning, new detail bands and refined hydrology. Keep current generator,
valley and noise identities unchanged because this operation reuses their
existing numeric semantics. Give sampling its own algorithm identity.

## Consequences and validation

Overlapping requests and nested levels share coordinates and values. The tests
compare regional samples to complete generated fixtures, water/mask values,
repeat visits, different evaluation batch sizes, translated grids and source
identity mismatches. Publication tests cover input changes, output failures,
repeatability, the public schema and cropped preview provenance.

Work at the finer resolution is bounded to the window, but initial preparation
still covers the complete source. The first command has no cache, GUI job,
cancellation or new local drainage solver. The sample limit does not bound all
possible geometry/constraint costs. Physical width/discharge evidence, parent
restriction, boundary slopes under added detail and inherited flow remain
separate implementation gates. No post-generation editing is introduced.

See the [usage contract](../terrain-regional-sampling.md) and
[public-fixture evidence](../research/2026-09-22-regional-field-sampling.md).
