"""Fixed physical river geometry for the constrained-surface experiment."""

from dataclasses import dataclass
from hashlib import sha256

import numpy as np
from numpy.typing import NDArray
from shapely.geometry import LineString, Point

from benchmarks.evolution.metrics import terminal_labels
from benchmarks.evolution.paths import FloatArray


@dataclass(frozen=True, slots=True)
class RiverNetwork:
    coordinates_m: FloatArray
    receivers: NDArray[np.int64]

    def __post_init__(self) -> None:
        xy = np.array(self.coordinates_m, dtype=np.float64, copy=True)
        r = np.array(self.receivers, copy=True)
        if (
            xy.ndim != 2
            or xy.shape[1] != 2
            or not 2 <= len(xy) <= 256
            or r.shape != (len(xy),)
            or r.dtype != np.int64
            or not np.all(np.isfinite(xy))
            or len(np.unique(xy, axis=0)) != len(xy)
        ):
            raise ValueError("Network requires 2-256 distinct finite xy nodes and int64 receivers.")
        terminal_labels(r)
        edges = np.flatnonzero(r >= 0)
        if not edges.size:
            raise ValueError("Network needs at least one required river edge.")
        # This small authored fixture has one embedded planar graph. Crossings
        # must be explicit shared nodes; a geometric intersection cannot invent a junction.
        for i, a in enumerate(edges):
            first = LineString(xy[[a, r[a]]])
            for b in edges[i + 1 :]:
                crossing = first.intersection(LineString(xy[[b, r[b]]]))
                shared = {int(a), int(r[a])} & {int(b), int(r[b])}
                if not crossing.is_empty and not (
                    len(shared) == 1 and crossing.equals(Point(xy[next(iter(shared))]))
                ):
                    raise ValueError("Physical river edges cross without an explicit junction.")
        for name, value in (("coordinates_m", xy), ("receivers", r)):
            value.flags.writeable = False
            object.__setattr__(self, name, value)

    @property
    def required(self) -> NDArray[np.bool_]:
        return self.receivers >= 0

    def heads(self) -> NDArray[np.int64]:
        incoming = np.bincount(self.receivers[self.required], minlength=len(self.receivers))
        return np.flatnonzero(self.required & (incoming == 0))

    def route(self, head: int) -> NDArray[np.int64]:
        if not 0 <= head < len(self.receivers) or not self.required[head]:
            raise ValueError("A route must start on the required network.")
        nodes = [head]
        while self.receivers[nodes[-1]] >= 0:
            nodes.append(int(self.receivers[nodes[-1]]))
        return np.array(nodes, dtype=np.int64)

    def points(self, nodes: NDArray[np.int64]) -> tuple[FloatArray, FloatArray]:
        xy = self.coordinates_m[nodes]
        return xy[:, 0], xy[:, 1]

    def identity(self) -> str:
        return sha256(
            self.coordinates_m.astype("<f8").tobytes() + self.receivers.astype("<i8").tobytes()
        ).hexdigest()
