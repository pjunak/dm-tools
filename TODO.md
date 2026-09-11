# Terrain tool roadmap

This is the working backlog for the deterministic terrain tool. It collects the
possibilities identified during the initial research and implementation without
treating every idea as an accepted design. Items marked **Research** need a
small prototype or architecture decision before they become implementation
commitments.

The [current development strategy](docs/strategy/README.md) is the authoritative
dependency-aware execution order. The sections below are grouped by product
area; their visual order is not a promise that every feature precedes algorithm
or UI work.

Priority labels:

- **P0** — next foundation or prerequisite;
- **P1** — high-value work after the relevant P0 contract exists;
- **P2** — useful later extension; and
- **Research** — compare approaches and validate with small synthetic terrain
  before selecting one.

The current baseline already includes deterministic coordinate-addressed
detail, dissolved multipart SVG land geometry, absolute and relative
brush/point/line constraints, per-tool settings, project save/open, colour
preview, and PNG export. Those are not repeated below as unfinished work.

## Features

### Durable data and output products

- [x] **P0 — Define the versioned build manifest.** Record project and input
  hashes, generator and schema versions, master and stage seeds, effective
  parameters, working extent and units, runtime/dependency versions, warnings,
  and authoritative output hashes.
  Current version-16 builds record named stage seeds, numeric product hashes,
  and explicit local-only NPY/GeoTIFF coordinates. World placement remains open.
- [x] **P0 — Export the authoritative Float32 DEM as local-metric GeoTIFF.**
  Implemented point registration, metre units, NaN nodata, embedded masks,
  numeric-source hashes and manifest linkage. See the
  [export contract](docs/terrain-geotiff.md).
- [ ] **P1 — Verify local GeoTIFF import in desktop GIS and standalone GDAL.**
  Rasterio numeric reads and Pillow TIFF-tag checks pass. Desktop display is
  unverified; Rasterio 1.5.1 `rio info` assumes an Earth-coordinate conversion
  and fails for the current engineering CRS.
- [ ] **P0 — Add explicit source-to-world placement and projected export.**
  Declare the planetary model, source correspondence and metric working
  projection; validate distortion and coordinate round trips. Local TIFF
  coordinates do not yet place a continent on a world map.
- [x] **P1 — Add a non-interactive build command.** Let
  `dmtools terrain build <project.dmterrain.json>` use the same domain,
  pipeline, and adapters as the desktop workbench.
  Implemented with required `--output NEW_DIRECTORY`, lossless NPY arrays,
  both existing preview styles, diagnostics and completion-last publication.
- [ ] **P1 — Derive contour vectors from a completed DEM.** Make interval,
  index-contour cadence, smoothing, and minimum feature size explicit; identify
  the source DEM in metadata.
- [ ] **P1 — Export hillshade and reusable elevation-colour images separately.**
  Keep both derived from the numeric DEM rather than from one another.
- [ ] **P2 — Export meshes and additional GIS vector products.** Possible
  outputs include drainage lines, catchments, ridgelines, slope classes, and
  local-relief layers.

### Authored geography

- [ ] **P0 — Add an explicit pass/saddle constraint.** Give it a location,
  elevation mode, saddle elevation or relative depth, influence along the
  parent ridge, and optional preferred crossing direction.
- [ ] **P0 — Give ridge and valley lines per-vertex profiles.** Vertices should
  optionally carry elevation, relative relief/depth, width, and transition
  length instead of forcing one value onto an entire structure.
- [ ] **P1 — Add asymmetric structure sides.** Let the two sides of a ridge,
  escarpment, or valley use different widths, steepness, and profile shapes.
- [ ] **P1 — Add divides, rivers, faults, escarpments, and general breaklines.**
  Define the semantics of each constraint before extending the project schema;
  a drawn line must not imply more geological certainty than the user supplied.
- [x] **P1 — Add first terrain-character regions.** Polygon authoring,
  plain/hills/plateau/mountain recipes, base height, local relief, feature size,
  orientation and inward transitions now feed both terrain and routing.
  See [the region guide](docs/terrain-regions.md) and ADR-0030.
- [x] **P1 — Bound automatic incision by regional relief.** Plains and
  plateau interiors now receive smaller budgets with the same regional
  transitions. Floor/steepness corrections respect those limits; numeric builds
  retain the effective limits and exact authored anchors remain authoritative.
  See [ADR-0031](docs/adr/0031-bound-incision-by-regional-relief.md).
- [x] **P1 — Classify channels blocked by regional cutting limits.** Retained
  edge evidence reports depression contact, remaining-cut deficits, final
  adjustment and regional transitions. Counts overlap; they are not causes.
  Read-only diagnostics now have their own module. See
  [ADR-0032](docs/adr/0032-classify-channel-conflicts.md).
- [x] **P1 — Map depression extents and spill/outlet candidates.** A shared
  257-node routing/review grid replaces the coarse separate inventory. Numeric
  labels, conditioned receivers, representative exit/spill/terminal records and
  exterior/enclosed boundary context support the workbench and four-panel review.
  See [ADR-0033](docs/adr/0033-map-basin-spill-candidates.md).
- [x] **P1 — Author lake levels, outlets and dry-basin footprints.** Polygon
  authoring, saved lake controls, automatic-cut retention, separate water/ground
  exports and shoreline/anchor/outflow review are implemented. See
  [ADR-0034](docs/adr/0034-author-lakes-and-dry-basins.md).
- [x] **P1 — Terminate planned flow inside authored basin footprints.**
  Canonical footprint nodes now absorb both D8 and MFD flow; contributing area
  is conserved and exported per intent; eligible outlet transfer follows below. See
  [ADR-0035](docs/adr/0035-retain-basin-flow-and-assess-outlets.md).
- [x] **P1 — Assess candidate downstream lake outlets on finished ground.**
  Review nearest outward attachments, whole candidate paths, uphill steps,
  basin re-entry, vector coastline gaps, cycles and terminal boundary context.
  Export sampled path evidence; a clear result does not activate flow.
- [x] **P1 — Connect eligible lake outlets and transfer retained area.**
  Finished-ground routes now carry captured MFD area from connected lake water
  and dry nodes that drain into it. Extra shoreline openings and invalid routes
  block connection; isolated pockets stay retained. Shared path segments add
  area once per source, and full terminal accounting is checked. See
  [ADR-0036](docs/adr/0036-connect-lake-outflow-with-area-transfer.md).
- [x] **P1 — Show collected and retained basin nodes.** The workbench and
  finished-ground review now map collected water, collected dry ground and
  retained nodes. Build v16 exports the classification and retained contribution
  at each footprint node; sample counts and area accounting remain distinct.
  Exact outlet ground minus water level is reported, including submerged outlets,
  without treating a clear sampled route as proof of a stable lake level. See
  [ADR-0037](docs/adr/0037-expose-basin-catchment-outcomes.md).
