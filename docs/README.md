# Documentation

## Where to start

1. To use the application, read the
   [terrain tool guide](../src/dmtools/terrain/README.md).
2. To contribute or choose the next implementation, read the
   [current development strategy](strategy/README.md).
3. To understand the present dependency direction and data flow, read the
   [architecture overview](architecture/README.md).
4. To inspect categorized future work, use the
   [terrain tool roadmap](../TODO.md).
5. For public file contracts and runnable inputs, see
   [schemas](../schemas/README.md) and [examples](../examples/README.md).
6. To generate and compare numeric output, use the
   [headless build guide](terrain-builds.md).
7. For source/local conversion, endpoint grids and world-positioning limits,
   read the [coordinate contract](terrain-coordinates.md).
8. For portable named stage seeds, read the
   [seed contract](terrain-seeds.md).

## Document roles and authority

Implemented code, public schemas, tests, and accepted ADRs define current
behavior. The strategy and architecture documents define the current direction.
The roadmap is a categorized backlog rather than an execution sequence. Dated
research preserves evidence and may become stale as packages and measurements
change.

- [`strategy/`](strategy/README.md) gives the current dependency-aware order of
  work and links each phase to its evidence gates.
- [`architecture/`](architecture/README.md) describes the current system and
  intended dependency direction.
- [`adr/`](adr/README.md) preserves accepted decisions, alternatives, and
  consequences; accepted ADRs are append-only history.
- [`research/`](research/README.md) contains dated evidence and prototype
  recommendations that are not architecture decisions.
- [`DEPENDENCIES.md`](DEPENDENCIES.md) records packages and assets actually used
  at runtime, with purposes and licenses.

Promote a selected solver, file-format contract, or external engine into an ADR
and tests. Do not rewrite old research to make it appear that a later decision
was already known.

For numeric GIS exchange and its local-coordinate limits, read the
[GeoTIFF export guide](terrain-geotiff.md).

For regional terrain authoring and its first four recipes, read the
[landform region guide](terrain-regions.md).

For the latest structure, validation and bottleneck review, read the
[2026-09-10 maintenance checkpoint](maintenance/2026-09-10-sanity-and-performance.md).
