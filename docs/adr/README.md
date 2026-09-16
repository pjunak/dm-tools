# Architecture decision records

ADRs preserve significant technical decisions and their trade-offs.

## Process

1. Copy the structure of an existing ADR.
2. Use the next four-digit sequence number.
3. Mark an undecided proposal as `Proposed` and an agreed decision as
   `Accepted`.
4. Do not rewrite an accepted decision to hide a later change. Add a new ADR and
   mark the old one `Superseded`.
5. Link implementation commits and validation evidence when they exist.

Earlier ADRs are historical records. [ADR-0027](0027-develop-current-behavior-without-legacy-support.md)
supersedes their legacy compatibility commitments during early development.

## Index

- [ADR-0001: Use Python 3.14 for the application and terrain engine](0001-python-3-14.md)
- [ADR-0002: Build the first terrain workbench with Tk and SVG input](0002-tk-svg-terrain-workbench.md)
- [ADR-0003: Author topography on the map and condition the base surface](0003-map-authored-constraints.md)
- [ADR-0004: Paint soft elevation guidance as vector strokes](0004-soft-elevation-brush.md)
- [ADR-0005: Separate absolute elevation from relative relief](0005-relative-relief.md)
- [ADR-0006: Persist authored terrain as versioned JSON with a verified SVG reference](0006-versioned-terrain-project.md)
- [ADR-0007: Use shape-preserving longitudinal profiles for anchored structures](0007-shape-preserving-structure-profiles.md)
- [ADR-0008: Interpret relative points as relative structure profile anchors](0008-relative-structure-profile-anchors.md)
- [ADR-0009: Dissolve multipart SVG land geometry before generation](0009-multipart-svg-land-geometry.md)
- [ADR-0010: Use Oleron's ordered land colours for elevation relief](0010-use-oleron-land-colours-for-elevation.md)
- [ADR-0011: Separate cartographic and scientific elevation styles](0011-separate-cartographic-and-scientific-relief-styles.md)
- [ADR-0012: Fix the cartographic colour scale at ten kilometres](0012-fix-cartographic-colour-scale-at-ten-kilometres.md)
- [ADR-0013: Preserve authored structure width at junctions](0013-preserve-structure-width-at-junctions.md)
- [ADR-0014: Condition valley floors from head to outlet](0014-condition-valley-floors-downstream.md)
- [ADR-0015: Route automatic valleys on a canonical hydrology grid](0015-route-automatic-valleys-on-canonical-grid.md)
- [ADR-0016: Scale generated valley width downstream](0016-scale-generated-valley-width-downstream.md)
- [ADR-0017: Report canonical drainage diagnostics without repairing the DEM](0017-report-canonical-drainage-diagnostics.md)
- [ADR-0018: Group diagnostic fill regions into basin candidates](0018-group-diagnostic-fill-regions-into-basin-candidates.md)
- [ADR-0019: Initiate generated channels with bounded area-slope thresholds](0019-initiate-generated-channels-with-bounded-area-slope-thresholds.md)
- [ADR-0020: Condition generated channel floors downstream](0020-condition-generated-channel-floors-downstream.md)
- [ADR-0021: Correct broad valleys with MFD convergence](0021-correct-broad-valleys-with-mfd-convergence.md)
- [ADR-0022: Bound extreme generated-channel steepening](0022-bound-extreme-generated-channel-steepening.md)
- [ADR-0023: Derive Strahler order without forcing valley width](0023-derive-strahler-order-without-forcing-valley-width.md)
- [ADR-0024: Publish local numeric terrain builds before changing algorithms](0024-publish-local-numeric-terrain-builds.md)
- [ADR-0025: Centralize local frames and endpoint grids](0025-centralize-local-frames-and-endpoint-grids.md)
- [ADR-0026: Version named terrain stage seeds](0026-version-named-terrain-stage-seeds.md)
- [ADR-0027: Develop current behavior without legacy support](0027-develop-current-behavior-without-legacy-support.md)
- [ADR-0028: Export local-metric GeoTIFF](0028-export-local-metric-geotiff.md)

- [ADR-0029: Route drainage over authored terrain](0029-route-drainage-over-authored-terrain.md)

- [ADR-0030: Author regional landforms](0030-author-regional-landforms.md)

- [ADR-0031: Bound incision by regional relief](0031-bound-incision-by-regional-relief.md)

- [ADR-0032: Classify channel conflicts](0032-classify-channel-conflicts.md)
- [ADR-0033: Map basin spill candidates](0033-map-basin-spill-candidates.md)

- [ADR-0034: Author lakes and dry basins](0034-author-lakes-and-dry-basins.md)

- [ADR-0035: Retain basin flow and assess outlets](0035-retain-basin-flow-and-assess-outlets.md)

- [ADR-0036: Connect lake outflow with area transfer](0036-connect-lake-outflow-with-area-transfer.md)
- [ADR-0037: Expose basin catchment outcomes](0037-expose-basin-catchment-outcomes.md)
- [ADR-0038: Route basin flats with integer gradients](0038-route-basin-flats-with-integer-gradients.md)
- [ADR-0039: Sample shorelines and outlet connections](0039-sample-shorelines-and-outlet-connections.md)
- [ADR-0040: Refine water profiles around authored features](0040-refine-water-profiles-around-authored-features.md)
- [ADR-0041: Review complete downstream outlet profiles](0041-review-complete-downstream-outlet-profiles.md)
- [ADR-0042: Review internal water links](0042-review-internal-water-links.md)
- [ADR-0043: Review dry collection paths](0043-review-dry-collection-paths.md)
- [ADR-0044: Guide water profiles through regional transitions](0044-guide-water-profiles-through-regional-transitions.md)

- [ADR-0045: Sample procedural detail and context shoulders](0045-sample-procedural-detail-and-context-shoulders.md)

- [ADR-0046: Forecast water-sampling budgets](0046-forecast-water-sampling-budgets.md)
- [ADR-0047: Edit generation inputs only](0047-edit-generation-inputs-only.md)
  (regional-generation scope corrected by ADR-0048)
- [ADR-0048: Keep zoom-driven detail generation in scope](0048-keep-zoom-driven-detail-generation.md)
- [ADR-0049: Navigate and save authored terrain inputs](0049-navigate-and-save-authored-inputs.md)
- [ADR-0050: Reconstruct automatic valleys with bounded cubics](0050-reconstruct-valleys-with-bounded-cubics.md)
- [ADR-0051: Connect diagonal valley shaping](0051-connect-diagonal-valley-shaping.md)
- [ADR-0052: Fit channel cuts to the sampled terrain](0052-fit-channel-cuts-to-sampled-terrain.md)
