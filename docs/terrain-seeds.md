# Reproducible terrain seeds

All terrain generation uses `named-stage-sha256@1`. The workbench exposes one
numeric master Seed; there is no seed-policy selector or direct-master mode.
The public [example](../examples/terrain/example.dmterrain.json) uses the same
implementation as programmatic calls and headless builds.

Only current project format 3 and build format 4 are supported. Older saves
are rejected and must be recreated. Current settings store the master seed;
the build records the seed algorithm and resolved stage seeds. Future changes
may replace this behavior without compatibility modes or migrations.

The master must be an unsigned 32-bit integer; booleans and floating-point
values are rejected. Python callers use `stage_seed(master_seed, stage_id)`
from `dmtools.terrain.domain.seeds`.

## Stable stage identity

There is currently one stochastic stage, `terrain.relief`. Its full-detail
and coarse evaluations use the same resolved seed because they are two views
of one field. Splitting them into unrelated fields would change the meaning
of the restored residual detail. Routing and constraint conditioning are
currently deterministic and do not need artificial random streams.

Future stochastic processes must use distinct stable names. Derivation takes
no stage index, execution order, resolution, mutable random generator, time or
process environment. Inserting or reordering an unrelated stage cannot change
an existing derived seed. This does not promise unchanged output if a new
process deliberately modifies that stage's inputs.

Names use 1-128 ASCII characters matching
`[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*`. These identify processes in build records, not
translated display names. Record algorithm changes when renaming a stage or
changing seed encoding; update current tests and examples together.

## Byte contract for another implementation

For `named-stage-sha256@1`, concatenate:

1. ASCII `dmtools.terrain-stage-seed@1`, followed by one zero byte;
2. the unsigned master seed in exactly four bytes, most significant byte first;
3. the ASCII stage name, without a trailing terminator.

Calculate SHA-256, take its first four digest bytes, and interpret them as an
unsigned integer, most significant byte first. No Python `hash()` or RNG is
involved. The existing coordinate noise and octave hashing are unchanged.
The result has 32 bits; collisions are possible, so this is deterministic
stream separation rather than a guarantee that every name has a unique seed.

These reference values were independently calculated with .NET SHA256:

| Master seed | `terrain.relief` | `test.rainfall` (test identifier only) |
|---:|---:|---:|
| 0 | 1845932015 | 1509020038 |
| 42 | 2355644248 | 3354607557 |
| 20260902 | 3486507418 | 3681552239 |
| 4294967295 | 380401938 | 377551747 |

The current build records the master in `settings.seed`, the derivation ID in
`algorithms.seed_policy`, and resolved values in `algorithms.stage_seeds`,
currently containing only `terrain.relief`. Schemas validate structure;
consumers checking provenance must also verify that derived values match the
recorded master and algorithm.

For offline validation, register the current project and build schemas from
[`schemas/terrain/`](../schemas/README.md) by their `$id` values. No historical
schema is needed.

Exact terrain reproduction still depends on algorithms, settings, geometry,
and the recorded runtime. Portable seed derivation alone does not guarantee
identical floating-point terrain across platforms. See the
[build guide](terrain-builds.md) and
[current development policy](adr/0027-develop-current-behavior-without-legacy-support.md).
