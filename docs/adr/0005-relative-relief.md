# ADR-0005: Separate absolute elevation from relative relief

**Status:** Accepted
**Date:** 2026-09-02
**Deciders:** Repository owner and project maintainer

## Context

The first authored constraints interpreted every metre value as an absolute
world elevation. This is appropriate for surveyed spot heights and known valley
floors, but it makes a generated mountain insensitive to the range beneath it.
Likewise, an absolute valley floor can pull a valley through a high plateau down
to the same elevation as one crossing a low plain.

The workbench also shared elevation and radius controls across all tools. Users
had to replace useful values whenever they switched between a broad brush, a
peak, a ridge, and a valley.

There is no universal terrain-file standard for the intended relative authoring
semantics. Established terrain-generation work does provide the relevant
building blocks: feature curves can carry elevation, slope, and roughness
constraints and diffuse them into a surface; local-relief models separate broad
landforms from residual height; and hydrologic DEM interpolation distinguishes
elevation observations from drainage constraints and their tolerances.

## Decision

- Give every brush stroke, height point, ridge, and valley an explicit
  `elevation_mode`: `absolute` or `relative`.
- Keep independent mode, elevation value, and radius or width controls for each
  authoring tool. Keep brush strength with the brush. Switching tools must not
  copy or reset another tool's values.
- Preserve `absolute` as the domain-model default for compatibility. Start the
  workbench with relative brush, relative ridge, relative valley, and absolute
  height point settings.
- Define relative values against the immutable surface entering the feature's
  named pipeline stage. Do not recalculate a moving neighbourhood mean while a
  feature is being applied.
- Interpret a relative brush or point as a signed vertical displacement. A
  relative ridge value is positive added relief; a relative valley value is
  positive incision depth.
- Apply stages in this fixed order: absolute brush targets, relative brush
  displacement, absolute ridges, relative ridge relief, absolute valleys,
  relative valley incision, relative point displacement, and absolute points.
- Combine overlapping absolute brushes as weighted targets. Sum relative brush
  and point displacements. Use the strongest same-kind ridge uplift or valley
  incision at each location. These rules are independent of authored list order.
- Suppress high-frequency residual terrain only for absolute constraints.
  Relative constraints retain it, making their result genuinely relative to the
  generated terrain beneath them.
- Continue applying the coastline gate and final elevation bounds to both modes.
- Describe relative values as displacement, relief, or incision—not as
  topographic prominence. True prominence depends on the final key saddle and is
  a later terrain-network measurement.

For a surface entering a stage as `H`, a smooth influence weight `w`, an
absolute target `A`, and a relative displacement `d`, the basic operations are:

```text
absolute guidance: H' = (1 - w) H + w A
relative guidance: H' = H + w d
```

Absolute ridges and valleys retain their minimum/maximum inequality semantics;
relative ridges and valleys use positive uplift and incision magnitudes.

## Options considered

### Absolute constraints only

This is unambiguous and appropriate for measured elevations, but it cannot state
that a feature should preserve and modify the terrain beneath it.

### Recalculate a local neighbourhood reference for every feature

This resembles an informal local-relief measurement, but its result depends on
window size, resolution, feature order, and whether previous constraints are
included. Those dependencies make author intent and deterministic refinement
harder to explain.

### Signed displacement fields over named reference stages

This is deterministic, scale-aware through the existing kilometre influence
radius, and composes naturally with the current base-plus-residual model. It does
not by itself guarantee hydrologic correctness or topographic prominence.

## Consequences

- A relative peak inherits the elevation of a ridge or plateau beneath it.
- A relative valley remains higher in high terrain while maintaining its
  authored incision depth.
- Absolute surveyed values remain available and authoritative.
- Signed relative brushes and points can intentionally lower terrain; ridge and
  valley magnitudes remain non-negative because their kind supplies direction.
- Repeated relative strokes accumulate. Undo and future project editing remain
  important for controlling that accumulation.
- Per-vertex elevation modes, explicit side slopes, hydrologic descent, and
  measured prominence remain future work.

## Research basis

- Hnaidi et al., *Feature based terrain generation using diffusion equation*,
  Computer Graphics Forum 29(7), 2010:
  <https://doi.org/10.1111/j.1467-8659.2010.01806.x>
- Australian National University, *ANUDEM 5.3* specification and user guide:
  <https://fennerschool.anu.edu.au/research/products/anudem-version-5-3>
- GRASS GIS, `r.local.relief`, documenting large-scale smoothing followed by
  elevation subtraction:
  <https://grass.osgeo.org/grass85/manuals/addons/r.local.relief.html>

## Validation

- Domain tests cover valid modes, signed relative point and brush values, and
  non-negative ridge relief and valley depth.
- Pipeline tests verify exact absolute constraints, relative brush displacement,
  peak-on-ridge composition, relative valley incision, coastline preservation,
  overlap order independence, and nested-resolution equality.
- The Tk interaction smoke test verifies that every tool retains its own mode,
  value, and size while switching.
