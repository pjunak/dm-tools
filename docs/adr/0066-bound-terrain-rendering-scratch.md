# ADR-0066: Bound terrain rendering scratch

- Status: Accepted
- Date: 2026-09-23
- Extends: [ADR-0065](0065-admit-regional-memory-estimates.md)

## Context

A bounded numeric region can still allocate a disproportionate review image.
Three-pixel-wide, very tall requests previously produced three minimum-width
300-pixel panels at the full source height. A public stress case peaked above
one GiB despite fewer than two million buffered samples. Full-raster Float64
palette and hillshade temporaries also dominated ordinary ground previews.

## Decision

Render scientific and cartographic ground in 256 by 256 cores, with one-node
halos for the existing finite-difference gradient. Use the original full-grid
spacing rather than reconstructing tile extents, retaining identical native
pixels at interior and global boundaries, including coasts. The final native
RGBA image remains allocated; this bounds scratch, not the full output image.

Move saved-parent comparison rendering into its own adapter. Fit each panel
within 1024 by 1024 without upscaling and preserve aspect ratio to the nearest
representable pixel. Retain the 300-pixel minimum caption width and 56-pixel
vertical furniture, bounding the RGB canvas at 3072 by 1080. Use BOX resampling
only on this review product. Keep native `scientific.png`, numeric samples,
coordinates, seeds and detail evidence unchanged. Difference colouring is tiled
and its scale/labels use the maximum absolute native added height before resizing.
Record layout identity, native/panel sizes, reduction status and native maximum
in comparison PNG metadata; display reduced dimensions in the footer.

Check saved-parent cancellation between tiles and panels. Explicitly close all
owned intermediate and export images on normal and exceptional exits; do not
rely on an in-memory Pillow image context manager to free its pixel buffer.
Borrowed source images remain usable. Individual resizes, encodes and file writes
remain cooperative native operations with no forced stop-latency guarantee.

Replace the rendering admission coefficient with native-image, bounded-tile and
bounded-canvas allowances. Share renderer limits/layout calculation with the
estimator. These remain estimates rather than an operating-system memory cap.
No schema or numeric algorithm version changes are required. Derived comparison
layout is intentionally different; normal source identity checks require fresh
parents after the update, without an old-build compatibility path.

## Validation and remaining work

Exact dense/tiled pixel tests cover both palettes, non-square spacing, random
coastal masks, two-node axes, global edges and tile seams. Cancellation tests
retain references to owned images and verify explicit closure. A saved-parent
integration test verifies native samples/scientific size, bounded review PNG,
metadata and completion hashes. Fresh-process before/after runs check exact
numeric artifacts and native scientific pixels on square and thin requests.

This does not finish water/composition/diagnostic-image ownership, dense-source
geometry or aggregate editor/whole-map accounting. Keep those roadmap gates open
before viewport scheduling. See the [accounting guide](../terrain-regional-memory.md)
and [measured comparison](../research/2026-09-23-bounded-terrain-rendering.md).
