# Authored lakes and dry basins

Draw a **Lake** or **Dry basin** area with three or more corners, then choose
**Finish area**. Lake controls specify water level in metres. Enable **Outlet at
first vertex** before finishing a draining lake; otherwise it has closed-basin
intent. Its first corner becomes the explicit outlet marker. Undo removes the
last area using the existing authoring workflow.

Generate terrain to apply retention and inspect **Basin details**. This reports
low boundary sections, disconnected pools, exposed height anchors, outlet
height conflicts and planned channels leaving closed basins. The public
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
silently repaired. Current formats only: project v4 and build v6 are removed.

The generation result retains water products and a review on the shared
257-longest-side canonical grid. Intent IDs are one-based, deterministically
sorted by kind, level, outlet and points. They identify this result and can change
when inputs change; they are distinct from derived depression candidate IDs.

Build v7 adds `water.npz`, sharing the delivered DEM's grid and axes:

| Field | Meaning |
|---|---|
| `surface_m` | Float32 lake level at wet samples; NaN everywhere else |
| `depth_m` | Float32 water surface minus ground at wet samples; zero elsewhere |
| `intent_ids` | UInt32 authored footprint ID, including dry portions; zero outside footprints |

`routing.npz` adds `basin_intent_ids` on its canonical grid.
`diagnostics.json` adds `authored_water` and `water_sha256`; existing DEM/routing
hashes and the completion manifest bind all products together. The water review
contains each ID's authored record and counts/flags. No pickle loading is needed.

## Review limits and next step

Review flags are findings, not automatic edits:

- `low_boundary` means wet land is adjacent, by D8, to below-level ground beyond
  the drawn polygon, or reaches the raster edge. An intended outlet can account
  for some of this evidence; it does not validate other shoreline sections.
- `exposed_height_anchor` identifies an absolute height point at or above lake
  level within the polygon. It may be an intentional island; the anchor stays.
- `outlet_above_water` uses the finished field evaluated at the exact authored
  outlet, rounded to Float32. Every declared outlet also remains marked
  `outlet_route_unvalidated` until downstream connectivity is checked.
- `planned_outflow_from_closed_basin` identifies planned channel edges that leave
  a lake with no outlet or a dry basin. Retention prevents automatic cutting
  inside the footprint, but the diagnostic planning graph still proposes exits.
- Tiny areas can be `unresolved_footprint`; a dry lake or multiple separate pools
  is reported as `no_water_at_level` or `disconnected_water`.

The water surface is an authored, clipped level preview. This slice does not
supply runoff, a water budget, automatic spill routing, a breach, sediment or a
nested depression hierarchy. A clean sampled review is not river certification.
Next, use these explicit intents to stop/redirect planned outflow and compare
complete downstream routes under existing cut budgets and authored constraints.
