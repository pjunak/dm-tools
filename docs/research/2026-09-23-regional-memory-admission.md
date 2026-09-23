# Regional memory admission and bounded loading

Date: 2026-09-23. Public fixtures only; no private map was used.

## Implemented scope

Saved-parent sessions now share estimated allocation budgets before staged file
loading and regional generation/export. The default pool is 1024 MiB, with
explicit caller/CLI overrides. Retained context and active work have separate
reservations; failure, cancellation and invalidation release the appropriate
owner. Detail-protection queries batch the cell dimension without discarding
intersections. See [ADR-0065](../adr/0065-admit-regional-memory-estimates.md) and
[the accounting guide](../terrain-regional-memory.md).

This is admission of engineering estimates, not a hard process RSS guarantee or
a viewport scheduler. Numerical terrain, experimental-detail status and finer
hydrology readiness are unchanged.

## Method and provenance

`benchmarks.regional_memory` launches a fresh process for each parent, mode and
refinement. Each worker opens one session and writes a cold artifact and an exact
cached repeat, including full export, then closes. It records process-lifetime
resident peaks (native allocations included), baseline peak after imports, actual
unique backing NumPy storage, cached bytes and admitted estimates. Parent builds
happen outside measured workers. No concurrent test/benchmark run was active.

The three public example, regional and water projects were rebuilt with seed 42,
two detail bands and 65 by 39 parent nodes. Each used the fixed eight-parent-cell
window from the session workload at refinement 8 and 128, producing buffered
67 by 67 and 1027 by 1027 samples. Both reference sampling and experimental detail
at 40 m were measured. One observation per combination is a memory investigation,
not a statistically supported timing comparison.

A first 12-worker run revealed an unexpected approximately 575 MiB peak even on
small windows. The bounded reader called `read(limit + 1)` with the 512 MiB
product safety ceiling. The corrected reader asks for observed file size plus
one byte, rejects size changes, and verifies declared product size before reading.
The second run repeated all 12 combinations and added four workers for an
example parent with 1025 by 607 nodes. That larger parent uses eight much smaller
physical cells; it is an ownership/loading check, not the same geographic window.

Environment: Windows 11 AMD64, CPython 3.14.7, NumPy 2.5.2, Pillow 12.3.0,
Shapely 2.1.2 / GEOS 3.13.1, Rasterio 1.5.1 / GDAL 3.12.4. Runtime identity and
runner hashes are recorded in the ignored local reports:

| Run | Package source SHA-256 | Report SHA-256 |
|---|---|---|
| Initial admission with old reader | `91f52bf1930d3f5b5467ea28480f75b1c56b84b140337f7b30f62ada1338991e` | `c9fe7a321418892ae58d5517d1da1397a87ce54c12f04a1e91110dedd77dfd94` |
| Corrected reader and batch release | `1f5851a682325c40c151cf6ae5f7d2ca4bbd7b7869c74d50693911c2e1ed8b37` | `e39ee8f82fa412c1f045e1ef212ef12887c98753207bf3b583b2333375898ba7` |

The reports are `artifacts/regional-memory-20260923.json` and
`artifacts/regional-memory-20260923-fixed.json`, with their sibling output
folders and separately built parents. Generated outputs stay untracked.
See [benchmark instructions](../../benchmarks/README.md#regional-admission-and-process-memory)
for reproducing with current-runtime public parents.

## Observations

Resident peaks below include imports and both writes; ranges span reference and
detail modes. MiB means 1,048,576 bytes. Baseline worker peaks were 62.5–63.3 MiB.

| Parent | Small window, old reader | Small window, corrected | Large window, old reader | Large window, corrected |
|---|---:|---:|---:|---:|
| Example, 65 by 39 | 574.5–574.9 MiB | 93.2–93.3 MiB | 574.7–574.8 MiB | 203.7–226.7 MiB |
| Regional, 65 by 39 | 574.5–574.6 MiB | 97.8–97.9 MiB | 574.5–575.1 MiB | 210.7–231.0 MiB |
| Water, 65 by 39 | 574.5–575.1 MiB | 97.2–97.3 MiB | 574.6 MiB | 209.8–229.9 MiB |
| Example, 1025 by 607 | Not measured | 118.9–119.0 MiB | Not measured | 211.3–235.1 MiB |

The small-fixture peak reduction is approximately 83–84%. Larger windows now
show the expected render/result-size contribution instead of being dominated by
the file reader. No wall-time speedup is claimed from these single observations.

Admitted peak estimates were 379.6–422.9 MiB across corrected workers. All measured
process peaks were below those envelopes, including imports which the pool does
not model. This is finite-fixture evidence only; it does not prove the coefficients
bound arbitrary geometry, Python/native implementations or accumulated allocator
retention. The cold-preparation allowance is deliberately generous relative to
these small fixtures and has not been tightened from this limited sample.

Decoded parent-array estimates matched actual unique allocations exactly.
Loaded-plus-prepared numeric storage was approximately 8.6 MiB for the three
small parents and 16.3 MiB for the larger parent, below its reserved numeric
allowance. Every session released all reservations on close.

All 16 corrected workers produced byte-identical cold/cached manifests and
products (32 complete exports). Comparing the 24 paired pre/post-fix exports
also found identical numeric NPZ/input JSON bytes and identical rendered pixels.
Manifest identities and PNG provenance metadata appropriately differ between
source revisions. Tests independently compare batched/unbatched protection
queries with 100 overlapping features and preserve active/protected results.

## Remaining work

Keep the broader total-memory roadmap item open. Extend evidence to maximum
parent sizes, near-limit and very skinny regional requests, dense coastal holes,
large/overlapping authored constraints, concurrent sessions/jobs, decoder/object
expansion and long-lived cache churn. Account for editor images, whole-map builds
and other retained application state before introducing a viewport scheduler.
Consider worker-process limits only if a hard ceiling becomes a product need.
Do not reduce sampling or silently change numerical quality to satisfy admission.
