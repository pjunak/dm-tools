# ADR-0008: Interpret relative points as relative structure profile anchors

**Status:** Accepted
**Date:** 2026-09-03
**Deciders:** Repository owner and project maintainer

## Context

ADR-0007 gave absolute ridges and valleys a continuous, shape-preserving
longitudinal profile. Relative height points still remained independent circular
displacement stamps applied after relative ridges and valleys. A relative peak
could build on a range, but it could not shape the crest leading toward that
peak or form a controlled pass between two summits.

Relative point values are signed vertical displacements, while relative ridge
and valley values are non-negative relief and incision magnitudes. Attaching a
signed point to a structure therefore requires different arithmetic for ridges
and valleys. It also requires an unambiguous ownership rule where structures
cross or run close together.

## Decision

- Consider a relative height point for automatic attachment only to relative
  ridges and valleys within the existing attachment distance.
- Attach it to the uniquely nearest compatible structure. If the nearest
  candidates have the same distance within numeric tolerance, leave the point
  free-standing rather than choosing according to authored list order.
- Project an attached point onto the chosen structure's arc length and use the
  same shape-preserving longitudinal interpolator and shoulder behavior as an
  absolute profile.
- For a relative ridge with base relief `R` and attached signed point
  displacement `d`, set the profile relief target to `R + d`.
- For a relative valley with base incision depth `D`, set the profile depth
  target to `D - d`. A positive point raises the valley floor and makes the
  incision shallower; a negative point lowers it and makes the incision deeper.
- Reject a profile target below zero. Reversing a ridge into a valley or a
  valley into a ridge must be authored as a different structure, not hidden in
  a point value.
- Consume an attached relative point in the structure profile. Do not apply its
  circular displacement again in the later relative-point stage.
- Preserve free-standing relative point behavior when no compatible structure
  is nearby or ownership is ambiguous.
- Do not attach an absolute point to a relative structure, or a relative point
  to an absolute structure. Mixed-mode semantics remain explicit rather than
  inferring a reference elevation from another pipeline stage.

## Options considered

### Keep relative points as circular stamps

This preserves the previous implementation but leaves peaks and passes as
local blobs rather than longitudinal features of their parent range.

### Attach a relative point to every nearby relative structure

This mirrors absolute crossing behavior, but one displacement would silently
reshape several structures and the result around crossings would be difficult
to predict. It also makes nearby parallel structures share anchors too easily.

### Attach to the uniquely nearest compatible structure

This gives one profile clear ownership, is independent of constraint order, and
falls back to the established free-standing behavior when ownership cannot be
resolved safely.

## Consequences

- Relative peaks and passes now shape the crest between authored points instead
  of adding isolated radial stamps.
- A relative valley can become shallower or deeper along its course without
  replacing the elevation of the terrain beneath it.
- Existing projects with a relative point near a relative ridge or valley will
  generate different terrain. Unattached and ambiguous points retain their
  previous behavior.
- The stored constraint schema does not change. Attachment is a deterministic
  derived relationship during generation.
- Automatic ownership remains intentionally conservative. Explicit parent
  identifiers and dedicated peak/pass handles may replace proximity attachment
  in a later schema version.
- This is terrain shaping, not a hydrologic guarantee. Valley profiles still
  need downstream monotonicity and outlet validation.

## Validation

- A two-peak/one-pass relative ridge fixture verifies exact relief anchors, no
  interval overshoot, saddle geometry, order independence, and nested-resolution
  equality.
- A relative valley fixture verifies that positive points reduce incision and
  negative points deepen it without profile overshoot.
- Existing peak-on-ridge coverage verifies that an attached point is consumed
  once rather than applied both as a profile anchor and a circular stamp.
- Equidistant candidate structures produce the same terrain after constraint
  reordering because the point remains free-standing.
- Invalid relative anchors that would reverse the parent structure are rejected.
