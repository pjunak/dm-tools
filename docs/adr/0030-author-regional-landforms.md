# ADR-0030: Author regional landforms before constraints and drainage

**Status:** Accepted
**Date:** 2026-09-08

## Decision

Add a normalized polygon constraint with typed landform settings for plains,
hills, plateaus and mountain belts. Keep geometry preparation and NumPy field
composition in `pipeline/landforms.py`; domain data has no Shapely dependency.
The Tk tool, project adapter and headless generation share these values.

Blend regional full/macro fields before the existing local constraints. Use
smoothstep influence over the inward boundary distance, zero outside the
polygon, and stable-order normalized overlap blending. Pass the same prepared
regions to routing, valley-profile references, final sampling and diagnostics.
Retain exact authored points, the land mask and the global elevation ceiling.

Use one named `terrain.landforms` stream independent of `terrain.relief`.
An elongated ridged carrier with a separate coordinate window for crest-height
variation defines mountain belts. Region identity/order does not seed the field;
editing or inserting a distant region cannot scramble another one's base noise.
The stage remains a procedural model, with no claim of geological simulation.

Project format 4 replaces 3; build format 6 replaces 5 and records the regional
algorithm and seed. Replace obsolete schemas and update examples; no legacy
loader or migration command is introduced. Generator identifier advances to
`coastline-constraint-terrain@3`; regional recipe identifier is `regional-landforms@1`.

Render planned D8 channel edges directly at display dimensions. The former
nearest-neighbour enlargement turned one canonical cell into a thick block;
changing that display does not increase the physical routing resolution or
repair remaining uphill segments.

## Validation and limits

Test recipe elevation/relief differences, mountain orientation, smooth regional
boundaries, invalid controls/geometry, overlap order, exact anchors, shared
nodes and selective/dense sampling including masked islands and holes. Validate
current JSON schemas and region save/load, and exercise polygon finish,
reopening and undo in Tk. Inspect fixed-seed before/after rendered terrain.

This is a first regional composition slice. Regional hydrology/erosion tuning,
quantitative lowland fractions, continuous plateau escarpment authoring and
connected ridge/divide skeletons remain separate work. No canonical geography
was inferred from the user's Tharkeniss Veld screenshot or applied to that map.

Validation completed on Windows/CPython 3.14: 194 tests, Ruff, strict Pyright
and dependency checks pass. The current public regional example built through
the CLI. Hidden Tk checks exercised polygon drawing, finish, save/reopen,
tool switching and undo. Fixed-seed renders were inspected after varying
mountain crest heights. In the 1000 km square, seed-42, 257-node comparison,
central elevation standard deviations were 15.8 m (plain), 112.5 m (hills),
17.1 m (plateau) and 676.2 m (mountains). These fixture measurements demonstrate
recipe separation, not a general terrain realism score or validated hydrology.
