# ADR-0057: Display water at the appropriate scale

- Status: Accepted; sampled-lake display implemented, river/local-generation integration planned
- Date: 2026-09-17
- Extends: [ADR-0048](0048-keep-zoom-driven-detail-generation.md)

## Context

The author requires distant views to show only the largest bodies of water.
Small rivers should become visible when zooming into substantially finer local
generation. Enlarging a coarse drainage raster cannot deliver that behavior.
Current rendered water consists of sampled authored lakes; planned D8 channels
and connected-outlet lines are diagnostic evidence, not validated river products.

## Decision

Separate the completeness of generated water from its cartographic visibility.
Retain all numeric water, ground and routing data irrespective of zoom. Use
screen size rather than fixed zoom multipliers: display importance must account
for the geographic extent and actual output dimensions. Diagnostic reviews and
authored instruction handles stay accessible at every scale.

### Implemented lake display

The renderer caches the area of each four-connected pool in the delivered wet
mask. Corner-touching pixels remain separate for display. This classification
is neither physical connectivity nor the finer internal lake/outlet review.
It preserves dry islands and does not promote an entire authored footprint,
which can contain several disconnected pools, to one large visible lake.

Pool area is measured in source-image pixels, then multiplied by both display
axis scale factors. A pool at or below 9 output pixels squared is hidden. A
smoothstep fade reaches full blue opacity at 36 pixels squared. These are
provisional cartographic thresholds, not scientific minimum lake sizes. The
underlying ground relief shows through when water is suppressed. Narrow visible
shorelines remain limited by the delivered grid; no extra shoreline geometry
or water is synthesized. Oceans and unclassified SVG water gaps are unchanged.

Classify whole pools before cropping the viewport. Moving a large lake partly
offscreen must not make its remaining sliver disappear. Cache areas per result
and render only canvas-sized arrays on navigation. Rasterio's existing
[connected-region extraction and rasterization](https://rasterio.readthedocs.io/en/stable/api/rasterio.features.html)
operate on a binary thematic mask; no new dependency is introduced. Preparation
memory depends on pool boundary complexity and must still be measured for very
fragmented, large rasters. The persistent area image uses four bytes per source
pixel when water exists; dry results need no water cache.

The same rule applies to full-map cartographic PNG exports at their native output
size. Current viewport zoom does not change an export. PNG text identifies
`sampled-pool-screen-area@1`; the palette and numeric build algorithms are
unchanged. Scientific elevation shows ground without lake tint. Numeric NPY,
GeoTIFF, water archives, diagnostics and build schemas do not change.

The workbench shows display km/px and the coarser of its ground x/y sample
spacings. Both describe the retained generation, including when authored scale
changes make it stale. Existing samples may be magnified; no new local detail is
claimed by this display change.

### Planned river and local-generation contract

1. Give derived river reaches stable identity, connected downstream topology,
   source resolution and explicit size evidence. Contributing area or stream
   order may rank importance, but neither is an implemented discharge or channel
   width model. Define and validate that model before claiming physical widths.
2. Select coarse water using screen footprint and the accepted river size
   model. Preserve downstream trunk continuity when hiding smaller tributaries;
   do not independently drop isolated edges of a selected river. Inherit lake
   identity and whole-body importance across local windows.
3. A closer view requests an immutable, parent-conditioned regional result at
   finer terrain **and hydrology** spacing. Define adequacy thresholds against
   feature width/shoreline sampling, as well as overlap/downsample tolerances,
   inherited upstream flow, fixed parent outlets and budget limits. Extra DEM
   pixels with the same coarse process graph are insufficient.
4. Reveal newly generated small rivers only when that result is ready and meets
   those criteria. Until then keep the existing coarse result visible and show
   its current resolution. Returning to an area or changing request order must
   reproduce the same water and avoid boundary gaps or disappearing trunk rivers.
5. Validate overview/local transitions using public multi-scale fixtures: major
   lakes and trunks retained, small streams absent in distant views, resolved
   tributaries appearing nearby, stable neighboring/overlapping windows and
   no upstream-flow loss. Measure threshold transitions, latency and memory.

The detail algorithm, river-width/runoff model, numeric resolution thresholds,
automatic request trigger and bounded cache/cancellation workflow remain open.
This decision adds the required behavior and its evidence gates; it does not
mark regional generation or a physical river network as implemented.

## Validation

Regression coverage checks pool separation, dry islands, monotone fade, both
axis scales, whole-pool classification during pan, fixed-canvas allocation,
equivalent raster extents, scientific ground, immutable water/DEM/routing and
native-size PNG metadata. Real Tk coverage exercises water layers, zoom, style
switches, export and stale-reference scale readout. Public visual/performance
observations are recorded in the [display check](../research/2026-09-17-water-display-scale.md).
