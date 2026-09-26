# Landscape evolution reference

This repository-only experiment evolves a public synthetic catchment through
prescribed uplift, accumulated effective runoff, implicit stream-power incision
and conservative linear hillslope transport. It implements the first LE1/LE2
batch in the [implementation plan](../../docs/strategy/landscape-evolution.md).
It is not the default generator and is not a saved-project format.

## Isolated environment

The tested platform is Windows x86-64, CPython 3.14.7. From the repository root:

```powershell
.\.venv\Scripts\python.exe -m venv artifacts/evolution-venv
.\artifacts\evolution-venv\Scripts\python.exe -m pip install --only-binary=:all: --require-hashes -r benchmarks/evolution/requirements-windows-py314.txt
.\artifacts\evolution-venv\Scripts\python.exe -m pip install --no-deps -e .
.\artifacts\evolution-venv\Scripts\python.exe -m pytest tests/test_evolution.py tests/test_evolution_reference.py
```

The lock pins 53 resolved wheels, including Landlab 2.11.0, SciPy 1.18.1,
NumPy 2.5.2 and the application's existing dependencies. It is a tested Windows
lock, not a portable cross-platform promise. `py-richdem==2.2.0rc3` and
`wrapt==2.5.0rc1` are explicit prereleases. Landlab is MIT, but its declared
`py-richdem` dependency is GPL-3.0-only. The selected solver does not call
RichDEM; the resolved environment still includes it. These dependencies remain
research-only and are not added to `pyproject.toml`, bundled with the application
or approved for product distribution. See the
[dependency register](../../docs/DEPENDENCIES.md#isolated-landscape-evolution-reference).

## Run and inspect

```powershell
.\artifacts\evolution-venv\Scripts\python.exe -m benchmarks.evolution --output artifacts/my-evolution-comparison
Start-Process artifacts/my-evolution-comparison/index.html
```

The default is four cases on an 80 x 60 km rectangle, seed 42, 625 m process
spacing: `two-epoch`, `constant`, `reversed`, and `current-generator`. Open the
HTML page or `comparison.png`. Each case also has `history.png`, `states.npz`,
`result.json`, the request and worker log. All outputs are ignored artifacts.
The command refuses an existing output directory. Run from the repository root;
`python -m benchmarks.evolution --help` also works in the base environment.

A focused cohort and controls:

```powershell
.\artifacts\evolution-venv\Scripts\python.exe -m benchmarks.evolution --output artifacts/evolution-cohort --seeds 42 7 20260902
.\artifacts\evolution-venv\Scripts\python.exe -m benchmarks.evolution --output artifacts/evolution-finer --cases two-epoch --spacing-m 312.5 --seeds 42
.\artifacts\evolution-venv\Scripts\python.exe -m benchmarks.evolution --output artifacts/evolution-ablations --cases uplift-only diffusion-only incision-only uniform-rock --seeds 42
.\artifacts\evolution-venv\Scripts\python.exe -m benchmarks.evolution --output artifacts/evolution-rotated --cases two-epoch --angle-deg 70 --seeds 7
```

Other controls are `--extent-scale`, `--maximum-step-years`, `--step-error-m`
and `--maximum-seconds`. Spacing is physical and independent of display size.
Extents must contain whole square-cell intervals. Limits are 262,144 nodes,
4,096 accepted steps, 8,192 trials and, by default, 60 seconds of solver work.
A fresh worker has a further 30-second startup/measurement allowance before
termination. That allowance does not extend the solver budget. Solver checks
are cooperative between kernels, not a guarantee that an individual native
call stops immediately. Failed workers have `failure.json`; a partial matrix
has `incomplete.json`, not a complete `comparison.json`.

Run serially without other heavy work. Source/runtime identity is checked
before and after workers and the cohort. Do not edit Python source during a
measurement. Native allocations and imports are included in each fresh
worker's process-lifetime peak. Solver stages and full worker wall time are
reported separately; figure rendering happens afterward in the parent process.

## Declared model

- Initial relief, resistance and uplift use metric coordinates and a named
  seed; they agree at common coordinates across process grids. Noise is drawn
  once, never per iteration.
- Active uplift lasts 2 Myr at 0.5 mm/year; waning uplift lasts 4 Myr at
  0.05 mm/year. The constant control integrates the same 1,200 m of weighted
  uplift and effective runoff. Reversing epochs changes their order only.
- Effective runoff is 0.4 m/year. Incision uses
  `E = Ke * (Q / 1,000,000 m3/year)^0.5 * slope`, `Ke=0.001 m/year`
  divided by resistance (1 to 4). Hillslope diffusivity is 0.05 m2/year.
  These are fixed experimental coefficients, not a geological age calibration.
- The 80 x 60 km endpoint grid has fixed zero perimeter elevation. Boundary
  nodes own no control area. At 625 m, contributing area is 4,712.890625 km2,
  not the 4,800 km2 bounding rectangle. Outlets export water; no lake storage
  is simulated. Depressions are routed without filling the ground.
- Operator order is uplift, reroute/accumulate, implicit incision, hillslope
  transport. Accept two half-steps only after comparing them to one full step
  within 0.5 m maximum nodal difference. Rejected trials roll back. This local
  estimator is not a global error bound or proof of converged river capture.
- Dry and flooded nodes do not incise. Incised material goes to an explicit
  export sink. Hillslope redistribution permits deposition and uses conservative
  link fluxes with stable substeps. This is not a bedrock/mobile-cover model.
- Solver arrays are Float64. Final elevations are also delivered as Float32 and
  rerouted/measured after quantization. Bilinear reconstruction is an explicitly
  limited research sampler, not the accepted parent terrain field.

The adapter uses Landlab `FlowAccumulator` with D8 and
`DepressionFinderAndRouter`, `FastscapeEroder` with `n=1`, and `LinearDiffuser`.
The faster router was selected by measurement. Landlab 2.11.0's discharge
accumulator uses a C `float` temporary; the adapter uses its public Float64
area-accumulation branch with local volumetric sources as additive weights,
then supplies that corrected discharge to incision. The physical-scale spatial
runoff test checks this boundary; installed package files are unmodified.

## Evidence and limitations

Reports record forcing/field hashes, source/runtime/package identities, process
spacing/origin, snapshots, numeric array hashes, step error and receiver-change
fractions, volume ledger, expected and measured outlet discharge, channel-area
threshold, density, D8 directions, longest straight run, and 17-station profiles.
The volume residual is normalized by total imposed/export throughput, with a
1 m3 floor, and is also retained in m3. Incision exports and hillslope boundary
exports are separate. Array hashes, rather than NPZ container hashes, are the
repeatability comparison.

The current generator baseline uses a present-day ridge and plain on the same
rectangle, recorded completely in its result. It is a visual/structural reference;
it does not have identical initial conditions or forcing. Native planned-channel
profiles and common final-DEM routing are reported separately. Do not claim a
percentage improvement on matched routes from unrelated automatic networks.

Scientific figures use a shared height range, physical-spacing hillshade and
no display-only river smoothing. Blue terrain colour denotes low elevation,
not a generated water body. Epoch profiles follow each state's own largest
outlet and largest-area donors; captures can change which channel is plotted.

D8 direction bias, reconstruction-induced internal rises, unchanged initial
noise spectrum, finite sampled profiles, rectangular coast and missing sediment
remain limitations. Off-grid authored targets, multipart coasts, retained basins,
shared physical channel geometry, history controls in the editor and conditioned
local detail require LE3 and later gates. Successful analytic controls prove
specific numerical behavior, not realistic geology.


## Frozen reconstruction comparison

After generating completed reference cases, compare their unchanged Float32
nodes and saved final Float64-snapshot routing using the base environment:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.evolution.reconstruction --source artifacts/my-evolution-comparison --output artifacts/my-reconstruction-comparison
Start-Process artifacts/my-reconstruction-comparison/index.html
```

`--source` accepts one or more cohort directories or individual completed worker
directories. Select at most 64 completed cases; use a new output directory.
No Landlab, SciPy or Matplotlib is imported or needed for this command. It does
not run evolution or modify the supplied states. Source container/numeric hashes,
coordinate conventions and delivery precision are checked, along with unchanged
source/runtime identity before completion. Failed/unfinished source workers are
listed explicitly. A source cohort need not be wholly complete, but an unfinished
worker is never treated as a completed state.

Both samplers use every interior outgoing edge at the fixed 25 km2 contributing
area threshold. Profiles cover every unique edge and every complete head-to-terminal
route at 100 m and 25 m arclength spacing, plus all original vertices. The saved
graph is **not** the separately Float32-rerouted graph behind the first report's
`final_metrics`. See the [measured follow-up](../../docs/research/2026-09-24-frozen-channel-reconstruction.md)
for metric definitions and all provenance limits.

The candidate splits required diagonal cells into linear triangles; other cells
remain bilinear. Crossing required diagonals are explicit rejections. It preserves
nodes and grid borders, not arbitrary off-grid authored targets or incision
budgets. Reports keep nodal uphill failures, reconstruction volume and C0 slope
creases visible. D8 direction bias and process-grid sensitivity remain unresolved.
The command is a comparison of candidate generation surfaces, not an output editor.

The output contains `index.html`, completion-last `comparison.json`, and per-case
`comparison.png` plus `result.json` with all edges/routes, identities and timing.
Figures use actual sampled ground, the same path overlay and shared height range.
Work bounds are one million stations per profile and eight million per sampler
pass, with 32 million as the internal API ceiling. Full-route totals repeat
shared downstream reaches; unique-network measures count edges once. Whole-process
peak includes verification, arrays and rendering, not just interpolation.

The final 2026-09-24 matrix can be reproduced from its existing frozen artifacts:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.evolution.reconstruction --source artifacts/evolution-cohort-20260924 artifacts/evolution-ablations-20260924 artifacts/evolution-spacing-20260924 artifacts/evolution-rotated-20260924 artifacts/evolution-extent-20260924 artifacts/evolution-repeat-20260924 artifacts/evolution-timestep-20260924 --output artifacts/my-frozen-reconstruction
.\.venv\Scripts\python.exe -m pytest tests/test_evolution_surface.py tests/test_evolution_comparison.py
```

These artifacts are ignored local results. On another checkout, first regenerate
the reference cohort with the commands above; do not substitute a private map.
The initial failed 156.25 m state remains excluded and explicitly listed.


## Physical channel path comparison

The base environment can also compare bounded physical paths and their shared
ground against the bilinear and required-triangle controls:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.evolution.physical_comparison --source artifacts/evolution-cohort-20260924 artifacts/evolution-ablations-20260924 artifacts/evolution-spacing-20260924 artifacts/evolution-rotated-20260924 artifacts/evolution-extent-20260924 artifacts/evolution-repeat-20260924 artifacts/evolution-timestep-20260924 --output artifacts/my-physical-paths
.\.venv\Scripts\python.exe -m pytest tests/test_evolution_physical.py tests/test_evolution_surface.py tests/test_evolution_comparison.py
```

This reuses the frozen loader, station metrics and ground renderer; it does not
run or import Landlab. It prepares fixed-boundary, positive-area meshes with at
most 125 m / 0.24-cell node displacement. Heads, junctions, terminals, graph edges
and their nodal bed heights stay fixed. Physical sampling uses that same mesh;
there is no independent display smoothing. Default preparation uses eight
iterations, 17 lateral candidates and a 25 m source-height penalty scale.

The report includes complete matched-route coverage at 100/25 m, original nodal
climbs, D8 alignment, fan area, cut/fill rejection, reproducibility and cost.
`--maximum-cut-m` (default 30) and `--maximum-fill-m` (default 0) set **experimental
sampled diagnostics**, not application settings or overrides of native region
budgets. The frozen cohort carries no hard authored targets; off-grid anchor
conflicts are covered separately by synthetic tests. Figures sample actual
ground; `geometry.npz` retains the prepared coordinates and their numeric hash.

Compatible states also receive frozen-graph receiver/outlet diagnostics at exact
shared coordinates. Different forcing orientations or domain extents are not
silently compared as the same geography. Results include the complete solver
budgets because timestep and local-error controls can change together.

The [measured report](../../docs/research/2026-09-25-physical-channel-paths.md)
rejects promotion: long straight reaches, sampled fill/cut violations, nodal
climbs, fixed-divide conflicts and process-grid sensitivity remain. The constrained
network-led comparison below constructs terrain from inputs; it does not patch
a completed DEM. Use a new output folder and keep artifacts untracked.


## Constrained network-led terrain

Run the fixed public range/valley/lowland construction in the base environment:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.evolution.network_comparison --output artifacts/my-network-surface
.\.venv\Scripts\python.exe -m pytest tests/test_network_surface.py
```

No isolated history engine or private map is required. Existing SciPy provides
linear feasibility and a strictly convex surface fit. A shared physical network,
native regional cut/no-fill limits, protected divide, off-grid heights and
whole-cell downstream derivatives constrain the actual Float32 ground. Bounds
and numeric solver failures reject delivery rather than softening instructions.
This is pre-generation research, not a completed-DEM repair operation.

The fixed 32 by 24 km fixture runs at 1,000/500/250 m spacing plus a 90-degree
rotation, preserving a 2,400 m valley support radius. Full route profiles use
100/25 m stations. Independent routing uses both process nodes and a common
125 m evaluation grid, without filling or imposing river receivers. Fixed 1 km
mouth tolerance and explicit head sampling keep the capture check interpretable.
The [measured report](../../docs/research/2026-09-25-constrained-network-surface.md)
records the conservative-bound proof, numeric tolerances and remaining limitations.

Output includes source/target/fitted arrays, complete route metrics, actual-ground
panels, independent head-route figures, source/runtime/artifact hashes, timings,
repeat checks, native-bound diagnostics and an explicit quality decision. A
completed experiment may be **rejected** for terrain use. Failed executions write
`incomplete.json` and never publish `comparison.json`. Use a fresh output folder.
The measured candidate passes hard constraints but fails capture and adds sinks;
no normal-generation or editor path uses it.


## Valley-bank feasibility

Compare bank-to-bed support under the same fixture's hard constraints:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.evolution.valley_comparison --output artifacts/my-valley-support
.\.venv\Scripts\python.exe -m pytest tests/test_valley_support.py tests/test_network_surface.py
```

The base environment uses the existing SciPy fit. Fixed 250 m physical stations
and 500 m bank offsets are independent of process spacing. Banks refer to their
nearest network reach, including at junctions. Required bank height differences
taper to zero at the fixed coastal mouth. The 1,000/500/250 m cases and rotated
250 m case keep native cut/no-fill limits, hard heights and the protected divide.

Local interval conflicts report physical probes and unavoidable shortfalls.
Joint conflicts can run a bounded diagnostic for minimum common bank shortfall
with all other conditions fixed; its terrain is never returned. A separate
pinned-bed control must reject without lowering the pin. Timeout/numeric failure
is an incomplete execution, distinct from an infeasible constraint result.

Reports measure 25 m inward cross-sections as well as bank endpoints, complete
100/25 m river profiles, and independent routing at process/common 125 m spacing.
Outputs include support and actual-route figures, full metrics and hashes,
source/control fields and geometry. Candidate `ground_m` exists only in
constructed cases. Completion-last `comparison.json` can record infeasible cases
and a rejected quality decision; failed execution writes `incomplete.json`.
Existing output directories are never overwritten.

The [measured report](../../docs/research/2026-09-25-valley-bank-feasibility.md)
rejects this candidate: all 525 endpoint checks pass at 500/250 m, but inward
profiles and capture fail; the 250 m sink count increases from 19 to 30. The
connected-patch comparison below follows it, preserving the fixed hard control.
Normal generation and the editor do not use these research candidates.


## Connected valley patches and raster delivery

Construct local valleys and separately inspect their actual Float32 raster:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.evolution.patch_comparison --output artifacts/my-connected-valleys
.\.venv\Scripts\python.exe -m pytest tests/test_valley_patches.py tests/test_valley_support.py tests/test_network_surface.py
```

This base-environment experiment needs no private input or external history engine.
It keeps the fixed/native control and separately declares fresh composition with
a 600 m cut ceiling, 120 km3 volume limit, protected divide, no fill and unchanged
hard heights. Rounded swept sections share junctions and blend into broad relief;
an explicit last-reach transition meets the fixture's straight coast. Guides do
not move and no erosion history is simulated. This is not a completed-map editor.

The eight cases use fixed 250 m physical profiles with 1,000/500/250 m process
grids and a quarter-turn. Local and delivered surfaces are both rerouted at common
125 m spacing without fill or imposed receivers. Complete guide/bank checks,
hard targets, caps, composition volume, repeat, rotation and projection corrections
remain visible. Height-pin projection currently supports disjoint cells only;
arbitrary coastlines and general network layout are outside this bounded fixture.

The [measured report](../../docs/research/2026-09-26-connected-valley-patches.md)
records fresh local capture of 4/4 heads and no sinks, versus 3/4 and one sink for
250 m raster delivery. Some local guide/bank conditions also fail. The fixed/native
control remains rejected, and no candidate is production-eligible. The 250 m
coastal ablation isolates the mouth transition; node-only cut bounds that failed
between nodes were replaced by conservative incident-cell bounds without raising
the envelope. The automatic-layout follow-up below now tests that delivery blockage.

A fresh output folder receives `index.html`, completion-last `comparison.json`,
per-case `result.json`, numeric/source/artifact hashes and `fields.npz` with local,
control and delivered ground plus prepared geometry. Figures show actual ground,
rerouted paths and the coastal ablation. Hard-input/envelope violations fail the
execution with `incomplete.json`; drainage failures complete with a rejected
quality decision. Keep local artifacts ignored and retain failed runs as evidence.


## Hard-target-aware automatic guide layout

Run the bounded detour comparison while retaining all fixed-guide controls:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.evolution.layout_comparison --output artifacts/my-valley-layout
.\.venv\Scripts\python.exe -m pytest tests/test_valley_layout.py tests/test_valley_patches.py
```

Only an explicit automatic-edge mask permits movement. The experiment preserves
every original vertex, junction, head and mouth, carries original reach ownership
through new nodes, and checks whole polyline segments against hard-target clearance,
the domain, protected divide and other river edges. Default bounds are 1,000 m
clearance, a 1,500 m corridor, 100 m amplitude steps and 25% maximum length growth.
The 600 m / 120 km3 fresh envelope and no-fill/height constraints are unchanged.
Finite search exhaustion is not proof that the authored requirements conflict.

The nested `fixed-guides/` run keeps all eight previous controls. Four new cases
add actual geometry, input roles, matched source/outlet routes, local and delivered
metrics, hashes and truthful before/after overlays. The parent completion manifest
hashes its control manifest; failure cannot publish a completed parent. Use a new
output directory and keep generated artifacts ignored.

The [measured report](../../docs/research/2026-09-26-hard-target-valley-layout.md)
records 250 m raster capture improving from 3/4 to 4/4, with no interior sinks or
uphill guide routes and every interior checking sample reaching the coast. Bank
shape and coarse delivery remain rejected. Probe counts differ after segmentation
and are explicitly recorded; do not claim matched bank improvements from raw
counts. Normal generation and history integration remain gated on full acceptance.
