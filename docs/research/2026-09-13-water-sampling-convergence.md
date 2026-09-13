# Water-profile convergence and regional guidance - 2026-09-13

Status: implemented research tooling and bounded regional sampling improvement.
This follows [exact water-sample reuse](2026-09-13-water-sampling-reuse.md).
[ADR-0044](../adr/0044-guide-water-profiles-through-regional-transitions.md)
owns the station policy; [TODO](../../TODO.md) owns remaining experiments.

## Findings and implemented change

Regular quarter-grid water probes can miss regional landforms completely. A
1 km plateau band on a 4000 km object was sampled as flat 100 m ground; the
finished field contains a 1050 m crest. Regional boundary/transition guidance
now finds that crest in both horizontal and diagonal tests, using 43 and 47
stations respectively instead of 5 and 7. A 400 km object already resolves the
same physical band with its baseline. The two seeds produce the same plateau
because its zero-relief recipe deliberately isolates transition behavior.

Guidance uses the real regional polygon and inward transition distance. Near
boundary corridors it samples at transition/4; crossed contained intervals can
request finer local spacing at length/4. Deep interiors retain the baseline.
Concave regions keep separate crossings; tangencies never create a zero-length
sampling interval. Duplicate guidance and equivalent ring order remain
reproducible. Broad transitions skip proven full-length or disjoint cases before
building corridors when neither can request a finer interval.

All shoreline, contact, full external route and internal wet/dry profiles use
this shared policy. A synthetic wet graph confirms that a regional crest blocks
the affected connection while a clear alternate path remains eligible. No
terrain cutting, authored-height adjustment, capture change, storage solver or
new dependency accompanies the probes. `feature-guided-float32-water-checks@3`
owns the change. Project v5, build v16, diagnostic fields, water/outflow gate IDs
and numeric archive layouts remain unchanged.

## Repeatable comparison method

