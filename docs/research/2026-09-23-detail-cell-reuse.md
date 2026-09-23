# Bounded detail-cell reuse - 2026-09-23

Status: implemented and measured. Extends the
[verified-parent experiment](2026-09-23-verified-parent-detail.md) under
[ADR-0062](../adr/0062-reuse-bounded-detail-cell-support.md).

## Scope and exactness

One prepared detail context now retains at most 4,096 scalar cell records:
protection, amplitude and the reference/detailed moments. Least-recently-used
eviction or explicit clearing only causes recomputation. No probe grids or
delivered rasters remain in the cache. Context creation/replacement starts empty;
capacity zero provides an uncached control. This is one completed slice of the
broader prepared-parent/result cache backlog, not a whole-application memory bound.

The baseline regression reproduced 12,427 unnecessary ground probes when a
previously sampled eight-by-eight-cell window was requested at finer density.
The optimized regression forbids those calls while checking exact shared ground,
amplitudes and moments. Additional tests cover overlapping windows, changed
amplitude settings, tiny-cache eviction, clearing, failed-probe retry and warm
publication. Cache state must not alter any numeric array or evidence field.

The numeric algorithm and schemas are unchanged. Build source hashes change
normally. `probe_samples` remains the fixed support represented by each artifact,
including cached support, rather than a history-dependent work counter. Cache
counts belong only to operational inspection and benchmark reports.

## Method

Linux x86_64, CPython 3.14.7, NumPy 2.5.3, Shapely 2.1.2 / GEOS 3.13.1,
Pillow 12.3.0 and Rasterio 1.5.1. Public `example`, `regional` and `water` parents
used seed 42, 65 longest-side nodes and two detail bands; the added residual
budget was 40 m. Parent builds, full replay, protection preparation, hashing and
exports are excluded from the sampling timings.

The sequence covers a fixed eight-by-eight-cell window with a halo: cold
refinement 8, zoom to 16, overlap shifted one cell in both axes, repeat, a distant
window and revisit. Each buffered request intersects 100 parent cells; together
they address 219 distinct cells. The water case deliberately retains its heavily
protected window as a control rather than selecting successful detail.

Three repetitions alternate the order of zero, 128 and 4,096 cache capacities
within one process. All 162 samples match exactly across capacities, repetition
and eviction in all numeric arrays, request metadata and deterministic evidence.
The reproduction commands are in the [benchmark guide](../../benchmarks/README.md#fixed-cell-preparation-reuse).

## Results

Median time for the complete six-request sampling sequence, seconds (range of
three repetitions):

| Public parent | Uncached | 128 cells | 4,096 cells | Default reduction |
|---|---:|---:|---:|---:|
| Example | 0.655 (0.654-0.666) | 0.470 (0.464-0.485) | 0.419 (0.419-0.421) | 36.0% |
| Regional | 0.503 (0.500-0.637) | 0.333 (0.328-0.334) | 0.285 (0.285-0.288) | 43.4% |
| Water | 0.214 (0.210-0.230) | 0.208 (0.207-0.213) | 0.207 (0.206-0.214) | 3.1% |

These are local sampling observations, not fresh-process or end-to-end build
speedups. The water timing ranges overlap. Its original window is fully protected
and performs no ground probes, so only repeated protection queries are avoided.
Its distant window has ten eligible cells and 2,890 represented probes.

For the two land cases, a fully cached repeat falls from 0.091 to 0.027 seconds
and from 0.078 to 0.021 seconds respectively. The cold default-cache requests
remain close to uncached: 0.092 versus 0.091 seconds, and 0.079 versus 0.079.
Caching does not remove requested reference-field evaluation, residual application
or bound checks, which explains the smaller gain at the denser zoom level.

The default retains 219 entries at the end of the sequence. The 128-cell variant
never exceeds 128 entries, evicts 91 on visiting the distant window, and retains
28 hits on revisit while recomputing the other 72. All three variants reproduce
the same revisited artifact data. Regression tests additionally fill the maximum
4,096-entry cache beyond capacity and check its bound after every insertion.

No process-memory improvement is claimed: the cache adds bounded scalar storage.
Full prepared-parent geometry/routing, sampling scratch and output arrays still
need their own lifecycle and memory budgets. This implementation is for serial
Python callers retaining one detail context; separate CLI invocations start cold.
It does not enable automatic workbench jobs or resolve experimental visual,
spectral and finer-hydrology acceptance.

## Local evidence identities

Generated artifacts stay untracked under `artifacts/`. The measurements above
come from `detail-cache-reuse.json`; parents and child comparisons are in
`detail-cache-parents/`. The report records all parent IDs and per-step output
hashes.

- Package source SHA-256: `6b0892ec2b4496ba47db9e951a61f56f11568aec31e61a5e84a827bffa9502ec`
- Benchmark source SHA-256: `13373a136ac37727e6af896efb66284e127685d79e7b7fc1db0de6ba079359c8`
- Measurement JSON SHA-256: `9c9860b09aa14b91f90b535e5cb6dbda4203fbacea130b14658aad43161b0e8d`

## Validation

- Full Python 3.14 suite: 1,070 passed; 25 desktop tests skipped because no display
  was available. The system Python's missing Tk 8.6 library was extracted to a
  temporary directory for this run; Tcl settings tests executed successfully.
- Ruff and strict Pyright: passed.
- Changed documentation: 351 local links resolved; `git diff --check` passed.
- Three public parent builds, nine nested detail outputs and 162 reuse/control
  samples completed. Cache history preserves every measured numeric/evidence
  identity; the warm-export regression also preserves every artifact byte.

Generated builds and measurement JSON are excluded from the commit.
