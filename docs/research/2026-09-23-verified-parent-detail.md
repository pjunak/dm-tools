# Verified parent replay and experimental local detail

Date: 2026-09-23. The saved-parent contract and commands are implemented.
The residual formula remains experimental and has not passed cartographic,
coarse spectral-power or finer hydrology acceptance. This report concerns
local public fixtures; no private Aethelara source was changed.

## What changed

Build v17 stores full effective inputs with explicit constraint types and a
portable snapshot schema. A consumer verifies completion, every product hash,
exact runtime/source identity, frame and algorithms, then replays every delivered
Float32 ground/water/mask/ID value and reused canonical routing field. Original
project/SVG files need not remain at their former paths.

`sample-parent` exposes denser unchanged samples of this reference.
`enrich-region --experimental` adds separate protected detail and publishes
reference/detail/difference images, numeric residuals, fixed cell moments and
explicitly false hydrology/small-river readiness. The parent remains unchanged.
The global terrain generator remains `coastline-constraint-terrain@17`.

This addresses three defects in the rejected
[bilinear experiment](2026-09-23-parent-cell-preservation.md): the original
prepared interior field is retained, only new residuals are conditioned, and
support/preparation no longer depends on requested sampling density. It does
not rehabilitate that previous projection.

## Residual and reference moments

For local cell coordinates u,v in [0,1], let `b(t) = sin(pi*t)^2`. The added field
is a weighted sum of:

- `b(u)*b(v)*sin(2*pi*u)`;
- `b(u)*b(v)*sin(2*pi*v)`;
- `b(u)*b(v)*sin(4*pi*u)*sin(4*pi*v)`.

Each term has an odd factor about the cell midpoint and therefore zero analytic
cell integral. Values and first derivatives vanish at cell boundaries. Explicit
zeroing at exact boundaries avoids relying on a floating-point `sin(pi)` zero.
Three SHA-256-derived coefficients in [-1/3,1/3] bind the named local-detail seed
and integer parent cell addresses. Their absolute sum bounds the residual by
the requested amplitude before Float32 storage.

A fixed 17-by-17 lattice samples the retained Float32 reference in each eligible
cell. Half the smallest observed height margin to zero/the representable Float32
ceiling limits its amplitude. Fixed trapezoidal reference/child means are evidence,
not a claim that four parent corners define the same cell average. The numeric
regressions compare these records with actual delivered refinement-16 samples.
A ceiling regression covers 1234.56 m, whose valid stored value is
1234.56005859375 m; comparisons respect authoritative Float32 rounding.

Whole cells intersecting point/line authoring cores, buffered basins/planned
channels or the coastal margin receive no additions. Unseen height extrema are
not certified: an out-of-bounds delivered sample aborts instead of being clipped.

## Public-project measurements

```powershell
.\.venv\Scripts\python.exe -m benchmarks.local_detail --case example regional water --seed 42 7 --output artifacts/verified-parent-detail-2026-09-23.json
```

The runner creates real completed parents from the existing public projects at
65 longest-side nodes and two detail bands, with seeds 42/7 and a 40 m residual
budget. Each parent has 2,535 delivered nodes and 39,064 canonical routing nodes.
Every node is replayed. Each fixed geographic window covers eight by eight
parent intervals: 500 km by approximately 498.995 km. Refinement 8/16/32 produces
65/129/257 core nodes per axis. No window was moved to maximize added detail.

There are 18 density results. Shared samples across densities, original parent
nodes, overlaps, revisits and sampled water match exactly. Fixed reference/detail
moments remain identical across densities. The table reports the finest window;
active/protected counts refer to its 64 parent cells.

| Project | Seed | Active / protected cells | Largest added height (m) | Largest fixed mean error (micrometres) | 257 x 257 generation (ms) |
|---|---:|---:|---:|---:|---:|
| example | 42 | 26 / 38 | 20.709229 | 7.153 | 171.9 |
| example | 7 | 40 / 24 | 21.531006 | 9.060 | 178.4 |
| regional | 42 | 27 / 37 | 20.709229 | 6.676 | 204.1 |
| regional | 7 | 39 / 25 | 21.531006 | 6.676 | 257.4 |
| water | 42 | 0 / 64 | 0.000000 | 0.000 | 217.2 |
| water | 7 | 0 / 64 | 0.000000 | 0.000 | 207.3 |

Both water windows lie wholly inside protected footprints: all 66,049 finest
samples retain their reference ground and water. A completed experimental request
can therefore add no detail. Separate numerical tests select eligible windows on
four public/synthetic cases, including authored/water contexts, to avoid treating
this zero result as the only preservation evidence.

Stage observations were collected serially in one process, after building each
parent. File loading/hash checks took 0.147-0.185 s; full prepared-field
replay took 0.470-0.994 s; protection preparation took
0.023-0.057 s. Child publication including image/NPZ output and
repeated verification took 0.023-0.059 s. These are small-fixture
observations with warm filesystem effects, not fresh-process speedup evidence
or a performance guarantee for large authored maps. The cost separation supports
reusing verified context in a future viewport workflow; no production cache or
cancellation policy is implemented yet.

Runtime: Python 3.14.7, NumPy 2.5.2,
Shapely 2.1.2. Package source SHA-256:
`d47eb203a47d0efdaad0fe7435be41e3bf99e38aea5d39ff4c4e67c7ef1589fa`.
The ignored JSON also records runtime/dependency versions, benchmark source hash,
project/parent/artifact identities and output hashes. Its sibling directory
contains six parents and 18 separate numeric/image comparison artifacts.

## Validation

The final repository gate passed 1,064 tests in 276.84 s, Ruff and strict
Pyright (zero errors/warnings). The 56 focused parent/detail regressions include
the Float32 ceiling and fixed-moment checks. All 723 local Markdown links across
136 files resolve. The three commands in the public trial guide were also run
successfully into fresh ignored directories; their runtime identity matches the
measured source above. No GUI job or finer hydrology workflow was claimed or tested.

## Visual inspection and acceptance

Inspected the regional seed-42 reference/detail/difference comparison at 257
samples. Reference terrain and its diagonal valley remain visible in place;
the addition is small relative to broad relief. The difference panel exposes
regular cell-scale patches and large protected gaps. These geometric stamps
are an expected weakness of the current basis and prevent calling it a finished
terrain-character model. Passing moments and overlaps does not establish realism.

Tests also check exact parent edges, arbitrary request overlaps/halos, different
point batches, repeat order, analytical basis moments and vanishing boundary
secants, water/height/channel protection, bounded work and rejected bound
violations. Parent I/O tests cover current schemas, source-file independence,
corrupted/missing/oversized products, forged hashes with wrong numeric values,
runtime/frame mismatches, exclusive output paths and failures before completion.

Remaining gates, recorded in [TODO](../../TODO.md):

1. Replace regular cell support with terrain-aware structure and measure coarse
   spectral power and final Float32 boundary slopes. An arbitrary crop edge is
   not automatically a zero-residual boundary to the original parent.
2. Compose conservative full-field bounds or retain explicit unresolved cases;
   a fixed probe lattice cannot certify every hidden extremum.
3. Inherit upstream inflow and outlet paths, refine routing and validate local
   water/tributaries before small-river readiness. Protecting existing planned
   corridors does not supply a fine catchment solver.
4. Add bounded prepared-cell/result caches, invalidation, cancellation and
   workbench requests. Do not replay a complete parent for every pointer move.

Use the [public trial guide](../terrain-parent-regions.md) and
[ADR-0061](../adr/0061-verify-parents-and-isolate-local-detail.md) for the executable
contract. This is generated regional output, not manual post-generation editing.
