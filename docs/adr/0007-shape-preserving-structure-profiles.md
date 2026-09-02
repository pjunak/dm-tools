# ADR-0007: Use shape-preserving longitudinal profiles for anchored structures

**Status:** Accepted
**Date:** 2026-09-03
**Deciders:** Repository owner and project maintainer

## Context

Absolute height points close to an absolute ridge or valley already acted as
longitudinal profile anchors. Their targets were blended with overlapping
Gaussian weights, after which synthetic ridge relief or valley incision was
added. This made the line react beyond a circular point stamp, but it did not
produce a controlled crest or floor.

A synthetic range with two peaks and a lower pass demonstrated the failure
quantitatively. A 3,400 m peak was surrounded by crest samples reaching about
3,978 m, and samples beside the 2,400 m pass could fall below the pass. The
authored points were exact only at their individual pixels; the intervening
structure did not form a shape-preserving peak/pass profile.

## Decision

- Coalesce absolute point anchors by projected arc-length position on each
  absolute ridge or valley. Reject conflicting elevations at the same projected
  position instead of averaging incompatible hard constraints.
- Add baseline-elevation shoulder knots before the first anchor and after the
  last. Their distance is twice the existing along-line anchor radius, bounded
  by the structure endpoints.
- Interpolate the knots with a PCHIP-style monotone piecewise cubic Hermite
  profile. It passes through every knot, is continuously differentiable, and
  does not overshoot the range of adjacent knot elevations.
- Ramp authored control smoothly from zero at each outer shoulder knot to full
  control at the nearest anchor, and keep full control between anchors.
  Attenuate synthetic crest relief or floor incision by the inverse of that
  control.
- Blend the controlled target across the ridge or valley using the existing
  tapered cross-structure weight. Along the centreline, the profile may raise or
  lower the incoming surface so a lower anchor between higher anchors becomes a
  saddle rather than merely a circular depression.
- Preserve minimum-ridge and maximum-valley inequality behavior outside the
  authored profile span.
- Combine overlapping same-kind controlled profiles as weighted targets so
  authored constraint order remains irrelevant.
- Keep the final exact-point stage. It remains the last authority at the point
  location and resolves crossings with other structure kinds.
- Apply this decision only to absolute height anchors on absolute structures.
  Relative structures and an explicit pass constraint need separately defined
  semantics.

## Options considered

### Weighted Gaussian anchor targets

This was the previous implementation. It is local and smooth, but overlapping
weights do not interpolate hard anchors and added synthetic relief can create a
higher summit beside an authored peak.

### Natural cubic spline

A global cubic spline is smooth but can overshoot between peaks and passes,
which recreates the defect this change is intended to prevent.

### Piecewise linear profile

Linear interpolation is exact and cannot overshoot, but introduces visible
slope discontinuities at every authored anchor.

### Shape-preserving cubic Hermite profile

This is exact at knots, monotone between monotone anchors, smooth in slope, and
small enough to implement without adding a SciPy runtime dependency. It does
not infer drainage or geological history.

## Consequences

- Multiple authored peaks and passes form one continuous crest profile without
  exceeding adjacent peak targets.
- A controlled pass is lower along the ridge direction and higher than terrain
  across the ridge, satisfying the geometric saddle invariant in the synthetic
  fixture.
- An isolated anchor returns smoothly to the structure's base target at its
  shoulder knots.
- Existing projects containing absolute points attached to absolute structures
  will generate different terrain. Projects without such attachments retain
  their previous structure behavior.
- Pass crossing direction, relative ridge/valley profiles, per-vertex widths,
  asymmetric slopes, and hydrologic descent remain future work.

## Validation

- A quantitative two-peak/one-pass fixture verifies exact anchor elevations,
  no interval overshoot, a longitudinal local minimum, and lower cross-ridge
  terrain at the pass.
- The anchored result is identical after constraint reordering.
- Shared samples remain bit-for-bit equal between 65 and 129 pixel nested
  resolutions.
- Conflicting hard anchors at one projected structure position are rejected.
- Existing ridge, valley, broad-falloff, coastline, and attached-point tests
  continue to pass.
