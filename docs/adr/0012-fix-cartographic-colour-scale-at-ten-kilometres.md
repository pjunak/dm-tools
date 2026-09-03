# ADR-0012: Fix the cartographic colour scale at ten kilometres

**Status:** Accepted
**Date:** 2026-09-04
**Deciders:** Repository owner and project maintainer

## Context

The first cartographic palette normalized colours to each generation's
elevation ceiling. As a result, the highest point in a modest 4,500 m region
received the same near-white colour as a world-extreme summit. That makes
individual images locally expressive, but prevents meaningful colour
comparison between continents.

Aethelara is similar in size to Earth and may have more extreme relief. A
10,000 m highest peak is the working world-scale target. It is roughly thirteen
percent higher than Everest, so it communicates exceptional fantasy geography
without requiring an alien planetary scale.

## Decision

- Fix the cartographic colour scale to absolute elevations from 0 to 10,000 m.
- Keep green, yellow, and brown for lowlands through ordinary mountains.
- Begin dark muted red at 7,000 m, introduce progressively lighter reds above
  8,200 m, and reserve near-white for 10,000 m.
- Clamp terrain above 10,000 m to the same white endpoint.
- Keep the scientific elevation style normalized to the active generation
  ceiling so it can show relative variation across the whole local DEM.
- Keep the generation ceiling independent from the display scale. Retain its
  4,500 m default while allowing values up to 12,000 m in the UI.
- Record the colour-scale maximum in exported PNG metadata.

## Consequences

- The same elevation now has the same cartographic colour on every continent,
  supporting a stable world-map visual language.
- A typical continent with a 4,500 m ceiling no longer reaches red or white.
  Those colours visually identify genuinely exceptional terrain.
- Raising a generation ceiling changes terrain amplitude but does not remap
  existing elevations to different cartographic colours.
- The 10,000 m endpoint is a display contract and working worldbuilding
  assumption. It does not by itself establish the location or canonical exact
  height of Aethelara's highest summit.

## Validation

- Palette tests cover brown, dark red, light red, pale red, and white anchors.
- A rendering invariant verifies that changing only the generation ceiling
  leaves cartographic pixels unchanged.
- PNG tests verify the palette version and 10,000 m scale metadata.
- The scientific render test verifies that its scale metadata still follows
  the active generation ceiling.