- [x] **P1 — Route internal flats with known exits.** Integer ranks now route
  exact flats without editing the DEM. Every link is vector-contained, real
  downhill alternatives take precedence, and paths to closed pits stay retained.
  Build v16 exports internal receivers and ranks; details separate resolved flat
  donors from those reaching lake water. The public flat-outlet fixture covers
  both outcomes. See [ADR-0038](docs/adr/0038-route-basin-flats-with-integer-gradients.md)
  and the [measured rundown](docs/research/2026-09-11-basin-flat-routing.md).
- [x] **P1 — Check shorelines and outlet contact between canonical nodes.**
  Bounded profiles now sample every boundary corner and the water/outlet/first
  attachment connection. Low boundary openings and above-water connection ground
  block transfer; exports retain positions/heights and the review marks failures.
  The public shoreline-gap fixture catches a real narrow opening missed by the
  coarse review. See [ADR-0039](docs/adr/0039-sample-shorelines-and-outlet-connections.md)
  and the [measured rundown](docs/research/2026-09-11-finer-water-connections.md).
- [x] **P1 — Target narrow authored cores and crossings.** Local intervals now
  refine to the evaluator's narrowest core radius, preserve every baseline probe,
  merge overlaps and reject excessive plans before evaluation. The public
  narrow-shoreline-gap fixture detects a 200 m influence missed by the fixed
  3.90625 km profile; ground and incoming flow stay unchanged. See
  [ADR-0040](docs/adr/0040-refine-water-profiles-around-authored-features.md) and
  the [measured rundown](docs/research/2026-09-11-feature-guided-water-sampling.md).
- [x] **P1 — Review complete downstream outlet profiles.** External candidate
  paths now receive bounded feature-guided Float32 profiles, canonical vertex
  mappings and cumulative uphill evidence. Unresolved profiles block transfer;
  details and red crest markers explain the result. A public 100 m point fixture
  catches a 43.85 m climb missed by canonical nodes without changing its DEM.
  See [ADR-0041](docs/adr/0041-review-complete-downstream-outlet-profiles.md) and
  the [measured rundown](docs/research/2026-09-11-downstream-outlet-profiles.md).
- [x] **P1 — Complete internal wet-link evidence.** Batched feature-guided
  checks now remove links with above-water ground, preserving alternate wet paths.
  All wet nodes must reach the unchanged selected contact; separated pools and
  excessive whole-lake sample budgets retain captured area. Builds retain each
  candidate link's maximum, location and sample provenance; the review marks
  barriers. See [ADR-0042](docs/adr/0042-review-internal-water-links.md) and the
  [measured rundown](docs/research/2026-09-11-internal-water-links.md).
- [x] **P1 — Check dry collection links between canonical nodes.** Batched
  profiles now reject dry-to-dry, dry-to-water and exact-flat climbs before
  routing; clear alternatives and lower closed pits remain eligible. Complete
  chosen paths also check cumulative rises before collecting area. Build v16
  exports per-link evidence and path excursions. A public narrow point catches
  a 131.44 m climb and reroutes without changing ground. See
  [ADR-0043](docs/adr/0043-review-dry-collection-paths.md) and the
  [measured rundown](docs/research/2026-09-11-dry-collection-paths.md).
- [ ] **Research — Compare path-aware alternatives after a cumulative rejection.**
  Local blocked links already admit other descents and flat exits. A composed
  path exceeding tolerance retains that donor and its upstream paths; it does
  not search different downstream choices. Compare bounded state-aware methods
  without favouring lake exits over closed pits or perturbing the DEM.
- [ ] **P1 — Reduce repeated network profile planning and evidence overhead.**
  Measure shared endpoint/interior evaluations, indexed feature candidates and
  compact diagnostics before optimizing. Preserve Float32 identity, all required
  probes, complete budget decisions and reviewable failed links.
- [ ] **P1 — Measure broader feature and project-scale sampling limits.** Add
  regional transitions, procedural extrema and overlapping/context-tail cases;
  compare local extrema and decisions across refinement levels. Current core
  corridors and radius/4 spacing are bounded review choices, not error bounds.
  Measure complex many-lake projects and total profile/export cost before adding
  a spatial index, shared-path reuse, a project-wide budget, or larger per-profile
  limits; preserve exact field evaluation and deterministic evidence when reusing work.
- [ ] **P1 — Define controlling sills and physical lake-level assumptions.**
  The exact outlet height and sampled connection maximum are now visible. Derive
  the controlling opening/crest across relevant paths and define inflow, storage
  and boundary assumptions before claiming stable levels. Do not drain isolated
  pockets solely because they share an authored polygon.
- [ ] **P1 — Connect explicit lake chains.** Require compatible water levels,
  reviewed incoming/outgoing paths and acyclic basin dependencies; keep closed
  and dry basins terminal. Current outlet paths reject every intervening basin.
- [ ] **P1 — Reconcile blocked channels through explicit water/outlet choices.**
  The plain fixture has 253 uphill edges; all exceed remaining receiver cut
  and 234 touch depressions. Spill candidates and exterior/enclosed raster
  boundaries are mapped, and lake/dry-basin intent now protects authored areas.
  Closed basins retain flow and eligible outlets now transfer captured area.
  Classify ocean boundaries and compare full paths before applying
  constrained breaches or rerouting. Measure full route depth/length,
  anchor preservation and downstream closure; never silently expand budgets.
- [ ] **P1 — Extend regional process controls.** Add drainage density,
  runoff and erosion resistance with measurable effects and authored authority.
- [x] **P1 — Render drainage review at display size.** Thin canonical D8
  segments replace enlarged cell blocks. Routing accuracy is unchanged;
  gridded/coast-parallel paths still need hydrology and river-geometry work.
- [x] **P1 — Support adjacent mainland sections and disconnected islands.** SVG
  land objects are dissolved into one polygonal mask, sub-sampling border
  slivers are repaired, and all components share one metric field and seed.
- [ ] **P1 — Classify SVG water holes and ocean boundaries.** Declare ocean
  levels and enclosed-water semantics. Authored lake/dry-basin footprints are
  implemented; an enclosed SVG gap still has no inferred lake level or intent.
- [ ] **P2 — Edit basin vertices and outlets after drawing.** Add selection,
  vertex movement and outlet relocation; current area authoring uses undo/redraw
  and the first vertex as an optional outlet.
