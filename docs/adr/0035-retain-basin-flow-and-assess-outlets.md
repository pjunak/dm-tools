# ADR-0035: Retain basin flow and assess downstream outlets

- Status: Accepted
- Date: 2026-09-11
- Supersedes: ADR-0034's diagnostic-only planned basin exits and unvalidated outlet review

## Context

Zero incision inside an authored basin prevented unwanted ground changes, but
both contributing-area calculations and planned channels still traversed it.
A low outlet marker alone did not establish a viable downstream route.

## Decision

Treat every canonical authored footprint node as an absorbing terminal. Seed
Priority-Flood there, preserve seed heights, suppress outgoing D8 and MFD flow,
and derive channels, stream order and bounded incision from this graph. Retain
incoming area at its first footprint node and sum terminal MFD area per intent.
The equal-node area convention remains unchanged. Do not pool interior flow,
invent a common basin floor or transfer area through an undeclared exit.

Hold lakes with declared outlets terminal as well until connection is supported.
Independently assess their nearest eligible outward attachment and downstream
finished-field conditioned route. Inspect unfilled Float32 heights, continuous
vector land and authored polygons. Export the inspected path, length, rises,
terminal context and precise blocked/unresolved findings. Candidate topology
must not certify a river merely because it descends on a filled copy.

A sampled-clear candidate stays pending: full lake connection needs wet-component
and shoreline checks, area transfer, basin-to-basin cycle checks, and revalidation
after any ground edit. No breach or reroute applies automatically. Existing
regional cutting limits and authored height/valley authority remain intact.

Generator becomes `coastline-constraint-terrain@7`, automatic valleys become
`regional-budget-mfd-d8-valleys@6`, water review becomes
`authored-basin-water-review@2`. Current project v5 remains unchanged. Build v8
adds the numeric retention-terminal mask and updated diagnostics; remove v7.
No compatibility loader or migration is introduced.

## Alternatives and consequences

Hiding exit lines would leave area and channel sizing inconsistent. Masking
basins out as non-land would discard their own contributing area and confuse
water intent with coastline topology. A nested Fill-Spill-Merge model would
need a depression hierarchy and water inputs absent from this product.

Footprint terminals are an explicit planning boundary, not simulated storage.
All internal footprint nodes retain local contributions independently. Narrow
features below canonical spacing need refinement. The separate natural-basin
inventory remains a boundary-conditioned diagnostic copy and can show routes
that the authored planning graph intentionally stops.

Outlet evidence is sampled, uses one deterministic attachment, and does not
search all alternatives or calculate constrained breach feasibility. It does
check vector geometry between samples. An early obstruction leaves a reviewed
prefix, whose length must not be presented as a full route length.

## Validation

Analytical tests cover terminal-area conservation for both routing models,
flat underflow behavior, existing downhill flow interception, protected ground,
nested-grid invariance, off-grid attachments, whole-route uphill evidence,
cycles, invalid receivers, basin re-entry, sub-grid vector gaps and basin
crossings, unresolved attachments and unspecified terminal levels. Repeated
headless builds verify current schema, arrays, diagnostics and hashes.
