# ADR-0079: Project connected world land into terrain projects

- Status: accepted
- Date: 2026-09-27

## Context

The world workspace retains authored geography and geographic context, while
users had to re-export continents independently to test local terrain. Separate
bounding-box scaling loses the world's metric scale; cutting a semantic
continent border out of connected land creates a false coast. Ordinary terrain
SVG cleanup can also remove legitimate tiny holes and gaps.

## Decision

Add an explicit standalone handoff. Start with every component belonging to the
chosen continent and include physically touching land transitively, including
world seams and poles. Include only connected foreign components, not every
island owned by a neighbouring continent. Preserve original semantic identity
in a retained world snapshot while dissolving internal borders for the terrain
coastline. Choose the projection centre from dissolved physical land, not
ownership pieces, so splitting the same geography cannot change its generated
terrain. Normalize only redundant collinear vertices and ring ordering.

A tiny gap is still authored water until its intent is established. Repair
confirmed accidental drawing offsets in the source; do not globally close gaps
or infer dry land from continent names.

Use Rasterio/PROJ spherical azimuthal equidistant projection with the declared
planet radius. Record centre, maximum sampled angular radius/transverse scale,
25 m curve tolerance and 0.25-degree source step. Refuse hemisphere-sized or
beyond-80-degree selections rather than resizing the world or clipping land at
an ownership border. A future regional-domain operation must supply shared
terrain boundary conditions.

Write a canonical prepared SVG containing visible projected paths and complete
world/projection/coastline metadata governed by world terrain source v1.
The reader verifies that metadata and visible paths agree and restores polygons
without generic SVG cleanup. The source remains usable as an ordinary terrain
project v6 path/hash reference. Fix object scale to projected extent in kilometres.
The retained projection uses east/south metres; the existing local frame and
Float32 DEM authority remain unchanged.

Keep selection, GIS projection, file format, application publication and panel
controls in separate modules. Create a fresh folder, verify the source, then save
the ordinary terrain project as the completion record. Preserve existing output
and unsaved editor work. The CLI and workbench call the same operation.

## Consequences and alternatives

Users can test real-world continents now, before climate/history coupling is ready.
A folder containing the project and prepared SVG is portable and keeps the
original world even if the external world source moves. Updating world geography
requires an explicit new handoff; existing terrain instructions are not rebased.

Simple per-continent normalization was rejected for losing physical scale and
neighbour continuity. Generic local SVG reimport was rejected for its deliberate
morphological simplification. A full climate/aging pipeline is unnecessary for
this usable handoff and retains separate adoption gates.

Projection has measurable distortion. No single plane serves a whole planet.
The existing GeoTIFF/build coordinate contract remains local and does not embed
the source's global correspondence. Inland holes retain the current coastline
semantics; this feature does not infer lake levels or improve drainage physics.
See the [workflow and evidence](../research/2026-09-27-world-to-terrain-workflow.md).
