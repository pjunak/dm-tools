# Architecture overview

DM Tools is a modular Python application with local desktop and command-line
interfaces. Hosting will add an HTTP adapter around the same application
operations later.

## System boundary

```text
Tk UI / CLI now / HTTP later
             |
             v
    application operations
             |
             v
   deterministic tool pipelines
             |
      +------+-------+
      |              |
      v              v
 domain model    adapter ports
                     |
             +-------+--------+
             |       |        |
             v       v        v
          files     GIS    optional engines
```

The domain and pipeline must remain usable without a web server. Adapters may
depend on Rasterio, GDAL, GeoPackage drivers, image renderers, or external
scientific engines; core contracts must not depend on those concrete libraries.

## Terrain pipeline

The current implemented path is:

1. Load and validate an SVG or versioned terrain project, then dissolve its
   closed land geometry.
2. Project normalized authored constraints into one metric working grid shared
   by mainland sections and islands.
3. Prepare valley profiles against a stable pre-incision reference and construct
   the broad routing surface with authored constraints. Route automatic valleys
   on its canonical grid and retain the drainage topology.
4. Apply authored brush, point, ridge, and valley semantics and restore
   coordinate-addressed residual detail.
5. Calculate finite-value, coastline, basin and drainage diagnostics. Compare
   planned channels against the finished field on matching routing nodes;
   preserve authoritative constraints and report unresolved uphill segments.
6. Return the Float32 DEM in memory and derive the workbench colour preview and
   PNG export. The shared headless application operation also writes numeric
   NPY arrays, local-metric GeoTIFF, both preview styles, spatial measurements and a completion
   manifest using the existing local-coordinate model.

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
- Elevation profiles and asymmetric side slopes along structural lines
- Authored lake, outlet, endorheic-basin, and depression-policy semantics
- Public drainage/catchment products and external hydrology validation boundary
- Multiresolution storage and refinement strategy
- Global climate-field and ecological-classification contracts
- Web framework, queue, storage, and frontend
- Public project license

These belong in ADRs when enough evidence exists to make the decision. The
[current development strategy](../strategy/README.md) gives their recommended
dependency order; the roadmap remains grouped by product area.
