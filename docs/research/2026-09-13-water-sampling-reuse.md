# Exact water-sampling reuse - 2026-09-13

Status: implemented and validated. This follows
[the documentation audit](../maintenance/2026-09-13-documentation-and-research-status.md)
and the [dry-collection baseline](2026-09-11-dry-collection-paths.md).

## Change and preserved behavior

Each immutable sampling feature now prepares its normalized point/line parts
once. Previously every profile segment normalized and split the same geometry.
A connected-lake dry network repeated that work for 16,413 links.

Within one profile/network call, ground evaluation also reuses identical pairs
of Float64 coordinate bytes, restoring every requested station in original order.
The connected example retains all 105,901 station occurrences while evaluating
73,281 distinct positions, a 30.8% reduction. Signed zero and neighbouring
Float64 coordinates stay distinct. No cache persists across calls or builds.

The callback represents a pointwise Float32 field. A sampler whose value depends
on batch membership/order is not valid for this reuse or the existing chunked
terrain evaluator. No coordinate rounding, interpolation, approximate distance
field, feature index or new dependency was introduced.

Logical station counts, radius/4 refinement, complete profile/network budgets,
canonical endpoint checks, link/path barriers, area conservation and every
exported evidence record are preserved. A ten-station network with nine distinct
positions still fails a nine-station budget before any evaluation. Existing wet
and dry budget regressions exercise that distinction.

No schema or numeric algorithm identity changes: this optimizes existing
`feature-guided-float32-water-checks@2` behavior. Builds still record changed
source identity; source/manifest hashes are expected to change even when terrain
and diagnostics do not. No compatibility branch or old sampler is shipped.

## Measurements

Windows / CPython 3.14.7 / NumPy 2.5.2 / Shapely 2.1.2. All runs were serial;
correctness tests ran separately. Measurements use public/synthetic fixtures,
768-pixel delivered resolution and seed 42. Exports are excluded from generation
measurements.

First, the regular fresh-process harness ran eight cases with three repetitions
before and after: authored, archipelago, regional, outlet, flat, dry, internal
and narrow. All 27 numeric hashes, input hashes and full quality/drainage/channel/
water/area evidence matched in every pair. Unaffected controls also became
9-16% faster between batches, so the apparent 19-20% water-scene gain from those
separate batches is not attributed entirely to this patch.

A second comparison alternated reference and optimized order in fresh workers
for three repetitions. Reference workers injected the saved pre-change feature
preparation and sampling functions, including feature construction. Both variants
used the current identical generator, project settings and dependency runtime.
All array and complete diagnostic identities matched between each pair.

| Case | Reference median (range), seconds | Optimized median (range), seconds | Reduction |
|---|---:|---:|---:|
| Regional control | 1.569 (1.551-1.587) | 1.578 (1.563-1.579) | -0.6% |
| Connected outlet | 2.616 (2.594-2.663) | 2.360 (2.340-2.366) | 9.8% |
| Flat outlet | 2.663 (2.656-2.688) | 2.461 (2.394-2.551) | 7.6% |
| Dry barrier | 2.702 (2.678-2.765) | 2.407 (2.400-2.413) | 10.9% |

The regional control's ranges overlap. These are representative local timings,
not a platform-wide speed guarantee. Process peak memory through generation was
approximately 140-141 MiB for the water scenes in both variants, and 135-136 MiB
for the control. These high-water marks include interpreter/import/preparation
cost and do not prove that reuse has zero scratch allocation. Large many-feature,
many-lake and 4096-pixel workloads remain unmeasured here.

A separate alternating prepared-stage comparison isolated the dry review with
identical already-prepared terrain and three repeats per variant:

| Dry review | Reference | Prepared parts only | Unique ground only | Combined |
|---|---:|---:|---:|---:|
| Connected outlet | 0.913 s | 0.752 s | 0.887 s | 0.669 s |
| Flat outlet | 1.128 s | 0.853 s | 1.005 s | 0.855 s |
| Dry barrier | 1.114 s | 0.907 s | 1.015 s | 0.811 s |

The combined median reduction is 24-27%. Preparation, routing, rendering and I/O
outside this stage are not included. The profiler that motivated preparation
reuse recorded 16,413 feature-window calls and 32,826 LineString constructions
in the connected case; instrumented durations were not used as speed claims.

## Validation

- Focused water sampling, feature, wet-link and dry-link tests: 55 passed.
- New regressions cover duplicate evaluation across batches, exact signed-zero/
  neighbouring-coordinate identity, strided inputs, station reconstruction,
  changed samplers without stale cached values and empty networks.
- Existing endpoint mismatch, complete-budget, alternate-path, cumulative-rise,
  feature-order/reversal and immutable replacement tests remain active.
- 250 additional old/new plans with points, repeated line vertices, multiple
  crossings and three-vertex profiles matched all plan fields and station bytes.
- Eight-case before/after and four-case alternating comparisons matched all 27
  numeric products plus full quality, drainage, channel-context, water-review and
  contributing-area evidence.
- Full repository gates: 415 tests passed in 202.44 s; Ruff passed; strict
  Pyright reported zero errors/warnings.
- The public dry-barrier project built through the CLI. Its completion manifest
  passed the current build-v16 schema; all 13 output sizes/hashes were verified.
  Every output file, including both previews, GeoTIFF, all numeric archives and
  the complete 9.9 MB diagnostic file, is byte-identical to the prior public
  build. The completion manifest records the new runtime source identity.
  Rasterio reads match NPY bytes and the land mask. Basin area-balance error is
  -9.31e-10 square kilometres, unchanged.
- 388 local links (including five heading anchors) across all 93 Markdown
  documents passed; `git diff --check` passed. No UI flow changed, so no new
  visible desktop or external GIS acceptance was performed.

Local evidence is ignored under `artifacts/`: `water-reuse-before-20260913.json`,
`water-reuse-after-20260913.json`, `water-reuse-stage-comparison-20260913.json`,
`water-reuse-interleaved-20260913.json`, `water-reuse-summary-20260913.json` and
`water-reuse-build-validation-20260913.json`. The public build is in
`artifacts/water-reuse-dry-build-20260913/`.
The regular harness command is:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.terrain --case authored archipelago regional outlet flat dry internal narrow --resolution 768 --seed 42 --repeats 3 --output artifacts/water-reuse-comparison.json
```

Use a new report name. The alternating experiment uses a local comparison script
and a saved pre-change source snapshot; the tracked runtime contains only the
optimized implementation. Git parent `5c2cd9c` provides the reference runtime
for reproducing the ordinary before/after harness.

## Next work

1. Measure procedural extrema, regional transitions and authored context tails
   across finer/shifted probes. Core guidance still supplies no error bound.
2. Define controlling-sill/storage assumptions, then compatible acyclic lake
   chains. Do not use faster review to justify new hydraulic claims.
3. Profile many-constraint/lake scenes and diagnostic serialization before
   feature indexing, shared-path caches, larger budgets or a native rewrite.
4. Continue direct per-vertex profiles, explicit passes and asymmetric sides
   under the current [strategy](../strategy/README.md).

[TODO](../../TODO.md) retains all partial and future research directions.
