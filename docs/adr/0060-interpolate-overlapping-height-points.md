# ADR-0060: Interpolate overlapping absolute height points

- Status: Accepted
- Date: 2026-09-23
- Implements the exact-point authority in ADR-0003 and ADR-0007 under overlap

## Context

Absolute height points are authored elevations, but the final point stage used
an ordinary weighted mean of all nearby targets. A point with unit influence at
its own centre still received its neighbours' contributions. In the public water
fixture, a 250 m point evaluated to 331.149811 m. This defect was exposed by the
[parent-preservation experiment](../research/2026-09-23-parent-cell-preservation.md)
and exists before any local enrichment. Freezing that result would preserve the
wrong authored reference.

Simply replacing isolated centre samples would leave discontinuities in nearby
terrain. Re-solving or modifying completed raster outputs would also violate the
input-only authoring contract. Correct the pointwise generation field instead.

## Decision

Keep the existing metric core/context response and coastal attenuation, giving
each point a weight w in [0,1]. Blend its target using a share proportional to
`w / (1-w)`, with the limiting value at w=1. A point dominates as its centre is
approached. The target remains a convex combination of authored heights; the
existing clipped sum of ordinary weights controls its blend with the preceding
terrain. Existing point/structure detail attenuation still applies.

Accumulate target shares using a common scale equal to the smallest `(1-w)` seen
so far at each query coordinate. Rescale previous totals as this decreases. Every
contribution then remains at most one; there is no singular division or arbitrary
epsilon floor. Evaluate absolute points in canonical coordinate/height/radius
order so authoring order cannot perturb floating-point accumulation. The scale is
computed independently at each query point, never from a sample batch or raster.

At exact authored coordinates, set the original target and suppress residual
detail completely. This handles zero-height points and the finite-precision case
where extremely close distinct points both round to unit influence. Ordinary
near-centre terrain already converges to the target; this final assignment is not
a replacement for that interpolating response. The delivered value is the authored
target rounded to Float32. No nearest-pixel snapping is introduced.

Reject conflicting absolute elevations at the same metric location before global
routing. Equal targets at that location remain allowed, including different
influence radii. Reject nonzero absolute points exactly on the sea-level land
boundary, including an SVG hole boundary; a zero target there is consistent and
remains allowed. Relative guidance retains its separate displacement semantics.

Advance the generator identity to `coastline-constraint-terrain@17`. Existing
project fields and build schema remain current; regenerated numeric terrain and
routing can change where absolute-point influence overlaps. Completed products
remain immutable. No old generator mode or migration is added.

## Validation and limits

Regression tests cover exact authored heights in the pointwise field and aligned
DEM nodes, zero/ceiling targets, nearby continuity from eight directions, equal
and conflicting coincident points, very close distinct points, sea level, point
order, query batching and 65/129/257 shared coordinates. Public water fixtures are
checked at two seeds and both two- and six-band detail settings. Existing
structure-profile and regional/full-source tests remain required.

The [implementation measurements](../research/2026-09-23-exact-height-points.md)
record baseline errors, post-fix values, public numerical/drainage changes,
timings and the full validation boundary.

This is an interpolation fix, not an erosion model or a complete hard/soft
constraint solver. It does not prove continuous slope bounds, monotonic drainage
between arbitrary hard points, shoreline convergence or a safe local-detail
restriction. Very close incompatible heights may require steep terrain even when
both are exactly satisfied. Parent-conditioned generation and finer hydrology
remain separate measured work.
