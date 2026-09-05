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

[`terrain/named-seeds.dmterrain.json`](terrain/named-seeds.dmterrain.json) uses
the same public coastline with explicit version-2 named stage seeds. Its terrain
intentionally differs from the original example with the same master seed.
See the [seed contract](../docs/terrain-seeds.md).
