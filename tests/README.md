# Tests

The test suite will be organized around observable contracts:

- unit tests for domain invariants and seed derivation;
- contract tests for versioned schemas and adapters;
- integration tests for small end-to-end terrain builds; and
- deterministic regression tests using compact, purpose-built fixtures.

Prefer numeric assertions and invariants over large binary golden files.

The current terrain suite specifically verifies that nested resolutions retain
identical masks and Float32 elevations at shared world-coordinate samples. It
verifies multipart SVG import, adjacent-land dissolution, near-touching seam
repair, islands, retained enclosed water, and rejection of cross-water lines. It
also verifies that soft terrain-brush strength is monotonic, can raise or lower
the base, preserves sea level, and survives preview metadata export.
Absolute and relative elevation modes are tested separately, including relative
peaks on ridges, relative valley incision, per-mode validation, deterministic
automatic MFD accumulation, D8 centreline concentration, downstream valley
width, floor-detail suppression, nested resolutions, and preservation of the
underlying relief field. Canonical drainage diagnostics have planar-outlet and
known-depression fixtures covering direct connectivity, significant fill depth,
fill volume, non-mutation, metadata, and resolution-independent summaries.
Project contract tests cover every current constraint kind and per-tool setting,
relative coastline paths, strict schema-version handling, and SVG hash mismatch
detection on both load and save.
The first quantitative terrain-quality fixture models two ridge peaks and a
lower pass. It checks exact anchors, interval overshoot, saddle geometry,
constraint-order independence, conflicting hard anchors, and nested-resolution
equality. Equivalent relative-profile fixtures check signed ridge relief,
shallower and deeper valley sections, single application of attached points,
structure-kind preservation, and the same ordering and refinement invariants.
