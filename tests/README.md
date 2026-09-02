# Tests

The test suite will be organized around observable contracts:

- unit tests for domain invariants and seed derivation;
- contract tests for versioned schemas and adapters;
- integration tests for small end-to-end terrain builds; and
- deterministic regression tests using compact, purpose-built fixtures.

Prefer numeric assertions and invariants over large binary golden files.

The current terrain suite specifically verifies that nested resolutions retain
identical masks and Float32 elevations at shared world-coordinate samples. It
also verifies that soft terrain-brush strength is monotonic, can raise or lower
the base, preserves sea level, and survives preview metadata export.
Absolute and relative elevation modes are tested separately, including relative
peaks on ridges, relative valley incision, per-mode validation, deterministic
nested resolutions, and preservation of the underlying relief field.
