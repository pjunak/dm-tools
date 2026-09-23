# ADR-0062: Reuse bounded detail-cell support

- Status: Accepted
- Date: 2026-09-23
- Extends: [ADR-0061](0061-verify-parents-and-isolate-local-detail.md)

## Context

Prepared detail contexts already retain verified global terrain and protection
geometry. Every overlapping or repeated request still evaluates the same fixed
17 by 17 probes to recover cell amplitudes and reference/detailed moments. These
values depend on the immutable parent and detail settings, not the requested
window, halo or density. Repeating them adds avoidable local-generation work.

## Decision

Each prepared detail context owns a private least-recently-used cache indexed by
global parent column/row. Retain only the protection flag, amplitude and two
Float64 moments per cell. Cache protected cells too, avoiding repeated geometry
queries. Never retain probe lattices, sample arrays, geometries or references to
other parents in cache entries.

Default to 4,096 entries, matching the maximum cells in one valid request. Python
callers may choose a smaller integer capacity, including zero to disable reuse.
Evict the least recently accessed/inserted cell before exceeding the capacity.
Expose an explicit clear operation and operational hit/miss/eviction counts.
The bound is per context and concerns fixed-size scalar records, including the
bounded integer cell addresses; it is not a byte budget for complete parents,
output rasters or arbitrary numbers of live contexts.

Bind identity through context ownership: a new or dataclass-replaced context
starts with an empty cache, including when changing parent, settings or protection
geometry. No global, disk or cross-context cache is introduced. The current
caller uses a context serially. Future worker scheduling must define ownership
and total memory limits before sharing or retaining contexts automatically.

Cache absence, eviction and clearing must reproduce every numeric result and
deterministic evidence record exactly. Keep request work limits independent of
cache state. `probe_samples` counts the fixed support represented by the result,
including support reused from cache; operational counters never enter artifact
identity. Ground delivery still evaluates the requested reference samples and
checks between-probe height bounds on every request.

There is no schema, stage-seed or numerical algorithm change. Source identity
changes normally, so completed-parent loading still requires a current build.
Applications retain their parent/runtime verification duties before publication.

## Consequences and evidence

Repeated and overlapping requests can avoid fixed probes and protection queries
without changing geography, residual modes, moments or exported files. Tests
cover overlap, density, tiny-cache eviction, explicit clearing, changed settings,
failed-probe retry, exact scalar/array/evidence equality and warm publication.
The [measurement report](../research/2026-09-23-detail-cell-reuse.md) compares
uncached, bounded and eviction-pressure sequences on public parents.

Prepared-parent/result caching, total job memory, cancellation, runtime freshness
management and workbench jobs remain open. The experimental detail formula keeps
all visual, spectral and hydrological limits from ADR-0061.
