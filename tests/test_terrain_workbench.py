"""Undo/redo owns authored inputs and never accepts a generated surface."""

from dataclasses import replace

import pytest

from dmtools.terrain.domain import ElevationPoint
from dmtools.terrain.workbench import InstructionHistory

POINT = ElevationPoint((0.5, 0.5), 1200, 80)


def test_instruction_history_restores_properties_deletion_and_clear_in_order() -> None:
    history = InstructionHistory()
    history.append(POINT)
    snapshot = history.constraints
    changed = replace(POINT, elevation_m=1800)
    history.replace(0, changed)
    history.append(replace(POINT, position=(0.2, 0.3)))
    before_delete = history.constraints
    history.delete(0)
    history.commit(())
    history.undo()
    assert len(history.constraints) == 1
    history.undo()
    assert history.constraints == before_delete
    history.undo()
    assert history.constraints == (changed,)
    history.undo()
    assert history.constraints == snapshot == (POINT,)
    history.redo()
    assert history.constraints == (changed,)
    assert snapshot == (POINT,)


def test_new_edit_discards_redo_but_noop_keeps_it() -> None:
    history = InstructionHistory((POINT,))
    history.delete(0)
    history.undo()
    history.replace(0, POINT)
    assert history.can_redo
    history.replace(0, replace(POINT, elevation_m=500))
    assert not history.can_redo
    history.redo()
    assert history.constraints[0] == replace(POINT, elevation_m=500)


def test_open_project_starts_a_new_history() -> None:
    history = InstructionHistory()
    history.append(POINT)
    history.undo()
    history.reset((POINT,))
    assert not history.can_undo and not history.can_redo
    history.undo()
    history.redo()
    assert history.constraints == (POINT,)


@pytest.mark.parametrize("index", [-1, 1, 10])
def test_invalid_selection_cannot_modify_inputs(index: int) -> None:
    history = InstructionHistory((POINT,))
    with pytest.raises(IndexError):
        history.delete(index)
    with pytest.raises(IndexError):
        history.replace(index, POINT)
    assert history.constraints == (POINT,) and not history.can_undo
