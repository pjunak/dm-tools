# ADR-0056: Condition network floors in both directions

- Status: Accepted and implemented
- Date: 2026-09-17
- Extends: ADR-0055; no project or build-schema change

## Context

The nodal floor correction previously only deepened downstream cuts. When a
receiver reached its limit, unnecessary upstream excavation could retain a
climb even when shallower upstream cuts admitted a descending path. Correcting
one segment cannot propagate that downstream requirement through tributaries.

The existing routing graph, regional/global budgets and local cut ceilings
already provide a bounded problem. First solve feasible nodal intervals on that
graph, while preserving unresolved cases for full-profile and route research.
The [comparison](../research/2026-09-17-network-floor-conditioning.md) records
both the reduction in large climbs and the increase in some smaller rises.

## Decision

Replace downstream-only floor conditioning with two passes over the selected
acyclic receiver network. For source height S, cut ceiling C and current cut I,
use the interval [S-C, S] and preferred floor S-I. The minimum nodal drop remains
0.01 m. No source height, receiver, terminal, cut ceiling or accumulation changes.

1. In downstream-first order, propagate required floors upstream:
   R[i] = max(S[i]-C[i], R[receiver]+drop).
2. Raise a preferred floor to that requirement, bounded by its uncut source S.
   This recovers automatic excavation, without depositing above the source.
3. In upstream-first order, lower each receiver to the incoming floor minus the
   minimum drop, bounded by its own S-C. All tributaries constrain a confluence
   before it distributes its downstream requirement.

If every propagated requirement fits under its source upper bound, these passes
produce descending nodal floors within all intervals. If a requirement exceeds
its source, retain the source/cut limits and report the unresolved edge count.
The algorithm does not increase budgets, reroute the graph, or reinterpret an
intentional retention terminal. Zero-cut terminals remain fixed. Non-channel
cells and caller-owned arrays are unchanged.

Require finite selected sources, cuts and ranks, cuts within nonnegative limits,
finite nonnegative drop, valid receiver indices and strictly descending receiver
ranks. A malformed or cyclic selected graph is an error, not a successful repair.
Use one stable rank sort and two channel traversals, with array storage linear
in the planning grid. Existing steepness correction follows the floor passes.

`DrainageIncision.floor_correction_m` is now the signed net incision change,
including subsequent steepness correction: positive for extra cutting, negative
for cut recovery. This is an internal diagnostic, not an exported build field.
Keep `steepness_correction_m` as the additional cut from that later stage.

Generator identity becomes `coastline-constraint-terrain@15`; automatic valleys
become `regional-budget-mfd-d8-valleys@13`. Generated canonical cuts and heights
may change, while the graph, local ceilings, suppression, named seeds and
user-authored controls retain their meaning. Add no dependency, public setting,
legacy mode or finished-output modification operation.

## Validation and limits

Cover a complete chain, unequal tributaries, storage permutations, an unfillable
pit, a conflicting path, fixed zero-cut nodes, unaffected cells, input ownership,
invalid intervals/ranks and independently constructed feasible branching graphs.
Compare dense public profiles, authored water outcomes and fresh-process builds.
Profile report version 2 adds counts above 1, 10, 50 and 100 m so reduced large
climbs cannot hide an increased count of smaller failures. Compare all-finite
populations when changed floors change the descending-endpoint subset.

The feasibility statement applies to the selected nodal source intervals, before
reconstruction and final authored operations. It does not establish continuous
river descent. Interpolation, residual detail, tapers and overlapping corridors
can still introduce rises, including regressions. Between-node obstacles absent
from the nodal intervals, infeasible source/ceiling combinations, retention
transitions, route alternatives and channel-turn smoothing remain open.
