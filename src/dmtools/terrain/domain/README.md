# Terrain domain

This package contains dependency-light terrain concepts and invariants. The
implemented authoring types are a closed coastline, exact elevation points,
soft terrain-brush strokes, ridge and valley centrelines, and effective
generator settings. Constraint positions use normalized coastline-bounds
coordinates until the pipeline converts them to the metric working extent.
Every authored elevation feature explicitly records whether its metre value is
an absolute elevation or a relative displacement, relief, or incision depth.
The domain also owns a format-independent terrain project and the authoring-tool
defaults that must survive between workbench sessions.

The domain should grow only when a public contract requires it. Planned areas
include explicit coordinate-reference metadata, per-vertex structure profiles,
build manifests, stable stage identifiers, and structured validation results.

Domain code must not read files, call external tools, render images, or depend on
CLI and web frameworks.
