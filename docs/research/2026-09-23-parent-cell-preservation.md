# Parent-cell preservation experiment - 2026-09-23

The cell-average projection is implemented and measured, but **rejected for
runtime adoption**. Exact coarse nodes and almost exact cell averages coexist
with altered authored heights, visible grid structure, density-dependent values
and worse inherited channel profiles. The generator, editor and public schemas
are unchanged. This does not enable zoom enrichment or finer rivers.

This follows [fixed detail-band amplitudes](2026-09-22-stable-detail-band-amplitudes.md)
and the [bounded regional sampler](2026-09-22-regional-field-sampling.md).
[TODO](../../TODO.md) retains the open parent/child and R34 work.

## Reproduction and scope

The executable experiment lives in
[`benchmarks/parent_cells.py`](../../benchmarks/parent_cells.py) and
[`benchmarks/parent_detail.py`](../../benchmarks/parent_detail.py). Run from the
repository root, using a fresh output file and an existing parent directory:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.parent_detail --case regional authored water --seed 42 7 --save-grids --output artifacts/parent-cell-results.json
```

`--save-grids` creates a fresh sibling directory named after the JSON stem,
containing numeric NPZ grids and ground-only PNG comparisons. Outputs are ignored,
not source-controlled. The report is marked complete only after every case and a
final source/runtime identity check succeed. It records public input, prepared
field, parent snapshot, implementation and output hashes.

The measured run used the product source at `5639ad2`, CPython 3.14.7, NumPy 2.5.2
and Windows 11 AMD64. Runtime and benchmark source hashes are retained in the
local `artifacts/parent-cells-2026-09-23/results.json`. The recorded package source
SHA-256 is `724ceb88d091a794b7507413612b02e4a99d0f0158cf9c3dfd9ea359d4f5f691`.
These are measurements of that source/runtime, not a cross-platform identity claim.

Each of three public fixtures uses seeds 42 and 7. A globally prepared two-band
field supplies an immutable in-memory 5x5 Float32 parent snapshot. A proposal adds
two bands while retaining that parent's prepared constraint profiles and canonical
routing. This is not an independently rebuilt four-band whole map. Four-by-four
whole-cell interior windows are subdivided into 65x65, 129x129 and 257x257 nodes,
roughly 3.9, 1.95 and 0.98 km apart. Same-density overlaps and repeated visit order
are checked independently.

The parent is not loaded from a verified completed build. All supplied cells are
finite land; partial coastal cells, nodata, shoreline crossings and external
inflow transfers are outside this kernel. The water fixture probes a lake interior.
No private map or live editor acceptance is included.

## Candidate and restriction

The explicit research restriction is `endpoint-bilinear-trapezoid@1`: reconstruct
the parent bilinearly and average each child cell using trapezoidal quadrature of
its node elevations. The parent target is the mean of its four corners. This is
neither a pixel average nor a sediment or hydrological volume budget.

For parent reconstruction B, finer proposal P and local cell coordinates u,v:

```text
b(t) = 16 t^2 (1-t)^2
w(u,v) = b(u) b(v)
c = sum(w * (P-B)) / sum(w)
D = w * ((P-B)-c)
child = Float32(B + alpha * D)
```

Because w vanishes on the cell boundary, D has zero trapezoidal cell mean before
rounding. One common alpha in [0,1] attenuates a whole cell enough to keep ground
between zero and the representable elevation ceiling. Individual node clipping
would break the zero-mean property. Alpha may be zero: preserving a completely
flat parent at the minimum or maximum elevation can require discarding all detail.

The kernel checks exact parent nodes and finite/bounded output. It allows measured
cell-mean rounding error of at most `2 * eps_float32 * max(1, ceiling_m)`. Inputs
remain unchanged; returned arrays are owned and read-only. Refinement is restricted
to powers of two from 4 through 64 and the existing two-million-sample budget.

The bubble has zero value and derivative on its continuous boundary, but the
actual delivered surface is a Float32 raster. Its finite secant slopes need not
vanish, and the bilinear parent already has cell-edge gradient changes. This
candidate does not establish first-derivative continuity.

## Numerical preservation and the reference mismatch

All 18 public case/density combinations preserved every parent node exactly,
agreed across same-density overlaps/repeats, and retained bilinear cell edges
exactly. The largest delivered cell-mean error was 0.000007868 m. All public
cells retained alpha=1; separate numerical tests exercise attenuation and alpha=0.

However, the unchanged prepared parent field itself disagrees with the chosen
bilinear means. The table shows maximum absolute cell-mean differences at the
257x257 density and shared-coordinate drift between successive child densities:

| Fixture/seed | Unchanged parent field vs bilinear mean (m) | Proposal vs bilinear mean (m) | Child drift 65 to 129 (m) | Child drift 129 to 257 (m) |
|---|---:|---:|---:|---:|
| regional / 42 | 322.108488 | 341.395239 | 0.197998 | 0.022705 |
| regional / 7 | 95.707703 | 140.409203 | 0.077637 | 0.014404 |
| authored / 42 | 40.781999 | 49.568876 | 0.033569 | 0.003174 |
| authored / 7 | 31.019732 | 35.955345 | 0.070190 | 0.026611 |
| water / 42 | 0.970621 | 1.968227 | 0.000183 | 0.000031 |
| water / 7 | 0.970621 | 2.155394 | 0.000183 | 0.000031 |

This is a reference-definition conflict: four sparse corner samples do not
preserve the shaped terrain between them. Forcing a child toward that bilinear
reference changes existing structure before considering new detail. It would be
incorrect to treat all correction to those means as removal of added detail.

The proposal itself is exact at shared coordinates across these densities. The
conditioned child is not: its weighted correction c is recomputed from each
requested raster. Complete-cell support solves crop/order dependence at a fixed
density, but does not solve density dependence. Smaller drift at the last tested
density does not prove a continuous or universally convergent field.

## Authored heights, channels and appearance

At the authored fixture's (2200 km, 1400 km) height point, both prepared parent and
proposal fields evaluate to exactly 1000 m. Sampling the finished 257x257 rasters
bilinearly gives:

| Seed | Proposal raster (m) | Bilinear parent (m) | Conditioned child (m) |
|---|---:|---:|---:|
| 42 | 1000.039551 | 1024.520630 | 1029.160767 |
| 7 | 999.963806 | 1020.314331 | 1024.297485 |

The roughly 24-29 m displacement is much larger than the proposal raster's
approximately 0.04 m interpolation difference. Coarse-node and cell-average
preservation therefore cannot stand in for authored-height preservation.

For channels, compare the same canonical directed edges whose two endpoints lie
inside the window, with 65 stations per edge. Each edge's uphill excursion is its
maximum rise above an earlier running minimum. The paired comparison uses the
actual parent field, not only the bilinear control:

| Fixture/seed | Matched interior edges | Edges worsening by more than 0.01 m | Largest individual increase (m) | Boundary-crossing edges, not evaluated |
|---|---:|---:|---:|---:|
| regional / 42 | 3 | 3 | 62.671875 | 2 |
| regional / 7 | 7 | 1 | 8.603516 | 1 |
| authored / 42 | 0 | 0 | n/a | 0 |
| authored / 7 | 16 | 4 | 31.157959 | 3 |
| water / 42 | 0 | 0 | n/a | 0 |
| water / 7 | 0 | 0 | n/a | 0 |

Eight of 26 sampled interior edges worsen. Retaining routing identities alone
does not preserve downhill ground. These tiny windows are not a whole-network
assessment, and cases with no matched edges supply no channel acceptance.

The selected lake-interior windows change no sampled wet/dry classifications.
That does not establish shoreline, water-level, lake-identity or outlet preservation.
Their nominal 250 m point already evaluates to 331.149811 m in the parent field;
it moves to 332.772034/332.906189 m in the conditioned rasters. The original
81.149811 m discrepancy predates this experiment. Its constraint interaction is
unresolved and is recorded under the existing hard-constraint TODO, rather than
misattributed entirely to enrichment.

Visual inspection of the regional/42 ground comparisons shows conspicuous 4x4
cell structure in both the bilinear and conditioned results. The latter adds
interior bulges while retaining grid creases. The unconditioned proposal preserves
a much smoother curved mountain flank. This is an additional rejection reason,
not a claim that the unconditioned proposal passes preservation or drainage gates.
The largest added boundary secant slope falls from 6.788 to 3.885 to 2.073 m/km
across the three densities, but is still nonzero at the finest grid.

Projection alone took 0.488-1.504 ms per 16-cell result in single measurements.
Global preparation, proposal sampling, profiles, export and complete-job memory
are separate costs. These small timings do not establish overall speed or scaling.

## Revised next implementation

1. Define an immutable parent reference that retains the prepared terrain
   structure as well as reproducing the authoritative parent DEM nodes. Bind its
   prepared context or reproducible reconstruction to verified build/input,
   algorithm and runtime identity. Do not silently make a live input field the
   authority for an unrelated completed map.
2. Measure and document the parent reference's own cell moments. Resolve their
   relationship to the parent raster and authored constraints explicitly. Retain
   the bilinear model as a diagnostic control, not the default enrichment base.
3. Condition only added residual structure. Protect accepted authored heights,
   lake surfaces and inherited channel floors. Diagnose parent constraint
   conflicts before attempting to preserve them or overwrite them with a child.
4. Make correction support and integration independent of requested output
   sampling density. Select a bounded reference quadrature or analytically
   constrained residual with explicit error tolerances and work budgets.
5. Repeat exact-node, parent-moment, 65/129/257, overlap/order, slope, authored,
   water and paired-channel checks before product integration. Measure coarse
   spectral power and rendering quality separately. Only then add finer routing,
   upstream/outlet transfer and the resolution gates for small cartographic rivers.

This rejects one reconstruction/conditioning combination. It does not reject
parent-conditioned generation or prove that a field-based alternative will pass.
The next reference/conditioning contract still requires its own measured decision;
[ADR-0048](../adr/0048-keep-zoom-driven-detail-generation.md) remains the product scope.

## Validation

The independent numerical tests integrate with NumPy's trapezoidal rule, exercise
extreme parents and bounded attenuation, validate overlap/order and input ownership,
and check the profile sampler against an analytic bilinear surface on nonuniform
axes. The six public fixture/seed runs completed at all three densities, with
numeric artifacts and visual comparisons retained locally. Final validation:

- 993 repository tests passed, including 51 new projection/profile tests.
- Ruff and Pyright passed without code or type findings.
- 672 local Markdown file links across 131 documents resolved.
- All four benchmark source hashes and all 24 recorded NPZ/PNG artifact hashes
  still matched the completed measurement after the code review.

These passes verify the experiment's behavior and measurements; the measured
product-quality failures above remain reasons to reject runtime adoption.
