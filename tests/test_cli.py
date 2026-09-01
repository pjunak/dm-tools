import pytest

from dmtools.cli import main


def test_root_help_is_available(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "terrain" in capsys.readouterr().out


def test_terrain_help_is_available(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["terrain"]) == 0
    assert "Terrain generation commands" in capsys.readouterr().out
