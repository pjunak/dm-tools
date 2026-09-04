"""Deterministic regular-grid primitives for drainage-guided terrain shaping."""

from heapq import heappop, heappush
from math import hypot

import numpy as np
from numpy.typing import NDArray

_NEIGHBOURS = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)


def priority_flood_surface(
    elevation_m: NDArray[np.float64],
    land_mask: NDArray[np.bool_],
) -> NDArray[np.float64]:
    """Return a routing surface on which every land cell can reach a coast.

    The returned surface is a temporary hydrology product. It fills accidental
    depressions but never replaces the authored/generated elevation surface.
    Raised cells receive the smallest representable downstream grade so flats
    have a deterministic route toward their spill point.
    """

    if elevation_m.shape != land_mask.shape or elevation_m.ndim != 2:
        raise ValueError("Elevation and land mask must be equally shaped 2D arrays.")
    if np.any(land_mask & ~np.isfinite(elevation_m)):
        raise ValueError("Land elevations must be finite before drainage routing.")

    height, width = elevation_m.shape
    filled = elevation_m.copy()
    visited = np.zeros_like(land_mask)
    queue: list[tuple[float, int, int]] = []

    for row, column in np.argwhere(land_mask):
        is_outlet = row in (0, height - 1) or column in (0, width - 1)
        if not is_outlet:
            is_outlet = any(
                not land_mask[row + row_offset, column + column_offset]
                for row_offset, column_offset in _NEIGHBOURS
            )
        if is_outlet:
            visited[row, column] = True
            heappush(queue, (float(filled[row, column]), int(row), int(column)))

    if np.any(land_mask) and not queue:
        raise ValueError("Land mask has no edge or coastline outlet.")

    while queue:
        current_height, row, column = heappop(queue)
        for row_offset, column_offset in _NEIGHBOURS:
            neighbour_row = row + row_offset
            neighbour_column = column + column_offset
            if not (
                0 <= neighbour_row < height
                and 0 <= neighbour_column < width
                and land_mask[neighbour_row, neighbour_column]
                and not visited[neighbour_row, neighbour_column]
            ):
                continue
            visited[neighbour_row, neighbour_column] = True
            original_height = float(filled[neighbour_row, neighbour_column])
            routed_height = max(
                original_height,
                float(np.nextafter(current_height, np.inf)),
            )
            filled[neighbour_row, neighbour_column] = routed_height
            heappush(queue, (routed_height, neighbour_row, neighbour_column))

    if np.any(land_mask & ~visited):
        raise RuntimeError("Priority-Flood left land disconnected from every outlet.")
    return filled


