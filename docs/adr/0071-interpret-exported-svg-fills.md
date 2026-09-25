# ADR-0071: Interpret exported SVG labels and filled paths

- Status: Accepted
- Date: 2026-09-25
- Amends: [ADR-0070](0070-retain-world-source-and-workspaces.md), SVG acceptance
  and reconstructed inspection identity only.

## Context

Normal drawing exports can contain an external DOCTYPE, original layer names in
vendor namespaces, globally unique numbered element IDs, anonymous transform
groups and self-intersecting closed paths. Rejecting all declarations, using only
older labels, or requiring every SVG ring to be a simple polygon loses valid
source geometry and semantic continent ownership.

## Decision

The world adapter accepts ordinary SVG external DOCTYPE metadata without fetching
or interpreting the referenced DTD. Expat validates the declaration and rejects
internal subsets/custom entities. Its first-element byte offset identifies the
prolog to omit from the derived parse copy; a second parse without the DTD rejects
unresolved references, including attributes that Expat can otherwise omit.
Original UTF-8 source text and its hash remain untouched.

Recognise current Affinity and Serif namespace labels before generated XML IDs.
Keep named hierarchy and transform effects, but do not invent names for anonymous
groups. The semantic ancestor immediately above `Land Shapes` owns that layer;
internal geometry clusters cannot introduce continent owners. Suggestions remain
explicit and undoable. Do not guess meaning by stripping numeric suffixes from
arbitrary authored names.

Flatten paths at the existing source-space tolerance. Node their linework and
polygonize faces, then use the original directed segments to compute nonzero or
even-odd membership. Self-intersections and retraced segments are valid SVG input;
a simple-polygon validity check is not a substitute for fill semantics. No buffer,
snap, coastline simplification or cross-shape dissolve is introduced. Open,
unsupported clipped/masked and empty-filled land still needs explicit resolution.

Bump reconstructed-source identity to `retained-svg-v2`, updating the current
schema and example together. Reject old identities; do not add save migration.
Import issues and exclusion counts are visible. Validation errors carry exact
feature IDs so the editor selects the affected shapes; messages include ancestry,
bounds or overlap measurements. The domain error has no Tk/Shapely dependency.

## Consequences and limits

All original source text remains authoritative. A self-crossing shape may produce
several filled components without changing source identity. Inspection geometry
still approximates curves. Strict world bounds and cross-shape overlap checks
remain; export rounding and genuine duplicate fills require visible source review.
This change does not introduce native Affinity import, automatic geometry repair,
draft saves, world-context generation or a new dependency.

The public regressions cover declaration retention/non-resolution, malicious or
unresolved entities, UTF-8 offsets, namespaced metadata, wrapper hierarchy, crossing
lobes, retraced winding, holes and UI issue selection. See the
[implementation report](../research/2026-09-25-world-import-corrections.md).

## References

- [SVG 2 fill rules](https://www.w3.org/TR/SVG2/painting.html#FillRuleProperty)
  define membership for self-crossing and compound paths.
- [Python Expat handlers](https://docs.python.org/3/library/pyexpat.html)
  document DOCTYPE events, byte offsets and parameter-entity parsing controls.
