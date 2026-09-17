# Current terrain research status

Reconciled on 2026-09-13 against code, tests, schemas and the installed Windows
Python environment. This is a status map; [TODO](../../TODO.md) owns the active
research register and the [strategy](../strategy/README.md) owns execution order.
Research IDs remain stable in dated reports when proposals leave the active scope.
Dated reports preserve measurements at their recorded revision, not timeless
performance claims. A source audit is not a successfully run engine comparison.

The noise-profile research, input editor and valley work were updated on
2026-09-16, with routing performance and crest refinement updated on 2026-09-17.
The external-engine inventory below retains the 2026-09-13 audit date.

## Implemented baseline

| Area | Implemented behavior | Remaining boundary |
|---|---|---|
| Input editor | Retained reference with freshness, geographic pan/zoom, property/geometry edits, undo/redo, guarded Save/Save As, resolution presets and ground inspection | Cancellation, automatic draft preview, comparison views, vertex insertion/removal, climate-region inputs |
| Local numeric builds | Saved-project CLI, Float32 NPY/GeoTIFF, review NPZ, previews, diagnostics and completion hashes | World placement, vector products, external desktop GIS acceptance |
| Zoom-driven local detail | Coordinate-addressed fields, shared-sample/grid foundations and a geographic viewport | Regional build requests, added detail, parent/overlap consistency, inherited hydrology and bounded caching |
| Coordinates/seeds (R01-R03) | Source/local round trips, endpoint grids, actual spacing metadata and portable named seeds | Planetary CRS, configurable process spacing, cell-average/resampling policy |
| Authored macro routing (R04-R05) | Authored macro, regular crest probes and bounded carrier-root/tangent searches shape a shared Priority-Flood/D8/MFD graph; topology and finished-field conflicts are exported | Other hidden extrema, filled barriers and unresolved final-ground climbs remain; routes are not validated rivers |
| Valley reconstruction | Bounded cubic fields, selected-diagonal shaping and source-aware cardinal/diagonal floor fitting; canonical nodes and cut ceilings preserved | D8 turns, hidden crests beyond cut limits, endpoint/retention conflicts and complete-field error bounds |
| Regional landforms | Plain/hill/plateau/mountain recipes, orientation, transitions and regional cut limits | Distribution targets, transition-gradient validation, related geological regions |
| Structural authoring | Absolute/relative point-anchored profiles, directed valley floors and compatible junctions | Direct per-vertex controls, explicit passes, asymmetric sides and generated branching |
| Basin intent and flow | Lake/dry footprints retain terrain and captured MFD area; eligible outlets transfer collected area conservatively | Runoff/discharge, equilibrium water levels, controlling sills, lake chains and nested depressions |
| Finer water review | Shoreline/contact/full-route profiles, regional transitions, procedural density, context shoulders, wet-link separation and dry-path checks | Residual blended/grazing extrema, continuous error bounds, complete-budget cost and off-grid/path alternatives |
| Measurements (R41) | Elevation min/max/mean/deviation and masked X/Y differences/semivariances at physical lags | Detrending, arbitrary direction, terrain atlas, multiscale/topological descriptors |
| Water demand forecast | Saved-project shoreline and potential internal-network plans, exact counts or bounded lower bounds, verified source identity | External routes/contacts, actual eligibility, whole-project cost and workbench access |
| Performance (R45-R47) | Selective sampling, exact water/guide reuse, ordered D8 array sweeps, streamed regional carriers and repeatable public-fixture benchmarks | Full many-region builds, larger grid/index crossover, export cost and native migration evidence |

The current format inventory lives in [schemas](../../schemas/README.md), and
algorithm identities, sample budgets and numeric evidence belong to the
[build](../terrain-builds.md) and [water](../terrain-water.md) contracts.
No new terrain/schema contract is implied by this status page.

R04 and R05 are complete as bounded routing/review slices. Other unchecked R IDs
may have partial foundations; their broader experiment is not complete merely
because related controls or exports exist. In particular, the four recipes do
not close regional distribution/geology research, and shared-point equality does
not prove cell-average equivalence. R07 remains open: dry-basin retention does not
enable negative land heights or bathymetry.

The [cubic reconstruction comparison](2026-09-16-bounded-valley-reconstruction.md)
records reduced cell-edge slope breaks. The
[connected-diagonal follow-up](2026-09-16-connected-diagonal-valleys.md) reduces
scalloping and sampled climb size on eight baseline and three additional cases.
Canonical routing matched; water outcomes matched in the eight performance
cases. The [source-aware floor follow-up](2026-09-16-source-aware-channel-floors.md)
then fits cuts to the actual source between nodes, reducing cardinal as well as
diagonal climbs. Off-grid heights intentionally change; large hidden crests
beyond the current cut ceiling remain. The
[mountain-crest routing follow-up](2026-09-16-mountain-crest-routing.md) now observes
selected crest crossings and rebuilds the drainage graph around lower passes.
Canonical routing and derived cuts can change, under the same budget policy.
Complete-field clearance, other hidden extrema, full downstream conditioning,
grid-aligned turns and physical river validity remain open.

The [routing-cost follow-up](2026-09-17-drainage-routing-cost.md) reduces repeated
Python work and bounds temporary carrier storage. All measured numeric products
and diagnostic summaries match; broader terrain-quality and whole-project scale
questions remain separate from that optimization.

