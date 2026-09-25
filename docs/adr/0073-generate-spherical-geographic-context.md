# ADR-0073: Generate spherical geographic context from retained vectors

- Status: Accepted
- Date: 2026-09-25
- Builds on [ADR-0070](0070-retain-world-source-and-workspaces.md) and
  [ADR-0072](0072-bound-world-source-imperfections.md).

## Context

WC1 needs useful geographic context before climate, macro terrain and regional
history can share a world. Binary coarse masks can erase small islands, close
straits or create false passages. Continents are semantic owners, not physical
components or solver boundaries. Flattening the source into a new binary mask
would lose the distinctions established by WC0.

## Decision

Use a bounded cell-centred full-sphere Plate Carrée grid on the authored radius
and frame, with exact spherical cell areas. Derive fractional land coverage from
intersection with WC0's prepared vectors and measure clipped boundaries using
the source-linear spherical integral. Remove its constant reference sine and
use compensated summation plus a stable small-angle correction so tiny positive
water pockets do not cancel to zero. Do not treat flat-page area or
local terrain endpoint samples as spherical cell averages.

Derive connected water from the vector complement of prepared land. Join water
polygons across longitude boundaries only along positive-length shared openings.
Do not join bodies through zero-width polar/point contacts. Rank water IDs by
physical area with deterministic geometric ordering. The complete source and
algorithm reconstruct this topology; continent labels do not partition it.

Each cell displays its dominant water region but separately flags mixed coverage,
disconnected water pieces and surfaces absent at the centre. Small features stay
in area fractions and vector identity. Neither a dominant ID nor a single pixel
gap certifies a numerical flow gateway. Explicit gateway width/capacity and verified
context consumption remain later WC1 work.

Expose Context generation/cancellation, three geographic layers, cell inspection,
input invalidation and export in the World workspace. Keep context inputs/results
separate from authored world files. Generate from an immutable verified snapshot;
reject stale worker results. Serialize current arrays and an input snapshot into
a new directory, record source/runtime and output hashes, and publish completion
last. No compatibility loaders or new dependencies are introduced.

The algorithm is `spherical-geography-v1`; context v1 (superseded by
[ADR-0074](0074-verify-context-and-measure-water-openings.md))
defines the exported contract. Generation has no random stage. A 360-row limit
bounds the raster to 259,200 cells. Row-local geometry, prepared predicates and
pure-cell shortcuts reduce repeated coastline intersections. Cancellation checks
surround progress and rows; native geometry calls are not interrupted internally.

## Evidence and limits

Controls cover sphere area, pole-centred avoidance, source scale/offset and grid
resolution, periodic topology, polar barriers, tiny islands/holes, a subcell
strait, split-water cells, deterministic arrays, cancellation, snapshot/runtime
identity, incomplete publication and actual Tk use. No source coastline is moved.
See the [validation report](../research/2026-09-25-geographic-world-context.md).

This is the geographic subset of WC1. It does not infer ocean bathymetry, climate,
plate history, province age, river runoff or terrain. Context outputs are not yet
verified terrain parents. The next stage must define geodesic exposure and finite
gateway support before claiming climate transport through unresolved cells.

## Implementation references

- [Shapely prepared geometry](https://shapely.readthedocs.io/en/stable/reference/shapely.prepare.html)
  documents accelerated repeated predicates used for row classification.
- [Shapely intersection](https://shapely.readthedocs.io/en/stable/reference/shapely.intersection.html)
  documents floating-point intersection; this stage does not add coordinate-grid snapping.
