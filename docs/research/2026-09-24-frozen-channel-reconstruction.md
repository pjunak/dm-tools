# Frozen terrain/channel reconstruction comparison

2026-09-24. Public synthetic states from the
[first landscape-evolution batch](2026-09-24-landscape-evolution-reference.md).
No private maps, authored projects or completed terrain builds were modified.
This implements the next bounded B/R48 comparison in the
[main strategy](../strategy/README.md), not a replacement application generator.

## Decision

Keep a drainage-aligned piecewise-linear surface as an executable numerical
control. It removes the measured between-node humps on the frozen descending
networks without changing their grid heights, heads, junctions or terminals.
The same physical paths drive ground queries, measurements and the report.

**Do not promote this surface into normal generation.** River geometry still
follows eight raster directions, the surface has slope creases, off-grid authored
heights can change, and reconstruction does not fix an uphill receiver graph.
The prior landscape's process-grid sensitivity is unchanged. This closes a
specific reconstruction experiment, not R48, LE2 acceptance or LE3 integration.

Next compare a physical valley/path representation within fixed catchment and
authoring constraints, and diagnose changes of receivers/outlets across process
spacing. Keep this candidate as the monotonic-profile control. Do not add more
local floor corrections, increase the failed finest-grid budget, or expose
history controls before those quality gates. Climate, sediment and zoom jobs
retain their existing dependencies.

## Implementation and reproduction

