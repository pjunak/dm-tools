# ADR-0048: Keep zoom-driven detail generation in scope

- Status: Accepted scope and design direction; generation workflow not implemented
- Date: 2026-09-16
- Corrects: ADR-0047's exclusion of regional generation and parent/halo contracts
- Preserves: ADR-0047's input-only editing and immutable completed results

## Context

The author distinguishes changing a finished map by hand from generating more
local detail when zooming into it. Zoom-driven local enrichment is a core planned
capability. The previous cleanup incorrectly removed this capability along with
manual post-generation modification. Earlier research already describes the
regional generation model and its validation gates:

- [Multiresolution determinism](../research/2026-09-03-terrain-algorithm-options.md#multiresolution-determinism)
  separates exact pointwise samples from process convergence and boundary rules.
- [Prototype C](../research/2026-09-04-terrain-prototype-contracts.md)
  specifies a fixed parent, a regional window at 65/129/257 endpoint samples,
  a buffered boundary, inherited inflow, and overlap/downsample checks.
- The same prototype report's R34 finding shows why merely increasing the
  current detail-band count does not guarantee preservation of existing relief.

## Decision

Keep three operations distinct:

1. **Authoring:** specify terrain intent, including regional guidance, before a
   generation. A previous result may be its read-only placement background.
2. **Zoom-driven generation:** request finer terrain for a geographic window
   using the authored project and a reproducible parent context. Generate a
   separate local result; keep the parent and surrounding geography unchanged.
3. **Manual output modification:** directly sculpt or patch generated elevations.
   This remains outside the active product scope.

Navigation identifies the visible geographic extent and requested detail. The
planned regional operation must retain the parent's coordinate frame, scale,
input/build identity, seed policy and relevant constraints. Current coordinates
are local metric coordinates; do not pretend a planetary frame is implemented.
A future world placement must preserve that correspondence.

Generate only the required window and its measured context buffer, then crop
for display/export. Neighboring and overlapping requests must agree at their
boundaries; zooming away and returning must reproduce the same region regardless
of request order. Choose the actual parent restriction/downsample rule and numeric
tolerances explicitly. Exact shared samples of an unchanged pointwise field do
not prove coarse-cell averages or the consistency of newly added detail.

Refinement may consume immutable parent boundary values and drainage context.
A geometric buffer alone may not include the upstream catchment: inherit flow
information or report incomplete hydrology. This use of parent context is not
manual editing of the parent DEM. Input changes create a new generation identity
and invalidate dependent local results rather than silently patching an old one.

The immediate editor work provides coordinate-preserving pan/zoom and input
placement. A later generator slice supplies bounded regional requests, added
local detail and parent/boundary validation. A larger view of existing pixels
or denser samples of the same fixed field must not be presented as completed
local enrichment.

## Current boundary and open choices

Implemented foundations are coordinate-addressed deterministic fields, local
metric frames, endpoint grids and shared-coordinate tests under matching inputs.
The public generator still builds the whole coastline extent. Navigation zoom,
viewport-based generation requests, parent-conditioned local detail, refinement
caches and the full parent/child validation are not implemented.

The earlier files define the intended behavior and small experiments, not a
finished implementation specification. The detail algorithm and band budgets,
restriction operator/tolerances, local hydrology policy, automatic zoom thresholds
versus an explicit generation action, request cancellation and cache/storage
budgets still need decisions and measurement. These are active generation work,
not a deferred sculpting module. Keep completed inputs/results immutable and do
not add legacy-save support.
