# Architecture overview

DM Tools is a modular Python application with local desktop and command-line
interfaces. Hosting will add an HTTP adapter around the same application
operations later.

## System boundary

```text
Tk UI / CLI
     |
     +--> application build operation
     |           |
     +-----------+--> numeric generation pipeline --> domain values
                 |
                 +--> project / SVG / render / GeoTIFF / build adapters
```

The workbench also calls generation and adapters directly. There is no generic
adapter-port framework. Domain modules are dependency-light; numeric pipeline
modules currently use NumPy and Shapely geometry. File formats, rendering and
publication remain in adapters outside generation.

The domain and pipeline must remain usable without a web server. Adapters may
depend on Rasterio, GDAL, GeoPackage drivers, image renderers, or external
scientific engines; core contracts must not depend on those concrete libraries.

## Terrain pipeline

The current implemented path is:

1. Load and validate an SVG or versioned terrain project, then dissolve its
   closed land geometry.
2. Convert normalized authored constraints into the source-bounds local metric
   frame shared by mainland and islands. This is scaling, not a world projection.
3. Compose regional full/macro fields, prepare stable valley profiles and apply
   authored macro constraints before canonical routing. Lake/dry footprints
   absorb flow; regional relief limits automatic incision.
4. Reapply final authored semantics and restore permitted coordinate-addressed
   detail. Return Float32 ground without filling it to the routing surface.
5. Review finished ground on the shared canonical grid, retaining basin labels,
   spill paths, topology and unresolved channel conflicts. `diagnostics.py`
   owns read-only review; `hydrology.py` owns flow and incision primitives.
6. Derive clipped lake water and review shorelines, outlet attachments, full
   external paths and internal wet/dry links against finer Float32 samples.
   `water_sampling.py` owns probe plans; `outlet_profiles.py`, `wet_links.py`
   and `dry_links.py` own path/link checks. `basin_flow.py` conserves captured
   area while transferring only eligible collections. These checks do not
   establish physical lake equilibrium, discharge or a complete river network.
7. The workbench renders derived relief/review overlays and exports PNG. The
   shared headless build operation writes NPY/NPZ, local-metric GeoTIFF, both
   preview styles, diagnostics and a completion-last manifest through adapters.

The next durable-build work adds world georeferencing,
derived GIS products, explicit hard/soft/inequality projection after optional
processes, and regional-refinement validation. Climate and ecological products
are a later derived system that consumes accepted terrain and global world
context rather than becoming an implicit terrain stage.

Source-to-local conversion and uniform endpoint grids are dependency-light
domain values shared by generation, routing, diagnostics, rendering and build
metadata. NumPy axis construction stays in the pipeline. Read the
[coordinate contract](../terrain-coordinates.md) and
[ADR-0025](../adr/0025-centralize-local-frames-and-endpoint-grids.md).

Each stage receives explicit inputs and configuration. It must not obtain
randomness, time, environment settings, or coordinate assumptions implicitly.
The [named seed policy](../terrain-seeds.md) resolves stable stage identifiers
from a master without mutable RNG state. Both coarse and detailed relief remain views of the same stage.
There is no alternative seed mode.

Completed-field sampling separates the pointwise evaluator from land masking
and output scattering. It omits ocean coordinates while preserving complete
canonical hydrology grids and precomputed valley profiles. Neighbor-dependent
algorithms must stay outside that pointwise evaluator. The repository-only
[benchmark harness](../../benchmarks/README.md) records stage time, process
memory and numerical identities without adding timing state to the engine.

## Interfaces

The first useful interface is a Tk/ttk desktop workbench launched through the
CLI. It maps controls to typed domain settings, then delegates to the same
pipeline and adapters used by the non-interactive build operation.
A future HTTP service can call those operations while adding job management,
storage, authentication, and resource limits outside the engine.

The current terrain-project adapter translates the public JSON contract into
domain models. It resolves the external SVG relative to the project, verifies
its content hash, then delegates coastline parsing to the SVG adapter. Neither
the domain nor the generation pipeline reads project files directly.

The SVG adapter turns one or more closed land shapes into dissolved polygonal
land geometry. Shared subcontinent edges are removed before generation;
disconnected islands and retained enclosed water use the same metric extent and
coordinate-addressed field. The pipeline therefore receives geometry, not SVG
layer or path boundaries.

## Deferred decisions

- World-georeferenced build contracts and explicit source placement
- Direct per-vertex profiles, explicit passes and asymmetric structural sides
  (point-anchored longitudinal ridge/valley profiles are implemented)
- Inter-lake transfer, constrained repair and nested depression policy
  (lake levels, retention, outlet checks and conservative area transfer are implemented)
- River/catchment vector products and external hydrology validation
  (numeric routing, footprint collection and basin review archives are implemented)
- Multiresolution storage and refinement strategy
- Global climate-field and ecological-classification contracts
- Web framework, queue, storage, and frontend
- Public project license

These belong in ADRs when enough evidence exists to make the decision. The
[current development strategy](../strategy/README.md) gives their recommended
dependency order; the roadmap remains grouped by product area.
