# Examples

Examples are small, public, reproducible projects intended for learning,
documentation, integration tests, and performance comparisons.

Do not copy private campaign maps here. Every generated example artifact must be
rebuildable, and large outputs should remain outside Git.

## Terrain

[`terrain/example.dmterrain.json`](terrain/example.dmterrain.json) is a complete
versioned project that references
[`terrain/coastline.svg`](terrain/coastline.svg), a synthetic closed vector
object containing no campaign geography. Open the JSON to restore settings and
authored constraints, or import the SVG alone to begin a fresh project.

The example always uses the current project format and named stage seeds.
Update it with implementation changes; do not keep legacy variants.

The [landform region example](terrain/landform-regions.dmterrain.json) adds four
soft polygon recipes to the public terrain coastline. See the
[region guide](../docs/terrain-regions.md) for controls and limitations.


The [authored-water example](terrain/basin-water.dmterrain.json) adds a lake and
a dry-basin footprint, preserving their ground while exporting water separately.
It demonstrates closed-basin retention and review.

The [connected-outlet example](terrain/connected-outlet.dmterrain.json) adds an
explicit valley reaching the coast. Its eligible lake outlet transfers captured
area downstream while isolated dry pockets retain their contributions.

The [flat-outlet example](terrain/flat-outlet.dmterrain.json) uses a zero-relief
plateau, shorter coastal transition and narrower height influences. Its exact
Float32 flats exercise internal routing with exits, including paths to lower
closed pits. Basin details separates resolved flat samples from those that
reach connected water. This synthetic scene tests routing, not lake stability.

The [shoreline-gap example](terrain/shoreline-gap.dmterrain.json) adds a narrow
zero-height point on the connected example's lake boundary. Its coarse outlet
path remains clear and detects no uncontrolled opening, but finer boundary
samples reveal the gap. The outlet stays blocked and orange review dots locate
the low ground. This demonstrates a real generated feature, not a painted mask.

The [narrow-shoreline-gap example](terrain/narrow-shoreline-gap.dmterrain.json)
reduces that height point's influence radius to 200 m. Fixed quarter-grid probes
miss the opening entirely; local feature-guided probes now detect it and retain
the lake's captured area. It uses the same public coast and a 750 m imposed level.
