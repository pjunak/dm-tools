# ADR-0025: Centralize local frames and endpoint grids

**Status:** Accepted
**Date:** 2026-09-05
**Deciders:** Codex implementation within the authorized Python foundation work.

## Context

Generation, canonical routing, diagnostic sampling, hillshade and manifests
independently calculated source scale, grid dimensions and sample spacing.
That duplication makes a later world-coordinate feature or language migration
more expensive and risks subtle differences between physical calculations and
the coordinates written to disk.

Version-1 projects specify a longest-side length for a local source plane.
They do not declare how parsed SVG coordinates correspond to a world map.
A campaign's fixed projection must not be inferred from a clipped coastline's
bounding box. Existing terrain and public formats must remain compatible.

## Decision

Introduce two dependency-light domain values and one NumPy sampling helper:

- `LocalMetricFrame` preserves source bounds, longest-side scale, local extent,
  and forward/inverse coordinate conversion. The local origin is the source
  minimum x/y; axes increase source-right and source-down. Conversion permits
  finite coordinates outside the extent, allowing a future halo without clipping.
- `EndpointGrid` owns ordered sample extents, width/height, registration and
  independent x/y spacing. Counts refer to nodes, including both endpoints.
  Spacing is axis span divided by count minus one. Extents may have nonzero or
  negative origins; they are not pixel outer corners.
- `grid_coordinates` constructs Float64 NumPy axes from that contract. Domain
  code remains independent of NumPy, Shapely, files and application interfaces.

Output, 257-sample canonical routing and 129-sample diagnostic grids share the
same shape factory. Preserve the old multiplication/division order and Python's
ties-to-even rounding. Output grids keep a two-sample axis minimum; canonical
routing and diagnostics keep a three-sample minimum. Aspect-ratio rounding means
x/y spacing may differ.

`GeneratedTerrain.grid` and `routing_grid` expose grid descriptions derived
from the existing arrays/shape. Rendering, quality measurements, benchmarks
and manifest publication use them. Generated axes remain uniform; the properties
do not validate arbitrary externally substituted arrays.

A refinement factor subdivides intervals: a count of N becomes
`(N - 1) * factor + 1`. This defines grid geometry only, not regional terrain
generation, parent restriction, halos or seam correction. Arbitrary-factor
floating-point samples need tolerance-aware comparison; existing dyadic
nested-sample checks remain exact.

## Options considered

| Option | Complexity/cost | Maintenance and migration consequence |
|---|---|---|
| Keep independent formulas | Low now | Multiple places can diverge and require separate migration |
| Shared local frame/grid values | Small, selected | One explicit contract reused by computation and export |
| Introduce full world positioning now | High | Requires project migration, source correspondence, projection and distortion policy |

## Trade-offs and consequences

The selected change improves the implementation boundary without reinterpreting
saved projects. It does not assign a world CRS, infer a planetary radius, change
seeds, introduce geographic resampling or add GIS dependencies. The public
project/build schemas and algorithm IDs remain unchanged. Source fingerprints
still identify the changed implementation.

Validation now rejects nonfinite, reversed, zero-area or numerically collapsed
extents and noninteger/insufficient sample counts at the domain boundary.
Scientific operations still require a suitable future metric working projection;
a local kilometre label alone does not establish world-ground distance.

The future GeoTIFF adapter must explicitly handle node registration and GDAL
pixel-corner versus sample-center semantics. It must not reuse node extents as
pixel outer bounds and silently introduce a half-cell shift. See the
[GDAL geotransform tutorial](https://gdal.org/en/stable/tutorials/geotransforms_tut.html).
The [PROJ Equidistant Cylindrical reference](https://proj.org/en/stable/operations/projections/eqc.html)
also documents latitude-dependent distortion, so global source-plane distances
must not be treated as uniform ground distances away from a true-scale parallel.

## Validation

Numerical tests cover source/local round trips, translated source geometry,
thin extents, explicit stage minimums, ties-to-even shape rounding, invalid
values, nonzero origins, interval refinement and unchanged rendered slopes.
Build tests still validate the version-1 manifest and its existing local-only
coordinate declaration.

Before editing, 16 public/synthetic cases were captured across four fixtures,
65/129-pixel resolutions and two seeds. Compare Float32 DEM bytes, masks,
coordinate vectors, drainage diagnostics and both rendered pixel arrays exactly.
All 16 baselines matched exactly on Windows / CPython 3.14.7. All 134 tests,
Ruff and strict Pyright passed. This is a local-runtime compatibility check,
not a cross-platform promise.

## Action items

- [x] Use shared frame/grid values throughout current generation and products.
- [x] Add numerical and compatibility checks.
- [ ] Declare source-to-world correspondence and a metric working projection in
  an explicit future project contract.
- [ ] Implement registered georeferenced exports and regional refinement.
- [ ] Introduce independently derived stage seeds through a versioned change.
