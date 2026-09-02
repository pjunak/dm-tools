# Terrain pipeline

This package will orchestrate explicit, named terrain stages. Each stage will
receive typed inputs, effective configuration, and its own deterministically
derived seed, then return typed outputs and diagnostics.

The implemented generator builds an unconditioned coordinate-addressed relief
field. When authored constraints exist, it separately builds a low-frequency
base, applies broad smooth ridge, valley, and height-point responses, and then
restores the high-frequency residual with attenuation near those features. Soft
terrain-brush strokes are combined as order-independent weighted targets before
structural constraints. The coastline remains a hard zero-elevation boundary.

Stages must not depend on implicit process state such as the current directory,
wall-clock time, ambient random generators, or undeclared environment settings.
