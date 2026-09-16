# DM Tools

DM Tools is a local-first collection of reusable worldbuilding and tabletop
utilities. The project begins with a deterministic terrain generator: an engine
that turns authored coastlines, elevation guidance, landform regions, basin
intent, generator settings and a seed into a reproducible digital elevation model.

The application runs locally in Python. A future web
interface should call the same engine rather than replacing it.

## Status

The desktop workbench imports and dissolves closed SVG land shapes; authors
absolute/relative brush, point, ridge and valley constraints; draws plain, hill,
plateau and mountain regions; and saves those inputs as `.dmterrain.json`.
The editor keeps the last result as a placement reference, supports instruction
selection/property edits and undo/redo, and marks changed inputs for regeneration.
Authored lakes and dry basins retain ground and captured contributing area.
Reviewed lake outlets transfer eligible area downstream, with visible shoreline,
wet-link and dry-path evidence. Water levels are imposed previews, not simulated
lake equilibria.

Generation produces a Float32 ground DEM and separate derived water and drainage
review products. The workbench exports PNG. Headless builds also write NPY/NPZ,
local-metric GeoTIFF, both relief styles, diagnostics and a completion manifest.
Zoom-driven local detail generation is a core planned capability; the current
build still covers the whole coastline. World placement and validated river
vectors also remain future work. See the [current research status](docs/research/status.md).

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

GitHub CI uses Windows and Python 3.14 to run the complete pytest suite, Ruff,
and strict Pyright checks, including the display-free Tcl settings tests.
Pytest reports are retained for 14 days. Secret scanning runs separately with
the complete Git history available.

Open the public
[`example.dmterrain.json`](examples/terrain/example.dmterrain.json) project or
import its [`coastline.svg`](examples/terrain/coastline.svg) directly for a first
generation. Use **Save project** after adding terrain guidance, then **Open
project** to restore the coastline, generator settings, constraints, and
per-tool controls. The workbench explains invalid inputs before generation.

## Current workflow

```text
authored constraints + terrain profile + master seed
                         |
                         v
               deterministic pipeline
                         |
          +--------------+---------------+
          |              |               |
          v              v               v
     Float32 DEM    numeric reviews   visual previews
```

Authored vector constraints and configuration remain inputs. A floating-point
raster DEM is the authoritative generated elevation surface. Water and drainage
reviews, hillshade and colour relief are derived products. Contour/river vectors
and meshes are planned.

Build the same saved project without opening the workbench:

```powershell
dmtools terrain build examples/terrain/example.dmterrain.json --output artifacts/example-build
```

Read the [numeric build guide](docs/terrain-builds.md) for products, coordinate
limits, diagnostics and completion checks. Builds include lossless NPY arrays
and [Float32 GeoTIFF](docs/terrain-geotiff.md) in an explicit local metric frame.
World placement remains planned.

The current [project and build schemas](schemas/README.md) and
[named stage seed algorithm](docs/terrain-seeds.md) describe implemented behavior.
This project is in early development: obsolete features and old saves are not
supported. Current correctness and useful improvements take priority.

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
- Reproduction requires matching inputs, algorithms, runtime and named seeds.
- User-authored geographic constraints are never silently mutated.
- Numeric terrain data is authoritative; rendered maps are derived.
- Edit generation inputs over a read-only generated reference, then regenerate.
  Completed DEMs are never sculpted or patched in the editor.
- Shared-coordinate values remain consistent across output grid sizes. Planned
  local enrichment must additionally preserve parent geography and match
  neighboring regional boundaries; see [ADR-0048](docs/adr/0048-keep-zoom-driven-detail-generation.md).
- Scientific language remains honest about what the model does and does not
  prove.

## Licensing

The repository does not yet declare a distribution license. Adopted dependency licenses
are recorded in the [dependency register](docs/DEPENDENCIES.md). A project license must be chosen before
the first public release.
