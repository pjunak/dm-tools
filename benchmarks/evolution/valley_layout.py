"""Bounded relocation of explicitly automatic river guides around hard targets."""

from dataclasses import dataclass
from math import ceil, isfinite

import numpy as np
from numpy.typing import NDArray
from shapely.affinity import scale
from shapely.geometry import LineString, Point, box

from benchmarks.evolution.network import RiverNetwork
from benchmarks.evolution.network_fixture import NetworkFixture

LAYOUT_MODEL_ID = "hard-target-guide-layout@1"


@dataclass(frozen=True, slots=True)
class LayoutSettings:
    clearance_m: float = 1000.0
    corridor_m: float = 1500.0
    amplitude_step_m: float = 100.0
    station_spacing_m: float = 250.0
    maximum_length_ratio: float = 1.25

    def __post_init__(self) -> None:
        for value in (
            self.clearance_m,
            self.corridor_m,
            self.amplitude_step_m,
            self.station_spacing_m,
            self.maximum_length_ratio,
        ):
            if isinstance(value, bool) or not isfinite(value) or value <= 0:
                raise ValueError("Guide layout scales must be finite and positive.")
        if (
            self.maximum_length_ratio < 1
            or self.amplitude_step_m > self.corridor_m
            or self.corridor_m / self.amplitude_step_m > 32
        ):
            raise ValueError("Guide search needs at most 32 amplitudes and a length ratio >= 1.")


class NoAdmissibleLayout(ValueError):
    """The finite candidate family failed; this is not geometric infeasibility."""

    def __init__(self, edge: int, reason: str, rejected: dict[str, int] | None = None):
        super().__init__(reason)
        self.edge = edge
        self.rejected = dict(rejected or {})


@dataclass(frozen=True, slots=True)
class GuideMove:
    original_edge: int
    amplitude_m: float
    side: int
    original_length_m: float
    length_m: float
    minimum_pin_clearance_m: float
    maximum_displacement_m: float


@dataclass(frozen=True, slots=True)
class GuideLayout:
    network: RiverNetwork
    source_network_identity: str
    original_node_count: int
    original_movable_edges: NDArray[np.bool_]
    original_edge_for_node: NDArray[np.int64]
    settings: LayoutSettings
    moves: tuple[GuideMove, ...]
    candidates_checked: int


