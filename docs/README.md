# Documentation

The documentation is split by purpose:

- [`architecture/`](architecture/README.md) describes the current system and
  the intended dependency direction.
- [`adr/`](adr/README.md) records decisions, alternatives, and consequences.
- [`research/`](research/README.md) contains dated evidence and prototype
  recommendations that have not yet become architecture decisions.
- [`DEPENDENCIES.md`](DEPENDENCIES.md) records runtime packages, purposes, and
  licenses.
- Tool-specific usage and data contracts live beside each tool; start with the
  [terrain tool guide](../src/dmtools/terrain/README.md).
- The [terrain tool roadmap](../TODO.md) separates planned features, numerical
  result improvements, and UI/UX work.

Architecture documentation describes the current design. ADRs preserve why a
decision was made and are not rewritten merely because the implementation later
changes. Research notes may be superseded as prototypes produce measurements;
accepted contracts should be promoted into an ADR.
