import pytest

from dmtools.cli import main


def test_root_help_is_available(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "terrain" in capsys.readouterr().out


def test_terrain_help_is_available(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["terrain"]) == 0
    output = capsys.readouterr().out
    assert "Build and inspect deterministic terrain projects" in output
    assert "gui" in output


def test_terrain_gui_help_is_available(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["terrain", "gui", "--help"])

    assert exit_info.value.code == 0
    assert "closed SVG land shapes" in capsys.readouterr().out