- [ ] **P2 — Refine retention boundaries and shoreline products.** Measure
  slopes where automatic incision resumes outside protected areas; soften the
  exterior transition if needed while preserving zero cuts inside. Derive
  vector shorelines and higher-resolution containment checks from numeric water.
  Test narrow footprint fingers and crossings between canonical nodes; sampled
  retention alone cannot resolve every authored polygon feature. Compare refined
  2D wet components and narrow off-grid water passages against canonical D8 links
  before treating sampled disconnection as a complete shoreline model.
- [ ] **P2 — Add reusable terrain profiles/presets.** Profiles should be
  versioned authored inputs with their own content hashes and should expose the
  effective values used by a build.

### Scale hierarchy and portability

- [ ] **P0 — Define regional refinement requests in world coordinates.** A
  local build must name its parent build, bounds, requested sample spacing, and
  buffered halo.
- [ ] **P0 — Define the parent/child consistency test.** Downsampling a refined
  region must reproduce the parent within a documented numeric tolerance while
  the added frequency bands contribute only new detail.
- [ ] **P1 — Build only a selected region at higher resolution.** Avoid
  allocating a planet- or continent-sized raster when the user needs one local
  map.
- [ ] **P2 — Evaluate a portable project bundle.** A bundle could package the
  JSON and authored source assets while retaining readable hashes; plain JSON
  plus relative files remains the default until portability justifies it.
- [ ] **P2 — Expose the engine through a hosted interface.** Keep local use
  complete and put job management, limits, authentication, and storage outside
  the deterministic engine.
- [ ] **P1 — Select a public project license before distribution.** Recheck the
  licenses and distribution implications of every optional scientific engine
  included in a hosted or downloadable build.

### World climate, ecology, and environmental zones (deferred)

These are backlog entries only. Do not begin implementation until the durable
terrain-output and regional-refinement contracts needed by the
[current strategy](docs/strategy/README.md) are proven.

- [ ] **Research — Define the global climate input and output contract.** Inputs
  should include the fixed world projection and latitude, ocean/land mask,
  accepted DEM, orbital and rotational assumptions, circulation or prevailing
  winds, and authored overrides. Outputs should be continuous monthly or
  seasonal fields with units, provenance, diagnostics, and uncertainty.
- [ ] **P2 — Prototype deterministic continuous climate fields.** Generate
  temperature, seasonal range, precipitation, coastal moderation,
  continentality, orographic precipitation and rain shadow, potential
  evapotranspiration, aridity, and runoff before assigning named zones.
- [ ] **P2 — Add versioned climate-zone classification views.** Derive familiar
  Köppen–Geiger-like and ecological Holdridge-like views from the continuous
  fields; keep thresholds and classification-version metadata explicit.
- [ ] **P2 — Generate biome suitability and display classes.** Use climate,
  elevation, growing season, slope, aspect, terrain wetness, substrate, and
  authored exceptions. Preserve fuzzy transitions or confidence instead of
  pretending every boundary is exact.
- [ ] **P2 — Generate separate, overlapping environmental layers.** Treat bogs
  and other wetlands as hydrology/ecosystem results, plains as landforms,
  tundra as a biome, and fields as cultural land use. Include additional
  grassland, forest, desert, marsh, fen, floodplain, alpine, and coastal types
  only within the layer whose semantics fit.
- [ ] **P2 — Preserve global-to-continent and refinement consistency.** Climate
  and ecology builds must share global boundary conditions while allowing
  continent and local resolution, authored corrections, rebuildable exports,
  and parent-build provenance.

## Algorithm and result improvements

The [2026-09-03 terrain algorithm research](docs/research/2026-09-03-terrain-algorithm-options.md)
recommends building the measurement harness first, then comparing local RBF and
sparse screened-Poisson correction fields, followed by drainage and optional
landscape-process spikes. It is working research, not an accepted architecture.

### Constraint-conditioned base surface

- [ ] **P0 — Create a quantitative terrain-quality fixture suite.** Include a
  range with two peaks and a pass, a branching mountain system, a high-altitude
  valley, a broad lowland river valley, an escarpment, and a parent/child
  refinement window. Record expected invariants rather than subjective image
  snapshots alone. The two-peak/one-pass ridge, connected-structure junction,
  and authored branch-root fixtures are complete; full branch topology and
  statistics and the other landform fixtures remain.
- [ ] **Research — Compare surface solvers for the low-frequency base.** Test
  the current smooth-response model against feature-curve diffusion/Poisson
  solving, radial-basis interpolation, and hydrologically conditioned
  interpolation. Compare constraint error, slope continuity, runtime, and
  nested-resolution behavior before replacing the current model. The first
  spike should compare deterministic local RBF and sparse screened-Poisson
  correction stages; use ANUDEM as a behavior and diagnostic reference rather
  than attempting a full clone.
- [ ] **P0 — Separate hard constraints, soft guidance, and inequalities in the
  solver contract.** Exact spot heights and water levels must remain exact;
  ridge minima, valley maxima, relative displacement, and brush guidance should
  retain their different meanings.
- [ ] **P1 — Make transitions aware of surrounding terrain.** Estimate the
  stable low-frequency reference surface entering a stage, then adapt shoulder
  reach and blending to local slope and relief without using an order-dependent
  moving neighbourhood.
- [ ] **P1 — Add terrain-character-aware residual detail.** Control spectral
  slope, anisotropy, roughness, and amplitude by region so plains, plateaus,
  rolling hills, and mountain belts do not share one texture.
- [ ] **P1 — Preserve authored constraints after every optional process stage.**
  Reproject or solve back to hard constraints after erosion/diffusion and report
  the remaining residual for soft constraints.

### Mountain systems, ridges, and passes

- [x] **P0 — Solve a continuous longitudinal ridge profile.** Interpolate
  authored peaks and passes along arc length, enforce minimum crests where
  requested, and avoid circular point stamps or abrupt changes at vertices.
  Absolute point anchors on absolute structures now use a shape-preserving
  cubic profile with controlled shoulders.
- [ ] **P0 — Generalize passes beyond absolute structure anchors.** An attached
  absolute point now forms a validated geometric saddle, lower along the ridge
  and higher across it. Relative points now shape the relief/depth profile of
  the uniquely nearest relative ridge or valley. Explicit crossing direction,
  mixed-mode attachment, and the dedicated pass constraint remain.
- [ ] **P1 — Vary ridge width and cross-section continuously.** Support broad
  old ranges, narrow alpine crests, rounded ridges, sharp crests, asymmetric
  escarpments, and smooth transitions between authored vertex values.
- [ ] **P1 — Add hierarchical ridge branching.** Generate secondary ridges and
  spurs from an authored main divide with deterministic branch identity,
  decreasing scale, plausible junction angles, and no isolated mountain blobs.
  Authored compatible ridge and valley segments now retain full width where
  their endpoints join; explicit parent/child topology and generated branches
  remain.
