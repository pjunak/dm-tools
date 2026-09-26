# Valley heads, mouths and matched bank evidence

Measured 2026-09-26 against baseline `c34aede` plus this implementation.
The previous [automatic layout](2026-09-26-hard-target-valley-layout.md) restored
250 m outlet capture but retained local bank defects. This batch fixes those
local defects on the same graph and isolates the remaining raster-delivery loss.
This is generated-hypothesis construction, not editing a completed map or
simulating geological time. Normal workbench generation remains unchanged.

## Decision and unchanged inputs

Retain `head-mouth-valley-sections@1` as a useful construction component.
All local fixture gates now pass, including an added dense bank check at the
unchanged 1 cm inward-rise tolerance. **Production remains rejected:** actual
Float32 raster banks fail at every tested spacing, and coarser capture fails.

The 32 x 24 km public fixture keeps its initial relief, admitted 32-node automatic
layout, four heads, two mouths, original 17 vertices/reach ownership, protected
divide and two hard off-grid heights. No geometry is moved or resubdivided here.
All 575 bank/bed pairs and 60,732.041 m of network length are matched between
control and candidate. The fresh 600 m cut ceiling, 120 km3 composition budget,
no-fill rule, zero coast and fixed/native controls remain unchanged. Independent
routing uses the same 125 m grid; no fill or imposed receivers is used.

The retained control is an experimental ablation, not legacy save support or a
second product path. The new boundary model explicitly rejects fixed-source
mode and sharp sections; those combinations have not been established.

## What failed and what changed

The previous 21 local inward failures consist of one head and 20 sections on
two terminal reaches. The head's generated bed is 146.592 m, but the local legal
floor is 189.882 m. Clipping to that sloping floor reverses the bank: the old
25 m profile rises 33.935 m. The denser probe measures 34.211 m. This is a
construction-envelope interaction, not an incompatible authored height.

For a clipped head, add its floor deficit plus the existing 10 m bank-rise
allowance to the generated bed. Taper the adjustment linearly with physical
arclength to zero at the first confluence (or terminal if there is no confluence).
The measured head lift is 53.290 m over 7,131.757 m to node 2. This adds a constant
grade, preserves the shared bed and stops before downstream reaches. Collinear
subdivision cannot change that length. It reduces excavation of the initial
hypothesis; it does not add terrain above the no-fill source. Hard-height kernels
are recomputed against the admitted field after changing its generated profile.
This is a bounded construction recipe, not a general bank-feasibility proof.

The original mouth treatment uses coast-parallel sections. For an oblique river,
a nominal inward bank sample also moves inland through that longitudinal taper,
which can make it climb away from its bed. The candidate uses perpendicular river
sections. With upstream fractions `t_r` along the river and `t_c` normal to the
coast, its bed taper is `h * max(t_r, 0)^3`. Its rounded bank relief is
`10 * (distance / 500)^2 * max(t_r, t_c, 0)^1.3`, in metres. The cubic bed taper
follows the near-mouth order of the existing fresh profile; the bank exponent
remains this fixture's coastal taper, not a calibrated estuary law. Existing
500 m core / 2,400 m support and blending are retained. The unchanged source bound
owns the exact zero coast.

Positive transverse relief also covers the inland wedge beyond the perpendicular
outlet section. Omitting that wedge left an edge defect, while making the entire
wedge zero would introduce a flat strip. Regression checks sample both sides of
that section and retain exact coastal heights.

## Measurements

Every row uses the same 575 bank pairs. Ordinary inward profiles retain their
25 m stations plus endpoints and 1 cm rise tolerance. The new independent dense
pass uses 202 points per pair: 116,150 heights, maximum step 2.488 m. It keeps the
same cumulative-excursion definition and tolerance. Endpoint support is still
measured independently at its existing tolerance.

| Field | Ordinary inward failures | Dense inward failures | Endpoint failures | Captured heads | Interior sinks |
|---|---:|---:|---:|---:|---:|
| Control local, all spacings | 21 | 21 | 5 | 4/4 | 0 |
| Candidate local, all spacings | 0 | 0 | 0 | 4/4 | 0 |
| Candidate raster, 1,000 m | 261 | 269 | 87 | 0/4 | 13 |
| Candidate raster, 500 m | 238 | 253 | 10 | 0/4 | 14 |
| Candidate raster, 250 m | 217 | 241 | 5 | 4/4 | 0 |
| Candidate raster, rotated 250 m | 217 | 241 | 5 | 4/4 | 0 |

