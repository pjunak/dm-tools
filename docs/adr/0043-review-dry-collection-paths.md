# ADR-0043: Review dry collection paths

- Status: Accepted
- Date: 2026-09-11
- Extends: ADR-0038 and ADR-0042; replaces build v15

## Context

Water connectivity alone cannot certify the dry paths feeding it. Coarse dry
endpoints can descend across a narrow ridge, and an exact canonical flat can
hide an intervening rise. Filling terrain or preferring only lake-bound exits
would violate authored ground and closed-pit routing rules.

## Decision

Use a separate typed dry-link stage before existing flat routing. Review every
vector-contained candidate descent or exact flat in bounded batches from the
finished Float32 field. Orient unequal heads downhill; equal dry heads must pass
both directions. Remove blocked pairs symmetrically and run the existing metric
steepest-descent and Barnes-derived integer-flat rules on the remaining graph.
No change to the flat kernel or its algorithm ID is required.

Wet terminals use imposed water level. A dry-to-water profile uses
`max(ground, water level)`; a dry-to-dry profile uses ground. Reject a link whose
maximum rise from an earlier sample exceeds 0.01 m. All usable exits remain
eligible, including lower closed pits. Rejected links may alter flat distances
and redistribute area; collected area is not guaranteed to decrease.

After routing, compose complete selected head profiles in reverse flow order.
A link minimum followed by a later suffix maximum can produce a cumulative
climb missed by separate link checks. Export the full-path excursion at every
node and collect only paths within tolerance reaching reviewed water. Retain
failing donors and upstream contributions, preserving valid downstream donors.
This gate does not reroute against alternative complete-path states; such a
search remains research. The sampled terrain check does not establish hydraulic
impossibility, water storage, a stable spill level or unobserved 2D detours.

The dry network has a 262,144-requested-sample budget per eligible lake, counting
repeated endpoints. All baseline/refinement plans must fit before evaluation;
existing per-profile 65,536 and per-call 4,096 limits remain. No accepted prefix
survives failure. Dry receivers/ranks/excursions then stay empty/zero and every
dry donor remains retained, while already verified water can drain. This differs
from an unresolved wet network, which blocks the entire outlet.

Retain oriented link indices, sample provenance, worst low/crest witnesses and
blocked flags in diagnostics. Record cumulative barrier origins and export
Float64 `internal_path_uphill_m` with the existing basin-flow arrays. A retained
dry node may have an exported selected path ending in water when its cumulative
excursion fails; classification and excursion must be read together. Display up
to 12 strongest spatially separated dry crests per basin to keep review usable.

Build v16 replaces v15 without a loader or migration. Record
`authored-basin-water-review@10` and `captured-mfd-reviewed-d8-outlets@8`.
Project v5, terrain generation, original MFD capture, regional incision budgets,
height anchors, shoreline/wet/external checks and array coordinate rules remain.
No dependency or native-language runtime is added.

## Evidence and limits

A public relative height point with 100 m influence creates a 131.44 m sampled
climb between two dry nodes. A control omitting only its extra probes chooses
that link; the complete review takes a clear neighbour. Ground and captured
area are identical between reviews. Synthetic tests exercise both flat directions,
water-head clipping, closed pits, composed low/crest witnesses, budget failure,
independent full-path reconstruction and sparse-graph flat invariants.

The [measured rundown](../research/2026-09-11-dry-collection-paths.md) records
reproducibility, conservation, UI/export checks and performance. Finite profiles
still miss unsampled procedural extrema, feature context tails and off-grid
connections. Prioritize broader convergence and measured planning/evidence cost
before enlarging routing grids or replacing Python.