def multiple_flow_accumulation(
    routing_elevation_m: NDArray[np.float64],
    land_mask: NDArray[np.bool_],
    *,
    x_spacing_km: float,
    y_spacing_km: float,
    exponent: float = 1.1,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return MFD contributing area in km2 and maximum local downslope grade.

    Flow is divided among every lower D8 neighbour in proportion to
    ``slope**exponent``. Stable descending ordering and a fixed neighbour order
    make ties reproducible without introducing a mutable random stream.
    """

    if routing_elevation_m.shape != land_mask.shape or routing_elevation_m.ndim != 2:
        raise ValueError("Routing elevation and land mask must be equally shaped 2D arrays.")
    if x_spacing_km <= 0.0 or y_spacing_km <= 0.0 or exponent <= 0.0:
        raise ValueError("Grid spacing and MFD exponent must be positive.")

    height, width = routing_elevation_m.shape
    cell_area_km2 = x_spacing_km * y_spacing_km
    accumulation = np.where(land_mask, cell_area_km2, 0.0).astype(np.float64)
    maximum_slope = np.zeros_like(routing_elevation_m)
    flat_indices = np.flatnonzero(land_mask)
    order = flat_indices[
        np.argsort(-routing_elevation_m.ravel()[flat_indices], kind="stable")
    ]

    for flat_index in order:
        row, column = divmod(int(flat_index), width)
        current_height = float(routing_elevation_m[row, column])
        recipients: list[tuple[int, int, float]] = []
        for row_offset, column_offset in _NEIGHBOURS:
            neighbour_row = row + row_offset
            neighbour_column = column + column_offset
            if not (
                0 <= neighbour_row < height
                and 0 <= neighbour_column < width
                and land_mask[neighbour_row, neighbour_column]
            ):
                continue
            drop_m = current_height - float(
                routing_elevation_m[neighbour_row, neighbour_column]
            )
            if drop_m <= 0.0:
                continue
            distance_km = hypot(
                column_offset * x_spacing_km,
                row_offset * y_spacing_km,
            )
            slope = drop_m / (1_000.0 * distance_km)
            recipients.append((neighbour_row, neighbour_column, slope**exponent))
            maximum_slope[row, column] = max(maximum_slope[row, column], slope)
        if not recipients:
            continue
        total_weight = sum(weight for _row, _column, weight in recipients)
        for neighbour_row, neighbour_column, weight in recipients:
            accumulation[neighbour_row, neighbour_column] += (
                accumulation[row, column] * weight / total_weight
            )

    return accumulation, maximum_slope


def _masked_smooth(
    values: NDArray[np.float64],
    land_mask: NDArray[np.bool_],
    iterations: int,
) -> NDArray[np.float64]:
    result = np.where(land_mask, values, 0.0)
    weights = land_mask.astype(np.float64)
    for _ in range(iterations):
        padded_values = np.pad(result, 1, mode="constant")
        padded_weights = np.pad(weights, 1, mode="constant")
        value_sum = 4.0 * padded_values[1:-1, 1:-1]
        weight_sum = 4.0 * padded_weights[1:-1, 1:-1]
        for row_offset, column_offset in _NEIGHBOURS:
            neighbour_weight = 1.0 if row_offset == 0 or column_offset == 0 else 0.7
            row_slice = slice(1 + row_offset, 1 + row_offset + values.shape[0])
            column_slice = slice(
                1 + column_offset,
                1 + column_offset + values.shape[1],
            )
            value_sum += neighbour_weight * padded_values[row_slice, column_slice]
            weight_sum += neighbour_weight * padded_weights[row_slice, column_slice]
        result = np.divide(
            value_sum,
            weight_sum,
            out=np.zeros_like(value_sum),
            where=weight_sum > 0.0,
        )
        result = np.where(land_mask, result, 0.0)
    return result


def drainage_incision(
    elevation_m: NDArray[np.float64],
    land_mask: NDArray[np.bool_],
    distance_to_coast_km: NDArray[np.float64],
    *,
    x_spacing_km: float,
    y_spacing_km: float,
    maximum_elevation_m: float,
    variability: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Derive broad valley incision and contributing area from a terrain surface."""

    routing_surface = priority_flood_surface(elevation_m, land_mask)
    accumulation_km2, slope = multiple_flow_accumulation(
        routing_surface,
        land_mask,
        x_spacing_km=x_spacing_km,
        y_spacing_km=y_spacing_km,
    )
    cell_area_km2 = x_spacing_km * y_spacing_km
    land_area_km2 = float(np.count_nonzero(land_mask)) * cell_area_km2
    channel_threshold_km2 = max(12.0 * cell_area_km2, 0.0015 * land_area_km2)
    largest_area_km2 = max(
        float(np.max(accumulation_km2, initial=channel_threshold_km2)),
        channel_threshold_km2 * 1.01,
    )
    log_progress = np.clip(
        np.log(np.maximum(accumulation_km2, channel_threshold_km2) / channel_threshold_km2)
        / np.log(largest_area_km2 / channel_threshold_km2),
        0.0,
        1.0,
    )
    channel = accumulation_km2 >= channel_threshold_km2
    channel_slopes = slope[channel]
    reference_slope = (
        max(float(np.percentile(channel_slopes, 90.0)), 0.001)
        if channel_slopes.size
        else 0.001
    )
    slope_factor = np.sqrt(np.clip(slope / reference_slope, 0.0, 1.0))
    stream_power_shape = np.where(
        channel,
        log_progress * (0.45 + 0.55 * slope_factor),
        0.0,
    )
    shoulders = _masked_smooth(stream_power_shape, land_mask, iterations=3)
    valley_shape = 0.58 * stream_power_shape + 0.42 * shoulders
    maximum_depth_m = maximum_elevation_m * (0.035 + 0.085 * variability)
    incision_m = maximum_depth_m * valley_shape
    coastal_gate = np.clip(
        distance_to_coast_km / max(2.0 * max(x_spacing_km, y_spacing_km), 1e-9),
        0.0,
        1.0,
    )
    incision_m *= coastal_gate
    incision_m = np.minimum(incision_m, 0.55 * np.maximum(elevation_m, 0.0))
    return np.where(land_mask, incision_m, 0.0), accumulation_km2
