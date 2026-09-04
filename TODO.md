# Terrain tool roadmap

This is the working backlog for the deterministic terrain tool. It collects the
possibilities identified during the initial research and implementation without
treating every idea as an accepted design. Items marked **Research** need a
small prototype or architecture decision before they become implementation
commitments.

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

- [ ] **P0 — Define the versioned build manifest.** Record project and input
  hashes, generator and schema versions, master and stage seeds, effective
  parameters, working extent and units, runtime/dependency versions, warnings,
  and authoritative output hashes.
- [ ] **P0 — Export the authoritative Float32 DEM as GeoTIFF.** Include an
  explicit metric coordinate system, extent, pixel size, elevation units,
  nodata value, and a link to the build manifest.
- [ ] **P1 — Add a non-interactive build command.** Let
  `dmtools terrain build <project.dmterrain.json>` use the same domain,
  pipeline, and adapters as the desktop workbench.
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
- [ ] **P1 — Add terrain-character regions.** A vector region should select a
  named profile controlling broad relief, roughness, drainage density, erosion
  resistance, and transition distance without baking those properties into a
  raster paint mask.
- [x] **P1 — Support adjacent mainland sections and disconnected islands.** SVG
  land objects are dissolved into one polygonal mask, sub-sampling border
  slivers are repaired, and all components share one metric field and seed.
- [ ] **P1 — Add explicit lakes and authored water holes.** Define water levels,
  outlets, endorheic status, and compound-path semantics rather than inferring
  all enclosed gaps from filled land shapes.
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
- [ ] **P2 — Add explicit project migration commands.** Never guess how to
  reinterpret an older public schema silently.
- [ ] **P2 — Evaluate a portable project bundle.** A bundle could package the
  JSON and authored source assets while retaining readable hashes; plain JSON
  plus relative files remains the default until portability justifies it.
- [ ] **P2 — Expose the engine through a hosted interface.** Keep local use
  complete and put job management, limits, authentication, and storage outside
  the deterministic engine.
- [ ] **P1 — Select a public project license before distribution.** Recheck the
  licenses and distribution implications of every optional scientific engine
  included in a hosted or downloadable build.

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
  smooth downstream with drainage hierarchy; authored per-vertex shape,
  glacial forms, floodplains, and terraces remain.
- [ ] **P0 — Derive drainage direction and flow accumulation.** Define the
  depression fill/breach policy, flat handling, edge outlets, and sea
  connectivity before promising hydrologically valid rivers. Prototype MFD for
  continuous accumulation and D8 for unique catchment trees; include rotated
  fixtures so grid-direction bias is measurable. A fixed canonical-grid
  Priority-Flood + MFD accumulation stage now drives automatic broad valleys,
  with a rotated fixture, and a complementary D8 tree supplies unique generated
  centrelines. A bounded area-slope channel-head rule now starts steep
  headwaters earlier, preserves large gentle rivers, and closes every selected
  path downstream. Public drainage products, authored depression policy, basin
  labels, and user-facing drainage-density profiles remain.
- [ ] **P1 — Reconcile authored rivers with generated drainage.** Rivers should
  descend to a valid outlet and occupy a local valley; report conflicts rather
  than silently moving an authored route.
- [ ] **P1 — Validate basins, outlets, and drainage connectivity.** Detect
  unintended inland sinks, uphill river segments, disconnected channels, and
  coastline outlets that fail to reach sea level. A resolution-independent
  129-cell canonical check now reports strict-D8 direct connectivity, potential
  sink cells, Priority-Flood depth/volume, outlets, and largest catchment without
  mutating terrain. Significant fill components are now ranked as coarse basin
  candidates and marked in the workbench with floor, spill, area, depth, and
  volume metadata. Authored basin classification, a full nested depression
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
  metadata; the other statistics and a durable build report remain.
- [ ] **P1 — Add explicit prominence and saddle analysis.** Keep this derived
  measurement separate from the current relative-relief controls.
- [ ] **P0 — Lock algorithm and stage identifiers before long-lived builds.**
  Parameter, solver, stage-order, or seed-derivation changes must be visible in
  the build manifest and regression fixtures.
- [ ] **P1 — Generate refinement halos and crop final tiles.** Evaluate all
  neighbourhood-dependent solvers and erosion on buffered bounds to avoid
  seams, then verify overlap and downsample consistency numerically.
- [ ] **P2 — Profile memory and runtime by stage.** Prefer chunked/vectorized
  computation and measured optimizations; consider compiled or external engines
  only for demonstrated bottlenecks.

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
