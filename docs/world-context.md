# Generate geographic world context

The World workspace now implements the first WC1 stage: fractional land coverage,
connected water regions, finite shared-edge water openings and resolution support
on a custom spherical planet. Completed context bundles can be reopened for inspection.
It consumes the validated source and its reported preparation adjustments.
Climate, ocean depth, tectonic provinces, rough world terrain and world-linked
regional generation remain later stages. This result is geographic context,
not a generated terrain parent.

## In the editor

1. Open a current `.dmworld.json`, or import and assign a world using the
   [world-source guide](terrain-worlds.md). Confirm its established frame and radius.
2. Open **Context**. Choose **90**, **180** or **360** latitude cells. Longitude
   uses twice as many columns: 2°, 1° or 0.5° angular cells respectively.
3. Click **Generate context**. The worker validates the current inputs and shows
   row progress. **Cancel context job** stops at a checkpoint. Individual SVG/GEOS
   operations cannot be interrupted mid-call; cancellation is cooperative.
4. Use the preview selector for **Source**, **Land coverage**, **Connected water**,
   **Resolution support** or **Water openings**. Zoom and pan inspect the same
   cells. Hover shows
   land fraction, the dominant water ID and whether local support is mixed. In
   Water openings, hover reports the longest north/east/south/west openings in km.
5. **Export context…** creates a new result directory. It includes the complete
   input snapshot, numeric arrays, previews and a manifest with hashes. Existing
   directories are never overwritten. A cancelled or failed export has no
   completed `context.json`; its partial files remain available for inspection.
6. **Open context…** selects a completed `context.json`, checks its manifest,
   source, output hashes and numeric contract, then restores the inputs and
   layers. The source snapshot inside that bundle is never the editor's Save
   target: Save prompts for a separate `.dmworld.json` when starting from context.

Changing the source, assignments, frame or context resolution invalidates the
in-memory result. An obsolete worker result cannot become current. Saving the
world saves its authored source, while Export context saves the derived result
and its resolution. Reopening a source-only world still requires context generation;
Open context restores the separately exported numeric result without regenerating it.
Failed or cancelled opening retains the current workspace. Generation does not mark
an unchanged source project dirty.

## Headless generation

From the installed repository environment:

```powershell
.\.venv\Scripts\dmtools.exe world context examples/world/four-shores.dmworld.json --output artifacts/four-shores-context --latitude-cells 180
```

The CLI accepts 4–360 latitude rows for bounded controls and generation. The UI
exposes the three useful overview choices. Source/runtime changes during a build
prevent completion. Exporting an in-memory result after software changes requires
regeneration. No stochastic stage or seed is involved in this geographic analysis.

Verify an existing result from a manifest or directory:

```powershell
.\.venv\Scripts\dmtools.exe world inspect-context artifacts/four-shores-context
```

Viewing retains the recorded producer runtime and accepts a supported current
format even if this installation's code/dependencies differ. The CLI reports that
mismatch. Export still requires the exact producing runtime: regenerate to create
new results under changed software. Context v1 is superseded; regenerate it from
its source snapshot. There is no compatibility loader or migration.

## What the layers mean

| Layer | Meaning |
|---|---|
| Land coverage | Area-weighted land fraction from 0 to 1 in each spherical cell. Tiny islands and water holes remain in these fractions. |
| Connected water | Water regions derived from continuous prepared vectors, joined across the longitude seam. Cell colour uses the body with the greatest aggregated water area within that cell. |
| Water openings | Blue edges: fully open; orange: partial opening; dark: closed. Three display pixels per cell reveal the shared edges when zoomed. Hover supplies physical widths. |
| Resolution support | Orange: land absent at the cell centre. Cyan: water absent at the centre. Violet: disconnected water pieces within one cell. Amber is other mixed coverage. |

Water IDs are ranked by area, with deterministic geometric tie-breaking. They
are derived IDs for one input/algorithm, not persistent names for oceans or lakes.
A named sea may be part of a much larger connected body. Small bodies retain
measured areas even when no cell displays their ID. The source remains available
at full retained vector detail.

Connectivity follows positive-length water openings across the seam. A point
contact, including at a pole, does not connect two bodies through a land barrier.
A narrow source strait can connect water globally while remaining unresolved by
this grid. A dominant water ID must never be used as an unqualified cell-to-cell
flow link. The flags conservatively expose mixed geometry. Edge widths are measured
separately, as described below; neither product specifies transport capacity.

## Water openings

Each cell stores the longest continuous wet interval along its east and south
shared edges. Land is removed using prepared source vectors; separate gaps are
not added into one opening. At the longitude seam the interval must be open on
both sides. The last east column links to the first; the last south row is zero,
since the pole has no finite-length edge. Northern values come from the cell
above, with zero at the north pole; western values come from the previous column.

