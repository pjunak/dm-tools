# Terrain tool

The terrain tool will generate reproducible elevation data from an authored
geographic skeleton. It is designed for continent-scale work that can later be
refined into consistent regional and local maps.

## Inputs

The intended input project contains:

- a coastline or land mask with sea level;
- spot heights and optional height ranges;
- ridge, divide, valley, river, fault, and escarpment guides;
- terrain-character regions;
- a versioned terrain profile;
- a master seed; and
- an explicit planetary model, projection, extent, and working resolution.

The exact serialized schema has not yet been accepted.

## Outputs

A successful build is expected to produce:

- a Float32 elevation raster in metres;
- a machine-readable build manifest;
- derived contours and drainage vectors;
- hillshade and elevation-colour previews; and
- validation results describing satisfied constraints and known limitations.

## Internal modules

| Module | Responsibility |
|---|---|
| `domain/` | Units, coordinates, constraints, profiles, grids, manifests, and ports |
| `pipeline/` | Deterministic stage orchestration and refinement rules |
| `adapters/` | File formats, GIS libraries, renderers, and optional engines |

These are boundaries, not promises of immediate complexity. Add modules within
them only when an implemented behavior needs them.

## Planned first vertical slice

The first end-to-end slice should deliberately be modest:

1. Read a versioned synthetic project.
2. Validate a closed coastline and several exact elevation points.
3. Establish a metric working grid.
4. Interpolate a deterministic base surface.
5. Enforce the land/sea boundary and validate the hard constraints.
6. Write a small Float32 GeoTIFF, hillshade preview, and complete manifest.

Conditioned stochastic detail, structural lines, erosion, hydrology, and local
refinement should follow only after this path is reproducible and tested.
