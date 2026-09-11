# Authored lakes and dry basins

Draw a **Lake** or **Dry basin** area with three or more corners, then choose
**Finish area**. Lake controls specify water level in metres. Enable **Outlet at
first vertex** before finishing a draining lake; otherwise it has closed-basin
intent. Its first corner becomes the explicit outlet marker. Undo removes the
last area using the existing authoring workflow.

Generate terrain to apply retention. Enable **Basin catchments** to locate
retained areas and the water/land feeding an outlet; teal lines show its connected
route. **Basin details** reports collected and retained sample counts, contributing
areas, outlet ground versus water level, shoreline findings and downstream routes. The public
[water example](../examples/terrain/basin-water.dmterrain.json) contains one lake
and one dry basin on the synthetic public coastline.

## What changes terrain

Every authored basin footprint excludes automatic incision and automatic detail
suppression. The canonical incision budget is zero inside it, and exact vector
membership also gates continuous sampling so bilinear interpolation cannot leak
a cut into the protected area between routing nodes. Authored height points,
brushes, ridges and valleys still apply; protection is against generated cutting.
It does not erase an authored valley crossing a dry basin.

A lake stores water separately from ground elevation. Its drawn polygon is the
maximum permitted water extent, not an instruction to flatten or excavate the
entire polygon. Land below the water level minus 0.01 m is wet; higher ground
remains exposed. A lake can therefore contain islands or multiple pools.
Changing only water level or outlet leaves its ground DEM unchanged. Changing
a footprint changes its automatic-cut protection and may change nearby terrain.

Cartographic relief displays wet samples in blue. Scientific elevation continues
to show ground height, including the lake bed. The generated Float32 DEM and
GeoTIFF remain ground elevations; a water surface never replaces an exact height
anchor or bathymetry sample.

## Authored and derived data

Current project v5 adds `lake` and `dry_basin` records to `constraints`. Both store
closed normalized `points`, `water_level_m` and `outlet`. A lake requires a finite
non-negative level no higher than the generation ceiling; its outlet is a
normalized boundary point or null. A dry basin requires null for both fields.
`authoring.tools.lake` remembers level and the first-vertex outlet checkbox.

Footprints must be valid, simple polygons entirely on land, excluding SVG holes.
They cannot overlap or touch, avoiding ambiguous ownership of protected samples.
Outlets must lie on the footprint boundary within 1e-9 times the longest metric
extent. Geometry checks run before generation; malformed footprints are not
silently repaired. Only the current project/build formats are supported.

The generation result retains water products and a review on the shared
257-longest-side canonical grid. Intent IDs are one-based, deterministically
sorted by kind, level, outlet and points. They identify this result and can change
when inputs change; they are distinct from derived depression candidate IDs.

Build v13 includes `water.npz`, sharing the delivered DEM's grid and axes:

| Field | Meaning |
|---|---|
| `surface_m` | Float32 lake level at wet samples; NaN everywhere else |
| `depth_m` | Float32 water surface minus ground at wet samples; zero elsewhere |
| `intent_ids` | UInt32 authored footprint ID, including dry portions; zero outside footprints |

`routing.npz` includes `basin_intent_ids` and `retention_terminal_mask` on its
canonical grid. All marked terminals have receiver -1.
`diagnostics.json` adds `authored_water` and `water_sha256`; existing DEM/routing
hashes and the completion manifest bind all products together. The water review
contains each ID's authored record, counts/flags, retained contributing area and
outlet-route evidence, connection state, captured/retained/exported contributing
area and uncontrolled shoreline counts. `collected_wet_cell_count`,
`collected_dry_cell_count` and `retained_cell_count` partition each footprint's
canonical samples. These counts are not contributing areas: a single sample can
capture a large area from outside the footprint. No pickle loading is needed.

## Planned retention and contributing area

Every canonical node in an authored footprint is an absorbing terminal in the
planning graph. Priority-Flood uses these nodes as additional seeds without
raising them. D8 assigns no outgoing edge, and MFD distributes none of their
area onward. Incoming planned channels end at their first footprint node.
Each interior node retains its own local contribution; this does not invent
an internal lake channel, a shared basin floor or overflow between pools.

`captured_contributing_area_km2` sums the MFD area at that intent's terminals.
`retained_contributing_area_km2` is the portion left after any outlet transfer.
Across all terminal land nodes, the sum equals land-node count times canonical
x/y spacing, within floating-point tolerance. This is the existing equal-node
contributing-area convention, not exact vector polygon area or water volume.
The review reports `unexpected_planned_basin_exit` if a channel violates the
terminal contract. No footprint node may receive automatic cutting or detail
suppression. Geometry smaller than the grid can resolve still needs refinement.

