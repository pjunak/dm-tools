# Terrain algorithm options — 2026-09-03

Status: working research, not accepted architecture.

This note narrows the algorithm items in the terrain roadmap. It is concerned
with believable, controllable results rather than reproducing a planet's full
geological history. The authoritative product should remain a numeric DEM;
contours, colour relief, hillshade, rivers, and meshes are derived views.

## Recommended order of work

1. Build quantitative synthetic fixtures and diagnostics before replacing the
   current generator. Attractive previews cannot distinguish improvement from
   a different style.
2. Formalize hard, soft, relative, and inequality constraints.
3. Benchmark two low-frequency correction solvers against the current smooth
   response: local RBF and a sparse screened-Poisson/biharmonic solve.
4. Add drainage analysis and an explicit depression policy. Prototype MFD for
   continuous accumulation and D8 where a unique receiver tree is required.
5. Only then test stream-power incision and nonlinear hillslope relaxation as
   optional, versioned process stages.

The first useful architecture is therefore a hybrid, not a wholesale rewrite:
keep the deterministic coordinate-addressed base and residual-detail model,
then solve a broad correction field that makes authored structures interact
coherently. Reapply hard constraints after every optional process stage.

## Mature approaches and experimental references

| Approach | Best use here | Main limitation | Recommendation |
|---|---|---|---|
| Sparse diffusion, Poisson, or biharmonic solve | Broad surface connecting points, feature curves, coastline, and slope guidance | Boundary conditions and grid spacing affect the solution | Prototype now |
| Local radial-basis interpolation | Smooth point-driven correction with a compact implementation | No native drainage semantics; global solve scales poorly | Prototype now |
| ANUDEM-style conditioning | Reference behavior for integrating points, contours, streams, sinks, cliffs, and boundaries | A complete equivalent is a substantial subsystem | Use as a benchmark and design reference |
| Priority-Flood depression handling | Drainage repair, basin labeling, and deterministic hydrology primitives | Filling every depression destroys real lakes and endorheic basins | Implement only with an authored depression policy |
| Stream-power erosion plus nonlinear diffusion | Process-informed river incision and hillslope form | Resolution and timestep dependent; can overwrite authored intent | Optional experiment after diagnostics |
| Iso-contour terrain authoring | Editable vector elevation hierarchy and level-of-detail experiments | Recent work reports overly smooth surfaces and weak fine drainage | Experimental reference |
| Oriented procedural terrain patterns | Structure-aligned ravines and multiscale residual detail | Texture model, not a hydrology or geology solver | Experimental residual-detail stage |

## Low-frequency surface solvers

### Constraint contract first

The solver should receive distinct constraint classes instead of reducing all
authoring to weighted target heights:

- **Hard Dirichlet:** coastline/water level and exact spot elevations. These
  must be restored exactly at represented samples after every stage.
- **Inequality:** a ridge crest is at least a requested elevation or relief; a
  valley floor is at most a requested elevation or relative incision.
- **Soft target:** brush guidance and broad preferred heights with an explicit
  weight and transition reach.
- **Derivative or breakline:** preferred slope, crest normal, cliff
  discontinuity, or drainage direction along a feature curve.
- **Relative:** displacement from a named, stable low-frequency reference
  surface, not from the partially modified result of the previous object.

A useful conceptual objective for one correction field is:

```text
minimize  sum_i w_i (h_i - t_i)^2
        + lambda * integral |gradient(h)|^2
        + mu * integral (laplacian(h))^2
subject to hard elevations and authored inequalities
```

This is a specification aid, not yet a selected discretization. The gradient
term discourages unnecessary relief; the Laplacian term discourages abrupt
curvature. Their physical meaning must not be overstated.

### Candidate A: local RBF correction

SciPy's `RBFInterpolator` supports exact interpolation when smoothing is zero,
several kernels, and a `neighbors` limit for local evaluation. Its documented
memory use grows quadratically with the number of data points for a global
solve, becoming impractical beyond roughly a thousand points. Shape-parameter
kernels can also become ill-conditioned. A local RBF is therefore suitable for
a comparison spike, not automatically for the final continent-wide solver.

Questions for the spike:

- Can a deterministic neighbor selection and overlap rule avoid tile seams?
- Does a low-degree polynomial tail preserve broad slopes without ringing?
- How do curve samples bias the fit compared with isolated point constraints?
- Can inequalities be projected after the solve without visible plateaus?

### Candidate B: sparse screened-Poisson or biharmonic correction

