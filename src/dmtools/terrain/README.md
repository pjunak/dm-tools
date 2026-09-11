# Terrain tool

The terrain tool generates reproducible elevation data from an authored
geographic skeleton. It is designed for continent-scale work that can later be
refined into consistent regional and local maps.

## Run the first workbench

```powershell
.\.venv\Scripts\dmtools.exe terrain gui
```

The current workbench imports closed SVG land shapes, dissolves adjacent
mainland sections, and retains disconnected islands in the same map. It exposes
numeric generator settings as sliders and steppers, and lets
the user draw exact height points plus ridge and valley centrelines. A terrain brush
paints broad soft elevation guidance directly over the continent. Import
validation and generation run on background workers with progress reporting.
The result is previewed and can be exported as a transparent colour-relief PNG.
The same window can save and open authored `.dmterrain.json` projects.
Every build uses named stage seeds derived from the numeric master Seed.
See the [seed contract](../../../docs/terrain-seeds.md). Only the current save
format is supported; older saves must be recreated.

For saved projects, `dmtools terrain build PROJECT --output NEW_DIRECTORY`
uses the same pipeline without opening the GUI. It saves the Float32 DEM,
mask, coordinates, both PNG styles, inspectable drainage and a completion manifest.
See the [numeric build guide](../../../docs/terrain-builds.md). The coordinate
model remains the local SVG plane. Builds now include a
[local-metric GeoTIFF](../../../docs/terrain-geotiff.md); world placement is still planned.

[`examples/terrain/example.dmterrain.json`](../../../examples/terrain/example.dmterrain.json)
is a small public project for trying the complete workflow; its referenced
[`coastline.svg`](../../../examples/terrain/coastline.svg) can also be imported
directly.

Automatic drainage now plans its route over the authored broad terrain.
Relative valley floors are prepared before generated incision. Exact point
anchors retain their final authority. Use **Drainage review** to see planned
channels in blue and segments that rise on the finished terrain in red.
This is a canonical-grid review, not a guarantee of valid rivers. See
[the stage decision](../../../docs/adr/0029-route-drainage-over-authored-terrain.md).

Use **Region** to draw plains, hills, plateaus and mountain belts.
The [region guide](../../../docs/terrain-regions.md) explains controls, overlap,
transitions and the [public example](../../../examples/terrain/landform-regions.dmterrain.json).

## Current input contract

- The file must be SVG.
- If groups named `Land Shapes` exist, only drawable objects beneath those
  groups are land. Otherwise, every drawable object is treated as land.
- Every land object must contain exactly one continuous, closed subpath.
- Every loop must enclose positive area and must not self-intersect.
- SVG transforms are applied before the coastline is sampled.
- Overlapping or nearly touching land objects are dissolved. Their shared edges
  do not become coastlines or terrain-generation boundaries.
- Disconnected polygons become islands or other separate land components in one
  shared generation. Larger enclosed gaps remain water; sub-sampling slivers at
  separately drawn borders are repaired.
- SVG water gaps remain non-land; authored lake levels use separate basin constraints.

The combined land geometry's **longest bounding-box dimension** is the object
scale in kilometres. The shorter dimension keeps the SVG aspect ratio. This
convention is explicit so that the same source and scale always establish the
same metric coordinate system. Every mainland section and island is evaluated
in that one coordinate-addressed field and with the same stage seed.

## Authoring topography

After importing a coastline, select a drawing tool above the map:

- **Terrain brush** paints broad, soft elevation guidance.
- **Height point** places one local height or height offset.
- **Ridge line** establishes a crest or adds ridge relief.
- **Valley line** runs from an upstream head toward its outlet and establishes
  an outlet floor or adds relative incision.

Each tool keeps its own mode, elevation value, and radius or width while tools
are switched. Brush strength is also retained independently. The initial modes
are relative brush, absolute height point, relative ridge, and relative valley.

Every feature can use one of two elevation modes:

| Mode | Meaning |
|---|---|
| **Absolute** | Specifies a world elevation in metres above sea level. A point is exact, a ridge is a minimum crest, a valley value is its downstream outlet floor, and a brush blends toward its target. |
| **Relative** | Specifies displacement from the terrain entering that pipeline stage. Positive point or brush values raise terrain, negative values lower it, ridge values add relief, and valley values add incision depth. |

Relative mode is deliberately local relief rather than true topographic
prominence. Prominence depends on the final summit and its key saddle, while a
relative constraint is a controlled deformation of the generated surface.

