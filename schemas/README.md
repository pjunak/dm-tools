# Schemas

Only the current terrain formats are supported:

- [Project v5](terrain/project-v5.schema.json): authored `.dmterrain.json` inputs.
- [Build v11](terrain/build-v11.schema.json): numeric products, coordinates,
  algorithm identities, named stage seeds and output hashes.

Register these two schemas locally by `$id` when validating builds. The build
references current project settings; neither schema depends on old versions.
The numeric arrays use an endpoint-node SVG-local plane. GeoTIFF records the
same samples in local metres with an upward y axis; neither has a world CRS.
See the [build guide](../docs/terrain-builds.md) and
[seed contract](../docs/terrain-seeds.md).

During early development, replace obsolete formats and update the current
example, tests and documentation. Version identifiers record provenance and
reject unsupported input; old saves, compatibility loaders and migration paths
are out of scope. Superseded schemas are available in Git history.
