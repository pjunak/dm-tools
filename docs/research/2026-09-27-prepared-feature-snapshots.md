# Prepared terrain snapshots and bounded queries

Measured 2026-09-27 against `72fc369` plus this implementation. This turns the
[short feature-preservation probe](2026-09-27-feature-preserving-terrain-delivery.md)
into a reproducible experiment under `benchmarks/evolution`. The application,
public build schemas and authoritative Float32 DEM contract remain unchanged.

## Outcome

The new reader reopens both the prepared valley field and its complete network
without regenerating them. All 575 dense bank sections, common-grid Float32
heights and existing quality measurements match the original exactly in four
matched cases. Each retains four captured heads, no interior sinks and its hard
heights, protected divide, cap/no-fill limits and longitudinal profiles. The
bilinear raster control still fails 267 / 251 / 238 / 238 dense sections.

The result is **passed on this fixture only**, with `production_eligible: false`.
Three background resolutions and a quarter turn share the same physical
landscape; they do not establish general-angle or held-out quality. No new
landforms, aging, groundwater, world coupling or editor controls are added.

## Implementation boundary

- `feature_surface.py` owns detached, read-only prepared arrays, including source,
  caps, hard targets, bed segments, mouth geometry and graph receivers. The buffers
  are backed by immutable bytes; an array view cannot re-enable writing. Settings,
  grid and head records remain frozen values. Original preparation arrays can
  change without changing the captured surface.
- `feature_archive.py` writes a new snapshot directory containing `fields.npz`
  and `manifest.json`. Only the current experimental format is accepted. Numeric
  payloads precede the completion manifest; an interrupted publication cannot
  reopen as complete. Existing output directories are never overwritten.
- `feature_comparison.py` runs the matched four-case experiment, separately
  measuring reopened features and rejected raster delivery. It publishes numeric
  witnesses, paired figures, provenance and the quality decision. Execution
  failure produces `incomplete.json`, not a successful comparison record.

The manifest declares metric frame, grid, model identifiers, fixed/fresh source
mode, hard targets, protected rectangle, physical settings and head records.
Source mode and field names retain their existing roles: fresh relief is a
generated hypothesis, fixed relief is a fixed source, pins are final hard heights,
and the rectangle/zero coast remain protected. The stored graph is prepared
geometry; loading never relocates it or rewrites authored inputs.

An input-parent digest covers this fixture's pre-layout source, original graph,
hard heights, native limits and protected bounds. Surface identity additionally
covers its prepared data and settings. Producer package/benchmark source hashes
and Python/NumPy versions are retained. File, array and manifest hashes detect
inconsistency; they establish neither authenticity nor physical correctness.
An optional expected surface identity lets a caller reject the wrong snapshot.

## Guarded loading and query contract

Loading rejects unknown fields/formats/models/frames, duplicate JSON keys,
nonfinite or boolean quantities, invalid counts, incomplete files, mismatched
hashes and linked input files. The manifest is capped at 256 KiB, the numeric
archive at 8 MiB. The existing product numeric reader enforces exact ZIP members,
bounded decompression and exact NPY v1 shape, dtype, storage order and payload
length before allocating. Pickle and object arrays are not accepted.

This experiment retains the existing limits of 256 graph nodes, 2,048 profile
segments and 16 hard-height pins. Semantic checks verify in-domain graph and hard
coordinates, source/cap grids, finite array shapes, model/settings compatibility,
rectangle and head records, and preserved hard heights. Prepared segments are
reconstructed geometrically from the stored graph and declared physical spacing
for exact consistency checking; bed elevations are not regenerated. Supported
mouths still require the fixture's straight west or south zero-height coast.
A structurally valid snapshot can still fail terrain-quality checks.

Height queries accept finite metric coordinates within the closed source domain,
including scalar, vector, broadcast and empty queries. Out-of-domain samples are
rejected rather than silently clamped. Work is limited to 262,144 query points,
processed in batches of at most 8,192. Input and broadcast sizes are checked
before Float64 conversion; complex, string and boolean coordinates are rejected.
Returns are Float32 heights from the
prepared field, not interpolation of an exported DEM.

For each matched case, 2,048 deterministic arbitrary points retain bitwise values
under shuffling and different batches. Four overlapping tiles retain exact full-
window values and both horizontal/vertical halo agreement. Coarser samples agree
at identical coordinates. These are queries of one frozen surface, **not**
independently generated detail tiles, anti-aliased downsampling or proof of
parent-cell mean preservation. The unit test additionally checks one-point batches.

## Measured evidence

