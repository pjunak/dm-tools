# Terrain adapters

This package owns concrete file and rendering boundaries:

- load, dissolve, validate and fingerprint SVG land geometry;
- strictly read and atomically write the current JSON terrain project;
- render relief, water and drainage review images and save PNG previews;
- write Float32 local-metric GeoTIFF, NPY terrain/mask/coordinate arrays and
  NPZ routing/water/basin-flow products; and
- serialize diagnostics and publish a hashed completion manifest after the
  build application verifies completion inputs.

Read the [build contract](../../../../docs/terrain-builds.md) for the product
inventory and publication rules. GeoTIFF export is implemented; world
projection, GeoPackage/vector products and external scientific-engine exchange
remain future adapters.

An adapter translates external behavior into domain contracts and reports its
effective tool/library versions where required by the build manifest.