Feature-curve terrain research demonstrates diffusion from parameterized
ridge, riverbed, and cliff curves with elevation, slope, and roughness
constraints, accelerated with multigrid. This matches authored structures more
naturally than stamping kernels at line vertices. An in-project prototype can
start with a regular-grid sparse system and conjugate-gradient solve; multigrid
is an optimization only after the formulation is useful.

Questions for the spike:

- Which boundary condition preserves the exact coastline without an artificial
  coastal rim?
- Is the operator and stopping criterion stable across 65, 129, and 257 sample
  fixtures?
- Can ridge and valley derivative constraints be expressed without producing
  overshoot at intersections?
- What halo is required for indistinguishable regional solves?

### Candidate C: hydrologically conditioned interpolation

ANUDEM is the strongest specification reference found. It integrates point
elevations, contours, streams, sinks, cliff lines, boundaries, and lakes; it
also reports sinks and scaled residuals rather than silently hiding conflicts.
We should borrow those contracts and diagnostics even if the implementation is
not ANUDEM itself. Hydrological conditioning should not be fused into the first
surface-solver spike: otherwise it will be difficult to tell whether geometry
or drainage repair caused a change.

## Drainage and valley generation

### Depression policy

Every depression must be classifiable as one of:

- an authored lake with a water level and outlet or endorheic status;
- an authored endorheic basin;
- a permitted small natural depression; or
- an accidental obstruction that may be breached or filled.

Priority-Flood is a robust baseline for detecting and filling accidental
depressions. Least-cost breaching may alter less terrain than filling and
should be compared on the fixtures. Neither operation should touch authored
basins without explicit permission. The raw pre-conditioning DEM, conditioned
DEM, and elevation delta should remain inspectable.

### Flow routing

- Use **MFD** first for accumulation, erosion forcing, and broad convergent
  flow. Recent comparison work found it more rotationally stable than D-infinity
  on analytic terrains; begin with a documented exponent near 1.1 and measure
  sensitivity rather than declaring it universal.
- Use **D8** when a unique downstream receiver, basin label, or river tree is
  required. Its 45-degree grid directions make it unsuitable as the only
  continuous-flow model.
- Keep **D-infinity** as a comparison, not the default. It can retain cardinal
  and diagonal grid bias.
- Treat iterative depth-based routing as later research. It better represents
  cases where water-surface slope differs from bed slope, but is too expensive
  for the first terrain-generation loop.

A user-authored valley should first receive a monotone longitudinal target
toward its outlet, except across an explicitly authored lake or basin. Its
floor then becomes a relative inequality against the reference terrain. Flow
analysis verifies the result; it must not silently move the authored route.

### Implemented downstream profile

The first implementation samples the complete deterministic surface entering
the valley stage at resolution-independent metric positions no more than 2 km
apart, inserting every authored profile anchor as an exact knot. Valley points
are ordered from head to outlet. Relative depth produces a preferred floor;
applying a cumulative downstream minimum makes the smallest downstream-only
cuts needed to remove rises. Absolute anchors must already be non-rising and a
conflict is reported instead of moving a hard height. This is longitudinal
conditioning, not yet full drainage validation: lakes, endorheic basins, flow
routing, and outlet-to-sea checks remain separate work.

### Implemented automatic broad valleys

The first generated-drainage stage follows the network-first direction of
Génevaux et al. and Cordonnier et al. A fixed 257-cell-longest-side grid routes
the stable macro surface with Priority-Flood and MFD (`slope^1.1` weights).
Contributing area selects larger drainage paths; a bounded area-and-slope
incision proxy plus masked smoothing creates connected valley centres and
shoulders. The world-coordinate field is sampled by every output resolution,
so refining an image does not reroute its major network.

The second refinement separates continuous accumulation from centreline
topology: MFD retains broad convergence, while a steepest-receiver D8 tree
locates one generated centre. A bounded logarithmic area hierarchy blends
narrow, near-shoulder, and broad-trunk kernels. It also suppresses stochastic
residual detail most strongly on major floors. A fixed-relief cross-section
fixture verifies that downstream trunks grow wider, without treating one
terrestrial width-area exponent as universal.

A later calibration uses that continuous MFD signal directly as a small broad-
valley correction. Logarithmic MFD progression is strongly gated toward major
trunks and contributes only 4% beside the established D8 and smoothed shoulder
terms. Full flow-connected D8 shoulders and full replacement by MFD were both
rejected after synthetic and Tharkeniss measurements: the former preserved D8
gaps, while the latter worsened completed-surface drainage diagnostics.

