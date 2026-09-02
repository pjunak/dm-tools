# Runtime dependency register

The first terrain vertical slice uses the following runtime dependencies. The
version range in `pyproject.toml` is authoritative; versions below are the
minimum accepted versions when the dependency was adopted.

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

The repository itself still needs a distribution license before a public
release. Dependency permissions do not license project-owned code.
