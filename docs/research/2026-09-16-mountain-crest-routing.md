# Mountain-crest observations for drainage routing

Date: 2026-09-16. Implemented decision: [ADR-0053](../adr/0053-observe-mountain-crests-in-drainage.md).

## Problem and alternatives

The [previous diagnosis](2026-09-16-source-aware-channel-floors.md) found mountain
crests hidden between descending routing nodes. Their required cuts exceeded
the automatic incision ceilings. More reconstruction within those ceilings
could not remove the obstacles, so this change lets planning observe them.

Three public-fixture experiments compared approaches against commit `165f789`.
They used seven interior observations per candidate edge and the existing
regional/global cut-budget policy:

| Approach | Regional 104729 maximum climb | Regional 20260902 maximum climb | Regional macro probes |
|---|---:|---:|---:|
| Previous generator | 383.26 m | 212.05 m | 0 additional |
| Local receiver swaps within the old filled ordering | 383.23 m | 212.07 m | Selected sources and their lower neighbours |
| Rebuild with observations on every land-land D8 edge | 53.38 m | 73.05 m | 899,857 per case |
| Rebuild with targeted mountain-carrier crossings | 54.28 m | 58.36 m | 8,484 / 9,898 |

The first seed uses 257 profile stations, the second 65. These are maxima across
selected channels with descending endpoints, not comparisons of one fixed edge.
Local swaps could not escape the previous ordering and slightly increased mean
excursions in these cases. Rebuilding the graph could find lower passes. Full
edge sampling also changed non-mountain cases, sometimes worsening their
profiles, and cost about 2.21-2.22 seconds just to prepare regional observations
in the exploratory process. Targeted observation preparation took about
0.037-0.041 seconds. These exploratory timings **exclude the remaining graph and
generation work** and are not a measured end-to-end speedup.

The scripts and complete exploratory results remain in the ignored local
`artifacts/crest-routing-2026-09-16/` directory. They are development evidence,
not a retained runtime mode or independent validation set.

## Adopted algorithm

Share the mountain recipe's broad noise carrier with routing. For positive
mountain relief, endpoint sign changes or zeros identify candidate D8 edges
near the region. Buffer the region by the longest grid edge so an intersecting
edge is not excluded merely because its endpoints lie outside the polygon.
Union candidates across overlapping regions, then sample the authored macro at
fractions 1/8 through 7/8. Each undirected edge is sampled once; batches contain
at most 4096 edges. A symmetric barrier stores the maximum observed height,
including both endpoints. Non-finite or incorrectly shaped observations fail.

Priority-Flood can improve a queued candidate through a later, lower pass.
With edge barriers, settle nodes on removal from the priority queue, rather
than on first discovery. Both MFD flow division and the steepest D8 receiver
then require a strictly lower neighbour reachable over the observed barrier.
Without raised observations, retain the node-only primitive and its cheaper
first-discovery queue handling. Retention terminals keep their authored roles.

The canonical grid remains 257 samples on its longest side. The filled surface
is temporary routing data. Recompute accumulation, channel selection, cuts and
local ceilings from the resulting graph, under unchanged regional/global budget
formulas. Authored inputs, landform recipes and stage seeds retain their meaning.
Generator identity becomes `coastline-constraint-terrain@12`; automatic valleys
become `regional-budget-mfd-d8-valleys@10`. No dependency, schema, user setting,
legacy loader or finished-map editing operation is added.

## Reproducible production comparison

Import baseline `165f789` from an isolated source archive. Run the maintained
`benchmarks.channel_profiles` harness with the same fixtures and environment
against baseline and current source. Reports retain input/runtime/source IDs,
canonical-array and Float32 profile hashes, station counts and non-finite counts.
No runtime source changed during measurement. The six complete reports are
`before/after-profiles.json`, `before/after-dense.json` and
`before/after-new-seeds.json` under the local experiment directory.

```powershell
.\.venv\Scripts\python.exe -m benchmarks.channel_profiles --output artifacts/crest-main.json
.\.venv\Scripts\python.exe -m benchmarks.channel_profiles --case archipelago square regional --seed 104729 --stations 257 --output artifacts/crest-dense.json
.\.venv\Scripts\python.exe -m benchmarks.channel_profiles --case regional --seed 7 3001 --stations 257 --output artifacts/crest-new-seeds.json
```

