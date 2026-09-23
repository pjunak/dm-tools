# ADR-0063: Reuse verified parent-region sessions

- Status: Accepted
- Date: 2026-09-23
- Extends: [ADR-0061](0061-verify-parents-and-isolate-local-detail.md) and
  [ADR-0062](0062-reuse-bounded-detail-cell-support.md)

## Context

The public application operation reloads and numerically replays its parent for
each regional artifact. Pipeline callers can retain prepared fields and cell
support, but must implement their own file/runtime checks and result lifecycle.
Repeated windows still evaluate the same delivered samples. Automatic workbench
jobs need explicit ownership and freshness before retaining those resources.

## Decision

Add a serial `ParentRegionSession` application API bound to one completed parent
and its exact runtime/source identity. Validate the parent files when opening;
defer numerical replay until the first valid request. Retain that verified parent
and at most one prepared detail context. A cache miss needing different detail
settings replaces cell support while reusing parent-dependent protection geometry.

The session's `write` operation produces a new completed artifact and returns its
manifest path. Keep all retained arrays private to application generation and
export. It is not a public mutable DEM or a raw-array cache interface. Route the
existing single-request operation through a temporary session with result
retention disabled; CLI flags and artifact schemas remain unchanged.

Retain completed numeric requests in a least-recently-used result cache. Default
to 64 MiB, allow integer budgets from zero through 256 MiB, and independently cap
entry count at 32. Count complete backing NumPy allocations, including bases of
small views; deduplicate allocations within an entry. Conservatively charge each
entry independently if storage is shared across entries. Unknown foreign buffers,
object arrays and writable arrays are ineligible. Oversized results bypass the
cache without displacing useful entries. Cache limits never reduce request
sampling or change its admissibility.

The result key includes the full aligned request (parent identity, frame,
refinement, window and halo) plus detail settings or reference mode. Raw requested
bounds can share an aligned numeric window; preserve their separate original
bounds in each new manifest. Operational counters never affect artifact identity.

Check all parent product hashes and runtime before every request, including hits,
after new generation and before publication. A cached-hit progress callback can
also change source files, so check again after it and before creating output.
Parent/runtime drift closes the session and releases its parent, detail and
result references. Failed exports retain no completed manifest; their valid
numeric result may be retried to a new destination. Failed numeric evaluation is
never cached.

Expose result byte/count statistics and explicit cache clearing. Clearing releases
results and detail-cell records while preserving prepared parent work. Closing
or exiting the context manager releases all session-owned parent/detail/results.
Reject reentrant generation and lifecycle changes during a write. This is serial
ownership, not a thread-safe scheduler or a global cross-session cache.

## Limits and validation

The byte budget covers retained numeric result allocations only. One loaded and
prepared parent, complete-source geometry, bounded scalar cell support, active
sampling/rendering scratch and Python metadata have separate costs. Counting
parents and detail contexts does not certify a process-memory limit for arbitrary
geometry. Total job admission, cancellation and workbench integration remain open.

Tests cover exact uncached/cached artifact bytes, mode/settings/density keys,
rounded-bound aliases, LRU/byte/entry limits, underlying array storage, result
bypass, stale-hit rejection, failed-generation/export retry and parent release.
The [session measurements](../research/2026-09-23-parent-region-sessions.md)
compare independent calls, prepared-only sessions and sessions with results.
Terrain formulas, seed policy and numerical/schema versions are unchanged;
normal source provenance requires rebuilding parents after installing the change.
