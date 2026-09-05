# Schemas

This directory owns versioned public data contracts for DM Tools. The first
accepted contract is the
[`terrain/project-v1.schema.json`](terrain/project-v1.schema.json) schema for
`.dmterrain.json` authored project files.

The [local build manifest](terrain/build-v1.schema.json) records implemented
numeric NPY outputs, previews, measurements and reproducibility information.
It explicitly describes an endpoint-node SVG-local plane with no world CRS.
See the [build guide](../docs/terrain-builds.md) for file semantics and validation.

Schemas should describe serialized structure and validation constraints. Python
models may implement them, but project files must not depend on private class
layout or unversioned implementation details.

Existing schema files are immutable compatibility references. Incompatible
changes require a new numbered schema and an explicit loader or migration path.

The opt-in [project v2](terrain/project-v2.schema.json) and
[build v2](terrain/build-v2.schema.json) add named stage seeds. Original-policy
projects still save/build as v1. Register all four schemas locally for v2
validation because it references immutable v1 definitions. See the
[seed contract](../docs/terrain-seeds.md) for policy selection and exact encoding.
