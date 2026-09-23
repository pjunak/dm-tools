# ADR-0064: Cancel generation at safe checkpoints

- Status: Accepted
- Date: 2026-09-23
- Extends: [ADR-0049](0049-navigate-and-save-authored-inputs.md) and
  [ADR-0063](0063-reuse-verified-parent-region-sessions.md)

## Context

The workbench reports progress but cannot stop a running generation. Verified
parent sessions now reuse expensive work; future local requests need to abandon
unwanted work without publishing partial artifacts or corrupting reusable state.

## Decision

Add a one-way `CancellationToken` and distinct `GenerationCancelled` exception.
Check the token at operation boundaries and on both sides of progress callbacks.
The existing progress path supplies checkpoints during preparation, replay,
regional sampling and detail batches. Whole-map water profile evaluation also
checks the token. Do not retain callbacks or tokens in prepared/cached results.
A fresh token is required for a retry; requesting a stop does not close a healthy
parent session or change its source/runtime validation rules.

Expose cancellation on whole-map generation, saved-project builds, regional
sampling and verified-parent writes. Check before reserving output and before
completion publication. Cancelled numeric work is never retained as a result;
valid completed numeric work and cell support may survive for a later retry.
Export cancellation leaves any written products incomplete. Publication starts
after the final check, so a later request does not undo an already completed
artifact. No existing output or parent is modified or removed.

The workbench reuses its Generate button as Cancel during generation and accepts
Esc as a stop request. Show elapsed time and the current stage. Keep the job busy
until acknowledgement and retain the previous reference. Identify progress,
result and failure events with the request token. Ignore old-job events; dispose
of their rendered images. If cancellation precedes UI acceptance of a queued
result, discard that result. Treat cancellation as a normal status, not an error
dialog. Numeric settings, authored inputs and undo history are unaffected.

## Limits and validation

This is cooperative cancellation. Individual native calculations, geometry
operations, rendering, hashing and file writes may run to completion before the
next checkpoint. No latency bound, thread termination, process-memory budget or
viewport job scheduler is implied. Import/open/save cancellation remains open.

Regression tests cover pre-cancelled operations, callback-triggered stops, stage
and chunk boundaries, exact uncancelled output, failed publication, session
retry/cache reuse, render-time cancellation, queued-result races, old-job event
rejection and return of workbench controls. The full Windows/Tk suite and strict
lint/type checks validate the shared paths. See the
[usage and lifecycle guide](../terrain-generation-control.md).

Terrain algorithms, seeds and schemas remain unchanged. Package source identity
still advances as normal, so saved parents must be rebuilt after this update.
