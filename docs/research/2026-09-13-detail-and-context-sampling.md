# Procedural detail and context sampling - 2026-09-13

Status: implemented bounded sampling improvement; continuous error bounds remain
open. [ADR-0045](../adr/0045-sample-procedural-detail-and-context-shoulders.md)
owns the policy, [the water guide](../terrain-water.md) owns its current contract,
and [TODO](../../TODO.md) records the follow-up work.

## Result and implementation

Water review now follows the finest active procedural lattice scale and the
broad context shoulders of authored features. The same prepared guidance feeds
shorelines, outlet contacts, complete downstream routes and internal wet/dry
links. It changes where the existing finished Float32 field is inspected.
Fixed-input ground, incision, authored anchors and captured area are preserved;
new evidence can change collection and transfer outcomes.

Global maximum spacing is `largest_feature_km / 2**detail_levels`, half the
finest octave's lattice cell. Global width detail remains active for ridge/valley
constraints even with zero base variability. Nonzero-relief regions request
`feature_size_km / 2**max(2, detail_levels)` inside their polygons, accounting
for the regional recipes' two mandatory macro octaves. Regional transitions and
narrow authored cores keep their existing guidance. Overlaps use the finest
request and preserve every baseline station.

Context radius factors are shared with the field evaluator. Narrow shoulders
use context/4 spacing in twice-context-radius corridors; broad shoulders add one
interior closest approach to the complete normalized geometry. This avoids
buffering every broad line segment. Use the maximum structure width variation
when estimating context extent; attached relative points remain part of their
parent profiles. No field filtering, new dependency or Rust component is added.

Diagnostics record `feature-guided-float32-water-checks@4`. Project v5, build v16,
water/outflow gate identifiers @10/@8 and archive layouts are unchanged.

## Research basis and choice

