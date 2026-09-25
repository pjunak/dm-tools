# Water-piece connectivity and finite-precision support — 2026-09-25

This completes the bounded water-incidence stage in the
[WC1 plan](../strategy/world-context.md). The [guide](../world-context.md) owns
current format, units and limits; [ADR-0078](../adr/0078-retain-water-piece-connectivity.md)
records the decision. This batch does not change land-terrain drainage or claim
improved terrain realism. It prevents later context consumers from treating all
water in a coastal grid cell as one connected node.

## Delivered and research basis

Each positive-area water piece has an independent node, spherical area, interior
inspection site and source body identity. Neighboring pieces connect only across
shared open intervals of positive length. Multiple gaps remain separate; seam
links are periodic and pole/corner contacts never become routes. Source-authored
coasts, world scale and continent ownership remain unchanged.

The implementation reuses mature dependencies already in the project:
[Shapely STRtree](https://shapely.readthedocs.io/en/stable/strtree.html) indexes
source geometry candidates, and [SciPy sparse connected components](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csgraph.connected_components.html)
labels undirected connectivity. These primitives support the engineering choice;
they do not validate a physical transport discretization. No new dependency,
external engine or Earth dataset was added. The earlier
[world-context research](2026-09-24-world-context-enrichment.md) remains the
physical-model and alternative-engine reference.

Context v4 adds a bounded numeric graph archive, declared registration/units,
source-verified reopening and a cell-resolution inspection layer. Rehashed links
must still reproduce actual source incidence. Fragmented source bodies and their
unsupported-transport status are explicit. The Context details now scroll, with
job controls and legends kept visible in compact windows. Bathymetry's geographic
identity follows v4; previous v3-linked inputs/results must be recreated.

## Evidence and limits

Nineteen topology tests cover a closed/open sphere, a wall separating two pieces
of one ocean within a cell, two intervals between one node pair, narrow straits,
corner-only contacts, matching/disjoint seam gaps, an enclosed lake beside an
ocean, source scale/origin, radius, deterministic immutable arrays, cancellation,
geometry admission and a synthetic floating-point sliver. File tests reject
rehashed false links, altered support, oversized counts and malformed array
headers. Existing context and bathymetry tests exercise schema, CLI, cancellation,
publication, current-format reopening and immutable dependency behavior.

A private retained nine-continent map exposes a useful support limit: one source
water region has an area of approximately `2.92e-12 km²` (about 2.9 mm²). At 180
and 360 rows, floating-point clipping reduces its shared cell-face opening to a
point. The graph has 49 components for 48 source water bodies. It keeps that
region's pieces and reports body 40 in `fragmented_bodies`; it does not erase the
region or invent a positive-width connection. At 90 rows it remains one piece
and all 48 components match. Therefore successful repeatability and area checks
alone are not complete topology acceptance. No transport consumer exists yet;
future consumers must reject fragmented regions before use.

Visible owned-workbench review at 1440 × 920 and 1160 × 760 confirms the layer,
legend, controls and scrollable Context details. The separate long source summary
still clips horizontally at the compact size and remains in TODO. Preview cells
show counts/support, not individual piece polygons or straight-line flow paths.
A final 180-row context was generated, exported and reopened with the unresolved
support retained. The private authored world and original SVG hashes match the
pre-run values; no native Affinity document or campaign canon was edited. Private
results, screenshots and raw measurements remain outside Git.

Final repository gates: `python -m pytest -q` — **1,644 passed, 1 expected skip**
in **399.52 s**. The skipped test requires the isolated scientific reference
environment; no reference solver changes belong to this batch. `python -m ruff
check .` and strict `python -m pyright` pass. The documentation audit finds **186 documents**, **1,325 valid local file links**
and **10 current JSON schemas**, with no missing, duplicate or extra inventory
entries. `git diff --check` passes.

## Performance observations

The reusable [benchmark](../../benchmarks/world_connectivity.py) uses one fresh
worker per resolution and two graph constructions per worker. Timings include
vector union, source water topology and graph construction; they exclude source
preparation, exposure/shore fields, rendering, hashing and serialization. Native
process peaks include imports, source geometry and allocator retention. Other
validation ran concurrently: these are observational wall times, not idle-machine
latency guarantees or timing assertions. Runtime: Windows 11 / CPython 3.14.7,
NumPy 2.5.2, Shapely 2.1.2 / GEOS 3.13.1 and SciPy 1.18.1.

| Private grid | Graph time, two runs | Process peak | Piece/link arrays plus derived labels | Pieces / intervals | Split cells |
|---|---:|---:|---:|---:|---:|
| 180 × 90 | 4.12–4.66 s | 140.2 MiB | 1,452,217 bytes | 14,023 / 26,745 | 299 |
| 360 × 180 | 8.00–8.23 s | 156.6 MiB | 5,638,195 bytes | 53,622 / 104,503 | 455 |
| 720 × 360 | 26.08–31.03 s | 282.0 MiB | 22,213,849 bytes | 209,491 / 413,193 | 578 |

All repeated ordered-array hashes matched. Sphere area residuals were zero at the
printed Float64 precision; no cell exceeded its full area in this private cohort.
The 180/360 runs retain the support limitation above. The public Four Shores
cohort also runs at all three resolutions and records complete graph identity and
support: 0.29 s at 90 rows, 0.83–0.84 s at 180 rows and 2.60–3.69 s at 360 rows.
Its largest worker peak was 253.9 MiB, with no fragmented source bodies.

The complete private 180-row context took 32.58 s to generate, 0.64 s to export
and 16.75 s to reopen/verify in a separate observation. This includes the new
incidence work and cannot be compared with graph-only timings as if both measured
the same operation. Reopening intentionally pays for source verification. A
maximum-resolution full geography/GUI process peak has not been measured here;
graph array bytes and the isolated graph-worker peak are not that bound.

Reproduce the public graph probe:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.world_connectivity --output artifacts/world-connectivity.json
```

`--source` accepts an authored world file; outputs must be new files. The report
retains source/runtime/benchmark identities, repeated array digests, area bounds,
fragmented source IDs and process peaks. Private source geometry is never embedded
in the tracked report or fixtures.

## Next work

Return to B/C's physical river-path and finished-ground comparison, directional
bias, resolution response and coherent landform acceptance before WC2 rough
world terrain. This world foundation must not become an indefinite series of
metadata panels. Later WC1 transport requires support admission, conservative
area/depth integration, explicit sill and capacity geometry, paired flux/storage
budgets and separate heat-capacity assumptions. A local-coordinate/exact-predicate
comparison for microscopic source slivers is a bounded follow-up when a consumer
needs that precision. No inferred bridge or centre-depth-as-volume shortcut is
accepted by this implementation.
