# Research notes

Research notes collect evidence and prototype recommendations that have not yet
become architecture decisions. They are working material: an approach listed
here is not part of the terrain contract until it is accepted in an ADR and
implemented with tests. Notes are listed newest first and package-support claims
may become stale; use the
[current development strategy](../strategy/README.md) for the active order.

- [Finer water connections - 2026-09-11](2026-09-11-finer-water-connections.md)
  records detected shoreline gaps, contact barriers, exported profiles and measured cost.
- [Basin flat routing - 2026-09-11](2026-09-11-basin-flat-routing.md)
  records exact-flat routing, preserved pits, exported paths and measured cost.
- [Basin catchment review - 2026-09-11](2026-09-11-basin-catchment-review.md)
  maps collected/retained nodes and records outlet-level evidence and next steps.
- [Connected lake outflow - 2026-09-11](2026-09-11-connected-lake-outflow.md)
  records conservative outlet transfer, a real rejected route, validation and runtime.
- [Basin retention and outlet assessment - 2026-09-11](2026-09-11-basin-retention-and-outlets.md)
  records conserved basin area, downstream evidence, validation and runtime.
- [Authored water implementation - 2026-09-10](2026-09-10-authored-water.md)
  records lake/dry-basin retention, validation and measured runtime limits.
- [Basin extent and outlet topology - 2026-09-10](2026-09-10-basin-outlet-topology.md)
  unifies diagnostic grids and records explicit escape routes and water-boundary context.
- [Depressions and channel conflicts - 2026-09-10](2026-09-10-depressions-and-channel-conflicts.md)
  compares retention, constrained breaching and outlet mapping, and records
  overlapping conflict diagnostics and the zero-height flow fix.
- [Selective terrain sampling — 2026-09-05](2026-09-05-selective-terrain-sampling.md)
  records the Python benchmark harness, exact-output optimization, timing/memory
  comparisons and rejected indexing probe for the first R45 slice.
- [Language and performance — 2026-09-05](2026-09-05-language-and-performance.md)
  measures the current generator, recommends a bounded foundation/performance
  pass in Python, compares a future Rust migration and records R45–R47 gates.
- [Geological structure and terrain composition — 2026-09-05](2026-09-05-geological-structure-and-terrain-composition.md)
  adds R40–R44: related regional recipes, material-coordinate and event-order
  requirements, distinct terrain/water graphs, directional measurements,
  multiscale landform classification and significant peak/pass comparisons.
- [Terrain prototype contracts — 2026-09-04](2026-09-04-terrain-prototype-contracts.md)
  narrows the first experiments with measured noise/grid effects, source audits
  of SPACE and GPU references, landform suitability, numeric exchange gates,
  and focused meander/delta alternatives. Adds R34–R39 to the roadmap.
- [Terrain realism and landform diversity — 2026-09-04](2026-09-04-terrain-realism-and-landform-diversity.md)
  extends the roadmap with R01–R33: regional composition, sediment, specialized
  landforms, scale contracts, recent papers, external tools, and comparison
  experiments. It also corrects the earlier procedural-pattern paper title
  and revisits the blanket preference against particle erosion.
- [Technology and world systems — 2026-09-04](2026-09-04-technology-and-world-systems.md)
  refreshes numerical, GIS, hydrology, storage, climate-model, classification,
  and licensing options and turns them into staged recommendations.
- [Terrain algorithm options — 2026-09-03](2026-09-03-terrain-algorithm-options.md)
  compares base-surface solvers, drainage methods, landscape processes,
  multiresolution implications, validation fixtures, and candidate libraries.
- [Elevation colour ramp — 2026-09-03](2026-09-03-elevation-colour-ramp.md)
  evaluates ordered elevation display and selects the accessible `oleron` land
  sequence for scientific inspection.
- [Cartographic relief style — 2026-09-03](2026-09-03-cartographic-relief-style.md)
  decomposes the preferred illustrated relief look and separates it from the
  ordered scientific inspection view.
