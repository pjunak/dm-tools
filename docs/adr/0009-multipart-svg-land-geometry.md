# ADR-0009: Dissolve multipart SVG land geometry before generation

**Status:** Accepted
**Date:** 2026-09-03
**Deciders:** Repository owner and project maintainer

## Context

ADR-0002 deliberately limited the first workbench to one closed SVG object.
The complete Tharkeniss source instead contains separate filled paths for four
adjacent subcontinents and their islands. Generating each group independently
would make the authored group boundaries into artificial elevation, noise, and
eventually drainage seams.

The source also demonstrates two ordinary vector-export issues: adjacent land
pieces can overlap slightly or stop less than one flattening sample apart, and
their union can contain tiny enclosed slivers. Those artifacts must not become
sea-level cuts through an otherwise continuous continent.

## Decision

- Prefer drawable shapes beneath groups whose direct `id` or namespaced
  `serif:id` normalizes to `Land Shapes`. If no such group exists, retain the
  simple-SVG behavior of treating every drawable shape as land.
- Require every selected land object to contain one continuous closed subpath.
  Apply SVG transforms before flattening and validate every polygon before
  combining it.
- Flatten curves adaptively against the complete land extent. If the adaptive
  polygon is invalid, retry only that object with the previous uniform bulk
  sampler. Do not perform an expensive exact-length calculation for every path.
- Union all valid land polygons. Close gaps smaller than the flattening
  tolerance, dissolve shared mainland edges, and fill enclosed slivers below a
  scale-relative area threshold. Preserve larger enclosed gaps as water.
- Store the largest connected polygon as the primary coastline and all other
  polygons as `LandComponent` values. A component may retain enclosed water
  rings.
- Define object scale from the combined bounds. Rasterize and condition every
  component in one metric grid with the same coordinate-addressed field and
  stage seed. Only the dissolved land-water boundary participates in the
  coastal elevation gate.
- Keep version-1 project JSON unchanged. It already stores the authoritative
  SVG path and byte hash rather than sampled geometry, so expanding the
  in-memory interpretation is backward compatible with existing one-loop
  projects.

This decision supersedes only ADR-0002's single-object SVG restriction. Its Tk,
pipeline-separation, scale, numeric-output, and background-work decisions remain
in force.

## Consequences

- Subcontinent paths may overlap or meet imperfectly without producing terrain
  seams.
- Islands share the continent's exact coordinate system, seed, and scale.
- Lines cannot cross open water, while point and local line constraints can be
  authored on any land component.
- Direct SVG group membership is intentionally discarded after dissolution.
  Future subcontinent-specific terrain profiles need explicit authored regions,
  not the accidental borders of filled land polygons.
- Tiny enclosed water features below the repair threshold can be removed. A
  future semantic lake/water input must represent deliberate small water bodies
  explicitly instead of relying on near-coincident filled land edges.
- Compound paths containing explicit hole subpaths remain unsupported. Larger
  enclosed gaps formed by separate valid land polygons are retained.

## Validation

- Adapter fixtures cover multiple disconnected objects, overlapping grouped
  land, filtering of non-land layers, near-touching edges, retained enclosed
  water, filled sliver gaps, open paths, and self-intersections.
- Pipeline fixtures verify one shared mainland/island grid, island constraints,
  cross-water line rejection, and a zero-metre retained water boundary.
- The actual `Tharkeniss.svg` source imports as 40 connected land components
  with no residual sliver holes and completes a low-resolution terrain build.
  On the validation host, adaptive import took approximately two seconds
  instead of approximately twenty-two seconds with per-path length solving.