Run the repository-only [convergence tool](../../benchmarks/README.md#water-profile-convergence):

```powershell
.\.venv\Scripts\python.exe -m benchmarks.water_convergence --seed 42 20260913 --repeats 2 --output artifacts/water-convergence.json
```

The matrix has 32 distinct scenes: four cases, two object scales (400/4000 km),
two path directions and two seeds. Each scene runs twice in a fresh process,
for 64 runs. The delivered raster is 64 pixels; the measured profile uses the
same prepared pointwise Float32 field as production water review on the
canonical 257-node grid. A retained dry footprint isolates authored/procedural
relief from automatic incision. Profiles span one horizontal/diagonal canonical
edge. These deliberately small-feature cases are stress inputs, not presets.

Aligned trials split every production interval by factors 1 through 64 in
powers of two. Half-shifted trials preserve original stations but offset their
interior probes by half a subdivision. The reference splits each interval by
128 and contains every trial station exactly. No field values are interpolated.
Shared positions and Float32 heights must match byte for byte, including
nonuniform feature stations and signed zero. Ground/area products and review
identity are checked before and after inspection. A control removes only
regional sampling guides while retaining the same generated field.

Profiles report min/max ground, the largest rise from an earlier sample,
low/crest witness positions, hashes and threshold changes at 0.01 m tolerance.
These are raw-ground/selected-level comparisons, not complete outlet decisions
or a water-head/storage calculation. Every trial/reference must fit its complete
budget before evaluation; a missing reference remains unresolved. Repeated
inputs, all 27 numeric products and complete comparison evidence matched in
all runs. No comparison exceeded its budget; the largest reference had 5889
stations. Production budgets were not raised.

## Remaining misses

Worst baseline differences against each profile's finite reference, across the
eight distinct scenes per case:

| Case | Baseline stations | Crest underestimate | Minimum overestimate | Cumulative-rise underestimate | Selected-level misses |
|---|---:|---:|---:|---:|---:|
| Regional, new guidance | 34-47 | 0 m | 0 m | 0 m | 0/8 |
| Procedural, 2 km largest feature | 5-7 | 388.969 m | 446.273 m | 971.282 m | 3/8 |
| Point context tail outside core corridor | 5-7 | 0.309 m | 0 m | 0.309 m | 2/8 |
| Overlapping positive/negative points | 26-36 | 0.308 m | 0.484 m | 0.487 m | 0/8 |

The unguided regional control misses a 950 m rise in all four 4000 km scenes;
the new guidance has zero extrema/rise differences in this matrix. This does
not prove all regional profiles are resolved. The regional selected level is
750 m; procedural, tail and overlap comparisons use 3100, 339.6 and 125 m.
These chosen levels test numerical classification changes and are not proposed
physical lake levels. Tail/overlap zero-relief controls also repeat across seeds.

Refinement counts alone are insufficient: one procedural profile returns the
same 3310.897 m maximum at aligned factors 2, 4, 8, 16, 32 and 64, while the
finite reference reaches 3312.830 m. Across procedural scenes, even factor-64
half-shifted trials can underestimate the reference crest by 32.568 m. Stopping
when two extrema agree would give false confidence. Overlap and tail differences
shrink substantially with finer samples here, but this supplies no general
error bound for arbitrary blends or grazing features.

## Research basis and interpretation

NASA's spatial-grid convergence guidance describes systematic refinement and
nested grids, and explains the assumptions behind extrapolation and convergence
indices. We apply the narrower idea of nested comparisons to actual terrain
profiles. We do not apply Richardson extrapolation, claim an asymptotic order,
or label these extrema differences a GCI/error estimate. Half-shifted trials
are an additional alignment test. [NASA/NPARC spatial grid convergence](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html).

Shapely defines minimum clearance through geometry-invalidating vertex
movement. That is not a physical region width; redundant close vertices can
make it tiny. The implementation therefore uses local contained path lengths
and actual transition distances instead. A regression with nearly coincident
collinear boundary vertices checks that they cannot impose a globally tiny
sampling radius. [Shapely minimum clearance](https://shapely.readthedocs.io/en/stable/reference/shapely.minimum_clearance.html).

## Performance and validation

Windows / CPython 3.14.7 / NumPy 2.5.2 / Shapely 2.1.2. Correctness tests,
convergence runs and performance probes ran serially. Generation measurements
use five existing public cases at 768 pixels and seed 42, with exports excluded.
The initial before/after batches showed a large machine-speed change even in
unaffected controls; they validate outputs but cannot establish a speedup.

A follow-up alternated fresh processes with and without regional guides on the
same current implementation, three runs per variant/case. The first version
added 36.1%/37.8% generation cost on outlet/dry cases, mostly from broad-region
corridors that produced no finer intervals. Proven full-length/disjoint cases
now skip that geometry work. Another 30-run alternating comparison verified
identical complete water evidence to the first guided implementation, alongside
identical input and all 27 numeric hashes across variants.

Final medians (seconds), with generation ranges in parentheses:

| Public case | Without regional guidance | With regional guidance | Generation difference | Prepared water-review cost, without/with |
|---|---:|---:|---:|---:|
| Regional, no basins | 1.566 (1.564-1.584) | 1.564 (1.561-1.571) | -0.1% | 0.00055 / 0.00065 |
| Water, unconnected | 1.511 (1.505-1.539) | 1.522 (1.520-1.533) | +0.7% | 0.00731 / 0.00772 |
| Connected outlet | 2.379 (2.368-2.385) | 2.441 (2.441-2.471) | +2.6% | 0.79656 / 0.88006 |
| Internal barrier | 1.744 (1.715-1.748) | 1.750 (1.722-1.826) | +0.4% | 0.11689 / 0.11939 |
| Dry barrier/alternative | 2.441 (2.430-2.442) | 2.540 (2.507-2.573) | +4.0% | 0.83334 / 0.94423 |

The regional evidence has a measured cost, not a speedup claim. Median native
process peak memory changed by less than 0.5 MiB in these cases; this does not
establish project-wide memory limits. The public cases retain their DEM,
original routing/capture, internal/transfer arrays and conservation outcomes.
Some profile positions/counts/witnesses change; it would be incorrect to claim
unchanged diagnostic evidence relative to the unguided sampler. Existing
closed/unconnected controls retain identical water records apart from the
sampling identifier.

The ignored reports retain inputs, runtime/source identity and full precision:
`artifacts/water-convergence-final-20260913.json`,
`artifacts/regional-guidance-before-20260913.json`,
`artifacts/regional-guidance-after-20260913.json`, and
`artifacts/regional-guidance-final-interleaved-20260913.json`. The last comparison
also retains the hash of its local measurement script. Committed convergence
code and public fixtures reproduce the scientific comparison; timing varies
with hardware and load. The earlier matrix and first interleaved report remain
local diagnostic records.

Validation on the final implementation:

- `python -m pytest`: **445 passed**, 212.69 seconds.
- `python -m ruff check .`: passed; strict `python -m pyright`: zero errors.
- All 64 final convergence runs matched the pre-optimization matrix's input,
  numeric-product, water-review and complete comparison hashes exactly.
- A fresh 768-pixel public dry-collection CLI build passed build-v16 schema
  validation; all 13 output sizes and SHA-256 hashes were verified. GeoTIFF/NPY
  elevations and masks matched exactly, input hashes remained unchanged, and
  retained plus transferred area equalled original capture at every basin node.
  Diagnostics record sampling @3. Validation is retained in
  `artifacts/regional-guidance-build-validation-20260913.json`.
- All 405 local Markdown links across 95 documents resolved; `git diff --check`
  passed. Historical ADRs/reports retain their original identifiers and findings.

These checks cover numeric generation, saved-project builds and sampler/graph
contracts. Private Tharkeniss Veld generation and interactive GUI/GIS acceptance
were not part of these runs. Arbitrary terrain clearance, controlling sills,
physical lake equilibrium and whole-project resource bounds remain unproven.

## Next work

1. Compare wavelength-aware spacing and bounded local refinement on the measured
   procedural misses. Preserve complete budgets and expose unresolved evidence;
   avoid accepting repeated extrema as continuous clearance.
2. Extend context-tail/overlap probes across radii, relative amplitudes,
   orientations and grazing paths. Measure cost before enlarging all corridors.
3. Exercise many-region/many-lake workloads, memory and diagnostic serialization.
   Only then adopt an index or broader cache when measurements demonstrate value.
4. Define controlling-sill and storage assumptions before lake chains or
   reviewable breach/reroute proposals. The current fixes improve sampled ground
   evidence; they do not establish stable physical water levels.
