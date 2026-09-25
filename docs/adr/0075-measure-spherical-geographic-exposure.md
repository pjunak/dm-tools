# ADR-0075: Measure spherical geographic exposure

- Status: Accepted
- Date: 2026-09-25
- Extends [ADR-0074](0074-verify-context-and-measure-water-openings.md); supersedes
  its context v2 product format and deferral of geographic exposure.

## Decision

Add cell-centre shoreline distance and eight directional water-exposure fields
as inspectable geographic context. They do not generate rainfall, winds, terrain
or a transport graph. Include inland shores and inland water; name the products
accordingly. Keep authored coastlines and ownership unchanged.

Use SciPy's KDTree on unit-sphere shoreline samples. Chord distance is monotonic
with great-circle distance, so exact nearest-neighbour lookup selects the nearest
sample. Convert the matched vectors to an arc with atan2(cross norm, dot). Densify
retained source-linear lon/lat edges with an upper bound on along-curve spacing:
`R * hypot(delta_phi, delta_lambda)`. Limit spacing to the lesser of 25 km and
one quarter of north-south cell spacing. The nearest-sample distance overestimates
the nearest retained shoreline by at most half the largest sample gap, apart
from floating-point roundoff. Record that bound and the sample count. Do not
mistake it for an error bound on the original unflattened SVG.

Remove artificial frame/polar edges before sampling. Matching land on opposite
seam sides has no shoreline there; differing coverage contributes a seam shore
once. No shore means an all-NaN distance array and zero sampling support, not a
zero-distance world. Admit at most 500,000 samples before integer count conversion
or index allocation, preventing count overflow on extreme custom radii.
Queries use one worker, exact search and batches of 4,096 centres.

Water exposure samples fractional water coverage along eight great-circle rays,
with initial bearings N, NE, E, SE, S, SW, W, NW clockwise from true north. The
range is min(3,000 km, pi*R/2), with exponentially decreasing weights exp(-3*d/range).
Use normalized midpoint quadrature and 32–256 distance samples; target a step
of at most one quarter of north-south grid spacing until the cap is reached.
Longitude wraps; rays can cross a pole. Land does not stop them. This is neither
continuous open-water fetch nor an evaporation/moisture transport calculation.

Record quadrature weight landing in mixed coastal cells separately. This is a
support diagnostic, not an error bound: a ray can miss a small feature entirely,
and a fine ray step cannot resolve a coarse coverage cell. Expose the range,
step count and support; compare resolutions before downstream use. Process
1,024 origins per chunk, check cancellation between chunks and retain Float32
fractions plus Float64 distances. Individual geometry/index calls are not
interruptible mid-call and the limits are not an OS process-memory guarantee.

## Products and interface

Context v3 (superseded; [current schemas](../../schemas/README.md)), algorithm
`spherical-geography-v3`, retains geography.npz and adds exposure.npz with distance
and all eight exposure/support planes. Export three new previews (distance,
north exposure and north support). Remove v2 schema/support. Rebuild from the
retained world project; source schema is unchanged. Extend bounded loading with
exact shapes/dtypes, distance/nodata and fraction constraints, fixed sampling
semantics and manifest consistency. Integrity checks are not an independent
scientific rerun or proof of origin.

The viewer adds Shore distance, Water exposure and Exposure support. A direction
selector only changes the view. Hover gives numeric values; layer-specific
legends state units and support limits. Source edits still invalidate results;
completed contexts remain immutable and cannot become the automatic Save target.

## Dependency and alternatives

Adopt SciPy >=1.18.1,<2 for this immediately used spatial index. The Windows x64
CPython 3.14 wheel was installed and exercised with NumPy 2.5.2. Its installed
license is BSD-3-Clause with bundled native notices; retain those when packaging.
Include SciPy in runtime identity and current build/context runtime schemas.
Landlab and its broader reference dependencies remain isolated.

A planar distance transform would distort global distance and lose retained
subcell shores. All-pairs spherical queries would scale with cells times source
samples. A custom spatial index adds maintenance without a current advantage.
A physically coupled climate model requires separate budgets and acceptance.

Primary references: [SciPy KDTree](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.html),
[exact query options](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.query.html),
and [SciPy licensing](https://github.com/scipy/scipy/blob/main/LICENSE.txt).

## Validation and remaining work

Analytic hemispheres check distance bounds, including polar and seam shores;
source scale/offset/rotation and radius controls retain spherical meaning. A
meridian-crossing exposure oracle checks midpoint convergence. Constant surfaces,
equal-latitude island/interior, reversed bearings, seam translation, pole crossing,
work admission, cancellation, saved arrays and UI view-only changes have controls.
See [implementation evidence](../research/2026-09-25-geographic-exposure.md).

Next add authored province/default hypotheses with explicit overlap/priority,
units, common present and separate ages/duration. Bathymetric hypotheses and
component-aware water incidence precede transport. Physical B/C and LE acceptance
still precede world-linked rough terrain and historical regional generation.