The third refinement replaces a single contributing-area channel-head cutoff
with a bounded area-slope rule. Once-smoothed receiver slope adjusts the local
area threshold by `(reference slope / local slope)^2`, clamped between 0.35 and
4.0. This preserves the observed inverse direction between source area and
channel-head slope without allowing one steep range to erase major rivers from
gentle plains. Every initiated cell is traced downstream over the D8 tree, so
the selected network is connected by construction. The constants are
continent-relative heuristics, not climate or substrate calibration.
A small 0-8% logarithmic width/depth ramp begins at the minimum eligible source
area. The additional steep reaches therefore gain visible relief, while the
existing higher-area hierarchy still controls downstream trunk scale.

The next refinement reconstructs the generated floor after residual-detail
suppression and applies a bounded upstream-to-downstream inequality pass over
the selected D8 tree. A downstream centre cell is lowered only enough to retain
a 0.01 m drop. Total incision is limited to 60% of reconstructed local
elevation, and the pass may add no more than 2% of the generation ceiling. This
removes local generated barriers without globally filling the DEM or deciding
the status of lakes and basins. On the aligned Tharkeniss grid it reduces
terminal cells, basin candidates, and estimated fill volume; the 129-cell
summary can alias the narrower correction, confirming that regional builds
need their own buffered drainage diagnostics.

This is intentionally narrower than a landscape-evolution model. It does not
iterate uplift, erosion, sediment, or hillslope diffusion, and it fills every
unclassified depression only in the temporary routing surface. Authored
constraints are reapplied after incision and remain authoritative. Connecting
authored divides and rivers to generated catchments requires a later explicit
reconciliation stage with conflict diagnostics.

The next implemented measurement re-evaluates the completed pipeline on a
fixed 129-cell metric grid. Strict downhill D8 reports potential terminal cells
and direct coast connectivity. Priority-Flood runs on a copy to measure fill
cell count, depth, volume, outlets, and largest conditioned catchment. The
summary is diagnostic only: it neither changes the Float32 DEM nor decides
whether a depression is accidental, a lake, or an endorheic basin.

The first review layer groups 8-connected significant-fill cells into ranked
basin candidates. It records a deepest-cell location, coarse area, floor and
spill estimates, depth, volume, and terminal membership, then overlays the
largest candidates in the workbench. This is deliberately not a depression
hierarchy: connected fill regions can merge nested depressions. Barnes et al.'s
binary-tree hierarchy and Fill-Spill-Merge routing are the appropriate next
reference when nested topology or water storage becomes a concrete feature.

## Process-informed erosion and slope relaxation

The most useful scientific prototype is stream-power incision coupled with a
nonlinear or threshold-limited hillslope diffuser, not a visual particle or
"droplet" erosion filter.

Stream-power incision commonly relates erosion rate to drainage area and
channel slope. Nonlinear diffusion can make transport grow rapidly as slopes
approach a critical material slope. These are simplified landscape-evolution
models, not complete geology. They need:

- fixed stage identifiers, parameter units, and deterministic tie-breaking;
- a documented timestep schedule and stopping criterion;
- fixed coastline, water levels, and exact authored elevation anchors;
- before/after deltas and constraint residuals;
- timestep-halving and grid-refinement convergence tests; and
- an explicit failure mode rather than clipping unstable values into a
  plausible-looking image.

Landlab is the most practical Python 3.14 experiment adapter found. It offers
flow routing, stream-power components, and hillslope components under an MIT
license, with current CPython 3.14 wheels. It should remain optional until the
prototype proves that the behavior belongs in the tool's domain model.

Fastscape is not a current recommendation for this repository: its Python
front end is permissively licensed, but the required `fastscapelib` is GPL-3.0
and its published build configuration inspected for this note did not establish
CPython 3.14 wheels. Revisit it only if compatibility and distribution policy
become clear.

## Mountains, branches, and passes

Hierarchical ridges need explicit topology before procedural decoration:

- authored or generated branches name one parent segment and a deterministic
  branch identity;
- relief and width must not increase abruptly at a child-parent junction;
- junction angles, taper, and curvature are measured rather than selected only
  for visual appeal;
- anisotropic residual detail is correlated along and across each structure
  separately; and
- orphan relief blobs are a validation failure.

A pass is not merely a low point. Its constraint should include the parent
ridge and optional preferred crossing direction. Validation samples two axes:
elevation falls toward the pass along the crest and rises away from it across
the crest. Prominence and key-saddle relationships are derived diagnostics,
not replacements for authored pass semantics. Morse-Smale terrain analysis is
a useful reference for that later topology stage.

