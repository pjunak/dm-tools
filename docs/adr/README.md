# Architecture decision records

ADRs preserve significant technical decisions and their trade-offs.

## Process

1. Copy the structure of an existing ADR.
2. Use the next four-digit sequence number.
3. Mark an undecided proposal as `Proposed` and an agreed decision as
   `Accepted`.
4. Do not rewrite an accepted decision to hide a later change. Add a new ADR and
   mark the old one `Superseded`.
5. Link implementation commits and validation evidence when they exist.

## Index

- [ADR-0001: Use Python 3.14 for the application and terrain engine](0001-python-3-14.md)
- [ADR-0002: Build the first terrain workbench with Tk and SVG input](0002-tk-svg-terrain-workbench.md)
- [ADR-0003: Author topography on the map and condition the base surface](0003-map-authored-constraints.md)
- [ADR-0004: Paint soft elevation guidance as vector strokes](0004-soft-elevation-brush.md)
- [ADR-0005: Separate absolute elevation from relative relief](0005-relative-relief.md)
- [ADR-0006: Persist authored terrain as versioned JSON with a verified SVG reference](0006-versioned-terrain-project.md)
- [ADR-0007: Use shape-preserving longitudinal profiles for anchored structures](0007-shape-preserving-structure-profiles.md)
- [ADR-0008: Interpret relative points as relative structure profile anchors](0008-relative-structure-profile-anchors.md)
