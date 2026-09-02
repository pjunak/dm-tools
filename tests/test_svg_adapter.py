from pathlib import Path

import pytest

from dmtools.terrain.adapters.svg import CoastlineInputError, load_svg_coastline

FIXTURES = Path(__file__).parent / "fixtures" / "terrain"


def test_loads_one_closed_svg_shape() -> None:
    coastline = load_svg_coastline(FIXTURES / "closed-coast.svg", sample_count=256)

    assert coastline.points[0] == coastline.points[-1]
    assert len(coastline.points) == 257
    assert coastline.source_name == "closed-coast.svg"


@pytest.mark.parametrize(
    ("filename", "message"),
    [
        ("open-coast.svg", "open"),
        ("two-objects.svg", "exactly one"),
        ("self-intersecting.svg", "not a valid loop"),
    ],
)
def test_rejects_unsupported_coastlines(filename: str, message: str) -> None:
    with pytest.raises(CoastlineInputError, match=message):
        load_svg_coastline(FIXTURES / filename, sample_count=256)


def test_rejects_non_svg_input(tmp_path: Path) -> None:
    source = tmp_path / "coast.txt"
    source.write_text("not svg", encoding="utf-8")

    with pytest.raises(CoastlineInputError, match="SVG files only"):
        load_svg_coastline(source)
