# Reproducible terrain seeds

The Seed row in the workbench now includes **Original terrain** and
**Independent stages**. Changing this choice changes generated terrain even
when the numeric seed stays the same. The original behavior remains the
default. Opening a project restores its saved behavior; saving preserves it.
Use a new project filename when comparing the two policies.

The public [named-seed example](../examples/terrain/named-seeds.dmterrain.json)
opts in explicitly. Build it with the usual command and a fresh directory:

```powershell
.\.venv\Scripts\dmtools.exe terrain build examples/terrain/named-seeds.dmterrain.json --output artifacts/named-seed-build
```

## Version compatibility

| Choice | Project/build version | Effective seed |
|---|---|---|
| Original terrain | 1 | Master seed passed directly to coordinate noise |
| Independent stages | 2 | Stable hash of master seed and stage identifier |

Version 1 retains its strict original settings fields. Version 2 requires
`settings.seed_policy = "named-stage-sha256@1"`. Missing or unsupported policies
are errors, never inferred defaults. Selecting the original policy again saves
version 1. Both loaders are supported; older applications reject version 2.
The version-1 schema files remain unchanged.

The Python `TerrainSettings` default is also the original policy. Callers opt
in with `seed_policy=NAMED_SEED_POLICY` from `dmtools.terrain.domain.seeds`.
The master seed must be a genuine unsigned 32-bit integer; booleans and
floating-point values are rejected.

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
`[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*`. They are compatibility identifiers, not
translated display names. Renaming an existing stage or changing seed
encoding requires a new explicit policy/algorithm contract.

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

The version-2 build records the master in `settings.seed`, policy in both
settings and algorithms, and resolved values in
`algorithms.stage_seeds`, currently containing only `terrain.relief`.
The version-1 manifest retains its original full/macro seed fields.
Schemas validate structure; consumers checking provenance must also verify
that recorded derived values match the declared master and policy.

For offline validation, register all four project/build v1/v2 schemas from
[`schemas/terrain/`](../schemas/README.md) by their `$id` values. Version 2
reuses immutable version-1 definitions through local URN references.

Exact terrain reproduction still depends on algorithms, settings, geometry,
and the recorded runtime. Portable seed derivation alone does not guarantee
identical floating-point terrain across platforms. See the
[build guide](terrain-builds.md) and
[ADR-0026](adr/0026-version-named-terrain-stage-seeds.md).