def relocate_guides(
    f: NetworkFixture,
    *,
    movable_edges: NDArray[np.bool_],
    settings: LayoutSettings | None = None,
) -> GuideLayout:
    """Preserve every original vertex and topology; insert bounded curved detours.

    Only an explicit automatic-edge mask permits relocation. A hard height has
    a conservative spatial clearance policy here, not an invented geological
    exclusion zone. All acceptance checks concern the actual piecewise-linear
    guide, including between stations. The finite per-edge search is greedy;
    exhaustion cannot prove that no other layout exists.
    """
    settings = settings or LayoutSettings()
    original = f.network
    movable = np.array(movable_edges, copy=True)
    if (
        movable.dtype != np.bool_
        or movable.shape != original.receivers.shape
        or np.any(movable & ~original.required)
    ):
        raise ValueError("Layout needs an explicit boolean automatic-edge mask.")
    if np.count_nonzero(original.required) > 64:
        raise ValueError("Guide layout is bounded to 64 original edges.")
    domain = box(0, 0, f.source.grid.width_m, f.source.grid.height_m)
    divide = scale(f.protected_divide_km, xfact=1000, yfact=1000, origin=(0, 0))
    pins = tuple(Point(xy) for xy in f.hard.points_m)
    current = original
    owners = np.where(original.required, np.arange(len(original.receivers)), -1).tolist()
    moves: list[GuideMove] = []
    checked = 0
    for edge in np.flatnonzero(original.required):
        a = int(edge)
        b = int(original.receivers[a])
        p, q = original.coordinates_m[[a, b]]
        initial = LineString([p, q])
        if not domain.covers(initial) or initial.intersects(divide):
            raise ValueError("Original guides must stay inside the domain and outside the divide.")
        clearance = min((initial.distance(pin) for pin in pins), default=float("inf"))
        if clearance >= settings.clearance_m:
            continue
        if not movable[a]:
            raise NoAdmissibleLayout(a, "Clearance conflicts with a fixed guide; it was not moved.")
        if any(
            min(Point(p).distance(pin), Point(q).distance(pin)) < settings.clearance_m
            for pin in pins
        ):
            raise NoAdmissibleLayout(a, "Fixed guide endpoints are inside the clearance policy.")
        capacity = 256 - len(current.receivers)
        if settings.station_spacing_m < initial.length / (capacity + 1):
            raise ValueError("Guide layout would exceed 256 network nodes.")
        pieces = ceil(initial.length / settings.station_spacing_m)
        t = np.linspace(0.0, 1.0, pieces + 1)
        d = q - p
        normal = np.array([-d[1], d[0]]) / initial.length
        rejected: dict[str, int] = {}
        selected: tuple[RiverNetwork, GuideMove] | None = None
        # A quadratic transverse bump returns exactly to the fixed endpoints.
        # Every new segment lies in the convex corridor of this original edge.
        for amplitude in np.arange(
            settings.amplitude_step_m,
            settings.corridor_m + settings.amplitude_step_m * 0.5,
            settings.amplitude_step_m,
        ):
            if amplitude > settings.corridor_m:
                break
            candidates: list[tuple[float, int, RiverNetwork, GuideMove]] = []
            for side in (-1, 1):
                checked += 1
                path = p + t[:, None] * d
                path += side * amplitude * 4 * t[:, None] * (1 - t[:, None]) * normal
                path[0], path[-1] = p, q
                geometry = LineString(path)
                separation = min(geometry.distance(pin) for pin in pins)
                reason = ""
                if separation < settings.clearance_m:
                    reason = "pin_clearance"
                elif geometry.length > settings.maximum_length_ratio * initial.length:
                    reason = "path_length"
                elif not domain.covers(geometry) or geometry.intersects(divide):
                    reason = "domain_or_divide"
                if reason:
                    rejected[reason] = rejected.get(reason, 0) + 1
                    continue
                coords = np.vstack((current.coordinates_m, path[1:-1]))
                added = np.arange(len(current.receivers), len(coords), dtype=np.int64)
                if not len(added):
                    rejected["no_interior_stations"] = rejected.get("no_interior_stations", 0) + 1
                    continue
                receivers = np.concatenate((current.receivers, np.concatenate((added[1:], [b]))))
                receivers[a] = added[0]
                try:
                    network = RiverNetwork(coords, receivers)
                except ValueError:
                    rejected["graph_intersection"] = rejected.get("graph_intersection", 0) + 1
                    continue
                displacement = max(initial.distance(Point(xy)) for xy in path)
                if displacement > settings.corridor_m + 1e-8:
                    raise RuntimeError("Constructed guide escaped its declared corridor.")
                move = GuideMove(
                    a,
                    float(amplitude),
                    side,
                    initial.length,
                    geometry.length,
                    separation,
                    displacement,
                )
                candidates.append((geometry.length, side, network, move))
            if candidates:
                _, _, network, move = min(candidates, key=lambda v: v[:2])
                selected = network, move
                break
        if selected is None:
            raise NoAdmissibleLayout(
                a, "No candidate in the bounded guide family was admitted.", rejected
            )
        network, move = selected
        owners.extend([a] * (len(network.receivers) - len(current.receivers)))
        current = network
        moves.append(move)
    owner_array = np.array(owners, dtype=np.int64)
    owner_array.flags.writeable = False
    movable.flags.writeable = False
    return GuideLayout(
        current,
        original.identity(),
        len(original.receivers),
        movable,
        owner_array,
        settings,
        tuple(moves),
        checked,
    )
