# AGENTS.md — DM Tools

Read this file before changing anything in this repository. More specific
`AGENTS.md` files add constraints within their subtrees.

## Purpose

DM Tools is a local-first collection of reusable worldbuilding and tabletop
utilities. Tools must work without a hosted service. A future web application
may expose the same application interfaces, but it must not become the only way
to use or reproduce a tool.

The first tool is a deterministic, constraint-driven terrain generator. It
turns authored geographic constraints and a versioned profile into numeric
elevation data and derived cartographic products.

## Repository contract

- Use CPython 3.14 for project-owned Python code.
- Keep the reusable engine independent of CLI, filesystem, GIS-library, and
  future HTTP concerns.
- Treat files under `src/dmtools/` as product code, `tests/` as executable
  contracts, `schemas/` as public data contracts, and `examples/` as small,
  reviewable demonstrations.
- Do not commit generated terrain builds. Small purpose-built fixtures are
  allowed under `tests/fixtures/` when their provenance is documented.
- Keep user-authored constraints authoritative. Generated output must never
  silently overwrite an input project.
- Record architectural decisions under `docs/adr/`; supersede decisions rather
  than rewriting their history.

## Architecture boundaries

The expected dependency direction is:

```text
interfaces -> application pipeline -> domain model
                    |
                    v
                 adapters
```

- Domain code owns units, coordinates, constraints, profiles, grids, manifests,
  and validation rules. It must not depend on CLI or web frameworks.
- Pipeline code orchestrates deterministic stages and depends on domain
  contracts, not concrete file formats.
- Adapters implement GeoPackage, GeoTIFF, image, external-process, and future
  service boundaries.
- Rendering is derived from numeric elevation data; visual products are never
  the authoritative terrain model.

Avoid a plugin system, task queue, database, or web framework until a concrete
requirement justifies one.

## Reproducibility

A numeric seed alone is not a reproducibility contract. Every completed build
must eventually record:

- schema and generator versions;
- master seed and named per-stage derived seeds;
- hashes of all authored inputs and profiles;
- coordinate reference system, extent, resolution, units, and nodata policy;
- algorithm identifiers and effective parameters;
- dependency and runtime versions; and
- hashes of authoritative outputs.

Changing the order of unrelated pipeline stages must not perturb existing
random streams. Derive stage seeds from stable stage identifiers rather than
sharing one mutable random-number generator.

## Scientific and cartographic integrity

- Store horizontal distances and elevations with explicit units.
- Never run distance-sensitive algorithms directly in angular or page
  coordinates. Use an appropriate metric working projection.
- Distinguish hard constraints, soft guidance, generated hypotheses, and
  derived display layers.
- Validate coastline elevation, authored height constraints, finite values,
  drainage behavior, refinement seams, and parent/child level consistency.
- Describe generated terrain as plausible or process-informed unless the model
  and evidence support a stronger scientific claim.

## Dependencies and licenses

- Prefer mature, maintained libraries over project-owned implementations of
  interpolation, projection, raster I/O, and numerical primitives.
- Keep optional scientific engines behind adapters so the core remains usable
  when an engine does not support Python 3.14 or the current platform.
- Record the package version, license, purpose, and distribution implications
  before adding a restrictive, copyleft, non-commercial, or source-available
  dependency.
- Add dependencies only with an immediate use; do not preload the full research
  shortlist into the base environment.

## Validation and Git

- Add or update tests with behavior changes. Prefer small deterministic fixtures
  and invariant/property tests over large golden rasters.
- Run the narrowest relevant checks while iterating, then the documented
  repository checks before committing.
- Commit logical, validated changes locally. Do not push, publish packages,
  deploy services, or rewrite shared history without explicit authorization.
- Preserve unrelated worktree changes and never commit generated outputs,
  private maps, credentials, or local tool state.
