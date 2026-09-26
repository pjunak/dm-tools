# Preserve terrain features through delivery

Measured 2026-09-27 against `8f1bb0a`, with unchanged tracked Python and the
existing NumPy/SciPy environment. This follows the
[cell-safe delivery comparison](2026-09-27-cell-safe-terrain-delivery.md).
These are short exploratory probes, not an adopted product representation or a
new supported benchmark command. Normal generation remains unchanged.

## Decision

Prioritize preserving prepared valley geometry through saving, reopening and
height queries before spending more solver time fitting it back into the same
world-aligned bilinear cells. A river-aligned positive control avoids defects
that survive comparable height accuracy on the world grid. A separate roundtrip
preserves the existing local field and its measured quality; converting it to
bilinear raster delivery loses that quality again.

This supports a representation experiment, not a claim that a new terrain engine
is finished. The current authoritative generated product remains the Float32
DEM. Adopting a richer numeric surface would require an explicit architecture
decision, build identity, schema and consumer changes. Do not quietly make a
rendered river overlay authoritative or call a failed raster accepted.

The user's test-duration constraint now applies: consult before a test expected
to take a longer time. Use roughly two minutes as the working threshold, and
consult sooner for uncertain or potentially expensive runs. Give an estimate,
purpose and stop condition before starting; silence is not approval. The two
completed probes below took 0.855 s and 20.625 s internally. No full regression
suite or long simulation was launched in this batch.

## 1. Separate elevation error from valley shape

Use a 4 x 4 km domain, 250 m world-grid spacing and an off-grid valley centre
`(2037, 2091) m`. For tangent `t` at angle theta and perpendicular normal `n`, let
`s = (position - centre) dot t` and `v = (position - centre) dot n`. Define:

```text
h(s, v) = 1000 - 0.01 s + 0.00004 v^2  [metres].
```

This has a 1% downstream grade and banks 10 m above the bed at 500 m offset.
At each angle, test both banks of 17 stations from -1,000 to 1,000 m along the
bed. Each bank-to-bed profile has 202 samples and the existing 1 cm cumulative
inward-rise tolerance: 34 profiles per angle, 238 in total.

Compare world-grid bilinear interpolation, quadratic tensor-product interpolation
of the same Float32 world-grid samples, and bilinear interpolation in a
river-aligned strip whose `v = 0` row explicitly contains the bed. The strip uses
11 by 7 nodes at 250 m spacing over `s = [-1250,1250]`, `v = [-750,750]`.
The world grid has 17 by 17 nodes and different coverage. This is a mechanism
control, not equal-cost compression evidence.

| Angle | World bilinear failures / 34 | Worst inward rise | Quadratic failures | River-aligned bilinear failures |
|---|---:|---:|---:|---:|
| 0 degrees | 17 | 0.243591 m | 0 | 0 |
| 15 degrees | 16 | 0.271179 m | 0 | 0 |
| 30 degrees | 16 | 0.179077 m | 0 | 0 |
| 45 degrees | 17 | 0.147217 m | 0 | 0 |
| 60 degrees | 15 | 0.208801 m | 0 | 0 |
| 75 degrees | 16 | 0.265930 m | 0 | 0 |
| 90 degrees | 17 | 0.256409 m | 0 | 0 |

Maximum absolute height errors are 0.625010 m for world bilinear, 0.625005 m
for river-aligned bilinear and 0.0000648 m for quadratic. The two bilinear
representations have nearly the same worst height error but different bank
behavior: 114 versus zero failed profiles. Alignment and retaining the bed
matter independently of a scalar elevation-error score. Straight, analytic
valleys do not establish behavior at bends, junctions or protected terrain.

A small linear feasibility probe also tests two bed stations inside one 250 m
cell. Four unknown corner heights are bounded to [-100,100] m. Both sides of
both stations require a nonpositive inward derivative throughout their segment,
at least 0.05 m endpoint drop, and 0.3 m downstream bed fall. Because a bilinear
field restricted to a straight segment is quadratic, derivative inequalities at
both endpoints cover the whole segment. HiGHS reports infeasible at 0, 15, 30,
60, 75 and 90 degrees, and feasible at 45 degrees, with a one-second solver limit.
This bounded numerical witness agrees with the
[limited bilinear-cell argument](2026-09-25-valley-bank-feasibility.md); it does
not prove the full 575-section fit infeasible or exclude approximate valleys,
grid-edge beds or a different basis. Use local feasibility checks before larger
fits, rather than treating more penalties as a guaranteed fix.

## 2. Reject generic smoothing as the network solution

Use the admitted automatic network and head/mouth field from the prior 250 m
comparison. Sample either its curvature-bounded delivered nodes or its local
field at the same nodes. Fit `RectBivariateSpline` with degree two or three and
`s=0`, then return Float32 queries. The
[official SciPy reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.RectBivariateSpline.html)
defines these interpolation parameters; it gives no terrain or hard-bound guarantee.
All 575 physical sections and the common 125 m routing check are unchanged.

