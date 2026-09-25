# ADR-0074: Verify saved context and measure shared water openings

- Status: Accepted
- Date: 2026-09-25
- Extends [ADR-0073](0073-generate-spherical-geographic-context.md); supersedes its
  current export format and deferral of context consumption/edge measurement.

## Decision

Ship a verified current-format context reader for the editor and CLI. Decode the
captured hash-checked source bytes once, prepare its geographic coverage and load
its numeric products without rerunning context generation. Check exact fields,
identities, bounded sizes/shapes/dtypes, coordinates, area conservation, IDs,
flags, physical edge bounds and image dimensions. Recheck captured files before
acceptance. Share the bounded NPY decoder with the existing terrain-parent reader.
No new dependency or general storage framework is needed.

Context v2 (`spherical-geography-v2`) includes a canonical manifest fingerprint,
eight numeric arrays, four previews, gateway semantics and the immutable world
source snapshot. Remove the v1 schema and reject superseded products; regenerate
from the retained world source. Source project format remains unchanged. Serialize numeric frame values as
floats consistently so API-created integer coordinates and reopened source
files have the same canonical identity.

Viewing a supported context does not require the producing code/runtime to be
installed. Retain the producer identity; do not relabel arrays as current output.
Export requires exact runtime identity. This is read-only inspection, not authority
to feed a mismatched context into future terrain/climate computation. Such reuse
will need its own consumption contract. Hashes demonstrate internal integrity,
not provenance authenticity or a fresh geometry calculation.

Opening context follows the existing unsaved-input guard and worker/cancellation
lifecycle. Failed, cancelled or obsolete results preserve current work. Restore
source/settings for inspection, but never assign the bundle's embedded input as
the editor's Save path. Editing invalidates the derived context and Save creates
or updates a separate authored project.

## Finite-edge measurements

For each east/south shared cell face, subtract prepared land and retain the
longest continuous water interval. Separate openings are not summed. Measure
meridian intervals as `R * delta_phi`, and latitude-circle intervals as
`R * cos(phi) * delta_lambda`, in kilometres. Store both arrays at grid shape;
the last east column represents periodic longitude and the last south row is zero.
The seam uses the intersection of water intervals on both sides. Map comparison
edges to the exact same x instead of translating by the frame width: finite
precision can make `x1 - (x1 - x0) != x0`, closing an otherwise open seam. This
also corrects vector water-component joining at fractional source origins.

A width measures shared-face support. It does not measure a strait's minimum
width/depth or its transport capacity. Disconnected water pieces inside a cell
remain flagged. Future transport must retain those pieces and their individual
face incidence, not combine them into one raster node. Topological ocean IDs
and edge openings alone must not be promoted into physical solver links.

The editor exposes Water openings as a derived edge preview with four-direction
hover readout. Zoom changes display size only. Geography still has no stochastic
stage, authored province defaults, climate, bathymetry or world terrain output.

## Evidence and limits

See the [implementation report](../research/2026-09-25-context-reopening-and-gateways.md)
for analytic controls, corrupt-bundle admission, Tk workflow checks and measurements.
Geometric work remains row-local and cancellable between GEOS operations. Numeric
storage is bounded by the existing 360-row/259,200-cell limit; geometry scratch
is not an OS memory ceiling. Geographic exposure/province inputs remain next.

## Implementation references

- [Shapely geometry and affine transforms](https://shapely.readthedocs.io/en/stable/manual.html#shapely.affinity.affine_transform)
  define the planar set operations and edge-coordinate identification. Distances
  are converted with the declared spherical metric, not interpreted as page units.
- [NumPy load](https://numpy.org/doc/stable/reference/generated/numpy.load.html)
  documents numeric loading, pickle control and header limits. The shared adapter
  additionally validates admitted dimensions/dtypes/payload sizes before loading.
