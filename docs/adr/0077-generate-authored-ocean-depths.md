# ADR-0077: Generate authored ocean-depth hypotheses independently of land terrain

- Status: Accepted
- Date: 2026-09-25
- Extends [ADR-0075](0075-measure-spherical-geographic-exposure.md) and the authored
  hypothesis boundary of [ADR-0076](0076-author-world-geology-inputs.md).

## Decision

Add separate current-only bathymetry input and result v1 formats. Retain the full
world, explicit connected-water selection, numeric shelf/slope/basin parameters,
geographic algorithm identity and producer runtime. A largest-water UI suggestion
is not an inferred ocean classification. Do not infer ocean age from width or
use column depth as mixed-layer heat capacity. No source coast or land DEM changes.

Use the existing spherical context and its shore-distance bound. Define a C1
smoothstep shelf and slope profile with a bounded constant basin depth. Evaluate
it at the conservative lower bound `max(0, sampled_distance − max_error)`; retain
its numerical depth envelope with outward Float32 rounding. Store negative bed
metres at actual selected-water cell centres, NaN elsewhere. This is a simplified
hypothesis, not a bathymetric reconstruction or hydrographic measurement.

Resolve centre membership from source water polygons; dominant area IDs cannot
stand in for points in mixed/split cells. Keep geographic support flags and report
selected waters with no centre samples. Centre values cannot establish conserved
ocean volume, sill capacity or connections between faces. Those need dedicated
geometry, area integration and conservative transfer contracts.

A new output directory retains a complete geographic bundle, authored snapshot,
bounded numeric archive, derived previews and a final published outer manifest.
Reopening verifies dependency identity, membership and scenario arrays in addition
to file hashes and metadata. The application refreshes geography before generation
when its producer or requested resolution differs. Existing current-format results
retain their producing runtime for inspection; they cannot be relabelled for export.

A dedicated World editor owns input dirty/save state, result freshness, ocean
selection, progress/cancellation and guarded world close/replacement. Saving inputs
is atomic with external-change detection. Editing retains the previous preview
and requires generation before export. Generated snapshots are never automatic
save destinations. The CLI calls the same application operations.

## Alternatives and consequences

Using ocean width as depth or age would invent geological information absent from
coastlines. Reusing dominant cell IDs would leak depth onto land and enclosed
water. A per-pixel depth brush would violate pre-generation-only authoring.
Physical ocean/tectonic simulators require histories and conservation contracts
not supplied by this input. Retaining nested geographic products costs disk space
but makes each scenario portable and reviewable without a hidden mutable parent.

The conservative distance bias leaves a shallow strip and can underrepresent narrow
shelves. The error field covers only distance discretization and Float32 rounding,
not uncertainty in assumed geology. Uniform basin floors and one global margin
profile are deliberate first-stage limits. Per-margin types, bathymetric guidance,
area/volume integration, component-aware transport, depth-driven climate and land
terrain remain later work. This decision does not alter land's R07 datum policy.

## Validation

Analytic equatorial coast, spherical radius and source-scale/offset tests cover
physical units, seam/pole behavior and the numerical envelope. Small land and lake
centres inside dominant-ocean cells exercise actual membership. Tests cover
unresolved selections, strict inputs, deterministic samples, immutable context,
corrupt/rehashed bundles, schema/CLI paths, cancellation and incomplete publication.
Real Tk workflows and visible private-world review exercise save/reopen, stale
previews, source isolation and guarded close. See the
[implementation report](../research/2026-09-25-authored-world-bathymetry.md).
