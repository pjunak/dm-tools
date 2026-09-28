# ADR-0084: Bind geographic context to bounded rough terrain

- Status: accepted
- Date: 2026-09-28
- Extends ADR-0075 and ADR-0079; implements the experimental M1 context consumer.

## Decision

Accept an optional verified `WorldContextRun` when creating a terrain project from
the retained world. Require exact world, projected coastline frame, projection and
optional geology-recipe identity. Transform the supported AEQD domain back to the
spherical context and freeze a fixed endpoint support grid with at most 129 samples
per axis. Save those immutable samples in project v9 and input snapshot v4; report
their binding in build v20.

Use bilinear weights for continuous land fraction, directional water exposure,
mixed-support fraction and conservative shore-distance intervals. Use nearest
source support for categorical water IDs and flags. Reject any domain whose full
bilinear stencil extends beyond the source latitude-cell centres. Do not extrapolate
across a pole, treat longitude/latitude as a flat process grid or imply a global
physical solve.

Keep projected source vectors authoritative for the land mask and exact coastline.
The only M1 numerical context consumer is coastal distance:

```text
effective distance = min(projected-vector distance,
                         continuous conservative spherical upper bound)
```

This can reduce AEQD distance overestimates that available context resolves. It
never enlarges the vector mask, invents a raster coast or uses the lower uncertainty
bound to force a zero-height coastal strip. Source masks and hard authored
constraints retain their existing authority.

Separate identity roles. `context_numeric_sha256` hashes geographic metadata and
actual numeric arrays independently of previews and container bytes.
`producer_runtime_sha256` records the context producer runtime. `binding_sha256`
hashes transferred metadata and every sampled field. Use the same bound context in
base/macros, automatic drainage and relative-valley preparation, point/regional
sampling and verified-parent replay.

Retain latitude, fractions, IDs, flags, exposure, support, water-body records and
optional geology identity for later declared consumers. Do not interpolate a water
graph. Mark climate, runoff, aging, bathymetry coupling and water transport
unsupported. The separate bathymetry product remains deferred to an M2 consumer.

## Consequences

The World workspace can pass its currently generated or opened context to
**World → Terrain**; the CLI exposes `world terrain --context`. Saved projects and
build snapshots are self-contained for regeneration and parent replay without the
original context bundle. Source or recipe mismatch fails before publication.

The first max/min-of-four cone interpolation preserved conservative bounds but was
discontinuous at support-cell edges. It is replaced by convex combinations of valid
per-node intervals, which preserve conservative validity and meet continuously.
[T18](../research/terrain-method-decisions.md#t18---take-extrema-from-the-nearest-four-context-distance-cones)
records the failed method and revisit gate.

This is an experimental M1 integration result, not terrain-quality acceptance, a
climate model, hydrological transport or an accepted world parent. Wider and polar
domains require an explicit shared-domain/global design in M5.

## Evidence

The [implementation report](../research/2026-09-28-context-bound-rough-terrain.md)
records the public paired control, continuity probe, identities, tests and current
validation boundary. No dependency was added.
