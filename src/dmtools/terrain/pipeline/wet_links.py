"""Bounded, batched ground checks for vector-contained internal water links."""

from dataclasses import dataclass
from math import ceil, hypot
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from dmtools.terrain.pipeline.water_sampling import (
    GroundSampler,
    GroundSamplingPlan,
    SamplingFeature,
    plan_ground_profile,
    profile_positions,
    sample_ground_positions,
)

MAX_WET_LINK_SAMPLES = 65_536


@dataclass(frozen=True, slots=True)
class WetLinkEvidence:
    first_flat_index: int
    second_flat_index: int
    sample_count: int
    feature_sample_count: int
    feature_spacing_limit_km: float | None
    maximum_ground_m: float
    maximum_position_km: tuple[float, float]
    blocked: bool


@dataclass(frozen=True, slots=True)
class WetLinkReview:
    status: Literal["sampled", "budget_exceeded"]
    spacing_limit_km: float
    candidate_link_count: int
    requested_sample_count: int
    blocked_link_count: int | None
    contact_reachable_wet_cell_count: int | None
    links: tuple[WetLinkEvidence, ...]


def review_wet_links(
    nodes: NDArray[np.int64], neighbours: NDArray[np.int64], wet: NDArray[np.bool_],
    contact: int, elevation_m: NDArray[np.float64], x_km: NDArray[np.float64],
    y_km: NDArray[np.float64], water_level_m: float, sample_ground: GroundSampler,
    features: tuple[SamplingFeature, ...] = (),
) -> tuple[WetLinkReview, NDArray[np.bool_]]:
    """Inspect each undirected wet link once; reach water only through clear links.

    A lake-wide sample budget is checked before evaluating any link. Endpoint
    samples must agree with the canonical Float32 field. Summary maxima retain
    the decision evidence without exporting a full profile for every clear link.
    """
    count = nodes.size
    local_contact = int(np.searchsorted(nodes, contact))
    if (neighbours.shape != (count, 8) or wet.shape != (count,)
            or local_contact >= count or nodes[local_contact] != contact or not wet[local_contact]):
        raise ValueError("Wet-link review needs matching nodes and a selected wet contact.")
    spacing = min(float(x_km[1] - x_km[0]), float(y_km[1] - y_km[0])) / 4
    sources, directions = np.nonzero((neighbours > np.arange(count)[:, None]) & wet[:, None]
                                     & wet[np.maximum(neighbours, 0)])
    targets = neighbours[sources, directions]
    width = elevation_m.shape[1]
    def coordinate(local: int) -> tuple[float, float]:
        row, column = divmod(int(nodes[local]), width)
        return float(x_km[column]), float(y_km[row])
    vertices = tuple((coordinate(int(a)), coordinate(int(b)))
                     for a, b in zip(sources, targets, strict=True))
    baseline = tuple(1 + max(2, ceil(hypot(b[0]-a[0], b[1]-a[1]) / spacing))
                     for a, b in vertices)
    requested = sum(baseline)
    connected = np.zeros(count, dtype=np.bool_)
    def unresolved() -> tuple[WetLinkReview, NDArray[np.bool_]]:
        return (WetLinkReview("budget_exceeded", spacing, len(vertices), requested,
                              None, None, ()), connected)
    if requested > MAX_WET_LINK_SAMPLES:
        return unresolved()
    plans: list[GroundSamplingPlan] = []
    for pair, base in zip(vertices, baseline, strict=True):
        plan = plan_ground_profile(pair, spacing, features)
        requested += plan.requested_sample_count - base
        if plan.status != "sampled" or requested > MAX_WET_LINK_SAMPLES:
            return unresolved()
        plans.append(plan)
    lengths = np.asarray([p.requested_sample_count for p in plans], dtype=np.int64)
    offsets = np.concatenate((np.zeros(1, dtype=np.int64), np.cumsum(lengths)))
    positions = (np.concatenate([profile_positions(p) for p in plans]) if plans else
                 np.empty((0, 2), dtype=np.float64))
    ground = sample_ground_positions(positions, sample_ground)
    graph = neighbours.copy()
    evidence: list[WetLinkEvidence] = []
    for i, (first, second, direction, plan) in enumerate(
        zip(sources, targets, directions, plans, strict=True)
    ):
        start, end = int(offsets[i]), int(offsets[i+1])
        heights = ground[start:end]
        canonical = elevation_m.ravel()[nodes[[first, second]]].astype(np.float32)
        if not np.array_equal(heights[[0, -1]], canonical):
            raise ValueError("Wet-link samples must match canonical Float32 ground.")
        maximum = start + int(np.argmax(heights))
        blocked = float(ground[maximum]) > water_level_m + .01
        if blocked:
            graph[first, direction] = graph[second, 7-int(direction)] = -1
        evidence.append(WetLinkEvidence(int(nodes[first]), int(nodes[second]), len(heights),
            len(heights) - plan.baseline_sample_count, plan.feature_spacing_limit_km,
            float(ground[maximum]),
            (float(positions[maximum, 0]), float(positions[maximum, 1])), blocked))
    queue = [local_contact]
    connected[local_contact] = True
    while queue:
        for neighbour in graph[queue.pop()]:
            target = int(neighbour)
            if target >= 0 and wet[target] and not connected[target]:
                connected[target] = True
                queue.append(target)
    return (WetLinkReview("sampled", spacing, len(vertices), requested,
                          sum(e.blocked for e in evidence), int(np.count_nonzero(connected)),
                          tuple(evidence)), connected)
