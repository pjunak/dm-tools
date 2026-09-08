# ADR-0031: Bound automatic incision by regional relief

**Status:** Accepted
**Date:** 2026-09-08

## Decision

The global height ceiling previously controlled automatic incision even in
low-relief regions. Derive per-node budgets from the existing regional relief
and character, without adding another authoring control. Plain/hills/plateau/
mountain factors are respectively 0.15/0.40/0.25/0.25 of relief, bounded above
by the existing global depth plus correction reserve. These are deliberately
heuristic recipe safeguards, not calibrated erosion or rock-resistance values.

Share regional geometry weights with elevation composition: zero influence
outside and at boundaries, smoothstep inward transition, stable normalized
overlap blending. Scale initial incision by local/global budget. Corrections
may spend the remaining budget while retaining the existing global correction
reserve and available-elevation bound. Both floor and steepness stages use the
same effective cap. Export it as `incision_limit_m` in `routing.npz`.

A fully influenced zero-relief region permits no automatic incision. Exact
height anchors and authored valleys remain authoritative; the limit excludes
them and residual-detail suppression. Routing resolution and graph formation
are unchanged. Budgets do not enforce downhill flow by removing authored
landforms. Unresolved conflicts remain visible in existing review products.

Generator identity advances to `coastline-constraint-terrain@4` and automatic
valleys to `regional-budget-mfd-d8-valleys@3`. Landform recipe identity remains
`regional-landforms@1`. Project 4 and build manifest 6 structures are unchanged;
the new derived archive array is identified by the recorded algorithm. No old
algorithm branch, compatibility loader or migration is added.

## Validation and measurements

Tests cover caps after corrections, zero budgets, invalid budget arrays,
non-mutation, boundary continuity, overlap ordering, exact anchors, shared
sampling nodes and export identity. Existing generation, routing and sampling
checks exercise the common pipeline.

Fixed comparison: seed 42, 1000 km square, global ceiling 6000 m, coastal rise
5 km, default variability, default recipe over the normalized 0.05..0.95
square. Maximum cuts use canonical nodes [64:193,64:193]; elevation standard
deviation uses delivered 65-node samples [16:49,16:49]. Uphill counts cover the
whole canonical grid, including transitions and background. Before is commit
4035819; values below compare that algorithm with this decision.

| Recipe | Maximum interior cut m, before/after | Interior elevation std m, before/after | Uphill edges, before/after |
|---|---:|---:|---:|
| Plain | 144.84 / 15.00 | 16.88 / 15.91 | 44 / 253 |
| Hills | 260.66 / 191.07 | 107.35 / 106.48 | 274 / 279 |
| Plateau | 218.69 / 18.32 | 18.32 / 4.27 | 11 / 9 |
| Mountains | 272.27 / 272.27 | 676.59 / 676.59 | 621 / 621 |

These fixtures show improved preservation of low relief, with a substantial
plain-routing tradeoff. They are not a realism score or evidence of resolved
hydrology. Prioritize classification of blocked channels, basin/lake/outlet
handling and region-transition reconciliation. Do not silently relax regional
budgets to make diagnostic counts look better.

Validation completed on Windows/CPython 3.14: all 201 tests, Ruff, strict
Pyright and dependency checks pass. The public regional example builds through
the CLI; its cartographic preview was inspected. That preview still has gridded
channel cuts and recipe transition artifacts, so river geometry and regional
composition remain open visual work. No Tharkeniss Veld source was modified.