The [crest-refinement follow-up](2026-09-17-refined-mountain-crests.md) admits
same-sign candidates and searches observed crossings/tangent approaches. It
retains every earlier regular observation and sharply reduces understated
barriers against dense finite references. Finished-channel metrics remain mixed;
features within one unsampled interval and full-route validity remain open.

## Research that has not been adopted

Midpoint-residual refinement is implemented only in the research harness.
The [measured experiment](2026-09-13-adaptive-water-profile-refinement.md) exposes
false convergence against a denser finite reference, including an exactly zero
indicator that misses a 20 m peak. It is not a runtime clearance rule or a
continuous error bound. Conservative bounds for the complete blended field
remain an open prerequisite for certified adaptive stopping.

The [noise-component experiment](2026-09-13-noise-component-bounds.md) now provides
natural and polynomial/cell enclosures with explicit rounding allowances, a
Float32 field boundary and complete cell-work budgets. These bound the isolated
noise component under the documented arithmetic assumptions. They do not cover
coast weights, regional/constraint blending, longitudinal profiles or incision,
and have not been adopted for runtime water decisions. The subsequent
[profile-strip experiment](2026-09-14-noise-profile-bounds.md) restricts cell work
along the rounded affine path and adds conservative ordered-rise bounds. All
864 profile trials fit the current limits, including broad diagonal cases that
exhaust rectangle bounds. Fine spans are slower and the roughest tested field
still has a 66.43 m uphill gap at 4096 subdivisions. Geometry clipping alone
therefore does not supply a practical full-field stopping rule. The
[bounded-refinement follow-up](2026-09-16-bounded-noise-refinement.md) adds hybrid
rectangle/strip selection and adaptive subdivision using local extrema and
ordered-rise gaps. It accounts for every completed wave against cumulative
cell/strip/sample limits and publishes no accepted profile on exhaustion.
This is a bounded stopping contract for the isolated noise field; the full
terrain composition and its water decisions remain open.

Local RBF/screened-Poisson replacement, time-stepped erosion, bedrock/sediment
transport, coupled ridge/drainage generation, specialized glacial/wind/volcanic
families, Earth-analogue synthesis and learned proposals remain candidates.
Global climate/ecology still needs its input, scale and validation contracts.
The input editor is followed by generation, including planned zoom-driven local
enrichment. [ADR-0048](../adr/0048-keep-zoom-driven-detail-generation.md) corrects
the earlier exclusion of regional generation; manual sculpting of completed
outputs remains out of scope. The complete alternatives and gates remain in TODO.

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

- [Bound-driven refinement](2026-09-16-bounded-noise-refinement.md) compares hybrid
  geometry and selective subdivision against uniform refinement and strip-only
  controls across 144 fresh-process runs. Adaptive hybrid accepts 99/144 distinct
  input/tolerance combinations versus uniform's 80/144; on paired successful
  six-octave cases it saves about 70% of cell work. Rough/high-detail cases still
  exhaust cumulative budgets; this is not a full-field water-clearance result.

- [Rounded profile bounds](2026-09-14-noise-profile-bounds.md) compare three
  policies across 216 fresh-process runs. They preserve all previous control
  evidence, bound rises within and across intervals, and separate saved cell
  work from remaining local uncertainty and strip-planning overhead.
- [Procedural-noise bounds](2026-09-13-noise-component-bounds.md) compare component
  tightness and cost, verify rounding/finite-reference inclusion and fix the
  twelfth-octave hash overflow warning without changing generated noise values.

- [Prepared guide bounds](2026-09-13-water-guide-bounds.md) reject distant
  geometric candidates without changing sampling policy. The paired comparison
  covers 4/16 lakes, 16/64 points and broad overlap, with separate forecast,
  generation, review/planning and evidence-serialization measurements.
- [Adaptive profile refinement](2026-09-13-adaptive-water-profile-refinement.md)
  measures midpoint residuals, finite-reference errors and bounded exhaustion;
  apparent convergence does not authorize a new runtime sampling policy.
- [Water-budget forecasting](2026-09-13-water-budget-forecast.md) adds read-only
  saved-project demand planning and preserves the existing terrain/sampler.
- [Detail and context sampling](2026-09-13-detail-and-context-sampling.md) is
  the latest station-policy change: global/regional lattice scales and context
  shoulders guide the shared sampler. The expanded comparison covers oblique profiles,
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
Prepared guide bounds also avoid unnecessary geometry calls; those spatial
bounds are not elevation-error bounds. Regional, procedural and context
guidance have finite-reference evidence.
The [water-budget command](../terrain-water-budget.md) now exposes shoreline
and potential internal-network demand using shared planning; the
[forecast report](2026-09-13-water-budget-forecast.md) measures its cost and verifies
unchanged terrain/evidence. It does not estimate whole-project or export cost.
Next, compare reusable refinement work and tighter component correlation where
high-detail bounds remain unresolved, and compose conservative bounds beyond
the isolated noise term. Measure whole-project sampling cost, then
define sill/storage semantics before lake chains. Five detail octaves keep the public flat-routing example within budget;
its six-octave regression deliberately retains every dry donor after exhaustion.
Do not present denser probes as continuous clearance or a physical lake model.
Keep the full roadmap instead of promoting every research direction into
immediate implementation.
