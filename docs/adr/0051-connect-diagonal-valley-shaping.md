# ADR-0051: Connect diagonal valley shaping

- Status: Accepted and implemented
- Date: 2026-09-16
- Extends: ADR-0050; no project or build-schema change

## Context

Bounded cubic reconstruction removes grid-edge slope breaks but interpolates
incision and detail suppression independently of channel topology. On a selected
diagonal connection, both shaping fields can weaken between the two channel
nodes, leaving a scalloped floor and substantial uphill excursions despite
descending endpoints. Moving the network or expanding incision budgets would
change a different contract.

## Decision

Use the existing selected D8 receiver edges to identify a single connected
diagonal in each canonical cell. Do not infer a connection from nearby channel
nodes. Leave unselected cells, cardinal edges and ambiguous crossing pairs with
the bounded cubic reconstruction. Prepare and own the cell topology once.

Within a selected cell, project queries onto that diagonal in metric coordinates.
Interpolate its two endpoint values to obtain a target for incision and another
for detail suppression. Add only a positive, smooth fraction of the gap from the
cubic value to that target. For gap `d >= 0`, use `d*d/(d+e)`, with `e` equal to
1% of the greater endpoint value (floored at 1e-8 before multiplication).
This correction is below `d` and has zero derivative where the gap vanishes.

Apply it inside a compact corridor of radius 0.35 times the shorter cell side,
with cross-weight `(1-u*u)^2` for normalized distance `u` clipped to [0,1].
Multiply by cubic smoothstep tapers over the outer 20% of both cell coordinates.
The correction and its first derivatives vanish on cell edges, preserving the
previous reconstruction there and at every canonical node. These fixed
process-grid fractions are shaping heuristics, not physical river-width laws.

Because the target is between two corner values and the weight is in [0,1],
the revised field remains in the original cell's corner range. Reapply the
existing bilinear incision ceiling. Exact vector basin retention, authored
constraints, coastline zero and the final generation ceiling retain authority.
Increasing suppression may raise ground where the removed residual was negative;
this is not a guarantee of lowering every affected DEM sample.

Evaluate both shaping fields together to share connection lookup and geometry.
Remove the redundant automatic-field copies and separate sampling entry points.
Record generator `coastline-constraint-terrain@10` and automatic valleys
`regional-budget-mfd-d8-valleys@8`. Keep public schemas and other algorithm IDs.
No new dependencies, compatibility switch or generated-map editing is added.

## Validation and consequences

Test both diagonals, a synthetic scalloped floor, exact nodes/edges, derivative
continuity, active ceilings, unaffected cells/divides, already deeper cuts,
nonuniform metric grids, symmetry, input ownership and chunk independence.
Measure complete Float32 channel profiles on real prepared fields, including
non-finite samples as unresolved evidence. See the
[comparison](../research/2026-09-16-connected-diagonal-valleys.md).

The correction substantially reduces sampled climb size and visible scalloping.
Canonical topology, nodal cut fields and routing diagnostics are unchanged.
This does not round D8 turns, condition cardinal channel interiors, repair every
uphill edge, prove continuous clearance, or generate new zoom-level detail.
Finite profile evidence and the remaining outliers stay explicit in the backlog.
