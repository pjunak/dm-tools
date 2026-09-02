# ADR-0003: Author topography on the map and condition the base surface

**Status:** Accepted
**Date:** 2026-09-02
**Deciders:** Repository owner and project maintainer

## Context

The coastline-only generator produced deterministic relief, but numeric
controls could not specify where important peaks, ranges, passes, and valleys
belong. The first direct-manipulation implementation placed height points and
ridge or valley lines correctly, but applying them as compact post-processing
stamps produced isolated circular bumps and narrow tubes that did not influence
the surrounding base terrain naturally.

The complete feature schema, geological process model, and serialized terrain
project are not settled. The current slice still needs a useful authoring
interaction and a resolution-independent numeric response without adding a GIS
application or raster-only editing state.

## Decision

- Author exact height points and ridge or valley centrelines directly over the
  imported coastline in the Tk workbench.
- Store positions normalized to the coastline bounding box. Convert them to the
  explicit metric working extent only inside the pipeline.
- Treat height points as exact target elevations, ridges as minimum elevations,
  and valleys as maximum elevations.
- Interpret the authored width as a strong-response core rather than a hard
  cut-off. Combine it with a broader, lower-amplitude Gaussian shoulder tied to
  the terrain's largest feature scale.
- Build a low-frequency terrain surface when constraints exist, condition that
  surface first, then restore the deterministic high-frequency residual with
  attenuation near authored geometry.
- Smooth multi-vertex structure guides, taper their free ends, and vary their
  effective width and permitted crest or floor relief with the deterministic
  terrain field.
- Attach nearby exact height points to structure profiles as longitudinal
  anchors. Keep a narrow exact point response for the authored location.
- Make constraint influence compete smoothly with distance to the coastline so
  the coastline remains a hard zero-metre boundary.
- Apply ridges first, valleys second, and exact height points last. This lets a
  valley cross an uplifted belt and lets a point explicitly resolve a local
  intersection.
- Record authored constraints in exported preview metadata. Continue to defer
  the versioned serialized project schema.

## Options considered

### Compact post-processing stamps

This was simple, deterministic, and preserved exact targets, but its hard
radius made structures visually separate from the terrain that surrounded
them. It is replaced by the conditioned base-surface model.

### Global Poisson or multigrid diffusion

Diffusion is a strong future option for asymmetric slopes, profiles, and dense
constraint networks. A raster solver would introduce resolution-dependent
iteration and boundary behavior before the parent/child consistency contract
is ready, so it is deferred.

### Process-informed uplift and erosion

This is the intended route to drainage-aware mountain systems. It remains a
later pipeline stage rather than a prerequisite for direct authoring.

## Consequences

- Authored structures influence the broad terrain trend and no longer end at a
  visible circular or tubular boundary.
- Exact targets, sea level, determinism, and shared samples at nested
  resolutions remain testable invariants.
- The response is plausible interpolation, not a claim of geological
  simulation.
- Ridge and valley lines currently have one base target elevation and symmetric
  sides. Nearby spot heights can bend the generated longitudinal profile, but
  explicit per-vertex profiles and asymmetric slopes require a later
  compatibility decision.

## Validation

- Domain tests cover normalized positions, structure vertices, physical
  elevations, and positive widths.
- Pipeline tests cover exact height targets, ridge raising, valley cutting,
  broad response beyond the core, hard sea level, deterministic output, and
  nested-resolution equality.
- PNG tests verify that authored inputs are retained in derived preview
  metadata.
