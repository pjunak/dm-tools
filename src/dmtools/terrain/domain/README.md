# Terrain domain

This package owns dependency-light terrain concepts and invariants: multipart
coastlines, absolute/relative brush and point constraints, ridge/valley lines,
landform regions, lake/dry-basin intent, effective settings and authoring defaults.
Constraint positions remain normalized to coastline bounds until the pipeline
converts them to local metric coordinates.

Elevation mode belongs to topographic constraints. Lake levels are explicit
absolute metre levels; dry basins impose retention without a water surface.
Regional recipes have their own base-height, relief and transition controls.
The format-independent project keeps authored inputs separate from generated
terrain and review products.

Local frames, endpoint grids and named stage seeds live here. World placement,
direct per-vertex structure profiles and explicit parent/child contracts for
zoom-driven local generation remain future work. Build application/adapters own
manifest publication.

Domain code must not read files, call external tools, render images, or depend on
CLI and web frameworks.
