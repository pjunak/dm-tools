# Authored ocean-depth hypotheses — 2026-09-25

This implements the next bounded WC1 slice from the
[world-context plan](../strategy/world-context.md). It adds an inspectable ocean
floor from explicit margin assumptions while preserving authored geography.
It does not claim better land drainage, tectonic reconstruction or realistic
circulation. See the [user guide](../world-bathymetry.md) and
[ADR-0077](../adr/0077-generate-authored-ocean-depths.md).

## Research basis and chosen scope

The [earlier source review](2026-09-24-world-context-enrichment.md) establishes
that coastlines cannot uniquely determine seafloor history or depths. Two primary
references checked for this implementation reinforce the distinction between a
plausible scenario and measured bathymetry:

- [NOAA: What are abyssal plains?](https://oceanexplorer.noaa.gov/ocean-fact/what-are-abyssal-plains/)
  describes broad, relatively flat deep-ocean regions. That supports a simple
  basin plateau as a first modelling choice, not a universal calibrated depth
  or this particular mathematical profile.
- [GEBCO grid development](https://www.gebco.net/data-products/gridded-bathymetry-data/grid-development)
  distinguishes source measurements and predicted/interpolated contributions.
  Its products combine evidence unavailable for a fictional coastline. Our
  inference is to retain the scenario's assumptions and distinguish numerical
  approximation from geological uncertainty; this implementation does not
  reproduce GEBCO processing or import its Earth grid.

The selected C1 smoothstep shelf/slope model is a transparent engineering
prototype, not a published validated ocean-history model. Starting values are
explicit illustrative inputs. Plate reconstruction, seafloor-age cooling laws,
ridges/trenches and varying margin provinces require additional authored evidence
and remain follow-ups. No package, dataset or runtime dependency was added.

## Delivered

- Separate portable input v1: full retained-world identity, explicit sorted ocean
  IDs, physical shelf/slope widths, shelf/basin depths and grid resolution.
- Actual vector water-centre membership; dominant-ocean cells cannot assign depths
  to land or a different enclosed water body. Unsampled selections remain visible.
- Bounded negative ocean-floor samples using conservative spherical shore distance.
  A separate outward-rounded field covers distance-sampling and Float32 error only.
- Independent owned editor with water selection, form inputs, three generated
  views, numeric hover, pan/zoom, background jobs and cancellation. Stale previews
  remain visible but cannot export until regenerated. Tiny areas display `<1 km²`.
- Atomic input saves, external-change/unsaved-close guards, verified result reopening,
  CLI commands and current schemas. Completed bundles retain their entire geographic
  dependency; input snapshots never become automatic save destinations.
- Current-format results retain producer identity for inspection. Generation
  refreshes geography when its producer or requested resolution differs. Completion
  is published last and cannot overwrite an existing output directory.

## Numerical and workflow evidence

Focused bathymetry controls: **56 passed**. An analytic hemisphere coastline checks the
conservative depth envelope, spherical radius, both longitude edges, near-pole
samples and three source scales/origins. Profile controls check endpoints,
monotonicity, C1 joins and bounds. Split-cell fixtures place land and a separate
inland water centre inside a dominant-ocean cell. A selected tiny water region with
no samples remains NaN and is explicitly reported. Inputs/context stay immutable.

File/application controls exercise canonical input identity, current schemas,
invalid/bool settings, duplicate JSON fields, external edits, bounded NPY headers,
rehashed numeric/metadata corruption, nested geographic corruption, wrong preview
dimensions, older producers, CLI paths, cancellation and incomplete publication.
Five real Tk integration tests cover prerequisites, source/context isolation,
layer rendering, stale export rejection, save/reopen, input snapshots, invalid
forms, close/save guards, selection freeze and cancellation retaining previous work.

Visible owned-app checks inspected the private nine-continent world at 1320 × 850
and 1050 × 760, plus the World entry controls and support layer. Input fields,
buttons, legends and status remained readable. The authored world and SVG hashes
were unchanged; no native map document or campaign canon was edited. Screenshots,
measurements and the explicitly labelled illustrative result stay in the private
campaign workspace, outside Git.

Final repository gates: `python -m pytest -q` — **1,606 passed, 1 expected skip**
in **505.06 s** after the coverage correction. The skip requires the isolated scientific reference environment;
this batch changes no reference solver. `python -m ruff check .` and strict
`python -m pyright` pass. The documentation audit finds **184 documents**,
**1,302 valid local file links** and **10 current JSON schemas**, with no missing,
duplicate or extra inventory entries. `git diff --check` passes.

The documented 90-row public recipe exposed an existing context roundtrip defect:
161 geometrically dry cells had coverage between `1 − 4.44e-16` and `1 − 1.11e-16`,
no water ID, and mixed-water flags. The reader correctly rejected the inconsistency.
Generation now sets exact full-land coverage, no water ID and no support flags
when the clipped wet geometry has zero area. It does not apply a fraction epsilon
that could erase genuine small water features. New tests exercise both geographic
and bathymetric reopening at the recipe's authored resolution. **155 focused
context/bathymetry tests pass**, and the actual example CLI generates and inspects
12,397 ocean samples successfully. The runtime fingerprint records this correction;
no schema/algorithm family or legacy acceptance rule was added.

## Performance observations

Single wall-clock observations on Windows / CPython 3.14.7, private retained world
with nine continents, 185 source shapes and 48 connected water regions. The largest
water body was selected. No timing assertions or worst-case guarantees are inferred.
Source parsing precedes these timings; native peak memory was not measured.
These observations preceded the final zero-area dry-cell correction. A fresh
corrected current-producer private result was subsequently regenerated, reopened
and inspected; it retained the same 51,045 selected centre samples. The private
audit records the separate timing and final-result runtime fingerprints.

| Grid (columns × rows) | Geography generation | Bathymetry with matching current geography | Selected samples | Three bathymetry arrays |
|---|---:|---:|---:|---:|
| 360 × 180 | 10.93 s | 1.21 s | 51,045 | 777,600 bytes |
| 720 × 360 (maximum) | 48.97 s | 3.62 s | 204,125 | 3,110,400 bytes |

Normal-grid export took **0.45 s**; reopening and verifying the complete dependency
and result took **12.24 s** in a separate observation. These costs include source
water geometry work; the numeric depth formula alone is not the bottleneck. The
three-array byte counts exclude geography, temporary geometry and UI memory.
The implementation performs generation and verification off the Tk event loop.

## Limits and next implementation

The default margin is schematic, and all selected oceans share one profile. The
conservative distance bound creates a shallow strip near shore; changing resolution
changes centre samples. The error field cannot validate chosen geology. Fractional
coverage/support survives, but a coarse ocean depth is not a cell-average, volume,
sill or physical transport capacity. Even unflagged geographic cells may not
resolve a narrow authored shelf. No new land-terrain-quality claim is made.

Next retain individual water pieces and their continuous face incidence before
using gateway widths as solver edges. Require dry-barrier, seam/pole, symmetry and
resource controls; no heat/water flux should be added without conservation budgets.
Per-margin scenarios and area/depth integration should follow concrete consumers.
Then return to B/C physical valley/path and landform acceptance for WC2 rough land,
with LE2/LE3 authoring/resolution gates before production evolution. Climate/runoff,
world parents and same-present regional histories retain their separate WC gates.
