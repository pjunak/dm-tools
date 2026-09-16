# ADR-0049: Navigate and save authored terrain inputs

- Status: Accepted and implemented
- Date: 2026-09-16
- Extends: ADR-0047 and ADR-0048; no generator or project-schema change

## Context

The input-only workbench can retain a completed map but needs accurate placement,
usable inspection and safe project switching for practical generation testing.
Navigation must become a foundation for local generation without implying that
magnifying the current image produces additional terrain detail.

## Decision

Use a normalized geographic viewport independent of the result raster. Wheel
zoom anchors the pointer; middle/Space drag pans and Fit restores the overview.
The viewport exposes its visible bounds. Shared transforms drive drawing and hit
testing; UI dimensions and zoom never change source geometry or physical scale.
Only a canvas-sized image is resampled, and review layers are cached per result
and toggle combination. Coastline display transforms are computed once per draw.

Select mode moves whole instructions or individual vertices. Preview immutable
candidates while dragging, then validate geometry and commit one undo entry on
release. Preserve ring closure; translate lake outlets with their footprint and
retain their fractional edge position when a corner moves. Reject invalid land
placement, crossing polygons and touching/overlapping basins without changing the
input. Display line segments follow the authored polyline rather than an unrelated
smoothed canvas curve. Direct outlet relocation and vertex insertion remain open.

Track saved generation inputs separately from generated-result inputs. Drafts
and unapplied edits make the document dirty; navigation, selection and new-tool
defaults alone do not. Defaults are still included in an explicit project save.
Save reuses a known path; Save As selects a new path using the existing atomic
adapter. Open/import/close offer Save, Discard or Cancel. A save continuation runs
only on success and only while the saved snapshot still matches current inputs.
Failure or picker cancellation must leave the project open. Workers disable input
controls while geographic navigation remains usable.

Provide explicit 257/1025 px output presets, startup --project loading, overlay
visibility and nearest-ground-sample inspection for a short testing loop. These
presets are real saved settings. Results and navigation remain session-local.

## Validation and boundaries

Cover pointer anchoring, resize/pan coordinates, viewport-bounded allocation,
immutable move history, invalid topology/water crossings, ring/outlet movement,
cache reuse, save round trips, cancellation/failure and stale save completions.
Inspect the actual Tk flow at default and minimum sizes, including event bindings.
Run the full Python checks; numerical generator algorithms are unchanged.

Current zoom inspects existing samples. Regional requests, new local detail,
parent/overlap consistency and inherited hydrology remain the active future
scope of [ADR-0048](0048-keep-zoom-driven-detail-generation.md). Automatic draft
previews, worker cancellation, comparison views, autosave and precise numeric
geometry editing remain separate editor work. No manual generated-DEM modification
or legacy-save support is introduced.
