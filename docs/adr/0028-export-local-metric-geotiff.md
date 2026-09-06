# ADR-0028: Export local-metric GeoTIFF

**Status:** Accepted
**Date:** 2026-09-06
**Decider:** Implementation within the authorized terrain-development work.

## Decision

Write the current Float32 surface as `elevation.tif` in every headless build.
Use Rasterio behind the file adapter boundary. Preserve the existing NPY
products for direct numeric analysis. Both represent the same surface.

Declare a local engineering CRS in metres, with Easting = 1000 * x_km and
Northing = -1000 * y_km. Do not invent world placement or use an Earth EPSG
code for unlocated SVG input. Export local data now so numeric GIS exchange,
point registration and nodata handling can be exercised before adding world
positioning. A local engineering CRS does not establish ground distances on
a planet.

Use PixelIsPoint and a half-cell outer-corner offset in GDAL's affine mapping.
Keep raster rows unchanged. Store NaN outside land, an internal valid-data mask,
a metre band unit, lossless DEFLATE compression and 256-square tiles. Record
numeric source and completion-manifest references without a circular build hash.
See the [export contract](../terrain-geotiff.md) and
[GDAL RFC 33](https://gdal.org/en/stable/development/rfc/rfc33_gtiff_pixelispoint.html).

Build format 4 adds the TIFF product, its coordinate mapping and native runtime
versions. Remove build schema 3; no compatibility path is provided. Project
format 3 is unchanged because no authored setting is added. Require successful
TIFF publication before publishing the final manifest.

## Alternatives and consequences

Waiting for full planetary projection would postpone useful numeric exchange.
Pretending the existing SVG plane is a geographic or projected Earth CRS would
misrepresent it. Exporting through a colour image would lose elevation data.
A local-metric raster is the smallest useful implementation with honest units
and position semantics.

Rasterio 1.5.1 and Affine 3.0.1 were installed from wheels on Windows /
CPython 3.14.7. The wheel exposes GDAL 3.12.4 and PROJ 9.8.1. Both packages use
BSD-style licensing; the [dependency register](../DEPENDENCIES.md) records
adoption and references. No projection library enters domain or generation code.

The output is not yet a world-georeferenced map, a cloud-optimized GeoTIFF,
a pyramid or a regional-refinement product. Extend the current implementation
when those capabilities are ready rather than retaining obsolete formats.

## Validation

Check exact Float32 values against NPY, zero-height valid samples, water masks,
unequal spacings, translated origins and raw TIFF point tiepoints. Validate
repeatable builds and strict current schemas. Failed exports and existing
outputs must not publish success or overwrite input data. Native GDAL option
contexts are scoped so writer behavior does not depend on inherited point
registration or sidecar preferences.

The 768 by 455 public example completed with a 802,708-byte GeoTIFF. Rasterio
API and raw TIFF metadata checks passed. The installed `rio info` command
failed because it unconditionally asks for Earth longitude/latitude from the
engineering CRS; this limitation is documented rather than supplying an
invented Earth position. Desktop GIS display remains unverified.

All 169 tests, Ruff, strict Pyright and pip dependency checks passed.
Validated 177 local documentation links.
