# Schemas

Only the current formats are supported:

- [World project v1](world/project-v1.schema.json): portable `.dmworld.json` source
  snapshot, full-sphere frame/radius and explicit continent/island assignments.
  This is a validated source, not a climate/terrain build or generated parent.

- [World context v4](world/context-v4.schema.json): generated spherical coverage, separate water-piece connectivity/support,
  vector-derived water regions, shared-edge widths, shore distance, eight-direction
  water exposure, resolution support and hashes of the numeric
  arrays, previews and original world snapshot. This is not a terrain parent.

- [World geology v1](world/geology-v1.schema.json): separate `.dmgeology.json`
  input recipe with retained world identity, continent defaults, priority provinces
  and independent ages/duration. This does not modify geography or generate terrain.

- [Bathymetry inputs v1](world/bathymetry-inputs-v1.schema.json): portable
  `.dmbathy.json` world snapshot, explicit water IDs and shelf/slope/basin assumptions.
- [Bathymetry v1](world/bathymetry-v1.schema.json): negative ocean-floor centre
  samples, numerical error/support, a retained verified geographic dependency and
  result hashes. Neither a land DEM nor physical transport/heat capacity.

- [Project v6](terrain/project-v6.schema.json): authored `.dmterrain.json` inputs.
- [Build v18](terrain/build-v18.schema.json): numeric products, coordinates,
  algorithm identities, named stage seeds and output hashes.
- [Regional samples v2](terrain/regional-samples-v2.schema.json): bounded
  unchanged-field windows, source/runtime identity, halo/crop coordinates and
  explicit capability limits.
- [Input snapshot v2](terrain/input-snapshot-v2.schema.json): portable effective
  geometry, typed constraints, settings and authoring state for current builds.
- [Parent region v1](terrain/parent-region-v1.schema.json): verified-parent samples
  or explicit experimental detail, fixed cell moments and hydrology limits.

Register all current schemas locally by `$id` for validation. The build
references project settings; regional samples reuse current project settings
and the build's runtime, seed and file-identity definitions. None depends on
obsolete formats.
Terrain numeric arrays use an endpoint-node SVG-local plane. GeoTIFF records the
same samples in local metres with an upward y axis; neither has a world CRS.
See the [build guide](../docs/terrain-builds.md) and
[seed contract](../docs/terrain-seeds.md).

The [world guide](../docs/terrain-worlds.md) describes the implemented source
format and its independent geographic contract. The
[context guide](../docs/world-context.md) owns the implemented geographic result.
The [world-context plan](../docs/strategy/world-context.md) specifies future shared
climate/history and regional boundary products. Those later products have no
public schema yet; do not add placeholders to source or terrain formats.

During early development, replace obsolete formats and update the current
example, tests and documentation. Version identifiers record provenance and
reject unsupported input; old saves, compatibility loaders and migration paths
are out of scope. Superseded schemas are available in Git history.
