# Schemas

Only the current terrain formats are supported:

- [Project v5](terrain/project-v5.schema.json): authored `.dmterrain.json` inputs.
- [Build v16](terrain/build-v16.schema.json): numeric products, coordinates,
  algorithm identities, named stage seeds and output hashes.
- [Regional samples v1](terrain/regional-samples-v1.schema.json): bounded
  unchanged-field windows, source/runtime identity, halo/crop coordinates and
  explicit capability limits.

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
