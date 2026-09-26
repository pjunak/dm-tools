"""Whole-tributary head transitions for the bounded valley experiment."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from benchmarks.evolution.network import RiverNetwork
from benchmarks.evolution.paths import FloatArray

BOUNDARY_MODEL_ID = "head-mouth-valley-sections@1"


@dataclass(frozen=True, slots=True)
class HeadTransition:
    head: int
    stop_node: int
    length_m: float
    lower_at_head_m: float
    lift_at_head_m: float


def head_transitions(
    network: RiverNetwork,
    segment_edges: NDArray[np.int64],
    segments_m: FloatArray,
    beds_m: FloatArray,
    lower_at_heads_m: FloatArray,
    bank_rise_m: float,
) -> tuple[FloatArray, tuple[HeadTransition, ...]]:
    """Lift a clipped generated head, fading to zero at its first confluence.

    The linear taper adds a constant grade, avoiding a steeper middle section
    through bends. It ends at the shared bed, with no change downstream of the
    first confluence; subdivision cannot change its physical length. This is a
    construction hypothesis, not a proof that every bank fits the envelope.
    Complete local and delivered profiles must still be measured.
    """
    incoming = np.bincount(network.receivers[network.required], minlength=len(network.receivers))
    result = beds_m.copy()
    records: list[HeadTransition] = []
    for head, lower in zip(network.heads(), lower_at_heads_m, strict=True):
        first = int(np.flatnonzero(segment_edges == head)[0])
        deficit = max(0.0, float(lower - beds_m[first, 0]))
        if deficit == 0.0:
            continue
        route = network.route(int(head))
        junctions = np.flatnonzero(incoming[route[1:]] > 1)
        if len(junctions):
            route = route[: int(junctions[0]) + 2]
        lengths = np.linalg.norm(np.diff(network.coordinates_m[route], axis=0), axis=1)
        total = float(lengths.sum())
        lift = deficit + bank_rise_m
        travelled = 0.0
        for edge, length in zip(route[:-1], lengths, strict=True):
            ids = np.flatnonzero(segment_edges == edge)
            start, stop = network.coordinates_m[[edge, network.receivers[edge]]]
            tangent = (stop - start) / length
            distance = travelled + (segments_m[ids] - start) @ tangent
            fade = np.clip(1.0 - distance / total, 0.0, 1.0)
            result[ids] += lift * fade
            travelled += float(length)
        records.append(HeadTransition(int(head), int(route[-1]), total, float(lower), lift))
    return result, tuple(records)