A third candidate adds a compact correction at each hard height, using
`delta * max(1 - distance^2 / 500^2, 0)^2`, and clips queried heights between
`max(source - cap, 0)` and `source`. This restores the sampled hard/bound gates
on this fixture but not its drainage. It is not an interior proof for arbitrary
spline reconstruction.

| Nodal input | Reconstruction | Dense failures / 575 | Worst rise | Captured heads | Sinks |
|---|---|---:|---:|---:|---:|
| Delivered | Existing bilinear control | 238 | 0.315582 m | 4/4 | 0 |
| Delivered | Quadratic | 25 | 5.194931 m | 0/4 | 4 |
| Delivered | Cubic | 43 | 8.220612 m | 2/4 | 2 |
| Delivered | Quadratic with bounded pin corrections | 25 | 5.194931 m | 2/4 | 4 |
| Local-node samples | Quadratic | 26 | 5.192871 m | 0/4 | 4 |
| Local-node samples | Cubic | 40 | 4.684525 m | 2/4 | 2 |
| Local-node samples | Quadratic with bounded pin corrections | 26 | 5.192871 m | 2/4 | 4 |

Unbounded splines also violate hard heights, protected terrain, no-fill and cut
limits. The delivered-node quadratic displaces one hard height by 111.583 m;
the cubic by 129.997 m. Pin correction returns both hard-height residuals to
zero, but all corrected candidates still fail guide, bank, endpoint, capture
and sink gates. Fewer failed sections do not offset larger rises or lost outlets.
These generic spline substitutions are rejected; the analytic success above
cannot be promoted to a full-network result.

## 3. Keep the prepared field instead of reconstructing it from heights

A trusted-data prototype writes the already prepared `ValleyPatches` parameters
and its source/cap arrays to compressed numeric NPZ files. It stores segment and
bed data, anchor corrections, mouth geometry, head transitions, hard targets,
settings, metric grid and protected bounds; network coordinates and receivers
are also retained. JSON metadata is encoded as a byte array. Loading uses
`allow_pickle=False` and reconstructs the field directly from the saved values,
without rerunning placement or valley preparation.

After the archive closes, compare all dense bank profiles, all reported quality
metrics and the common-grid Float32 heights with the original field. They match
exactly. The tests use the original fixture and bank-support network as their
independent comparison inputs; a complete reopened network/project workflow is
not implemented. Stored source arrays are generated fixture data, not an imported
private map or modified authored project.

| Background spacing / orientation | Archive size | Reopened dense failures / 575 | Captured heads | Sinks | Failures after bilinear delivery |
|---|---:|---:|---:|---:|---:|
| 1,000 m | 10,091 bytes | 0 | 4/4 | 0 | 267 |
| 500 m | 16,430 bytes | 0 | 4/4 | 0 | 251 |
| 250 m | 42,612 bytes | 0 | 4/4 | 0 | 238 |
| 250 m, quarter turn | 42,682 bytes | 0 | 4/4 | 0 | 238 |

Maximum dense inward excursion remains 0.006195 m, below the unchanged 1 cm
threshold. Existing sampled hard-height, divide, cap, no-fill, guide, endpoint
and composition-volume gates pass. Routing still means raw D8 on a common 125 m
sample grid with the existing 1,000 m outlet tolerance, not exact streamline
tracing. These four cases share the same physical fixture; they are not four
independent landscapes or arbitrary-angle acceptance.

The archive is deliberately only a trusted-data experiment. It has no public
schema, hostile/corrupt-input limits, supported reader, immutable ownership
contract, spatial index or tile cache. Compression size is fixture-specific.
Roundtrip equality preserves existing quality; it does not improve the local
terrain or establish whole-cell correctness, physical erosion or world-scale cost.
The bilinear failures return when those features are reduced to heights alone.

## Existing approaches worth carrying forward

