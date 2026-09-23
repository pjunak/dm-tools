# ADR-0069: Connect and scale drainage review

Date: 2026-09-24

Status: Accepted

## Context

The workbench stretched a cached review raster during zoom, magnifying its
channel strokes. All selected automatic channels had equal visual weight.
Generation had an implicit fixed drainage-density policy. Actual routes also
retain D8 direction bias; decorative curve smoothing would misrepresent the
terrain being reviewed.

## Decision

Add an authored density multiplier (0.25–2.0, default 1.0) to automatic channel
initiation. Compute the slope reference independently of the multiplier and
retain downstream closure, regional incision caps and basin terminals. Keep the
validated default rather than silently reducing valley development globally.
A trial default of 0.75 failed an existing downstream-shoulder-width invariant.

Derive immutable reaches from every selected edge, splitting at heads and
junctions and sharing their exact metric coordinates. Measure unique D8 area at
the last donor of each reach. Use this downstream-monotone area for complete-reach
visibility, independently of viewport cropping. Retain MFD capture as a separate
numeric product. Reach and display identities are
`canonical-d8-connected-reaches@1` and `connected-catchment-screen-scale@1`.

Redraw channel vectors in the visible viewport with bounded tiled antialiasing.
Fade reaches between 64 and 112 px square-root catchment area. Keep an explicit
All channels view and draw every sampled uphill edge in red at every scale.
Only collinear vertices are compacted; actual turns and junctions do not move.
Basin raster overlays retain their independent cache and lifetime. A separate
Depressions toggle starts off, keeping coarse basin polygons out of the default
channel inspection while preserving their full diagnostic view.

Require project v6, build v18, input snapshot v2 and regional samples v2, and
remove their obsolete schemas. Parent-region v1 keeps its layout and points to
current build definitions. Generator @18 and automatic valleys @14 own changed
input semantics. No compatibility loaders or output editing are introduced.

## Consequences

Density changes the generated valleys; zoom filtering only changes inspection.
The review is clearer without claiming new local hydrology or physical river
widths. Static exported diagnostics remain complete. Cache preparation stays on
the bounded canonical graph; rendering scratch does not grow with map zoom.

Grid-direction artifacts and infeasible channel floors remain visible and are
still P0 generation work. A future off-grid path must be shared with incision
and sampled ground validation. See the [guide](../terrain-drainage.md) and
[measurements](../research/2026-09-24-connected-drainage-review.md).
