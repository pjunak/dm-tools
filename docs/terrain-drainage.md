# Drainage density and network review

The workbench separates generation inputs from inspection scale. Completed
terrain remains immutable; changing density or authored geography requires a
new generation. Diagnostic paths are planned channels, not validated river water.

## Try it

1. Open a current project and generate terrain.
2. Enable **Drainage review**. The overview prioritizes larger catchments.
3. Zoom in to reveal tributaries already present in the canonical network.
4. Enable **All channels** to inspect the complete network at any zoom.
5. Enable **Depressions** separately to inspect coarse basin/spill polygons.
6. To change the generated network itself, set **Drainage density**, then Generate.
   Start with 0.5 for a sparser comparison, or 1.5 for a denser one. Default is 1.0;
   the supported range is 0.25–2.0. The response is nonlinear and map-dependent.

Blue paths are planned channels; red segments are sampled uphill conflicts on
finished ground. Every red segment is drawn regardless of catchment filtering.
The legend reports selected/total reaches for the whole map at the current scale,
not only those inside the viewport. The separate **Depressions** toggle shows
purple basin areas and yellow spills;
it starts off so enlarged basin cells do not obscure the channel paths. Authored
lake outlets and basin catchments retain their existing diagnostic meanings.
The exported four-panel `drainage.png` remains the complete canonical-grid review.

## Generation contract

Density multiplies the slope/area initiation index and inversely scales the
minimum source area. The reference slope is computed independently of density,
so increasing density can only add channel candidates. Every candidate is traced
to its downstream terminal; no selected tributary is disconnected by thresholding.

Changing density leaves the planning elevation, D8 receiver field, MFD capture
and incision ceilings unchanged. The selected channels and resulting valley
shaping can change, including shoulder widths and the finished-ground agreement.
This parameter is not a runoff, climate, erosion-time or river-width model.
At density 1.0, the pre-change numeric behavior is preserved.

The current project format requires `settings.drainage_density`. Build v19, input snapshot v3 and
regional samples v3 record the new effective settings. Current examples are
updated; earlier formats are unsupported. Parent-region v1 retains its layout
and requires a current verified parent. Generator `coastline-constraint-terrain@18`
and valleys `regional-budget-mfd-d8-valleys@14` identify the new input semantics.

## Connected display

A reach runs from a head or junction to the next junction or terminal. Every
selected D8 edge belongs to exactly one reach, and shared junction coordinates
are exact. Reach importance uses unique D8 contributing area at its last donor,
before other tributaries join. It therefore never decreases downstream. MFD
capture is a separate quantity and is not used for this hierarchy.

A reach fades in as the square root of its contributing area in screen pixels
passes 64 px and reaches full opacity at 112 px. These are cartographic thresholds,
not catchment boundary dimensions or inferred water widths. The downstream reach
always has at least as much opacity, preserving visible drainage connections.
Pan/cropping cannot change a reach's importance. Stream order changes display
stroke prominence only; it does not set physical channel incision or width.

Paths are redrawn at viewport resolution with antialiasing. Only collinear
vertices are removed; no artificial bends or displaced junctions are introduced.
The renderer retains one output image plus a 256 px tile with a 5 px halo and
3x antialiasing scratch, independently of zoom. The graph is cached per result;
no zoom-sized offscreen map raster is allocated.

## Limits and next work

The routing grid still has 257 samples on its longest axis. Output resolution
and view zoom do not refine that graph. This batch removes magnified line pixels
and overview clutter; it does not solve D8 direction bias, between-node channel
rises, river meanders, runoff or fine local tributary generation.

The next priority is terrain-guided paths shared by the routing, floor-fitting
and rendering stages. Compare them against the current graph using actual
finished-ground profiles, junction/connectivity tests, angular bias, incision
budgets, authored divides and lake terminals. Filled-depression convergence and
D-infinity accumulation are separate candidates; neither is a substitute for
validated channel geometry. See [TODO](../TODO.md),
[ADR-0069](adr/0069-connect-and-scale-drainage-review.md) and the
[measured public cases](research/2026-09-24-connected-drainage-review.md).
