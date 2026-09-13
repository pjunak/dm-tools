# Current terrain research status

Reconciled on 2026-09-13 against code, tests, schemas and the installed Windows
Python environment. This is a status map; [TODO](../../TODO.md) owns the complete
R01-R47 register and the [strategy](../strategy/README.md) owns execution order.
Dated reports preserve measurements at their recorded revision, not timeless
performance claims. A source audit is not a successfully run engine comparison.

## Implemented baseline

| Area | Implemented behavior | Remaining boundary |
|---|---|---|
| Local numeric builds | Saved-project CLI, Float32 NPY/GeoTIFF, review NPZ, previews, diagnostics and completion hashes | World placement, vector products, external desktop GIS acceptance |
| Coordinates/seeds (R01-R03) | Source/local round trips, endpoint grids, actual spacing metadata and portable named seeds | Planetary CRS, configurable process spacing, parent averages/refinement |
| Authored macro routing (R04-R05) | Authored terrain shapes canonical planning; D8/MFD topology and finished-field conflicts are exported | Filled routes are not validated rivers; unresolved uphill channels remain |
| Regional landforms | Plain/hill/plateau/mountain recipes, orientation, transitions and regional cut limits | Distribution targets, transition-gradient validation, related geological regions |
| Structural authoring | Absolute/relative point-anchored profiles, directed valley floors and compatible junctions | Direct per-vertex controls, explicit passes, asymmetric sides and generated branching |
| Basin intent and flow | Lake/dry footprints retain terrain and captured MFD area; eligible outlets transfer collected area conservatively | Runoff/discharge, equilibrium water levels, controlling sills, lake chains and nested depressions |
| Finer water review | Shoreline/contact/full-route profiles, regional transitions, procedural density, context shoulders, wet-link separation and dry-path checks | Residual blended/grazing extrema, continuous error bounds, complete-budget cost and off-grid/path alternatives |
| Measurements (R41) | Elevation min/max/mean/deviation and masked X/Y differences/semivariances at physical lags | Detrending, arbitrary direction, terrain atlas, multiscale/topological descriptors |
| Performance (R45-R47) | Selective land sampling, exact water-sample reuse and a 13-case benchmark harness | Remaining network/serialization cost, complex-scene crossover, 4096/memory budgets and native migration evidence |

The current format inventory lives in [schemas](../../schemas/README.md), and
algorithm identities, sample budgets and numeric evidence belong to the
[build](../terrain-builds.md) and [water](../terrain-water.md) contracts.
No new terrain/schema contract is implied by this status page.

R04 and R05 are complete as bounded routing/review slices. Other unchecked R IDs
may have partial foundations; their broader experiment is not complete merely
because related controls or exports exist. In particular, the four recipes do
not close regional distribution/geology research, and shared-point equality does
not prove parent-cell averaging. R07 remains open: dry-basin retention does not
enable negative land heights or bathymetry.

## Research that has not been adopted

Local RBF/screened-Poisson replacement, time-stepped erosion, bedrock/sediment
transport, coupled ridge/drainage generation, specialized glacial/wind/volcanic
families, Earth-analogue synthesis and learned proposals remain candidates.
Global climate/ecology and regional refinement still need their input, scale and
validation contracts. The complete alternatives and gates remain in TODO.

SciPy, Landlab and Numba are not installed in the environment checked for this
audit. GRASS, Whitebox, SPACE, HighMap, GPU transport, geological engines and
learned tools appearing in older reports are references/candidates, not new
runtime dependencies or successful end-to-end comparisons. Package/Windows,
Python, hardware and license claims from those reports retain their original
dates and require a fresh source/runtime check before use. No external engine
or paper shortlist was re-evaluated as part of this documentation audit.

[The dependency register](../DEPENDENCIES.md) lists adopted packages. The local
application remains Python with NumPy/Shapely numerical and geometric work and
Rasterio/GDAL inside the export adapter. A future Rust port needs representative
measured benefit and packaging/workflow evidence; it is not the next prerequisite.

## Evidence and next experiments

- [Detail and context sampling](2026-09-13-detail-and-context-sampling.md) is
  the latest accepted change: global/regional lattice scales and context shoulders
  guide the shared sampler. The expanded comparison covers oblique profiles,
  fixed-input field preservation, residual misses and complete-budget failures.
- [Regional guidance and convergence](2026-09-13-water-sampling-convergence.md)
  records the preceding 64-run matrix and regional barrier detection. Its
  procedural/tail misses motivated the current change; the original measurements
  remain historical evidence rather than current error claims.
- [Dry collection paths](2026-09-11-dry-collection-paths.md) records full-path
  head checks, preserved terrain/area and measured planning/sampling cost. Its
  fresh-process generation measurements are distinct from prepared-stage timings and full CLI-build timings.
- [Feature-guided sampling](2026-09-11-feature-guided-water-sampling.md) shows
  why regular quarter-grid stations miss narrow cores. Radius/4 guidance is a
  bounded sampling choice, not a terrain error bound. The later convergence
  matrix extends these measurements across regions, procedural detail and tails;
  broad geometric/feature distributions and accuracy bounds remain open.
- [Selective sampling](2026-09-05-selective-terrain-sampling.md) records a
  successful exact-output optimization and a slower rejected coast index.
  Neither result proves the best method for today's enlarged water workload.

Exact feature/sample reuse is now implemented with preserved station counts and
evidence; see the [measured follow-through](2026-09-13-water-sampling-reuse.md).
Regional, procedural and context guidance now have finite-reference evidence.
Next, compare bounded local error refinement for blended/grazing extrema and
whole-project sampling cost, then define sill/storage semantics before lake
chains. Five detail octaves keep the public flat-routing example within budget;
its six-octave regression deliberately retains every dry donor after exhaustion.
Do not present denser probes as continuous clearance or a physical lake model.
Keep the full roadmap instead of promoting every research direction into
immediate implementation.
