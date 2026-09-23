# ADR-0065: Admit regional memory estimates before allocation

- Status: Accepted
- Date: 2026-09-23
- Extends: [ADR-0063](0063-reuse-verified-parent-region-sessions.md) and
  [ADR-0064](0064-cancel-generation-at-safe-checkpoints.md)

## Context

A result-cache byte limit does not account for loading/replaying a parent,
complete-source geometry or active sampling/rendering. Future viewport requests
need an aggregate admission decision before allocation. Measurements also exposed
that the parent's bounded file reader requested its 512 MiB ceiling even for tiny
archives, causing excessive transient allocation.

## Decision

Use a nonblocking shared `RegionalMemoryBudget` for saved-parent application
sessions. Default sessions share 1024 MiB within the process; explicit pools and
CLI `--memory-mib` support caller policy. Reserve bootstrap/input/decoded-file
estimates in stages, before reading/parsing or decoding their large payloads.
Check declared product sizes before reading and request only the observed size
plus one byte, rejecting growth/shrinkage and retaining complete hash checks.

Reserve one loaded/prepared parent, one optional detail context, geometry/input
allowances and full configured numeric-cache capacity for each session's life.
Before each write, reserve the complete result plus the maximum serial stage
allowance for preparation/replay, sampling and rendering, and I/O overhead.
Cache hits still reserve export work. No waiting, implicit quality reduction,
automatic capacity expansion or eviction of another owner's data is allowed.
Use one shared thread-safe pool for related sessions; each session rejects
concurrent/reentrant mutation. Release job reservations on all exits and retained
reservations on close or invalidation. Cancellation preserves valid retained work.

STRtree protection queries must batch the cell dimension and release pair arrays
between batches. Every intersection still affects the same protected cells.
Expose estimate components and actual cache bytes separately, and keep both out
of numerical/artifact identity. Algorithms, seeds and schemas are unchanged;
package source identity still requires rebuilding saved parents after an update.

## Limits and validation

The pool admits explicit estimates, not measured process RSS. Geometry/native
allocation, Python overhead and allocator retention prevent claiming a hard memory
ceiling. Direct pipeline/whole-map/editor work and separate pools/processes are
outside this policy. Calibration at larger source/constraint scales and aggregate
application ownership must precede viewport scheduling. Do not mark the broader
total-memory roadmap item complete on the strength of this first policy.

Tests cover pre-allocation rejection, size-change detection, exact complete
numeric/output equivalence, overlapping protection batches, thread contention,
failed reservation growth, cancellation/failure/drift release and retry. A
fresh-process benchmark records native resident peaks, unique retained numeric
allocations and admitted estimates for public fixtures; see the
[usage and accounting guide](../terrain-regional-memory.md) and
[measured report](../research/2026-09-23-regional-memory-admission.md).
