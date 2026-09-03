# ADR-0010: Use Oleron's ordered land colours for elevation relief

**Status:** Superseded in part by ADR-0011
**Date:** 2026-09-03
**Deciders:** Repository owner and project maintainer

## Context

The first colour-relief renderer used a hand-built hypsometric tint. It put a
pale brown at sea level, darkened through green, returned to brown in the
uplands, and lightened again at the top. Repeated hues and lightness reversals
made low and high terrain easy to confuse and could perceptually distort an
ordered numeric field.

The preview must remain attractive enough for ordinary map work, but its first
job is to communicate elevation. It should also remain usable when hue
differences are reduced by colour-vision deficiency or grayscale output.

## Decision

- Replace the custom stops with entries 128–255, the land sequence, of Fabio
  Crameri's `oleron` Scientific Colour Map 8.0.
- Map zero elevation to dark green and the configured elevation ceiling to pale
  buff, interpolating through the complete 128-sample table.
- Keep the elevation tint perceptually ordered. Brown is reserved for uplands;
  it no longer appears at sea level.
- Apply the existing subtle hillshade after tinting. Hillshade communicates
  local form while colour communicates elevation.
- Build the UI legend from the renderer's palette rather than duplicating
  colour literals.
- Record `oleron-land@scm-8.0` in exported PNG metadata.
- Vendor only the small numeric colour table and its MIT attribution. Do not
  add Matplotlib or `cmcrameri` as a runtime dependency solely to load one
  fixed palette.

## Options considered

### Repair the hand-built terrain colours

This could remove the repeated browns, but proving perceptual ordering and
colour-vision-deficiency behavior would become project-owned colour science.

### Use a generic sequential scientific ramp

Palettes such as `batlow` or `viridis` provide strong analytical ordering, but
their hues are less immediately legible as conventional land elevation. They
remain good candidates for a future scientific-inspection preset.

### Use Oleron's land sequence

This combines an ordered, accessible scientific design with conventional
green-lowland, ochre-upland, pale-summit semantics. Its sea/land split also
matches the workbench's zero-metre coastline and transparent ocean.

## Consequences

- Low and high terrain have unambiguous, visibly different endpoints.
- The tint remains readable through a monotonic lightness cue even when its
  green-to-brown hue change is difficult to distinguish.
- The palette indicates elevation only. It must not be interpreted as biome,
  exposed rock, or snow cover.
- Changing the elevation ceiling changes the metres represented by each colour,
  but the same DEM and settings continue to render reproducibly.
- Existing PNG previews will look different when regenerated. Authoritative
  Float32 elevation values and authored constraints are unchanged.
- Additional display presets remain separate future work.

## Validation

- A dense 1,025-sample test verifies strictly increasing relative luminance.
- Tests verify distinct low-green and pale-high endpoints, legend direction,
  and the exported palette identifier.
- The normal terrain test suite continues to verify transparency and PNG
  provenance metadata.