- [ ] **P1 — Correlate detail along and across structures differently.** Use
  anisotropic fields so ridge grain follows the range rather than cutting across
  it as isotropic noise.
- [ ] **P2 — Add optional geological provinces and uplift fields.** Use faults,
  plate-boundary-like guides, domes, basins, or directional compression as
  simplified causes of broad relief; label the result process-informed rather
  than tectonically simulated unless a stronger model is implemented.
- [ ] **Research — Evaluate diffusion-based feature-curve terrain fitting.**
  The approach in the feature-based terrain research may provide smoother
  networks and explicit slope control, but must be tested for determinism,
  coastline boundaries, exact anchors, and regional refinement. Start with a
  regular-grid sparse solve and postpone multigrid until measurements justify
  the added implementation complexity.

### Valleys, rivers, and hydrology

- [x] **P0 — Give valleys a downstream longitudinal profile.** Enforce
  non-increasing flow toward an outlet except where an authored lake or basin
  permits otherwise; let high-terrain valleys remain high while retaining
  relative incision. Valleys are now ordered head-to-outlet and use a stable
  pre-valley metric reference profile plus downstream-only floor correction. Authored
  lake and basin exceptions remain part of the explicit-water work.
- [ ] **P1 — Add variable valley cross-sections.** Support narrow V-shaped
  valleys, glacial U-shaped valleys, broad floodplains, terraces, and smooth
  width/depth changes along a line. Generated fluvial valleys now widen and
  smooth downstream with drainage hierarchy. A high-order, low-weight MFD
  convergence correction now reduces D8 cross-section gaps without cutting
  across a synthetic drainage divide. The generated D8 tree now carries
  Horton-Strahler order, but measured regressions rejected using it as a direct
  width or depth control without valley character or confinement; authored
  per-vertex shape, glacial forms, floodplains, and terraces remain.
- [ ] **P0 — Derive drainage direction and flow accumulation.** Define the
  depression fill/breach policy, flat handling, edge outlets, and sea
  connectivity before promising hydrologically valid rivers. Prototype MFD for
  continuous accumulation and D8 for unique catchment trees; include rotated
  fixtures so grid-direction bias is measurable. A fixed canonical-grid
  Priority-Flood + MFD accumulation stage now drives automatic broad valleys,
  with a rotated fixture, and a complementary D8 tree supplies unique generated
  centrelines. A bounded area-slope channel-head rule now starts steep
  headwaters earlier, preserves large gentle rivers, and closes every selected
  path downstream. Generated floors are now conditioned after residual-detail
  restoration with bounded downstream-only cuts; the aligned Tharkeniss network
  improves. Extreme generated knickpoints now receive a second bounded
  normalized-steepness pass with explicit unresolved diagnostics, while the
  coarser completed-surface diagnostic documents remaining scale aliasing.
  Horton-Strahler order now records equal-tributary hierarchy without changing
  the DEM. Public drainage products, authored depression policy, basin labels,
  and user-facing drainage-density profiles remain.
- [ ] **P1 — Reconcile authored rivers with generated drainage.** Rivers should
  descend to a valid outlet and occupy a local valley; report conflicts rather
  than silently moving an authored route.
- [ ] **P1 — Validate basins, outlets, and drainage connectivity.** Detect
  unintended inland sinks, uphill river segments, disconnected channels, and
  coastline outlets that fail to reach sea level. A resolution-independent
  257-node shared routing/review grid reports strict-D8 boundary connectivity,
  potential sinks, fill depth/volume and largest catchment without changing terrain.
  Significant fill components now retain extent labels and representative
  exit/spill/terminal routes, plus raster exterior/enclosed-water boundary context. Authored basin classification, a full nested depression
  hierarchy, river-segment checks, and local refinement diagnostics remain.
- [ ] **Research — Compare a mature hydrology adapter with selected in-project
  primitives.** Candidates already considered include ANUDEM-style
  hydrological conditioning and established GIS flow/depression tooling. Keep
  optional engines behind adapters and measure Python 3.14/platform support,
  determinism, license implications, and refinement behavior. Landlab is the
  strongest Python 3.14 experiment adapter found; GRASS and Whitebox remain
  external comparison tools with explicit license/version boundaries.

### Landscape processes and validation

- [ ] **Research — Prototype deterministic hydraulic or stream-power erosion.**
  Start with a small post-process that respects fixed coastline and elevation
  anchors; reject it if it merely adds noisy gullies or makes results
  resolution-dependent. Prefer stream-power incision plus explicit flow
  routing over a visual particle or droplet erosion filter. The first bounded
  area-and-slope incision proxy is implemented for automatic broad valleys;
  time-stepped stream-power evolution and convergence testing remain research.
- [ ] **Research — Prototype thermal erosion/talus relaxation.** Use it only
  where material and slope assumptions are explicit, and verify that it does
  not erase authored passes, ridges, or valley floors.
- [ ] **P2 — Add simplified lithology/erosion-resistance fields.** Let rock
  resistance influence valley density, escarpment retention, and slope limits
  without pretending to reconstruct full geological history.
- [ ] **P1 — Add measurable result diagnostics.** Report constraint residuals,
  slope and curvature distributions, hypsometry, coastline correctness,
  drainage statistics, and the fraction of terrain clipped by elevation bounds.
  The first compact drainage summary now travels with generated terrain and PNG
  metadata. Internal generated-channel results now also report total and
  steepness-only floor corrections, excessive normalized-steepness ratios, and
  unresolved uphill edges; public profile statistics and a durable build report
  remain.
- [ ] **P1 — Add explicit prominence and saddle analysis.** Keep this derived
  measurement separate from the current relative-relief controls.
- [x] **P0 — Record algorithm and stage identifiers in each build.** Record
  generator, noise, automatic-valley and diagnostic IDs plus source hashes.
  Deliberate improvements may change outputs; update identifiers and tests.
- [x] **P0 — Derive stable named seeds.** All generation uses
  `named-stage-sha256@1` with `terrain.relief` and `terrain.landforms`. Macro/full detail stay
  views of one relief field. Portable reference values and current generation
  checks exercise the [seed contract](docs/terrain-seeds.md).
- [x] **P0 — Remove early-development compatibility overhead.** Removed the
  original seed mode, policy selector, old-save loaders, four superseded
  schemas, duplicate example and dual-version tests. Only current project/build
  formats are supported. Keep obsolete code in Git history, not active support paths.
- [ ] **P1 — Generate refinement halos and crop final tiles.** Evaluate all
  neighbourhood-dependent solvers and erosion on buffered bounds to avoid
  seams, then verify overlap and downsample consistency numerically.