## Multiresolution determinism

The coordinate-addressed base and residual fields can remain bit-for-bit stable
at shared sample coordinates. Neighborhood solvers, drainage routing, and
erosion generally cannot promise the same property merely by adding points:
their operators, contributing catchment, and numerical trajectories change
with grid spacing.

Use two explicit contracts:

1. **Pointwise nested stages:** shared coordinates must be exactly identical.
2. **Process stages:** either run at a named canonical process resolution, or
   meet documented overlap, downsample, and convergence tolerances.

A regional process build needs parent boundary values and a measured halo. It
should generate the halo, crop only after processing, and compare the overlap
against the parent. Flow accumulation may require the complete upstream
catchment, not merely a geometric halo; a local build must therefore accept
inflow boundary data or declare accumulation incomplete.

Residual correction that forces each group of fine cells to reproduce its
parent mean is worth testing, but it is not automatically safe: changing local
heights after drainage can create new pits or reverse flow.

## Quantitative fixture suite

Each fixture stores authored inputs, algorithm/stage IDs, numeric outputs, and
measurements. Preview images remain useful review artifacts but are not the
only oracle.

| Fixture | Required measurements |
|---|---|
| Two peaks and a pass | Hard residuals; elevation decreases along the ridge into the pass and increases across it; prominence/key-saddle relation |
| Branching range | Connected child-parent topology; taper at junctions; crest continuity; absence of isolated blobs; branch length/angle/scale statistics |
| High valley | Relative incision against the reference terrain; monotone route to outlet except authored basins; drainage connectivity |
| Broad lowland valley | Shallow longitudinal grade; accumulation growth downstream; floodplain-width continuity; no unintended sink |
| Escarpment | Crest continuity; signed slope-asymmetry ratio; no diffusion through an authored breakline |
| Refinement window | Exact shared samples for pointwise stages; overlap and downsample error for process stages; seam gradient across crop edge |
| Rotation set | Plane, cone, and convergent hollow at several grid rotations; routed-area and direction error reveal grid bias |

Common gates are finite values, exact final enforcement of hard represented
samples, no inequality violation beyond documented Float32 tolerance, stable
output under input-object reordering, deterministic repeat builds, and a report
of clipped elevations. Candidate-specific accuracy thresholds should be set
from baseline measurements rather than invented before the harness exists.

## Tool and license findings

| Tool | Current finding on 2026-09-03 | Use in this project |
|---|---|---|
| SciPy 1.18.1 | BSD; Python 3.12+; CPython 3.14 Windows wheels | Direct prototype dependency for RBF and sparse solvers |
| Landlab 2.11.0 | MIT; Python 3.11+; CPython 3.14 wheels | Optional process-model comparison adapter |
| GRASS GIS 8.5 | GPL-2.0-or-later; cross-platform/Conda; new Python API is still stabilizing through 8.6 | External validation and hydrology comparison, not linked core code |
| Whitebox | Legacy `whitebox-tools` is MIT; active development moved to a next-generation product with licensed extensions | Optional CLI comparison only after pinning exact component and license |
| Fastscape / fastscapelib | BSD front end plus GPL-3.0 compiled dependency; CPython 3.14 support not established here | Defer |

License compatibility must be rechecked when a dependency is selected and
again before distribution. A command-line comparison tool is not equivalent to
copying or linking its code into the application.

## Prototype plan

### A. Measurement harness

Add the remaining fixtures and a machine-readable report. Capture constraint
residuals, slope/curvature distributions, hydrology statistics, stage timings,
and resolution comparisons. Freeze the current algorithm as the baseline.

### B. Surface-solver spike

Implement interchangeable experimental stages:

- local RBF correction using deterministic neighbor selection; and
- sparse screened-Poisson/biharmonic correction using an explicit tolerance,
  iteration limit, boundary condition, and convergence report.

Compare them at 65, 129, and 257 samples before choosing one. Do not expose a
public project-schema setting until the solver contract is accepted.

### C. Hydrology spike

Implement or adapt Priority-Flood depression discovery, preserve authored
basins, compare fill with least-cost breach, and measure D8/MFD routing on the
rotation fixtures. Export sinks, outlets, accumulation, and conditioning deltas
for inspection.

### D. Process spike

Run stream-power incision and nonlinear diffusion only on fixed fixtures.
Compare repeated builds, timestep halving, grid refinement, hard-constraint
reprojection, and before/after hydrology. Reject the stage if it produces
resolution-specific gullies or improves only the colour preview.

