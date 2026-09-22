# ADR-0059: Preserve noise-band amplitudes

Date: 2026-09-22
Status: Accepted

## Context

Zoom-driven local enrichment must be able to add structure without changing
existing noise coefficients. The former finite normalized sum divided every
band by the sum of the selected amplitudes. At roughness 0.55, increasing two
bands to six reduced every existing coefficient by 28.26%. Coordinate sampling
was deterministic, but changing the detail setting reweighted broad terrain.

[ADR-0058](0058-sample-bounded-regional-windows.md) supplies unchanged-field
regional sampling. Stable coefficients are a prerequisite for added detail;
they do not establish its finished-parent contract.

## Decision

Use a fixed unit budget over the infinite geometric series. For roughness
`0 < r < 1`, band `k` receives `(1-r) * r^k`. Evaluate the same Float64 recurrence
for every request and never renormalize the selected prefix or tail. At `N`
bands the mathematical resolved budget is `1-r^N`; the unevaluated share stays
reserved. Production supports 1 through 12 bands. Lattice hashing, octave
addresses, interpolation, stage seeds and physical feature spacing stay fixed.

Expose tail selection by starting band, retaining its original coefficient and
address. Regional shape and summit carriers are separate, fixed two-band
recipes with roughness 0.5 and full-scale weights 2/3 and 1/3. Regional texture
uses only bands with zero-based indices 2 and above. It no longer subtracts a
different broad carrier from the whole noise field. This prevents coarse
components from leaking into what is intended as fine regional texture.

Global and regional base macro fields remain identical when increasing detail
from two to six or twelve bands. This invariant concerns the pre-constraint
base, not the finished terrain, authored longitudinal profiles or routing.

The research component enclosure uses the same rounded coefficients and
arithmetic order as runtime noise. Its scope remains isolated default-prefix
noise, not regional shape scaling, selected tails or the complete terrain.

Advance generator identity to `coastline-constraint-terrain@16`, noise to
`coordinate-value-noise-fixed-budget@2`, landforms to `regional-landforms@2`,
and the component-bound method to `rounded-cell-value-noise@2`. File schemas
and seed derivation stay unchanged. Remove the obsolete normalization outright;
there is no old-policy mode or saved-output compatibility promise.

## Consequences and validation

High roughness with few bands uses less of the total variation budget. Default
terrain, channel selection and derived water evidence can change. This is a
foundation change with mixed drainage effects, not a universal quality gain.
The [comparison](../research/2026-09-22-stable-detail-band-amplitudes.md) records
both improvements and regressions, including the larger known seed-7 crest.

Regression tests isolate every band, check exact coefficient prefixes and
bounded additive tails, keep base macro fields fixed, and exercise existing
conservative enclosures, authored constraints and shared-coordinate sampling.
Whole-terrain measurements show that fixed coefficients still permit substantial
coarse-cell drift and authored route changes. R34 remains open for coarse power,
parent restriction and conditioned generation. Small cartographic rivers remain
gated on future finer terrain and hydrology, not image magnification.
