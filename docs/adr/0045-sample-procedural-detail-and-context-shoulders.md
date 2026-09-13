# ADR-0045: Sample procedural detail and context shoulders

- Status: Accepted
- Date: 2026-09-13
- Extends: ADR-0040 and ADR-0044

## Context

The first finished-field convergence matrix found procedural crests almost
389 m above existing probes and a missed context shoulder outside its point
core corridor. Regional boundary guidance alone cannot inspect those features.
Noise-cell spacing and the evaluator's context scales provide inexpensive
prepared metadata for choosing more representative stations.

## Decision

Add a physical density guide alongside geometry/transition guides. Global
spacing is half the finest active value-noise lattice cell:
`largest_feature_km / 2**detail_levels`. Include it for nonzero global variability
and for ridge/valley width variation even when base variability is zero.
For each nonzero-relief region, apply
`feature_size_km / 2**max(2, detail_levels)` only inside that polygon. Regional
recipes always use at least two macro octaves; rotated mountain stretching
lengthens one axis while the unstretched axis determines this scale. A flat
region adds no regional noise guide, but does not cancel the global guide.

Share context radius factors with the existing field evaluator. Use the maximum
structure radius (1.18 times nominal) and the actual attached absolute-point
radius (0.45 times nominal) when preparing shoulder extents. Narrow contexts
request context/4 spacing in conservative twice-context-radius corridors.
Broad contexts retain baseline spacing and add one interior closest approach
to the complete normalized point/line within twice the context radius. Avoid
per-part buffers for that broad case. Relative attached points act through their
parent profile and do not create independent local guidance.

Keep all existing baseline stations, authored-core and regional-transition
requirements. Use strict containment and disjointness checks before constructing regional
intersections; strictly interior segments retain their exact 0-to-1 interval.
Boundary tangencies still use clipping, preserving re-entrant/hole contact
stations even when there is no gap in the covered path. Merge
overlaps before counting, preserve exact Float32 evaluation,
and apply the shared policy to every shoreline/contact/downstream/wet/dry
profile. Do not change terrain, authored inputs, incision limits, capture,
hydraulic head definitions or transfer gates.

Keep the 65536 whole-profile, 262144 whole-network and 4096 evaluation-batch
limits. Do not coarsen or accept a prefix after budget exhaustion. Higher detail
can therefore leave an entire dry network unresolved while verified wet flow
survives. Set the public flat-routing example to five detail octaves; retain its
six-octave variant as an actual budget-exhaustion regression, alongside forced
budget tests. This example setting change deliberately changes its field.

Record `feature-guided-float32-water-checks@4`. Project v5, build v16, diagnostic
fields and array layouts remain current. Water/outflow gate identifiers remain
@10/@8: the independently recorded sampling identifier owns station policy.
Add no compatibility path, runtime dependency or native rewrite.

## Validation and limits

The [measured report](../research/2026-09-13-detail-and-context-sampling.md)
compares nested and shifted real-field samples, global and regional detail,
context shoulders and overlapping influences, including oblique paths. Controls
remove only the new guidance on the same field. Fixed-input terrain/capture
hashes, complete budgets, deterministic evidence and area conservation remain
required. Report fresh-process runtime separately from prepared-stage timings.

Half a lattice cell is a sampling scale, not a spectral cutoff or an error bound.
Finite reference extrema can still miss peaks, particularly in blended features;
Gaussian tails extend outside finite corridors and one broad-context closest
approach does not identify every longitudinal extremum. This does not certify
continuous passage, off-grid two-dimensional connectivity or stable lake levels.

## Budget correction - 2026-09-13

The network-limit statement above incorrectly generalized the dry-network cap.
The unchanged runtime limits are 65,536 stations per profile, **65,536 per wet
network**, and 262,144 per dry network; evaluation batches remain 4,096.
[ADR-0046](0046-forecast-water-sampling-budgets.md) corrects this documentation error. No sampling cap or reported
measurement has changed as part of this correction.
