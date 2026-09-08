# ADR-0029: Route drainage over authored terrain

**Status:** Accepted
**Date:** 2026-09-08

## Decision

Plan automatic valleys on the canonical 257-node-longest-axis grid after
applying the currently supported brush, ridge, valley and point constraints.
Supersede the unconstrained routing order of ADR-0015 and the automatic-incision
dependency in the relative-valley reference of ADR-0014.

Prepare authored valley profiles first. Relative valley depth uses the stable
unincised base plus brush/ridge guidance and retained detail; absolute profiles
keep their authored levels. Their non-rising floors are fixed before routing.
There is one planning pass, not an iterative feedback loop.

Apply the resulting automatic incision to the base, then evaluate the same
prepared constraints and restore retained detail for the finished field. This
bounded reconciliation preserves the existing point/structure precedence and
avoids adding relative displacements twice. Absolute anchors remain authoritative.
It can disagree with the planned drainage. It is not a coupled constrained
hydrology solve, and no generated process may silently move an authored point.

Retain the planning DEM, Priority-Flood copy, D8 receivers, MFD accumulation,
channel heads, channels, Strahler order, outlets and incision. Sample the
finished Float32 field on those same canonical nodes. Compare its filled D8
receivers with planned channel receivers, and separately measure uphill edges
on its unfilled elevations using a 0.001 m tolerance. Receiver changes alone
are not necessarily errors; final-surface uphill segments need review.

Expose the review in the workbench as a toggleable channel overlay and in
headless builds as `routing.npz`, `drainage.png` and diagnostics. Build schema 5
replaces 4; project schema 3 and named seeds are unchanged. Generator and
valley algorithm identifiers advance; there is no compatibility branch.

## Limits and consequences

Maps with authored constraints intentionally change, including areas downstream
of an edit. The canonical process grid remains independent of export resolution.
The comparison samples the same field as the DEM, but is not an analysis of
all delivered raster nodes. Source and final arrays share the routing grid.
Both use zero outside land and require the stored land mask.

Relative valley depths no longer depend on earlier automatic valleys. Existing
relative brush/ridge offsets still act on the terrain entering their final
constraint stage. Minor differences in otherwise similar authored surfaces can
change flow paths, so junction geometry is tested on the authored surface and
final junction relief separately.

There are no explicit river/divide entities or authored lake levels yet.
Conflicts are reported, not repaired through a new erosion process. Regional
landform controls are the next visible-quality feature; topology provides a
reviewable basis for later lakes and rivers.

## Validation

Controlled ridge, pass anchor, valley, coastal outlet and brush cases must alter
planning; exact absolute anchors, zero shoreline, deterministic topology and
shared output nodes remain checked. Synthetic uphill edges verify disagreement
without mutating terrain. Builds validate current schema, source linkage,
product hashes and byte-for-byte repeatability, including the numeric archive.

Validation completed on Windows/CPython 3.14: 177 tests, Ruff, strict Pyright
and dependency checks pass. A public example build completed; the authored
benchmark review image was inspected, and the Tk overlay toggle passed a
hidden-window smoke check. The seed-42 authored case reports 390 uphill edges
of 2455, with 135.07 m maximum rise. This establishes a measured remaining
limitation, not a hydrologically accepted final river network.
