# Terrain pipeline

This package will orchestrate explicit, named terrain stages. Each stage will
receive typed inputs, effective configuration, and its own deterministically
derived seed, then return typed outputs and diagnostics.

The implemented generator builds a coordinate-addressed relief field and a
separate low-frequency macro surface. It routes MFD contributing area over a
Priority-Flood-conditioned copy of that macro surface on a fixed canonical
grid, then cuts a bounded, stream-power-inspired automatic valley field. The
incision is sampled in world coordinates, so output resolution does not reroute
the continent's major valleys. When authored constraints exist, the pipeline
then applies broad smooth brush, ridge, valley, and height-point responses and
restores the high-frequency residual. Absolute constraints attenuate that
residual to satisfy world elevations. Relative constraints are deterministic
displacement fields over the surface entering their stage and preserve its
residual relief. The order is brush, ridge, valley, relative point, then exact
absolute point. Same-kind overlaps are order-independent. The coastline remains
a hard zero-elevation boundary.

Absolute height points attached to an absolute ridge or valley define a
shape-preserving longitudinal profile through their projected arc-length
positions. Baseline shoulder knots return isolated authored sections to the
structure target. The controlled centreline can rise or fall through peaks and
passes, while the existing cross-structure weight turns a lower crest anchor
into a saddle. Synthetic crest/floor variation is suppressed inside that
authored span so it cannot overshoot the supplied anchors.

A relative point near a relative structure is attached to the uniquely nearest
compatible line and uses the same longitudinal interpolation. Its signed value
modifies ridge relief as `base relief + displacement` or valley incision as
`base depth - displacement`. An attached point is consumed by the structure
profile and is not applied again as a circular point field. Ambiguous and
unattached relative points retain their free-standing displacement behavior.

Valley vertex order is semantic: the first vertex is upstream and the final
vertex is the outlet. Before chunked raster generation, the pipeline samples
the complete deterministic surface entering the valley stage at metric
positions spaced by at most 2 km, with every authored anchor inserted as an
exact knot. Relative incision profiles are subtracted from this reference. A
cumulative downstream minimum then removes only floor rises; it never raises
the preferred floor. Absolute valleys interpolate non-rising world-height
anchors toward the line's outlet-floor value and reject an uphill hard-anchor
sequence. The prepared profile is independent of output raster resolution and
is reused by every processing chunk.

Automatic drainage is broad terrain structure, not a hydrologic certification.
Its temporary filled surface is never substituted for the DEM, and it currently
routes the generated macro surface before authored structures are reapplied.
It does not yet represent authored lakes, endorheic basins, sediment, lithology,
climate, unique river trees, or river vector export.

MFD accumulation measures broad convergence, while a complementary D8 receiver
tree supplies one generated valley centreline. A logarithmic contributing-area
hierarchy blends narrow channel, near-shoulder, and broad trunk responses so
larger downstream valleys widen at a fixed incision relief. The same canonical
field suppresses fine residual noise most strongly on major floors and tapers
that suppression across shoulders. D8 here is an internal shaping tree, not yet
an exported or validated river product.

The selected D8 tree also receives deterministic Horton-Strahler order. Channel
heads have order one; equal highest-order tributaries increment the downstream
order, while a smaller tributary joining a larger reach does not. The order
raster is retained as typed internal topology, with zero outside the channel
network. It does not currently modify elevation or width: direct order-based
width and centreline-depth experiments regressed the synthetic width fixture or
the coarse Tharkeniss drainage diagnostic. Area and slope therefore remain the
active shaping controls until valley character and confinement are explicit.

The broad response also receives a deliberately small MFD convergence
correction. MFD area is normalized logarithmically above the channel threshold,
raised to a high-order trunk gate, combined with bounded local slope, and added
at 4% strength. This pulls a D8-quantized cross-section toward the continuous
flow minimum without replacing the connected D8 network or its floor
conditioning. The established residual-detail suppression field is unchanged.

Channel initiation combines source area and once-smoothed receiver slope. The
local area threshold follows a bounded `A*S^2` relation: it may fall to 35% of
the base threshold on steep terrain or rise to four times that threshold on
gentle terrain. Initiated cells are closed downstream over the D8 receiver tree,
so large low-gradient trunks remain connected even where they would not
independently satisfy the headwater test. This is a heterogeneous-terrain
heuristic, not a rainfall- or substrate-calibrated channel prediction.
A small logarithmic relief ramp rises from zero to 8% between the minimum
source area and the established area threshold. This makes selected heads
visible without allowing their cross-sections to rival downstream trunks.

The generated floor is checked again after its permitted residual detail is
restored. A stable upstream-to-downstream pass lowers a selected receiver only
when its reconstructed floor would otherwise climb, enforcing a 0.01 m minimum
drop. Correction is limited to 60% of reconstructed local elevation and an
additional 2% of the generation ceiling; cap-limited edges remain explicit
internal diagnostics. This is conservative generated-network conditioning, not
final-DEM filling or authored stream burning.

A second generated-only profile pass checks consecutive channel edges with
normalized steepness `S * A^0.45`. A downstream reach may be up to eight times
the upstream normalized steepness before it is treated as an extreme numerical
knickpoint. The solver lowers only the middle cell, reuses the existing incision
cap, and converges through at most 16 fixed upstream-to-downstream passes.
Ordinary slope variation remains, and bound-limited residuals are reported.
This heuristic does not apply to authored terrain and does not infer uplift,
lithology, waterfall status, erosion rate, or equilibrium.

After all generated and authored shaping, the pipeline re-evaluates the complete
surface on a fixed 129-cell-longest-side diagnostic grid. Strict downhill D8
reports direct outlet connectivity and potential inland terminals. Priority-
Flood runs only on a copy to quantify significant fill cells, maximum fill
depth, estimated volume, and largest conditioned outlet catchment. The compact
summary is resolution-independent and never repairs the authoritative DEM.
Significant fill cells are grouped by 8-connectivity into deterministic coarse
basin candidates. Candidate measurements and preview markers support review;
they are not lake polygons, nested depression trees, or authored constraints.

Free ridge and valley endpoints narrow gradually so authored structures do not
end as blunt walls. When an endpoint meets another structure of the same kind
and elevation mode, the junction keeps its full cross-section instead. A stable
metric tolerance of at most 2 km (and no more than 2% of the narrower structure
radius) recognizes drawing-level contact without making near but separate
features connect. Splitting one authored range or valley into compatible
segments therefore preserves the continuous line's junction cross-section;
minor bounded differences away from the join can remain because distance to a
segmented Shapely geometry is not numerically identical to distance to one
line.

Stages must not depend on implicit process state such as the current directory,
wall-clock time, ambient random generators, or undeclared environment settings.