| Background spacing / orientation | Numeric archive | Write and reopen | Dense failures / 575 | Captured heads | Sinks | Raster-control failures |
|---|---:|---:|---:|---:|---:|---:|
| 1,000 m | 9,299 bytes | 0.052 s | 0 | 4/4 | 0 | 267 |
| 500 m | 15,640 bytes | 0.072 s | 0 | 4/4 | 0 | 251 |
| 250 m | 41,823 bytes | 0.065 s | 0 | 4/4 | 0 | 238 |
| 250 m, quarter turn | 41,892 bytes | 0.066 s | 0 | 4/4 | 0 | 238 |

Archive sizes exclude the JSON manifest. Maximum dense inward excursion remains
0.006195 m under the unchanged 1 cm gate; there are 202 samples per section.
Routing retains the previous 125 m raw-ground D8 check and 1,000 m outlet tolerance.
No imposed receivers or hidden fill are introduced. Common sampled ground agrees
exactly under the quarter turn. No broader angle result follows from this.

The standalone comparison took **26.273 s**, with **169.05 MiB** peak resident
memory and no concurrent test suite. Repeat manifests and numeric archives match
byte-for-byte in this runtime. Compression byte identity across different zlib
versions is not promised. These fixture timings and sizes are not world-scale
performance forecasts.

Local evidence: `artifacts/feature-delivery-final-20260927`. All saved numeric
and file hashes were verified. The 250 m bank/routing plots were visually reviewed:
the reopened profiles preserve the local banks while the raster still rises near
some intended beds. The simple fixture does not demonstrate final visual realism.

Benchmark source SHA-256:
`023783e00036cd3695c1838453009f97f96ca448566b353c0105e2ed9b0f2d3a`.
Product package-source SHA-256 remains
`609434a82e7be0ecef9be7e91b81986e61750b036f2873282d33693b3f0a9bda`.

## Reproduction and validation

Run in the existing Python 3.14 environment from the repository root:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.evolution.feature_comparison --output artifacts/my-feature-snapshots
.\.venv\Scripts\python.exe -m pytest tests/test_feature_surface.py -q
```

The comparison writes an `index.html` with figures and links to numeric decisions.
`--no-figures` skips image production only; it retains numerical quality gates.
It does not produce an app-openable terrain build or promise old snapshot support.

The 50 focused regressions pass in 33.60 s, including the complete comparison.
Repository Ruff and Pyright checks pass. Tests cover roundtrip ownership and
identity, query order/batching/overlaps, malformed JSON, spoofed counts, oversized
compressed members, duplicate ZIP entries, huge NPY shape headers, object arrays,
nonfinite/negative capacities, mismatched network geometry and interrupted output.
An ownership review found the writer's returned metadata initially shared its
frame dictionary; returning a fresh frame and a regression remove that mutation
path. Two initial malformed-JSON tests failed to inject their intended corruption
because they assumed compact whitespace; their corrected inputs now exercise the
actual rejection paths. Neither issue changed the generated valley field.

After the user's approval, the full repository suite passed **1,800 tests with
one expected skip in 524.70 s (8 minutes 45 seconds)**, within the agreed 15-minute
stop limit. The skipped Landlab reference test requires the separate scientific
reference environment; no new skip was added. The local run log and exit status
are retained under `artifacts/feature-full-suite-20260927`. Tested package and
benchmark source hashes match the standalone evidence above. Documentation
validation passed for 738 local links and anchors across 11 changed Markdown
files, all 196 Markdown inventory entries plus one legal notice, and whitespace.

## Next acceptance work

1. Add a small held-out geometry set: tight bends, short tributaries, confluences,
   hard-target proximity and oblique layouts within explicitly supported bounds.
   Do not call a quarter turn arbitrary-angle coverage. Keep failed native/fixed
   controls distinct from the larger fresh-construction envelope.
2. Address irregular coast/mouth domains explicitly before applying the prototype
   to a continent. Any patch, strip or constrained-mesh replacement needs its own
   join, bound and actual-ground evidence; it cannot inherit the bilinear proof.
3. Test real parent/detail filtering and shared hydrology. Current overlap tests
   validate one saved field only. Compare means, terrain structure and flow across
   resolutions before enabling zoom enrichment or hiding detail in a coarse cache.
4. If these gates pass, record an ADR and change numeric authority, identities,
   schemas and consumers together. Until then, keep this as a Python benchmark
   component. Resume B2 history and LE3/WC2 only after accepted construction and
   delivery, with no post-generation sculpting or legacy loaders.

Consult before longer tests; use an explicit estimate and stop condition. This
batch's terrain comparison remained short. A general backend rewrite or a new
scientific dependency is not needed for the next bounded experiment.
