# ADR-0026: Version named terrain stage seeds

**Status:** Accepted
**Date:** 2026-09-05
**Deciders:** Codex implementation within the authorized Python foundation work.

## Context

Long-lived terrain builds need random streams that do not depend on the order
or number of unrelated future processes. Existing projects pass the master
seed directly into coordinate noise. Replacing this silently changes their
geography. Python remains the iteration language; seed derivation should have
an exact portable contract ready for a later Rust implementation.

## Decision

Add a dependency-light domain seed policy, used by the actual relief evaluator
and recorded by the project/build adapters. Preserve the original behavior by
default. Offer an explicit workbench choice and a public named-seed example.

`named-stage-sha256@1` derives an unsigned 32-bit value from fixed domain bytes,
a big-endian master seed and a stable ASCII stage name. The exact encoding and
reference vectors are in the [seed contract](../terrain-seeds.md).

The current stochastic stage is `terrain.relief`. Full and macro evaluations
retain their shared field identity. Generated routing is deterministic; do not
invent unused random seeds for processes that do not consume randomness.
Future stochastic processes must declare separate stable names.

Version-1 projects/builds and their immutable schema definitions remain
supported. Explicit selection of named seeds saves version 2, requiring the
new policy. Opening either version restores its behavior; switching back to
original behavior saves version 1. Unsupported policies fail validation.
Version-2 manifests record a named stage-seed map and reuse unchanged v1
geography, runtime, product and authoring definitions through URN references.

## Options considered

| Option | Cost and maintenance consequence |
|---|---|
| Replace every seed silently | Small patch, unacceptable changes to existing projects |
| Shared mutable RNG or indexed seed spawning | Couples streams to insertion/order; poor migration boundary |
| Split full and macro seeds | Breaks their common-field relationship and changes residual semantics |
| Explicit named policy with legacy support | Selected; small domain API and explicit format compatibility cost |
| Wait for a Rust rewrite | Leaves another implicit behavior to recover later |

## Consequences

No runtime dependencies or terrain/noise equations change. The same master
under the new policy intentionally produces a different terrain realization.
Original numeric output stays compatible on the tested runtime. This change
supports future feature independence; it does not itself introduce new
landforms or claim improved physical realism.

Derivation is stateless and independent of raster shape. A 32-bit output can
collide; names are not guaranteed globally unique random values. Algorithm
and runtime fingerprints remain necessary for exact terrain reproduction.
The contract does not promise field independence when a later process changes
shared physical inputs. The original policy remains limited to old behavior.

## Validation

Reference vectors cover zero, representative seeds and the UInt32 maximum;
.NET and Python agree. Tests cover stage insertion/order, invalid masters and
names, unknown policies, project round trips with authored constraints, strict
v1/v2 schemas, repeatable headless output and workbench settings persistence.
Named generation is compared with legacy generation receiving the resolved
seed across square, archipelago and authored fixtures. Dyadic shared-node
samples and drainage diagnostics remain consistent.

All 16 saved legacy baselines matched exactly: Float32 DEM, land masks,
coordinates, canonical drainage and both rendered pixel arrays, across four
fixtures, two resolutions and two seeds. Validation is local to Windows /
CPython 3.14.7; it does not promise cross-platform terrain equality. All 174
tests, Ruff and strict Pyright passed. The Tk workbench was initialized with
a withdrawn window; both policies also passed Tcl settings round-trip tests.

## Action items

- [x] Implement named derivation and retain original-project behavior.
- [x] Publish strict version-2 contracts, a reviewable example and migration guidance.
- [x] Exercise real generation, project/build and workbench settings boundaries.
- [ ] Require separate stable names for each future stochastic process.
- [ ] Add source/world positioning and registered GeoTIFF in a later contract.
