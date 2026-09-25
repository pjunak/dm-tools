# Geographic world context — 2026-09-25

This implements the first geographic part of WC1 from the
[staged plan](../strategy/world-context.md). [ADR-0073](../adr/0073-generate-spherical-geographic-context.md)
records the decision; the [user guide](../world-context.md) explains the editor,
headless generation and array contract.

## Delivered

- Bounded spherical cell grid, physical cell areas and fractional land coverage.
- Vector-derived connected water with periodic longitude and finite-opening pole
  policy, independent of semantic continent names and coarse display resolution.
- Mixed/subcell support flags that expose tiny features and disconnected water
  pieces instead of asserting that a dominant pixel ID defines a flow link.
- Context generation, progress, cancellation, source/context preview switching,
  cell readout and invalidation after input edits in the desktop World workspace.
- Reproducible current-format exports with numeric NPZ, three PNG views, the full
  world snapshot, source/runtime identity and a last-published hashed manifest.
  `world context` runs the same stage without the UI.

World-source geometry/preparation is unchanged. No scientific engine or new
runtime dependency is installed. The pixel display intentionally retains its
selected resolution when zoomed. It does not claim local enrichment or terrain.

## Verification

The focused world suite passes 129 tests. New controls cover positive spherical
cell areas and total sphere coverage, latitude centres away from singular poles,
source scaling/translation, multiple grid resolutions, same-source land-area
conservation, longitude seam connectivity and pole barriers. A tiny source strait
connects vector water without becoming a falsely resolved cell passage. Tiny
islands and water holes retain area and support evidence. Reordering features
preserves arrays/IDs; result arrays are read-only.

Private export validation exposed cancellation in the original spherical boundary
integral: extremely small positive water pockets could measure as zero, violating
the result schema. The shared area calculation now removes a constant reference
sine before summation, evaluates the small sinc correction directly and uses
compensated summation. Analytic tiny-rectangle controls and a tiny-hole integration
case cover this failure. Nonpositive/nonfinite connected-water areas fail before
publication; the corrected private export passes schema and output-hash checks.

Publication controls validate the public schema, numeric dtypes/shapes, original
snapshot and every output hash. Source/runtime changes, cancellation and existing
destinations cannot publish a new completed result. Real Tk tests generate,
preview, export, invalidate and cancel; issue highlighting returns to the source
view. Window captures on a private world check readability and the complete map.
The final repository suite passes 1,428 tests with one expected skip for the
isolated scientific reference environment (382.56 seconds). Repository-wide Ruff
and strict Pyright pass. Local documentation links and the complete inventory
are checked: 173 Markdown documents plus one legal notice, with eight supporting
machine-readable contracts listed separately.
Private campaign inputs/names/screenshots remain outside this repository.

## Bounded performance observation

Measured after SVG import on one 185-shape private world, with unchanged prepared
geometry, frame and radius, after the precision correction. The repository
regression suite was running concurrently; these are indicative local costs:

| Grid | Generation seconds | Retained numeric bytes | Mixed cells | Split-water cells |
|---|---:|---:|---:|---:|
| 180 x 90 | 2.702 | 211,320 | 1,779 | 299 |
| 360 x 180 | 5.078 | 843,840 | 4,191 | 455 |
| 720 x 360 | 10.523 | 3,372,480 | 9,544 | 578 |

All three grids identify the same 48 connected water regions. Land-area residuals
are at most 1.50e-8 km² against the prepared source. The default grid's north-south
spacing is about 104.7 km on that 6,000 km sphere. This is an overview product.
Cell counts at different resolutions are not directly comparable resolution
scores. Numeric byte totals exclude geometry, Python/native overhead, UI and
export scratch; these are timings/allocation observations, not peak-memory caps.
The end-to-end private build/export/schema-and-hash verification took 12.14
seconds. The initial pre-correction public probe took about 0.155 seconds at
180 x 90; it is not a measurement of the final compensated area implementation.

## Next work

WC1 remains partial: implement verified context consumption, explicit finite
gateway support, geodesic interior distance/directional water exposure and authored
province/default inputs. Bathymetry remains a hypothesis with independent
mixed-layer depth. WC2 rough world relief must still pass terrain-quality and
physical-resolution gates. Seasonal climate/history coupling and same-present
regional generation retain their later acceptance requirements.

A source-based topology is useful evidence, not solved circulation. Water IDs
may include inland water and tiny source holes, and do not name oceans or set
water levels. Local terrain generation remains an independent existing workflow.