With the terrain brush selected, drag over the land to paint a continuous
stroke. The ordinary mouse wheel changes its full width. **Ctrl+wheel** changes
its strength in five-percent steps. The cursor ring and adjacent readout show
both values before paint is committed. A click without dragging creates one
circular brush mark.

In absolute mode, brush strength blends toward the target height. In relative
mode it scales the signed height offset. Overlapping absolute strokes combine as
weighted targets; overlapping relative strokes add their displacements. Both
behaviours are independent of stroke list order. Structural lines are applied
after brush guidance, and exact absolute points remain the final authority.

Set the tool's elevation value and radius before placing a point or finishing a
line. The core radius is the half-width of the strongest response, not a hard
cut-off; a lower-amplitude geological shoulder continues beyond it. Ridge and
valley lines collect vertices until **Finish line** is pressed or the map is
right-clicked. **Undo** first removes unfinished vertices, then committed
features. Importing another coastline asks before clearing authored features.
Valleys must be drawn from their upstream head toward their downstream outlet;
the arrow at the final vertex makes this direction visible.

Polyline corners are gently rounded during generation, and their effective
width varies with the deterministic terrain field instead of producing a
perfect extrusion. Free ends taper. A height point close enough to a ridge or
valley also becomes an elevation anchor along that structure, so peaks, passes,
and floor heights bend its longitudinal profile rather than forming an
independent circular stamp. Absolute points attach to nearby absolute
structures. A relative point attaches only to the uniquely nearest relative
structure; if ownership is ambiguous or no compatible line is nearby, it keeps
its free-standing displacement behavior.

When several anchors lie on one compatible structure, a shape-preserving cubic
profile connects them along the line without overshooting adjacent targets.
Absolute anchors set world elevations. On a relative ridge, a point's signed
displacement is added to the line's base relief; on a relative valley, it is
subtracted from the base incision depth, so a positive point makes the floor
shallower and a negative point makes it deeper. A profile cannot reverse the
parent feature's kind. Two peaks surrounding a lower point can therefore create
a geometric saddle while the terrain still falls away across the ridge.
Conflicting targets at the same projected line position are rejected rather
than silently averaged.

Before raster generation, every valley samples the stable terrain surface
entering the valley stage at resolution-independent metric positions. Relative
depth is subtracted from that reference, then a downstream-only correction
removes any uphill floor segment without ever raising terrain. This keeps a
valley through a high plateau high while still making its route drain toward
the authored outlet. Absolute floor anchors must already be non-rising in the
authored direction and are rejected if they conflict. Relative depth remains a
preferred minimum incision: the downstream correction may deepen it where that
is necessary to avoid an uphill floor. Authored lake/dry-basin retention applies to automatic channels; this explicit
valley profile remains authoritative inside those areas.

Constraints use normalized coastline-bounds coordinates while being authored
and are converted to explicit metric coordinates during generation. They are
kept separate from the imported coastline and are recorded in exported PNG
metadata.

## Saving terrain projects

**Save project** writes the coastline reference, all generator settings, every
committed constraint, the active tool, and each tool's independent controls to
a readable JSON document ending in `.dmterrain.json`. **Open project** restores
that state. An unfinished ridge or valley must be finished or undone before
saving so no invisible draft is lost.

The SVG remains the authoritative coastline rather than being duplicated into
the project. Its path is relative to the project file whenever possible, and
the project records a SHA-256 fingerprint of the exact SVG bytes. Opening fails
clearly if the SVG is missing or changed. Saving also fails if the SVG changed
on disk after import; re-importing makes that geographic change deliberate.

Project files contain authored inputs only. Generated arrays and PNG previews
are not embedded. Saves use a temporary file followed by atomic replacement so
an interrupted write does not leave a partially written project. The current format is
strict: unknown fields or unsupported versions are rejected rather than
guessed. The public contract is
[`schemas/terrain/project-v5.schema.json`](../../../schemas/terrain/project-v5.schema.json)
and its rationale is recorded in
[ADR-0006](../../../docs/adr/0006-versioned-terrain-project.md).

## Generator settings

