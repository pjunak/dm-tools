# DM Tools

DM Tools is a local-first collection of reusable worldbuilding and tabletop
utilities. The project begins with a deterministic terrain generator: an engine
that will turn an authored coastline, elevation constraints, structural terrain
guides, a profile, and a seed into a reproducible digital elevation model.

The repository is intentionally starting as a local Python project. A future web
interface should call the same engine rather than replacing it.

## Status

The first terrain-generator vertical slice is usable. Its desktop workbench can
import and dissolve closed SVG mainland and island shapes, paint broad soft
elevation guidance, draw exact or relative height points plus ridge and valley
centrelines, generate a deterministic constraint-conditioned elevation field,
preview it as colour relief, and export the preview as a transparent PNG. Every
authoring tool keeps its own mode, value, and width while the user switches
tools. Authored work can be saved and reopened as a versioned
`.dmterrain.json` project.
The headless build command also saves numeric elevations, both preview styles,
spatial measurements and a versioned provenance manifest in a new directory.

## Requirements

- CPython 3.14
- Git
- Tk 9 (included with the official Windows CPython 3.14 distribution)

Runtime dependencies and their roles and licenses are recorded in
[the dependency register](docs/DEPENDENCIES.md).

## Quick start

Create a Python 3.14 virtual environment and install the project in editable
mode with its development tools:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Then open the terrain workbench and run the tests:

```powershell
.\.venv\Scripts\dmtools.exe --help
.\.venv\Scripts\dmtools.exe terrain gui
.\.venv\Scripts\python.exe -m pytest
```

Open the public
[`example.dmterrain.json`](examples/terrain/example.dmterrain.json) project or
import its [`coastline.svg`](examples/terrain/coastline.svg) directly for a first
generation. Use **Save project** after adding terrain guidance, then **Open
project** to restore the coastline, generator settings, constraints, and
per-tool controls. The workbench explains invalid inputs before generation.

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

Build the same saved project without opening the workbench:

```powershell
dmtools terrain build examples/terrain/example.dmterrain.json --output artifacts/example-build
```

Read the [numeric build guide](docs/terrain-builds.md) for products, coordinate
limits, diagnostics and completion checks. The current build uses lossless NPY
arrays in the existing local SVG plane; world-georeferenced GeoTIFF is planned.

The accepted version-1 project contract is published in
[`schemas/terrain/project-v1.schema.json`](schemas/terrain/project-v1.schema.json).
The explicit [named stage seed policy](docs/terrain-seeds.md) uses project/build
version 2 while preserving original-project behavior by default.

## Repository layout

| Path | Responsibility |
|---|---|
| `src/dmtools/` | Shared package and command-line interface |
| `src/dmtools/terrain/` | Terrain domain, pipeline, and adapters |
| `schemas/` | Versioned public input and manifest schemas |
| `examples/` | Small public example projects |
| `tests/` | Unit, contract, integration, and deterministic regression tests |
| `benchmarks/` | Repeatable development-only terrain timing and memory probes |
| `docs/architecture/` | Current system structure and data flow |
| `docs/adr/` | Append-only architecture decisions |
| `docs/strategy/` | Current dependency-aware development order |
| `docs/research/` | Dated evidence and prototype recommendations |

Start with [the current development strategy](docs/strategy/README.md), then see
[the documentation index](docs/README.md),
[the architecture overview](docs/architecture/README.md), and
[the terrain tool guide](src/dmtools/terrain/README.md). The categorized
implementation backlog is maintained in the [terrain tool roadmap](TODO.md).
Use the [benchmark guide](benchmarks/README.md) to compare performance without
changing authored projects or introducing machine-dependent test thresholds.

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
