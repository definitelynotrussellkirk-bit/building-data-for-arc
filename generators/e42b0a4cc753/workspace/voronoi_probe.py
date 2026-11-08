"""Independent oracle and rival probes for task e42b0a4cc753.

This module deliberately does not import the selected generator.  Task tests and
future reviewers can use it to inspect canonical examples, generated inputs, and
specific Manhattan-Voronoi shortcut hypotheses without trusting production code.
"""
from __future__ import annotations

from collections import Counter
from typing import Literal, Sequence

Grid = list[list[int]]
Point = tuple[int, int]
Seed = tuple[int, int, int]
Metric = Literal["manhattan", "euclidean2", "chebyshev"]
TieRule = Literal["reading", "lower_color", "higher_color", "reverse_reading"]


def frame_bbox(grid: Sequence[Sequence[int]]) -> tuple[int, int, int, int]:
    frame = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if not frame:
        raise ValueError("grid contains no color-8 chamber frame")
    return (
        min(r for r, _c in frame),
        min(c for _r, c in frame),
        max(r for r, _c in frame),
        max(c for _r, c in frame),
    )


def seed_cells(grid: Sequence[Sequence[int]]) -> list[Seed]:
    """Return non-background, non-wall cells in row-major order."""
    return [
        (r, c, int(value))
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 8)
    ]


def _distance(point: Point, seed: Seed, metric: Metric) -> int:
    dr = abs(point[0] - seed[0])
    dc = abs(point[1] - seed[1])
    if metric == "manhattan":
        return dr + dc
    if metric == "euclidean2":
        return dr * dr + dc * dc
    if metric == "chebyshev":
        return max(dr, dc)
    raise ValueError(f"unknown metric: {metric!r}")


def nearest_indices(
    grid: Sequence[Sequence[int]],
    *,
    metric: Metric = "manhattan",
    limit: int | None = None,
) -> dict[Point, tuple[int, ...]]:
    seeds = seed_cells(grid)
    if limit is not None:
        seeds = seeds[:limit]
    if not seeds:
        return {}
    r0, c0, r1, c1 = frame_bbox(grid)
    result: dict[Point, tuple[int, ...]] = {}
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            if grid[r][c] != 0:
                continue
            distances = [_distance((r, c), seed, metric) for seed in seeds]
            best = min(distances)
            result[(r, c)] = tuple(
                index for index, distance in enumerate(distances) if distance == best
            )
    return result


def fill(
    grid: Sequence[Sequence[int]],
    *,
    metric: Metric = "manhattan",
    tie: TieRule = "reading",
    limit: int | None = None,
) -> Grid:
    """Apply a nearest-seed rule while preserving the input grid."""
    seeds = seed_cells(grid)
    if limit is not None:
        seeds = seeds[:limit]
    out = [list(row) for row in grid]
    if not seeds:
        return out
    for (r, c), indices in nearest_indices(grid, metric=metric, limit=limit).items():
        candidates = [seeds[index] for index in indices]
        if tie == "reading":
            chosen = min(candidates, key=lambda seed: (seed[0], seed[1]))
        elif tie == "reverse_reading":
            chosen = max(candidates, key=lambda seed: (seed[0], seed[1]))
        elif tie == "lower_color":
            chosen = min(candidates, key=lambda seed: seed[2])
        elif tie == "higher_color":
            chosen = max(candidates, key=lambda seed: seed[2])
        else:
            raise ValueError(f"unknown tie rule: {tie!r}")
        out[r][c] = chosen[2]
    return out


def disagreement_cells(left: Sequence[Sequence[int]], right: Sequence[Sequence[int]]) -> list[Point]:
    return [
        (r, c)
        for r, (left_row, right_row) in enumerate(zip(left, right))
        for c, (a, b) in enumerate(zip(left_row, right_row))
        if a != b
    ]


def owner_counts(grid: Sequence[Sequence[int]], *, metric: Metric = "manhattan") -> Counter[int]:
    counts: Counter[int] = Counter()
    for indices in nearest_indices(grid, metric=metric).values():
        if len(indices) == 1:
            counts[indices[0]] += 1
    return counts


def tie_cells(grid: Sequence[Sequence[int]], *, metric: Metric = "manhattan") -> list[Point]:
    return [
        point
        for point, indices in nearest_indices(grid, metric=metric).items()
        if len(indices) >= 2
    ]


def metric_disagreement_cells(grid: Sequence[Sequence[int]]) -> list[Point]:
    manhattan = nearest_indices(grid, metric="manhattan")
    euclidean = nearest_indices(grid, metric="euclidean2")
    return [point for point in manhattan if manhattan[point] != euclidean[point]]


def lower_color_rival(grid: Sequence[Sequence[int]]) -> Grid:
    return fill(grid, tie="lower_color")


def ignore_after_first_two_rival(grid: Sequence[Sequence[int]]) -> Grid:
    return fill(grid, limit=2)


def euclidean_rival(grid: Sequence[Sequence[int]]) -> Grid:
    return fill(grid, metric="euclidean2")
