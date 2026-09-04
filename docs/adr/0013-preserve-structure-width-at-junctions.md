# ADR-0013: Preserve authored structure width at junctions

**Status:** Accepted
**Date:** 2026-09-04
**Deciders:** Repository owner and project maintainer

## Context

Ridge and valley lines narrow toward their free endpoints so an isolated
feature blends into surrounding terrain. Applying that rule independently to
every line also narrowed endpoints that joined another compatible structure.
A mountain range split into two authored lines therefore developed an
artificial waist at the join, and a branch could begin with a weak pinched root.

Authored networks need continuity before procedural branch generation or
erosion can improve them. The correction must remain deterministic,
order-independent, and stable across raster resolutions.

## Decision

- Classify a ridge or valley endpoint as a junction when it meets another
  structure with the same kind and elevation mode.
- Use a metric contact tolerance capped at 2 km and at 2% of the narrower
  structure's influence radius. This tolerance is independent of raster
  resolution and constraint order.
- Preserve the full cross-section at a junction endpoint.
- Continue narrowing genuinely free endpoints with the existing smooth taper.
- Do not infer parent/child hierarchy, connect different structure kinds, or
  merge absolute and relative structures. Those require explicit semantics.

## Consequences

- Splitting a compatible ridge or valley into connected line segments preserves
  the same junction cross-section as one continuous line. Small bounded
  differences can remain away from the join because geometric distance to two
  segments is not numerically identical to distance to one line.
- Authored range branches and valley networks no longer receive an artificial
  narrow neck solely because of line boundaries.
- Near but intentionally separate features remain independent unless their
  endpoint falls within the small metric contact tolerance.
- This is a network-continuity improvement, not hierarchical branch
  generation. Branch identities, taper by hierarchy, junction angles, and
  procedural spurs remain future work.

## Validation

- Synthetic ridge and valley fixtures compare a continuous line with two
  connected segments. The junction cross-section must match exactly and the
  complete Float32 raster must remain within a measured 3 m tolerance.
- A T-shaped ridge fixture verifies that a connected child line has materially
  more shoulder relief at its root than the same line treated as isolated.
- Reordering the connected segments must produce an identical raster.
- Existing deterministic, nested-resolution, constraint, and coastline tests
  continue to pass.
