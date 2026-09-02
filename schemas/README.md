# Schemas

This directory owns versioned public data contracts for DM Tools. The first
accepted contract is the
[`terrain/project-v1.schema.json`](terrain/project-v1.schema.json) schema for
`.dmterrain.json` authored project files.

Schemas should describe serialized structure and validation constraints. Python
models may implement them, but project files must not depend on private class
layout or unversioned implementation details.

Existing schema files are immutable compatibility references. Incompatible
changes require a new numbered schema and an explicit loader or migration path.