- **Continuous river patches:** the abstract of
  [Genevaux et al. (2013), Terrain Generation Using Procedural Models Based on Hydrology](https://doi.org/10.1145/2461912.2461996)
  describes a continuous construction from a river graph and blended/carved
  patches. This supports retaining feature geometry as a research direction.
  The abstract was retrievable in this pass; the full PDF was not reopened.
  Earlier project research already discusses it. This prototype is not an
  implementation or validation of that paper's complete method.
- **Feature-conforming triangles:**
  [CGAL's constrained triangulation reference](https://doc.cgal.org/latest/Triangulation_2/index.html)
  describes preserving supplied polylines as triangulation edges. A locally
  constrained mesh is a fallback if analytic patches cannot meet join and query
  requirements. Geometry predicates, interpolation, bounds, licensing and
  Python/Windows packaging would need separate evaluation; no CGAL dependency
  was installed or adopted.
- **Separate process resolution from retained topography:**
  [Yamazaki et al. (2011)](https://doi.org/10.1029/2010WR009726) use subgrid
  topographic parameters for river/floodplain storage and water levels. The
  [versioned HydroMT-SFINCS example](https://deltares.github.io/hydromt_sfincs/v1.0.3/_examples/build_from_script.html)
  likewise retains finer elevation/roughness information in subgrid tables.
  These are useful precedents for preserving information below a process grid,
  not ready-made terrain generators. No hydrodynamic engine, conservation claim
  or justification for accepting a failed terrain surface follows from them.

## Revised implementation order and stop conditions

1. **Formalize the smallest feature roundtrip in the existing benchmark.**
   Store numeric prepared fields, geometry, roles, units, immutable parent/model
   identity and integrity hashes. Add strict size/shape/dtype/finite-value guards
   and deterministic ordering. Reopen the network and field independently, then
   repeat the original quality checks. Reject incomplete or inconsistent data.
   This is generated terrain data, not post-generation editing or a general
   plugin/solver framework.
2. **Test the query boundary before adopting it.** Require arbitrary query-order
   and batch-size agreement, same-coordinate repeatability, adjacent-tile/halo
   agreement, physical bounds and explicit unsupported-domain behavior. Retain
   source/hard-input authority and the fixed/native rejected control. A new
   interpolator cannot inherit the bilinear envelope proof. Compare analytic
   patches with river-aligned strips or constrained triangles only where an
   observed failure or measured cost requires that alternative.
3. **Expand quality and local-detail evidence.** Add held-out bends/junctions,
   oblique landscapes, irregular coasts, short tributaries and near-hard-target
   cases, then tile seams and parent/downsample checks. Keep narrow features and
   flow connectivity in retained data even when overview rendering hides small
   rivers. Fine terrain must still pass actual-ground tests; coarse invisible
   feature metadata is not accepted fine topography. No visual-only bypass.
4. **Decide product authority explicitly.** If the richer representation passes,
   record an ADR and replace the relevant build/schema/consumer contracts together.
   Consider Float32 rasters as declared-resolution exports or caches only after
   that decision. Keep hashes linking derivatives to the accepted numeric source;
   avoid maintaining two conflicting authorities or legacy readers. No backend
   language rewrite is required for this experiment.
5. **Resume coupled generation after construction/delivery acceptance.** Connect
   the accepted surface to B2's history reference, then LE3/WC2 and local enrichment.
   Keep groundwater, lateral erosion and sediment as separate mechanism trials
   with their own budgets. Do not use them to explain away interpolation defects.

Pause a candidate that breaks hard inputs, loses outlets, creates sinks or fails
its bound/quality gates. Record its actual result and reason before trying the
next representation. Keep local bilinear feasibility as a small diagnostic;
defer the previously proposed full least-change bank solve until a chosen cell
layout can represent its requirements. Do not increase cut budgets, relax the
1 cm threshold or uniformly refine the world to conceal failures.

## Evidence and validation boundary

Local ignored artifacts:

- `artifacts/representation-probe-aligned-20260927.py` and its `.json`: analytic
  angles, single-cell feasibility and six network spline comparisons; 0.855 s.
- `artifacts/feature-surface-probe-20260927.py` and the matching directory's four
  NPZ archives plus `result.json`: trusted-field roundtrip; 20.625 s.

These are one-off local probes, not committed executable coverage. Reproduction
from a fresh checkout requires formalizing step 1; existing supported comparison
commands remain in the [benchmark guide](../../benchmarks/evolution/README.md).
The formulas, parameters and acceptance limits above make the method reviewable.
The source baseline is `8f1bb0a`; CPython 3.14.7, NumPy 2.5.2 and SciPy 1.18.1.
Benchmark source SHA-256:
`26784d38ef1c622c0a7658b15db0f89db32dbf8a9a7df7f0090a50d4a922512f`.
Runtime package-source SHA-256:
`609434a82e7be0ecef9be7e91b81986e61750b036f2873282d33693b3f0a9bda`.

| Local evidence file | SHA-256 |
|---|---|
| Representation script | `6a54dfe91ea023ca931078c00a208fa3ac5dc4d1c26fd5c4c9f45474fbe8b739` |
| Representation result | `58427cff4fad69b57e70ed958ea671c745f62ca32755108d0d2be112edca708e` |
| Roundtrip script | `56089b46f60d7db240578670db0479e141f3507ca3749bc34ac3bc7a720309f8` |
| Roundtrip result | `23a3135fb4385114c0d67ab70855d707d0e2b7505f13475e2fe4d4017b137b33` |

All stored numeric array hashes and archive hashes were checked against their
saved results, and both result identities match the unchanged repository code.
This batch changes documentation only. Validation passed for 728 local links and
anchors across 11 changed Markdown files, the complete inventory of 195 Markdown
files plus one legal notice, and whitespace. It does not rerun the previous
ten-minute Python suite. Public reader safety, general-angle
network acceptance, tile/LOD behavior and end-user visual quality remain untested.
