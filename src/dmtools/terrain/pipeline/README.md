# Terrain pipeline

This package will orchestrate explicit, named terrain stages. Each stage will
receive typed inputs, effective configuration, and its own deterministically
derived seed, then return typed outputs and diagnostics.

Stages must not depend on implicit process state such as the current directory,
wall-clock time, ambient random generators, or undeclared environment settings.
