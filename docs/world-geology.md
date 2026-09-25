# Authored world geology

The World workspace now has a **Geology…** editor for pre-generation instructions.
It resolves continent defaults and explicit provinces into inspectable land
coverage. These are working hypotheses, not reconstructed Earth history or
implemented uplift, erosion, climate or world terrain. The existing local terrain
generator does not consume this recipe yet.

## Try it

1. Open a saved world, or import and validate its source/frame/assignments.
2. Choose **Geology…**. The world stays fixed while this editor is open.
3. Select a continent default. Choose a geological setting and optional ages;
   **Apply** validates the complete coverage. Blank ages mean unknown.
4. Choose **Draw province**, click at least three vertices, enter a name and
   priority, then **Apply / finish polygon** or press Enter on the map.
   Backspace removes the last vertex; Escape or **Revert / cancel** discards the draft.
5. Review **Geology coverage** colours, effective land area and numeric hover.
   Use **Source** or an available geographic context layer as the background.
   **Look** selects the direction for exposure/support backgrounds. The original
   Context page owns their numeric scales and geographic limitations.
6. Save a separate **`.dmgeology.json`** recipe. **Open recipe…** restores it against
   the currently open world. The editor remembers the last saved recipe during
   the application session and rechecks its file when reopened.

To use the synthetic example, open
[`four-shores.dmworld.json`](../examples/world/four-shores.dmworld.json), choose
**Geology… → Open recipe…**, and open
[`four-shores.dmgeology.json`](../examples/world/four-shores.dmgeology.json).
Use Save As for experiments. It has an active belt crossing two continent labels
and a rift crossing the longitude seam; its old-crust/young-rejuvenation values
are invented examples, not defaults for another world.

```powershell
dmtools terrain gui --world examples/world/four-shores.dmworld.json
dmtools world inspect-geology examples/world/four-shores.dmgeology.json
```

Use the tree or click resolved land to select a region. **Redraw** replaces a
province boundary after validation; **Delete** removes it. Defaults cannot be
deleted, and continent names/ownership are edited in the World workspace.
Twenty accepted edits are retained for Undo/Redo during a session. Apply or revert
an unfinished edit before changing selection or using history. Zoom and pan move
the view, not the authored geometry. There is no output sculpting.

## Values and overlap rules

- `setting`: unspecified, stable-interior, active-belt, rift, volcanic, or
  sedimentary-basin. These categorical hypotheses carry no implicit physical coefficients.
- `crust_age_ma`: optional age of the crust, in million years before the common present.
- `rejuvenation_age_ma`: optional time since uplift/rejuvenation, in the same units.
- `evolution_duration_ma`: optional requested simulation duration ending at that
  common present. It is not a crust age, an instruction to run a solver now, or
  permission to advance a refined region beyond its parent present.

Each numeric value is finite and in 0–1,000,000 Ma, or null/blank. This broad
admission bound is not geological calibration. Zero is distinct from unknown.
The fields are independent: old crust may carry recent rejuvenation. No
age-to-erodibility conversion, lithology, epoch schedule, seed or taper setting
is offered before a physical consumer defines and validates it.

Each continent has one complete default profile. A province overrides that
**entire profile**, including unspecified settings and blank ages. Higher
integer priority wins (0–100). Equal-priority provinces that compete for the
same effective land are rejected with their names. Boundary-only contact is
allowed; exact shared-edge inspection uses stable IDs. A higher-priority
province may mask a lower-priority conflict; removing that mask must resolve
without ambiguity or the deletion is rejected. Ocean-only overlap is harmless.

Province boundaries are independent of continent labels. Authored footprints
can include water, but only their intersection with prepared land receives
geology. A fully masked or ocean-only province is retained and reports zero
square kilometres; it is not silently deleted. The resolved regions cover all
prepared land exactly once, including existing source preparation adjustments.
Areas use the declared custom sphere, not pixel counts.

## Coordinates and limits

A province is a simple source-linear polygon with 3–256 distinct vertices,
without a repeated closing point or holes. Each edge, including closure, spans
at most half a world width in longitude; use intermediate vertices for longer
boundaries. The first vertex is inside the declared longitude frame. Subsequent
x coordinates may be unwrapped by one world width to cross its seam; the whole
ring spans at most one world width. Latitudes remain inside the world frame.
The editor unwraps each click to the nearest previous longitude. The closing
edge is checked rather than guessed; an unsupported winding must be redrawn.
Self-intersections and degenerate polygons fail without geometric repair.

There are at most 128 provinces. Coverage is a hard categorical partition.
Its boundary is **not** an elevation discontinuity or a physical forcing taper.
Continuous, calibrated forcing and any physical transition widths belong to a
later consumer. Vertex dragging, multipart/holed provinces, polar winding
conventions, per-field inheritance and rebasing to an edited world are follow-ups.

## Persistence and cancellation

The [current v1 schema](../schemas/world/geology-v1.schema.json) embeds the
retained world and a canonical SHA-256 identity of its entire source document:
SVG bytes, importer/preparation, frame/radius/meridian, names and assignments.
A different world is rejected, even if it reuses the same SVG. Reordered world
records have the same identity. Geographic context v3 and world-source v1 remain
separate formats; no generated bundle is modified when saving geology.

Recipes are limited to 40 MiB; their embedded world still has its 32 MiB limit.
Unknown fields, duplicate JSON keys and unsupported versions fail. Saving
validates geometry and retained source, writes a temporary sibling, flushes it,
then replaces the target. A loaded file's byte hash is checked before replacement;
an external edit or deletion requires reopening or Save As to another path.
This guard is not a cross-process filesystem lock.

Coverage/open jobs run off the Tk thread and support cooperative cancellation
between bounded geometry operations; an individual GEOS call or SVG parse is
not interruptible. Cancellation/failure retains applied inputs and the current
form/draft. Atomic saves finish before closing. Closing or replacing world input
also checks this editor's unsaved work. Save applies a valid pending edit first;
invalid input cannot disappear through a Save confirmation.

See [ADR-0076](adr/0076-author-world-geology-inputs.md),
[validation evidence](research/2026-09-25-authored-world-geology.md), and the
[WC0–WC6 plan](strategy/world-context.md) for the remaining generation work.
