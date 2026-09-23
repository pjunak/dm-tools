# Shared-edge terrain detail - 2026-09-23

The opt-in local-detail experiment now connects additions across parent cells
using terrain-slope weights. It retains the verified prepared reference, exact
parent nodes, fixed cell moments and protected context. It is still experimental:
grid direction and protected gaps remain visible, coarse spectral leakage is
not eliminated, and neither automatic zoom jobs nor finer hydrology is enabled.
The global generator remains `coastline-constraint-terrain@17`.

## Research and formula

The old cell-interior basis pinned every edge to zero, creating isolated stamps.
The replacement gives each global edge a shared two-mode signal. Let
`b(t) = sin(pi*t)^4`, with `t` in [0,1]:

```text
q_odd(t)  = (sqrt(6)/2) * (6/5)^(5/2) * b(t) * sin(2*pi*t)
q_even(t) = b(t) * (2 + 3*cos(2*pi*t))
h(t)      = 10*t^3 - 15*t^4 + 6*t^5
edge(t)   = c_odd*q_odd(t) + c_even*q_even(t)
```

Both modes are bounded by one. The odd mode integrates to zero by symmetry;
for the even mode, `integral(b)=3/8` and `integral(b*cos(2*pi*t))=-1/4`, giving
zero integral. The even term removes the old forced midpoint zero. Each pair of
SHA-256-derived coefficients lies in [-0.5,0.5], with keys binding stage seed,
edge axis and integer address. Normalization is fixed, never output-dependent.

