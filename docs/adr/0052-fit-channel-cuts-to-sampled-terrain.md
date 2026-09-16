# ADR-0052: Fit channel cuts to the sampled terrain

- Status: Accepted and implemented
- Date: 2026-09-16
- Extends: ADR-0050 and ADR-0051; no project or build-schema change

## Context

Interpolating incision and detail suppression does not interpolate the resulting
floor: the procedural source varies between canonical nodes. Both source humps
and overly deep automatic cuts can leave uphill interiors between descending
endpoints. Deepening cuts alone cannot remove a rise out of an artificial dip.
Some larger crests also exceed the existing between-node cut ceiling.

## Decision

After reconstructing incision and suppression, fit incision against the actual
macro height and retained residual at each query. During preparation, retain the
canonical floor before authored constraints are reapplied:

```text
floor = max(max(macro - incision, 0) + residual * (1 - suppression), 0)
```

Only explicit selected D8 edges whose endpoints are both land supply targets.
Use linear interpolation of these two floor heights as the local target.
Clamp the required cut to `[0, macro]`, then blend from the reconstructed cut
toward that value. A cut may increase to lower a hump or decrease to avoid an
artificial dip. This never adds elevation above the uncut source with its
retained detail. Authored constraints still apply afterward, with their existing
priority; these are generation operations, not edits to a completed DEM.

Use compact metric corridors of radius 0.35 times the smallest canonical axis
spacing. This shared radius preserves continuity across a nonuniform grid.
The cross-weight is `(1-u*u)^2`, with normalized distance `u` clipped to [0,1].
A smoothstep over the outer 20% of each segment tapers its endpoints. Diagonals
also taper across the outer 20% of each cell coordinate, so their corrections
vanish on cell edges. Cardinal corridors agree across their shared cell edge.
These fractions remain process-grid heuristics, not physical river widths.

At junctions, average the candidate cut changes by their corridor weights and
multiply by union coverage `1 - product(1 - weight)`. This keeps the correction
within the individual proposals without a maximum-selection crease. Reapply the
existing **bilinear nodal incision ceiling** after blending. The final cut need
not stay between the original corner *cut values*, unlike the initial bounded
cubic stage, but it remains between zero and that unchanged ceiling.

Keep every canonical sample, receiver, channel selection, suppression field and
nodal incision/limit array unchanged. Exact vector retention masks still zero
both automatic effects. Coastline zero and the global elevation ceiling remain
in force. The source, active ceilings and other existing operations may have
slope breaks; this is not an unconditional differentiability claim.

Record generator `coastline-constraint-terrain@11` and automatic valleys
`regional-budget-mfd-d8-valleys@9`. Reuse the prepared bounded incision grid;
add no dependency, legacy mode, save migration or public setting.

## Validation and consequences

Exercise positive/negative source residuals, all eight directed D8 orientations,
canonical endpoints, active ceilings, unavailable/non-land edges, unchanged
areas, shared cardinal boundaries, nonuniform metric symmetry, immutable inputs
and chunk/order independence. Compare finished Float32 profiles, canonical
products, water outcomes, appearance and generation cost; see the
[measurements](../research/2026-09-16-source-aware-channel-floors.md).

This reduces sampled interior climbs, especially on cardinal edges. It cannot
repair an obstacle beyond the cut ceiling or a pit below the uncut source, and
it preserves endpoint slopes through the tapers. It does not condition a whole
downstream route, round D8 bends, prove continuous clearance, or add zoom detail.
