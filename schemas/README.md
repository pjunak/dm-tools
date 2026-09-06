# Schemas

Only the current terrain formats are supported:

- [Project v3](terrain/project-v3.schema.json): authored `.dmterrain.json` inputs.
- [Build v3](terrain/build-v3.schema.json): numeric products, coordinates,
  algorithm identities, named stage seeds and output hashes.

Register these two schemas locally by `$id` when validating builds. The build
references current project settings; neither schema depends on old versions.
The coordinate model is an endpoint-node SVG-local plane with no world CRS.
See the [build guide](../docs/terrain-builds.md) and
[seed contract](../docs/terrain-seeds.md).

During early development, replace obsolete formats and update the current
example, tests and documentation. Version identifiers record provenance and
reject unsupported input; old saves, compatibility loaders and migration paths
are out of scope. Superseded schemas are available in Git history.