| Setting | Meaning | Start value |
|---|---|---:|
| Seed | Stable integer selecting the generated field | 20,260,902 |
| Object scale | Longest coastline-bounds dimension | 4,000 km |
| Output resolution | Pixels along the longest dimension | 768 px |
| Elevation ceiling | Upper bound used by the synthetic relief model | 4,500 m |
| Largest feature | Wavelength of the broadest noise band | 450 km |
| Detail levels | Number of successively halved spatial bands | 6 |
| Fine-detail strength | Amplitude retained at each finer band | 0.55 |
| Coastal rise distance | Distance over which relief rises from sea level | 180 km |
| Elevation variability | Mix between an even interior and generated relief | 0.75 |

## Determinism and resolution

The stochastic component is coordinate-addressed. A stable integer hash maps
the seed, detail band, and absolute kilometre lattice coordinate to a value.
It does not consume a mutable random-number stream and does not depend on raster
dimensions or evaluation order.

Consequently, if a finer grid includes the same world-coordinate samples as a
coarser grid, their values are bit-for-bit equal; the finer grid only adds
samples between them. The test suite verifies this with nested 65 and 129 sample
grids. Arbitrary output dimensions do not necessarily share pixel positions,
but querying the same kilometre coordinates still gives the same terrain.

This is the basis for later local refinement. It is not yet a complete
multiresolution storage scheme, nor does it make separately chosen regional
settings automatically continuous with a parent build.

## Scientific scope of the first result

The current surface combines multi-scale value noise, distance from the coast,
and user-authored elevation guidance. When constraints are present, a broad
low-frequency surface is conditioned first. Absolute constraints suppress fine
residual relief as needed to satisfy their world elevations. Relative
constraints operate as smooth displacement fields and retain the pre-existing
residual relief, so a peak on a tall ridge becomes taller and a valley through a
high plateau remains high while being incised. A smooth outer shoulder prevents
structures from appearing as hard-edged stamps, while a coast-distance gate
keeps the coastline fixed at sea level.

This is a constraint-aware, process-informed terrain model, not a full
landscape-evolution model. A fixed-resolution hydrology stage now fills
accidental sinks on a temporary routing surface, accumulates multiple-direction
flow, and uses contributing area plus slope to incise broad automatic valleys.
The generated valley hierarchy stays fixed when output resolution changes.
MFD represents broad convergence, a deterministic D8 tree locates one centre,
and drainage-area hierarchy makes major downstream trunks broader and smoother
than their headwaters. Channel heads now use a bounded area-slope criterion:
steep convergent terrain can initiate with less source area, while a fourfold
cap on the local area threshold preserves large rivers through gentle plains.
Every initiated cell is traced down the D8 tree so selected channels cannot
vanish merely because a downstream reach becomes flatter.
The generated tree now also carries Horton-Strahler order, distinguishing joins
of comparable tributaries from small tributaries entering a larger trunk. This
is retained as derived topology only. Tests showed that making order directly
widen or deepen valleys could regress downstream-width or coarse drainage
measurements, so it does not yet alter the DEM.
A high-order, 4%-strength MFD convergence correction now nudges broad generated
valleys toward the continuous flow minimum where the unique D8 tree is
directionally quantized. It leaves the connected D8 centreline, downstream
floor correction, and residual-detail suppression authoritative.
After residual detail is restored on the canonical grid, generated channel
floors receive a bounded downstream-only correction: a receiver is lowered just
enough to retain a 0.01 m drop, never raised, and never cut without limit. The
pass may use at most 60% of reconstructed local elevation and add at most 2% of
the generation ceiling. It affects generated centre cells only and runs before
authored constraints.
Consecutive generated-channel edges then receive a second bounded profile
check. Only a downstream normalized-steepness increase above eight is relaxed,
using `S * A^0.45`; the middle cell is lowered under the same incision cap.
This removes extreme numerical knickpoints without flattening ordinary profile
variation or modifying authored features.
The model still does **not** simulate plate tectonics, rock type, sediment,
climate or geological time. Authored lake/dry-basin areas now exclude automatic
cutting and absorb planned flow. Eligible downstream outlets transfer captured area after finished-ground
and shoreline checks; unresolved dry pockets remain retained. The drainage
field is exported for review but is not certified as a river network.

Every result includes a canonical broad-scale drainage check on the same
257-longest-side grid as channel review. It reports direct boundary connectivity,
potential sinks and required filling of a copied surface. Significant fill
regions have ranked IDs, extent labels, floor/depth/area/volume measurements,
and a representative escape route with a concrete spill point and terminal.
The **Drainage review** toggle shows purple extents plus yellow routes and spill
diamonds for the eight deepest candidates. Exterior and enclosed non-land have
separate diagnostic classes without changing existing routing boundaries.
These findings do not alter elevation, assign lakes or model nested depressions.
Read the [basin contract](../../../docs/terrain-basins.md) for numeric products
and the remaining explicit-water authoring work.

