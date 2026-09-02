# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false
# pyright: reportArgumentType=false, reportOptionalMemberAccess=false
"""Read one continuous closed coastline from a simple SVG document."""

from math import hypot
from pathlib import Path as FilePath

from shapely.geometry import Polygon
from shapely.validation import explain_validity
from svgelements import SVG, Path, Shape

from dmtools.terrain.domain import Coastline


class CoastlineInputError(ValueError):
    """The imported vector cannot serve as the one supported coastline."""


def _same_point(first: tuple[float, float], second: tuple[float, float], tolerance: float) -> bool:
    return hypot(first[0] - second[0], first[1] - second[1]) <= tolerance


def load_svg_coastline(source: FilePath, *, sample_count: int = 4_096) -> Coastline:
    """Load exactly one closed drawable shape and flatten it for generation."""

    if source.suffix.lower() != ".svg":
        raise CoastlineInputError("The first version accepts SVG files only.")
    if sample_count < 32:
        raise ValueError("sample_count must be at least 32.")

    try:
        document = SVG.parse(str(source), reify=True, on_error="raise")
    except (OSError, ValueError, TypeError) as error:
        raise CoastlineInputError(f"Could not read SVG: {error}") from error

    shapes = [element for element in document.elements() if isinstance(element, Shape)]
    if len(shapes) != 1:
        raise CoastlineInputError(
            f"Expected exactly one drawable vector object; found {len(shapes)}."
        )

    path = Path(shapes[0])
    path.reify()
    if path.count_subpaths() != 1:
        raise CoastlineInputError("The coastline must contain exactly one continuous subpath.")
    if len(path) < 2 or path.first_point is None or path.current_point is None:
        raise CoastlineInputError("The coastline path is empty.")

    bbox = path.bbox()
    if bbox is None:
        raise CoastlineInputError("The coastline has no measurable bounds.")
    min_x, min_y, max_x, max_y = (float(value) for value in bbox)
    longest_span = max(max_x - min_x, max_y - min_y)
    tolerance = max(1e-9, longest_span * 1e-9)
    first = (float(path.first_point.x), float(path.first_point.y))
    last = (float(path.current_point.x), float(path.current_point.y))
    if not _same_point(first, last, tolerance):
        raise CoastlineInputError("The coastline is open; join its final node to its first node.")

    sampled: list[tuple[float, float]] = []
    for index in range(sample_count):
        point = path.point(index / sample_count)
        sampled.append((float(point.x), float(point.y)))
    sampled.append(sampled[0])

    polygon = Polygon(sampled)
    if polygon.area <= 0:
        raise CoastlineInputError("The coastline encloses no area.")
    if not polygon.is_valid:
        raise CoastlineInputError(f"The coastline is not a valid loop: {explain_validity(polygon)}")

    return Coastline(points=tuple(sampled), source_name=source.name)
