# World SVG import corrections — 2026-09-25

This follows the [WC0 workspace batch](2026-09-25-world-source-workspace.md).
It repairs source interpretation and diagnostics, without advancing climate or
terrain generation. [ADR-0071](../adr/0071-interpret-exported-svg-fills.md) owns the
acceptance decision; the [world guide](../terrain-worlds.md) owns user workflow.

## Confirmed implementation defects

- A blanket DOCTYPE substring rejection required manual editing of normal exports.
- Only the older Serif label namespace was recognised. Numbered XML identifiers
  such as `Land-Shapes1` therefore hid semantic layer names and caused exclusions.
- Anonymous/named wrappers beneath a land layer could become invented owners.
- SVG self-intersecting closed paths were rejected as invalid simple rings before
  their actual fill rule was evaluated, leaving valid filled shapes invisible.
- Import issue/exclusion totals and geometry-conflict identities were too hard to
  discover in the editor.

## Delivered behavior

Ordinary external declarations are parsed without resolving their identifiers;
internal DTD subsets and custom references remain rejected. Original SVG text is
retained exactly, including the header. Modern Affinity/Serif and Inkscape labels
precede generated IDs, anonymous wrappers do not invent hierarchy labels, and the
owner above the semantic land layer remains responsible for nested shapes.

Sampled linework is noded and polygonized. Face membership follows directed
segment winding rather than assuming every ring is simple. Bow-tie lobes,
retraced loops, nested holes and ordinary polygons retain their SVG fill meaning.
This is fill interpretation, not a repair or dissolve operation.

The editor counts unassigned, excluded and problematic shapes; import issues are
marked and selected. World validation reports source paths/IDs and offending
bounds or overlap areas and selects the corresponding shapes for review.
A spatial index limits failed-overlap diagnostics to intersecting bounds.
The importer identity, schema and public example move together to `retained-svg-v2`.

## Validation

Public, invented fixtures cover header round trips and no external entity loading,
internal subset rejection, comments, Unicode prolog offsets, both Affinity label
namespaces, wrapper ownership, self-crossings, repeated winding and preserved holes.
Geometry diagnostics identify out-of-frame/overlapping shapes without mutating
source. Real Tk tests check issue counts, selection and failed validation handling.

The focused world suite passes 67 tests. The full application suite passes
1,366 tests with one expected skip for the isolated scientific reference
environment (306.50 seconds). Ruff and strict Pyright pass. The final error-message
adjustments were rechecked with the 67 world tests and both repository-wide static
gates. A real Tk import window was captured and visually compared with the native
source render: previously missing land is visible and ownership counts agree.
Private campaign source evidence remains outside this repository; no private
geometry, source names or generated campaign previews are public test fixtures.

## Remaining work

Export rounding can displace a polar boundary or make touching shapes overlap.
Strict validation currently rejects those discrepancies. More decimal precision
and flattened export transforms should be compared with native geometry before
accepting any bounded derived tolerance. Actual overlapping/contained objects
also need review; higher precision cannot eliminate source duplication.

The TODO retains a consolidated source-quality report and zoom-to-conflict review.
No automatic snapping, widening the world frame, polygon repair, redundant-shape
exclusion or native `.af` loader is included. Full-world context and physical
terrain acceptance remain at their existing gates.
