"""Independent one-dimensional controls for the pinned implicit incision component.

These use a fixed outlet and closed sidewalls, not the rectangular product fixture.
Their convergence does not establish convergence of a changing two-dimensional network.
"""

from importlib import import_module
from typing import Any

import numpy as np


def channel_error(spacing_m: float, step_years: float, *, knickpoint: bool) -> float:
    package = import_module("landlab")
    components = import_module("landlab.components")
    length, duration, speed, slope = 12_000., 2000., 1., .01
    grid: Any = package.RasterModelGrid((3, round(length/spacing_m)+1), xy_spacing=spacing_m)
    grid.set_closed_boundaries_at_grid_edges(True, True, False, True)
    x = np.asarray(grid.x_of_node, dtype=np.float64)
    initial = slope*x + (200.*(x > 6000.) if knickpoint else 0.)
    z = grid.add_field("topographic__elevation", initial.copy(), at="node")
    router = components.FlowAccumulator(grid, flow_director="D8", runoff_rate=1.)
    eroder = components.FastscapeEroder(grid, K_sp=speed, m_sp=0., n_sp=1.)
    for _ in range(round(duration/step_years)):
        z[grid.core_nodes] += speed*slope*step_years
        router.run_one_step()
        eroder.run_one_step(step_years)
    exact = slope*x + (200.*(x > 6000.+speed*duration) if knickpoint else 0.)
    core = np.asarray(grid.core_nodes, dtype=np.int64)
    return float(np.mean(np.abs(np.asarray(z, dtype=np.float64)[core]-exact[core])))


def controls() -> dict[str, Any]:
    spatial = [{"spacing_m": dx, "step_years": 5.,
                "mean_absolute_error_m": channel_error(dx, 5., knickpoint=True)}
               for dx in (200., 100., 50.)]
    temporal = [{"spacing_m": 50., "step_years": dt,
                 "mean_absolute_error_m": channel_error(50., dt, knickpoint=True)}
                for dt in (100., 50., 25.)]
    return {"equation": "z_t = U - v*z_x; v=1 m/year, U=0.01 m/year",
            "initial": "0.01*x plus a 200 m step above x=6000 m",
            "duration_years": 2000., "outlet": "fixed zero at x=0; closed other boundaries",
            "steady_slope_mean_error_m": channel_error(100., 100., knickpoint=False),
            "knickpoint_spatial_refinement": spatial,
            "knickpoint_temporal_refinement": temporal,
            "scope": "linear fixed-flow component control; not 2D landscape convergence"}