The default matrix is example/regional/authored/outlet with seeds 42/20260902.
The two additional regional seeds were selected after adopting the algorithm
and were not used in the development experiments. This is a small additional
check, not a broad statistical claim about all seeds.

An uphill excursion is the largest rise above an earlier running minimum along
an edge. Heights are delivered Float32 values promoted to Float64 before
subtraction. Only finite profiles with endpoint drop greater than 0.01 m enter
these summaries; mean values include zero-excursion edges.

| Regional seed | Stations | Descending edges before / after | Uphill interiors before / after | Mean m before / after | P95 m before / after | Maximum m before / after |
|---|---:|---:|---:|---:|---:|---:|
| 42 | 65 | 2392 / 2405 | 494 / 494 | 0.723 / 0.725 | 3.608 / 3.591 | 59.00 / 58.99 |
| 20260902 | 65 | 2422 / 2405 | 601 / 586 | 0.913 / 0.827 | 3.804 / 3.795 | 212.05 / 58.36 |
| 104729 | 257 | 2585 / 2595 | 555 / 573 | 0.834 / 0.654 | 2.893 / 3.126 | 383.26 / 54.28 |
| 7, additional | 257 | 2182 / 2185 | 580 / 564 | 1.163 / 0.865 | 4.604 / 4.473 | 483.64 / 53.04 |
| 3001, additional | 257 | 3147 / 3130 | 832 / 828 | 0.879 / 0.876 | 3.170 / 3.168 | 64.89 / 64.91 |

The three large outliers fall by 72.5-89.0%. This is **not universal improvement**:
seed 104729 has more small flagged climbs and higher P95, seed 42 has a slightly
higher mean, and seed 3001 has a slightly higher maximum. Network and channel
selection change, so the measured edge populations also differ.

All eight non-mountain case/seed pairs retain identical canonical inventories
and profile hashes: example/authored/outlet at both default seeds, plus
archipelago/square at 104729. The archipelago still has **three non-finite
profiles in both versions**, excluded and unresolved. The other twelve pairs
have none. All thirteen input and harness identities match. Canonical axes match
in every pair. All five regional pairs change receivers, selected channels,
incision, nodal ceilings and suppression; these are intentional derived changes.
Regression tests separately compare unchanged authored macro samples and land
masks, and verify incision remains within ceilings and regional budget policy.

## Appearance

Generate matched 1025 px scientific previews for regional seeds 104729 and
20260902. Inspect identical crop coordinates in `crest-comparison.png`; full
previews and Float32 grids are retained under `before-visuals/` and
`after-visuals/`. The change relocates local valley shading while preserving the
large mountain forms. At this scale the visible difference is subtle. Grid-based
bends and the existing ridge recipe remain visible; this is not a new landscape
style or a solution to straight-channel appearance.

| Regional seed | DEM difference RMS | Maximum lowering | Maximum raising |
|---|---:|---:|---:|
| 104729 | 3.33 m | 223.38 m | 186.95 m |
| 20260902 | 4.00 m | 245.79 m | 181.29 m |

Land masks match in both visual pairs. Raising relative to the old build can
result from moving or reducing an old cut; it is not permission to raise the
source surface or to expand an incision budget.

## Performance and output identity

Run the maintained `benchmarks.terrain` harness at 513 px, with fresh processes
and two repetitions per case/seed. The initial after batch was substantially
slower even for unchanged fixtures, so repeat the complete before/after pair.
Retain all four repetitions per version: **64 total runs**. Reports are
`before/after-performance.json` and `before/after-performance-repeat.json`.
No test suite, visual generation or runtime edits competed with these runs.
Times exclude file export; memory is lifetime process peak resident usage,
including imports, rather than an isolated allocation count.

