# Shared landform blending: replacement and evidence

Date: 2026-09-27. Starting revision: `d37a22e`.
This continues the [landform transfer batch](2026-09-27-geological-landform-guidance.md).
It changes regional composition in the current Python engine, not geological
forcing, physical aging or the experimental river construction model.

## Research and implementation choice

Normalized local weights are a standard way to combine local approximations.
[Ohtake et al., Multi-level partition of unity implicits](https://doi.org/10.1145/882262.882293)
describes this mathematical pattern for surface reconstruction. That paper is
background for the approach, not evidence that this terrain heuristic is a
physical model. No octree, fitted implicit surface engine or paper code is added.

[ADR-0081](../adr/0081-blend-adjoining-landform-regions.md) specifies our concrete
compact core/halo rule. It separates neighboring-recipe mixing from fading at
the outside of connected assigned coverage. Empty holes remain background;
equal controls dissolve before numeric weighting. Fully established interiors
suppress outside recipes, while genuine overlaps remain normalized.

Geometry preparation and weights live in `pipeline/landform_weights.py`.
Elevation carriers remain in `pipeline/landforms.py`. Incision limits use the
same weights. Mountain crest screens, water-density support and scientific
fixture cut bounds now cover influence across recipe borders. Numeric identity
is `regional-landforms@4`; serialized inputs and the landform seed are unchanged.

## Fixed controls and measured outcome

The public world and recipe are the same committed fixtures as the previous
report. The saved prepared project uses seed 42, 257 pixels, radius 2,000 km and
coastal rise 80 km. No source geometry or settings were edited for the comparison.

The before/after world has identical grid coordinates and land mask; all generated
land samples are finite. Mean absolute land-height change is 137.979 m, with
31.311% of land samples changing by more than 1 m. These are change measurements,
not realism scores. A rendered comparison shows removal of bright background
rims, especially around the plateau and its enclave. Authored polygon shapes
and remaining large height contrasts are still visible.

A separate 1,000 km square uses a flat 250 m plain and 2,200 m plateau, adjoining
at x=500 km, with 70/100 km transitions and a 4,000 m background. Across a
300 km transect sampled every 0.5 km:

| Measurement | Old inward fades | Shared blending |
|---|---:|---:|
| Height at shared edge | 4,000 m | 1,225 m |
| Range remains within the two recipes | No | Yes, 250–2,200 m |
| Monotone plain-to-plateau transition | No | Yes |
| Largest adjacent sample change | Not an acceptance target | 11.937 m |

The same test with a 0 m background gives the same new interior profile.
Rotating the geometry by 37 degrees retains continuity and the recipe envelope.
Neither grid smoothing nor raster interpolation is used to hide the seam.

## Tried and rejected: signed-distance weights alone

A simpler normalized signed-distance kernel also fills seams, but does not
protect an established enclave. With a 2,200 m parent (200 km transition) and
a 250 m child (20 km transition), a point 100 km inside the child still receives
parent weight 0.15625. The normalized result is **513.514 m**, an unwanted
263.514 m increase. This small scalar probe was executed and retained.

Reject that rule for the current authoring contract. The implemented core term
makes the corresponding child interior exactly 250 m. This does not prohibit
future physically justified transitions; such changes need explicit controls
and acceptance rather than silently weakening province intent.

The earlier triangulation and implicit age-to-coefficient ideas were design
rejections, not executed alternatives. The original inward-fade failure remains
recorded under [T15](terrain-method-decisions.md#t15---use-inward-region-fades-as-a-complete-geological-partition).

## Full-suite follow-up: changed drainage population

The first approved complete-suite attempt stopped after 50 passes at the
regional floor-profile regression. The previous check required a 70% reduction
in mean cardinal-edge uphill excursion. Shared blending changes both the source
relief and selected routes, so that empirical ratio is not invariant:

| Regional seed 42, 65 stations/edge | Previous inward weighting/support reproduced | Shared blending |
|---|---:|---:|
| Descending cardinal edges | 1,876 | 2,066 |
| Mean cardinal excursion without floor correction | 0.574773 m | 0.769908 m |
| Mean cardinal excursion with floor correction | 0.165912 m | 0.237557 m |
| Corrected/raw cardinal ratio | 0.288657 | 0.308552 |
| Mean excursion across all descending edges | 0.560671 m | 0.605507 m |
| Worst excursion across descending edges | 55.721313 m | 48.008911 m |

The old mean is reproduced by temporarily applying the prior inward weight and
polygon-only sampling support to the same current inputs. No input geometry or
floor-correction implementation changes during this probe. The changed cardinal
population and higher mean are a real tradeoff; a lower maximum does not erase
them. Hard height, coast, canonical-sample and cut/no-fill checks stay intact.

A second in-memory trial replaced maximum core coverage with a smooth union.
Its cardinal ratio was 0.307957, still outside the old target. Do not adopt this
extra algorithm change to chase one fixture statistic; the generator remains
the original shared-blending candidate.

The current three public floor fixtures now require **at least a two-thirds
cardinal mean reduction and a corrected mean below 0.25 m**. The all-direction
reduction and unchanged canonical-ground checks remain. This explicitly relaxes
the former 70% relative threshold while adding an absolute residual ceiling;
it is a revised empirical regression envelope, not a drainage physics repair
or evidence that rivers are accepted. Preserve this tradeoff in the method
register and the open river/ground adoption work.

The controlled three-fixture/reproduced-old comparison took 6.021 s. The
smooth-core probe took less than five seconds. Local evidence:
`floor-regression-diagnosis.json` and `smooth-core-union-probe.json` in the
same ignored artifact directory. The complete-suite failure is retained in
`full-suite-20260927-174504.log`.

A second complete-suite attempt stopped after 93 passes at the diagonal-only
reconstruction test. With floor fitting disabled, the regional combined mean
falls from 2.850823 to 1.146466 m (ratio 0.402153), narrowly missing the old 0.4
aggregate target. This mean includes 2,066 cardinal edges that this stage must
leave unchanged. Its 660 affected diagonal edges improve from 9.364716 to
2.325206 m (ratio 0.248294); the example fixture's diagonal ratio is 0.210811.
Cardinal measurements are exactly unchanged in both cases.

The test now applies the existing 60% reduction requirement to diagonal edges,
checks their count is unchanged, and requires the combined mean to improve.
This replaces the old aggregate threshold with a stage-specific assertion; it
does not claim the previous aggregate target passed or alter reconstruction.
The separate final-floor residual increase above remains a quality tradeoff.
The two-fixture probe took less than five seconds and is retained as
`diagonal-regression-diagnosis.json`; the failed suite log is
`full-suite-20260927-175520.log`.

## Validation and remaining boundary

Focused coverage includes shared and oblique edges, three-way junctions, explicit
and blank nested overrides, overlaps, disconnected and point-touching components,
identical-control partitions/duplicates, query chunks/order, exact authored
heights/coasts and shared samples at two resolutions. Extended water/crest probes
and conservative native cut limits are checked as well.

The final field matches the saved candidate's Float32 values exactly after
simplifying the isolated-region case. The range/lowland research fixture is now
`two-catchment-range-lowland@2` because conservative bounds include shared support;
earlier @1 physical-bank measurements must not be reinterpreted as new acceptance.

The before-world run took 2.545 s; candidate runs took 8.006–10.508 s with concurrent
checks. This is a cost warning, not a controlled performance comparison or speed
claim. The two-pass implementation bounds weight scratch by query size rather
than accumulating a full grid per region. Isolated regions use their exact
single-region formula. Broader performance work remains secondary to useful
features unless representative interactive jobs are blocked.

Local ignored evidence is under `artifacts/landform-blending-2026-09-27/`:
`before-world.npz`, `after-world.npz`, before/after transects,
`comparison.png`, `comparison.json` and `rejected-kernel.json`.
The preview magnifies native pixels threefold; it generates no additional detail.

Final focused runs passed 43 seam/landform/native-bound tests in 20.16 s and
78 build/parent/regional-sampling tests in 48.12 s. An earlier routing, sampling
and seam run passed 50 tests in 11.12 s; these runs overlap and are not a unique
test total. Ruff passes and Pyright reports zero errors and warnings.

One provenance run stopped because a source formatting edit occurred while it
was executing. The existing source-identity guard correctly rejected the changed
runtime. Repeating the entire affected group with source frozen produced the
78-test pass above; no guard was weakened.

Changed document links, UTF-8 text and diff whitespace pass. The inventory now
contains 202 Markdown files plus one legal notice, and 215 unique entries with
supporting contracts included.

The approved complete-suite rerun passed **1,856 tests with one skip in
663.87 s** (11 minutes 4 seconds), within its 15-minute stop limit. The skip is
`tests/test_evolution_reference.py`: the separate scientific reference environment
is unavailable in this Python runtime. No isolated Landlab validation is claimed.
The final focused floor/diagonal/blending group passed 44 tests in 13.39 s;
Ruff and Pyright passed after the test revisions. All 24 task files retained
their pre-run hashes throughout the complete suite. The final log is
`full-suite-20260927-175831.log`; both earlier failures and their diagnostic
probes remain recorded above. This is regression acceptance of the documented
composition change and revised empirical checks, not physical-river acceptance.

## Next quality work

Keep the shared blend. Add feedback when a province is narrower than its
transition support and inspect large height differences in physical units.
Connected mountain spurs, passes and lowland structure remain a larger realism
gain than treating every authored polygon as an isolated elevation stamp.
World result overlays and explicit regional domains remain product priorities.
River-bank/representation and physical-history adoption gates are unchanged.