The maximum local dense rise is 0.006195 m, below the unchanged 0.01 m tolerance;
this is not a claim of exact continuous monotonicity. Four local cases share one
physical field and a quarter-turn, not four independent landscapes. All 48,705
interior checking samples reach the coast locally and in 250 m delivery. Local
and 250 m delivered longitudinal profiles pass at both 100 m and 25 m spacing.
All hard-height, divide, coast, no-fill, construction-cap and volume gates pass.

The old 250 m raster has 222 ordinary inward and 11 endpoint failures; the new
217 and five are only partial delivery gains. Its maximum dense inward rise is
still 54.062 m. The head witness figure shows the remaining bounds-projection
problem directly. At the head itself, the local height is 198.722 m and its legal
floor is 189.882 m; the conservative incident-cell floor raises the delivered
node to 253.630 m. This isolates that large error to bound projection rather than
Float32 quantization. Conservative incident-cell cap projection changes some 250 m
node heights by up to 93.045 m; hard-target projection adds up to 118.714 m. These
are separate from interpolation's smaller displaced bank minima. Do not call
these artifacts erosion, hide them as groundwater or accept capture alone.

An additional untimed 250 m delivery ablation separates those effects. The raw
nodal field is the saved local common field sampled every second row/column;
its equality with a fresh local sample was checked. The cap-only case uses the
same inward Float32 bounds but stops before hard-height projection. Both are
rejected diagnostics, not deliverable alternatives. Counts use the same dense
banks and 125 m cap-check points:

| Delivery stage | Dense bank failures | Maximum inward rise | Cap violations | Maximum hard-height error |
|---|---:|---:|---:|---:|
| Unprojected nodes, bilinear | 238 | 0.315582 m | 196 | 84.776490 m |
| Conservative caps only | 241 | 54.061676 m | 0 | 84.776490 m |
| Complete delivery | 241 | 54.061676 m | 0 | 0 m |

Thus bounds projection explains the large head defect; interpolation already
causes many smaller defects. Hard-height projection changes neither bank count
nor worst rise on this cleared layout. Simply omitting either projection is not
an admissible fix. This diagnostic adds no timing or full-cohort acceptance claim.

Composition cut is 30.376 km3 locally, and 25.804 / 28.655 / 29.689 km3 in the
1,000 / 500 / 250 m raster deliveries. These are 125 m trapezoidal differences
from generated initial relief, not geological material or sediment accounting.
Repeated construction matches exactly. Rotating the 250 m raster back gives zero
maximum height difference. All twelve previous control cases retain their full
numeric-hash dictionaries from `valley-layout-evidence-20260926`.

## Rejected exploratory alternatives

These exploratory probes informed the retained recipe; they are not independent
acceptance cohorts and are not retained production fallbacks.

| Attempt | Observation and reason for rejection |
|---|---|
| Head-only sampled radial envelope | 500/1,000 m supports remove the large head error but leave 19/25 inward failures through the curved reach. Endpoint success does not constrain the swept minimum union. |
| Short cubic head transition | 2,400 m fade leaves 16 local inward failures. Concentrating the added grade moves valley minima around bends. |
| Whole-tributary cubic fade | Passes 25 m probes, but denser sampling exposes three sections above 1 cm (maximum 0.010223 m). A smooth taper is not automatically a better bank. |
| Whole-tributary quintic fade | Five ordinary / eight dense failures, with dense maximum 0.014145 m. The steeper middle remains problematic. |
| Fade only on the final straight approach | Ordinary probes pass but one denser section rises about 0.406 m. Moving the grade transition does not remove its junction interaction. |
| Initial perpendicular mouth without inland wedge | Only three ordinary failures remain, but two are outlet-section edge artifacts up to 0.639 m. Explicit wedge relief removes them. |