This automatic-incision graph continues to absorb lake area during terrain
generation. The finished-ground outflow layer connects eligible declared
outlets afterward. Changing a lake level or outlet leaves ground and the
automatic-incision graph unchanged; its derived water connection can change.
The separate `canonical_drainage` analysis still fills a diagnostic copy toward
land boundaries to inventory natural depressions. Its conditioned receivers
are candidate topology; they do not override authored retention.

## Candidate outlet review

The exact authored outlet is evaluated on the finished field, rounded to
Float32. `outlet_ground_minus_water_m` records ground elevation minus the authored
water level: positive is above water, negative is below, null means no evaluated
outlet. A difference within 0.01 m is treated as equal for review findings.
`outlet_above_water` blocks connection; `outlet_below_water` is an informational
finding and does not block it. Submerged ground does not establish a controlling
sill or a stable water level. The tool never moves the outlet or changes the
water level to erase this difference.

Within one grid diagonal, the nearest outward land node supplies a
candidate attachment; row-major order breaks distance ties. The attachment
must stay on vector land, leave its own footprint, and avoid other footprints.
Selection happens before downstream success is known, so an obstruction is not
hidden by choosing a farther node. A wet sample within the same distance and
connected by a segment inside the footprint is required for sampled water contact.

The water-contact node, exact outlet and selected outside attachment form a
short connection profile. Re-evaluate the finished ground between those points,
rounding each value to Float32. Spacing is at most one quarter of the shorter
canonical axis step; every nonzero segment also includes an interior sample.
Authored narrow cores receive additional feature-guided stations as described below.
A sampled height above water plus 0.01 m blocks the connection. A submerged
crest can remain passable. The largest sampled ground height and its position
are evidence for this selected connection, not a surveyed controlling sill.

The review follows the finished field's conditioned D8 receivers to a terminal
or the first invalid step. It inspects **unfilled** ground heights along the
entire visited route, including the attachment from the lake's water level.
It records canonical flat indices, reviewed length in kilometres, uphill step
count, maximum rise, maximum height above lake level, terminal index and boundary
flags. The maximum height above water includes the finer connection profile;
uphill counts/rises still describe the coarse downstream steps. Downstream
statistics cover the inspected prefix if geometry or a graph error blocks
further tracing; they are not a complete breach estimate.

Every segment is checked against vector land and every authored footprint, so
a gap or protected area between raster nodes cannot be silently jumped. Re-entry,
cycles, invalid receivers, inland terminals, uphill steps above 0.01 m and an
outlet above water are reported. Enclosed SVG-hole terminals and raster-edge
terminals without exterior-water adjacency need an explicit boundary level.

`outlet_route.status` is `sampled_clear`, `blocked` or `unresolved` (no eligible
attachment). `sampled_clear` means this candidate has no detected obstruction
at the sampled spacing. The short water/outlet attachment receives the finer
check above; subsequent downstream edges still use canonical ground heights.
Ocean levels and finer river gradients remain unresolved. Connection additionally
requires the water and shoreline checks below. Every regeneration reassesses
the route on the current finished field; no stale connected state is persisted.

## Connecting an eligible outlet

An outlet is `closed` when absent, `blocked` when its route or lake checks fail,
and `connected` when its sampled path and water connection are usable. The
explicit outlet is the authorization to derive this connection; the process
adds no new authored geography and changes no ground height.

A connected lake must have one wet component reaching the selected contact
node, with vector-contained D8 links between water samples. All low shoreline
edges outside the declared outlet opening block connection. The opening is
bounded to one canonical grid diagonal from the exact outlet: both endpoints
of an exempt low edge must be within that distance. Raster-edge leakage is
never exempt. This aperture remains a declared sampling allowance, not an
estimated channel width.

The exact polygon boundary also receives finer ground samples at the spacing
above. Every drawn corner is included, with canonical ring orientation/start.
Any boundary sample below water minus 0.01 m outside the allowed opening blocks
connection, even when no coarse wet node reveals it. Closed lakes receive the
same review with no permitted opening; dry basins have no water-boundary review.
A low boundary sample is potential uncontained water, not proof that a particular
interior pool reaches it. The conservative gate does not merge isolated pools.

Each profile permits at most 65,536 requested samples, evaluated in batches of
at most 4,096. If the requested count exceeds that budget, it returns unresolved
with empty evidence and blocks connection. It never silently loosens spacing.
These are deterministic checks, independent of delivered DEM resolution; they
cannot rule out unsampled terrain between probes. The baseline alone cannot
resolve narrow authored cores; the local refinement below targets those cores.

Dry footprint nodes transfer captured area only when their internal D8 path
reaches connected lake water. Each link must stay entirely inside the authored
polygon, including between samples. The steepest eligible downhill neighbour
wins; slopes use metric axis spacing and fixed D8 order for ties. Wet receivers
use lake surface height, not submerged bed depth.