Sampling theory explains why widely spaced probes can miss information and why
exact reconstruction requires assumptions about frequency content. Those
assumptions do not establish the extrema of this blended terrain field.
[PBRT 4e, Sampling Theory](https://www.pbr-book.org/4ed/Sampling_and_Reconstruction/Sampling_Theory)
is the primary reference checked for that distinction. Our value-noise lattice
cell is a useful sampling scale, not a spectral cutoff or a Nyquist guarantee.

An exploratory comparison on the original eight procedural scenes tested half,
quarter and eighth of the finest cell. Against each plan's 16-fold finite
reference, worst crest misses were 5.99, 1.63 and 0.34 m respectively. Half-cell
plans requested 53-709 stations, quarter-cell 101-1417 and eighth-cell 201-2833.
Half-cell guidance caught all selected-level misses at the lowest measured cost
of those candidates. It is an incremental choice, not a proven optimum. The
final matrix below uses a denser 128-fold reference and adds oblique paths.

## Finished-field convergence

```powershell
.\.venv\Scripts\python.exe -m benchmarks.water_convergence --seed 42 20260913 --direction horizontal diagonal oblique --repeats 2 --output artifacts/detail-context-convergence-20260913.json
```

The completed matrix has 60 distinct scenes, each repeated in a fresh process:
five cases, 400/4000 km objects, three directions and two seeds, for 120 runs.
The added regional-detail scene uses rotated hills (31 degrees), 2 km feature
size and zero global variability, isolating regional noise. Protected dry
footprints isolate these fields from automatic incision. A 64-pixel delivered
raster does not determine the sampled field. Horizontal/diagonal paths join
canonical neighbours; the optional `(1, 0.37)` grid-edge vector ends off-grid.
These are deliberate numeric stress scenes, not authoring presets.

Aligned trials refine production intervals by factors 1-64 in powers of two;
half-shifted trials preserve original stations while shifting their interior
probes. Each reference uses factor 128 and contains every trial station exactly.
Shared coordinates and Float32 values must match byte for byte. `geometry_only`
omits new procedural/context guidance on the same prepared field while retaining
core and regional-transition probes. `without_region_guidance` separately omits
polygon transition guides while retaining density. These are research controls,
not runtime switches or alternate terrain generators.

Worst factor-1 differences from each policy's own finite reference, across the
12 distinct scenes per case (metres):

| Case | Crest miss, control → current | Minimum overestimate, control → current | Cumulative rise miss, control → current | Current stations |
|---|---:|---:|---:|---:|
| Regional transition | 0 → 0 | 0 → 0 | 0 → 0 | 34-47 |
| Global procedural detail | 483.359 → 8.644 | 446.273 → 3.366 | 971.282 → 12.010 | 53-709 |
| Rotated regional detail | 454.771 → 1.515 | 326.422 → 2.134 | 897.572 → 2.729 | 53-709 |
| Context shoulder | 0.308563 → 0.000122 | 0 → 0 | 0.308563 → 0.000122 | 6-8 |
| Overlapping positive/negative points | 0.307816 → 0.307816 | 0.483944 → 0.483944 | 0.486698 → 0.486698 | 26-36 |

The global control misses an above-level decision in 4/12 scenes; the context
control misses it in 2/12. Current guidance misses none of the selected above-
level, below-level or uphill decisions across these 60 scenes at 0.01 m
tolerance. These are raw-ground/selected-level checks, not complete outlet or
hydraulic decisions. The oblique case exposes a larger old crest miss than the
388.97 m maximum in the original horizontal/diagonal matrix.

Every comparison completed; the largest reference contained 90,625 stations.
The research CLI cap is now 262,144 because the former 65,536 default could not
fit full references for the denser production plans. Production caps remain
65,536 per profile and 262,144 per eligible wet/dry network, with batches of
4096. Repeat inputs, all 27 numeric products and complete comparison evidence
matched. All 64 runs shared with the preceding matrix also matched its input
hashes and all 27 numeric hashes. Inspection preserved prepared terrain and water
review identity.

## Complete-budget boundary

Finer probes require more work. The existing six-octave flat-outlet settings
request 1.5625 km global spacing, including detail that changes valley width
across the otherwise flat regional plateau. Its 17,042-candidate dry network
exceeds 262,144 requested stations. Planning stops with a required lower bound
of 262,150; this is not the full unconstrained count. No dry prefix is evaluated
or accepted. Every dry donor remains retained, while fully reviewed wet flow
can still leave through the connected outlet.

The public flat-routing example now explicitly uses five octaves, giving a
3.125 km procedural limit and a complete 199,188-station dry plan. It retains
1507 nonzero flat ranks and collects 4147 dry nodes in the 65-pixel regression.
Changing this example's octave setting changes its field; historical six-octave
measurements are not current fixture timings. Both forced-cap and real six-
octave exhaustion tests verify wet-flow preservation and full area accounting.
The engine never changes a user's settings to make a review fit.

## Runtime and verification

A separate cProfile run located avoidable regional intersection work. In the
unoptimized dry case, `_contained_intervals` took 1.024 s cumulative inside
2.859 s of profile planning; the geometry-only control spent 0.769 s in planning.
These instrumented times locate work and are not interchangeable with the
unprofiled timings below. Strict containment and disjointness checks now avoid
creating and projecting unchanged regional segments; partial crossings retain the same
clipping calculation. Paths touching a re-entrant or hole corner must still
retain that split-interval contact; regression tests cover both. Exact-evidence
replay checks this optimization. It re-ran all 60 distinct convergence scenes
and all 42 timing/control runs, matching their pre-optimization input, complete
numeric and water-evidence hashes exactly; convergence comparison hashes also
matched. The initial 120-run matrix and final 60-scene replay are separate from
the timing runs. The optimization reduces the added generation cost on the
connected outlet and dry barrier cases from the initial 55-60% to 31-34%, preserving every requested
station and review result. Final unprofiled measurements follow.

Seven workloads ran in alternating control/current order, three fresh processes
per policy at 768 pixels and seed 42: 42 runs total. `flat6` restores six octaves
in memory; the other fixtures use their current public settings. The control
removes density/context guides at the prepared review call and changes no field
input. Source/runtime identities were checked before and after. Tests, builds
and convergence runs were not concurrent with these timings.

Median seconds (generation includes review; the prepared-review column is not
an additional cost to add to generation):

| Case | Generation, control → current | Change | Prepared review, control → current |
|---|---:|---:|---:|
| Regional | 1.549 → 1.572 | +1.4% | 0.0005 → 0.0006 |
| Closed basin water | 1.481 → 1.499 | +1.2% | 0.0070 → 0.0131 |
| Connected outlet | 2.407 → 3.153 | +31.0% | 0.866 → 1.616 |
| Flat outlet, five octaves | 2.445 → 3.095 | +26.6% | 0.894 → 1.533 |
| Flat outlet, six octaves | 2.462 → 2.134 | -13.3% | 0.899 → 0.528 |
| Internal water barrier | 1.664 → 1.714 | +3.0% | 0.116 → 0.161 |
| Dry collection barrier | 2.458 → 3.293 | +34.0% | 0.912 → 1.741 |

Connected-outlet generation ranges were 2.401-2.417 s control and 3.138-3.155 s
current; dry-barrier ranges were 2.451-2.463 s and 3.272-3.304 s. Five-octave
flat ranges were 2.441-2.453 s and 3.077-3.163 s. The six-octave case becomes
faster because it rejects the dry plan before evaluation, losing dry collection;
that timing is not an accepted optimization. Regional/closed-water timing
ranges overlap; three repeats do not establish such small performance changes.
Peak process memory stayed within
135.3-141.2 MiB control and 135.0-140.8 MiB current across these workloads.
These are local cold-process generation measurements, not full-build timings.

All 19 terrain/capture product hashes matched between policies in every workload.
They also matched the preceding revision's recorded hashes for the five unchanged
public cases available in that report. All 27 products and evidence hashes were
repeatable within each policy. Area balance errors remained below 1e-6 km2.
The connected-outlet case now collects 1370 dry nodes instead of 1477; the dry
barrier case collects 1349 instead of 1458. New sampled barriers/rises leave
more area retained without changing the original capture graph. Five-octave
flat collection and all its numeric products matched the geometry-only control.
The unchanged 100 m dry barrier still rejects its link and chooses a clear
alternative. Terrain preservation is compatible with changed transfer arrays
when new probes find barriers.

Validation completed:

- Full pytest: **469 passed in 213.88 s**; Ruff passed and strict Pyright reported
  zero errors or warnings. Tests cover density locality, preserved baseline
  coordinates, duplicate/reversed geometry, actual field misses, context-radius
  refactor equivalence, complete budgets, real dry rerouting and flat collection.
- The fresh 768-pixel public flat-outlet CLI build passed the current build-v16
  schema, completion-ID verification and all 13 output hashes/sizes. Source
  project/SVG hashes matched; GeoTIFF elevations and masks matched the NPY
  products exactly. Retained plus transferred area exactly matched captured
  area at every footprint node; terminal/source sums agreed, with 1507 flat ranks.
- Runtime: Windows 11 AMD64, CPython 3.14.7, NumPy 2.5.2, Shapely 2.1.2 /
  GEOS 3.13.1, Rasterio 1.5.1 / GDAL 3.12.4, Pillow 12.3.0. Engine source hash
  `f1418ad1d18981984b560e8bba9d277ffd539bba6fc388cfb43b82f27e4b73f0`.

Ignored local evidence is stored in
`artifacts/detail-context-convergence-20260913.json`,
`artifacts/detail-context-convergence-final-20260913.json`,
`artifacts/detail-context-performance-final-20260913.json`,
`artifacts/detail-context-final-equivalence-20260913.json`,
`artifacts/detail-context-build-validation-final-20260913.json` and
`artifacts/detail-context-flat-build-final-20260913/`. The pre-optimization
performance comparison remains in
`artifacts/detail-context-performance-20260913.json`. The exploratory station-scale
comparison remains in `artifacts/sampling-scales-prototype-20260913.json`.
Generated runs and profiles are not committed.

## Remaining work

1. Compare bounded local refinement for blended extrema, longitudinal variation
   and grazing paths, using amplitude/gradient bounds where practical. Sweep
   octave counts, roughness and physical feature sizes before promising accuracy.
2. Estimate and expose whole-project sampling cost before expensive high-detail
   water reviews. Compare many-lake/many-constraint planning, memory and diagnostic
   serialization without dropping required stations or hiding budget exhaustion.
3. Define controlling-sill, inflow and storage assumptions before explicit lake
   chains. A clear finite path does not establish a stable lake level.

Gaussian tails extend beyond finite corridors; one broad-context closest
approach does not find every peak, and overlapping fields can move extrema.
Residual metre-scale procedural error exceeds the 0.01 m decision tolerance.
The matrix is finite reference evidence, not continuous clearance, off-grid 2D
connectivity, a hydraulic model or a universal performance bound. Manual
workbench interaction and a Tharkeniss Veld rebuild remain unverified.
