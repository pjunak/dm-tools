# Architecture overview

DM Tools is a modular Python application with local command-line interfaces.
Hosting will add an HTTP adapter around the same application operations later.

## System boundary

```text
CLI now / HTTP later
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
domain model   adapter ports
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

The planned high-level stages are:

1. Load and validate a versioned terrain project.
2. Normalize authored constraints into a metric working grid.
3. Construct a base surface satisfying hard and soft constraints.
4. Add deterministic, conditioned relief at named spatial scales.
5. Apply optional process-informed erosion or diffusion.
6. Validate hydrology, constraints, finite values, and level-of-detail
   consistency.
7. Write the authoritative DEM, derived vectors, previews, and build manifest.

Each stage receives explicit inputs and configuration. It must not obtain
randomness, time, environment settings, or coordinate assumptions implicitly.

## Interfaces

The first interface is a CLI. Its eventual build operation should delegate to
an application service that accepts typed configuration and returns an artifact
manifest. A future HTTP service can call that same operation while adding job
management, storage, authentication, and resource limits outside the engine.

## Deferred decisions

- Terrain project and constraint schema details
- Initial interpolation algorithm
- Hydrology engine
- Multiresolution storage and refinement strategy
- Web framework, queue, storage, and frontend
- Public project license

These belong in ADRs when enough evidence exists to make the decision.