## Primary sources

- Hnaidi et al., [Feature Based Terrain Generation Using Diffusion Equation](https://doi.org/10.1111/j.1467-8659.2010.01806.x), 2010.
- SciPy, [`RBFInterpolator`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.RBFInterpolator.html)
  and [conjugate gradient solver](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.cg.html).
- Australian National University, [ANUDEM 5.3](https://fennerschool.anu.edu.au/research/products/anudem-version-5-3).
- Barnes et al., [Priority-Flood depression filling](https://arxiv.org/abs/1511.04463).
- Montgomery and Dietrich,
  [Source areas, drainage density, and channel initiation](https://doi.org/10.1029/WR025i008p01907)
  and [Channel initiation and landscape scale](https://doi.org/10.1126/science.255.5046.826).
- Orlandini et al.,
  [Prediction of channel heads in complex alpine terrain](https://doi.org/10.1029/2010WR009648).
- ANU Fenner School,
  [ANUDEM drainage enforcement](https://fennerschool.anu.edu.au/research/products/anudem-version-5-3).
- Zhang et al.,
  [Topographic hydro-conditioning with preserved depressions](https://pmc.ncbi.nlm.nih.gov/articles/PMC10434835/).
- Barnes et al., [Depression hierarchies](https://esurf.copernicus.org/articles/8/431/2020/)
  and [Fill-Spill-Merge](https://esurf.copernicus.org/articles/9/105/2021/).
- Génevaux et al., [Terrain Generation Using Procedural Models Based on Hydrology](https://doi.org/10.1145/2461912.2461996), 2013.
- Cordonnier et al., [Large Scale Terrain Generation from Tectonic Uplift and Fluvial Erosion](https://doi.org/10.1111/cgf.12820), 2016.
- Lague, [The stream power river incision model](https://doi.org/10.1002/esp.3462), 2014.
- GRASS GIS, [`r.watershed`](https://grass.osgeo.org/grass85/manuals/r.watershed.html),
  [`r.richdem.filldepressions`](https://grass.osgeo.org/grass-stable/manuals/addons/r.richdem.filldepressions.html),
  [8.5 release](https://grass.osgeo.org/news/2026_05_08_grass_8_5_0_released/),
  and [license](https://grass.osgeo.org/grass85/source/COPYING).
- Whitebox, [depression and storage analysis](https://www.whiteboxgeo.com/manuals/qgis/hydrology-depressions-storage.html),
  [legacy tools](https://github.com/jblindsay/whitebox-tools), and
  [next-generation repository](https://github.com/jblindsay/whitebox_next_gen).
- Landlab, [software paper](https://esurf.copernicus.org/articles/8/379/2020/),
  [PriorityFloodFlowRouter](https://landlab.readthedocs.io/en/latest/tutorials/flow_direction_and_accumulation/the_Flow_Director_Accumulator_PriorityFlood.html),
  [stream-power component](https://landlab.readthedocs.io/en/latest/generated/api/landlab.components.stream_power.stream_power.html),
  [timestep guidance](https://landlab.readthedocs.io/en/latest/user_guide/time_steps.html),
  and [nonlinear hillslope diffusion](https://landlab.readthedocs.io/en/latest/tutorials/hillslope_geomorphology/depth_dependent_taylor_diffuser/depth_dependent_taylor_diffuser.html).
- Prescott et al., [Flow-routing comparison](https://esurf.copernicus.org/articles/13/239/2025/), 2025.
- Salles, [eSCAPE landscape evolution model](https://gmd.copernicus.org/articles/12/4165/2019/), 2019.
- Huftier et al., [Terrain Synthesis and Authoring Based on Iso-Contours](https://onlinelibrary.wiley.com/doi/10.1111/cgf.70389), 2026.
- Grenier et al., [Controlled Procedural Terrain Generation Using Spatially Varying Patterns](https://onlinelibrary.wiley.com/doi/full/10.1111/cgf.14992), 2024.
- de Ferranti and Kirmse, [Global topographic prominence and key saddles](https://journals.sagepub.com/doi/10.1177/0309133317738163), 2017.
- Kummu et al., [Universal ridge network](https://doi.org/10.1093/comnet/cnz017), 2019.
- Package metadata for [SciPy](https://pypi.org/project/scipy/),
  [Landlab](https://pypi.org/project/landlab/),
  [Fastscape](https://github.com/fastscape-lem/fastscape/blob/main/pyproject.toml),
  and [fastscapelib](https://github.com/fastscape-lem/fastscapelib/blob/main/pyproject.toml).
