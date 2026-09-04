# ADR-0015: Route automatic valleys on a canonical hydrology grid

Status: Accepted

## Context

Coordinate-addressed noise creates local relief at every requested resolution,
but it does not create a connected drainage hierarchy. Dark grooves may look
like valleys while climbing, terminating inland, or covering a slope uniformly.
Running a neighbourhood erosion solver directly on each output raster would
make the river network change with output resolution and break the existing
nested-sample contract.

Hydrology-based procedural terrain work instead treats the drainage network as
large-scale structure. Génevaux et al. generate continuous terrain around a
river network, while Cordonnier et al. combine a stream graph with uplift and
the stream-power equation. Priority-Flood provides a defined depression-filling
baseline, and recent comparisons support MFD for continuous contributing area.

## Decision

- Build one 257-cell-longest-side hydrology grid in metric world coordinates,
  independent of requested output resolution.
- Generate the stable two-octave macro-surface there. Keep it unchanged and
  create a separate temporary routing surface.
- Apply Priority-Flood to the routing surface. Raster edges and land beside sea
  or enclosed water are outlets. Raised cells get the smallest representable
  downstream grade so filled flats route deterministically.
- Accumulate contributing area with eight-neighbour MFD using weights
  proportional to `slope^1.1`, stable elevation ordering, and fixed neighbour
  order.
- Select larger drainage paths by contributing area and shape their depth with
  a bounded, stream-power-inspired area-and-slope response. Blend the channel
  with three masked smoothing passes to create shoulders rather than trenches.
- Bilinearly sample incision at output coordinates. Subtract it equally from
  macro and full-detail surfaces so residual frequency bands remain unchanged.
- Apply authored brushes, ridges, valleys, and exact heights afterward. Authored
  constraints remain authoritative.

## Consequences

- Major generated valleys are connected by contributing flow and grow toward
  outlets instead of being independent negative noise marks.
- Shared world coordinates receive the same automatic valley field regardless
  of output resolution.
- The canonical grid represents continental and regional valleys, not local
  gullies. Later refinement can add finer drainage inside parent catchments.
- Automatic routing currently uses the generated macro-surface, not authored
  ridges or rivers. A future reconciliation stage must condition divides
  explicitly and report conflicts without breaking authored structure rules.
- All unclassified depressions are filled only for routing. Authored lakes and
  endorheic basins still require explicit water constraints.
- The incision is process-informed shaping, not time-stepped erosion, sediment
  transport, climate, lithology, or geological simulation.

## Evidence

- Synthetic tests cover depression routing, downstream accumulation growth,
  rotational equivalence, channel concentration, deterministic builds, and
  nested 65/129 output samples.
- Primary references: Génevaux et al., [Terrain Generation Using Procedural
  Models Based on Hydrology](https://doi.org/10.1145/2461912.2461996), 2013;
  Cordonnier et al., [Large Scale Terrain Generation from Tectonic Uplift and
  Fluvial Erosion](https://doi.org/10.1111/cgf.12820), 2016; Barnes et al.,
  [Priority-Flood](https://arxiv.org/abs/1511.04463); Prescott et al.,
  [flow-routing comparison](https://esurf.copernicus.org/articles/13/239/2025/),
  2025; and Lague, [The stream power river incision model](https://doi.org/10.1002/esp.3462),
  2014.
