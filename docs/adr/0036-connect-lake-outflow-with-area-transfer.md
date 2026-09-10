# ADR-0036: Connect lake outflow with conservative area transfer

- Status: Accepted
- Date: 2026-09-11
- Supersedes: ADR-0035's pending-only declared lake connections

## Context

The existing planning graph correctly absorbs basin flow and reviews candidate
outlets. A usable downstream path still needs shoreline containment, a real
connection to lake water, and accounting that does not invent drainage of dry
pockets or count shared downstream area more than once.

## Decision

Keep the automatic-incision MFD capture graph and all ground authority intact.
After generation, review the current finished Float32 ground and connect an
explicit lake outlet only when its candidate is sampled-clear, its water is
connected, and no low shoreline opening lies outside its bounded outlet aperture.

Require vector-contained D8 links between wet nodes. Collect additional dry
nodes only if their steepest descending D8 path reaches the water without
leaving the footprint. Use the lake surface as the wet receiver height. Dry
pits and unresolved flats remain retained. Exposed authored anchors may form
islands; their presence alone does not invalidate the connection.

Transfer the collected nodes' captured MFD area along the reviewed exterior
D8 path. Do not add rainfall or another local-cell contribution. Shared path
segments add each source once. Routes reject every intervening basin, preventing
self-return and inter-basin cycles while lake-chain semantics remain undefined.
No outlet transfer changes channel incision, width or authoritative ground.

The terminal accounting is source area = retained basin area + original direct
boundary area + delivered outlet area. Per-basin captured area equals retained
plus exported area. Fail the build on an imbalance. Store source, additional
throughput and terminal delivery separately to avoid presenting their mixture
as a new all-purpose MFD/D8 receiver graph.

Build v9 adds `basin-flow.npz` and corresponding diagnostics/hash; remove v8.
Current project v5 is unchanged. Generator identity becomes
`coastline-constraint-terrain@8`, water review becomes
`authored-basin-water-review@3`, and outlet transfer is
`captured-mfd-reviewed-d8-outlets@1`. Automatic-valley identity is unchanged.

## Consequences and limits

The explicit outlet authorizes a derived connection on generation; connection
state is not persisted as authored input. Each regeneration checks current
terrain. This provides a useful numeric and visible result without making a
post-generation terrain change invalidate its own outlet assessment.

The aperture is one canonical grid diagonal around the exact outlet, requiring
both endpoints of an exempt low edge to fall within it. Raster-edge leakage
is never exempt. Finer shoreline and terrain checks remain necessary for
physical hydrology. This is contributing-area transfer, not runoff, storage,
transient overflow or a nested depression model. Lake chains and automatic
breaches remain separate future work.

## Validation

Analytical and real-project tests cover area balance, connected and closed
outlets, isolated dry pockets, shoreline conflicts, disconnected water,
uphill/re-entry rejection, shared downstream trunks, order independence,
resolution independence, changed-ground revalidation and unchanged ground
when closing an outlet. Repeated builds verify numeric products and hashes.
