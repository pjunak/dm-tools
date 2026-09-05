# Terrain performance checks

These repository-only tools measure the installed Python engine without adding
runtime dependencies or changing authored projects. Run them from the repository
root with its development environment; they are not installed as `dmtools`
commands.

```powershell
.\.venv\Scripts\python.exe -m benchmarks.terrain --resolution 768 2048 --seed 42 --repeats 3 --output artifacts/performance.json
```

The output must be a new file. Reports are generated artifacts and must not be
committed. A failed run retains an incomplete file without a valid completed
report. The runner checks that repeated inputs produce identical numeric
outputs/diagnostics and that generator source, dependencies and benchmark code
have not changed during the run. Do not edit engine or benchmark Python files
while measuring them, and avoid concurrent tests or other heavy workloads.

## Cases

| Case | Purpose |
|---|---|
| `example` | Existing public SVG project and its settings; no authored constraints |
| `square` | Four-edge land boundary; every grid sample is land |
| `archipelago` | Synthetic irregular coast, three islands and inland water; 960 boundary vertices |
| `authored` | Square land with a ridge, peak/pass anchors, relative valley and relative brush |

Select cases and multiple resolutions/seeds explicitly:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.terrain --case example archipelago --resolution 768 --seed 42 20260902 --repeats 3 --output artifacts/coasts.json
```

The synthetic cases are workload probes, not a complete terrain-realism fixture
suite. A 4,096-pixel run can be requested separately; it is intentionally absent
from the default to keep routine measurements bounded. Regional refinement and
process-spacing experiments still need their own fixtures.

## What is measured

Each repetition starts a new Python subprocess, with no warm-up generation:

- fixture/project loading;
- generation wall time and process CPU time;
- intervals between the generator's existing progress labels;
- delivered-surface quality measurements;
- cartographic and scientific rendering separately; and
- total worker wall time, including startup, imports and result serialization.

Progress labels are diagnostic grouping, not a new public pipeline-stage API.
Canonical drainage diagnostics remain within generation time. Output quality
and rendering are measured afterward. Disk export, PNG encoding and publication
are excluded; these results must not be called full-build timings. Report
serialization and child-process communication are included only in worker wall
time. Deterministic hashes identify elevations, masks and both coordinate axes;
quality and drainage summaries are also retained.

Peak resident memory comes from the OS and includes native-library allocations.
The generation measurement is the process high-water mark up to generation's
completion; the products measurement is the high-water mark through quality
and rendering. Both include imports and fixture preparation. They are neither
current memory usage nor sums of per-stage allocations, and their difference
is not a stage's allocation count. Windows uses `GetProcessMemoryInfo`; Linux
and macOS use `getrusage` with platform-specific units. Unsupported platforms
report null. Windows is the currently exercised platform. See the
[Windows counter definitions](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters).

## Comparing revisions

Keep before/after reports from identical arguments. Match rows by case,
resolution and seed, then require identical input hashes, array hashes,
drainage and quality for an optimization that promises unchanged results.
Compare medians and ranges; retain Python, NumPy, GEOS and platform identity.
Source hashes are expected to differ between implementations. A speed change
without matching inputs or numerical validation is not an accepted result.

Run benchmarks separately from the correctness suite. Do not add machine-
dependent timing thresholds to ordinary tests. Use a separate profiler run to
locate expensive functions; profiler timings are not interchangeable with the
unprofiled measurements. These cold-process measurements also differ from the
earlier exploratory repeated generations within one warmed Python process.

The [language assessment](../docs/research/2026-09-05-language-and-performance.md)
records why optimization begins in Python and the evidence required before a
native-language migration.
