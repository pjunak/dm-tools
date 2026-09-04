# ADR-0016: Scale generated valley width downstream

Status: Accepted

## Context

ADR-0015 used MFD contributing area both to locate and size automatic valleys.
MFD represents broad convergence well, but dividing flow among several cells
also makes the apparent channel laterally diffuse. Its first shoulder kernel
therefore changed depth downstream more clearly than width. Fine residual noise
was also restored without regard to valley floors, allowing drainage-scale
structure to become locally rough again.

Channel and valley width are commonly related to discharge or drainage area by
power laws. The exponent is not universal: it varies with material, process,
climate, and landscape history. A fantasy-continent generator without those
inputs should preserve the robust direction of the relation—larger downstream
drainage supports wider valleys—without claiming an Earth-calibrated width.

## Decision

- Retain MFD accumulation as the continuous measure of broad convergent flow.
- Derive a complementary D8 accumulation tree from the same Priority-Flood
  routing surface. Use its steepest receiver as the deterministic generated
  valley centreline; fixed neighbour order resolves exact ties.
- Select channels and calculate downstream hierarchy from D8 contributing area.
  Keep MFD accumulation as the reported internal accumulation product.
- Blend three cross-section scales: a narrow centre, two-iteration near
  shoulders, and seven-iteration trunk shoulders. Weight the broadest response
  by a bounded logarithmic drainage-area progression so large downstream trunks
  widen more than headwaters.
- Measure the width fixture at a fixed incision relief, rather than a percentage
  of each cross-section's maximum depth. This matches the river-corridor idea of
  measuring lateral width at a fixed height above the floor.
- Derive a second canonical field that suppresses up to 92% of stochastic
  residual detail at major valley floors, tapering across their shoulders and
  to zero at the coast. Apply it before authored constraints.

## Consequences

- Automatic headwaters retain narrower, more textured valleys while larger
  downstream trunks become deeper, broader, and smoother.
- D8 grid directions affect the unique centreline, while MFD still supplies the
  less directionally biased broad convergence measurement. Rotated MFD and
  synthetic D8 fixtures make that division explicit.
- Floor smoothing is deterministic and sampled from the same canonical field,
  so it preserves nested output-resolution behavior.
- This is a scale hierarchy for generated continental valleys, not a prediction
  of channel bankfull width, floodplain width, terraces, or lithologic valley
  confinement. Authored variable cross-sections remain separate future work.

## Evidence

- Leopold and Maddock, [The Hydraulic Geometry of Stream Channels and Some
  Physiographic Implications](https://doi.org/10.3133/pp252), 1953.
- Harel et al., [Drainage reorganization induces deviations in the scaling
  between valley width and drainage area](https://doi.org/10.5194/esurf-10-875-2022),
  2022.
- Langston and Tucker, [A physics-based model for fluvial valley
  width](https://doi.org/10.5194/esurf-12-493-2024), 2024.
- Synthetic fixtures verify a unique downstream tree, greater width at fixed
  relief downstream, stronger downstream floor control, authored relative
  valley depth, and exact nested samples.
