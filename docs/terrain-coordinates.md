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
DEM consistency. Non-dyadic floating-point refinement may need numerical
tolerances even when the abstract positions coincide.

The shape factory retains the existing aspect-ratio calculation and ties-to-
even rounding. Both x and y spacing must be read from the resulting grid;
short-side rounding and minimum counts can make them different.

| Grid | Longest-axis samples | Minimum per axis |
|---|---:|---:|
| Delivered terrain | Requested resolution | 2 |
| Automatic routing | 257 | 3 |
| Canonical diagnostics | 129 | 3 |

All three use the same local extent. Increasing delivered resolution does not
increase either process grid's resolution. Generator arrays, hillshade,
quality measurements and exported metadata share the same grid description.

## World positioning remains explicit future work

Current projects have no declared source-to-world correspondence, working CRS
or planetary radius. They remain local after this refactor. A source origin
recorded in parsed SVG units is not enough to infer its relationship to an
original document or global projection.

World support must preserve a campaign's established frame, declare source
placement explicitly, choose appropriate metric working coordinates, and
validate distortion and round trips. It must also distinguish node sample
extents from raster pixel outer corners. Existing projects must not silently
acquire a different physical scale.

The [ADR](adr/0025-centralize-local-frames-and-endpoint-grids.md) records the
implementation boundary and alternatives. See the [build guide](terrain-builds.md)
for the current local numeric products and [TODO](../TODO.md) for remaining
world-coordinate and refinement work.
