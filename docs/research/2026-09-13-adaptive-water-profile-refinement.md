# Adaptive water-profile refinement - 2026-09-13

Status: implemented research experiment; midpoint residuals are not adopted as
runtime clearance or continuous error bounds. [TODO](../../TODO.md) tracks the
remaining accuracy and cost work. The current runtime station policy remains
[ADR-0045](../adr/0045-sample-procedural-detail-and-context-shoulders.md).

## Result and decision

Adaptive probes can reduce missed terrain heights, but a small midpoint residual
alone does not bound an unseen peak. The new experiment preserves production
stations, separates indicator satisfaction from finite-reference accuracy, and
reports budget, depth and coordinate exhaustion explicitly. A regression fixture
misses a 20 m peak despite an exactly zero indicator. Keep this method as a
research control; do not use it to authorize water transfer or to remove existing
probes. No terrain, routing, water-gate, project or build contract changes here.

## Research basis

[Gonnet, A Review of Error Estimation in Adaptive Quadrature (2010)](https://arxiv.org/abs/1003.4629)
examines error indicators and false convergence when sampled differences become
small despite unresolved behavior. This is a methodological warning from
integration, not a terrain-extrema formula or a clearance guarantee. Our
midpoint experiment tests that failure mode directly rather than treating an
integration estimator as a bound on the maximum height.

[Bouttier et al., Regret analysis of the Piyavskii-Shubert algorithm for global Lipschitz optimization (2022 revision)](https://arxiv.org/abs/2002.02390)
studies global maximization with a known Lipschitz upper bound and possibly
perturbed evaluations. With a valid constant L, sample heights can form a
conservative upper envelope through `min_i(h_i + L * distance(x, x_i))` in the
unperturbed setting. Measured secant slopes do not supply that prerequisite.
Our inference is to establish conservative component/combined-field bounds and
an evaluation-error envelope before selecting a certified adaptive method.
Float32 quantization also prevents treating the stored field as a smooth
function without a rounding allowance.

Neither paper supplies bounds for our complete terrain evaluator. Procedural
noise, coast weights, regional and absolute/relative constraint blends,
longitudinal profiles and incision interpolation need separate analysis. No
external implementation, package or new dependency was adopted for this test.

## Experiment contract

`benchmarks/profile_refinement.py` adds `midpoint-residual-research@1` to the
existing finished-field runner. It starts with the actual production plan,
then measures the absolute difference between a midpoint height and the mean
of the two endpoint heights. It subdivides intervals whose residual exceeds
the requested threshold. Every pending wave must fit the sample cap before any
of its points are evaluated; no accepted prefix escapes an exhausted run.

Integer dyadic keys locate probes directly within original intervals, avoiding
repeated coordinate interpolation. All original stations survive, including
corners, retraces and signed zero. Distinct anchors that round to the same
coordinate remain in the profile but add no interior subdivision. A positive
interval whose midpoint rounds to an endpoint returns `precision_exhausted`.
It is not silently dropped or certified. Budget/depth/precision failures report
visited/requested counts and unresolved intervals without accepted metrics or
reference comparisons.

`indicator_satisfied` is deliberately weaker than a bounded-error result.
Only after selecting the probes does the experiment evaluate its independent
nested reference. Default depth 7 permits adaptive subdivision through factor
128, with a factor-256 reference containing every adaptive coordinate exactly.
Positions and Float32 ground must match byte for byte at shared stations. The
reference's extrema and greatest downstream rise from an earlier minimum are
compared against both the original and adaptive station sets. This is not a sum
of every positive slope, a water-head calculation or a hydraulic model.

Adaptive profiles are capped at 65,536 stations; reference work is separately
capped at 262,144. An excessive reference leaves the comparison unknown, even
if the indicator was satisfied. Production limits remain 65,536 per profile,
65,536 per wet network, 262,144 per dry network and 4,096 per evaluator batch.
Counts are requested path stations, including repeated coordinates, not unique
evaluations. Depth is limited to 1-8. The research report format is now v2;
product schemas and algorithm identities are unchanged.

## Counterexample with an exactly zero residual

The regression uses a 1 km path with original stations at 0, 0.25, 0.5, 0.75 and
1 km. Its ground is `20 * max(0, 1 - abs(x - 1/16) / (1/64))` metres, where x is
in kilometres. Every original point and first midpoint has height zero. The
indicator accepts all intervals after nine probes, with residual exactly zero.
The 1,025-point reference includes the 20 m peak at x = 0.0625 km; the adaptive
profile misses both that crest and the selected 10 m above-level decision.
`reference_exceeds_tolerance` reports the discrepancy. This constructed field
is a regression of the stopping rule, separate from the real-field matrix.

## Finished-field measurements

```powershell
.\.venv\Scripts\python.exe -m benchmarks.water_convergence --seed 42 20260913 --direction horizontal diagonal oblique --repeats 2 --adaptive-tolerance 1 .1 .01 --output artifacts/adaptive-profile-matrix-final-20260913.json
```

The matrix uses the five existing public stress cases, two object scales
(400/4000 km), three path directions and two seeds: 60 distinct scenes, repeated
in fresh processes for 120 runs. Each compares three midpoint thresholds.
Protected dry footprints isolate the prepared field from automatic cuts. These
are short profile stress cases, not a many-lake performance benchmark or
representative authoring defaults. The delivered 64-pixel raster does not
supply the field sampled by the experiment.

Outcome counts below use distinct scenes, not their repeated runs. Error maxima
include only trials that satisfied the indicator and obtained a complete
reference. Unresolved profiles are excluded, never assigned zero error.

| Residual threshold (m) | Satisfied / 60 | Depth exhausted | Precision exhausted | Worst crest miss (m) | Worst minimum error (m) | Worst ordered-rise miss (m) |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 52 | 0 | 8 | 0.156647 | 0.211914 | 0.225586 |
| 0.1 | 52 | 0 | 8 | 0.013672 | 0.016846 | 0.021851 |
| 0.01 | 42 | 10 | 8 | 0.002197 | 0.001343 | 0.002686 |

At the tightest threshold (0.01 m), work varies considerably by terrain:

| Case | Satisfied / 12 | Original stations | Adaptive stations when satisfied | Sample multiplier | Worst crest miss (m) |
|---|---:|---:|---:|---:|---:|
| Regional transition | 0 | 34-47 | — | — | — |
| Global procedural detail | 12 | 53-709 | 2,615-34,897 | 42.1-54.2x | 0.001953 |
| Rotated regional detail | 12 | 53-709 | 1,293-19,051 | 23.1-28.9x | 0.002197 |
| Context shoulder | 12 | 6-8 | 21-35 | 3.1-4.8x | 0.000122 |
| Overlapping points | 6 | 26-36 | 405-422 | 12.8-15.6x | 0.000565 |

On the global procedural scenes, the worst original crest miss falls from
8.644287 m to 0.001953 m, at 42.1-54.2 times the original station count. Rotated
regional detail falls from 1.514771 m to 0.002197 m at 23.1-28.9 times the count.
The context cases gain no measured crest accuracy from the added probes. The
four regional-transition scenes with completed loose trials already capture
the reference extrema in their original profiles, yet the midpoint criterion
still demands extra work and never completes at 0.01 m. This is useful evidence
against applying the heuristic uniformly.

All 146 completed real-field trials (52 + 52 + 42) stay within their requested
threshold against the factor-256 reference and miss none of the selected
above-level, below-level or uphill decisions. No baseline/adaptive sample cap
or reference cap was reached in this matrix; the largest reference has 181,249
stations. The bounded-failure regressions separately exercise those caps.
The ten depth failures at 0.01 m are four horizontal regional-transition
scenes and six 4000 km overlapping-point scenes.

The eight precision failures are diagonal/oblique regional profiles with
positive anchor intervals approximately 1.4e-14 to 2.5e-13 km long. Their
midpoints round to an endpoint. This exposes a coordinate-representation limit,
not a geographic barrier; the prototype leaves it unresolved. Coincident
anchors are handled separately as zero-length intervals. Any future certified
method needs an explicit rounding policy as well as a terrain bound.

The existing uniform/shifted controls retain their factor-128 reference;
adaptive trials use their own factor-256 reference. Compare the original and
adaptive errors against the latter, not across differently sampled references.
Neither reference is continuous ground truth. The runner records generation and
comparison time and process memory, but comparison time includes all uniform
controls, all thresholds and reference evaluations. Sample multipliers above
are not runtime speed ratios or estimates of total project cost.

## Verification and evidence

- Full pytest: **509 passed in 233.17 s**. The focused uniform/adaptive profile
  suite passed all 42 checks. The 24 new regression cases cover false convergence,
  curved extrema, exact shared stations, coincident anchors, budget/depth/precision
  exhaustion, unavailable references, invalid/nonpointwise ground, CLI control
  validation, output preservation and fresh-process repeatability.
- Ruff passed for the repository; strict Pyright reported zero errors or warnings.
- All 137 local Markdown links in the six changed documentation files resolve;
  the final diff passes whitespace checks.

The full matrix preserved the input hashes, all 27 numeric-product hashes,
water-review identity and complete uniform/shifted control evidence for all
60 scenes shared with the preceding detail/context replay. Adaptive results
also matched between fresh-process repeats. The helper refactor does not alter
existing comparison results. Source/runtime hashes are checked before and
after measurement; no heavy tests or build jobs ran concurrently with it.

Engine source fingerprint remains
`fa0c985857d9646781feb6e974b956dfb35ea9dae6357fbf62cb75713113f4bc`.
Runtime: Windows 11 AMD64, CPython 3.14.7, NumPy 2.5.2, Shapely 2.1.2 / GEOS
3.13.1, Rasterio 1.5.1 / GDAL 3.12.4, Pillow 12.3.0. Engine code and export
behavior did not change, so the [preceding build verification](2026-09-13-water-budget-forecast.md)
remains the relevant production-build evidence. No workbench or Tharkeniss Veld
rebuild was performed in this research slice.

Ignored local evidence:

- `artifacts/adaptive-profile-matrix-final-20260913.json`: 120-run corrected matrix;
  SHA-256 `7c5b3713248d84a5648a6dd99ed560bcdc1d63de1e2a8f5f30ef535fdeb02641`.
- `artifacts/adaptive-profile-summary-final-20260913.json`: outcome/error/work summary and prior-output equality;
  SHA-256 `339f2c1fe61853a3fc08224a6fe22b49c31d3564e4f2d86f710e3cb5c1e73200`.
- `artifacts/adaptive-profile-precision-20260913.json`: positive collapsed-midpoint interval measurements;
  SHA-256 `b925de70ca3f9ba3e640b7236519b896c9d3722362d12887c555c12b26eda7ec`.
- `artifacts/analyze_adaptive_profile.py`: summary and unchanged-control verification helper;
  SHA-256 `94141729a13011ce19d1cea0a853ac607086dd956bbaa2a28bb37a2c98121cd3`.

The initial matrix identified coincident anchors incorrectly treated as
precision failures by the prototype. The final helper retains both anchors and
skips only their zero-length interval, with a dedicated regression; the full
matrix was rerun after that fix. Initial runs remain in
`artifacts/adaptive-profile-matrix-20260913.json`; final figures above use only
the corrected run. Generated artifacts are not committed.

## Next work

1. Evaluate conservative interval bounds for field components and their actual
   composition, including rounding. Measure tightness, evaluation cost and
   unresolved outcomes on these fixtures before choosing a certified adaptive
   solver. A height-maximum bound alone also does not establish ordered-rise or
   two-dimensional connectivity bounds.
2. Broaden adversarial and physical-scale cases: shifted/blended peaks, grazing
   paths, octave/roughness changes and narrow off-grid passages. Preserve
   original stations and explicit exhaustion. Raising sample or depth limits
   does not repair an invalid stopping rule.
3. Measure many-lake/many-constraint planning, total requested/unique work,
   scratch memory and diagnostic serialization before changing network limits
   or adding an index. Then define controlling-sill/storage semantics for lake
   chains and reviewed breach/reroute proposals.

The current Python implementation remains suitable for these experiments.
Neither a language rewrite nor a heuristic clearance shortcut resolves the
missing mathematical and workload evidence.