| Case / seed | First pair s before / after | Repeat pair s before / after | All-run median s before / after | Median peak change MiB |
|---|---:|---:|---:|---:|
| example / 42 | 0.987 / 1.242 | 1.000 / 1.039 | 0.995 / 1.087 | -0.23 |
| example / 20260902 | 0.994 / 1.311 | 1.002 / 1.037 | 0.996 / 1.134 | -0.01 |
| regional / 42 | 1.140 / 1.670 | 1.150 / 1.349 | 1.143 / 1.507 | +0.68 |
| regional / 20260902 | 1.144 / 1.883 | 1.164 / 1.353 | 1.148 / 1.605 | +0.84 |
| authored / 42 | 1.744 / 2.870 | 1.769 / 2.012 | 1.755 / 2.483 | +0.03 |
| authored / 20260902 | 1.751 / 2.446 | 1.778 / 1.856 | 1.759 / 2.118 | +0.07 |
| outlet / 42 | 2.733 / 3.899 | 2.821 / 2.820 | 2.760 / 3.168 | +0.43 |
| outlet / 20260902 | 2.733 / 4.047 | 2.783 / 2.943 | 2.754 / 3.459 | +0.95 |

In the repeat, regional generation adds 0.19-0.20 s (16.3-17.3%). The first pair
showed much larger penalties that were not reproduced. For example/42, current
runs span 1.037-1.351 s, while baseline runs span 0.983-1.000 s. Non-mountain
repeat medians vary from essentially unchanged to 13.7% slower. These data
support additional regional routing cost, but not a precise universal overhead
or a speedup. Keep hot-loop and many-region scaling work in TODO. Median peak
memory increases by 0.68/0.84 MiB in the two regional cases; the full matrix spans
-0.23 to +0.95 MiB. Larger-resolution and many-region costs remain unmeasured.

```powershell
.\.venv\Scripts\python.exe -m benchmarks.terrain --case example regional authored outlet --resolution 513 --seed 42 20260902 --repeats 2 --output artifacts/crest-performance.json
```

All repetitions retain identical per-version numeric hashes and input identity.
Across versions, **every measured product and summary remains identical in all
six non-mountain performance cases**. The two regional cases change elevation,
receivers, accumulation, channels, cuts, nodal limits, canonical final heights,
basin labels and conditioned final receivers. The conflict raster also changes
for regional/20260902. Land masks, axes and authored-water/outflow products
retain their hashes in all eight cases. This does not establish unchanged water
behavior for untested mountain-and-lake combinations.

Regional final-ground diagnostics remain mixed. For seed 20260902, node-to-node
uphill channel edges fall from 194 to 188 and their maximum rise from 219.50 to
210.77 m, but depression cells rise from 5178 to 5223 and potential sinks from
237 to 238. The diagnostic fill-volume estimate rises from 326,007 to
339,528 km3. Seed 42 adds one basin candidate while its fill volume decreases
slightly. These are diagnostic filling estimates, not generated lake volumes.
The large endpoint climbs are a different population from the preceding table,
which specifically measures interiors of edges with downhill endpoints. Neither
measure supports a claim that whole river routes are now physically valid.

## Checks and next work

- Full suite: **797 tests passed**. Ruff passes; strict Pyright reports zero
  errors and warnings. All 562 local Markdown file targets resolve. No
  editor UI behavior was changed.
- New regressions cover late lower passes, shared D8/MFD barriers, conservation,
  strictly decreasing routing levels, retention, input immutability, symmetric
  observation reuse, bounded batches, invalid observations and regional examples.
- Profile the added routing-loop cost and measure many-region preparation
  before expanding observation coverage. Carrier storage currently grows with
  the number of mountain regions; bound that working storage and preserve
  deterministic numeric results when optimizing.
- Extend observation beyond endpoint sign changes: multiple or tangent roots,
  actual crest positions, other recipes, authored features and blended extrema.
  Explicit source-scale/process-grid limits remain necessary.
- Continue whole-route conditioning and turn smoothing while preserving authored
  divides, anchors, retention and cut-budget policy. Resolve the archipelago's
  non-land samples separately.

Seven interior probes can miss between-probe maxima. Even an observed barrier
may require temporary filling, while a final-ground cut remains budget limited.
These results do not certify continuous clearance, complete downhill rivers or
physical drainage. Zoom-driven regional enrichment remains separate planned
generation work, as described in [ADR-0048](../adr/0048-keep-zoom-driven-detail-generation.md).
