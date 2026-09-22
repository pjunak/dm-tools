# Generate a region from a verified parent

Two commands now consume completed terrain builds. `sample-parent` samples the
parent's unchanged prepared field more densely. `enrich-region --experimental`
adds a small, protected residual to that field. Each writes a separate result;
neither changes the parent or any authored input. Workbench zoom jobs are still
planned. Small rivers remain unavailable until finer hydrology is implemented.

## Quick public example

The [local-detail project](../examples/terrain/local-detail.dmterrain.json) uses
the existing public coastline and landform instructions with a small 65-node
longest-side parent and two detail bands. From the repository root, choose new
output directories:

```powershell
.\.venv\Scripts\python.exe -m dmtools terrain build examples/terrain/local-detail.dmterrain.json --output artifacts/detail-parent
.\.venv\Scripts\python.exe -m dmtools terrain sample-parent artifacts/detail-parent --output artifacts/parent-window --bounds-km 1375 800 1875 1300 --refine 16
.\.venv\Scripts\python.exe -m dmtools terrain enrich-region artifacts/detail-parent --output artifacts/detail-window --bounds-km 1375 800 1875 1300 --refine 16 --amplitude-m 40 --experimental
```

Open `artifacts/detail-window/comparison.png`: left is the verified reference,
middle is experimental ground, and right is the actual added height in metres
(blue lowers, red raises). The reference and detailed panels use the same height
scale; the difference panel uses the largest absolute change in this result.
`scientific.png` contains only the detailed ground. Nothing is loaded into the
workbench automatically.

Use `--amplitude-m` in (0, 100]; the default is 12 m. This is an upper residual
budget, not a calibrated geological parameter. Parent settings and their noise
bands are unchanged. Broad cell protections can produce a region with no added
heights; check `detail.evidence.changed_samples` in its manifest. The explicit
experimental flag is required because this formula has not passed visual,
spectral or hydrological acceptance.

## Verified parent contract

Only [current build v17](../schemas/terrain/build-v17.schema.json) from the exact
current source/runtime is accepted. Rebuild after changing installed source or
dependencies. Old builds have no compatibility loader.

The loader checks completion, manifest identity, all required product names,
sizes and hashes, runtime, algorithms, settings and coordinates. Numeric headers,
dtypes and shapes are checked before allocation; object arrays are forbidden.
The [typed input snapshot](../schemas/terrain/input-snapshot-v1.schema.json)
contains full coastline geometry, explicitly typed constraints, settings and
saved authoring controls. Original project/SVG files need not remain available.
Their hashes remain provenance; the snapshot does not pretend to recreate their
original file bytes.

Preparation reconstructs the full input-defined field, then checks **every**
delivered Float32 ground, land, water and basin-ID sample. It also checks the
canonical axes, land mask, source/final heights, receivers, channels, accumulation
and incision budgets actually reused by the operation. A mismatch rejects the
parent. Read-only owned arrays retain this prepared reference across API calls.
This is reconstruction and verified replay, not a serialized Python cache.

File hashes are checked again before publication, as is runtime identity. Existing
destinations and outputs inside the parent directory are rejected. A failure may
leave partial output files but no completed manifest. A parent-region artifact
cannot itself be used as a parent build: recursive enrichment is not implemented.

## Sampling, budgets and outputs

Bounds use the parent's original local kilometres, x right and y down. No world
projection is introduced. Requests round outward to globally anchored fine-grid
nodes and include one halo cell. The existing [regional request rules](terrain-regional-sampling.md)
apply: power-of-two refinement and at most 2,000,000 delivered nodes including
halo. Experimental detail requires refinement at least 8 and at most 4,096
parent cells intersecting the buffered window. Original parent nodes are exact.

Each eligible cell uses a fixed 17 by 17 probe lattice, independently of output
resolution. Thus preparation adds at most 1,183,744 probes. The pointwise output
uses batches of at most 65,536. Full-parent replay and complete-source geometry,
constraints and routing still cost work outside the window; these limits do not
claim a hard total-memory/time bound for arbitrary input geometry.

| Product | Content |
|---|---|
| `samples.npz` | Buffered ground/mask, axes, sampled water and basin IDs; detail mode also includes reference ground, actual added heights, addressed cell budgets and fixed reference/detailed moments |
| `inputs.json` | Portable typed parent inputs, unchanged |
| `scientific.png` | Ground shaded with the halo, then cropped to the requested core |
| `comparison.png` | Reference/detail/added-height comparison, experimental mode only |
| `manifest.json` | Parent identities and replay counts, request/grids, runtime, stage seed, detail evidence, capability limits, file hashes and completion identity |

Load NPZ with `allow_pickle=False`. `core_slice.rows` and `.columns` contain
exclusive-stop Python slices. Ground is Float32 metres and NaN off land. Added
heights are zero off land. `cell_columns`/`cell_rows` address the original parent
cells; protected cells have zero amplitude and NaN moments because no probes
were needed. Some otherwise eligible cells can also have zero amplitude when
the observed terrain reaches its height bounds.

The [parent-region v1 schema](../schemas/terrain/parent-region-v1.schema.json)
explicitly distinguishes `reference-samples` from `experimental-detail`.
Completion means the described experiment finished; it does not mean the detail
is accepted for cartography. `refines_hydrology` and `small_rivers_ready` are
always false. The parent's existing diagnostic routing is not upgraded to rivers.

## Experimental preservation rule

The existing prepared field is retained everywhere; there is no bilinear
replacement of its interior structure. Only a new additive residual is generated.
Coefficients depend on the named `terrain.local-detail` seed and global parent
cell addresses. Smooth cell basis functions have zero analytic added mean and
zero value/first derivative at cell edges. The fixed trapezoidal reference moments
are computed from the prepared field, not inferred from four sparse corner heights.
Float32 storage introduces small measured moment errors.

Whole cells touching authored point/line cores, basin footprints or buffered
planned channel edges are protected. Cells near the coastline are also excluded.
This conservatively keeps authored heights, sampled lake ground and inherited
planned channel corridors unchanged, including between original nodes. These
protections are fixed against the full source, not recomputed from a cropped
catchment.

Amplitude uses half the smallest observed distance from zero/the elevation
representable Float32 ceiling on the fixed probes, capped by the requested budget. Those probes do
not certify unseen extrema: if a delivered point exceeds a bound, the request
fails instead of clipping and changing its moments. Parent-cell edges retain
the reference value at every density; boundaries of arbitrary partial-cell
windows must be blended/displayed with another result of the same detail field,
not assumed to meet an unenriched parent there.

The regular cell support is visible in difference images. Terrain-aware support,
coarse spectral-power acceptance, derivative checks on the final quantized field,
partial coastal/basin detail, inherited outlet paths and upstream flow, finer
routing, cache budgets, cancellation and workbench requests remain open. Read
[ADR-0061](adr/0061-verify-parents-and-isolate-local-detail.md), the
[measurements](research/2026-09-23-verified-parent-detail.md) and [TODO](../TODO.md).

Python callers can reuse `prepare_verified_parent(...)` and its regional sampler,
then `prepare_regional_detail(...)` across windows. File loading belongs to
`load_terrain_parent(...)`; `sample_parent_region(...)` owns completion checks
and publication. A cached caller must retain and verify the corresponding parent
and runtime identities before publishing any result.
