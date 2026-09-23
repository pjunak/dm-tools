# Verified parent-region sessions - 2026-09-23

Status: implemented and measured under
[ADR-0063](../adr/0063-reuse-verified-parent-region-sessions.md). This extends
[bounded cell support](2026-09-23-detail-cell-reuse.md) into a reusable application
operation with automatic freshness checks and explicit resource ownership.

## Change and correctness

`ParentRegionSession.write(...)` retains one loaded/prepared parent and one detail
context. Complete numeric results use a 64 MiB default byte budget, configurable
from zero through 256 MiB, plus a 32-entry limit. Eviction is least-recently-used;
oversized results bypass retention without reducing requested work. Arrays remain
private, and callers receive new artifact paths. Clearing discards cached work;
closing releases session-owned parent, detail and result references.

Byte accounting includes complete backing NumPy allocations, including large bases
behind small views, and deduplicates storage within each result. Object arrays,
writable arrays and unknown foreign buffers bypass retention. Python metadata,
parent/geometry storage and active scratch are outside this numeric payload budget;
this is not a complete process-memory limit.

The aligned request and detail settings form the result key inside a parent/runtime
session. Differently requested metric bounds can reuse identical aligned samples,
while each manifest records the original bounds for its write. Every operation,
including a cache hit, verifies parent hashes and runtime. Source/runtime drift
or unavailable runtime verification closes the session before further reuse.
Completion remains last; valid numeric work can survive an export failure for a
retry to a different output directory. Failed numeric evaluation is not cached.

The original single-call API and CLI now use temporary sessions with result
retention disabled. No formula, seed, schema or numeric algorithm changes.
Current source identity still requires rebuilding old parents.

## Measurement method

Linux x86_64, CPython 3.14.7, NumPy 2.5.3, Shapely 2.1.2 / GEOS 3.13.1,
Pillow 12.3.0 and Rasterio 1.5.1. Three public parents (`example`, `regional`,
`water`) use seed 42, 65 longest-side nodes and two detail bands. Regional writes
use the experimental 40 m residual.

The fixed six-write sequence covers cold refinement 8, zoom to 16, a one-cell
overlap, repeat, a distant window and revisit. Each core spans eight parent cells
per axis, with the normal one-cell halo. Three repetitions alternate variant
order in one process:

1. Independent application calls, each loading, replaying, generating and exporting.
2. One session retaining parent/cell preparation, with result caching disabled.
3. One session also retaining complete numeric results under the default budget.

Timing includes session setup/close, file/runtime verification, numerical work,
rendering, file writes and completion publication. The benchmark separately
rechecks output hashes after each timed write. Its own verification/report work
is excluded. Every write uses a new directory, and all 162 published artifacts
match their independent controls exactly, including complete manifest bytes.
These are serial observations, not fresh-process startup comparisons. Reproduction
commands are in the [benchmark guide](../../benchmarks/README.md#verified-session-reuse).

## Results

Median complete six-write duration in seconds (range of three repetitions):

| Public parent | Independent calls | Prepared work retained | Prepared work and results | Reduction vs independent |
|---|---:|---:|---:|---:|
| Example | 6.818 (6.734-10.087) | 1.521 (1.519-1.569) | 1.472 (1.466-1.505) | 78.4% |
| Regional | 9.422 (9.297-9.705) | 1.972 (1.929-1.980) | 1.930 (1.899-1.960) | 79.5% |
| Water | 6.193 (6.151-6.195) | 1.402 (1.388-1.469) | 1.346 (1.330-1.353) | 78.3% |

Most of the improvement comes from avoiding repeated full-parent preparation and
replay. Complete-result retention adds a smaller 2-4% median reduction over the
prepared-only sequence; the regional timing ranges overlap. A repeated artifact
write costs about 0.038-0.040 seconds with result reuse, versus 0.056-0.062 seconds
with only prepared work retained. These remaining costs include verification,
rendering and output publication, which still run on hits.

The first independent example sequence was slower than its later repetitions;
the full range is retained rather than attributing that variation to caching.
No cross-platform speed or whole-map generation improvement is claimed.

Each default session ends with four numeric results totaling **664,500 bytes**:
three smaller requests at 99,341 bytes and the denser request at 366,477 bytes.
The repeat and revisit are hits. All sessions report zero retained result bytes
after close. Correctness tests separately force real-result byte eviction and
exercise the 32-entry limit; this small benchmark does not approach 64 MiB or
measure process RSS. Complete parent/geometry and active-job admission remain
future work, along with cancellation and workbench jobs.

## Local evidence

Generated parents and comparison children are under
`artifacts/parent-session-current-parents/`. The report is
`artifacts/parent-session-results.json`, with generated session products in its
sibling directory. These generated files remain untracked.

- Package source SHA-256: `0af51d71a94e7303ce958ad149eecee4d0c9ac48898d424ca323c604ecb4caeb`
- Benchmark source SHA-256: `c02fce34257670acd543b08295d5e06be3d010cb775c3fad74e817a333aa3dfc`
- Measurement JSON SHA-256: `468e4ecb2cfe8d5e514b0ba49de38518a4c297ddd77d1e3c7aa65de1c7dc414f`

## Validation

- Full CPython 3.14.7 suite: **1,095 passed**, 25 desktop tests skipped because no
  Tk display was available. Tcl coverage ran with the local Tk library path.
- Ruff and strict Pyright: passed.
- Public parent/detail benchmark: three parents and nine nested children passed
  numeric invariants; all 162 session artifacts matched their independent controls.
- Documentation review: 382 local links resolved; `git diff --check` passed.

No workbench behavior changed. Generated parents, children and measurement JSON
remain local artifacts rather than committed fixtures.
