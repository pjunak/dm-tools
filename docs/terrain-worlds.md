# Import and review a world map

The **World** workspace implements WC0: retain an authored world, confirm its
geographic frame, assign continents and islands, inspect it and save a portable
source project. Context, rough world terrain and regional history generation
remain planned. The **Terrain** workspace continues to generate local terrain;
it does not yet consume a saved world or extract georeferenced continents.

## Try the public example

From the repository root after the installation in [README](../README.md):

```powershell
.\.venv\Scripts\dmtools.exe terrain gui --world examples/world/four-shores.dmworld.json
.\.venv\Scripts\dmtools.exe world inspect examples/world/four-shores.dmworld.json
```

The example has four invented continents, two touching mainlands, separately
owned islands, an inland hole, excluded map furniture and an island crossing the
longitude seam. Its 6,500 km sphere is a demonstration, not a default planet.
**Save As** creates your working copy. No original SVG is needed to reopen it.

`dmtools terrain gui` opens the World workspace. To start directly in Terrain:

```powershell
.\.venv\Scripts\dmtools.exe terrain gui --project examples/terrain/example.dmterrain.json
```

`--world` and `--project` are mutually exclusive startup choices. Both workspaces
remain available in the same window, with separate documents and dirty states.

## Import your own source

1. Export a UTF-8 SVG with explicit vector shapes and a numeric `viewBox` from
   your drawing application. Native Affinity documents and raster maps are not
   accepted. Exporting a copy leaves your drawing document untouched.
2. In **World**, choose **Import SVG**. The original SVG text, element IDs,
   transforms and group hierarchy are retained in an embedded snapshot. Import
   does not move geometry or infer planet size from display pixels.
3. Review the shape list. **Suggest from groups** proposes continent names and
   ownership; it is an explicit, undoable action. It recognises `Land Shapes`,
   `islands` and `Map Furniture`. When land layers exist, other thematic layers
   are proposed as excluded. Inspect all proposals before accepting them.
4. Select shapes in the list or click the map. Use Ctrl-click or the list's
   extended selection for several shapes. Choose or enter a **Continent name**,
   select **Mainland**, **Island** or **Exclude**, then **Assign selected shapes**.
   Every source shape needs one assignment or explicit exclusion before saving.
   Ungrouped or invalid shapes are not guessed into a continent.
5. In **World frame**, enter your planet radius and the exact projection bounds.
   The SVG `viewBox` supplies an initial suggestion, not proof of that frame.
   Remove page margins, legends and scale bars from the geographic rectangle.
6. Click **Validate world**. Resolve reported invalid shapes, unassigned objects,
   out-of-frame land or overlapping land. Touching continents are allowed;
   positive-area duplicate fills are not silently dissolved.
7. **Save As** a `.dmworld.json` file. Reopen it to review the same source and
   membership. Save rechecks the original snapshot and geometry before replacing
   an existing file atomically. Failed validation leaves the existing file intact.

For the public raw SVG, the world frame is left **10**, top **10**, width **360**,
height **180**, radius **6500 km**, central meridian **0°**. The full page is
380 by 210 source units, with furniture outside the world frame. These values
are specific to the example; use your own map's established scale and projection.
The seam island's group suggestion initially uses Mainland; select `seam-island`
and assign **Island** to match the saved example's intended role.

A continent is a semantic owner. It can have multiple land pieces and can touch
another continent. Islands keep their chosen owner, not their nearest mainland.
**Rename assigned continent** preserves its ID and all membership. Assigning a
continent's last shape elsewhere removes that now-unused owner; Undo can restore it.

## Navigation and document handling

- Mouse wheel zooms around the pointer. Middle/right drag pans. **Fit world** or
  **F** restores the overview. Zoom inspects retained source geometry; it does
  not generate higher-resolution terrain.
- The pointer readout shows longitude/latitude once frame and radius are valid;
  before that it reports source positions. Grid lines show the declared sphere.
