# Runtime dependency register

The first terrain vertical slice uses the following runtime dependencies. The
version range in `pyproject.toml` is authoritative; versions below are the
minimum accepted versions when the dependency was adopted.

This register lists packages and data actually used at runtime. Evaluated
candidates remain in [dated research](research/README.md) and the
[current strategy](strategy/README.md) until an implementation has an immediate
need, supported-platform validation, and a completed license review.

| Dependency | Minimum | Purpose | License |
|---|---:|---|---|
| CPython Tk/ttk | 3.14 / Tk 9 | Native desktop widgets, progress, and file dialogs | PSF / Tcl-Tk BSD-style |
| NumPy | 2.5.2 | Deterministic array computation and Float32 elevation grids | BSD-3-Clause |
| Pillow | 12.3.0 | In-app raster preview and PNG export | MIT-CMU |
| Shapely | 2.1.2 | Polygon validity, land mask, and distance-to-coast queries | BSD-3-Clause |
| svgelements | 1.9.6 | SVG shape/path parsing, transforms, and curve evaluation | MIT |

Primary references:

- [Python Tkinter documentation](https://docs.python.org/3/library/tkinter.html)
- [NumPy licensing](https://numpy.org/doc/stable/license.html)
- [Pillow licensing](https://github.com/python-pillow/Pillow/blob/main/LICENSE)
- [Shapely project documentation](https://shapely.readthedocs.io/)
- [svgelements package page](https://pypi.org/project/svgelements/)

## Vendored data assets

| Asset | Version | Purpose | License |
|---|---:|---|---|
| Scientific Colour Maps `oleron` land lookup table | 8.0 | Perceptually ordered, colour-vision-deficiency-safe elevation tint | MIT; Copyright (c) 2023 Fabio Crameri |

The terrain renderer includes entries 128–255 of the `oleron` RGB table rather
than adding a plotting-library dependency. See the
[upstream palette](https://github.com/callumrollo/cmcrameri/blob/main/cmcrameri/cmaps/oleron.txt),
[Scientific Colour Maps](https://www.fabiocrameri.ch/colourmaps/), and the
[vendored license notice](licenses/SCIENTIFIC_COLOUR_MAPS_LICENSE.txt).

The repository itself still needs a distribution license before a public
release. Dependency permissions do not license project-owned code.
