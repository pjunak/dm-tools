# Terrain tool

The terrain tool generates reproducible elevation data from an authored
geographic skeleton. It is designed for continent-scale work that can later be
refined into consistent regional and local maps.

## Run the first workbench

```powershell
.\.venv\Scripts\dmtools.exe terrain gui
```

The current workbench imports one SVG coastline, exposes every implemented
generator setting as a slider and numeric stepper, and lets the user draw exact
height points plus ridge and valley centrelines over the map. Import validation
and generation run on background workers with progress reporting. The result is
previewed and can be exported as a transparent colour-relief PNG.

[`examples/terrain/coastline.svg`](../../../examples/terrain/coastline.svg) is a
small public input for trying the workflow.

## Current input contract

- The file must be SVG.
- It must contain exactly one drawable vector object.
- That object must contain exactly one continuous, closed subpath.
- The loop must enclose positive area and must not self-intersect.
- SVG transforms are applied before the coastline is sampled.
- Holes, islands, and multiple land objects are intentionally deferred.

The imported object's **longest bounding-box dimension** is the object scale in
kilometres. The shorter dimension keeps the SVG aspect ratio. This convention is
explicit so that the same coastline and scale always establish the same metric
coordinate system.

## Authoring topography

After importing a coastline, select a drawing tool above the map:

- **Height point** records an exact target elevation at one location.
- **Ridge line** records a minimum crest elevation and raises lower terrain.
- **Valley line** records a maximum floor elevation and cuts higher terrain.

Set **Height** and **Core width** before placing the point or finishing a line.
The core width is the half-width of the strongest response, not a hard cut-off;
a lower-amplitude geological shoulder continues beyond it. Ridge and valley
lines collect vertices until **Finish line** is pressed or the map is
right-clicked. **Undo** first removes unfinished vertices, then committed
features. Importing another coastline asks before clearing authored features.

Polyline corners are gently rounded during generation, and their effective
width varies with the deterministic terrain field instead of producing a
perfect extrusion. Free ends taper. A height point close enough to a ridge or
valley also becomes an elevation anchor along that structure, so peaks, passes,
and floor heights bend its longitudinal profile rather than forming an
independent circular stamp.

Constraints use normalized coastline-bounds coordinates while being authored
and are converted to explicit metric coordinates during generation. They are
kept separate from the imported coastline and are recorded in exported PNG
metadata. The serialized terrain-project contract remains a future decision.

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
and user-authored elevation structures. When constraints are present, a broad
low-frequency surface is conditioned first. Fine deterministic relief is then
restored as a residual that fades near the authored geometry. A smooth outer
shoulder prevents structures from appearing as hard-edged stamps, while a
coast-distance gate keeps the coastline fixed at sea level. Seeded width and
crest/floor variation avoids perfectly uniform tubes while respecting ridges as
minimum heights, valleys as maximum heights, and spot heights as exact anchors.

This is a constraint-aware interpolation model, not yet a landscape-evolution
model. It does **not** model plate tectonics, rock type, erosion, drainage,
sediment, or climate. River networks and geomorphically believable mountain
systems still require the planned process-informed stages.

The generated elevation array is Float32 metres in memory. The PNG is a derived
visual product with transparent ocean, elevation tint, subtle hillshade, source
name, and settings metadata. It is not an authoritative DEM file; GeoTIFF and a
versioned build manifest remain future work.

## Inputs

The intended input project contains:

- a coastline or land mask with sea level;
- spot heights and optional height ranges;
- ridge, divide, valley, river, fault, and escarpment guides;
- terrain-character regions;
- a versioned terrain profile;
- a master seed; and
- an explicit planetary model, projection, extent, and working resolution.

The exact serialized schema has not yet been accepted.

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
| `domain/` | Units, coordinates, constraints, profiles, grids, manifests, and ports |
| `pipeline/` | Deterministic stage orchestration and refinement rules |
| `adapters/` | File formats, GIS libraries, renderers, and optional engines |

These are boundaries, not promises of immediate complexity. Add modules within
them only when an implemented behavior needs them.

## Next vertical slices

The next end-to-end work should deliberately remain staged:

1. Define a versioned project and build-manifest schema.
2. Define elevation profiles and asymmetric side slopes along ridge and valley
   structures.
3. Persist the Float32 DEM as GeoTIFF with explicit coordinate metadata.
4. Add regional refinement requests in the same world-coordinate frame.
5. Derive contours and validate hydrology.

Process-informed erosion should follow only after the hard constraints,
reproducibility, and multiresolution contracts are validated.
