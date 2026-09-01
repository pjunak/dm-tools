# Tests

The test suite will be organized around observable contracts:

- unit tests for domain invariants and seed derivation;
- contract tests for versioned schemas and adapters;
- integration tests for small end-to-end terrain builds; and
- deterministic regression tests using compact, purpose-built fixtures.

Prefer numeric assertions and invariants over large binary golden files.
