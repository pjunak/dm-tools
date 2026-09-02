# ADR-0004: Paint soft elevation guidance as vector strokes

**Status:** Accepted
**Date:** 2026-09-02
**Deciders:** Repository owner and project maintainer
**Amended by:** [ADR-0005](0005-relative-relief.md)

## Context

Point and line constraints place important summits, ridges, passes, and valleys,
but broad provinces still require many individual features. Editing a raster
paint layer would tie authored input to one resolution and weaken the existing
local-refinement contract.

The workbench needs a fast map-first interaction for shaping plateaus, basins,
uplands, and lowlands without making those strokes exact hard constraints.

## Decision

- Add a terrain-brush constraint stored as one or more normalized vector points,
  a target elevation, an influence radius, and a strength from zero to one. The
  workbench presents twice that radius as the full brush width.
- Interpret strength as a soft blend toward the target elevation. It is not an
  additive height delta and can therefore guide terrain upward or downward.
- Combine overlapping strokes as order-independent weighted targets.
- Apply brush guidance to the low-frequency base before ridges, valleys, exact
  height points, and restored deterministic residual detail.
- Keep the coastline at zero metres through the same coast-distance gate used by
  other authored features.
- In the Tk workbench, drag to paint, use the mouse wheel to change width, and
  use Ctrl+wheel to change strength. Display a live brush ring and numeric
  readout at the pointer.
- Record strokes in derived PNG metadata while the complete versioned terrain
  project schema remains deferred.

## Options considered

### Raster paint mask

This maps directly to pixels and would be simple to blend, but authoring would
be tied to the current output resolution. Resampling a mask could also make
regional refinement inconsistent with the continent build.

### Additive raise and lower brushes

Additive deltas are intuitive for sculpting, but repeated strokes accumulate
without a stable physical meaning. A target-height blend is easier to inspect,
combine, and reproduce.

### Polygon-only terrain regions

Explicit region polygons remain valuable for named terrain character and sharp
boundaries. Freehand vector strokes are a faster first interaction and can
later coexist with polygons.

## Consequences

- Broad terrain can be shaped quickly without sacrificing deterministic
  coordinate-addressed generation.
- Increasing brush strength monotonically moves the base toward the target.
- The brush controls elevation tendency only. It does not yet paint roughness,
  directional grain, rock resistance, or erosion character.
- Project save/load is still required before authored work is durable between
  sessions.

## Validation

- Domain tests reject empty strokes, repeated adjacent points, and invalid
  strength.
- Pipeline tests cover raising, lowering, strength ordering, coastline
  preservation, deterministic nested resolutions, and metadata export.
- The desktop workbench is smoke-tested through construction and an idle event
  cycle without showing a window.
