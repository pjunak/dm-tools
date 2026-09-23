# Preview image ownership and water composition - 2026-09-23

## Finding and implementation

After ground shading was tiled, native water composition still created a
whole-raster area viewport, opacity arrays and RGBA overlay before blending.
One-shot map rendering also copied its newly created ground, even though no
other owner needed to retain it. Editor replacement and reset paths dropped
old image references without explicitly closing the underlying pixel buffers.
Pillow's in-memory context exit alone does not perform that close.

Water colouring now runs in 256-square tiles. Native composition paints directly
into its owned ground target and does not allocate a full water overlay or area
viewport. The editor's PNG export copies borrowed reference ground once;
one-shot rendering composes into its new image and transfers it directly.
Viewport rendering keeps the original nearest-neighbour affine transform for
its categorical area raster, then colours that raster in tiles. Keeping the
transform intact avoids subtle sampling changes at fractional tile boundaries.
The final area and RGBA viewports still occupy canvas-sized buffers.

The editor explicitly releases ground, cached water areas and diagnostics on
replacement/reset/shutdown. Hiding both diagnostic layers releases their cache.
Temporary viewport and export images close after Tk transfer or PNG writing,
including failures. Old Tk photo references and the owned polling callback are
released too. Failed style replacement preserves the old image, water, selected
style and legend. Failed diagnostic replacement closes its new canvas while
retaining the previous cache. Workbench cancellation reaches ground-render tiles
and checks around native water classification; colour tiles accept the same token.

These changes preserve native pixels and water visibility. They introduce no
terrain formula, schema, seed, numerical resolution or rendering-metadata change.
They do not modify a completed DEM. See
[ADR-0067](../adr/0067-own-preview-images-and-tile-water.md).

## Reproduction

Run from the repository root on each revision, using new report names:

```powershell
python -m benchmarks.preview_memory --resolution 1024 4096 --mode compose water viewport --output artifacts/preview-memory.json
```

The benchmark creates a square RGBA ground image and a Float32 area image with
synthetic category bands at 0, 4, 9, 16, 25, 36 and 100000 source pixels squared.
These are intentionally synthetic cached display inputs, not a geographic lake
fixture. They exercise hidden, fading and opaque alpha calculations while
excluding generation and polygonization/rasterization from the measurement.
The ground colour is (83, 127, 96, 255).

Each size/mode gets a fresh process and three serial renders. Modes are:

- `compose`: compose borrowed native ground and water at full source dimensions;
- `water`: render a native-sized standalone water overlay;
- `viewport`: render water into a fixed 1296 by 768 output, with the same
  fractional display rectangle (-175.25, -102.75, 1950.5, 1830.125).

Times cover the rendering call only. Peak resident memory is the process-lifetime
native high-water mark, including imports, source buffers and allocator retention.
Pixel hashes are computed outside timing in 64-row bands so hashing does not
allocate another full-size image. Reports also retain setup/baseline peaks and
source hashes. Source/runtime drift prevents report publication. No concurrent
terrain tests or other terrain benchmarks ran during these measurements.

Environment: Windows 11 AMD64, CPython 3.14.7, NumPy 2.5.2 and Pillow 12.3.0.
Before package source:
`70f46a39fe16b6a8530614a89471bc1ca9087d2bc80cf4551a740fa09572a916`.
After package source:
`f17c890aaff063fd736dde28f66aee387b827220598b8e822c8075ffbdd75885`.

## Measurements

MiB means 2^20 bytes. Peak is the maximum recorded across the three renders;
time is their median. There is one fresh worker per mode/size per revision,
not repeated independent trials or a cross-machine guarantee.

| Source size / mode | Before peak MiB | After peak MiB | Before median seconds | After median seconds |
|---|---:|---:|---:|---:|
| 1024 / compose | 97.4 | 75.5 | 0.0141 | 0.0118 |
| 1024 / water | 93.6 | 79.5 | 0.0115 | 0.0095 |
| 1024 / viewport | 92.3 | 78.9 | 0.0108 | 0.0089 |
| 4096 / compose | 638.6 | 256.7 | 0.2352 | 0.1707 |
| 4096 / water | 574.6 | 319.7 | 0.2151 | 0.1279 |
| 4096 / viewport | 213.3 | 198.8 | 0.0111 | 0.0091 |

The 4096 composition process peak fell about **60%**; the full water overlay
case fell about 44%. Native composition retains the borrowed ground, cached
area raster and an export copy; it cannot be constant-memory. The standalone
water case deliberately still retains an area viewport and output image.
The fixed viewport's higher peak with a 4096 source primarily includes the
larger retained source buffers; zoom does not request a source-sized display.
These isolated timings improved in this run, but no UI-latency promise follows.

The one-shot ground-copy removal is verified separately by ownership tests;
the `compose` benchmark intentionally exercises the borrowed-reference path
that still needs one copy. Do not add the removed-copy saving to these measured
numbers as though it were another measured effect.

## Correctness and lifecycle evidence

All 12 workers produced identical repeated output pixel hashes. Across revisions,
all six corresponding source and output hashes matched exactly. Unit tests add
an independent dense opacity control with fractional offsets, anisotropic scale,
large magnification, transparency, threshold-adjacent values and tile seams.
Native tiled alpha composition also matches a complete-overlay control with
random ground alpha, and preserves the borrowed input pixels and metadata.

Ownership tests hold discarded image objects alive and confirm that their buffers
are explicitly closed. They cover cancelled water tiles, failed/cancelled layer
preparation, failed composition, one-shot ground ownership and water disposal.
Real-Tk tests cover new-result acceptance, project reset, style switching and
style failure, navigation photo replacement, hidden diagnostics, failed overlay
replacement, failed PNG export and shutdown. They verify retained references stay
usable where required, old buffers/handles close, and the poll callback is removed.
Existing input-editing, cancellation, water-display and build tests remain applicable.
These are automated Tk workflow checks, not a manual UX acceptance session.

Reports remain ignored under `artifacts/`:

| File | SHA-256 |
|---|---|
| `preview-memory-20260923-before.json` | `0b6a3984fe73c4e6b70961192e66bbbd604f153474c4438aee702b0ef14d5602` |
| `preview-memory-20260923-after.json` | `ff691eb9f512053e0ba06bd7b70249ae2c4dcc0f37d9e7937701d71768cc170e` |

## Remaining work

Whole-source wet-component polygonization/rasterization and its geometry are not
tiled by this change. The cached area image, native reference image, numeric
terrain, diagnostic preparation and Tk copies remain real costs. Concurrent
old-reference/new-worker storage, long sessions and complex source geometry still
need aggregate measurements and an application admission policy. The saved-parent
memory pool does not yet cover the editor or whole-map workers. Explicit release
does not promise immediate resident-memory return from Python/native allocators.

The [TODO](../../TODO.md) keeps that broader gate open. Local-detail visual/spectral
acceptance and inherited finer hydrology remain separate work; neither zoom-driven
automatic generation nor small rivers are enabled by these display changes.