- [ ] **P0 — Profile memory and runtime by stage.** Establish repeatable draft,
  regional and maximum-resolution benchmarks with simple and complex coasts,
  authored constraints and multiple seeds. Separate generation, rendering,
  diagnostics, I/O, startup and peak memory; distinguish native calls from
  Python loops. The first public-example timing/profile is recorded in the
  [language assessment](docs/research/2026-09-05-language-and-performance.md);
  it is not yet a representative benchmark suite or memory measurement.
  A [repeatable harness](benchmarks/README.md) now covers five public/synthetic
  cases, selectable seeds/resolutions, generation stages, CPU time, quality,
  rendering, process peak memory and numerical hashes in isolated repetitions.
  The [2026-09-10 review](docs/maintenance/2026-09-10-sanity-and-performance.md)
  adds regional landforms, retained routing identities and CPU profiles.
  Export timing, regional-refinement/4096 cases, many-constraint stress tests
  and agreed latency/memory budgets remain.
- [ ] **P1 — Optimize measured boundary-distance cost.** Prototype indexed
  coast-segment distance queries on complex coasts before a native rewrite;
  the prior simple-coast STRtree probe was slower. Preserve exact masks,
  shared samples, numeric hashes and routing products. Compare simple coasts,
  islands, holes and many authored regions; retain peak memory evidence.
- [ ] **P1 — Reduce preview peak memory.** Profile full-raster RGB and
  hillshade temporaries, then compare tiled rendering with gradient halos and
  identical pixels/alpha/metadata. Measure 4096 separately before assuming
  full-resolution previews fit the intended desktop memory budget.
- [ ] **P1 — Split growing modules along the next feature boundaries.** Extract
  structure-profile preparation from generation and workbench controls/drawing
  as those features change. Basin/conflict diagnostics are now extracted;
  keep typed values and one owner per operation.

### Realism research register — 2026-09-04

These additions extend the existing region, hydrology, refinement, and
diagnostic items. They are possible improvements, not a commitment to implement
every process. `R01`–`R33` are stable references into the
[landform-diversity research](docs/research/2026-09-04-terrain-realism-and-landform-diversity.md),
which records primary sources, tool boundaries, and proposed experiments.
The [prototype-contract follow-up](docs/research/2026-09-04-terrain-prototype-contracts.md)
refines those items with local measurements and source audits, and adds
`R34`–`R39`. All IDs remain stable; source inspection is not runtime validation.
The [geological-composition follow-up](docs/research/2026-09-05-geological-structure-and-terrain-composition.md)
adds `R40`–`R44` and refines geological, graph and measurement requirements.
The [language and performance assessment](docs/research/2026-09-05-language-and-performance.md)
adds `R45`–`R47` and brings stage profiling forward before a language migration.
Priorities remain conditional on the current strategy's prerequisites.

#### Coordinate, scale, and drainage contracts

- [ ] **P0 — R01: Preserve source-world georeferencing.** Extend the local
  longest-dimension model with source origin, planetary model, projection and
  regional working CRS. Check ground-distance distortion and a world/region
  round trip. A metric label alone must not imply geographic accuracy.
  The [shared coordinate contract](docs/terrain-coordinates.md) now preserves
  source/local inverse conversion and explicit grid extents. World placement,
  planetary metadata and working-CRS declarations remain future project work.
- [ ] **P0 — R02: Expose effective process and diagnostic spacing.** Record the
  shared 257-sample routing/diagnostic grid in the build report;
  flag landforms too small to resolve. Define versioned process resolution
  independently of PNG pixels and test small-island/coastal-channel coverage.
  Local build manifests now expose actual routing, diagnostic and output grid
  spacing. Feature-resolution warnings and a public process-resolution control
  remain unfinished.
- [ ] **Research — R03: Define point samples versus cell averages.** Choose
  raster registration, integration/resampling, and anti-aliasing policy. Test
  coordinate round trips and parent restriction separately from existing
  bit-identical shared-point tests; do not silently weaken those tests.
  For endpoint-node grids test `2*(N-1)+1` refinement, not doubled node counts;
  shared-node equality does not imply equal coarse-cell averages.
  Endpoint registration, interval-based grid refinement, axis-specific spacing
  and current stage shape rounding now have a shared domain implementation and
  numerical tests. Cell averages, resampling and parent restriction remain open.
- [x] **P0 — R04: Route on currently authored macro geography.** Brush, ridge,
  point and prepared valley constraints now participate in canonical routing.
  Relative valley profiles use a stable pre-incision reference, with one
  planning pass and existing final constraint precedence. Explicit river/divide
  and water-level entities remain future work; see ADR-0029.
- [x] **P1 — R05: Retain inspectable drainage topology.** Builds retain source
  and filled routing DEMs, final-field samples, D8 receivers, MFD accumulation,
  stream order, channels, heads and outlets with coordinates, mask and hashes.
  Same-grid receiver differences and uphill edges are reported; the workbench
  overlay and headless review image expose planned channel conflicts.
- [ ] **P1 — Reconcile remaining planned/final channel conflicts.** Quantify
  hard-anchor conflicts separately from residual-detail and depression effects.
  Preserve authored intent; do not treat filled routes as validated rivers.
  The seed-42 authored benchmark currently reports 390 uphill edges among 2455
  planned channel edges (maximum rise 135.07 m); this is a baseline for future
  reconciliation, not hydrologic acceptance.
- [ ] **P1 — R06: Separate coastline height from coastal terrain character.**
  Compare regional coastal plains, steep mountain coasts, cliff approaches and
  plateau margins with the uniform exponential rise. Keep the authored shore
  fixed and test estuary/outlet continuity. Shelf/bathymetry work depends on R07.
- [ ] **Research — R07: Support below-sea-level terrain deliberately.** Separate
  land mask, bed elevation, water surface and sea datum before allowing dry
  inland depressions, overdeepened lake beds or bathymetry. Audit all zero
  clipping; test inland isolation, ocean connection and nodata semantics.

#### Regional composition and authoring

- [ ] **P1 — R08: Control regional height distributions.** Add soft targets for
  lowland fraction, plateau height, local relief and peak density to the
  terrain-character design. Compare equal-height-ceiling regions, and reject
  global histogram remapping that alters hard anchors or drainage.
- [ ] **Research — R09: Couple ridge and drainage skeletons.** Generate spurs
  between tributaries, preserve divides and saddle connections, and measure
  network crossings, orphan peaks, junction angles and branch scale. Extend
  existing hierarchical branching rather than creating a second ridge system.
  Preserve the distinct surface-ridge, divide, thalweg and channel meanings
  described by R42 rather than assuming the two skeletons are exact duals.
