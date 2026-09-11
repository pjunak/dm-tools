# Basin catchment review: implementation and next steps

Date: 2026-09-11. Accepted decision:
[ADR-0037](../adr/0037-expose-basin-catchment-outcomes.md).
Current usage and numeric contract: [authored water](../terrain-water.md).

## Result

The **Basin catchments** workbench toggle shows collected water in cyan,
collected dry ground in green, and retained footprint nodes in amber. Teal
lines trace connected lake outlets. **Basin details** gives collected/retained
sample counts and contributing areas, explains partial collection, and compares
exact outlet ground with authored water level. The finished-ground drainage
panel includes the same fills.

Build v10 exports UInt8 `catchment_class` and Float64 `retained_km2` alongside
source, throughput and terminal amounts. At each footprint terminal, source
plus retained area equals its original MFD capture. Classes show footprint
outcomes, not the full upstream watershed. Closed lakes, blocked outlets and
dry basins retain all their nodes. No repair is inferred from their colours.

The signed outlet-ground-minus-water difference reports both high and submerged
outlets. Above-water outlets remain blocked. Below-water ground is informational:
it does not by itself prove or disprove the imposed level's physical stability.
Authored levels, ground generation and source routing are unchanged.

## Research decision

The USACE [HEC-RAS hydraulic reference](https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/6.6/modeling-bridges/hydraulic-computations-through-the-bridge/high-flow-computations)
relates weir discharge to head above the crest, effective opening length and a
coefficient, with downstream submergence affecting flow. Its bridge example is
not a lake solver, but it illustrates why water above an outlet bed cannot be
classified as erroneous solely from that elevation difference. Our inference:
report the measured difference and leave stability unresolved until controlling
geometry and inflow/boundary conditions are explicit. Do not add an arbitrary
maximum permitted depth or silently lower the lake level.

[Fill-Spill-Merge](https://esurf.copernicus.org/articles/9/105/2021/esurf-9-105-2021.html)
redistributes runoff through a depression hierarchy and uses storage/overflow
relationships. Our captured-area transfer does not simulate those volumes.
This remains a useful reference for later lake-chain and storage work; no
additional dependency is needed for the current diagnostic improvement.

[Barnes, Lehman and Mulla's flat-routing paper](https://arxiv.org/abs/1511.04433)
combines a gradient away from higher terrain with one toward lower terrain,
resolving flats only when they have outlets. It describes a linear-time method
without perturbing elevations to represent tiny gradients. This is the leading
next prototype: assign temporary integer routing ranks within each flat, prove
that each assigned path reaches an eligible exit, and keep closed pits retained.
Our adaptation must also honor vector-contained basin links and lake-surface
receiver heights. Test multiple exits, diagonal contacts, narrow polygon gaps,
input order, unchanged ground, area conservation and controlled runtime before
adoption. The paper's performance figures are not predictions for this Python
implementation, and its supplemental code has not been incorporated.

## Validation and measurements

The public connected-outlet example has a canonical 257 by 152 grid:

| Footprint | Collected water samples | Collected dry samples | Retained samples |
|---|---:|---:|---:|
| A1: dry basin | 0 | 0 | 1,672 |
| A2: connected lake | 276 | 2,324 | 1,840 |

The lake delivers 649,077.696806 km2 of captured contributing area and retains
1,417,084.121850 km2; the closed dry basin retains 1,207,356.489491 km2. The
complete land-area balance error is -9.3e-10 km2. These are the existing equal-node
area convention, not surveyed areas or water volumes. Sample counts and area
fractions differ because footprint terminals also receive outside contributions.

The lake outlet ground is 221.705353 m against its imposed 750 m water level:
`outlet_ground_minus_water_m = -528.294647`. This large difference is now visible;
the synthetic straight valley tests a connection, not a stable natural lake.

- **320 tests passed**, covering per-node area/class partition, wet/dry/retained
  counts, closed and blocked outlets, pit/flat retention, deep/shallow beds with
  lake-surface routing, signed height differences at exact tolerance boundaries,
  resolution/order independence, endpoint rendering and deterministic exports.
- Ruff, strict Pyright and all 152 local links in the 10 changed Markdown files passed.
- Hidden Tk checks passed for connected, closed and blocked basin details, all
  12 combinations of review toggles, and full control widths at both 1280 px
  and the supported 1040 px minimum. Review controls have their own toolbar row
  to prevent clipping of the style selector.
- The public headless build completed. Its DEM, GeoTIFF, masks, axes, routing and
  water archives are byte-identical to the preceding connected-outlet build.
- The generated drainage image was visually inspected. Repeated export and
  manifest/schema checks are included in the automated suite.

CPython 3.14.7 on Windows, 768 px, seed 42, two fresh processes per scene:

| Scene | Generation seconds | Highest generation process peak (MiB) |
|---|---:|---:|
| Authored | 2.264 / 2.320 | 124.2 |
| Archipelago | 2.621 / 2.711 | 105.0 |
| Regional | 1.734 / 1.600 | 131.1 |
| Water | 1.563 / 1.530 | 136.1 |
| Outlet | 1.620 / 1.645 | 135.8 |

All 24 recorded numeric hashes repeat exactly in each scene. All 22 previous
numeric hashes per scene match the preceding implementation; the two new hashes
cover classification and retained area. The extra retained products use nine
bytes per canonical node, about 0.34 MiB for the public example, independently
of delivered DEM resolution. This excludes temporary arrays and renderer buffers.

Evidence: `artifacts/basin-catchment-performance-20260911.json`,
`artifacts/basin-catchment-final-20260911/`, and
`artifacts/basin-catchment-ui-smoke-20260911.json`. Benchmarks ran without competing
tests or terrain generation. These observations do not establish a speedup:
there was no interleaved cross-revision timing experiment. File export, drainage
review rendering, many-outlet stress and 4096 px generation were not benchmarked.


## Next gains

1. Define internal flat routing with known exits, preserving closed pits and
   vector-contained links. Measure how much retained area each proposal changes.
2. Refine water contact and shoreline apertures between canonical samples;
   derive controlling-sill evidence with explicit inflow/storage assumptions.
3. Connect explicitly authored lake chains with compatible levels and acyclic
   dependencies. Intervening basins still block current outlet routes.
4. Compare full constrained breach/reroute proposals, preserving regional cut
   budgets and authored anchors. Channel geometry and width feedback follow
   validated paths.

All work remains in Python. These improvements and their unresolved boundaries
are logged in [TODO](../../TODO.md); no legacy schema support is retained.
