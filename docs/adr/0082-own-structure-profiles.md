# ADR-0082: Own ridge and valley profiles on their source lines

- Status: accepted
- Date: 2026-09-27
- Extends the existing authored structure and longitudinal profile pipeline.

## Decision

Add immutable `StructureProfileKnot(position, elevation_m)` values to each
`TerrainStructure.profile`. An empty tuple retains ordinary base/point-guided
behavior. A nonempty tuple contains 2-64 strictly ordered knots, includes 0 and
1, and follows normalized arc length of the smoothed metric centreline. Heights
or relief/depth magnitudes are finite and nonnegative; absolute valley floors
cannot rise downstream. Absolute heights obey the terrain ceiling.

Prepare these knots directly into the existing longitudinal interpolation.
Explicit profiles own their line and are excluded from proximity-based point
attachment. Independent absolute height points keep final authority; existing
cross-structure mixing, downstream no-fill behavior and sea-level constraints
remain. This is explicit structural guidance, not a network equality solver.

Keep the typed contract in `domain/structure_profiles.py`, interpolation in the
existing pipeline module and the dialog in `structure_profile_ui.py`. The
selected-instruction action applies one history entry. Cancel does not mutate
inputs or completed terrain. Elevation-mode changes require clearing the profile.

Use shape-preserving interpolation already present in the engine rather than
introducing a second spline implementation. Add local water-sampling density at
one quarter of the shortest profile interval, bounded spatially by the existing
line influence context and operationally by the water sampling limits. This
retains narrow-pass evidence without promising continuous hydrological validity.

## Current-format cutover

Use terrain project v8, input snapshot v3, build v19 and regional samples v3.
Every serialized ridge/valley requires a `profile` array. Advance the generator
to `coastline-constraint-terrain@19`; no random stream changes. Update examples,
replay/schema references and current guides, and remove superseded schemas.
World geology and prepared-world source payloads are unchanged; their references
to unchanged landform/coastline definitions move to the current schema owners.
No compatibility loader or format migration is added.

## Evidence and limits

The [implementation report](../research/2026-09-27-line-owned-terrain-profiles.md)
records the public example, numeric saddle and downstream checks, independent
point authority, saved-parent replay, GUI tests and measured limitations.
Automatic spurs, explicit graph junction solving, broad terrain realism and
physical history remain separate work. In particular, a desired line target can
shift where another ridge or valley also influences the ground.
