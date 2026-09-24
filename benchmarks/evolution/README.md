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
