# Schemas

Only the current terrain formats are supported:

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
The numeric arrays use an endpoint-node SVG-local plane. GeoTIFF records the
same samples in local metres with an upward y axis; neither has a world CRS.
See the [build guide](../docs/terrain-builds.md) and
[seed contract](../docs/terrain-seeds.md).

During early development, replace obsolete formats and update the current
example, tests and documentation. Version identifiers record provenance and
reject unsupported input; old saves, compatibility loaders and migration paths
are out of scope. Superseded schemas are available in Git history.
