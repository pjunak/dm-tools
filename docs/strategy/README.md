# Current development strategy

This document is the current execution order for DM Tools. It translates the
categorized backlog and dated research into one dependency-aware plan. Update it
when measurements change the recommended order; preserve accepted decisions in
ADRs and preserve dated research as evidence.

## Document authority

When documents differ, use this order:

1. implemented code, public schemas, tests, and accepted ADRs define current
   behavior;
2. this strategy and the architecture overview define the current direction;
3. the roadmap lists possible and scheduled work by area, not execution order;
4. dated research records evidence available at the time and may become stale.

An evaluated package does not become a dependency merely by appearing in
research or this strategy. Adoption requires an immediate implementation use,
license review, Python 3.14 and Windows verification, and a measured benefit.

## Product boundary

```text
authored geography + versioned settings + master seed
                         |
                         v
             deterministic terrain build
                         |
                authoritative Float32 DEM
                         |
       +-----------------+------------------+
       |                 |                  |
       v                 v                  v
  terrain measures   climate fields   visual/GIS products
       |                 |
       +--------+--------+
                v
       ecological suitability
                |
                v
  biome, wetland, landform, and land-use views
```

The authored inputs and generated DEM remain authoritative for terrain.
Climate, ecological classifications, contours, drainage, and presentation
layers are derived products that can be rebuilt and inspected independently.

## Recommended execution order

### 1. Make terrain builds durable and reproducible

The first local build slice is implemented: headless project builds preserve
numeric NPY arrays, both previews, spatial diagnostics and a versioned manifest.
See the [build guide](../terrain-builds.md). It records the existing endpoint
grid and explicitly leaves world CRS/planetary radius unspecified; the steps
below still govern georeferenced output and independently seeded future stages.
The [coordinate contract](../terrain-coordinates.md) now centralizes source/local
conversion, endpoint registration and spacing across generation and products.
It preserves current numeric results without assigning a world position.

- Define source-world origin, planetary model, working projection, raster
  registration and effective process spacing before freezing georeferenced
  outputs. The current longest-dimension local plane is not a world CRS contract.
- Define the versioned build manifest and lock algorithm and stage identifiers.
- Export the authoritative Float32 DEM as a georeferenced GeoTIFF.
- Add the headless `terrain build` operation using the same project and pipeline
  as the desktop workbench.
- Record hashes, units, extent, sample spacing, effective settings, dependency
  versions, diagnostics, and output provenance.

Rasterio is the preferred Python GeoTIFF adapter, with pyproj for coordinate
operations and GDAL command-line tools as independent interoperability checks.

### 2. Measure before replacing the base solver

- Use the [benchmark harness](../../benchmarks/README.md) to record stage timing,
  process memory and numeric identities before changing algorithms or language.
  Keep Python for the current foundation/terrain experiments; reconsider a
  native core against the [migration gates](../research/2026-09-05-language-and-performance.md).
- Finish the quantitative landform fixtures and statistics in the roadmap.
- Add SciPy only for a focused comparison of local-neighbour RBF correction and
  a sparse screened-Poisson solve against the current surface.
- Select a replacement only if constraint residuals, slope continuity,
  runtime, and nested-resolution behavior improve measurably.

### 3. Complete the authored-terrain contract

- Separate hard equalities, soft guidance, and inequalities explicitly.
- Add per-vertex structure profiles, passes, asymmetric sides, and
  terrain-character regions.
- Reproject hard constraints after every optional process stage and report soft
  residuals rather than silently changing authored intent.

### 4. Finish hydrology semantics and validation

- Define authored lakes, outlets, endorheic basins, depression policy, and the
  public drainage and catchment products.
- Compare the in-project routing against Landlab first and GRASS GIS as an
  external reference. Keep Whitebox behind a separately audited optional
  boundary because its product family has mixed licensing.
- Treat landscape evolution as an optional, deterministic post-process only
  after hydrology and constraint preservation have quantitative tests.

### 5. Prove regional refinement

- Define parent-build identity, world-coordinate bounds, target spacing, halo,
  crop, and numeric downsample tolerance.
- Keep GeoTIFF as the first durable format. Evaluate chunked Zarr storage only
  after profiling demonstrates a real partial-I/O or large-array need.

### 6. Prototype climate as a separate global-context system

Do not implement climate continent by continent without shared global context.
The first deterministic prototype should consume the fixed world projection,
latitude, land/ocean mask, accepted DEM, orbital and rotational parameters,
prevailing circulation, and explicit authored overrides. It should produce
continuous seasonal or monthly fields before assigning named zones:

