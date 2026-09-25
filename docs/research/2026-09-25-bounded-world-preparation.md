# Bounded world preparation — 2026-09-25

This follows the [SVG interpretation fixes](2026-09-25-world-import-corrections.md).
The remaining failure was strict topology validation: export rounding and valid
same-owner duplicate fills still prevented a complete world from being saved.
[ADR-0072](../adr/0072-bound-world-source-imperfections.md) records the revised
contract; the [world guide](../terrain-worlds.md) explains the workflow.

## Delivered

Derived coverage now clips tiny polar overflow, counts same-continent shared land
once and resolves narrowly bounded cross-continent border overlaps. Original SVG,
source features, names, assignments and frame stay unchanged. Shared area is
allocated deterministically and counted once. Redundant source shapes retain their
identity and role, including when they contribute no independent area.

The editor provides an Adjustments tab with selectable source highlighting and
measured areas. Input changes clear stale reports. Open, validation and save
recompute the report; CLI inspection prints it. The public schema and example
require `preparation: bounded-world-v1`, separately from SVG parsing identity.
No old-format migration is introduced.

Linear tolerance is `1e-5` of the shorter source-frame dimension. Foreign overlap
must fit both boundary buffers, at most `1e-4` of each involved shape, and the
same cumulative foreign-overlap budget per shape. These are declared product
bounds, not a universal model of export error. Deep overlaps, contained foreign
islands, excessive rounding and entirely outside land remain actionable errors.

## Validation

The 85 focused world tests pass, covering scale/offset invariance, both poles,
exact source/frame retention, disjoint union conservation, area accounting,
contained/shared same-owner shapes, genuine foreign conflicts, aggregate budgets,
seams/holes, reorder determinism, save/reopen and real Tk selection/invalidation.
The final repository suite passes 1,384 tests with one expected skip for the
isolated scientific reference environment (407.23 seconds). Repository-wide Ruff
and strict Pyright pass. Changed documentation links and the complete inventory
are checked: 170 Markdown documents plus one legal notice.

A private 185-shape, nine-continent source now validates and saves with four
reported adjustments. One edge exceeded its native frame by about 0.001921 source
units; two foreign border overlaps were about 0.023104 and 0.005712 square source
units; a contained same-owner shape duplicated about 8.632229 square source units.
All source IDs and assignments survive reopening. Native documents and exported
SVG are retained unchanged. A real Tk capture verifies the complete world and
readable adjustment details; private geometry/names/previews stay outside the repo.

Preparation after parsing took about 0.184 seconds on this machine; SVG import
was about 2.5 seconds. These observations are not a performance guarantee or a
comparison of scientific terrain engines. Union-versus-summed planar area differs
only by floating-point accumulation noise (about 4.7e-10 square source units).

## Remaining work

Zoom-to-conflict and broader high-precision/native export comparisons remain in
TODO. The current list highlights original shapes; it does not edit them or
render a separate prepared-border overlay. Partial drafts, cancellation and
world context remain at their existing gates. WC1 should consume this prepared
coverage and its identity to avoid reintroducing overlap double-counting.
