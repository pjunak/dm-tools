# Elevation colour-ramp research — 2026-09-03

**Status:** Retained for the scientific inspection style; superseded as the
everyday default by ADR-0011.

## Question

What default colour ramp lets a person read relative elevation reliably while
still looking like terrain, including with colour-vision deficiency or a
grayscale display?

There is no universally best ramp for every map. A purely analytical DEM view,
a printed atlas, and an illustrated fantasy map have different priorities. The
best scientific-inspection view for this workbench is therefore a
scientifically ordered topographic ramp; the everyday cartographic style is a
separate display choice.

## Why the previous ramp was confusing

The previous custom ramp began with pale tan at sea level, became dark green,
returned to tan and dark brown through the uplands, and then became pale again
at the summit. Its lightness reversed more than once, and similar brown hues
appeared near opposite parts of the elevation range. A reader could not infer
"higher" consistently from either hue or brightness.

Elevation above sea level is ordered scalar data. ColorBrewer's cartographic
guidance classifies this as a sequential-map problem, for which ordered
lightness is the primary cue. Crameri, Shephard, and Heron further show that
uneven perceptual gradients can exaggerate some numeric intervals and hide
others, and that colour maps should remain readable for people with
colour-vision deficiencies and in black and white.

## Selected scientific palette

Use the **land half of Fabio Crameri's `oleron` Scientific Colour Map 8.0**.
`oleron` is the suite's special surface-topography map. Its full form has
separate sequential halves for bathymetry and land, separated at sea level.
The workbench makes ocean transparent, so entries 128–255 provide exactly the
part needed here.

The land sequence moves in one visual direction:

1. sea level and lowlands: dark green;
2. lower and middle terrain: green to olive;
3. uplands: ochre and light brown; and
4. highest terrain: pale rock/buff.

The complete 128-sample lookup table is retained instead of reconstructing the
ramp from a few hand-picked RGB stops. This preserves the designed progression
without adding Matplotlib or `cmcrameri` as runtime dependencies. The table is
MIT licensed and is recorded in the dependency and asset register.

## Rendering contract

- `0 m` maps to the first land colour and the configured elevation ceiling maps
  to the last colour.
- Intermediate heights interpolate between adjacent samples in the supplied
  lookup table.
- The base tint has strictly increasing relative luminance. Hue provides
  intuitive terrain character, but lightness remains the redundant ordered
  cue if hues are difficult to distinguish.
- Fixed hillshade is applied after the elevation tint. It intentionally changes
  local brightness to reveal slope orientation, while the underlying tint
  remains the elevation key.
- Exported PNG metadata records the palette identifier so derived images remain
  reproducible.

## Important limitations

- Green means low elevation, not vegetation. Pale summits mean high elevation,
  not guaranteed snow. Biome and climate layers must remain separate.
- The ramp is normalized against the configured elevation ceiling, not against
  the current raster's minimum and maximum. This keeps colours stable between
  reruns with the same settings and avoids a small outlier remapping every
  other height.
- Colour is not a substitute for exact measurements. Cursor readouts, contours,
  and a numeric legend remain the right tools for precise elevation inspection.
- A future display-preset feature should offer a neutral analytical sequence,
  unshaded tint, hillshade alone, and decorative cartographic treatments
  without changing the authoritative DEM.

## Sources

- Fabio Crameri, Grace E. Shephard, and Philip J. Heron,
  [*The misuse of colour in science communication*](https://www.nature.com/articles/s41467-020-19160-7),
  *Nature Communications* 11, 5444 (2020).
- Fabio Crameri,
  [Scientific Colour Maps](https://www.fabiocrameri.ch/colourmaps/) and the
  [palette catalogue](https://www.fabiocrameri.ch/colourpalettes/).
- Cynthia Brewer and Mark Harrower,
  [ColorBrewer 2.0 sequential-scheme guidance](https://colorbrewer2.org/learnmore/schemes.html).
- Crameri colour data as packaged by `cmcrameri`,
  [`oleron.txt`](https://github.com/callumrollo/cmcrameri/blob/main/cmcrameri/cmaps/oleron.txt)
  and [MIT license](https://github.com/callumrollo/cmcrameri/blob/main/LICENSE.txt).
