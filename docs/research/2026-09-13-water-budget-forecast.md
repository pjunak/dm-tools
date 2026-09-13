# Water-sampling budget forecast - 2026-09-13

Status: implemented and measured. The new read-only command exposes shoreline
and potential internal-network station demand before a detailed build.
[ADR-0046](../adr/0046-forecast-water-sampling-budgets.md) owns the shared-planning
boundary and corrects earlier wet-budget documentation. The
[command guide](../terrain-water-budget.md) explains usage and interpretation.

## Implemented behavior

- A shared prepared field supplies normal generation and the forecast. The
  latter evaluates only finished Float32 canonical ground, irrespective of
  delivered pixel resolution.
- Shorelines use the same normalized vertices. Vector-contained basin graphs,
  wet/dry candidate selection and bounded network planning now have one owner
  used by both actual review and forecasting.
- Completed plans report exact requested counts; excessive plans report required
  lower bounds, visited/candidate profile counts and the first limiting budget.
  Repeated stations count against the budget exactly as they do at runtime.
- Internal networks are potential demand. The forecast does not evaluate
  finer shoreline/outlet/wet gates, so full review may skip those networks.
  External route/contact demand, unique evaluations and exports are excluded.
- Saved-project, SVG and installed source/runtime identity are checked before
  and after planning. The CLI prints the relevant hashes and creates no build.

The actual unchanged limits are 65,536 stations per profile, **65,536 per wet
network**, 262,144 per dry network, and batches of 4,096 evaluation positions.
ADR-0044/0045 and the preceding detail/context report incorrectly generalized
the dry-network cap; appended correction notes preserve their original history.
The new command does not alter any limit, detail setting or clearance gate.

## Demand agrees with full review

At seed 42 on the public five-detail flat fixture, shoreline/wet/dry demand is
2,195 / 6,475 / 199,188. The dry network has 17,042 candidate links and fits its
budget. Raising detail to six stops dry planning at a required lower bound of
262,150; actual review reports the same failure and retains dry donors.

Forecast/executed counts and status agree wherever full review actually performs
that profile/network. Closed lakes retain shoreline-only demand, dry basins have
no water profiles, and tiny footprints expose zero canonical nodes. A blocked
internal-water example still has potential dry demand even though actual review
skips that network. It is not a false promise of collection.

Changing resolution from 64 to 4,096 and reversing constraint order preserve the
same forecast. Tests also verify per-profile, coarse-network and refinement
budget failure without allocating any fine station arrays or evaluating their
ground, and reject saved inputs/runtime changed during planning.

## Fresh-process measurements

Windows 11 AMD64, CPython 3.14.7, NumPy 2.5.2, Shapely 2.1.2 / GEOS 3.13.1.
Eight case/resolution pairs, two operations, three repetitions each: **48 fresh
processes**. Alternating operation order reduces systematic order bias. Seed is
42 and public settings are unchanged except the named six-detail variant and
output resolution. No tests ran concurrently with these measurements.

Times below cover in-memory forecast or generation after imports/input loading;
they exclude CLI startup, file-hash checks, export and serialization. Memory is
process peak working set through the operation, including imports, not incremental
scratch allocation. Generation includes real water review; the forecast does not.

| Fixture | Pixels | Forecast seconds | Generation seconds | Peak MiB, forecast / generation |
|---|---:|---:|---:|---:|
| regional | 768 | 0.5414 | 1.5739 | 89.2 / 132.2 |
| water | 768 | 0.4684 | 1.5207 | 89.4 / 136.9 |
| outlet | 768 | 1.3946 | 3.2909 | 90.3 / 137.1 |
| flat | 768 | 1.0543 | 3.2683 | 90.9 / 137.1 |
| flat6 | 768 | 1.0083 | 2.2021 | 89.1 / 137.0 |
| internal | 768 | 1.4477 | 1.8681 | 90.1 / 136.8 |
| dry | 768 | 1.4432 | 3.6333 | 90.0 / 136.9 |
| flat | 4096 | 1.1398 | 38.4246 | 91.2 / 478.1 |

The 4,096-pixel flat fixture spends about 1.14 s forecasting versus 38.42 s
generating, with 91.2 versus 478.1 MiB median process peak. This avoids generating
a large delivered surface just to discover water-sampling demand. These timings
compare planning a subset of water work with full generation. Output resolution
does not change the requested stations, and this small fixture matrix does not establish
a universal speed ratio. The blocked internal scene offers much less saving
because forecast planning includes potential dry work that full review skips.

### Paired generation control

