# ADR-0047: Edit generation inputs only

- Status: Accepted
- Date: 2026-09-16
- Extends: ADR-0003, ADR-0004, ADR-0006, ADR-0030 and ADR-0034

## Context

The author wants to specify a map and regenerate it, using an earlier result to
place better instructions. Direct editing of completed terrain would introduce
a second source of truth and a separate workflow. Selected-region post-build
refinement and parent/halo requirements in earlier plans added that scope before
it was needed. Existing brush and area tools already produce authored inputs;
no generated-height sculpting API exists to retain.

## Decision

The active product edits pre-generation specifications only. Completed DEMs and
their images are read-only results. Adding or editing an instruction retains the
last successful generation as a background reference, then explicit generation
rebuilds from coastline, settings and constraints. Neither the previous image
nor DEM is an input to this operation. Remove post-build patching/refinement
requirements from the active strategy, TODO and current guidance.

Selection exposes the existing instruction properties. Apply replaces its
immutable domain value while preserving geometry. Instruction history covers
committed addition, replacement, deletion and clear-all. A new/opened project
resets history; unfinished vertices retain the existing backstep behavior.
Generator settings and drafts are not covered by committed-instruction redo.

Each generation worker returns its exact input snapshot with the result. Compare
that snapshot to the current inputs for persistent current/stale labelling and
PNG export eligibility, including settings edited during a worker run. A failure
leaves the previous reference available. Changing coastline/project clears that
reference because its frame and ownership may differ. Save files still contain
only authored state; image caches, selection and history are session-local.

Numerical adaptive sampling, shared-coordinate resolution checks and optional
process stages configured before generation remain distinct from output editing.
They do not provide a completed-map modification API. Dated research and accepted
ADRs retain their evidence; this decision supersedes their broader editing scope
where they conflict with the current product boundary.

## Consequences and validation

The editor can advance without a mutable DEM, patch storage, regional parent
identity, halo workflows or save migrations. Current controls support terrain
intent; future climate guidance needs an actual climate input/output contract.
Pan/zoom, vertex editing and save safeguards remain input-editor work.

Tests exercise immutable instruction history, every current property family,
selection, retained terrain, stale result/settings handling, failure/save state,
coastline replacement, and regeneration from revised inputs. Visual inspection
must check the desktop controls and reference labels as a separate gate.
