# Basin and spill review

**Implemented:** derived basin geometry and representative escape routes.
**Authored water:** lake levels, outlets and dry-basin footprints now have a
[separate authoring contract](terrain-water.md). Nested depression hierarchy
and automatic channel reconciliation remain unimplemented.

## One review grid

Basin and channel diagnostics now use the same 257-longest-side endpoint grid.
The finished terrain is evaluated at those nodes and rounded to Float32 before
analysis, matching the numeric terrain field. Priority-Flood operates on a copy.
Changing output resolution does not change these review nodes or basin IDs.
The separate 129-node diagnostic evaluation has been removed.

`canonical_drainage` in `diagnostics.json` records algorithm
`canonical-d8-priority-flood-diagnostics@4`, spacing, tolerances and candidates.
The archive's `routing_sha256` binds those records to `routing.npz`; its coordinates
locate all flat indices with `row, column = divmod(index, grid_width)`.
These are sampled review products, not a guarantee about every delivered DEM cell.

## Extents and representative outlets

The significant-fill threshold is 0.01 m. Eight-connected above-threshold nodes
form a candidate; zero in `basin_labels` means no significant depression.
Candidates are ranked by descending maximum fill depth, then descending fill
volume, then row-major deepest node. One-based IDs match labels and `B1`, `B2`,
etc. in the review. IDs belong to a generated result, not persistent authored
features: changing inputs can change ranks.

Each record stores the deepest node, the lowest original node (both with
row-major exact-tie resolution), floor, depth, area, fill volume and terminal
count. Area uses node count times x/y spacing; volume sums fill depth times
that area divided by 1000. These coarse support-cell estimates are not surveyed
shorelines, exact polygon areas or available water volumes.

The representative outlet follows the deepest node's conditioned D8 receivers:

1. `source_flat_index` and `receiver_flat_index` identify the first edge leaving
   that candidate's significant-fill extent.
2. `spill_flat_index` is the highest **original terrain** node from that source
   through the downstream terminal; the nearest exact maximum wins ties.
3. `spill_elevation_m` is that original height, without representable flood steps.
4. `terminal_flat_index` and its overlapping `boundary_flags` describe where the
   conditioned route ends.

`exit_edge_count` counts all conditioned D8 edges leaving the extent. The selected
route is deterministic, not the unique or necessarily preferred lake outlet.
All exits can be recovered by comparing receiver labels in the numeric archive.
A component may contain nested depressions, multiple spill levels or multiple
exits. It is not a nested hierarchy, watershed or a flat lake surface. The first
extent exit may precede the terrain saddle; these locations are intentionally
separate. A conditioned route can rise on the unfilled DEM.

## Numeric arrays

All arrays below share the routing grid and are derived:

| Array | Contract |
|---|---|
| `basin_labels` | UInt32; zero outside significant depressions; positive candidate ID |
| `conditioned_final_elevation_m` | Float64 Priority-Flood copy of finished terrain; zero outside land |
| `conditioned_final_receivers` | Int64 D8 flat receivers for that copy; -1 at terminals and non-land |
| `final_fill_depth_m` | Float64 required fill in metres; zero outside land; includes sub-threshold steps |
| `nonland_class` | UInt8; 0 land, 1 exterior non-land, 2 enclosed non-land |
| `boundary_flags` | UInt8 on land; 1 grid edge, 2 adjacent exterior non-land, 4 adjacent enclosed non-land |

Non-land classification uses eight-neighbour raster connectivity: exterior means
connected to a raster edge. Flags may overlap. Narrow inlets or small holes can
vanish or change connectivity at this resolution; classification does not assert
SVG topology, ocean salinity, an ocean level or authored lake intent. Existing
diagnostic routing still accepts all three boundary kinds at their terrain
elevations. Planning additionally terminates at authored retention nodes; its
receiver graph is distinct from this diagnostic copy.

## Display and water-authoring boundary

**Drainage review** now toggles basin extents alongside planned channels in the
workbench. Purple shows extents; white circles mark the eight deepest candidates;
yellow lines and diamonds show their representative routes and spill points.
IDs match the numeric records. `drainage.png` has four panels including the same
basin overlay. Standard relief exports omit diagnostic overlays; cartographic relief also
shows explicitly authored lake water.

The [authored-water slice](terrain-water.md) now implements lake levels, optional
outlets and dry-basin footprints with automatic-cut protection. It keeps these
concepts separate:

- Exterior ocean/open boundaries, including declared levels where required.
- Enclosed SVG gaps, which remain unspecified non-land until classified.
- Authored lakes with a footprint, water level and explicit draining/closed mode.
- Authored dry or endorheic basins whose retention intent prevents forced exits.

Lake and dry-basin constraints are current project fields. Ocean levels and
classification of SVG gaps remain future work. Review shoreline/anchor conflicts
before adopting an outlet; breaching and rerouting still need downstream validation.
See [ADR-0033](adr/0033-map-basin-spill-candidates.md) and the
[research](research/2026-09-10-basin-outlet-topology.md).