- [ ] **Research — R10: Add layered substrate to lithology regions.** Evaluate
  resistant caps, bed thickness, dip and differential erodibility for mesas,
  cuestas, escarpments and canyon walls. Distinguish geometry from decorative
  strata colours; keep weathered/mobile cover separate from bedrock.
  Prototype material-coordinate queries at the eroding bedrock surface. Check
  true versus vertical thickness, contact geometry and process-grid support;
  compare effective coarse resistance with resolved regional layers.
- [ ] **Research — R11: Represent regional process histories.** Compare a short
  authored sequence of uplift, incision, deposition and glacial episodes with
  one uniform erosion-age parameter. Record order, units and assumptions;
  label the history a design hypothesis rather than inferred canon.
  Compare a simple analytical event sequence with LoopStructural as an optional
  reference; distinguish reverse-time reconstruction from forward simulation.
- [ ] **Research — R12: Prototype contour-guided authoring.** Compare the 2026
  iso-contour approach for plateaus, basin margins and elevation bands. Reject
  crossing/contradictory contours and quantify DEM reconstruction, river-floor
  and hard-anchor errors. Exported contours remain derived products.
- [ ] **Research — R13: Prototype skeleton-preserving deformation.** Use the
  2025 vector-terrain work to assess moving/stretching a range while retaining
  internal structure. Preview changes, keep authoring editable, and measure
  geometry, drainage and reconstruction errors before accepting a deformation.

#### Erosion, deposition, and recognizable landforms

- [ ] **Research — R14: Compare analytical erosion with time stepping.** Use
  the 2024 analytical stream-power method as a bounded candidate for fast
  terrain-age control. Test uplift/base-level assumptions, convergence,
  authored anchors and runtime against the current incision baseline.
- [ ] **Research — R15: Evaluate multi-scale erosion amplification.** Compare
  the MIT 2024 reference implementation with current residual detail on one
  refined mountain/valley window. Preserve parent restrictions, inherited
  upstream inflow and boundary gradients; include deposition and seam checks.
  Verify actual OpenGL/GLSL requirements, numeric export normalization,
  finite shader outputs and fixed-step operation before judging its images.
- [ ] **Research — R16: Prototype bedrock plus mobile sediment.** Start with a
  Landlab SPACE comparison on a channel opening onto a plain. Track erosion,
  storage, deposition and export; verify nonnegative cover and bounded balance
  error before adding floodplain or alluvial-fan presets.
  The audited large-scale SPACE component needs single-receiver routing;
  start with a D8 reference, explicit discharge units, porosity/control-volume
  accounting and explicit flooded-node behavior rather than passing MFD data.
- [ ] **Research — R17: Evaluate 2026 stochastic geomorphological transport.**
  Compare resolved regional meanders/fans with a stream-power baseline.
  Distinguish MIT `geotransport` reference code from LGPL/CUDA `soillib`;
  verify Windows/Python runtime, seed ensembles, GPU repeatability, transport
  conservation and resolution behavior before proposing adoption.
  Measure floating-point atomic-reduction variance independently of seed
  repeatability; package metadata alone does not prove runtime compatibility.
- [ ] **Research — R18: Separate catchment trees from channel regimes.** Define
  confined bedrock, alluvial, meandering, braided and delta/distributary
  networks. Relate width to discharge/material/confinement, not Strahler order
  alone. Test connectivity, split/join flux and source-DEM consistency.
- [ ] **Research — R19: Generate terraces from explicit events.** Compare
  base-level or uplift episodes with authored terrace benches. Require ordered
  levels, coherent valley continuity and a valid modern outlet; do not terrace
  the entire elevation field by quantization.
- [ ] **Research — R20: Add glacial landform options.** Compare a bounded
  authored U-valley/cirque recipe with the 2023 glacial-erosion reference.
  Include hanging valleys and overdeepened basins only with explicit former
  ice context, water semantics, and sufficient regional resolution.
- [ ] **Research — R21: Add mass-wasting and debris-flow options.** Evaluate
  the 2024 debris-flow work for scars, scree aprons and cones. Verify material
  movement, authored crest/pass preservation and downstream blockage after
  deposition; compare with the existing thermal-relaxation proposal.
- [ ] **Research — R22: Add wind-shaped terrain selectively.** Use the 2024
  wind/sand study to compare dune and lee-deposit recipes or simulations.
  Require wind direction/variability, sand availability and world-unit scale;
  test boundary flux and avoid treating all deserts as sand seas.
- [ ] **Research — R23: Add authored volcanic and impact families.** Evaluate
  cones, shields, calderas, lava plateaus and impact rims as distinct recipes
  with optional weathering. Validate radial profiles, rim continuity,
  surrounding transitions and coast preservation; no automatic canon changes.
- [ ] **Research — R24: Define karst and subsurface-drainage exceptions.** Allow
  authored sinkholes, losing streams and spring connections in suitable
  substrate. Test a routed underground connection without carving a surface
  outlet. Caves and overhangs need a separate representation from the DEM.

#### Comparison tools, rendering, and scientific limits

- [ ] **P1 — R25: Build an Earth-analogue descriptor atlas.** Use small,
  provenance-recorded USGS 3DEP and optional Copernicus samples at matched
  extent/resolution. Compare relief, curvature, hypsometry, prominence,
  directional spectrum and drainage; use terrain-descriptors/GRASS as
  references. Separate DSM vegetation/buildings from desired terrain texture.
- [ ] **Research — R26: Compare example-based residual synthesis.** Transfer
  selected terrain character from reference patches after fitting broad relief
  and boundaries to authored geography. Measure repeated motifs, seams,
  constraint errors and drainage changes; retain source data rights/hashes.
- [ ] **P1 — R27: Add a reproducible candidate comparison gallery.** Extend the
  existing seed/before-after view with fixed-seed ensembles, region descriptors
  and multiple valid alternatives. Keep visual interest separate from hard
  validity; adoption is an explicit author choice, not one opaque quality score.
- [ ] **P1 — R28: Compare multiscale and multidirectional relief rendering.**
  Use GDAL hillshade variants and coarse/fine shading at the same DEM and fixed
  elevation colours. Record exaggeration; test rotated ranges, flat areas and
  coasts. Material/snow overlays require their own fields or authored inputs.
- [ ] **Research — R29: Evaluate learned terrain as proposals only.** Compare
  MESA and PlanetDiffusion for regional inspiration or global-context research.
  Audit code/weights/data separately, pin the environment and sample settings,
  preserve the custom planet scale, and validate height/drainage/refinement
  after conditioning. Do not replace the local deterministic authoring core.
