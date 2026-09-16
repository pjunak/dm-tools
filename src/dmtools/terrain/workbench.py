"""Input editing state for the workbench; generated surfaces are never editable."""

from dataclasses import dataclass, field

from dmtools.terrain.domain import Coastline, TerrainConstraint, TerrainSettings


@dataclass(frozen=True, slots=True)
class GenerationInputs:
    """The exact input snapshot used by a background generation request."""

    coastline: Coastline
    settings: TerrainSettings
    constraints: tuple[TerrainConstraint, ...]


@dataclass(slots=True)
class InstructionHistory:
    """Reversible edits of immutable authored inputs, scoped to one open project."""

    constraints: tuple[TerrainConstraint, ...] = ()
    _undo: list[tuple[TerrainConstraint, ...]] = field(
        default_factory=list[tuple[TerrainConstraint, ...]], init=False)
    _redo: list[tuple[TerrainConstraint, ...]] = field(
        default_factory=list[tuple[TerrainConstraint, ...]], init=False)

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def reset(self, constraints: tuple[TerrainConstraint, ...] = ()) -> None:
        self.constraints = constraints
        self._undo.clear()
        self._redo.clear()

    def commit(self, constraints: tuple[TerrainConstraint, ...]) -> None:
        if constraints == self.constraints:
            return
        self._undo.append(self.constraints)
        self.constraints = constraints
        self._redo.clear()

    def append(self, constraint: TerrainConstraint) -> None:
        self.commit((*self.constraints, constraint))

    def replace(self, index: int, constraint: TerrainConstraint) -> None:
        if not 0 <= index < len(self.constraints):
            raise IndexError("No instruction at this index.")
        self.commit((*self.constraints[:index], constraint, *self.constraints[index + 1:]))

    def delete(self, index: int) -> None:
        if not 0 <= index < len(self.constraints):
            raise IndexError("No instruction at this index.")
        self.commit((*self.constraints[:index], *self.constraints[index + 1:]))

    def undo(self) -> None:
        if self._undo:
            self._redo.append(self.constraints)
            self.constraints = self._undo.pop()

    def redo(self) -> None:
        if self._redo:
            self._undo.append(self.constraints)
            self.constraints = self._redo.pop()