- surface temperature and seasonal range;
- precipitation, moisture transport, orographic enhancement, and rain shadow;
- coastal moderation and continentality;
- potential evapotranspiration, aridity, runoff, and terrain wetness; and
- diagnostics and uncertainty or suitability values.

Use a transparent NumPy/SciPy process model first. Smith-Barstad-style linear
orographic precipitation, FAO Penman-Monteith evapotranspiration, and the Budyko
water-balance relation are useful scientific components. Climlab and xclim are
reference or comparison libraries; ExoPlaSim is an external plausibility
experiment, not an interactive production dependency.

### 7. Derive classifications without collapsing their meanings

Named climate zones should be versioned classification views over continuous
fields. A familiar Köppen–Geiger-like view and a Holdridge-like ecological
cross-check can coexist. Biomes should use climate plus elevation, slope,
aspect, wetness, substrate, and authored overrides, preferably as fuzzy
suitability fields before a display classification.

Environmental concepts must remain separate overlapping layers:

| Concept | Layer | Main evidence |
|---|---|---|
| Tundra | Biome or life zone | Temperature, growing season, moisture, elevation |
| Bog | Wetland/ecosystem | Water balance, drainage, terrain wetness, substrate |
| Plain | Landform | Relief, slope, curvature, scale |
| Field | Cultural land use | Human choice plus terrain, climate, soil, and access suitability |

This prevents a single enum from forcing physically valid combinations such as
a bog on a tundra plain or cultivated fields within a temperate grassland into
mutually exclusive categories.

## Current technology position

| Area | Recommendation now | Evidence gate before adoption |
|---|---|---|
| Numeric core | Keep NumPy; spike SciPy locally | Fixture improvements and deterministic tolerances |
| DEM exchange | Rasterio GeoTIFF; pyproj metadata | Round-trip tests and GDAL interoperability |
| Hydrology comparison | Landlab, then external GRASS | Routing and basin fixture agreement |
| Large multidimensional data | Defer xarray/Zarr | Measured climate or partial-I/O requirement |
| Climate prototype | Transparent NumPy/SciPy fields | Earth analog fixtures and energy/water sanity checks |
| Full climate model | External ExoPlaSim experiment only | Reproducible workflow and useful validation signal |
| Classifications | Versioned in-project rules | Published definitions, edge fixtures, and uncertainty |

## Revisit points

The [landform-diversity research](../research/2026-09-04-terrain-realism-and-landform-diversity.md)
adds the R01–R33 candidate register in the roadmap without promoting research
engines to dependencies. Within the phases above, prioritize a measured
regional-character/oriented-detail comparison, reconciliation of generated
drainage with authored macro geography, a sediment-aware valley experiment,
and multi-scale regional refinement. Measure final-surface drainage after
constraint restoration and parent restriction. The 2026 stochastic-transport
paper merits an isolated comparison; retain the existing reproducibility and
constraint gates rather than rejecting particle methods as a whole.

The [prototype-contract follow-up](../research/2026-09-04-terrain-prototype-contracts.md)
adds R34–R39 and narrows the first detail experiment to suitable mountain
regions. Measure spectral-amplitude changes and regional transition gradients
before judging oriented detail; use separate recipes for plateau tops and
alluvial floors. Compare SPACE with a single-receiver reference and a sediment
ledger. Establish numeric exchange, fixed iteration counts and grid registration
before evaluating external multiscale engines. Shared-node equality and parent
cell-average consistency need separate tests. Meanderpy and pyDeltaRCM remain
focused channel/delta comparisons after their prerequisites, not dependencies.

The [geological-composition follow-up](../research/2026-09-05-geological-structure-and-terrain-composition.md)
adds R40–R44 within those experiments. Compare related regional recipes and a
small analytical substrate before considering a geological engine. Measure
spatial arrangement, direction and observation scale alongside height
distributions. Keep morphological ridges, drainage divides and active channels
semantically distinct, and compare important peak/pass relationships across
stages. LoopStructural, SurfaceNetwork and TTK are optional reference tools;
their appearance in research does not change the core dependency plan.

Create or amend an ADR when a prototype selects a new solver, file format,
external engine, climate contract, or classification contract. Revisit this
order when a prerequisite is measured complete, a dependency lacks supported
Python 3.14/Windows behavior, or a supposedly later capability is proven to
change an earlier public data contract.
