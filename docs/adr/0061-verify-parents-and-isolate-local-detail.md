# ADR-0061: Verify saved parents and isolate experimental local detail

- Status: Accepted parent/reference and artifact contracts; residual formula experimental
- Date: 2026-09-23
- Extends: [ADR-0048](0048-keep-zoom-driven-detail-generation.md),
  [ADR-0058](0058-sample-bounded-regional-windows.md) and
  [ADR-0060](0060-interpolate-overlapping-height-points.md)

## Context

Unchanged-field regional sampling did not consume a completed parent. The first
[parent-cell experiment](../research/2026-09-23-parent-cell-preservation.md)
replaced existing structure by a bilinear reference and changed authored heights,
shared samples across densities and inherited channels. Stable noise amplitudes
alone did not resolve those defects.

## Decision

Build v17 replaces the ambiguous dataclass dump with a versioned, typed portable
input snapshot and records its version. Remove the obsolete v16 schema; do not
load older builds. Parent consumers validate completion, all product hashes,
exact runtime/source identity, expected metric frame/settings and algorithm IDs.
Bound numeric headers/shapes before allocation. Reconstruct complete-source
context and replay every delivered ground/water/mask/ID value and the canonical
routing fields reused by the operation before treating it as a verified reference.
Keep the original source-file hashes as provenance without requiring their paths.

`sample-parent` samples this verified reference. `enrich-region --experimental`
adds a separately identified residual with explicit amplitude controls. Both
bind the parent build ID, globally anchored request, runtime and output hashes in
a new parent-region v1 artifact; no parent file or authored input is changed.
Completion is published last, after repeated parent/runtime checks. Reject output
paths inside the parent and existing destinations. No recursive child-parent
loading is introduced.

Use the current prepared field as the interior reference. The experimental
residual uses three smooth tensor modes with coefficients derived from the named
`terrain.local-detail` seed and cell coordinates. Each mode has an odd factor
about the cell midpoint, zero integral, and zero boundary value/first derivative.
Condition only this residual. Fixed 17 by 17 probes determine each cell's height
budget and reference moments, independently of request density or neighbors.
Keep an explicit distinction between analytic residual moments, measured
Float32 moments, and restriction of the original sparse DEM.

Protect entire cells intersecting authored cores, buffered basins/planned channels
or the coastal margin. Keep water samples unchanged. Bound buffered output to
two million nodes and preparation to 4,096 intersected parent cells. Reject any
observed between-probe height-bound violation instead of clipping. These are
bounded sampled checks, not a continuous certificate for the full terrain field.

Publish reference/detail/difference views and actual added-height arrays. Require
the experimental CLI flag and explicit unaccepted status. Hydrology remains
unreviewed at the new density and small-river readiness is false. GUI scheduling
and visibility must not infer readiness from a denser raster or successful manifest.

## Consequences and evidence

The accepted foundation supports standalone saved parents, exact replay and
reusable prepared context. The residual is a testable experiment, not the default
terrain recipe. Numerical tests cover 65/129/257 density, overlaps, request order,
parent nodes/edges, basis moments/slopes, water/point/channel protections and budget
failures. File tests cover invalid/tampered builds, bounded decoding, source-file
independence and incomplete publication.

The [public measurements](../research/2026-09-23-verified-parent-detail.md) expose
regular cell support and regions fully excluded by protections. Those findings
keep visual/terrain-character and coarse-power acceptance open. Finer drainage,
upstream inflow/outlet inheritance, full-field bounds and partial-cell transition
handling remain required before workbench/cartographic adoption. No manual
post-generation editing is added.
