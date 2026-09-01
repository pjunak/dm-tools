# Schemas

This directory owns versioned public data contracts for DM Tools. Terrain
schemas will live under `terrain/` once their fields and compatibility policy
have been accepted.

Schemas should describe serialized structure and validation constraints. Python
models may implement them, but project files must not depend on private class
layout or unversioned implementation details.
