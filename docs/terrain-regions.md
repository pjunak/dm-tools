# Shape terrain with landform regions

Select **Landform region** in the workbench. Choose plain, hills, plateau or
mountains, adjust its controls, click at least three polygon corners and choose
**Finish region** (or right-click). Generate to apply it. Undo removes the last
corner while drawing, then the last committed feature. Region controls apply to
the next polygon; existing regions are currently replaced through undo/redraw.

Try [the regional example](../examples/terrain/landform-regions.dmterrain.json),
which references the same small public coastline as the empty example project.
Regions and the active tool controls are included in project save/open.

## Controls and effects

| Control | Meaning |
|---|---|
| Character | A terrain recipe, independent of climate, biomes and land use |
| Base height | The regional elevation reference in metres before coastal conditioning |
| Relief | Scale of height variation; not a guaranteed peak-to-valley range |
| Feature size | Characteristic size in kilometres; larger values give broader features |
| Transition | Distance inward from the polygon edge over which regional influence reaches full strength |
| Direction | Rotation in the local map plane; 0 degrees is horizontal, 90 is vertical |

Plains use little fine detail. Hills have more local height variation and
texture. Plateaus use a raised, comparatively level interior and a transition
at the region boundary. Mountain belts use elongated ridged relief, varying
crest heights and stronger small-scale detail; direction controls their long
axis. Other recipes rotate their texture without imposing a preferred axis.
These are controllable procedural landforms, not tectonic or erosion simulations.

Changing character loads its starting values. Each saved polygon stores its
complete effective settings. The defaults are:

| Recipe | Base m | Relief m | Feature km | Transition km |
|---|---:|---:|---:|---:|
| Plain | 250 | 100 | 150 | 50 |
| Hills | 700 | 900 | 100 | 70 |
| Plateau | 2200 | 200 | 200 | 40 |
| Mountains | 1000 | 3500 | 120 | 100 |

## Boundaries and authoring priority

A simple polygon may cross the coastline; only land is generated. Holes and
sea keep their existing mask. The region must cover some land and its base
height cannot exceed the global ceiling. Coastline heights remain zero.

Influence is zero at the polygon edge, then increases smoothly inward. Thin
regions may never reach full strength if their transition is wider than their
interior. Adjacent polygon edges retain the background there; overlap regions
when a continuous transition between recipes is desired. Overlaps use a
normalized weighted average in stable order, not last-drawn precedence.
There is no global histogram remapping.

Regions shape the base before brush, ridge, valley and height-point constraints.
The regional base enters relative-valley references, automatic drainage planning
and the final field. Exact height anchors retain their existing authority.
A region can redirect drainage beyond its polygon even though the regional base
itself has no influence outside it.

The new stage uses the named `terrain.landforms` seed. Shared metric coordinates
produce identical values across display resolutions and sampling chunks. The
routing grid remains 257 nodes on its longest axis. The review overlay now draws
thin D8 segments at display size rather than enlarging canonical raster cells;
its topology and uphill-conflict meaning are unchanged. Straight/grid-aligned
routes are still present and should not be mistaken for finished river geometry.

## Regional automatic valleys

Automatic valley depth now follows regional relief. At full regional influence,
its total cutting budget is 15% of relief for plains, 40% for hills, and 25%
for plateaus and mountains. Default plains therefore allow at most 15 m and
plateaus at most 50 m. These are procedural safeguards, not measured erosion
rates or a simulation of rock resistance.

Budgets use the same inward transition and overlap weights as landform shape.
They cannot exceed the global automatic-cut budget. Zero relief at full
influence disables automatic cutting. The initial valley shape is scaled to
this budget; downstream floor and steepness corrections must respect it too.
Authored height points and valleys retain their authority. These limits bound
automatic incision, not the combined effect of authored features, coastal
conditioning and residual-detail suppression.

Shallower cuts can leave more uphill edges in the planned channel graph. The
Drainage review continues to flag these conflicts; increasing cuts until every
filled route is downhill would erase the intended landform. Lake/outlet and
routing reconciliation are still needed. Completion status now reports cut-limit
and depression context counts; the headless build adds a coloured context panel
and numeric edge evidence ([ADR-0032](adr/0032-classify-channel-conflicts.md)). See
[ADR-0031](adr/0031-bound-incision-by-regional-relief.md) for fixture results.

## Current limits

There are no regional sediment, rock-resistance, runoff or drainage-density
controls yet. Lowland-fraction and peak-density targets,
asymmetric escarpments, connected mountain spurs and explicit lakes remain in
[TODO](../TODO.md). Use Drainage review to inspect remaining uphill conflicts.

Only current project/build formats are supported; see the [schema index](../schemas/README.md).
[ADR-0030](adr/0030-author-regional-landforms.md) records the implementation.
