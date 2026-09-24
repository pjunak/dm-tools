# World-source workspace implementation — 2026-09-25

## Delivered result

WC0 is implemented in the desktop/CLI application. A world source now has its
own retained SVG snapshot, stable element/continent membership, full-sphere
Plate Carrée frame, explicit planet radius, topology validation and portable save.
The World workspace provides source mapping and geographic review alongside the
existing local Terrain workspace. [The guide](../terrain-worlds.md) owns usage;
[ADR-0070](../adr/0070-retain-world-source-and-workspaces.md) owns the decision.

This is source handling, not generated terrain or a climate simulation. It adds
no scientific engine, runtime dependency, private campaign data or completed-map
editing. World-linked regional terrain and history replay remain planned.

## Correctness and UI evidence

The public `examples/world/` fixture has four invented continents, touching
mainlands, owned islands, a compound-path hole, excluded furniture, an offset
projection frame and an island crossing the seam. Its source page dimensions
intentionally differ from display pixels. Original source remains embedded and
hash-verified; inspection wrapping and curve flattening never rewrite it.

Regression controls cover frame round trips with/without longitude wrapping,
custom-radius great-circle distances, polar caps and whole-sphere area; SVG
transforms, compound even-odd/nonzero fill rules, retained tiny gaps/holes;
seam area/identity and overlap rejection; malformed/unsupported/ambiguous input;
current schema, portable reopen, snapshot integrity, failed validation and atomic
replacement; preview holes/clipping; CLI dispatch; and real Tk import, assignment,
undo/redo, rename identity, validation, save/reopen, dirty guards, workspace
shortcuts and callback cleanup. Source-name bounds also match the public schema.

The compound-path tests exposed a library representation detail: a subpath's
initial Move can still carry the preceding ring's endpoint. Clearing that
irrelevant start before flattening restores correct independent ring closure.
Clipping/masking is checked in inherited parsed styles as well as attributes.
Unsupported appearance is reported instead of silently imported as full land.

Application-window captures were inspected at 1440×900 (World overview) and
1160×760 (world frame controls and Terrain). Shape names now stay readable while
selection shows group ancestry. Owner colours are separated across the current
owner set, and periodic outlines stay inside the declared frame. These checks
used the public example, not a private-world export. Automated UI tests run real
Tk; screenshot review is separate evidence, not proof of every display/scale.

Final validation: **1344 passed, 1 expected skip**, Ruff clean and strict Pyright
clean. The skip is the separately installed scientific-reference environment;
this batch does not modify or rerun that evolution solver. New world controls
account for 45 tests, including five real-Tk workflow tests. Existing terrain
regressions remain in the full suite. The local ignored report is
`artifacts/world-ux/pytest.xml`; captures are under the same directory.

## Bounded timing probe

After the first full suite finished, measure three sequential in-process runs
on Windows 11 / CPython 3.14.7, with no concurrent test run. Time parsing,
`prepare_world_map` and a 1200×700 `render_world_source` separately. Rendering
closes each PIL image. This is warmed-process wall time, excluding process startup,
Tk image upload and disk save; native peak memory was not measured. It is not a
latency guarantee, terrain benchmark or large-private-map acceptance test.

| Source | Shapes | Sampled points | Median parse | Median validation | Median render |
|---|---:|---:|---:|---:|---:|
| Public Four Shores | 7 | 191 | 0.0127 s | 0.00110 s | 0.00217 s |
| Synthetic curved islands | 1,024 | 33,792 | 3.689 s | 0.209 s | 0.0404 s |

For reproducibility, the second source is a 360×180 SVG with 1,024 circles:
for `i=0..1023`, ID `island-i`, centre `(10 + 5*(i%64), 10 + 10*(i//64))`,
radius 2 source units. Assign each row to one of 16 semantic continents as islands,
use frame `(0,0,360,180)`, central meridian 0°, planet radius 6,500 km, and the fit
viewport. The first source uses the saved public project's assignments/frame.
The raw repeated timings are in ignored `artifacts/world-ux/performance.json`.

SVG curve parsing is the dominant cost in this probe. Background import/save
keeps it out of the Tk callback, but GIL contention and individual native steps
have no responsiveness bound. Viewport rendering remains synchronous. Keep
checkpoint/cancellation and dense-curved-source profiling in TODO; do not infer a
need for a language rewrite or claim all supported inputs render at this speed.

## Next implementation and limits

WC1 should first establish spherical cell areas, fractional coverage and periodic
connected water, with explicit unresolved straits/islands. Then derive directional
exposure/interior distance before adding bathymetric and geological hypotheses.
Preserve the original source and separate inferred fields from authored geography.
The [updated plan](../strategy/world-context.md) gives the controls and sequence.

Other projections, partial worlds, native Affinity/raster import, partial mapping
draft saves and import cancellation remain unimplemented. Geometry is flattened
for inspection with a stated tolerance, not an exact analytic curve integral.
Saving a world does not project the existing local generator's terrain. Remaining
B/C terrain/path and LE2 authoring/resolution gates still govern WC2 admission;
this source-workflow batch makes no drainage-quality improvement claim.
