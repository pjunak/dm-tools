# Selective terrain sampling — 2026-09-05

Status: **implemented Python optimization with local validation**. This follows
the [language assessment](2026-09-05-language-and-performance.md) and covers the
first profiling/R45 slice in [TODO](../../TODO.md). It does not change terrain
semantics, introduce a solver or complete the broader profiling roadmap.

## Change and numerical boundary

Delivered elevation and canonical diagnostic sampling now classify land first.
Water-only chunks return zero without evaluating the field; mixed chunks
evaluate land coordinates and scatter results back into the original shape.
Entirely land-covered chunks keep rectangular evaluation. The public DEM still
uses NaN outside land.

The pointwise evaluator is separate from masking and scattering. Its operations
must remain independent of neighboring output samples. Automatic routing still
uses its complete canonical grid, and downstream profiles are prepared before
point evaluation. Skipping water in those neighborhood-dependent stages would
be a different change and is not part of this implementation.

Project schemas, algorithms, parameters, seeds, coordinates and constraint rules
are unchanged. Existing algorithm IDs remain appropriate because the field's
mathematical definition is unchanged; the installed-source fingerprint records
the implementation change. Exact equality below applies to the exercised
runtime/cases, not to every platform or floating-point implementation.

## Repeatable measurements

The new [benchmark harness](../../benchmarks/README.md) measures public and
synthetic cases in fresh processes. Both batches used:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.terrain --resolution 768 2048 --seed 42 --repeats 3 --output artifacts/NEW-REPORT.json
```

Windows 11 / AMD64, CPython 3.14.7, NumPy 2.5.2, Shapely 2.1.2, GEOS 3.13.1,
Pillow 12.3.0 and svgelements 1.9.6 were identical between batches. No tests ran
concurrently with benchmarks. Other host activity and CPU behavior were not
controlled, so these are local measurements rather than performance guarantees.

Generation includes canonical drainage diagnostics but excludes imports,
fixture loading, delivered-surface quality, rendering and disk export. Memory
is median process peak resident memory through generation, including native
allocations, imports and fixture preparation; it is not incremental allocation.

| Case | Longest dimension | Before median, s | After median, s | Before peak, MiB | After peak, MiB |
|---|---:|---:|---:|---:|---:|
| Public example | 768 | 1.231 | 1.114 | 89.3 | 90.7 |
| Public example | 2,048 | 7.158 | 6.196 | 171.3 | 173.9 |
| Square | 768 | 1.404 | 1.417 | 91.6 | 91.6 |
| Square | 2,048 | 7.023 | 7.418 | 180.4 | 180.3 |
| Archipelago | 768 | 3.601 | 2.233 | 91.5 | 82.6 |
| Archipelago | 2,048 | 24.942 | 14.378 | 180.2 | 151.3 |
| Authored square | 768 | 1.939 | 1.968 | 101.8 | 101.5 |
| Authored square | 2,048 | 13.037 | 11.142 | 207.3 | 207.4 |

At 2,048 pixels the archipelago was about 42% faster and used about 16% less
peak resident memory. Before times were 24.942/26.365/24.004 seconds; after
times were 12.985/14.379/14.378 seconds. About 52.5% of its samples are land.
The public example is about 83.8% land: its duration improved about 13%, but
peak memory increased slightly. Compression/scattering creates temporary
arrays, so memory reduction is not universal.

Do not attribute the authored-square timing improvement to skipped ocean work:
it has no ocean samples. The square's separate batches suggested a 5.6%
slowdown. An interleaved follow-up checked that concern within one process
after a 64-pixel warm-up, using the square at 2,048 pixels/seed 42. It alternated
selective/dense/dense/selective/selective/dense evaluation. Selective times were
6.865/6.808/6.678 seconds; dense times were 6.932/6.917/6.645 seconds. Medians
were 6.808 and 6.917 seconds, with identical DEM hashes. The earlier all-land
slowdown was not reproduced; no material all-land speedup is claimed either.
This follow-up uses a different method from the fresh-process table.

Local uncommitted reports are `artifacts/performance-before-20260905.json` and
`artifacts/performance-after-20260905.json`. They retain every repeat, timings,
memory, numerical identities and source/runtime fingerprints. Before package
source SHA-256 is
`74ff044aea58a57fca24818b73b63ef3b9f025103903d2479eeb6eb7d13e278e`;
after is `ee8c968c3c1c85ad8669e2c75c7b22b114fed217ecbc6175e6bbb1de246ac139`.

## Rejected candidate

An exact STRtree boundary-piece probe used 87,552 points on the public example
and its 227 boundary vertices. Direct GEOS distance took 0.1174 seconds.
Indexed queries using pieces of 1/8/32/128 segments took
0.3574/0.2734/0.2632/0.1725 seconds, plus index-build costs. All distance arrays
matched exactly. This single probe ruled out adopting the index for this
workload; benefits on more complex coasts remain untested. See the
[STRtree API](https://shapely.readthedocs.io/en/stable/strtree.html).

## Validation and remaining work

- All 24 paired before/after runs have identical input hashes, elevation/mask/
  coordinate hashes, quality summaries and drainage diagnostics.
- Differential tests compare selective and dense evaluation across two seeds,
  simple and irregular coasts, islands, inland water and authored structures,
  including structures on the irregular mainland.
- Tests also cover water-only short-circuiting, coastline zero elevation, NaN
  inland water, nested shared samples, fresh-process benchmark repeatability,
  OS peak-memory reporting and output overwrite refusal.
- Ruff, strict Pyright (including benchmark code), and all 112 tests passed on
  Windows. No external numerical engine or new dependency was added.

Next foundations include world/grid and independent stage-seed contracts,
broader quality/refinement fixtures, export timing and agreed performance
budgets. Noise fusion and native kernels remain measured follow-ups. Linux/
macOS memory branches and interactive UI performance were not exercised here.