The quintic transition has zero first and second derivatives at its endpoints.
This interpolation choice follows the primary discussion in Ken Perlin's
[GPU Gems chapter, section 5.4](https://developer.nvidia.com/gpugems/gpugems/part-i-natural-effects/chapter-5-implementing-improved-perlin-noise).
The edge modes and parent-preservation construction here are project-specific;
that source supports the interpolation choice, not terrain realism or hydrology.
No dependency was added.

Each cell blends left/right signals using `h(u)`, and top/bottom signals using
`h(v)`, then multiplies the sum by 2/3. Every term has zero tangential integral.
The residual is C2 across shared edges in real arithmetic; the unchanged parent
field and a Float32 raster do not acquire that guarantee merely by adding it.

Fixed 17-by-17 parent probes provide central-difference slope energies Ex/Ey
in physical kilometres. The x preference is `0.25 + 0.5*Ex/(Ex+Ey)`; flat cells
use 0.5. A horizontal edge uses the averaged adjacent x preference and a vertical
edge its complement. Each edge uses the smaller adjacent amplitude budget, still
capped by half the observed height margin and the requested budget. An axis is a
convex blend and its weight is at most 3/4; the final 2/3 bounds the sum by the
cell's own amplitude. These bounds concern the addition, not unobserved extrema
of the parent. Delivered height-bound violations still fail without clipping.

The first candidate used a cubic blend and a squared-sine bubble. It connected
the cells but raised the finest edge-secant error to 0.174-0.237 m/km and residual
coarse power to 2.75-4.11%. The adopted quintic/fourth-power version addresses
those measured problems. Neither candidate replaces the original parent field.

## Paired public evidence

```powershell
.\.venv\Scripts\python.exe -m benchmarks.local_detail --seed 42 7 2026 --output artifacts/shared-edge-detail-20260923.json
```

The same runner captured the old formula before runtime edits, under
`artifacts/detail-support-20260923-before.json`. It builds real completed parents
from `example`, `regional` and `water`, each at 65 longest-side nodes with two
parent detail bands and a 40 m addition budget. Each fixed window covers eight
parent cells per axis, approximately 500 by 499 km. No window was moved to favor
the candidate. Refinements 8/16/32 yield 65/129/257 nodes: 27 paired windows.

All paired reference-ground, mask, water and basin-ID arrays match exactly.
Parent nodes, common-density coordinates, overlaps, revisits and fixed moments
are unchanged across requested densities. Dedicated tests additionally cover
partial-cell requests, cache pressure, authored contexts and the actual delivered
refinement-16 moments. The largest fixed Float32 mean drift is 0.000012875 m.

The table describes finest-density output. Edge RMS excludes original parent
nodes; interior RMS excludes parent-cell edges. The slope diagnostic is the
maximum change to the two-sided normal secant jump after adding detail, computed
from the delivered Float32 fields in m/km. It is not a claim about all parent
slopes or all possible locations.

| Case / seed | Edge/interior RMS, new | Maximum added edge secant jump, old -> new (m/km) | Residual coarse-power share, old -> new |
|---|---:|---:|---:|
| example / 42 | 0.784 | 0.077155 -> 0.004259 | 1.092% -> 2.454% |
| example / 7 | 0.800 | 0.082063 -> 0.005000 | 1.267% -> 1.754% |
| example / 2026 | 0.782 | 0.090750 -> 0.004563 | 1.866% -> 2.054% |
| regional / 42 | 0.803 | 0.093375 -> 0.004500 | 1.926% -> 2.286% |
| regional / 7 | 0.805 | 0.108531 -> 0.005500 | 0.974% -> 2.104% |
| regional / 2026 | 0.802 | 0.090750 -> 0.005625 | 1.917% -> 1.577% |

Old edge RMS was identically zero. The new ratio shows that detail crosses the
cell grid; it alone is not a realism score. The new maximum secant error falls
from 0.134-0.192 m/km at refinement 8 to 0.004259-0.005625 at refinement 32.
Compared with the old finest result it is approximately 94-95% lower. Float32
rounding eventually limits finite-difference convergence.

For spectral diagnostics, drop the duplicate final endpoints, remove the mean,
apply a separable Hann taper and take a 2D FFT. Coarse modes have radial frequency
at most 0.5 cycles per parent interval, excluding DC. Record both the fraction
of residual power there and the change to reference-ground coarse power. This
finite-crop diagnostic has taper/leakage effects and is not an exact restriction
operator. The largest absolute relative change in ground coarse power is 0.1211%.
Preserved cell means do not guarantee preserved coarse spectral power.

All three fixed water windows are completely protected: zero additions, zero
moment drift and no residual spectral fraction. They prove protection, not detail
quality. Other tests select eligible water-context windows to exercise additions.

## Visual review and boundary implications

Inspected baseline and new `regional-42/detail-32/comparison.png` products.
The terrain/diagonal inherited valley remain in place. The difference panel
changes from isolated cell stamps to connected patches, but horizontal/vertical
shapes and broad empty protection regions remain apparent. This is an incremental
support improvement, not cartographic acceptance or a completed terrain model.

The new outer-crop additions reach 7.68-11.28 m in these whole-cell windows.
Only original nodes and protected interfaces are pinned; an intermediate point
on a parent-cell edge is no longer guaranteed to equal the unenriched parent.
Neighboring results from the same detail field meet exactly. A separate transition
policy is required before displaying an enriched patch over an unenriched parent.

## Work, memory and provenance

These 64-cell output windows now prepare a 100-cell support rectangle. The existing
4096-cell limit includes the new halo, before allocation. A formerly fitting
window may require smaller bounds. Scalar cache records add a direction weight;
halo-only moments are computed when first delivered. The temporary Float32 probe
bank is at most 4.52 MiB, included in admission, and released before delivery.

Single serial sampling observations varied: the six nonzero cold windows took
38.3-163.7 ms after the change versus 25.1-43.1 ms before; finest cached-support
sampling took 144.8-459.1 ms versus 131.7-229.7 ms. These are not isolated timing
trials or proof of a speedup. Shared-edge preparation does more cold work; future
profiling should separate that cost from scheduling noise and field sampling.

A fresh-process million-sample check used:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.regional_memory --parent artifacts/shared-edge-detail-20260923/regional-42/parent --refine 128 --mode detail --output artifacts/shared-edge-memory-20260923.json
```

Its 1025-by-1025 core plus halo completed with a 168.9 MiB cold resident peak and
169.3 MiB process peak after a cached write. The retained estimate was 109.4 MiB;
cold-job allowance 295.9 MiB; peak aggregate reservation 405.3 MiB. Cold and cached
artifact bytes match. Closing released every reservation. These observations do
not bound unrelated editor work, arbitrary geometry or OS resident memory.

Runtime: CPython 3.14.7, NumPy 2.5.2, Pillow 12.3.0, Shapely 2.1.2 on Windows AMD64.
The reports contain full runtime, input, parent, runner and product hashes.

| Evidence | SHA-256 |
|---|---|
| Baseline package source | `f17c890aaff063fd736dde28f66aee387b827220598b8e822c8075ffbdd75885` |
| New package source | `202410c9e8dda1f66baed313da4381c810db39756743236d6fddf0bbd7b7ec82` |
| Baseline report | `cab06049de04a659d6de453b25d6fac6cefc488aaa5361c577bbacefe73ed16c` |
| New report | `b50557ad62f6726eb53c0de7f34d83d8a4c38bf6daf79faa51a705681f19e2a9` |
| New memory report | `71c6ee92b969a64c19ed603765ee4156c73abc0d8ad40d74f7a01f633c559ea7` |

## Remaining work

[TODO](../../TODO.md) retains R34 and the larger parent/child acceptance gate:

1. Replace remaining axis preference with oblique terrain-character support and
   measure spectral/visual behavior across more seeds and physical cell sizes.
2. Set explicit slope and coarse-power tolerances, including small physical
   parent cells where a fixed metre budget can create excessive local slopes.
3. Define a view transition for both whole-cell and arbitrary crop boundaries;
   do not splice this residual directly into the unenriched parent.
4. Establish inherited inflow/outlet paths and fine routing before small rivers;
   conservative protected corridors do not supply a fine hydrological solver.
5. Validate partial coast/basin support and stronger unseen-extrema bounds.

No private Aethelara source or generated parent was modified. The old runtime
formula was removed. The [ADR](../adr/0068-share-terrain-detail-across-edges.md)
and [public guide](../terrain-parent-regions.md) define the current experiment.

## Validation

Focused numerical/cache/admission/CLI/schema checks passed 145 tests. The final
repository suite passed 1,233 tests in 382.86 s; Ruff and strict Pyright passed
with zero errors/warnings. All 846 local Markdown file targets resolve (fragment
anchors are not covered by that check). The package source and both benchmark
helper hashes still match the report, and all 108 recorded comparison-product
hashes were rechecked. No GUI behavior changed or manual GUI acceptance was claimed.
