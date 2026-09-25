# ADR-0072: Bound world-source imperfections in derived coverage

- Status: Accepted
- Date: 2026-09-25
- Amends: [ADR-0070](0070-retain-world-source-and-workspaces.md) and
  [ADR-0071](0071-interpret-exported-svg-fills.md), strict bounds/overlap rejection
  for the cases below only.

## Context

Normal exports can place a polar boundary just outside its declared frame or
produce a narrow overlap along a shared continent border. Authored shapes may
also duplicate land within the same semantic continent. Requiring all of these
to be manually redrawn blocks otherwise usable worlds. The user requested that
these situations be handled in the importer or source.

## Decision

Retain the original SVG bytes, hash, source features, frame and assignments.
Prepare disjoint polygonal coverage separately, under `bounded-world-v1`:

1. Permit north/south overflow up to `min(frame width, frame height) * 1e-5`
   source units. Clip it to the declared frame. Reject larger overflow and shapes
   with no in-frame land. Keep longitude wrapping and its existing extent limits.
2. Count overlapping and contained shapes within one continent once. Retain every
   feature ID and role; redundant shapes may have empty prepared coverage.
3. Permit different continents to share only a narrow border sliver: overlap must
   be entirely inside both shapes' boundary buffers at the same linear tolerance,
   and at most `1e-4` of each shape's area. The union of all foreign overlaps for
   each shape must also fit that area budget. Reject larger/deeper or contained
   foreign conflicts with their affected IDs.
4. Allocate shared coverage in deterministic order: mainland before islands,
   then larger wrapped/clipped footprint, then feature ID. Subtract higher-priority
   coverage, preserve the land union and calculate spherical area on the result.
5. Report each clipping/overlap with kind, affected IDs, source paths and planar
   area. The editor's Adjustments tab highlights those source shapes; CLI inspection
   prints the same reports. Preview geometry remains the retained source.

The linear and area thresholds are conservative product tolerances, not evidence
that every qualifying overlap came from rounding. Reports make the inference
reviewable. They do not fill gaps, remove holes, grow the frame, exclude features,
rewrite coastlines or transfer an entire foreign island to another continent.

The independent required `preparation` field records this policy alongside the
existing `retained-svg-v2` source parser. Opening/saving recomputes coverage and
reports from the embedded source. Previous snapshots require reimport; no migration
or legacy behavior is added. Future context stages must use the prepared coverage
and record both identities, rather than double-count original overlapping fills.

## Evidence and limits

Public controls check tolerance under scaling/translation, clipping at both poles,
source retention, union/area conservation, same-owner duplicates, foreign conflict
rejection, aggregate overlap budgets, holes/seams, ordering, save/reopen and real
Tk report selection/invalidation. Private source verification stays outside the
repository. See the [implementation report](../research/2026-09-25-bounded-world-preparation.md).

Large ownership conflicts still need author input. Automatic zoom to a conflict,
partial mapping saves, import cancellation and native Affinity import are separate
features. This decision does not add world context, climate or terrain generation.
