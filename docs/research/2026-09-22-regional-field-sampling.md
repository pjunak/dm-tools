# Bounded regional field sampling — 2026-09-22

This implementation adds denser sampling of a requested window while preserving
the unchanged full-source terrain field. It is a measurable foundation for local
generation, with explicit limits on its scope; see
[ADR-0058](../adr/0058-sample-bounded-regional-windows.md).

## Experiment

Measured on the local Windows Python 3.14 environment against the working
implementation based on `658c419`. The ignored result at
`artifacts/regional-sampling-2026-09-22/measurements.json` records complete runtime,
input and harness identities. Reproduce from the repository root after creating
a fresh artifacts directory:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.regional --output artifacts/regional-measurements.json
```

The four public/synthetic fixtures use seed 42 and a 65-longest-side reference
grid. A centered 16-by-16-reference-interval window is refined by 4, 8 and 16,
giving 65, 129 and 257 core nodes per axis. One halo cell on each side gives
4,489, 17,161 and 67,081 evaluated samples. Timings are medians of three window
evaluations after one full-source preparation. The full finer-field comparison
uses one timed evaluation at refinement 16 through the same sampler. Timing
excludes file export, previews, imports and full-build water/drainage review;
these are sampling measurements, not end-to-end build speedups.

| Fixture | Preparation, s | 65 core, ms | 129 core, ms | 257 core, ms | Full finer samples, s | Full sample count |
|---|---:|---:|---:|---:|---:|---:|
| regional | 0.628 | 15.4 | 49.4 | 196.3 | 1.436 | 624,225 |
| authored | 0.552 | 7.9 | 28.0 | 110.3 | 1.713 | 1,050,625 |
| water | 0.350 | 15.4 | 48.9 | 203.2 | 2.014 | 624,225 |
| archipelago | 0.697 | 19.3 | 79.7 | 275.3 | 2.842 | 1,050,625 |

The largest local windows use about 89–94% fewer nodes than the complete finer
field. Preparation is still global (about 0.35–0.70 s here); reusing the prepared
sampler across windows avoids repeating it. No broad latency guarantee follows
from four fixtures or a single full-field comparison per fixture.

## Correctness and delivery

All 65/129/257 nested core comparisons were exact for Float32 ground, land masks,
water surfaces and complete-source basin IDs. Repeat visits in reverse level
order retained exact numeric hashes. The largest windows, including their halos,
matched the corresponding full-field samples exactly.

Regression tests additionally compare against `generate_terrain` on square,
regional, water, archipelago and authored fixtures; verify overlap and different
batch boundaries; enforce precision and halo budgets before expensive work;
and prevent allocating an entire refined-world axis for a small window.
The saved-project CLI reproduces identical artifacts, checks source/runtime
changes, preserves inputs and existing output directories, and never labels a
failed export complete. The public command in the usage guide was run and its
scientific preview inspected.

Validation: 912 repository tests passed; Ruff and Pyright passed. All 637 local
Markdown links resolved. The public regional CLI preview was checked at roughly
1.3 km spacing against its 5.2 km reference grid.

## Remaining work

This samples the same field. It does not resolve R34's band-amplitude issue,
condition on a finished parent DEM, increase the canonical routing resolution,
or create finer rivers. Halo samples provide neighboring ground values, without
proving parent restriction or boundary-slope properties after adding detail.
Local lake levels are unreviewed numeric samples, and the ground-only preview
avoids inventing cropped-pool visibility identities.

Next, specify the immutable parent result and restriction/tolerance contract,
prototype additive detail that preserves broad terrain, then add inherited-flow
local hydrology. Wire zoom jobs and smaller-river display only when their
resolution and consistency evidence is available. The
[active plan](../../TODO.md) keeps these steps separate.

Measured generator source SHA-256: `e4d9e05d9b410cb86d94b48f6d42ad0e75d234e7ef8f3d75fcf55c0a7a37f831`.