- Colours distinguish continent owners; selected outlines are gold, unassigned
  shapes grey and excluded shapes muted. Colours are reproducible for a given
  owner set, but may change when that set changes. IDs carry identity.
- Selecting a shape shows its source group path and any import issue. **Show
  excluded shapes** affects only the preview, never assignments or validation.
- **Ctrl+O**, **Ctrl+S**, **Ctrl+Shift+S**, **Ctrl+Z**, **Ctrl+Y**, **F** and
  **Ctrl+Enter** act on the active workspace. In World, Ctrl+Enter validates.
  Native editing shortcuts still apply inside text fields.
- Ownership assignments and renames have Undo/Redo. Frame text uses normal text
  editing; it is not part of the ownership undo stack.
- Open/import/close guard unsaved changes. Both documents are checked on exit.
  Saving an incomplete world requires resolving its assignments/frame first;
  there is no partial-draft file format in this batch.
- Import, open, validation and saving use a background worker. Input controls
  lock during a job; wait for it to finish before closing. World jobs have no
  cancellation command yet. Existing Terrain generation still supports Cancel.

## Geographic and source contract

The first supported projection is a **full-world spherical Plate Carrée** frame:
left/right span 360° and top/bottom span +90° to -90°. Radius is explicit in km;
central meridian is in [-180°, 180°). Other projections and partial-world sources
are unsupported. A rectangle's aspect ratio alone cannot establish its projection.
Custom planets are not labelled with an Earth EPSG code.

Longitude is periodic. A seam-crossing shape must use locally continuous source
coordinates, such as x=350..370 for a 0..360 frame, or be split into separate
source shapes assigned to the same continent. A path jumping directly from
x=359 to x=1 means a long source-space segment; the importer cannot infer that
you intended a short seam crossing. Polar vertices are supported and latitude
limits are checked; there is no polar climate or terrain solver here.

Original SVG text is authoritative and retained byte-for-byte through UTF-8
encoding, with a SHA-256 identity. Inspection geometry is separately flattened
at `max(viewBox width, height) / 32768` source units. Curved boundaries and derived
areas therefore have sampling error. Compound even-odd and nonzero fill rules,
holes and transforms are respected. Tiny gaps and holes are not repaired away.
The existing local terrain importer has a different dissolve/repair contract.

For preview/area checks, derived geometry is wrapped and clipped at the declared
longitude frame. Source coordinates never change. Surface areas integrate the
sampled source-linear boundary on the declared sphere; they are neither flat-page
areas nor geodesic-chord polygon areas. Touching shapes stay separate owners.

The source importer accepts at most 8 MiB, 30,000 XML elements, 4,096 shapes and
500,000 retained inspection points. These are input limits, not an OS memory
ceiling. SVG `use`, embedded/external images, nested SVG, scripts and foreign
objects must be exported to explicit paths first. Clipped/masked or open shapes
are visible import issues and must be fixed in the source or explicitly excluded.
Text is retained in the original SVG but is not treated as land. DTDs and entity
declarations, duplicate element IDs and indistinguishable anonymous shapes fail
import. Give important shapes stable unique SVG IDs.

The [world project schema](../schemas/world/project-v1.schema.json) owns current
serialized fields. Its `retained-svg-v1` importer identity records how inspection
geometry is reconstructed. Saved world files are bounded to 32 MiB. Unsupported
versions, projections and unknown fields fail rather than fall back to a guessed
format. This project has no legacy-save compatibility policy.

## What follows

[WC1](strategy/world-context.md) adds geographic/ocean connectivity and exposure,
then inspectable geological hypotheses. It must preserve this source contract.
World terrain, climate, shared history, world-linked regional generation and
local river enrichment require their own stage gates. Existing local terrain
builds remain in local metric coordinates; saving a world does not georeference
their DEMs or add climate fields to them. See [coordinates](terrain-coordinates.md),
[architecture](architecture/README.md) and [ADR-0070](adr/0070-retain-world-source-and-workspaces.md).
