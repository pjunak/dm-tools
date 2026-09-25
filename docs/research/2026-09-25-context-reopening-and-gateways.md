# Context reopening and shared water openings

Date: 2026-09-25. Implementation evidence for
[ADR-0074](../adr/0074-verify-context-and-measure-water-openings.md).
This extends the [first geographic slice](2026-09-25-geographic-world-context.md).

## Delivered behavior

- World Context can open completed bundles, restore their authored source/settings
  and inspect all layers without repeating context generation. Embedded input
  files do not become Save targets. Changed inputs invalidate the result.
- The headless `world inspect-context` operation verifies the same contract and
  reports whether the recorded producer matches this installation.
- Context v2 records shared east/south face openings in kilometres, a fourth
  preview, gateway semantics/counts and a canonical manifest fingerprint.
  Superseded context v1 is rejected; its source snapshot can be regenerated.
- Water intervals are measured from prepared vectors. Separate gaps are not
  added into a fictitious wider opening; the longitude seam needs overlapping
  openings on both sides. Poles and point contacts have zero gateway width.
- A confirmed roundoff defect in longitude-edge joining is fixed. Fractional
  source bounds could make `x1 - (x1 - x0)` differ from x0, causing a false closed
  seam. Comparison edges now share an exact x; source geometry is unchanged.

## Validation

The focused context/editor suite passes **98 tests**, including 46 new controls:

- Analytic closed, 0.01-degree and 4-degree straits; disjoint gaps retain the
  longest interval rather than their sum; split-water flags remain present.
- Positive seam intersections versus non-overlapping seam openings, fractional
  source origins at three scales, reflected east/west geometry, custom radius,
  translated/rescaled source coordinates and latitude-cosine edge lengths.
- Zero polar edges and all-land water openings; deterministic read-only arrays.
- Current bundle round trip without generation, normalized whole-number/float
  coordinate identities, producer-runtime retention,
  rejection of relabelled exports and matching input/numeric identity.
- Changed manifests/products, rehashed inconsistent metadata, NaN/out-of-range
  arrays, duplicate JSON/ZIP entries, unexpected members, object arrays, oversized
  declared dimensions and expansion limits. Malformed array controls fail before
  NumPy allocates from the header.
- Cancellation, file changes during verification, failed/obsolete UI loads and
  opening/saving a separate source project without changing embedded snapshots.

Final gates: **1,474 passed, 1 expected skip** in 414.23 s for the full repository
suite; Ruff and strict Pyright pass. The skip is the isolated scientific reference
environment, not a context test. Source/context/editor checks also passed together
(159 tests) after the numeric-frame identity fix. All 741 changed-document local
links resolve, and the complete inventory has 176 documentation files with no
missing or duplicated entries. Actual Tk and final CLI/schema/runtime checks pass.

## Bounded measurements

A retained private nine-continent source was used only for local validation;
its geometry, source names and generated data are not public fixtures. The
numeric stage used an already prepared world, with one observation per size on
Windows/CPython 3.14.7. This is a cost observation, not a stable performance promise.

| Latitude rows | Longitude columns | Numeric generation | Retained numeric arrays |
|---:|---:|---:|---:|
| 90 | 180 | 2.45 s | 470,520 bytes |
| 180 | 360 | 5.03 s | 1,880,640 bytes |
| 360 | 720 | 11.69 s | 7,519,680 bytes |

Array counts include coverage, water IDs, support flags, row areas and both edge
widths. They exclude source/GEOS geometry, temporary decoding buffers, preview
images and transient coordinate vectors. Row-local intersections still use
native-library scratch; these figures are not peak process memory.

The default context conserved land area with an absolute error of approximately
1.49e-8 km² and retained all 48 connected water regions. Tiny regions need not
have a dominant display cell. In a separate full-source trial, verified reopening
took 3.30 s, export 0.24 s, and the application generation operation 10.90 s
(including source revalidation/preparation). A subsequent complete generation,
export and reopen took 12.14 s. Timings are separate observations, not additive
parts of one run. The final refreshed build and verified reopen took 15.18 s
while the full regression suite was running; its producer identity matches the
final source. All 11 original native/SVG map hashes remained unchanged.

Actual Tk inspection opened the saved bundle, inspected coverage and Water openings
at normal scale and 4x zoom, and verified that the source path remained unset for
Save. The edge preview resolves individual faces when zoomed; it does not enrich
numeric resolution. Captures and raw measurements remain with the private run.

## Interpretation and next work

These widths are along shared cell faces, not the minimum width along an entire
strait. They contain no depth, sill or transport-capacity estimate. Multiple faces
can lead into different water pieces inside one cell; a future transport graph
must retain that incidence. The current result must not be used as an unqualified
raster flow graph or accepted terrain/climate parent.

Next implement geodesic interior distance and directional water exposure with
bounded work and explicit sampling/support limits. Equal-latitude island/interior,
longitude-seam, pole, source-scale and reversed-direction controls precede
province defaults and bathymetric hypotheses. No rainfall, ocean circulation,
rough world elevation or regional history is claimed by this batch. The existing
terrain/drainage quality gates remain open in the main strategy.