Exact equal-height areas with exits gain separate integer routing ranks toward
lower ground and away from higher ground. A flat edge always decreases rank;
a strict downhill edge always decreases head. Elevations are never nudged or
filled. All downhill exits participate, including paths ending in lower closed
pits. No exit is invented at the polygon or grid boundary, and nearly equal
Float32 heights are not rounded together. Closed flats and dry pits retain
their contributions. An exposed height anchor can remain an island.

This bounded adaptation of the Barnes/Lehman/Mulla method is recorded in
[ADR-0038](adr/0038-route-basin-flats-with-integer-gradients.md). Internal flat
routing runs only after the declared outlet and connected water pass review;
it cannot make a blocked outlet usable.

The connected wet and dry nodes supply captured MFD area to the reviewed
outlet path. Every path node receives that amount as additional throughput;
its final boundary receives it once. Routes avoid all authored basins, so
self-return and inter-basin cycles cannot be activated. Connections between
lakes remain unsupported. Shared downstream segments add the contributions of
independent outlets without adding local source area a second time.

This is a derived transfer layer over the existing MFD capture model. It does
not resize or cut the downstream channel, recompute all terrain runoff, or
certify the other planned rivers. **Drainage review** shows connected outlet
paths in teal; ordinary relief and the DEM remain ground/water-surface products.

## Finer water evidence

Build v13 stores the additional evidence in `diagnostics.json`, under
`authored_water`; numeric archives retain their existing layouts.
`sampling_algorithm_id` identifies `feature-guided-float32-water-checks@2`.

Each lake's `shoreline` contains a `profile`, `opening_radius_km`,
`low_sample_count`, `uncontrolled_low_sample_count` and
`uncontrolled_low_sample_indices`. The last field indexes the profile directly;
counts include its repeated closing endpoint. A dry basin has null shoreline.
`outlet_route.connection_profile` is null without both a selected water contact
and an outside attachment.

Both profiles use the same fields:

| Field | Meaning |
|---|---|
| `status` | `sampled` or `budget_exceeded` |
| `spacing_limit_km` | Maximum requested spacing in local kilometres |
| `requested_sample_count` | Exact count when sampled; required lower bound when over budget |
| `feature_sample_count` | Added stations beyond the baseline, or null when unresolved |
| `feature_spacing_limit_km` | Smallest local core-spacing limit used in the plan, or null |
| `positions_km` | Ordered local metric coordinate pairs, including exact vertices |
| `ground_m` | Matching Float32 ground values represented as JSON numbers |
| `minimum_ground_m`, `maximum_ground_m` | Sample extrema, null when unresolved |
| `maximum_position_km` | First position attaining the sampled maximum, or null |

Unresolved profiles contain empty position/height lists. All evaluated values
must be finite; an invalid sampler result fails generation. Boundary and short
connection checks share the current final-field evaluator and preserve source
constraints, ground arrays and the original capture graph.

The baseline stations remain present. Each prepared point, brush segment or
smoothed ridge/valley segment whose narrowest core radius divided by four is
less than the baseline spacing can request refinement. Intersect a conservative
corridor extending two nominal influence radii around that geometry with the
profile; include closest approaches, projected endpoints and corridor ends.
Sample the intersecting intervals with spacing no greater than one quarter of
the narrowest core radius. Use the evaluator's 0.35 endpoint taper and 0.82
minimum width variation for structures, and its 0.45 attached absolute-point
radius factor. Attached relative points act through a structure profile; they
do not add a separate local core. Region boundaries and procedural features do
not yet provide guidance.

Split polylines into segments to keep multiple crossings, normalize feature
geometry, merge overlapping interval requirements using the finest active
spacing, and retain deterministic station order. Duplicate guidance does not
increase sample counts. The profile count is checked before allocating the
refined positions or evaluating ground. If the baseline alone exceeds the
budget, its count is a lower bound and feature planning is skipped. Otherwise
the count includes the complete merged refinement plan. Neither failure returns
partial ground evidence. The smallest local spacing is not a global uniform
resolution or an accuracy guarantee; Gaussian context tails extend outside the
chosen core corridors and interacting features can move extrema.

**Basin details** reports boundary counts and the highest sampled connection
ground, plus extra feature samples and the smallest local spacing limit. Orange
dots mark low boundary samples outside the opening; red diamonds
mark above-water connection ground. Both review toggles and the finished-terrain
review show these markers. The complete evidence remains in the diagnostic file.

## Outflow products and conservation

Build v13 includes `basin-flow.npz`, using the canonical axes in `routing.npz`:

