# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false
# pyright: reportArgumentType=false, reportOptionalMemberAccess=false
"""Read one continuous closed coastline from a simple SVG document."""

from dataclasses import dataclass
from hashlib import file_digest
from math import hypot
from pathlib import Path as FilePath

import numpy as np
from shapely.geometry import Polygon
from shapely.validation import explain_validity
from svgelements import SVG, Path, Shape

from dmtools.terrain.domain import Coastline


class CoastlineInputError(ValueError):
    """The imported vector cannot serve as the one supported coastline."""


@dataclass(frozen=True, slots=True)
class CoastlineSource:
    """A parsed coastline and the fingerprint of its authoritative SVG source."""

    path: FilePath
    sha256: str
    coastline: Coastline

    def __post_init__(self) -> None:
        if not self.path.is_absolute():
            raise ValueError("Coastline source path must be absolute.")
        invalid_character = any(
            character not in "0123456789abcdef" for character in self.sha256
        )
        if len(self.sha256) != 64 or invalid_character:
            raise ValueError("Coastline source SHA-256 is invalid.")


def coastline_sha256(source: FilePath) -> str:
    """Fingerprint a coastline source without loading the whole file into memory."""

    try:
        with source.open("rb") as stream:
            return file_digest(stream, "sha256").hexdigest()
    except OSError as error:
        raise CoastlineInputError(f"Could not read SVG: {error}") from error


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

    positions = np.linspace(0.0, 1.0, sample_count, endpoint=False, dtype=np.float64)
    length_error = max(1e-6, longest_span * 1e-6)
    sampled_array = np.asarray(path.npoint(positions, error=length_error), dtype=np.float64)
    if sampled_array.shape != (sample_count, 2) or not np.all(np.isfinite(sampled_array)):
        raise CoastlineInputError("The coastline could not be sampled into finite coordinates.")
    sampled = [(float(x), float(y)) for x, y in sampled_array]
    sampled.append(sampled[0])

    polygon = Polygon(sampled)
    if polygon.area <= 0:
        raise CoastlineInputError("The coastline encloses no area.")
    if not polygon.is_valid:
        raise CoastlineInputError(f"The coastline is not a valid loop: {explain_validity(polygon)}")

    return Coastline(points=tuple(sampled), source_name=source.name)


def load_svg_coastline_source(source: FilePath) -> CoastlineSource:
    """Load a coastline with stable source provenance for project persistence."""

    try:
        resolved = source.resolve(strict=True)
    except OSError as error:
        raise CoastlineInputError(f"Could not read SVG: {error}") from error
    before = coastline_sha256(resolved)
    coastline = load_svg_coastline(resolved)
    after = coastline_sha256(resolved)
    if before != after:
        raise CoastlineInputError("The SVG changed while it was being imported; import it again.")
    return CoastlineSource(path=resolved, sha256=after, coastline=coastline)
