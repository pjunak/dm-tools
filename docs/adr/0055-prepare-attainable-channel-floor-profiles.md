# ADR-0055: Prepare attainable channel-floor profiles

- Status: Accepted and implemented
- Date: 2026-09-17
- Extends: ADR-0052; no project or build-schema change

## Context

A straight floor target can demand more incision than the local ceiling allows.
Cutting down toward that line before an unremovable obstacle creates an extra
dip and a larger downstream climb. An unfillable source pit has the converse
problem: a higher downstream target can require climbing out of that pit.

The regional seed-7 edge 9958 -> 9702 illustrates both the opportunity and the
limit. Its sampled climb was about 85.77 m. Even the deepest legal cut leaves
a sampled crest about 50.93 m above its fixed upstream node. More cutting alone
cannot solve the route within the existing budget. See the
[diagnosis and comparison](../research/2026-09-17-attainable-channel-floors.md).

## Decision

Prepare finite floor guidance after the canonical routing, incision, suppression
and cut ceilings have been computed. Keep those products unchanged. For each
selected undirected cardinal edge or unambiguous diagonal with nonincreasing
floor pins in the receiver direction, sample 17 equally spaced positions.
Prepare at most 256 edges per batch, independently of delivered resolution.

Use the same pre-constraint macro and residual detail as final evaluation, with
reconstructed detail suppression. At each observed position, define:

```text
upper = max(macro + retained_detail, 0)
lower = max(macro - min(bilinear_cut_ceiling, macro) + retained_detail, 0)
```

Pin both endpoint intervals to the existing canonical floors. In downstream
order, form the suffix maximum of `lower` and the prefix minimum of `upper`.
Clamp the original linear target between those two envelopes:

```text
target = max(suffix_max(lower), min(linear_target, prefix_min(upper)))
```

The downstream lower envelope prevents avoidable cutting before an obstacle;
the upstream upper envelope carries an unfillable source depression downstream.
Where these envelopes overlap, they admit a nonincreasing sampled target. Where
they conflict, retain the obstacle target as guidance and let actual source/cut
bounds prevail. The algorithm neither fills terrain above its uncut source nor
increases a cut ceiling to force a route. A conflict remains unresolved.

Store only profiles differing from the linear target, with four grid edge-ID
maps and sparse target rows. Retain owned read-only arrays. Share the existing
vectorized PCHIP slope calculation with bounded grid reconstruction; do not
change its arithmetic. Interpolate targets with range-bounded cubic segments,
then apply the existing corridor weights, endpoint tapers and junction blend.
Reapply the exact local cut ceiling during every point evaluation. Canonical
nodes and cells without changed profile guidance retain their prior behavior.

An unavailable station on sea or a retained basin omits that complete profile;
do not accept a partial prefix or turn missing ground into zero. Invalid finite
land-height contracts fail preparation. Upward endpoint pairs keep the existing
local target: this increment does not adjust canonical nodes. The final exact
retention masks and authored constraints still apply in their existing order.

Record generator `coastline-constraint-terrain@14` and automatic valleys
`regional-budget-mfd-d8-valleys@12`. No new public setting, stochastic stage,
dependency, legacy mode or manual output-editing operation is introduced.

## Validation and limits

Test attainable and conflicting intervals, both propagation directions, all
D8 orientations, fixed pins, source/cut limits, unavailable profiles, malformed
samples, sparse ownership, cubic range/derivative behavior, query and preparation
batch independence, unchanged canonical ground and the seed-7 regression.
Compare public channel profiles, full numeric builds, water outcomes, rendering
and fresh-process runtime against the previous commit.

Seventeen stations do not bound unseen detail or prove continuous clearance.
Envelope feasibility concerns sampled pre-constraint targets, not completed
rivers. Pointwise clipping, endpoint tapers, overlapping corridors and later
authored constraints can retain climbs. Whole-route changes to pins, route
alternatives, lake/retention transitions, channel turns and physically justified
widths remain separate work. Keep every authored anchor and current cut budget
authoritative when addressing those cases.
