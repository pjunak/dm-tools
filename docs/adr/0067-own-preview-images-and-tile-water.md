# ADR-0067: Own preview images and tile water

- Status: Accepted
- Date: 2026-09-23
- Extends: [ADR-0066](0066-bound-terrain-rendering-scratch.md) and
  [ADR-0057](0057-display-water-at-the-appropriate-scale.md)

## Context

Ground shading scratch is bounded, but full-size water rendering still allocates
whole-raster area/fade/alpha/RGBA temporaries and an overlay. One-shot rendering
also duplicates ground despite owning it. The editor drops old image references
on replacement rather than explicitly closing their pixel buffers; Pillow's
in-memory image context manager does not close those buffers.

## Decision

Use 256-square tiles for water colour and opacity calculations, preserving the
existing Float32 arithmetic, pool-area thresholds, categorical sampling and alpha
composition. Native water composition paints directly into caller-owned RGBA
ground of matching size. It allocates no full-size area viewport or water overlay.
The API may partially paint its owned target on cancellation/failure; callers
close that derived target rather than exposing it as a completed result.

Viewport rendering retains the original whole-viewport affine transform, then
colours its area raster in tiles. Reconstructing an affine transform per tile can
round differently at sample boundaries. Keep this exact-pixel contract; the
area viewport and final RGBA viewport are deliberate retained allocations.
Full-source pool classification and its cached Float32 raster remain unchanged.

Separate owned from borrowed ground. One-shot rendering composes water into its
new ground image and transfers that image to the caller. Export of an editor's
retained reference makes one copy, closing it on failure. Layer preparation closes
partially constructed ground/water on failure or cancellation. `WaterDisplay.close`
releases its area image; callers explicitly close rendered images and owners.

The editor transfers a complete worker/style result before releasing the previous
ground/water. Reset and shutdown release these owners. Failed style replacement
keeps the previous view, water and legend. Review overlays close on replacement,
reset, shutdown or when both toggles are off; failed replacement closes its new
canvas while preserving the previous cache. Viewport and export temporaries close
after transfer/write, including failures. Tk photo references and the single owned
poll callback are released through the same lifecycle. Existing busy/unsaved-close
guards remain in force; no worker is forcefully terminated.

Pass workbench cancellation through ground rendering and check around native
water preparation. Water colouring/composition checks between tiles when a token
is supplied. No hard stop latency is promised for a native transform, connected
component operation or file encode.

## Evidence and limits

Tests compare exact dense/tiled water pixels across fractional transforms, scale
thresholds, tile boundaries and transparent ground. Ownership tests retain references
to discarded images to verify explicit closure on success, failure and cancellation.
Real-Tk tests cover map/style replacement, reset, navigation, hidden reviews, export
failure and shutdown, including old photo handles and the poll callback.

The [fresh-process comparison](../research/2026-09-23-preview-image-ownership.md)
measures isolated cached-water display, not complete geometry preparation, Tk,
worker coexistence or an OS memory limit. Aggregate application admission remains
open. No terrain formula, numeric data, water-visibility policy, schema, seed or
render metadata changes; normal source identity still requires rebuilding parents.
