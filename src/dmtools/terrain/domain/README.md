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

Local frames, endpoint grids, named stage seeds and bounded regional sampling
requests live here. Requests bind an input-defined full field and reference grid
to nested fine addresses and a halo, with sample and precision limits. World
placement, direct per-vertex structure profiles and finished-parent restriction
contracts for added local detail remain future work. Application/adapters own
manifest publication.

Domain code must not read files, call external tools, render images, or depend on
CLI and web frameworks.
