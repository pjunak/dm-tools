# Terrain pipeline

This package will orchestrate explicit, named terrain stages. Each stage will
receive typed inputs, effective configuration, and its own deterministically
derived seed, then return typed outputs and diagnostics.

The implemented generator builds an unconditioned coordinate-addressed relief
field. When authored constraints exist, it separately builds a low-frequency
base, applies broad smooth brush, ridge, valley, and height-point responses, and
then restores the high-frequency residual. Absolute constraints attenuate that
residual to satisfy world elevations. Relative constraints are deterministic
displacement fields over the surface entering their stage and preserve its
residual relief. The order is brush, ridge, valley, relative point, then exact
absolute point. Same-kind overlaps are order-independent. The coastline remains
a hard zero-elevation boundary.

Absolute height points attached to an absolute ridge or valley define a
shape-preserving longitudinal profile through their projected arc-length
positions. Baseline shoulder knots return isolated authored sections to the
structure target. The controlled centreline can rise or fall through peaks and
passes, while the existing cross-structure weight turns a lower crest anchor
into a saddle. Synthetic crest/floor variation is suppressed inside that
authored span so it cannot overshoot the supplied anchors.

A relative point near a relative structure is attached to the uniquely nearest
compatible line and uses the same longitudinal interpolation. Its signed value
modifies ridge relief as `base relief + displacement` or valley incision as
`base depth - displacement`. An attached point is consumed by the structure
profile and is not applied again as a circular point field. Ambiguous and
unattached relative points retain their free-standing displacement behavior.

Stages must not depend on implicit process state such as the current directory,
wall-clock time, ambient random generators, or undeclared environment settings.
