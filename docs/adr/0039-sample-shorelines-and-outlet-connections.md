# ADR-0039: Sample shorelines and outlet connections

- Status: Accepted
- Date: 2026-09-11
- Extends: ADR-0036 through ADR-0038; replaces build v11 and water/outflow review identities

## Context

Canonical ground samples can miss a narrow ridge between connected water and
an outlet, or a low opening between boundary nodes. Vector containment checks
establish where a segment lies, but do not establish its intervening height.
The exact outlet height alone is insufficient evidence for either connection.

## Decision

Keep canonical routing, authored ground and water levels. Re-evaluate the same
finished field at additional metric positions and round each height to Float32.
Sample the entire authored lake boundary and the selected water-contact node,
exact outlet and first outside attachment. Subsequent downstream edges and
internal basin links retain their existing canonical height checks.

Maximum sample spacing is one quarter of the shorter canonical axis step;
every nonzero input segment has at least one interior point. Include each
vertex exactly and normalize boundary-ring start/direction. Repeat the first
boundary point to close its profile. Derived checks are independent of output
resolution and unrelated constraint order.

A connection profile with sampled ground above water plus 0.01 m blocks transfer.
A crest below the imposed water surface may remain passable. Finer boundary
samples below water minus 0.01 m outside the existing one-grid-diagonal outlet
allowance also block transfer. Retain coarse shoreline tests, including crop
boundary rejection. Closed lakes have no permitted opening; dry basins receive
no water-boundary profile. A low boundary finding does not prove which interior
pool reaches it; the conservative check must not merge isolated pools.

A profile allows at most 65,536 samples in batches of at most 4,096. An excess
returns `budget_exceeded`, the requested count and empty evidence; unresolved
checks block transfer without silently increasing spacing. Nonfinite sampled
ground fails generation. These budgets bound each profile, not total project
cost or the number of user-authored basins.

Build v12 stores complete profiles in `diagnostics.json`, with positions,
heights, spacing, completeness, extrema and low-boundary indices. Keep current
project v5 and numeric archive layouts; remove the superseded build schema.
Record `quarter-grid-float32-water-checks@1`, `authored-basin-water-review@6`
and `captured-mfd-reviewed-d8-outlets@4`. No new dependency is introduced.
The workbench and review image locate low boundary samples with orange dots
and above-water connection maxima with red diamonds. Details shows counts,
spacing and the highest sampled connection ground.

## Consequences and validation

Exported evidence explains previously missed openings and barriers. A sampled
maximum can underestimate a narrower crest between samples; it is neither a
complete controlling-sill search nor an equilibrium lake level. The circular
opening allowance remains a review convention, not inferred hydraulic width.

Synthetic cases change only between-node evidence while preserving all coarse
heights; they test inner/outer barriers, extra openings, submerged crests,
tolerance, retention and unresolved budgets. A public generated shoreline-gap
project reproduces the missed-opening problem through a narrow authored height
constraint. Existing outlet examples still connect. Tests cover profile spacing,
corners, batching, ring order, resolution independence, area conservation,
exported evidence and marker positions. The
[research rundown](../research/2026-09-11-finer-water-connections.md) records the
measured results and remaining validation limits.
