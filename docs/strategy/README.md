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

## Early-development priority

Implement and improve current behavior. Remove obsolete features, old-save
loaders, compatibility switches and superseded schemas as they become
unnecessary. Version identifiers serve provenance, not support promises.
The execution order below addresses engineering prerequisites, not a freeze
on current outputs. See [ADR-0027](../adr/0027-develop-current-behavior-without-legacy-support.md).

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

## Next implementation order

The implemented baseline includes local numeric builds, named seeds and endpoint
grids, authored-macro routing, four regional recipes with incision caps, and
lake/dry-basin authoring. Water review retains captured MFD area, checks exact
flats, finer shorelines, full external routes and internal wet/dry paths, then
transfers only eligible area. See [current research status](../research/status.md)
for evidence and limits, and [ADR-0043](../adr/0043-review-dry-collection-paths.md)
for the latest accepted water behavior.

1. Reduce measured repeated water-network work in Python, preserving every
   probe, budget decision, Float32 result and failed-link record. Compare whole
   generations and controls, not only a faster isolated helper.
2. Measure sampling convergence for procedural relief, regional transitions and
   authored context tails. Define controlling-sill/storage assumptions before
   introducing explicit lake chains with compatible levels and acyclic flow.
3. Compare retention, constrained breach and reroute proposals using full paths,
   cut depth/length and preserved anchors, then expose reviewable river networks.
4. Extend point-anchored ridge/valley profiles with direct per-vertex controls,
   explicit passes and asymmetric sides.
5. Add regional drainage-density/runoff controls, then selected-region refinement
   with explicit parent and halo contracts.

R04/R05 provide the first drainage correctness slice and review products;
[ADR-0029](../adr/0029-route-drainage-over-authored-terrain.md) records its limits.
Measure representative fixtures with each feature. A solver replacement,
Rust rewrite, additional export infrastructure or global climate model is not
a prerequisite for these next landform improvements. World placement moves
forward when integration or regional/climate coordinates require it.

## Engineering checkpoint

The [2026-09-13 documentation audit](../maintenance/2026-09-13-documentation-and-research-status.md)
reconciles current contracts with the backlog. The earlier
[2026-09-10 review](../maintenance/2026-09-10-sanity-and-performance.md) identified
native coast-distance cost and large generation/UI modules. The later
[dry-path measurements](../research/2026-09-11-dry-collection-paths.md) add a
substantial repeated planning/sampling cost on connected-water scenes. Earlier
coast-only profiles do not describe that enlarged workload.

Measure unchanged inputs before optimizing. Prefer bounded reuse of exact
geometry and field evaluations; retain full evidence and conservation checks.
The [earlier STRtree probe](../research/2026-09-05-selective-terrain-sampling.md)
was slower on the simple coast, so do not adopt an index without a demonstrated
crossover. Keep process spacing and terrain budgets unchanged for an exact-output
optimization. Separate profile preparation and workbench interaction modules as
their next feature changes require, without a broad architecture rewrite.

## Remaining work by dependency

### 1. Make terrain builds durable and reproducible

The first local build slice is implemented: headless project builds preserve
numeric NPY arrays, local-metric GeoTIFF, both previews, spatial diagnostics and
a versioned manifest. The [GeoTIFF adapter](../terrain-geotiff.md) now handles
point registration and embedded masks without assigning a world position.
See the [build guide](../terrain-builds.md). It records the existing endpoint
grid and explicitly leaves world CRS/planetary radius unspecified; the steps
below still govern georeferenced output.
The [coordinate contract](../terrain-coordinates.md) now centralizes source/local
conversion, endpoint registration and spacing across generation and products.
It preserves current numeric results without assigning a world position.
The [seed contract](../terrain-seeds.md) provides portable named stage seeds
for all generation. Only the current project/build format is supported.
Future stochastic stages must get their own stable identifiers.

- Define source-world origin, planetary model and working projection before freezing georeferenced
  outputs. The current longest-dimension local plane is not a world CRS contract.
- Add world placement to the implemented local-metric Float32 GeoTIFF export.
- Extend the existing build manifest only when a new product needs additional
  provenance. Local numeric export, headless builds, hashes, stage identities,
  units and runtime recording are complete.

Rasterio now writes the local GeoTIFF. Evaluate pyproj for source/world
coordinate operations and GDAL command-line tools for additional interoperability
checks when declaring planetary placement.

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
- Extend current point-anchored ridge/valley profiles to per-vertex authoring,
  explicit passes and asymmetric sides. The first four regional recipes are
  implemented; distribution targets and coupled/geological regions remain open.
- Reproject hard constraints after every optional process stage and report soft
  residuals rather than silently changing authored intent.

### 4. Finish hydrology semantics and validation

- Extend implemented lake/dry-basin intent and sampled outlet transfer with
  sill/storage semantics, lake chains and nested depression policy. Numeric
  drainage/basin archives exist; river/catchment vectors and physical flow
  validation remain open.
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

For that future prototype, evaluate a transparent NumPy/SciPy process model. Smith-Barstad-style linear
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

This is an adoption plan, not a list of installed engines. NumPy and Rasterio
are runtime dependencies; SciPy, Landlab and Numba are not installed in the
environment checked on 2026-09-13. The [dependency register](../DEPENDENCIES.md)
owns adopted packages. External support/license findings remain dated evidence
and require a fresh check before a prototype or adoption.

| Area | Recommendation now | Evidence gate before adoption |
|---|---|---|
| Numeric core | Keep NumPy; spike SciPy locally | Fixture improvements and deterministic tolerances |
| DEM exchange | Rasterio local GeoTIFF; defer pyproj to world placement | Round-trip tests and GDAL interoperability |
| Hydrology comparison | Landlab, then external GRASS | Routing and basin fixture agreement |
| Large multidimensional data | Defer xarray/Zarr | Measured climate or partial-I/O requirement |
| Climate prototype | Transparent NumPy/SciPy fields | Earth analog fixtures and energy/water sanity checks |
| Full climate model | External ExoPlaSim experiment only | Reproducible workflow and useful validation signal |
| Classifications | Versioned in-project rules | Published definitions, edge fixtures, and uncertainty |

## Revisit points

The [landform-diversity research](../research/2026-09-04-terrain-realism-and-landform-diversity.md)
adds the R01–R33 candidate register in the roadmap without promoting research
engines to dependencies. The first regional recipes and authored-macro routing are implemented.
Remaining comparisons concern regional transition gradients, complete final-field
drainage, sediment-aware valleys and multiscale refinement. Measure final-surface drainage after
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