The generated elevation array is Float32 metres in memory. The PNG is a derived
visual product with transparent ocean, elevation tint, hillshade, source name,
settings, render style, palette, and colour-scale metadata. The preview toolbar
switches between **Cartographic relief**, the default fixed 0–10,000 m world
scale with stronger terrain shading, and **Scientific elevation**, the ordered
and colour-vision-deficiency-safe Oleron land sequence normalized to the active
generation ceiling. The cartographic scale uses green lowlands, yellow and
brown ordinary uplands, a gradual umber-to-muted-red transition from 6,000 to
8,200 m, progressively lighter red above 8,200 m, and near-white only at
10,000 m. Changing style re-renders the same DEM and does not regenerate or
alter elevation.

The **Elevation ceiling** remains a generation control, not a colour control.
Its default is 4,500 m and its UI range extends to 12,000 m for exceptional
terrain. Raising it does not stretch ordinary elevations into summit colours;
on every continent, a given metre elevation retains the same cartographic hue.

These colours express elevation only; they do not claim vegetation, exposed
rock, or snow. The PNG is not an authoritative DEM file; headless builds write
the numeric GeoTIFF and a completion manifest. The current display decisions are recorded in
[ADR-0011](../../../docs/adr/0011-separate-cartographic-and-scientific-relief-styles.md)
and [ADR-0012](../../../docs/adr/0012-fix-cartographic-colour-scale-at-ten-kilometres.md),
with supporting [cartographic-style analysis](../../../docs/research/2026-09-03-cartographic-relief-style.md)
and [scientific colour-ramp research](../../../docs/research/2026-09-03-elevation-colour-ramp.md).

## Inputs

The intended input project contains:

- a coastline or land mask with sea level;
- spot heights and optional height ranges;
- ridge, divide, valley, river, fault, and escarpment guides;
- terrain-character regions;
- a versioned terrain profile;
- a master seed; and
- an explicit planetary model, projection, extent, and working resolution.

The current project persists the implemented coastline, generator
settings, authoring defaults, brush strokes, height points, ridges, and valleys.
Add planned input kinds to the current schema as their semantics are accepted;
remove obsolete formats without maintaining old-save support.

## Outputs

A successful build is expected to produce:

- a Float32 elevation raster in metres;
- a machine-readable build manifest;
- derived contours and drainage vectors;
- hillshade and elevation-colour previews; and
- validation results describing satisfied constraints and known limitations.

## Internal modules

| Module | Responsibility |
|---|---|
| `application/` | Shared saved-project build operation and completion checks |
| `domain/` | Units, coordinates, constraints, profiles, grids, manifests, and ports |
| `pipeline/` | Deterministic stage orchestration and refinement rules |
| `adapters/` | File formats, GIS libraries, renderers, and optional engines |

These are boundaries, not promises of immediate complexity. Add modules within
them only when an implemented behavior needs them.

## Next vertical slices

Follow the [current development strategy](../../../docs/strategy/README.md)
for the implementation order and evidence gates. The
[terrain roadmap](../../../TODO.md) tracks the wider backlog, including world
placement, refinement and contour exports.

Process-informed erosion should follow only after the hard constraints,
reproducibility, and multiresolution contracts are validated.


## Authored lakes and dry basins

Use **Lake** or **Dry basin** to draw a closed area and choose **Finish area**.
Lake controls set a water level and optional first-vertex outlet. Generated cuts
are excluded inside either footprint; authored height and structure constraints
still apply. Cartographic relief displays water over its preserved ground DEM.
**Basin catchments** colours water and dry ground that feed a connected outlet,
and the footprint nodes that remain retained. **Basin details** explains sample
counts, contributing areas, shoreline findings and exact outlet ground versus
water level. Footprint nodes capture planned area; eligible declared outlets
transfer the portion that can reach the lake. Connected outlet paths appear in
teal in either review overlay. Lake levels remain imposed previews.
See the [water guide](../../../docs/terrain-water.md), public
[closed-water example](../../../examples/terrain/basin-water.dmterrain.json) and
[connected-outlet example](../../../examples/terrain/connected-outlet.dmterrain.json).
Supported formats are listed in the [schema index](../../../schemas/README.md).