The [reference guide](../../benchmarks/evolution/README.md#frozen-reconstruction-comparison)
owns commands. The new command runs in the application's existing Python
environment: no Landlab, SciPy, Matplotlib or new package is needed.

- `surface.py`: immutable, coordinate-addressed Float32 sampling with explicit
  required diagonal edges; preserve corner values and every grid-cell border.
- `paths.py`: connected required networks, all head-to-terminal routes, physical
  station distances, bounded work, numerical summaries and target residuals.
- `frozen.py`: verify container and numeric hashes, grid/precision/graph contracts,
  incomplete-source inventory and unchanged input files before completion.
- `reconstruction.py` and `surface_report.py`: identical-path comparison at two
  physical spacings, full per-edge/per-route records, timings, process peak,
  paired actual-ground figures and completion-last local reports.

Use a new output directory. The command refuses to overwrite one, fails if
source/runtime identity changes, and retains explicit topology rejections.
Failures after output creation leave `incomplete.json`; only a completed comparison
publishes `comparison.json`. Source results remain untouched. Required diagonal
crossings are rejected rather than dropped or made into invented junctions.

### Exact comparison boundary

The frozen experiment's `states.npz` contains **final Float64-snapshot receivers
and contributing areas**. The previous report's `final_metrics` instead rerouted
the delivered Float32 DEM; those rerouted links were not saved. This comparison
explicitly uses the saved graph, together with the unchanged delivered Float32
node heights, for both surfaces. It does not relabel that graph as delivery
routing or compare its numbers directly with the previous 17-station results.

Select every interior outgoing edge with at least 25 km2 contributing area,
using the same threshold as the first experiment. Require downstream connectivity
to the graph's terminals. Selection is fixed before reconstruction; no troublesome
edge or head is removed. Unselected flow directions are not claimed as preserved
physical river beds. Some current-generator graphs have crossings outside this
selection; there were no required-diagonal conflicts in the 22 completed cases.
Synthetic crossing tests verify rejection separately.

A current-generator fixture here means its frozen DEM and common research routing,
not its full native constraint-aware prepared field. Consequently these results
are not evidence that the application's existing authoring/cut contract is met.

### Surface and integral

In a cell used by a required diagonal, split the square on that diagonal and use
barycentric interpolation on its two triangles. Other cells retain bilinear
interpolation. Cardinal edges are already linear. Weights stay nonnegative and
sum to one, so there is no corner-range overshoot. A required edge's height is
the line between its endpoints in real arithmetic. Float32 profiles and identical
shared-coordinate queries are tested independently.

This is continuous height (C0), not continuous slope (C1). It can lower or raise
the interior relative to bilinear reconstruction. Report the exact unquantized
geometric integral over the full rectangle, separately from the solver's
interior-node volume ledger. For corner heights a,b,c,d in row order, let
`t = a+d-b-c`. The mean change in a selected cell is `t/12` for its a-d diagonal,
`-t/12` for b-c, with maximum absolute point difference bounded by `abs(t)/4`.
Multiply the mean by cell area for volume. This composition is not an erosion
flux or a sediment-conservation claim.

For two-epoch seed 42 at 625 m, 225 cells change. The integral decreases by
0.332292 km3, the full-domain mean by 0.06923 m, and the maximum point-change
bound is 54.81694 m. At 312.5 m the volume difference is -0.092724 km3.
An off-grid height target can therefore be materially violated even though every
grid node is unchanged. A regression explicitly preserves a 100 m node anchor
but reports a 52.5 m error at an incompatible bilinear-midpoint target; it never
patches the candidate to hide that error. Cut budgets and real authored coast,
ridge, basin and height controls still need their full integration gate.

## Metric definitions and coverage

Every unique selected edge and every complete head-to-terminal route is sampled
at uniform arclength stations no farther than **100 m**, then **25 m**, with all
original vertices included. The 0.01 m height tolerance is fixed. Both samplers
receive the identical graph, geometry and station requests.

- Uphill ascent sums every positive height difference, in metres.
- Affected length sums positive-rise intervals within nondecreasing runs whose
  total rise exceeds 0.01 m. Apply the tolerance to the whole run, not every
  interval: finer sampling must not hide a gentle climb. Flat quantized intervals
  do not contribute to that length. This is a sampled measure, not an exact
  subinterval crossing calculation.
- Maximum excursion is the greatest height above the previously encountered
  minimum along the ordered route. A route is unresolved when it exceeds 0.01 m.
- Unique-network lengths/ascent count each selected edge once. Full-route ascent
  can repeat shared downstream reaches and is labelled separately; neither is
  silently used as the other's denominator.
- The nodally nonascending subset is defined from input node heights, before
  sampling either surface. It is not a full physical-feasibility certificate:
  lake semantics, actual water storage, authored budgets and divides are absent.

The final matrix covers **22 completed source cases, 19,228 selected edges and
1,183 complete routes**. Counts include the original repeated seed-42 run; they
are coverage totals, not independent statistical samples. Per sampler, 542,351
stations were evaluated at 100 m and 1,934,992 at 25 m, counting both unique-edge
and full-route passes. The original 156.25 m worker failed its 60-second solver
budget and has no usable final state; it remains listed as an omitted failed
source, not a successful fine-grid result.

All **1,030 nodally nonascending routes** have zero candidate ascent at both
spacings. On that same subset, 689 control routes were unresolved; summed
full-route control ascent at 25 m was 40,012.39 m (shared reaches repeated).
Across the whole matrix unresolved counts change from 842 to 153 at both spacings.
Every remaining route has an input nodal uphill segment. No route disappeared.
Finite sampling success is not continuous-water certification.

## Per-case results

Dense 25 m stations plus vertices. Ascent is the unique-edge network total;
maximum is the complete-route excursion. Values before/after always refer to
bilinear/candidate on the same frozen case. Units are metres unless stated.

| Frozen case | Edges / routes | Unresolved routes | Total ascent (m) | Maximum route rise (m) |
|---|---:|---:|---:|---:|
| diffusion-only-seed42-dx625 | 334 / 29 | 0 -> 0 | 0.00 -> 0.00 | 0.00 -> 0.00 |
| incision-only-seed42-dx625 | 859 / 50 | 39 -> 0 | 3088.25 -> 0.00 | 61.48 -> 0.00 |
| uniform-rock-seed42-dx625 | 877 / 46 | 33 -> 0 | 2240.91 -> 0.00 | 39.67 -> 0.00 |
| uplift-only-seed42-dx625 | 360 / 23 | 3 -> 3 | 0.27 -> 0.16 | 0.27 -> 0.16 |
| constant-seed20260902-dx625 | 846 / 51 | 31 -> 0 | 2407.68 -> 0.00 | 56.23 -> 0.00 |
| constant-seed42-dx625 | 827 / 48 | 35 -> 0 | 2596.97 -> 0.00 | 46.18 -> 0.00 |
| constant-seed7-dx625 | 842 / 53 | 33 -> 0 | 2250.43 -> 0.00 | 51.85 -> 0.00 |
| current-generator-seed20260902-dx625 | 1149 / 52 | 52 -> 52 | 469.90 -> 388.30 | 23.49 -> 23.49 |
| current-generator-seed42-dx625 | 1115 / 45 | 45 -> 45 | 277.93 -> 255.97 | 19.55 -> 19.55 |
| current-generator-seed7-dx625 | 1130 / 53 | 53 -> 53 | 456.77 -> 388.04 | 27.26 -> 27.26 |
| reversed-seed20260902-dx625 | 826 / 47 | 30 -> 0 | 2704.95 -> 0.00 | 50.56 -> 0.00 |
| reversed-seed42-dx625 | 765 / 47 | 36 -> 0 | 2463.84 -> 0.00 | 52.66 -> 0.00 |
| reversed-seed7-dx625 | 815 / 50 | 30 -> 0 | 2617.07 -> 0.00 | 51.04 -> 0.00 |
| two-epoch-seed20260902-dx625 | 878 / 54 | 30 -> 0 | 1929.36 -> 0.00 | 45.70 -> 0.00 |
| two-epoch-seed42-dx625 | 820 / 46 | 33 -> 0 | 1881.78 -> 0.00 | 37.57 -> 0.00 |
| two-epoch-seed7-dx625 | 832 / 52 | 32 -> 0 | 1665.15 -> 0.00 | 41.68 -> 0.00 |
| two-epoch-seed7-dx1250 (160 x 120 km) | 1570 / 205 | 159 -> 0 | 1819.40 -> 0.00 | 35.10 -> 0.00 |
| two-epoch-seed42-dx625 (original repeat) | 820 / 46 | 33 -> 0 | 1881.78 -> 0.00 | 37.57 -> 0.00 |
| two-epoch-seed7-dx625 (70 degrees) | 731 / 43 | 33 -> 0 | 937.30 -> 0.00 | 34.92 -> 0.00 |
| two-epoch-seed42-dx1250 | 425 / 50 | 32 -> 0 | 769.36 -> 0.00 | 48.52 -> 0.00 |
| two-epoch-seed42-dx312.5 | 1586 / 48 | 37 -> 0 | 1918.50 -> 0.00 | 24.55 -> 0.00 |
| two-epoch-seed42-dx625 (tighter time steps) | 821 / 45 | 33 -> 0 | 1981.66 -> 0.00 | 37.69 -> 0.00 |

Two-epoch seed 42 at 625 m changes from 88.225 km of sampled affected network
length to zero; seeds 7 and 20260902 change from 77.875 and 85.775 km to zero.
These are interpolation gains on fixed graphs, not a claim that the networks
have become less straight or less grid aligned.

### Material failures and regressions

All 150 routes in the three current-generator references remain unresolved:
node-level rises remain, with maximum route excursions of 19.55, 27.27 and
23.49 m for seeds 42, 7 and 20260902. Ascent declines, but that does not make any
of those complete routes acceptable. Current seed 42's sampled affected length
slightly **increases**, from 183.571 to 183.883 km, as its uphill shape changes.

The uplift-only control retains three unresolved routes and a 0.15607 m maximum
rise. Its total ascent falls from about 0.265 to 0.156 m, while affected length
**increases** from 1.100 to 1.509 km: replacing the bilinear curve spreads an
existing nodal climb over more of the edge. Both regressions remain in the
report. A zero affected-length reading for a gentle climb in the initial smoke
metric prompted the whole-run tolerance correction described above; final
measurements were repeated on the corrected code without changing the surface.

The paired full maps remain visually similar. Crops and longitudinal profiles
show removal of humps, but directional grooves and the oversimplified uplift
crest persist. Nodes, graph direction bins, heads, terminals and junctions are
identical by construction. No lower-direction-bias or process-convergence claim
can follow from that unchanged geometry.

## Provenance, resource cost and validation

Final ignored artifacts:

- `artifacts/reconstruction-verified-20260924/`: all 22 cases, local HTML index,
  full comparisons, paired maps/crops and complete control-worst route profiles.
- `artifacts/reconstruction-repeat-verified-20260924/`: independent fresh-process
  seed-42 repeat. Every profile hash, numerical summary and composition measure
  matches, with identical measurement source/runtime identity.

Earlier `reconstruction-smoke-20260924/`, `reconstruction-cohort-20260924/` and
`reconstruction-repeat-20260924/` are exploratory outputs, not the final evidence.
Source cohort locations and original package inventories remain in the first
report. Each new case carries original source identity, input file hashes and
current measurement identity separately. No evolution was rerun in this batch.

```text
package_source_sha256:
ca0d8870258c393f2d37f6aba8d01291e246c35eb472c71d5ef0155bfed66b34
benchmark_source_sha256:
36288fadcf72dadace3da663b0bd461acb8955bfa01f53152865ef3d825fb8bc
```

On the same Windows/CPython 3.14.7 Ryzen 7 9800X3D machine, the serial matrix took
13.323 seconds including input verification, measurements, case JSON and figure
work, before final index/summary publication. Whole-process lifetime peak was
146.75 MiB, including native arrays and rendering. This is not a fresh per-case
solver peak. The independent one-case repeat took 0.666 seconds with 126.27 MiB
process peak. No heavy tests ran concurrently with these measurements.

Candidate preparation on the 625 m seed-42 field took 10.46 ms; one 25 m
unique-edge/full-route pass took 87.6 ms versus 70.2 ms for bilinear. At 312.5 m,
preparation took 33.03 ms, and candidate/control passes took 152.6/127.6 ms.
These are single observations, not guaranteed timings or acceptance thresholds.
Evolution runtime remains separate and unchanged.

The 33 new regressions cover diagonal/cardinal profiles, nodes/cell borders,
shared queries, range bounds, 90-degree covariance, explicit crossings, graph
cycles/non-D8/disconnected paths, whole routes, nodal uphill preservation,
off-grid anchors, composition integral, flat/planar controls, gentle climbs,
sample budgets, corrupt/stale sources, completion failure and repeatability.
The isolated reference environment passes all 58 reference/domain/reconstruction
tests. The full base-environment suite passes: **1,299 passed, 1 optional module
skipped**, in 322.54 seconds. That optional module passed in the isolated run.
Ruff and strict Pyright pass. All 307 relative document targets checked resolve;
`git diff --check` passes. Evolved and current-generator paired figures were
visually inspected. No editor workflow or private-map generation is claimed:
this batch deliberately remains a research comparison.

## Next implementation gate

1. Use the candidate's descending profiles as a numerical control for a bounded
   physical valley/path prototype. Preserve junctions, terminals and coarse
   catchment coverage; constrain real ground rather than smoothing only the line.
2. Diagnose receiver/outlet changes at shared physical locations across the
   existing spacing/time controls. Distinguish captures, flat tie choices and
   insufficient valley support; fix a physical process policy before requesting
   another expensive finer history. The prior spatial nonconvergence is unresolved.
3. Preserve the existing native authoring/cut controls and add off-grid, crossing,
   coast, ridge and retained-basin cases before promotion. Record composition
   corrections separately from geological flux and reject incompatible targets.

Do not expand the report framework before that prototype. LE2/R48 remain open;
LE3 authoring integration follows their quality decision, not this test count.