| Array | Type | Meaning |
|---|---|---|
| `internal_receivers` | Int64 | Canonical row-major flat index of the internal receiver; -1 for terminals or no derived route |
| `flat_rank` | UInt32 | Positive integer rank at resolved flat donors; zero for other nodes |
| `catchment_class` | UInt8 | 0 outside footprints; 1 retained; 2 collected water; 3 collected dry ground |
| `retained_km2` | Float64 | Captured MFD area still held at each footprint terminal; zero elsewhere |
| `source_km2` | Float64 | Captured MFD area removed from eligible footprint terminals |
| `throughput_km2` | Float64 | Additional area carried along connected outlet paths; shared segments sum |
| `terminal_km2` | Float64 | Additional area delivered once at each downstream boundary terminal |

Every footprint node has exactly one class. Closed lakes, dry basins and blocked
outlets retain all nodes. A connected lake collects its reachable wet and dry
nodes; dry nodes without a downhill or resolved-flat path to connected water
stay retained. Internal receivers describe a separate graph, not the original
MFD capture graph or the external outlet path. Water nodes are terminals in
this internal graph. Closed/blocked basins have receivers -1 and ranks zero.
A positive flat rank does not by itself imply collection: its path can still
end in a closed pit.

Per-basin diagnostics report `flat_routed_cell_count` for all resolved dry flat
donors and `collected_flat_cell_count` for those reaching water. These count
flat steps, not every upstream node benefiting from them. **Basin details**
shows both. Diagnostics also record `flat_routing_algorithm_id`.

`source_km2 + retained_km2` equals the original captured MFD area at each footprint
terminal and is zero outside. The `retained_km2` sum matches the retained-area
summary. The classification is a footprint review, not a delineation of the
entire upstream watershed. **Basin catchments** uses cyan for collected water,
green for collected land and amber for retained nodes. Colours use nearest
canonical nodes and preserve endpoint alignment when resized. The finished-ground
panel in `drainage.png` shows the same fills; they never recolour the ground DEM.

`throughput_km2` is not total river discharge and must not be summed as a
catchment area or added to every old terminal balance. Source and terminal
sums must agree. Diagnostics include the outflow algorithm ID and accounting:

`land-node source area = retained basin area + direct MFD boundary area + outlet boundary area`

An imbalance outside the floating-point tolerance fails the build. Per-basin
captured area equals retained area plus `outlet_contributing_area_km2`. The
`basin_flow_sha256` and manifest bind the archive to the other products.

The [connected-outlet example](../examples/terrain/connected-outlet.dmterrain.json)
authors a narrow valley all the way to the public coast. Part of its captured
area drains through the lake; isolated dry pockets remain retained. The
[flat-outlet example](../examples/terrain/flat-outlet.dmterrain.json) adds a
zero-relief plateau and narrower height influences to exercise exact flat
routing alongside retained pits.

## Shoreline findings and remaining work

- `shoreline_low_ground`: finer boundary samples fall below water outside the
  permitted opening; connection is blocked despite any clear coarse route.
- `shoreline_sampling_unresolved`: the whole boundary exceeds the sample budget.
- `outlet_connection_above_water`: the short contact/outlet/attachment profile
  finds above-water ground; recorded on the candidate route.
- `outlet_connection_unresolved`: the connection profile exceeds the sample budget.
- `low_boundary`: wet land borders below-level ground beyond its drawn polygon
  by D8, or reaches the raster edge. An intended outlet can explain part of
  this evidence; other shoreline sections still need review.
- `exposed_height_anchor`: an absolute height point is at or above lake level
  within the polygon. It may be an intentional island; its height stays.
- `outlet_above_water`: the exact outlet ground is above the authored level.
- `outlet_below_water`: the exact outlet ground is below the authored level;
  informational, with the measured signed difference. Sill stability is unmodeled.
- `unresolved_footprint`, `no_water_at_level` and `disconnected_water`: the
  canonical grid resolves no area, no wet ground or multiple separate pools.
- `outlet_shoreline_uncontained`, `outlet_water_disconnected` and
  `outlet_route_blocked`: connection is blocked by extra shoreline openings,
  water links crossing outside the footprint, or downstream route findings.
- `outlet_partial_catchment`: the outlet connects, but dry ground that cannot
  reach its water surface retains part of the captured contributing area.

The water surface remains an authored, clipped level preview. No runoff,
water budget, automatic spill, breach, sediment or nested depression hierarchy
is simulated. Next, extend finer evidence beyond the targeted authored cores,
check internal water links and downstream paths, and define controlling-sill
and storage assumptions before explicit lake chains. Full constrained
breach/reroute proposals must preserve budgets and authored anchors. See
[ADR-0040](adr/0040-refine-water-profiles-around-authored-features.md).

For measured results and the prioritized next steps, read the
[implementation rundown](research/2026-09-11-feature-guided-water-sampling.md).
