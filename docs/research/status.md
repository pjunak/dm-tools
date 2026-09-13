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
| Finer water review | Shoreline/contact/full-route profiles, wet-link separation, dry-link alternatives and chosen-path cumulative checks | Sampling error bounds, off-grid 2D passages and alternatives after cumulative rejection |
| Measurements (R41) | Elevation min/max/mean/deviation and masked X/Y differences/semivariances at physical lags | Detrending, arbitrary direction, terrain atlas, multiscale/topological descriptors |
| Performance (R45-R47) | Selective land sampling and a 13-case fresh-process benchmark harness | Repeated network work, complex-scene crossover, 4096/memory budgets and native migration evidence |

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

- [Dry collection paths](2026-09-11-dry-collection-paths.md) is the latest
  accepted behavior baseline: full-path head checks, preserved terrain/area and
  measured planning/sampling cost. Its fresh-process generation measurements
  are distinct from prepared-stage timings and full CLI-build timings.
- [Feature-guided sampling](2026-09-11-feature-guided-water-sampling.md) shows
  why regular quarter-grid stations miss narrow cores. Radius/4 guidance is a
  bounded sampling choice, not a terrain error bound. Broader procedural,
  regional-transition and feature-tail convergence remains necessary.
- [Selective sampling](2026-09-05-selective-terrain-sampling.md) records a
  successful exact-output optimization and a slower rejected coast index.
  Neither result proves the best method for today's enlarged water workload.

Next, measure exact reuse of repeated network preparation/evaluation without
removing probes, relaxing budgets or dropping failure evidence. Then compare
sampling refinement/offsets on procedural, transition and tail fixtures before
sill/storage semantics and lake chains. Keep the full roadmap instead of
promoting every interesting research direction into immediate implementation.
