# Valley-bank feasibility: endpoint support does not establish capture

Date: 2026-09-25. Status: **implemented and measured research comparison;
rejected for production use**. This completes the bounded bank/confluence
experiment after the [constrained-network fit](2026-09-25-constrained-network-surface.md).
The [main strategy](../strategy/README.md) owns the next gate;
[benchmark instructions](../../benchmarks/evolution/README.md#valley-bank-feasibility)
own the command. Normal generation and campaign sources are unchanged.

## Decision

Adding physical bank-to-bed constraints makes the selected bank endpoints higher
than their river beds, while retaining native cut limits and hard heights. It
still permits intervening rises and fails actual drainage capture. At 250 m,
interior sinks increase from 19 in the longitudinal-only control to 30. No case
passes the terrain-quality gate. Do not promote the candidate or describe the
endpoint improvement as solved drainage.

The next bounded construction should carry river-aligned cross-sections and
junction geometry into local surface patches. Keep this fixture, admission
checks and actual-ground measurements. More endpoint inequalities or a globally
finer raster are not the selected next step. This is a representation hypothesis
to test, not an accepted new terrain backend.

## What is implemented

`nearest-network-bank-support@1` prepares physical stations every 250 m on all
15 required edges, including heads, junctions and mouths. Candidate banks are
500 m to either side. Each bank projects to the closest reach of the whole
network, so a tributary is not incorrectly raised as another reach's bank.
The immutable support retains requested and actual edge ownership, physical
coordinates, remaining distance to the mouth and the network identity.

All process spacings share 525 bank probes; 60 refer to an adjoining reach rather
than their requesting edge. Three outside-domain probes are counted and omitted.
They are not removed after seeing their heights. The support generator is
bounded to 8,192 candidate probes. Existing grid, active-node and solver limits
remain; no new dependency or application setting was added.

For a bank `b` and its projected bed `p`, require
`height(b) - height(p) >= 0.0005 * distance(b,p) * taper`.
Away from the mouth the nominal 500 m offset therefore asks for a 0.25 m drop.
Over the last 500 m of remaining network length, `taper = u*u*(3-2*u)` with
`u = min(remaining_length/500, 1)`. It reaches zero at the fixed sea-level mouth.
A uniform positive bank drop at the mouth contradicted the zero-height coastal
boundary; the explicit taper corrects that model assumption without raising
cut limits, moving heights or adding fill. The same taper is used in every case.

The existing fit combines these inequalities with whole-cell downstream descent,
off-grid hard-height equalities and the conservative native cut/no-fill bounds.
Every delivered Float32 bank difference is checked again, with at most 0.0001 m
residual. This is an endpoint height condition, **not** a continuous inward-slope
condition. Physical cross-sections are independently sampled every 25 m to
expose the distinction, using the existing 0.01 m whole-climb tolerance.

### Feasibility diagnostics

Before fitting, an interval calculation bounds each bank inequality using its
actual bilinear weights and permitted nodal heights. Locally impossible pairs
report coordinates, edge ownership, required drop and unavoidable shortfall.
The 1,000 m fixture rejects six pairs at lowland transitions; the largest
unavoidable shortfall is **0.54265 m**. No candidate surface is published.

If individual intervals pass but the joint linear problem is infeasible, a
bounded diagnostic solve minimizes one common bank shortfall while retaining
all hard heights, native bounds and longitudinal conditions. Its nonzero dual
weights identify participating bank rows at that optimum. They do not identify
a unique or minimal conflict set. This diagnostic never returns a generated
surface and is not permission to soften the instructions. The meaning of the
inequality marginals follows the [SciPy HiGHS documentation](https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs.html).

An explicit 500 m control pins the bed at `(13000, 2000)` to its source height,
745.4375 m. The nearest bank's no-fill ceiling is about 732.0461 m, while its
required rise is 0.25 m. The height-only problem is feasible; adding bank support
rejects it and reports **13.64136 m** minimum common shortfall. No pinned height
is lowered. Solver errors and timeouts remain failed executions, not scientific
infeasibility results or fallback terrain.

## Fixed comparison and measured results

Reuse `two-catchment-range-lowland@1`: 32 by 24 km, four heads, two mouths,
15 edges, the same 2 km parent source, protected central divide and two off-grid
heights. Native mountain/hill/plain caps remain 150/120/15 m under the 156 m global
limit. The conservative incident-cell envelope changes its padding with process
spacing; this remains a sensitivity comparison rather than a pure convergence
claim. The earlier longitudinal-only fit is the matched control.

Each constructed case retains all required paths, has zero unresolved river
profiles and zero sampled network ascent at both 100 m and 25 m stations, and
passes all 49,601 common-grid native cut/no-fill/protection samples and both
hard heights. Maximum sampled cuts are 148.118 m at 500 m and 145.895 m at 250 m.
These successful constraints do not compensate for failed valley capture.

| Process spacing | Bank fit | Endpoint violations, control / candidate | Cross-sections with inward rises / 525, control / candidate | Interior sinks at common 125 m, control / candidate | Candidate heads reaching mouth / 4 |
|---|---|---:|---:|---:|---:|
| 1,000 m | Infeasible | 168 / n/a | 241 / n/a | 3 / n/a | n/a |
| 500 m | Constructed | 123 / 0 | 259 / 255 | 16 / 15 | 0 |
| 250 m | Constructed | 113 / 0 | 264 / 273 | 19 / 30 | 0 |
| 250 m, rotated 90 degrees | Constructed | 113 / 0 | 264 / 273 | 19 / 30 | 0 |

The largest inward rise decreases from 56.23 to 32.96 m at 500 m and from 46.49
to 37.01 m at 250 m, but hundreds of cross-sections still climb. At common 125 m
spacing, 13,608 of 48,705 interior stations fail to reach coast at 500 m; 14,620
fail at 250 m. Divide crossings remain zero. Raw D8 routing imposes no river
receivers, filling or mouth connections. A captured head must reach zero-height
coast within the existing 1,000 m mouth tolerance. The no-new-sink gate compares
to the original source, which has zero interior sinks, not to an already failing
fitted control.

Repeated fits are exactly equal as Float32 arrays in the recorded runtime.
Rotating the 250 m case back changes ground by at most **0.00000215 m**, within
the fixed 0.001 m rotation check. This is not exact byte equality under rotation,
arbitrary-angle invariance or a cross-platform guarantee. Finer sampling and
D8 capture remain diagnostics, not continuous two-dimensional flow proofs.

A separate manufactured straight valley has inward support, a fixed coastal mouth
and successful raw routing. It verifies a feasible positive control; it does not
reverse the branching fixture's rejection. The actual-ground figures were
inspected: the candidate still has inland stopping points and incomplete valley
connections, consistent with the measurements.

## Why change the local representation next?

The following is a limited mathematical observation about this comparator.
Inside a bilinear cell, write `h(x,y) = a + b*x + c*y + d*x*y`. For a straight
river with unit tangent `t = (tx,ty)` and normal `n = (-ty,tx)`, differentiating
the normal gradient along the river gives
`d/ds (gradient(h) dot n) = d * (tx*tx - ty*ty)`.
An exact differentiable transverse minimum along an interior segment requires
zero normal gradient throughout. At generic directions where `tx*tx != ty*ty`,
that forces `d = 0`: the patch is planar, with no strict transverse minimum.
This does not rule out grid-edge valleys, piecewise approximations, other
surfaces or useful finer rasters. It does explain why imposing an exact oblique
valley on this fixed cell representation can be restrictive.

[Génevaux et al. (2013), sections 6–7](https://cs.purdue.edu/homes/bbenes/papers/Genevaux13ToG.pdf)
construct river primitives from bed elevation and cross-sectional distance to a
river skeleton, with junction primitives and terrain composition. That supplies
a primary-source basis for testing local river-aligned patches. This batch does
not reproduce their algorithm, adopt their whole construction tree or establish
that their method meets our native caps and hard inputs.

The next experiment should construct one connected range-to-lowland valley with
explicit bank, confluence and mouth geometry; bound transitions to the unchanged
source; and check both the local field and its Float32 raster delivery. Keep the
current network and hard inputs as the first control. Where automatic guidance
is impossible, compare bounded rerouting/relocation separately and retain route
coverage; incompatible fixed requirements must stay visible. Promotion requires
all four heads to reach their mouths, no additional unintended sinks, preserved
native limits/heights/divide, repeat/rotation checks and actual-ground inspection.
Only then broaden seeds, coasts and landforms or integrate LE3/WC2. A full TIN
backend, Rust rewrite, history UI or another benchmark framework is not justified
by this result.

## Cost, artifacts and validation

The standalone four-case run took **18.79 s**, with **167.57 MiB** whole-process
lifetime peak. Candidate fit/rejection times were 0.002/0.949/3.098/3.726 s at
1,000/500/250/rotated-250 m. The fits use 501 free constrained nodes at 500 m and
1,460 at 250 m. The existing default 20 s cooperative solver budget and
500-iteration limit were not increased. These are local bounded observations,
not continental-scale estimates or a hard native-kernel interruption guarantee.

Ignored local evidence: `artifacts/valley-support-final-evidence-20260925/`. The HTML
gallery links actual-ground support and routing figures. Per-case NPZ stores
source/control/target/caps, complete geometry and hard inputs; `ground_m` exists
only when a candidate was constructed. Case JSON retains conflicts, all bank
profiles, quality gates, repeat checks and artifact hashes. Completion-last
`comparison.json` records source/runtime identity, measured cost and the rejected
quality decision. Failed execution writes `incomplete.json`; existing folders
are not overwritten. The recorded runtime uses NumPy 2.5.2 and SciPy 1.18.1.
No private map or isolated history engine was run.

The 31 focused bank/network tests pass. They cover physical-scale independence,
junction ownership, mouth taper, manufactured capture, unchanged hard inputs,
local/joint conflicts, hidden cross-section humps, bounded preparation,
identity mismatch, repeat/rotation and complete/incomplete artifact publication.
A solver claiming success with an invalid delivered field must fail the run;
it cannot be reported as proof that the user inputs are infeasible.
The final full base-environment suite passes **1,690 tests**, with the one expected
isolated scientific-reference skip, in 422.46 s. Ruff and Pyright pass. All
606 local links in changed documents and the complete 189-document inventory
pass, with 11 separately listed supporting contracts. The final seven figures
are byte-identical to the inspected run. These checks verify the implementation
and its evidence; they do not override the rejected terrain-quality decision.
