# ADR-0081: Blend adjoining landform regions without background seams

- Status: accepted
- Date: 2026-09-27
- Supersedes the weighting rule in [ADR-0030](0030-author-regional-landforms.md)
  and [ADR-0031](0031-bound-incision-by-regional-relief.md).
- Extends [ADR-0080](0080-transfer-geological-landform-guidance.md).

## Problem and decision

Inward-only weights are zero on both sides of a shared recipe border. This
reintroduces unrelated background elevation and incision limits inside a fully
assigned geological partition. Keep the region inputs and procedural carriers;
replace the composition rule in a separate `pipeline/landform_weights.py` module.

Dissolve equal controls before numeric preparation, including direct terrain
regions. Use each connected polygon of the union as an independent coverage
domain. Preserve its empty holes and gaps; neither point contacts nor nearby
disconnected components create blending connections.

For a sample, let `S(z)` be cubic smoothstep of `z` clamped to [0, 1], `s_i` the
signed boundary distance (positive inside recipe i), `t_i` its transition in km,
and `d` the distance to the coverage boundary. Define:

~~~text
core_i = S(s_i / t_i)
halo_i = S((1 + s_i / t_i) / 2)
remaining = 1 - max(core_i)
raw_i = core_i + remaining * halo_i
weight_i = raw_i / sum(raw) * S(d / t_i)
background_weight = 1 - sum(weight)
~~~

Only samples inside that coverage domain participate. The raw denominator is
positive there: some recipe contains the point, giving at least half halo
strength unless another core already has strength one. Weights are nonnegative
and sum to at most one. A single region retains its original inward fade exactly.
Fully established interiors exclude recipes outside their polygons; overlapping
interiors retain normalized contributions. Shared boundaries retain participating
recipes instead of background, except where the coverage itself fades outward.

Equal-control dissolving avoids duplicate or partition-dependent weight. World
priority is resolved before this soft composition, so blank overrides remain
unassigned holes. Explicit enclaves blend at their borders and retain their own
full-strength interior. Controls remain guidance, not hard elevation footprints.

Use the same weights for macro/full relief and automatic incision limits. Keep
hard heights, coasts and authored features downstream. Queries depend on metric
coordinates and canonical region order, not the output grid or query chunks.

## Integration and identity

Mountain crest screens and local procedural-density probes must include the
new support across adjacent recipe borders. Conservative sampling bounds may
overestimate support; exact distances define actual weights. Expand benchmark
cell cut-limit bounds too, or they can permit a cut larger than the native
blended limit. The range/lowland fixture advances to
`two-catchment-range-lowland@2`; its older measurements remain historical.

The production identity becomes `regional-landforms@4`. No serialized input
field changes, dependency additions, compatibility mode or DEM editing is needed.

## Evidence and limits

The [comparison report](../research/2026-09-27-shared-landform-blending.md) records
a fixed public world, numeric seam controls and the rejected distance-only kernel.
The latter leaked high terrain into an enclave's established lowland interior;
the core term is necessary for the chosen authoring contract.

This is procedural composition, not physical uplift, erosion or accepted terrain
realism. Distance fields and maximum/core selection can have derivative kinks.
Smooth weights do not bound the slope caused by large neighboring height
differences. Narrow regions may lack an established interior. Keep connected
range/pass/lowland structure and slope/support feedback on the quality plan.
