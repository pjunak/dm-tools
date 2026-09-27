# ADR-0083: Preserve shared ridge crests and authored contacts

- Status: accepted
- Date: 2026-09-27
- Extends ADR-0082; changes explicit absolute ridge composition and smoothing.

## Decision

Prepare explicitly profiled absolute ridges as simple open lines with compatible
contacts. Preserve their raw intersections while applying the existing corner
smoother to the spans between them. Reuse identical shared coordinates when
reassembling spans; keep original authored inputs immutable. Do not snap gaps.

Validate resulting contacts against both profiles, with a 0.001 m height
compatibility tolerance. Fail with instruction numbers, metric position and
profile percentages when they disagree. Reject loops, self-crossings and shared
line spans with an explanation of how to express separate branches and one
shared crest. This avoids claiming an ambiguous longitudinal target.

After ordinary absolute/relative ridge guidance, blend explicit absolute crests
with rescaled inverse-square distance target shares. Keep the maximum physical
response as coverage. Each axis controls its target, including extremely close
parallel ridges whose Gaussian responses round to one. Compatible zero-distance
contacts share their agreed value. Sort ridge inputs before accumulating.

Retain sea level, later valley carving, final independent point authority,
incision budgets and generation-only editing. Relative profiles and proximity
attached points retain their prior rules. The new helper module
`pipeline/ridge_crests.py` owns topology preparation, contact checks and blending.

Advance `coastline-constraint-terrain` to **@20**. Serialized fields are unchanged:
project v8, snapshot v3, build v19 and regional samples v3 remain current.
No legacy support, new package or random stream is added.

## Evidence and limits

The [comparison report](../research/2026-09-27-shared-ridge-crests.md) records
seed/scale controls, a repaired 75 km corner gap, protected coast/budgets, editor
failure handling and saved-parent replay. Protected junctions may have sharp
turns; continuous slopes, generated branches, explicit graph editing and full
mountain/drainage realism remain open. A later valley or hard height point may
change the final ground away from a ridge's declared crest height.
