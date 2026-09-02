# Terrain domain

This package contains dependency-light terrain concepts and invariants. The
implemented authoring types are a closed coastline, exact elevation points,
ridge and valley centrelines, and effective generator settings. Constraint
positions use normalized coastline-bounds coordinates until the pipeline
converts them to the metric working extent.

Future domain types will add units, coordinate reference systems, structure
profiles, grids, manifests, stage identifiers, and validation errors.

Domain code must not read files, call external tools, render images, or depend on
CLI and web frameworks.
