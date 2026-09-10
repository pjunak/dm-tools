# Repository sanity and performance review - 2026-09-10

Scope: a bounded local maintenance pass before further terrain features.
Baseline: clean `main` at `2c4776d`. No authored project or geographic source was
changed. Generated benchmark reports and profiles remain ignored in `artifacts/`.

## Structure and fixes

The repository has one product package, current project/build schemas, public
examples, tests and development benchmarks. Domain and pipeline imports do not
point outward to application, file or UI modules. The domain is dependency-light;
NumPy and Shapely are current pipeline dependencies. The application operation
orchestrates numeric generation and concrete adapters. The desktop workbench
also invokes them directly; a generic adapter-port framework is not implemented.

Corrections made:

- Reject non-finite physical settings and non-integer sample/octave counts at
  the direct Python domain boundary. The JSON adapter already validates these;
  direct callers previously reached numeric generation with invalid settings.
- Emit the sampling progress label before the first chunk, so benchmark stage
  time no longer charges that chunk to routing. Remove a duplicate final clamp.
- Add the public four-region scene to the benchmark harness and include routing
  hashes and planned/final agreement in repeated-run comparisons.
- Repair eight Windows-encoded dashes in otherwise UTF-8 TODO text. Refresh
  outdated pipeline/domain documentation and completed items in the strategy.
- Ignore local CI test reports. No generated terrain, caches or reports are
  tracked, and no archive or private source was deleted.

The large files remain a maintenance concern: approximately 2,132 lines in
`ui.py`, 1,300 in `generate.py`, and 1,182 in `hydrology.py` at baseline. Line count
alone is not a defect. Extract basin/conflict diagnostics with the next hydrology
feature; separate structure profiles and workbench drawing/controls when those
features change. Avoid a directory reshuffle without a concrete ownership gain.

## Reproducible measurements

Windows 11, AMD64, CPython 3.14.7; NumPy 2.5.2, Shapely 2.1.2/GEOS 3.13.1.
Two cold subprocess repetitions per case/resolution, seed 42, no concurrent tests.
Values below are after cleanup. Times are generation medians; memory is the
maximum process high-water mark across repetitions, including imports/native
allocations. Through-products memory includes quality and both render styles;
it is not a per-stage allocation count. Different scene extents contain different
numbers of pixels, so cross-case times are not algorithm rankings.

| Case | Longest side | Generation s | Peak through generation MiB | Peak through products MiB |
|---|---:|---:|---:|---:|
| Authored square | 768 | 2.302 | 123.3 | 138.7 |
| Archipelago | 768 | 2.548 | 105.3 | 136.7 |
| Regional example | 768 | 1.597 | 130.1 | 130.1 |
| Authored square | 2048 | 11.738 | 229.8 | 537.9 |
| Archipelago | 2048 | 13.142 | 173.2 | 529.8 |
| Regional example | 2048 | 8.066 | 251.3 | 353.4 |

At 2048, shapes are 2048x2048, 2048x2040 and 1214x2048 respectively.
Before-cleanup authored/archipelago generation medians were 11.906/13.024 s;
after ranges were 11.691..11.785/13.027..13.256 s. This pass demonstrates no
material speedup. Before/after input, DEM, mask, coordinate, quality and drainage
identities all match for the eight paired runs. New routing identities and
agreement also match within each pair of repeated final runs.

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.terrain --case authored archipelago regional --resolution 768 2048 --seed 42 --repeats 2 --output artifacts/sanity-performance-20260910-after.json
```

The output path must be new; choose another name to repeat. Raw before/after
reports are `artifacts/sanity-performance-20260910-before.json` and
`artifacts/sanity-performance-20260910-after.json`.

## Bottlenecks and implications

Separate cProfile runs around generation at 2048 show:

- Archipelago: 13.693 s total; Shapely distance calls take 9.785 s (71.5%).
  Noise generation takes 1.877 s cumulatively (13.7%).
- Regional example: 8.317 s total; distance calls take 3.448 s (41.5%).
  Noise generation takes 2.220 s cumulatively (26.7%).
- Unprofiled canonical routing costs roughly 0.45..0.70 s at 2048. Raster
  evaluation takes 7.28..12.08 s. The retained routing grid is still bounded at
  257 on its longest side; increasing it requires new measurements.

Profiles are `artifacts/sanity-archipelago-20260910.prof` and
`artifacts/sanity-regional-20260910.prof`. Profiled timings are separate from
cold-process medians. Shapely distance enters native GEOS work, so translating
Python orchestration to Rust alone would not remove the dominant cost.

The first speed experiment should compare boundary-distance algorithms on
complex coasts. The [earlier STRtree probe](../research/2026-09-05-selective-terrain-sampling.md)
was slower on the simple public coast; do not adopt an index without measuring
its crossover, memory and exact numeric behavior. Noise reuse/fusion is the
second candidate. Both need equality or explicitly versioned error bounds.

The renderer allocates full Float64 RGB, gradients and surface-normal arrays.
Investigate buffer lifetimes and rendering tiles with gradient halos to reduce
memory while preserving pixels and metadata. The products high-water mark is
consistent with that source pattern; it does not isolate individual allocations.

## Implementation order and boundaries

Keep Python and the current product direction. First classify blocked planned
channels while extracting diagnostic responsibilities, then implement explicit
lake/outlet or rerouting choices under regional limits. Follow with structural
profiles and asymmetric sides, then runoff/density and regional refinement.
Performance experiments can use separate fixtures without changing those
hydrology semantics. See the [maintained strategy](../strategy/README.md).

## Validation

All 230 tests passed in 158.78 s. Ruff, strict Pyright, installed-dependency
consistency, UTF-8 decoding, local Markdown target-file checks and the scoped
import-direction check passed. Existing build/schema, anchor, sampling and
hydrology contracts remain covered. The suite's slowest individual test took
6.21 s; there was no isolated test accounting for most of its runtime.

4096-pixel runs, many-region/constraint stress, export/PNG compression timings,
interactive UI latency, other operating systems and external GIS validation
were not measured. No dependency upgrade or solver/language migration was made.
