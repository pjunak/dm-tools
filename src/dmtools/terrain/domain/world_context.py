"""Cell-centred full-sphere geography, distinct from local terrain node grids."""

from dataclasses import dataclass
from math import cos, pi, sin

from dmtools.terrain.domain.world import WorldFrame

WORLD_CONTEXT_ALGORITHM = "spherical-geography-v1"
MAX_CONTEXT_ROWS = 360
MIXED_COAST = 1
SPLIT_WATER = 2
SUBCELL_LAND = 4
SUBCELL_WATER = 8


@dataclass(frozen=True, slots=True)
class WorldContextSettings:
    latitude_cells: int = 180

    def __post_init__(self) -> None:
        if type(self.latitude_cells) is not int or not 4 <= self.latitude_cells <= MAX_CONTEXT_ROWS:
            raise ValueError(
                f"Context latitude cells must be an integer from 4 to {MAX_CONTEXT_ROWS}."
            )

    @property
    def longitude_cells(self) -> int:
        return 2 * self.latitude_cells


@dataclass(frozen=True, slots=True)
class SphericalContextGrid:
    frame: WorldFrame
    settings: WorldContextSettings

    @property
    def shape(self) -> tuple[int, int]:
        return self.settings.latitude_cells, self.settings.longitude_cells

    @property
    def angular_step_deg(self) -> float:
        return 180 / self.settings.latitude_cells

    @property
    def north_south_spacing_km(self) -> float:
        return pi * self.frame.radius_km / self.settings.latitude_cells

    def latitude_deg(self, row: int) -> float:
        return 90 - (row + 0.5) * self.angular_step_deg

    def longitude_deg(self, column: int) -> float:
        return (
            self.frame.central_meridian_deg + (column + 0.5) * self.angular_step_deg
        ) % 360 - 180

    def cell_area_km2(self, row: int) -> float:
        # The sine difference is written as a product to retain polar precision.
        half = pi / (2 * self.settings.latitude_cells)
        latitude = pi / 2 - (row + 0.5) * 2 * half
        return self.frame.radius_km**2 * 4 * half * cos(latitude) * sin(half)


@dataclass(frozen=True, slots=True)
class ConnectedWater:
    id: int
    area_km2: float
    crosses_seam: bool
    displayed_cells: int
