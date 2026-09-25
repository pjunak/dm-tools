# Geographic exposure implementation — 2026-09-25

## Delivered scope

WC1 now adds spherical cell-centre shore distance, eight directional geographic
water fractions and corresponding mixed-coastal-cell support. The World viewer
adds three layers, compass selection, source outlines, numeric hover and focused
legends. Changing direction is a view operation; editing inputs still invalidates
context. Completed v3 bundles reopen with all arrays, support and producer identity.
The [guide](../world-context.md) and [ADR-0075](../adr/0075-measure-spherical-geographic-exposure.md)
define the numeric and UI contract. The current schema replaces v2; no migration
or legacy loader is retained. Source projects keep their existing format.

Distance uses an exact SciPy KDTree query on unit-sphere samples of the prepared
shoreline. Stored distance overestimates the true retained shoreline distance by
at most the reported half-gap bound, apart from roundoff. Artificial polar/frame
edges are removed; genuine seam mismatches remain. Inland water shores count.
A world with no shore has NaN distances and explicit zero sample support.

Exposure is a normalized exp(-3*d/range) weighted water fraction along eight
initial compass bearings. Rays follow great circles, wrap longitude and can
cross a pole. Their range is min(3,000 km, pi*R/2); land does not stop them.
32–256 midpoint samples target one quarter of north-south grid spacing before
capping. These are geographic scores, not atmospheric moisture, solved winds,
continuous open-water fetch or rainfall. Mixed support is the quadrature weight
landing in unresolved coastal cells; it is not an error estimate. Completely
missed small features can yield zero support, and finer rays cannot reconstruct
coarse geography. Fixed range/weights are declared algorithm assumptions.

## Existing solution and dependency decision

[SciPy KDTree](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.html)
and its [query contract](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.query.html)
provide exact nearest samples without a bespoke index or all-pairs work. The
monotonic chord/arc relation on the sphere preserves nearest-sample ordering.
The code converts the chosen unit vectors to stable atan2 arc distances.

Installed SciPy 1.18.1 from its CPython 3.14 Windows x64 wheel, using NumPy 2.5.2.
The installed BSD-3-Clause license and bundled notices were inspected. Include
SciPy in runtime identity and current runtime schemas. Packaging must retain
native notices. This adopts neither Landlab nor its GPL reference dependency;
that larger environment remains isolated. See the [dependency register](../DEPENDENCIES.md).

## Evidence

Public synthetic controls cover analytic hemisphere/equator and meridian shore
distances, inland holes, empty/all-land nodata, source scaling/offset and sphere
rotation, radius units, finite bounded fractions, constant surfaces, and immutable
arrays. Equal-latitude island and continental-interior cases distinguish geographic
exposure. Mirroring reverses E/W bearings; seam shifts preserve scores; northward
rays cross into the opposite longitude at the pole. A known meridian-crossing
integral checks midpoint refinement against an independent analytic value.
Work admission rejects sample counts before Int64 conversion or summation,
including enormous but finite custom planets. Admission and cancellation are checked, as are all-bearing exact roundtrips,
invalid exposure payload rejection, obsolete-format rejection and view-only
bearing changes. A shore-free result also exports, reopens and renders grey nodata.

Campaign-scale measurements used an existing private source without adding its
geometry or names to this repository. They are local timings, not public quality
fixtures or portable performance promises. Numeric generation excluded import,
export and UI; retained bytes are array storage, not process peak memory.

| Grid | Numeric stage | Retained numeric arrays | Shore samples | Maximum shore overestimate |
|---|---:|---:|---:|---:|
| 180 x 90 | 2.59 s | 1,636,920 bytes | 50,077 | 12.4783 km |
| 360 x 180 | 7.23 s | 6,546,240 bytes | 50,077 | 12.4783 km |
| 720 x 360 | 39.21 s | 26,182,080 bytes | 60,089 | 6.5443 km |

These runs share a 6,000 km sphere. Each query batch is bounded; maximum exposure
work is 8 x 256 x 259,200 sample visits. The largest grid costs more than four
times the default because ray step count also increases. The 180-row setting
remains the default. No timing assertion is added to tests.

Visible inspection at 1440 x 1000 and the default 1440 x 900 covered context
reopening, all three new
layers, westward exposure, zoomed support, source outlines, legends and numeric
hover. Read-only view changes retained the source state and kept the Save path
separate from the result snapshot. All 11 native/source files in the campaign
hash audit remained unchanged. Screenshots, timings and source checks are private
agent-run evidence, not public test fixtures. At the minimum 1160 x 760 window,
controls and the layer legend remain usable, but the long context summary is
clipped; scrolling/responsive summaries are logged as a UI follow-up.

The documentation inventory contains 178 prose/legal files; all are represented
once, and 1,227 repository relative file links were checked (1,241 including the
campaign Maps README). All seven current JSON schemas validate against their
metaschema and have distinct IDs. Final gates:

- `python -m pytest -q`: **1,504 passed, 1 skipped**, 383.46 seconds. The skip is
  the opt-in isolated scientific-reference environment, not a geographic test.
- `ruff check .`: passed.
- Strict `pyright`: zero errors or warnings.
- `pip check` and `git diff --check`: passed.

The final campaign bundle verifies against the current producer. All nine numeric
arrays match exactly across the final count-admission guard change, confirming
that the guard did not alter admitted map results. Source geometry stayed unchanged.

## Remaining work

The [revised plan](../strategy/world-context.md) moves next to authored province
and continent-default hypotheses, explicit overlap/units and a common present.
Bathymetric hypotheses and water-piece/face incidence precede transport; the
existing face widths cannot establish that capacity. Physical path/ground and
B/C/LE acceptance still precede rough world terrain and regional history replay.
This batch improves geographic inputs and inspection, not the current terrain
DEM, drainage quality or automatic zoom enrichment.
