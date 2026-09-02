# Terrain tool

The terrain tool generates reproducible elevation data from an authored
geographic skeleton. It is designed for continent-scale work that can later be
refined into consistent regional and local maps.

## Run the first workbench

```powershell
.\.venv\Scripts\dmtools.exe terrain gui
```

The current workbench imports one SVG coastline, exposes every implemented
generator setting as a slider and numeric stepper, performs import validation
and generation on background workers with progress reporting, previews the
result, and exports a transparent colour-relief PNG.

[`examples/terrain/coastline.svg`](../../../examples/terrain/coastline.svg) is a
small public input for trying the workflow.

## Current input contract

- The file must be SVG.
- It must contain exactly one drawable vector object.
- That object must contain exactly one continuous, closed subpath.
- The loop must enclose positive area and must not self-intersect.
- SVG transforms are applied before the coastline is sampled.
- Holes, islands, multiple land objects, and interior elevation constraints are
  intentionally deferred.

The imported object's **longest bounding-box dimension** is the object scale in
kilometres. The shorter dimension keeps the SVG aspect ratio. This convention is
explicit so that the same coastline and scale always establish the same metric
coordinate system.

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

The current surface combines multi-scale value noise with distance from the
coast. It is useful as deterministic synthetic relief and as an architectural
test of scale and refinement behavior. It does **not** yet model plate
tectonics, rock type, erosion, drainage, sediment, climate, or user-authored
spot heights. River networks and geomorphically believable mountain systems
will require later conditioned stages.

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
2. Add exact elevation points and structural ridge/valley constraints.
3. Persist the Float32 DEM as GeoTIFF with explicit coordinate metadata.
4. Add regional refinement requests in the same world-coordinate frame.
5. Derive contours and validate hydrology.

Process-informed erosion should follow only after the hard constraints,
reproducibility, and multiresolution contracts are validated.
