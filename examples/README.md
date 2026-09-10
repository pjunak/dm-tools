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
