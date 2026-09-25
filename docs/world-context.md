# Generate geographic world context

The World workspace now implements the first WC1 stage: fractional land coverage,
connected water regions and resolution support on a custom spherical planet.
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
4. Use the preview selector for **Source**, **Land coverage**, **Connected water**
   or **Resolution support**. Zoom and pan inspect the same cells. Hover shows
   land fraction, the dominant water ID and whether local support is mixed.
5. **Export context…** creates a new result directory. It includes the complete
   input snapshot, numeric arrays, previews and a manifest with hashes. Existing
   directories are never overwritten. A cancelled or failed export has no
   completed `context.json`; its partial files remain available for inspection.

Changing the source, assignments, frame or context resolution invalidates the
in-memory result. An obsolete worker result cannot become current. Saving the
world saves its authored source, while Export context saves the derived result
and its resolution. Reopening a world requires generating context again; the
editor does not yet reopen exported context bundles. Generation does not mark
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

## What the layers mean

| Layer | Meaning |
|---|---|
| Land coverage | Area-weighted land fraction from 0 to 1 in each spherical cell. Tiny islands and water holes remain in these fractions. |
| Connected water | Water regions derived from continuous prepared vectors, joined across the longitude seam. Cell colour uses the largest water region within that cell. |
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
flow link. The flags conservatively expose mixed geometry; they do not measure
minimum gateway width, water depth or transport capacity.

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

[Context v1](../schemas/world/context-v1.schema.json) owns the manifest. It records
`spherical-geography-v1`, importer/preparation identities, the canonical complete
input hash, software/runtime identity, frame, grid, settings, area checks, water
regions, support counts and SHA-256/byte counts for every output.

| Product | Contents |
|---|---|
| `world.dmworld.json` | Portable original SVG, assignments, frame and source identity. |
| `geography.npz` | Numeric arrays listed below; load with `allow_pickle=False`. |
| `land.png`, `water.png`, `support.png` | Cell-scale previews, regenerated from the numeric result. |
| `context.json` | Completion manifest, published last with an atomic rename. |

NPZ fields: `land_fraction` Float64 [rows, columns], `water_body` Int32
[rows, columns] (0 means no assigned water), `support_flags` UInt8 [rows, columns],
`cell_area_km2` Float64 [rows] (broadcast across columns), and Float64 centre
coordinates `latitude_deg` [rows], `longitude_deg` [columns]. Flags are bitwise:
1 mixed land/water, 2 disconnected water pieces, 4 land absent at centre,
8 water absent at centre. A cell can carry several flags.

Generated results do not alter the world source. They are not yet accepted parents
for terrain/climate solvers; a verified context reader, explicit finite gateway
support, geodesic exposure and province hypotheses are the next WC1 work. See
[the staged plan](strategy/world-context.md) and
[implementation evidence](research/2026-09-25-geographic-world-context.md).
