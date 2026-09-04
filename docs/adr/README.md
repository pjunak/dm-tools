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
