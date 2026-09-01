# DM Tools

DM Tools is a local-first collection of reusable worldbuilding and tabletop
utilities. The project begins with a deterministic terrain generator: an engine
that will turn an authored coastline, elevation constraints, structural terrain
guides, a profile, and a seed into a reproducible digital elevation model.

The repository is intentionally starting as a local Python project. A future web
interface should call the same engine rather than replacing it.

## Status

Early architecture scaffold. The package and command-line entry point exist,
but terrain generation is not implemented yet.

## Requirements

- CPython 3.14
- Git

No GIS or numerical runtime dependencies are included yet. They will be added
stage by stage after compatibility, licensing, and reproducibility checks.

## Quick start

Create a Python 3.14 virtual environment and install the project in editable
mode with its development tools:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Then inspect the available command structure and run the tests:

```powershell
.\.venv\Scripts\dmtools.exe --help
.\.venv\Scripts\dmtools.exe terrain --help
.\.venv\Scripts\python.exe -m pytest
```

The terrain command currently exposes help only. Its first useful operation will
be a deterministic build from a versioned project file.

## Intended workflow

```text
authored constraints + terrain profile + master seed
                         |
                         v
               deterministic pipeline
                         |
          +--------------+---------------+
          |              |               |
          v              v               v
     Float32 DEM     vector products   visual previews
```

Authored vector constraints and configuration remain inputs. A floating-point
raster DEM is the authoritative generated elevation surface. Contours, drainage,
hillshade, colour relief, and future meshes are derived products.

The future command shape is expected to resemble:

```powershell
dmtools terrain build examples/terrain/minimal/project.yaml
```

The exact project schema will be designed and versioned before this command is
implemented.

## Repository layout

| Path | Responsibility |
|---|---|
| `src/dmtools/` | Shared package and command-line interface |
| `src/dmtools/terrain/` | Terrain domain, pipeline, and adapters |
| `schemas/` | Versioned public input and manifest schemas |
| `examples/` | Small public example projects |
| `tests/` | Unit, contract, integration, and deterministic regression tests |
| `docs/architecture/` | Current system structure and data flow |
| `docs/adr/` | Append-only architecture decisions |

See [the documentation index](docs/README.md), [the architecture overview](docs/architecture/README.md), and [the terrain tool guide](src/dmtools/terrain/README.md).

## Design principles

- Local use is complete use; hosting is an additional interface.
- The same inputs, versions, and seed produce the same authoritative output.
- User-authored geographic constraints are never silently mutated.
- Numeric terrain data is authoritative; rendered maps are derived.
- Continental and local detail form a parent/child hierarchy rather than
  independent generations.
- Scientific language remains honest about what the model does and does not
  prove.

## Licensing

The repository does not yet declare a distribution license. Dependency licenses
will be recorded as tools are selected. A project license must be chosen before
the first public release.