The constant-grade linear head taper passes the denser check without changing
its tolerance. Exploratory scripts remain in ignored `artifacts/valley-*-probe-20260926.py`;
committed implementation, tests and the controlled manifest own reproducibility.
The previous register's whole-network radial lifting remains rejected as well.
See [T11](terrain-method-decisions.md#t11---construct-head-and-mouth-sections-before-raster-delivery).

## Reproduction, verification and cost

Run from the repository root in the existing base Python 3.14 environment:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.evolution.boundary_comparison --output artifacts/my-valley-boundaries
.\.venv\Scripts\python.exe -m pytest tests/test_valley_boundaries.py
```

Measured artifacts are in `artifacts/valley-boundaries-evidence-20260926`.
The command reruns the twelve nested controls and four candidate cases, with
repetition, dense profiles, common routing and 37 figures. It publishes the
parent manifest last, hashes its control manifest, and retains hard-input or
execution failure as `incomplete.json`. Quality rejection is a completed result.
Saved arrays contain both bank coordinates, ownership, profiles, source/ground,
prepared beds, hard targets and corrections. Witness figures use matched axes
and label control, local candidate and raster candidate independently.

The 250 m bank-witness and local/delivery routing figures were visually inspected.
They confirm the local head/mouth gain and continuing raster/D8 limitations;
this is not visual acceptance of natural-looking production landforms.
Eight new regression cases cover tributary/subdivision ownership, complete local
and delivery gates, coastal continuity, a separate oblique-mouth positive control,
dense detection of a missed narrow hump, unsupported modes and complete/failed
publication. The small oblique-mouth test does not establish arbitrary-angle
landscape behavior. No dependency, product setting or save schema changed.

The first two full runs each passed 1,733 tests and failed the same geology
save-on-parent-close check, with the expected scientific-reference skip and
8/7 Tk warnings (539.98 / 509.47 s). The existing eight-second wait expired while
`Variable.__del__` warnings reported finalization off the Tk main loop. All nine
geology-editor tests passed unchanged in isolation (5.58 s), so isolated success
did not clear the full-suite failure.

A targeted test-isolation change now runs `gc.collect()` on the test/main thread
after each UI/workbench test protocol. Inspection of pytest's runner confirmed
that its protocol finally block releases `funcargs` and request references after
fixture teardown; collecting during fixture teardown alone is too early. This
prevents released UI cycles from being left for a later worker to collect.
It changes no editor behavior, deadline, assertion or application GC policy.
All 28 focused world/editor tests pass after the change (16.64 s).

A separate isolated shutdown probe found that removing Tcl variable traces
allows an otherwise retained closed workbench to be collected. That broader
callback/resource ownership issue remains a TODO, not a runtime fix claimed by
this test-isolation change. The validation history is retained rather than
reporting only the passing focused rerun.

After the test-isolation correction, the full suite passes **1,734 tests**, with
one expected isolated scientific-reference skip, in 543.78 s and without Tk
finalization warnings. Ruff and Pyright pass. All 53 artifact hashes, 265 numeric
array hashes, both linked control manifests and current source/runtime identities
were verified. The 701 local links in changed documents and the complete
194-document inventory pass. No private-world regeneration or isolated history-
engine run was required for the numerical change.

The standalone cohort took 62.067 s and peaked at 211.76 MiB resident memory,
without concurrent tests. Candidate preparation plus repeat/delivery took roughly
0.039 / 0.059 / 0.131 s at the three spacings. These are bounded-fixture timings,
not continent-scale forecasts. Benchmark-source SHA-256:
`ceb44f323bd401538caa6107936e94481d0861664f318945e679c506527ab2cb`.

## Next bounded implementation

Keep this local field and all matched/control evidence. First isolate conservative
cap projection from interpolation: compare tighter delivery bounds that still
protect every cell interior, without returning to node-only checks. Include
cells touching the protected divide, where the allowed cut starts quadratically:
a bilinear cut can exceed that envelope between valid nodes. A tighter method
needs an explicit interior bound as well as denser samples; clipping negative
capacity estimates to zero must not silently invalidate that bound. The large
head correction makes this a concrete target before a broad representation change.
Then compare one bounded channel-conforming reconstruction if bank distortion
persists. Keep actual Float32 delivery, full guide/bank/capture and dense guards,
hard targets, no-fill/cap/volume, repeat and rotation requirements. Add held-out
and general-angle coverage before adoption. No uniform global refinement or
higher cut budget is justified.

History coupling, broader landforms, LE3/WC2 and normal workbench integration remain
gated on a complete accepted construction/delivery pair. Groundwater and canyon
mechanisms remain separate hypotheses with their own storage and erosion budgets.