Some initial generation times were higher than the earlier dated measurements.
A separate 18-process run alternated the original `d07efdc` source and current
source on three water-heavy scenes, again three repetitions. The original source
was extracted into an ignored control directory; subprocess imports were verified
to resolve to distinct source roots. Both versions used current identical inputs.

| Fixture | Generation seconds, control / current | Prepared water review seconds, control / current |
|---|---:|---:|
| flat | 3.1829 / 3.1413 | 1.5726 / 1.5442 |
| internal | 1.9280 / 2.0711 | 0.2003 / 0.2018 |
| dry | 3.8647 / 3.8571 | 2.1111 / 2.1238 |

The prepared water-stage medians differ by less than 0.03 s here. Whole-generation
medians vary more, including a 7.4% increase on the internal scene in this paired
sample. These short runs do not establish a generator speed improvement or a
stable zero-overhead guarantee; keep the measured variation visible. A larger
many-constraint/many-lake workload is still needed for planning/index crossover.

## Output and build verification

All 27 numeric hashes and the complete authored-water-evidence hash match the
pre-refactor controls on seven 768-pixel fixtures. The additional 4,096-pixel
fixture repeats exactly across its three fresh generation processes; every
forecast repeats exactly too. The paired source comparison also preserves all
numeric and water-evidence hashes. Area-balance error stays below 1e-6 km2.

A fresh public flat-outlet CLI build validates against build schema 16. All 13
export product hashes and byte sizes match the pre-refactor build, including
numeric arrays, diagnostics, PNGs and GeoTIFF. TIFF ground/mask match NPY data,
retained-plus-outgoing area exactly matches captured footprint area, and the
fixture retains 1,507 flat ranks. The manifest's new source identity gives a new
build ID, as intended. No project/build format or numeric algorithm ID changed.

Final checks: **485 pytest tests passed in 262.29 s**; full Ruff passed and
strict Pyright reported zero errors/warnings. The installed CLI command and
fresh build workflow passed, and all 265 local links across the 16 changed
Markdown files resolved. The visible feature is CLI-only; no workbench widget
was added in this slice.

## Provenance

Base revision: `d07efdc`. Installed package source SHA-256 for the final measured
implementation: `fa0c985857d9646781feb6e974b956dfb35ea9dae6357fbf62cb75713113f4bc`.

Ignored local evidence files (not distributable build inputs):

- `artifacts/water-budget-performance-20260913.json`: 48-operation matrix,
  SHA-256 `30d61703906101f44156c6be41b72949975b6131834a02c6a3d77c80212bbd24`.
- `artifacts/water-budget-paired-control-20260913.json`: 18-operation paired
  comparison, SHA-256 `c994e31ab77e92f468f49327ced7414cd105d9d95af53e5059b615c1677fbe33`.
- `artifacts/water-budget-control-imports-20260913.json`: distinct import roots
  and runtime fingerprints for the original/current source.
- `artifacts/water-budget-build-validation-20260913.json`: verified schema,
  products, TIFF/mask and contributing-area identities.
- `artifacts/water-budget-build-20260913/manifest.json`: build ID
  `7bd2dedc6651a48f545fb0be1029f3b526ce8c5d12f981b919a612648c66d009`.

The original unchanged-input controls are in
`artifacts/detail-context-performance-final-20260913.json` (SHA-256
`13330e33cf76683da19507352a9aca6802fc2b066f1e8b768a078e007ae940e5`).
The local matrix helper is `artifacts/measure_water_budget.py` (SHA-256
`dd0e626a5a011fa3720f26984c824b2159396c49387e8533d38d12f86c15e8ad`); it uses
`benchmarks.terrain.fixture`, `numeric_hashes`, `peak_resident_bytes`,
`generate_terrain` and `forecast_water_sampling` in fresh Python processes.
Package source was held fixed and rechecked across measurement and validation.

## Next work, in order

1. Investigate conservative local error refinement for remaining blended/grazing
   extrema. Preserve complete budgets and explicit unresolved results; demand
   visibility does not establish continuous terrain clearance.
2. Measure many-lake/many-constraint planning, total profile/evidence memory and
   serialization before selecting an index, shared-path reuse or larger limits.
   Evaluate workflow access and report export without automatically doubling
   generation work through a mandatory preflight.
3. Define controlling-sill, inflow/storage and lake-level assumptions before
   connecting explicit lake chains; then compare bounded breach/reroute proposals
   and expose reviewable river networks.

These items are tracked in [TODO](../../TODO.md) and the
[current strategy](../strategy/README.md). Python remains suitable for these
experiments; this slice adds no native dependency or compatibility machinery.
