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
| `regional` | Public four-region project, including regional relief and incision budgets |
| `water` | Authored lake/dry-basin footprints, cut protection and separate water products |
| `outlet` | Connected public lake with a reviewed route to the coast |
| `flat` | Exact internal flats, collected water and retained pits |
| `shoreline` | Narrow boundary opening missed by the canonical wet nodes |
| `narrow` | 200 m boundary feature needing local refinement |
| `downstream` | 100 m downstream height feature blocking a canonically clear route |
| `internal` | 100 m internal height feature separating a canonically connected lake |
| `dry` | 100 m dry height feature rejected before selecting a clear alternative |

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
quality, drainage, planned/final routing agreement and overlapping conflict
context summaries are also retained.
Hashes also cover receivers, channels, incision, incision limits, conflict flags
and the finished field on routing nodes. Internal basin paths, flat ranks, full-path
uphill excursions and area-transfer arrays are hashed too. Sampling now emits its label before the first chunk;
older reports charged that first chunk to the preceding routing interval.

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

The [2026-09-10 review](../docs/maintenance/2026-09-10-sanity-and-performance.md)
records earlier coast/regional bottlenecks. The
[dry-path follow-up](../docs/research/2026-09-11-dry-collection-paths.md) measures
the expanded water workload; the [current status](../docs/research/status.md)
tracks remaining performance and validation gaps.

## Water-profile convergence

```powershell
.\.venv\Scripts\python.exe -m benchmarks.water_convergence --seed 42 20260913 --repeats 2 --output artifacts/water-convergence.json
```

This separate read-only runner compares real finished-ground profiles in five
synthetic scenes: a narrow regional plateau, global procedural detail, rotated
regional detail, a point's context tail outside its core corridor, and overlapping
positive and negative points. Defaults compare 400/4000 km objects, horizontal/diagonal
canonical edges and a 64-pixel delivered raster. Protected dry footprints keep
automatic cuts from obscuring the field being studied. These are numeric
stress fixtures, not recommended authoring presets. Optional `--direction oblique`
uses a `(1, 0.37)` grid-edge vector; its endpoint is deliberately off the canonical
grid. Horizontal and diagonal remain the defaults.

Every trial preserves the complete production station set. Aligned trials
split each original interval by factors 1, 2, 4, 8, 16, 32 and 64; half-shifted
trials instead place interior probes at `(i + 0.5) / factor`, also keeping the
original endpoints. The reference uses twice the largest factor and includes
all trial stations exactly. It is a finite sampled reference, never continuous
ground truth, a GCI calculation or a hydraulic model. Extrema, greatest raw-ground
rise from an earlier minimum, witness positions, 0.01 m threshold decisions and differences
to that reference are recorded. Shared positions and Float32 values must match
byte for byte; no resampling or interpolation substitutes for field evaluation.

Use `--case`, `--scale`, `--direction`, `--resolution`, `--seed`, `--refinements`
and `--max-samples` to select an experiment. Refinements must be increasing
powers of two starting at 1 (maximum 256); the comparison cap defaults to 262144
and cannot exceed that value. The former 65536 default could not fit the full
128-fold reference after procedural guidance enlarged production profiles. Each complete trial/reference budget is checked before
allocation or evaluation. A missing reference or over-budget baseline remains
explicitly unresolved, with no error difference or accepted prefix. This
research-only cap does not change any production budget.

Reports record inputs, engine/runtime and harness source hashes, all 27 numeric
product hashes, water evidence identity, per-run time/peak process memory and
repeatability. `geometry_only` removes procedural density and context guidance
while keeping authored cores and regional transitions. `without_region_guidance`
omits polygon transition guides only; procedural density remains. Both inspect
the exact same finished field, and are research controls rather than product
settings. The runner observes the existing prepared evaluator call
and verifies that inspection leaves numeric products and water review unchanged.
No new product API is added. Each repeat is a fresh process; output files must
be new, publication is completion-last, and source changes during measurement
invalidate the run. Avoid concurrent heavy work. Results belong under ignored
`artifacts/`; the [station-policy report](../docs/research/2026-09-13-detail-and-context-sampling.md)
records the implemented guidance and remaining gaps.

### Adaptive midpoint experiment

```powershell
.\.venv\Scripts\python.exe -m benchmarks.water_convergence --seed 42 20260913 --direction horizontal diagonal oblique --repeats 2 --adaptive-tolerance 1 .1 .01 --output artifacts/adaptive-profile-matrix-final-20260913.json
```

`--adaptive-tolerance` adds midpoint-residual trials to the `current` profile;
geometry controls and uniform trials remain available. Each threshold is a
positive finite number of metres. This research experiment adds probes where
midpoint ground differs from the endpoint average. It preserves all production
stations and evaluates the entire pending wave only if it fits. The defaults
are `--adaptive-max-depth 7` (allowed 1-8) and `--adaptive-max-samples 65536`
(allowed 1-65536). Exhausted baseline, wave, depth or coordinate precision is
explicit, with no accepted partial metrics or reference comparison.

`indicator_satisfied` means only that the tested residuals passed. It does not
mean clear water, bounded extrema or a converged terrain solution. Afterwards,
a separate reference divides each original interval into
`2**(adaptive_max_depth + 1)` parts: factor 256 at default depth. It includes
all adaptive probes exactly and shares the `--max-samples` reference cap.
A reference that cannot fit remains `budget_exceeded`, and error comparisons
remain unknown. The reference never chooses the adaptive probes.

The report records visited/requested station counts, residuals, hashes, extrema,
baseline/adaptive differences against the same finite reference and
`reference_exceeds_tolerance`. That last flag compares the largest minimum,
maximum or ordered-rise discrepancy with the requested residual threshold;
it is not a hydraulic decision. Station counts include repeated path positions;
they are not unique evaluations. Timings include controls and reference work,
not just the proposed probes. Research report schema v2 records the experiment
method/source identity; product schemas and algorithm identities are unchanged.
See the [adaptive report](../docs/research/2026-09-13-adaptive-water-profile-refinement.md)
for measured benefits, false convergence and the decision to keep this heuristic
out of runtime clearance checks.
