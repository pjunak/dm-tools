# ADR-0080: Transfer explicit geological landform guidance

- Status: accepted
- Date: 2026-09-27
- Extends: [ADR-0076](0076-author-world-geology-inputs.md) and
  [ADR-0079](0079-project-world-land-into-terrain.md)

## Context

World recipes identify geological hypotheses and priority provinces, but the
usable terrain handoff previously transferred coastlines alone. Deriving height,
uplift or erosion coefficients from geological categories or age would introduce
unreviewed assumptions. Nested provinces also require cutouts that ordinary
terrain-region inputs could not represent.

## Decision

Add an optional explicit LandformSettings value to each geological profile.
The editor offers plain, hills, plateau and mountains with editable physical-unit
controls. A blank value requests background terrain. It replaces lower-priority
guidance with the rest of the profile; it does not inherit that guidance.

At terrain creation, reread the selected recipe and verify its canonical world
identity. Resolve existing priority semantics, intersect selected physical land,
merge identical landform settings across continent labels and different ages,
and project through the same bounded custom-sphere projection as the coast.
Generate ordinary editable TerrainRegion instructions. Holes retain higher-priority
enclaves and blank overrides. Whole-region and vertex editing, rendering,
hit-testing, serialization and numerical weighting all respect those rings.

Use separate input-adapter, projection, compilation and form modules. Both world
and ordinary terrain documents share strict landform parsing. No new scientific
engine or runtime dependency is added.

Retain the original recipe and explicit-geology-landforms@1 compiler identity in
the prepared SVG. Terrain constraints become the effective inputs; subsequent
edits to them do not rewrite the original recipe. Retaining the recipe is provenance,
not a claim that later edited constraints can be reconstructed from it alone.
The existing project/source pair remains portable without the original recipe file.

Current formats become geology v2, prepared source v2 and terrain project v7.
The landform algorithm becomes regional-landforms@3 to record hole support.
Remove obsolete formats and update examples; do not add migrations.

## Consequences and limits

Coastline coordinates, membership, projection and physical scale are unchanged
by selecting a recipe. Blank recipes do not infer elevation from category or age.
Hard terrain controls still apply after procedural landform composition.

This is a usable input-to-terrain feature, not a physical geological simulation,
rough global parent, climate coupling or historical regional replay. Local projected
direction is explicit; it is not a true-bearing world field. Each selected domain
still has the existing 80-degree/hemisphere limits.

The paired preview exposes a separate limitation: inward transition weights vanish
at adjoining recipe boundaries, reintroducing generic background terrain and
producing polygon-shaped rims. This batch preserves the current regional composition
contract. Continuous shared-boundary blending is the next quality task; its acceptance
must include priorities, blank cutouts, hard heights, coast/mask and stable sampling.

Triangulating cutout regions was rejected as a design shortcut because existing
inward fades would create transitions on every artificial triangle edge. No triangle
experiment was run. Implicit category-to-height/age-to-erosion conversion was also
rejected as an input-policy shortcut, not disproved as a scientific model.

See the [implementation evidence](../research/2026-09-27-geological-landform-guidance.md).
