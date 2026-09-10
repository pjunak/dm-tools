# Authored lakes and dry basins

Draw a **Lake** or **Dry basin** area with three or more corners, then choose
**Finish area**. Lake controls specify water level in metres. Enable **Outlet at
first vertex** before finishing a draining lake; otherwise it has closed-basin
intent. Its first corner becomes the explicit outlet marker. Undo removes the
last area using the existing authoring workflow.

Generate terrain to apply retention and inspect **Basin details**. This reports
low boundary sections, disconnected pools, exposed height anchors, outlet
height conflicts, retained contributing area and candidate downstream routes. The public
[water example](../examples/terrain/basin-water.dmterrain.json) contains one lake
and one dry basin on the synthetic public coastline.

## What changes terrain

Every authored basin footprint excludes automatic incision and automatic detail
suppression. The canonical incision budget is zero inside it, and exact vector
membership also gates continuous sampling so bilinear interpolation cannot leak
a cut into the protected area between routing nodes. Authored height points,
brushes, ridges and valleys still apply; protection is against generated cutting.
It does not erase an authored valley crossing a dry basin.

A lake stores water separately from ground elevation. Its drawn polygon is the
maximum permitted water extent, not an instruction to flatten or excavate the
entire polygon. Land below the water level minus 0.01 m is wet; higher ground
remains exposed. A lake can therefore contain islands or multiple pools.
Changing only water level or outlet leaves its ground DEM unchanged. Changing
a footprint changes its automatic-cut protection and may change nearby terrain.

Cartographic relief displays wet samples in blue. Scientific elevation continues
to show ground height, including the lake bed. The generated Float32 DEM and
GeoTIFF remain ground elevations; a water surface never replaces an exact height
anchor or bathymetry sample.

## Authored and derived data

Current project v5 adds `lake` and `dry_basin` records to `constraints`. Both store
closed normalized `points`, `water_level_m` and `outlet`. A lake requires a finite
non-negative level no higher than the generation ceiling; its outlet is a
normalized boundary point or null. A dry basin requires null for both fields.
`authoring.tools.lake` remembers level and the first-vertex outlet checkbox.

Footprints must be valid, simple polygons entirely on land, excluding SVG holes.
They cannot overlap or touch, avoiding ambiguous ownership of protected samples.
Outlets must lie on the footprint boundary within 1e-9 times the longest metric
extent. Geometry checks run before generation; malformed footprints are not
silently repaired. Only the current project/build formats are supported.

The generation result retains water products and a review on the shared
257-longest-side canonical grid. Intent IDs are one-based, deterministically
sorted by kind, level, outlet and points. They identify this result and can change
when inputs change; they are distinct from derived depression candidate IDs.

Build v8 includes `water.npz`, sharing the delivered DEM's grid and axes:

| Field | Meaning |
|---|---|
| `surface_m` | Float32 lake level at wet samples; NaN everywhere else |
| `depth_m` | Float32 water surface minus ground at wet samples; zero elsewhere |
| `intent_ids` | UInt32 authored footprint ID, including dry portions; zero outside footprints |

`routing.npz` includes `basin_intent_ids` and `retention_terminal_mask` on its
canonical grid. All marked terminals have receiver -1.
`diagnostics.json` adds `authored_water` and `water_sha256`; existing DEM/routing
hashes and the completion manifest bind all products together. The water review
contains each ID's authored record, counts/flags, retained contributing area and
optional outlet-route evidence. No pickle loading is needed.

## Planned retention and contributing area

Every canonical node in an authored footprint is an absorbing terminal in the
planning graph. Priority-Flood uses these nodes as additional seeds without
raising them. D8 assigns no outgoing edge, and MFD distributes none of their
area onward. Incoming planned channels end at their first footprint node.
Each interior node retains its own local contribution; this does not invent
an internal lake channel, a shared basin floor or overflow between pools.

`retained_contributing_area_km2` sums the MFD area at that intent's terminals.
Across all terminal land nodes, the sum equals land-node count times canonical
x/y spacing, within floating-point tolerance. This is the existing equal-node
contributing-area convention, not exact vector polygon area or water volume.
The review reports `unexpected_planned_basin_exit` if a channel violates the
terminal contract. No footprint node may receive automatic cutting or detail
suppression. Geometry smaller than the grid can resolve still needs refinement.

A lake with a declared outlet also remains absorbing pending connection.
Changing its level or outlet therefore leaves ground and planning unchanged.
The separate `canonical_drainage` analysis still fills a diagnostic copy toward
land boundaries to inventory natural depressions. Its conditioned receivers
are candidate topology; they do not override authored retention.

## Candidate outlet review

The exact authored outlet is evaluated on the finished field, rounded to
Float32. Within one grid diagonal, the nearest outward land node supplies a
candidate attachment; row-major order breaks distance ties. The attachment
must stay on vector land, leave its own footprint, and avoid other footprints.
Selection happens before downstream success is known, so an obstruction is not
hidden by choosing a farther node. A wet sample within the same distance and
connected by a segment inside the footprint is required for sampled water contact.

The review follows the finished field's conditioned D8 receivers to a terminal
or the first invalid step. It inspects **unfilled** ground heights along the
entire visited route, including the attachment from the lake's water level.
It records canonical flat indices, reviewed length in kilometres, uphill step
count, maximum rise, maximum height above lake level, terminal index and boundary
flags. Length and height statistics cover the inspected prefix if geometry or
a graph error blocks further tracing; they are not a complete breach estimate.

Every segment is checked against vector land and every authored footprint, so
a gap or protected area between raster nodes cannot be silently jumped. Re-entry,
cycles, invalid receivers, inland terminals, uphill steps above 0.01 m and an
outlet above water are reported. Enclosed SVG-hole terminals and raster-edge
terminals without exterior-water adjacency need an explicit boundary level.

`outlet_route.status` is `sampled_clear`, `blocked` or `unresolved` (no eligible
attachment). `sampled_clear` means this candidate has no detected obstruction
at the sampled spacing. It does not check terrain between nodes, certify the
shoreline, choose an ocean level, validate river gradients at finer scales or
activate flow. Every declared outlet keeps `outlet_connection_pending` until
basin-to-outlet routing and area transfer are implemented together.

## Shoreline findings and remaining work

- `low_boundary`: wet land borders below-level ground beyond its drawn polygon
  by D8, or reaches the raster edge. An intended outlet can explain part of
  this evidence; other shoreline sections still need review.
- `exposed_height_anchor`: an absolute height point is at or above lake level
  within the polygon. It may be an intentional island; its height stays.
- `outlet_above_water`: the exact outlet ground is above the authored level.
- `unresolved_footprint`, `no_water_at_level` and `disconnected_water`: the
  canonical grid resolves no area, no wet ground or multiple separate pools.

The water surface remains an authored, clipped level preview. No runoff,
water budget, automatic spill, breach, sediment or nested depression hierarchy
is simulated. Next, connect eligible outlets with explicit basin-area transfer,
revalidate after terrain changes, and compare full constrained breach/reroute
proposals while preserving regional budgets and authored anchors. See
[ADR-0035](adr/0035-retain-basin-flow-and-assess-outlets.md).

For measured results and the prioritized next steps, read the
[implementation rundown](research/2026-09-11-basin-retention-and-outlets.md).
