# ADR-0014: Condition valley floors from head to outlet

**Status:** Accepted
**Date:** 2026-09-04
**Deciders:** Repository owner and project maintainer

## Context

Relative valley lines previously subtracted a constant or anchored depth from
the terrain independently at each location. A valley crossing rising terrain
could therefore climb toward its supposed outlet. Absolute valley profiles
could likewise contain uphill hard anchors. Both results looked valley-like in
cross-section but did not provide a coherent longitudinal floor.

The correction must keep high-altitude valleys high relative to their setting,
preserve deterministic nested-resolution behavior, and distinguish hard world
heights from relative incision guidance. Full flow routing, lakes, and basin
semantics are not yet available.

## Decision

- Interpret valley vertices in authored order from upstream head to downstream
  outlet. Show that direction with an arrow in the workbench.
- In absolute mode, interpret the line value as the downstream outlet floor.
  Interpolate attached exact height anchors with a shape-preserving profile and
  reject any hard-anchor sequence that rises downstream.
- In relative mode, sample the complete deterministic surface entering the
  valley stage and subtract the authored incision-depth profile.
- Sample in metric coordinates at no more than 2 km spacing and no more than
  one quarter of the valley radius. Insert every authored profile anchor as an
  exact sample knot. The samples do not depend on output raster resolution.
- Apply a cumulative downstream minimum to the preferred floor. This only cuts
  downstream rises and never raises the floor.
- Treat relative depth as preferred minimum incision. The monotonic correction
  may deepen a downstream reach where retaining the requested depth would make
  the floor climb.
- Continue suppressing residual detail at the valley centreline so the prepared
  monotonic floor is not broken by later high-frequency restoration.

## Consequences

- High-altitude valleys retain the elevation of their low-frequency setting
  while gaining a coherent non-rising route.
- Reversing a valley line changes its hydrological meaning and may change the
  result. Existing project-version-1 valleys use their stored vertex order and
  may need to be redrawn if that order was previously arbitrary.
- Exact absolute anchors are never silently moved. An incompatible sequence is
  a generation error with guidance to draw head-to-outlet.
- Relative anchors are guidance rather than hard floor heights. A shallower
  downstream request can be overridden by the non-rising-floor inequality.
- Flat reaches are permitted. Minimum channel grade, lakes, endorheic basins,
  depression policy, flow routing, and sea connectivity remain future stages.

## Validation

- A high relative valley fixture verifies non-rising centreline elevation and
  at least the requested incision without collapsing the valley to lowland.
- An absolute fixture verifies exact non-rising anchors, outlet height,
  constraint-order independence, and nested-resolution equality.
- An invalid uphill absolute-anchor fixture must fail explicitly.
- Existing flat-reference relative-depth fixtures preserve their requested
  incision and attached relative profile semantics.
