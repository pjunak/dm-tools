# Authored geology inputs — 2026-09-25

This is implementation evidence for the province/default slice of WC1, following
[the world-context research](2026-09-24-world-context-enrichment.md) and
[the staged plan](../strategy/world-context.md). It introduces no new scientific
model, runtime dependency or claim of improved terrain output. The first consumer
is an inspectable categorical coverage resolver. See the
[user guide](../world-geology.md) and [ADR-0076](../adr/0076-author-world-geology-inputs.md).

## Delivered

- Separate portable v1 recipe with retained full-world identity, exact field/type
  checks, independent crust/rejuvenation/duration values and a common present.
- Continent defaults and cross-continent/seam provinces with explicit priority,
  water clipping, invalid-polygon rejection, zero-coverage reporting and spherical
  land-area conservation. No implicit smoothing or age-derived coefficients.
- Dedicated World → Geology editor: select/edit, draw/redraw/delete, apply/revert,
  undo/redo, zoom/pan, source/context backgrounds, effective coverage and numeric
  hover. Separate save/open and parent-window unsaved guards protect the source.
- Background resolution/open jobs with cancellation; validated atomic saves and
  external-file-change checks. CLI inspection, current schema and synthetic example.

## Evidence

Focused geology controls: **45 passed**, including analytic area across three
source scales/origins, both seam directions, cross-label old-crust/young-belt
profiles, masked ties, water-only overlap, inland holes, invalid geometry/values,
strict identity, schema, deterministic save/reopen and failed atomic replacement.
Nine real Tk workflow tests include pointer-based seam drawing, full-precision
age retention, cancellation, invalid-form guards and save-on-parent-close.

Visible owned-app checks used the public example at 1320 × 850 and 1050 × 740,
and a private nine-continent world at the normal size. Source documents were
unchanged; the private world received no authored geology. Existing context was
opened as a read-only background. Screenshots and timings stay in the private
campaign audit, outside this repository. The public example's two provinces
retain total land area 162,111,179.5951518 km².

Final gates: `python -m pytest -q` — **1,549 passed, 1 expected skip** in
383.54 s. The skip requires the isolated scientific reference environment; this
batch changes no reference solver. Ruff and strict Pyright pass. The documented
module invocation includes repository benchmark helpers; a direct `pytest.exe`
launch was discarded after import-collection errors from its different search path.
The documentation audit accounts for **181 documents**, **1,261 local links**
and **8 current JSON schemas**, with no missing inventory entries or local files.

Warm prepared-world performance, three repetitions after the regression run,
median wall seconds on Windows / CPython 3.14.7:

| Fixture | Resolve coverage | Render 1320 × 850 |
|---|---:|---:|
| Public two-province example | 0.00207 | 0.00163 |
| Public 128 provinces × 256 vertices | 0.37799 | 0.00595 |
| Private nine-continent defaults, unspecified geology | 0.52468 | 0.01778 |

The 128-province fixture places nonintersecting radius-two source-unit circles
on a 16 × 8 lattice over the public world. These measurements exclude source
parsing, context reopening, Tk, persistence and native-memory accounting. They
are bounded workload observations, not worst-case runtime guarantees. All three
resolved sums matched their prepared-world land areas at reported precision.
The UI keeps geometry work off its event loop and draws one canvas path per
province outline, avoiding one Tk item for every polygon edge.

## Remaining limits and next step

The categorical fields do not yet drive rough relief, a tectonic/erosion model,
climate, bathymetry or regional refinement. Their successful tests establish input
and coverage behavior, not a geologically realistic result. No new comparison of
terrain quality is claimed. Every future physical consumer must define calibrated
units, transitions, time-dependent forcing and resolution/conservation controls.

Next, define and implement a bounded bathymetric hypothesis product from authored
shelf/slope/basin assumptions, with topology-derived water masks and explicit
uncertainty. Ocean width is not a depth/age estimate. Before any transport solver,
retain water-piece face incidence through split cells; existing positive edge
widths alone cannot connect those pieces safely. B/C physical path/landform and
LE2/LE3 authoring/resolution acceptance still gate world terrain/evolution.

Editor follow-ups include multipart/holed provinces, vertex manipulation,
explicit world rebasing and stronger resource/complexity measurements. Add only
those needed by the next consumer rather than expanding a no-op parameter panel.
