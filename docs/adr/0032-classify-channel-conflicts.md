# ADR-0032: Classify planned-channel conflicts without changing authored terrain

**Status:** Accepted
**Date:** 2026-09-10

## Decision

Move read-only basin candidates, drainage diagnostics and planned/final routing
review into `pipeline/diagnostics.py`. Flow primitives stay in `hydrology.py`.
Consumers import the current owner; no old-module compatibility aliases remain.

Review uses the same 257-longest-side routing nodes and finished Float32 values
stored as Float64. Retain existing agreement metrics, and add a typed summary
plus spatial arrays. All contexts are measured evidence; they may overlap and
must not be interpreted as mutually exclusive physical causes.

`channel_conflict_flags` is a UInt8 donor-node mask:

| Bit | Meaning on an uphill planned edge |
|---:|---|
| 1 | Receiver is more than 0.001 m above donor on finished terrain |
| 2 | Either endpoint needs more than 0.01 m filling on a finished-field Priority-Flood copy |
| 4 | Rise exceeds remaining receiver incision allowance by more than 0.001 m |
| 8 | Finished edge rise exceeds the macro-minus-incision edge delta by more than 0.001 m |
| 16 | Either endpoint lies within at least one region's inward transition |

Zero means no above-tolerance uphill planned edge at that node; it does not
certify hydrology. A bit-1-only edge is unclassified. A region boundary itself
counts when inside its polygon; overlap with a full-strength region does not
remove the transition flag. This is context, not a measured seam defect.

Additional arrays in `routing.npz` are `channel_rise_m`,
`receiver_cut_deficit_m`, `final_adjustment_rise_m` and `final_fill_depth_m`.
The first is positive rise on any planned edge, including sub-tolerance rises.
Deficit and final-adjustment arrays are zero outside above-tolerance uphill
edges. Fill depth covers all canonical land, with zero at sea; epsilon flood
steps can occur below the depression threshold. All arrays share routing-grid
coordinates and are bound to diagnostics by the existing routing archive hash.

Remaining receiver allowance is `max(incision_limit_m - incision_m, 0)`;
deficit is `max(rise - receiver_allowance, 0)`. This is an optimistic edge-local
bound: authored restoration may prevent spending the allowance, and lowering
one receiver can invalidate its next downstream edge. It is not a complete
breach depth, a recommended edit or permission to relax a regional budget.
Final-adjustment evidence combines residual detail and constraint restoration;
it cannot attribute a conflict to one particular authored feature.

The build review adds a context panel; visual priority is transition, final
adjustment, depression, then cut limit. The numeric mask retains all flags.
The workbench retains thin blue/red review edges and adds context counts to
completion status. No source project, DEM or receiver is modified by review.

## Numerical defect found during validation

Near zero elevation, Priority-Flood's representable steps can underflow in
slope conversion and exponentiation. MFD now rescales relative drops only when
all outgoing weights underflow. D8 compares normalized drops if all candidate
physical slopes underflow to zero. Preserve strict lower-height receivers,
stable neighbor order and physical slopes; do not add an arbitrary fill depth.
This fixes invalid contributing area and disconnected conditioned flat grids.

Identities become generator `coastline-constraint-terrain@5`, automatic valleys
`regional-budget-mfd-d8-valleys@4`, canonical drainage diagnostics
`canonical-d8-priority-flood-diagnostics@3`, and routing agreement
`planned-final-d8-agreement@2`. Context is `planned-channel-context@1`, recorded
in `diagnostics.json`. Current project 4 and build manifest 6 structures remain;
new derived arrays are identified by diagnostics and product hashes.

## Validation and limits

Analytical fixtures cover each context, overlapping flags, receiver allowance,
slope-change accounting, unclassified rises, tolerance, ocean nodata, terminals
and non-mutation. Existing tests cover nested sampling, anchor authority,
regional order and numeric build reproducibility. Zero-height and scaled-small
surfaces test finite, conserved flow and strict receiver descent.

See the [research and measurements](../research/2026-09-10-depressions-and-channel-conflicts.md).
Explicit lake/outlet authoring, spill topology, water availability, endorheic
intent and route-wide reconciliation remain separate work. Present filled
connectivity never certifies a naturally flowing river on the finished terrain.

Validation completed on Windows/CPython 3.14: 241 tests, Ruff, strict Pyright,
and dependency checks pass. Hidden Tk checks exercised result handling and
thin-channel overlay; the final public example CLI build and three-panel review
were inspected. Paired 768-pixel, seed-42 benchmarks retained existing DEM,
mask, coordinate, routing and incision hashes for authored, archipelago and
regional cases. Existing diagnostic values match apart from advanced algorithm
IDs. Generation medians were 2.331, 2.624 and 1.610 s respectively (two cold
runs each); these are not speedup claims. Zero-height behavior intentionally
changes as covered by the new conservation tests.
