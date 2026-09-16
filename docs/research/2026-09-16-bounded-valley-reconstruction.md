# Bounded valley reconstruction - 2026-09-16

Status: adopted generator improvement, [ADR-0050](../adr/0050-reconstruct-valleys-with-bounded-cubics.md).
The baseline is commit `e3d9cc0`, generator `coastline-constraint-terrain@8`,
automatic valleys `regional-budget-mfd-d8-valleys@6`. The new identities are
`coastline-constraint-terrain@9` and `regional-budget-mfd-d8-valleys@7`.
Project/build schemas and dependencies are unchanged. All inputs are public or
synthetic; no private world map is used as a fixture.

## Method and sources

Bilinear reconstruction of a fixed valley grid joins straight slopes at cell
edges. The replacement prepares bicubic Hermite patches sharing nodal first and
mixed derivatives. One shared scale per node limits its derivative contributions
so every Bezier control lies within that cell's four-corner range. All adjacent
cells participate in choosing the scale. The convex hull then bounds the patch
in exact arithmetic. Final local-range clipping handles numerical roundoff;
incision additionally obeys the unchanged bilinear cut ceiling. A binding
ceiling can retain a slope break. Exact vector retention still zeroes automatic
cutting and suppression inside authored basin footprints.

[SciPy's PCHIP documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.PchipInterpolator.html)
describes the one-dimensional harmonic-mean slope construction and continuous
first derivatives used as a starting point. Its cited
[Fritsch-Butland paper](https://doi.org/10.1137/0905021) is the original method;
only its metadata/abstract and the documentation were consulted here.
[MIT's Bezier-surface reference](https://web.mit.edu/hyperbook/Patrikalakis-Maekawa-Cho/node14.html)
provides the tensor-product and convex-hull properties. The joint 2D limiter is
our construction, not a claim that PCHIP independently proves 2D monotonicity.
No SciPy dependency was added. Bounding a patch's range does not forbid interior
extrema, establish physical erosion or certify an arbitrary downstream path.

## Crease and terrain measurements

Four fixtures (`example`, `regional`, `authored`, `outlet`), each with seeds 42
and 20260902, were generated before/after at a longest side of 1025 samples.
For each axis, probe every fourth interior canonical node (indices 4 through
`size-4`, exclusive at the upper end). Offset the other coordinate by 0.371 of
its canonical spacing to avoid measuring only node intersections. Keep land
probes and evaluate left/right slopes with `h = spacing * 1e-4` km; also use
`1e-3` as a step-size control. Combine the two axes by sample-count-weighted RMS.
The metric is `abs((f(p+h)-f(p))/h - (f(p)-f(p-h))/h)`.
Use the prepared Float64 field here to avoid a Float32 quantization floor.
This samples grid seams, not overall slope smoothness or terrain realism.

RMS slope mismatch at the finer probe step, in m/km:

| Case / seed | Incision before | Incision after | Complete field before | Complete field after |
|---|---:|---:|---:|---:|
| example / 42 | 1.5283 | 0.00047 | 2.2479 | 0.00115 |
| example / 20260902 | 1.4962 | 0.04880 | 2.7145 | 0.04888 |
| regional / 42 | 1.4573 | 0.00045 | 1.6546 | 0.00098 |
| regional / 20260902 | 1.6277 | 0.18657 | 2.0409 | 0.18663 |
| authored / 42 | 1.5956 | 0.19695 | 2.2894 | 0.17663 |
| authored / 20260902 | 1.5415 | 0.04368 | 2.3524 | 0.04198 |
| outlet / 42 | 0.8863 | 0.00027 | 1.2649 | 0.56917 |
| outlet / 20260902 | 0.8877 | 0.00027 | 1.4012 | 0.60595 |

Incision seam mismatch falls by 87.7-99.97%; suppression by about 99.97%.
The larger residuals come from active cut ceilings or other field terms.
Whole-field reductions range from 55.0% to 99.95%; smoothing the two automatic
fields does not smooth all authored/retention boundaries. Reducing the probe
step tests local convergence, not a global curvature guarantee.

Across these eight 1025-sample results, height differences have RMS 1.30-3.15 m
and maximum absolute differences 46.06-78.73 m. Land masks, axes, incision,
suppression, cut limits, receivers, source heights, channels and finished
canonical heights are exactly equal. Canonical routing agreement/conflict
summaries are identical. This is a deliberate between-node field change, not an
output-preserving optimization. Shared-coordinate and nested-grid tests still
apply to the new algorithm.

Enlarged before/after relief views were inspected for the public coast and
regional fixture. The change softens interpolation transitions, but prominent
straight/diagonal D8 turns and local scalloping remain visible. The global
terrain composition is unchanged. Inspect with the workbench **Detail (1025 px)**
preset after regeneration; a 257-sample result uses the unchanged canonical nodes.
This does not add local detail when zooming.

## Check inside channel edges

A separate finite comparison uses the same prepared field and substitutes the
old bilinear samplers only as a research control. Evaluate the full field at 17
equally spaced stations on every selected channel-to-receiver edge, cast to
Float32, and retain edges whose endpoint drop exceeds 0.01 m. For each, measure
the maximum height above any earlier station's running minimum. Count excursions
over 0.01 m. The percentile includes zero-excursion edges.

| Case / seed | Descending edges | Uphill interiors before / after | 95th percentile excursion m before / after |
|---|---:|---:|---:|
| example / 42 | 1962 | 438 / 428 | 47.95 / 41.67 |
| example / 20260902 | 1906 | 454 / 453 | 58.13 / 54.29 |
| regional / 42 | 2281 | 455 / 425 | 22.98 / 19.23 |
| regional / 20260902 | 2275 | 522 / 514 | 29.30 / 27.04 |
| authored / 42 | 2030 | 774 / 752 | 79.06 / 75.63 |
| authored / 20260902 | 2426 | 761 / 730 | 65.45 / 62.82 |
| outlet / 42 | 1245 | 191 / 188 | 26.47 / 21.33 |
| outlet / 20260902 | 1130 | 188 / 188 | 53.07 / 48.84 |

Counts never increase across this matrix; the mean, 95th percentile and maximum
excursions decrease in each case. Individual edges are not guaranteed to improve.
There are still many sampled uphill interiors, with after-change maxima of
128.22-250.31 m. Canonical downhill endpoints therefore remain insufficient for
river validity. Seventeen stations do not certify the unsampled intervals.
[TODO](../../TODO.md) retains flow-aware geometry, full-path repair and conservative
complete-field bounds as separate work.

## Runtime and memory

Run the existing harness before/after without editing engine/benchmark source or
running heavy checks concurrently. Four cases, two seeds and two fresh-process
repeats give 16 runs per version. Before/after runs were sequential, not
alternated. This is a bounded cost check, not a speedup claim or a 4096-pixel test.
Windows 11 AMD64, CPython 3.14.7, NumPy 2.5.2, Shapely 2.1.2. Timings exclude
rendering/export; memory is process high-water through generation, including
imports. Median seconds and peak MiB:

| Case / seed | Before s | After s | Change | Peak MiB before / after |
|---|---:|---:|---:|---:|
| example / 42 | 0.960 | 0.988 | +2.9% | 95.1 / 102.1 |
| example / 20260902 | 0.948 | 0.994 | +4.9% | 94.9 / 102.2 |
| regional / 42 | 1.111 | 1.133 | +2.0% | 107.3 / 109.7 |
| regional / 20260902 | 1.126 | 1.148 | +2.0% | 107.6 / 109.9 |
| authored / 42 | 1.682 | 1.721 | +2.3% | 104.3 / 109.1 |
| authored / 20260902 | 1.859 | 1.750 | -5.9% | 104.3 / 108.9 |
| outlet / 42 | 2.906 | 2.733 | -6.0% | 114.5 / 116.9 |
| outlet / 20260902 | 2.774 | 2.739 | -1.3% | 114.0 / 116.8 |

The observed timing range is -6.0% to +4.9%, with 2.4-7.3 MiB extra peak memory.
Two repeats and sequential runs cannot distinguish every small difference from
host noise. No native rewrite or cache was introduced.

All repeated runs were deterministic and had identical input hashes. Only the
elevation hash changed among the retained numeric product hashes; routing,
water review evidence and basin-outflow summaries matched for these fixtures.
This does not promise unchanged water decisions on other off-grid geometry.
The existing full water regressions remain part of acceptance.

## Reproduction and validation

Use separate source checkouts for baseline `e3d9cc0` and the adopted version.
Run the installed development environment against each source with the same
fixture inputs; never mix modules from the two checkouts in a timed worker.
The performance command for each source is:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.terrain --case example regional authored outlet --resolution 513 --seed 42 20260902 --repeats 2 --output artifacts/reconstruction-performance.json
```

Use distinct, previously absent output paths. The report records installed-source
and benchmark fingerprints. This run's ignored evidence lives under
`artifacts/generation-interpolation-2026-09-16/`: `before.json`, `after.json`,
1025-sample before/after surfaces, `surface-comparison.json`,
`channel-profiles.json` and `valley-comparison.png`. These generated outputs are
not source fixtures. The seam/profile algorithms and parameters above describe
the independent numeric probes; no compatibility sampler is shipped at runtime.

`tests/test_terrain_reconstruction.py` covers exact knots, analytic fields,
nonuniform grids, dense local bounds, active ceilings, shared-edge slope
convergence, axis symmetry/reflection, input ownership, invalid queries and
pointwise chunk independence. Regional and retention integration checks cover
the prepared fields. Existing generation, routing, sampling, water and export
tests cover the surrounding contracts. Validation completed: 751 tests passed,
Ruff passed, strict Pyright reported no errors or warnings, and 528 local
Markdown file links resolved. The diff whitespace check also passed.

The next work is flow-aware between-node geometry and valid bounds for the
complete terrain. This local convex-hull limiter is not an outward-rounded
interval implementation and does not close the separate water-sampling research.
