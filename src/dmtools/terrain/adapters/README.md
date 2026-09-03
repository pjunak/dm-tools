# Terrain adapters

This package contains concrete integration boundaries. The current adapters
load, dissolve, validate, and fingerprint SVG land geometry, strictly read and atomically write the
versioned JSON terrain project, and render or save a PNG preview. Future adapters
will add GeoPackage and GeoTIFF I/O, projection libraries, and optional external
scientific engines.

An adapter must translate external behavior into domain contracts and report its
effective tool and library versions for the build manifest.