- [ ] **Research — R30: Define a bounded external-tool comparison adapter.**
  Assess Houdini, Gaea, World Machine, World Creator and HighMap only where
  useful. Exchange numeric heights, extent, datum, masks and settings; detect
  normalization or coast movement. Verify exact component license, automation
  rights and runtime; pyHighMap currently documents Linux-only support.
- [ ] **Research — R31: Benchmark GPU routing/process backends after profiling.**
  Compare FastFlow, compute-shader and CUDA candidates only for a demonstrated
  bottleneck. Record hardware, drivers, precision and repeat-run variance;
  retain an inspectable CPU reference and distinguish numeric tolerances from
  bitwise reproducibility.
- [ ] **P0 — R32: Audit constraint, process and refinement corrections together.**
  Extend the measurement harness with per-stage deltas and material accounting.
  Recheck drainage after hard-height restoration or parent restriction, and
  report incompatible requirements. Separate intentional basins from numeric
  sinks and canonical-grid checks from exported-surface checks.
- [ ] **Research — R33: Weight runoff before assigning river size.** Define an
  optional authored runoff field and future climate-derived discharge adapter.
  Keep contributing area distinct from water flux. Test wet/dry catchments of
  equal size, seasonal assumptions and upstream boundary flux; full climate
  generation remains deferred under the existing strategy.

#### Prototype findings and additional improvement candidates

- [ ] **Research — R34: Stabilize amplitudes when adding detail bands.** Compare
  fixed versioned band budgets with the current normalized sum. A local default
  2-to-6-band probe reduces existing band coefficients by 28.26%; this is a
  setting-change effect, not broken shared-coordinate determinism. Measure
  coarse power and parent restriction after nonlinear mapping and processes;
  preserve old presets and algorithm identifiers.
- [ ] **Research — R35: Constrain regional transition gradients.** Match
  province reference levels and budget the extra slope from blending surfaces
  at different heights. Measure slope/curvature across flat, plateau and
  mountain boundaries; smooth blend weights alone do not prevent escarpments.
- [ ] **Research — R36: Stabilize oriented-detail reference fields.** Compare
  ridge-axis and directed-flow orientation, define low-slope confidence and
  fallback, and test saddles, crest reversals and phase seams. Keep the
  reference field independent of preview resolution and tile boundaries.
- [ ] **Research — R37: Gate processes by landform suitability.** Combine
  authored landform, slope/relief, substrate and confinement to select detail
  recipes. The controlled-pattern paper is a mountain-detail candidate with
  explicit plateau/cliff/floodplain limitations. Test masks and transitions;
  expose uncertainty and keep alternate valley/plateau recipes available.
- [ ] **Research — R38: Prove external numeric exchange before comparisons.**
  Round-trip an asymmetric signed metre ramp with nodata, unequal axis spacing
  and explicit registration. Detect normalization, quantization, transposition
  and half-cell shifts. Record engine commit, settings, step counts, scale,
  offset and output identity; visual exports alone cannot validate elevation.
- [ ] **Research — R39: Compare focused meander and delta references.** Evaluate
  Apache-2.0 meanderpy against a bounded authored corridor, and MIT pyDeltaRCM
  against a distributary recipe. Check cutoff semantics, valley confinement,
  inlet/outlet continuity, sediment flux and domain boundaries. Audit material
  assumptions and runtime support; keep coast/river changes reviewable.

#### Geological composition and structural measurements — 2026-09-05

- [ ] **Research — R40: Compose related terrain regions.** Add optional,
  editable relationships between belts, plateau margins, basins, valley
  corridors and receiving plains. Compare coherent recipes with independent
  regional textures; measure cross-sections, transitions and outlet alignment.
  Surface conflicts with authored geography instead of silently relocating it.
- [ ] **Research — R41: Measure directional structure over physical scales.**
  Extend analogue comparisons with directional variograms/spectra, physical
  lag distances, mask support and explicit detrending. Separate orientation
  agreement from rotation-normalized character. Include identical-histogram
  ramp/shuffle fixtures so distribution matching cannot masquerade as realism.
  Local builds now report masked X/Y semivariances and height differences at
  requested 25/100/400 km lags, including effective rounded distances and pair
  counts. Rotation-normalized, arbitrary-angle and detrended comparisons remain.
- [ ] **Research — R42: Type terrain and drainage graph relationships.** Keep
  authored lines, morphological ridges/thalwegs, divides and active channels
  distinct, with source-surface and depression-policy provenance. Compare
  SurfaceNetwork externally on saddles, dry valleys, flats and outlet basins;
  audit its GPL boundary and hole semantics before reuse.
- [ ] **Research — R43: Retain landform measurements at several scales.**
  Compare GRASS geomorphons and quadratic-fit descriptors at world-unit radii.
  Record thresholds, rounded windows, orientation/curvature conventions and
  support/halo limits. Test local flatness on plateaus versus valley floors,
  rotated fixtures and small coastal islands before driving process masks.
- [ ] **Research — R44: Track significant peaks and passes across stages.**
  Compare persistence and peak/saddle relationships using TTK as a read-only
  reference. Specify metre thresholds, prominence conventions, ties, masks and
  island boundaries. Protect authored passes even when persistence is small;
  distinguish added local detail from unwanted changes to large landmarks.

#### Performance and language migration

- [ ] **Research — R45: Reduce geometry-query work before changing language.**
  Compare exact indexed boundary-segment queries, reusable distance fields and
  avoiding unnecessary off-land samples against the current GEOS calls.
  Key caches by geometry, coordinates and algorithm identity. Any approximate
  distance field needs an explicit error budget, coastline/constraint checks,
  and refinement tests; never simplify authored geometry silently.
  The first implementation skips ocean samples in the delivered field and
  diagnostic sampling while preserving full canonical routing grids. Exact
  indexed segment queries were slower on the public coastline in a small probe;
  they have not been adopted. Broader indexing/caching comparisons remain.
- [ ] **Research — R46: Compare compiled kernels on demonstrated bottlenecks.**
  Start with fused noise evaluation and allocation reduction; test hydrology
  loops when representative profiles justify them. Compare existing NumPy,
  a bounded Numba experiment and an optional Rust proof using identical inputs.
  Include cold/warm latency, memory, transfer costs and complete-generation
  speedup. Verify Python/NumPy/Windows compatibility before installing anything.
- [ ] **Research — R47: Define the evidence gate for a Rust migration.**
  Stabilize units, grids, constraint priority, seeds, stage boundaries and
  numerical tolerances first. Require representative fixtures, an end-to-end
  measured benefit and a tested native-library/Windows packaging path. Explicitly
  choose a temporary Python/Rust bridge or a complete runtime replacement;
  a kernel port does not establish full project, CLI or desktop workflow parity.

