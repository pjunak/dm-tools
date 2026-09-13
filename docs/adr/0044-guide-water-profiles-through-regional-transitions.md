# ADR-0044: Guide water profiles through regional transitions

- Status: Accepted
- Date: 2026-09-13
- Extends: ADR-0040

## Context

A real finished-terrain fixture contains a 1 km plateau strip between canonical
nodes on a 4000 km object. Quarter-grid samples all see 100 m ground, while
finer samples find a 1050 m crest. Existing point/line core guidance cannot see
regional polygons. Increasing every profile's density would spend more work
without addressing arbitrarily thin regions or proving continuous clearance.

## Decision

Prepare normalized regional polygons alongside the existing point and line
sampling features. Use the actual inward transition distance as the regional
sampling scale. Near each boundary segment, conservative square-cap corridors
extend twice that distance and request transition/4 spacing when it is finer
than the existing baseline.

Intersect the profile segment with the complete region. For each nonzero
contained interval, refine its overlap with those boundary corridors to the
smaller of transition/4, contained length/4 and baseline spacing. Add the
interval midpoint when it lies in the corridor. This resolves crossed strips
that never reach their nominal transition depth, while keeping deep interiors
at baseline spacing. Retain separate crossings of concave geometry; ignore
point-only intersections for the contained-length calculation. Do not use
minimum vertex clearance as a global physical width or accuracy estimate.

Reuse existing overlap merging, exact baseline stations and Float32 field
sampling for shoreline, contact, external-route and internal wet/dry evidence.
The 65536 per-profile, 262144 per-network and 4096 per-evaluation limits remain.
An excessive complete plan has no accepted prefix. Geometry only chooses where
to inspect; it does not alter ground, authored constraints, incision budgets,
capture, hydraulic head definitions or the existing transfer gates.

Record `feature-guided-float32-water-checks@3` in water diagnostics. Project v5,
build v16, array layouts and diagnostic field names remain unchanged. The
parent water-review/outflow identifiers remain @10/@8 because their gate and
accounting rules are unchanged; the independently recorded sampling identifier
owns the changed station policy. Add no legacy sampler, compatibility loader,
new runtime dependency or native-language implementation.

## Evidence and limits

The repository-only convergence runner compares the actual prepared finished
field at nested refinements and half-shifted interior stations. It preserves
production stations, checks exact shared-coordinate/value identity, rejects
excessive plans before evaluation and reports differences against a finite
sampled reference. It neither modifies terrain nor simulates storage/discharge.

Tests cover thin regions, broad transitions, deep interiors, multiple crossings,
ring equivalence, redundant close vertices, tangencies, budget rejection and
wet-link separation with clear alternate paths. The
[measured report](../research/2026-09-13-water-sampling-convergence.md) records
real-field comparisons and cost. Procedural extrema, context tails, blended
peaks, grazing geometry and off-grid 2D passages remain finite-sampling limits.
This decision does not certify continuous clearance or stable lake levels.
