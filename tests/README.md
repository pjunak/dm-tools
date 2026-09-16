# Tests

The suite checks observable domain, adapter, generation and build contracts with
small deterministic fixtures. Run the full pytest, Ruff and strict Pyright gates
from [the repository instructions](../AGENTS.md) for runtime/schema changes.

Current coverage includes:

- strict current project/schema validation, SVG hashes, atomic saves, per-tool
  settings and display-free Tcl control behavior;
- instruction history plus real Tk selection/property editing, immutable generated
  references, settings/worker freshness and regeneration from changed inputs;
- multipart coast dissolution, islands/holes, cross-water rejection, local-frame
  round trips, endpoint grids and portable named stage seeds;
- absolute/relative anchors, brush strength, shape-preserving point-anchored
  ridge/valley profiles, downstream floors, regional recipes and incision caps;
- MFD accumulation, D8 topology, initiation, Strahler order, bounded corrections,
  basin labels/spill routes and overlapping final-channel conflict evidence;
- authored lake/dry retention, captured-area conservation, eligible outlet
  transfer, exact flats, contained links, finer shorelines and full outlet paths;
- narrow feature guidance, internal wet/dry barriers, alternate paths, cumulative
  rises, complete-budget rejection and canonical Float32 endpoint agreement; and
- headless builds, all numeric archives, GeoTIFF point registration/masks,
  repeatable hashes, diagnostics and completion-last publication failures.

Sampling tests compare the selective evaluator with a dense reference and check
exact shared local-metric nodes across nested output grids, chunk boundaries,
regions and authored water. These are point-sample guarantees, not cell-average
equivalence. No completed-map editing workflow is supported.

Prefer numeric invariants over large binary golden files. Full visible desktop
flows and external desktop GIS acceptance require separate inspection; Tcl tests
alone do not establish those workflows. `test_terrain_ui.py` uses an actual Tk
root and skips where no display is available; it does not replace visual inspection.

The [benchmark harness](../benchmarks/README.md) measures fresh-process stage
time, native peak memory and numerical identities separately from correctness
tests. Its tests cover repeatability and report publication. Do not add fragile
machine-dependent timing assertions to the correctness suite.
