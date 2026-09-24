# Terrain coordinate and grid contract

The current generator uses a local metric plane. Parsed SVG bounds define its
origin and aspect ratio; `object_scale_km` sets the **longest dimension**, not
necessarily the width. Axes increase source-right and source-down.

`LocalMetricFrame` in
[the domain](../src/dmtools/terrain/domain/coordinates.py) owns this conversion:

```text
scale = longest_side_km / max(source_width, source_height)
local_x = (source_x - source_min_x) * scale
local_y = (source_y - source_min_y) * scale
```

The inverse retains the original source origin. Neither direction clips points
to the coastline or bounds. This makes coordinate conversion usable for future
buffered regions without changing authored geography. It does not establish
longitude/latitude or a planetary scale.

## Endpoint samples

`EndpointGrid` describes sample positions including the minimum and maximum
coordinates on both axes. For example, five nodes from -10 to 10 km are
-10, -5, 0, 5 and 10 km. Their spacing is 5 km, and their extent is 20 km.

A span with N nodes has N-1 intervals. Subdividing each interval twice produces
2N-1 nodes: 65 becomes 129, not 130. The domain's `refined` helper computes
this geometry; it does not generate child terrain or guarantee parent/child
DEM consistency. [ADR-0048](adr/0048-keep-zoom-driven-detail-generation.md) keeps
zoom-driven regional generation in scope and identifies the missing parent and
window contracts. Non-dyadic floating-point refinement may need numerical
tolerances even when the abstract positions coincide.

The shape factory retains the existing aspect-ratio calculation and ties-to-
even rounding. Both x and y spacing must be read from the resulting grid;
short-side rounding and minimum counts can make them different.

| Grid | Longest-axis samples | Minimum per axis |
|---|---:|---:|
| Delivered terrain | Requested resolution | 2 |
| Routing and canonical diagnostics | 257 | 3 |

Both use the same local extent. Increasing delivered resolution does not
increase the shared process/review grid's resolution. Generator arrays, hillshade,
quality measurements and exported metadata share the same grid description.

## Regional subdivisions

[Regional sampling](terrain-regional-sampling.md) now subdivides each reference
interval by a power of two. Integer window addresses belong to that complete
fine grid even though only local arrays are allocated. Original nodes are reused
exactly; exported axes own the precise rounded positions. Bounds round outwards
and the halo clips only at the full source boundary. The manifest distinguishes
reference, core, buffered and complete-source canonical routing grids.

## Retained world coordinates and local terrain remain separate

[World projects](terrain-worlds.md) now declare a full-world spherical Plate Carrée
frame, radius in kilometres and central meridian. `WorldFrame` in
[the world domain](../src/dmtools/terrain/domain/world.py) owns reversible
source-to-sphere conversion and great-circle distances:

```text
longitude = central_meridian + 360 * (source_x - frame_left) / frame_width - 180
latitude  = 90 - 180 * (source_y - frame_top) / frame_height
```

Longitude normally wraps into [-180°, 180°); conversion with wrapping disabled
retains the explicit side of the seam for round-trip controls. Latitude outside
[-90°, 90°] fails. The full declared frame covers the entire sphere, independently
of export pixels, source margins or a continent's bounds. The radius must be
explicit; this custom sphere is not Earth EPSG:4326. Other projections and partial
worlds are not accepted by the initial format.

Original SVG remains unchanged. Derived inspection geometry splits continuous
seam-crossing shapes into periodic clipped views without losing ownership or
counting area twice. Spherical area integrates sampled source-linear boundaries,
including holes; it does not use flat pixel areas or geodesic-chord polygons.
Tests cover offset frames, changed meridians, great-circle distances, seam
ownership, polar caps and whole-sphere area. Curve flattening has the explicit
source-space tolerance documented in the world guide.

**Generated terrain projects and builds still have no source-to-world binding or
regional working CRS.** Their scale and endpoint-node model above remain local.
A saved world does not silently rescale a terrain project or georeference its
GeoTIFF. World-to-region metric projections, distortion gates and transfers to
proposed cell-centred climate grids remain future work. Node samples are not
cell means. [WC1-WC5](strategy/world-context.md) owns those staged contracts.

The [ADR](adr/0025-centralize-local-frames-and-endpoint-grids.md) records the
implementation boundary and alternatives. See the [build guide](terrain-builds.md)
for the current local numeric products and [TODO](../TODO.md) for remaining
world-coordinate and sampling work.