For a meridian interval, length is `R * delta_phi`. For a latitude-circle interval
at latitude phi, it is `R * cos(phi) * delta_lambda`; angles are radians, radius and
output are kilometres. These are lengths along cell faces, not great-circle chords.
The seam comparison pins both edge geometries to the exact same source x coordinate,
avoiding roundoff in `x1 - (x1 - x0)` without moving any land geometry.

A positive opening is evidence of a shared wet edge. It is **not** a strait's
minimum width, a navigable passage, depth, sill height, or discharge capacity.
Several face openings can touch different disconnected water pieces inside a
cell. The split-water flag remains authoritative: joining all those faces through
one raster node would create false routes. A component-aware transport graph
and bathymetry are still required before a physical flow solver uses these data.

## Numeric and geographic contract

The grid covers the declared full-sphere Plate Carrée frame, with cell centres
strictly between the poles. Longitude is periodic. For latitude edges phi_n and
phi_s and longitude width delta_lambda in radians, cell area is
`R² * delta_lambda * (sin(phi_n) - sin(phi_s))`. Rows run north to south; columns
follow the source frame west to east. Stored longitudes wrap into [-180°, 180°)
around the declared central meridian and need not be numerically sorted.

Coastal cell intersections use the same source-linear spherical boundary integral
as world preparation, with reference subtraction and compensated summation for
tiny pockets. Land fractions are physical area fractions, not flat-page fractions. All cell areas sum to the sphere; land coverage and connected water
must conserve prepared source area to `max(sphere area * 1e-9, 1e-8 km²)`.
Numeric roundoff within 1e-9 of a fraction bound is clipped to [0, 1]. Curved SVG
boundaries still have the retained importer's documented flattening error.

The largest supported grid contains 259,200 cells. Geometry is intersected one
row at a time and pure cells avoid per-cell coastline operations. This bounds
numeric grid allocation; it is not an OS memory cap on native geometry operations.
North-south cell width is `pi * R / latitude_rows`; east-west width varies with
latitude. This context does not reuse the local terrain endpoint-node grid.

## Export contract

[Context v2](../schemas/world/context-v2.schema.json) owns the manifest. It records
`spherical-geography-v2`, importer/preparation identities, the canonical complete
input hash, software/runtime identity, frame, grid, settings, area checks, water
regions, support counts, gateway semantics/counts and SHA-256/byte counts for every
output. `context_sha256` fingerprints the entire canonical manifest excluding
that field; `input_sha256` identifies the complete source/settings/algorithm.

| Product | Contents |
|---|---|
| `world.dmworld.json` | Portable original SVG, assignments, frame and source identity. |
| `geography.npz` | Numeric arrays listed below; load with `allow_pickle=False`. |
| `land.png`, `water.png`, `support.png`, `gateways.png` | Derived previews; gateways use three pixels per cell to show shared faces. |
| `context.json` | Completion manifest, published last with an atomic rename. |

NPZ fields: `land_fraction` Float64 [rows, columns], `water_body` Int32
[rows, columns] (0 means no assigned water), `support_flags` UInt8 [rows, columns],
`cell_area_km2` Float64 [rows] (broadcast across columns), and Float64 centre
coordinates `latitude_deg` [rows], `longitude_deg` [columns]. `east_opening_km` and
`south_opening_km` are Float64 [rows, columns]. Multibyte arrays are little-endian,
C-order numeric NPY entries, with no object/pickle payloads. Flags are bitwise:
1 mixed land/water, 2 disconnected water pieces, 4 land absent at centre,
8 water absent at centre. A cell can carry several flags.

Opening checks exact output/member names, product lengths and hashes, canonical
input/manifest identity, supported algorithm/importer/preparation, source geometry,
coordinate and area consistency, water IDs, support flags, finite numeric ranges,
edge-length bounds and preview dimensions. It rechecks files before accepting
the captured snapshot. Manifest input is capped at 4 MiB, world input at 32 MiB,
and other products at 16 MiB each. NPY shape/dtype/order and exact payload length
are checked before allocation; each compressed entry is bounded by its admitted
array size plus 10,000 header bytes. These are allocation guards, not an OS memory cap.

Verification establishes internal consistency, not authenticity or an independent
rerun of every geometric measurement. Preview layers are rebuilt from verified
arrays when displayed. Loaded arrays are read-only.

Generated results do not alter the world source. They are not yet accepted parents
for terrain/climate solvers. Geodesic exposure, component-aware transport and
province hypotheses remain WC1 work. See [the staged plan](strategy/world-context.md)
and [current implementation evidence](research/2026-09-25-context-reopening-and-gateways.md).
