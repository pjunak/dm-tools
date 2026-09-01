# AGENTS.md — Terrain tool

These instructions apply to `src/dmtools/terrain/` and its tests, schemas,
examples, and documentation when they implement the terrain tool.

## Product contract

The terrain tool compiles authored constraints into a deterministic hierarchy
of elevation products. It does not invent or silently change canonical
geography. A run may offer alternatives, but adopting one remains a user
decision.

The build identity is the combination of authored inputs, effective profile,
master seed, schema and generator versions, working grid, algorithm versions,
and runtime environment. Never describe the seed alone as sufficient for exact
reproduction.

## Source boundaries

- `domain/` owns dependency-light types, invariants, units, errors, and ports.
- `pipeline/` owns named deterministic stages and orchestration.
- `adapters/` owns concrete files, GIS libraries, rendering libraries, and
  external processes.
- This `README.md` owns the current terrain-tool overview. Public schemas under
  `/schemas/terrain/` own serialized field names and validation rules.

Dependencies point inward. Domain modules must not import adapters or interface
frameworks. Pipeline stages operate on typed domain values rather than loose
dictionaries or global settings.

## Authoritative data

- Vector constraints express coastlines, water levels, spot heights, ridges,
  valleys, divides, breaklines, and terrain-character regions.
- A Float32 raster DEM in metres is the authoritative generated elevation
  surface for a build.
- Contours, hillshade, colour relief, drainage, catchments, and meshes are
  derived outputs and must identify their source DEM.
- Local refinements must preserve their parent level when downsampled within a
  documented tolerance. Generate buffered halos and crop them to avoid seams.

## Stage rules

- Give every stochastic stage a stable identifier and a separately derived
  seed.
- Make units, nodata behavior, boundary conditions, and projection explicit.
- Do not mutate input objects or overwrite authored files.
- Write build artifacts to a new output directory and publish the manifest only
  after all authoritative outputs succeed.
- A failed run must not look complete.

## Testing

- Test hard constraints numerically, not only through image snapshots.
- Include invariants for finite values, land/sea masks, units, deterministic
  hashes, drainage connectivity where promised, and refinement boundaries.
- Use small synthetic fixtures with known intent. Large private world maps are
  not test data.
- Treat changes to schemas, seed derivation, algorithms, or numeric tolerances as
  compatibility changes requiring explicit documentation.