## UI / UX improvements

### Editing and navigation

- [ ] **P0 — Add selection and a property inspector.** Click a brush stroke,
  point, ridge, or valley to inspect and edit its mode, elevation, size, and
  strength without deleting and redrawing it.
- [ ] **P0 — Add multi-step undo and redo.** Cover creation, deletion, movement,
  property edits, project loading, and clear-all as explicit commands.
- [ ] **P0 — Add pan and zoom.** Keep wheel-based brush sizing predictable by
  assigning zoom to a modifier or dedicated navigation mode; show current map
  scale and cursor coordinates.
- [ ] **P1 — Add draggable line vertices and insertion/removal of vertices.**
  Preserve normalized/world positions exactly and provide numeric entry for
  precise authoring.
- [ ] **P1 — Add explicit peak and pass handles along ridge profiles.** Show
  their along-line order, elevation mode, influence length, and saddle or peak
  role.
- [ ] **P1 — Add a constraints/layers panel.** List, name, reorder where order is
  meaningful, hide/show, lock, duplicate, and delete authored objects; keep
  generated overlays visually distinct.
- [ ] **P1 — Add a regional-refinement selection tool.** Draw or enter bounds,
  choose target sample spacing, show the halo, and preview the parent pixels
  that must remain consistent.

### Feedback and terrain inspection

- [ ] **P0 — Add a fast draft preview.** Debounce edits and regenerate a low-
  resolution preview in the background while retaining an explicit full-quality
  Generate action.
- [ ] **P0 — Add stage-aware progress and cancellation.** Show the current
  pipeline stage, elapsed work, and cancellation status without leaving a
  partial build that appears complete.
- [ ] **P1 — Add switchable inspection overlays.** Include contours, hillshade,
  slope, curvature, influence extents, hard-constraint residuals, drainage,
  catchments, and clipped-elevation warnings.
- [ ] **P1 — Improve elevation inspection.** Show elevation under the cursor,
  local slope, active constraint contributions, and an optional cross-section
  through the selected ridge or valley.
- [ ] **P1 — Make relative-versus-absolute behavior visible.** Use concise
  tooltips and preview labels that state target height, signed displacement,
  ridge relief, or valley incision in the correct terms.
- [ ] **P1 — Add before/after and seed comparison views.** Compare a changed
  constraint, profile, or seed without relying on memory of the previous image.
- [x] **P2 — Add separate cartographic and scientific elevation styles.** Use
  expressive hypsometric tint and stronger relief for everyday mapping while
  retaining an ordered, colour-vision-deficiency-safe inspection view.
- [ ] **P2 — Add tint-only and hillshade-only display modes.** Keep these as
  derived inspection choices that never change the authoritative DEM.

### Project safety and everyday workflow

- [ ] **P0 — Track unsaved changes.** Show a dirty marker and ask before closing,
  opening another project, or importing a replacement coastline.
- [ ] **P0 — Add Save, Save As, and keyboard shortcuts.** After the first Save
  As, ordinary Save should update the known project path atomically; include
  standard undo/redo and open shortcuts.
- [ ] **P1 — Add recoverable autosave.** Keep autosave outside the authored
  project, identify recovery state clearly, and never treat recovery data as a
  completed user save.
- [ ] **P1 — Help relink a moved or deliberately changed SVG.** Display the old
  path and hash, preview whether bounds/topology changed, and require explicit
  acceptance before reusing normalized constraints.
- [ ] **P1 — Add recent projects and clear validation summaries.** Surface
  missing inputs, unsupported versions, constraint conflicts, and output paths
  in language useful to a map author.
- [ ] **P1 — Add named tool presets and sensible per-continent defaults.** Keep
  settings separate for every tool and make copying values deliberate.
- [ ] **P2 — Improve keyboard and accessibility support.** Provide focus order,
  non-mouse authoring alternatives where practical, scalable text, sufficient
  contrast, and controls that do not depend on colour alone.
- [ ] **P2 — Prepare a hosted UI without changing the engine contract.** Reuse
  the same project schema and build operation; add upload, job, quota, and
  download UX only at the service boundary.

## Related decisions and research

- [ADR-0025](docs/adr/0025-centralize-local-frames-and-endpoint-grids.md) centralizes
  source/local conversion and endpoint grids while preserving existing terrain.

- [Selective terrain sampling — 2026-09-05](docs/research/2026-09-05-selective-terrain-sampling.md)
  records implemented profiling and ocean-sample elimination, exact numeric
  comparisons, runtime/memory results and the remaining measurement limits.
- [Language and performance — 2026-09-05](docs/research/2026-09-05-language-and-performance.md)
  records generation timings, native geometry/noise bottlenecks, a foundations-
  first recommendation, language tradeoffs and proposed migration gates R45–R47.
- [Geological structure and terrain composition — 2026-09-05](docs/research/2026-09-05-geological-structure-and-terrain-composition.md)
  connects geological controls, network semantics, measured descriptor limits
  and optional structural/topology tools to R40–R44 and existing experiments.
- [Terrain prototype contracts — 2026-09-04](docs/research/2026-09-04-terrain-prototype-contracts.md)
  records measured noise/grid effects, external source audits, R34–R39 and
  three bounded mountain-detail, sediment-valley and refinement experiments.
- [Terrain realism and landform diversity — 2026-09-04](docs/research/2026-09-04-terrain-realism-and-landform-diversity.md)
  connects R01–R33 to code limitations, scientific papers, tool/runtime
  boundaries, real-data comparisons and ordered prototype gates.
- [Current development strategy](docs/strategy/README.md) orders work by
  dependencies and records the evidence gates for adopting evaluated tools.
- [Technology and world systems — 2026-09-04](docs/research/2026-09-04-technology-and-world-systems.md)
  refreshes numerical, GIS, hydrology, storage, climate, classification, and
  licensing options.

- [Terrain algorithm options — 2026-09-03](docs/research/2026-09-03-terrain-algorithm-options.md)
  records the current solver, hydrology, erosion, multiresolution, validation,
  tooling, and license findings without accepting an implementation.

- [ADR-0003](docs/adr/0003-map-authored-constraints.md) records the initial
  feature-curve conditioning decision and diffusion/process-informed options.
- [ADR-0004](docs/adr/0004-soft-elevation-brush.md) explains why authored brush
  guidance remains vector-based rather than resolution-bound raster paint.
- [ADR-0005](docs/adr/0005-relative-relief.md) defines absolute versus relative
  semantics and links the existing terrain-interpolation research.
- [Terrain tool guide](src/dmtools/terrain/README.md) documents the implemented
  behavior that this roadmap builds on.
