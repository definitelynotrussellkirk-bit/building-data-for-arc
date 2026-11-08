"""Semantic model and constructive sampler for public parent 45a5af55.

The authoritative executable is the adjacent Racket program.  This module is a
small independent oracle used for generated labels and source-level tests; it
never reads ARC fixtures.
"""
from __future__ import annotations

from typing import Iterable

from puzzle_generators.base import gen_ctx

TASK = "public_eval_45a5af55"
VERSION = "1.0.0"


def validate(grid: list[list[int]]) -> None:
    if (
        type(grid) is not list
        or not 3 <= len(grid) <= 16
        or any(type(row) is not list for row in grid)
        or not grid
        or not 1 <= len(grid[0]) <= 30
        or any(len(row) != len(grid[0]) for row in grid)
        or any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row)
    ):
        raise ValueError("expected a rectangular 3..16 by 1..30 exact-integer color grid")
    if any(any(value != row[0] for value in row) for row in grid):
        raise ValueError("every input row must be monochromatic")
    if grid[-1] != grid[-2]:
        raise ValueError("the final row must duplicate the preceding center stripe")


def layer_colors(grid: list[list[int]]) -> list[int]:
    validate(grid)
    return [row[0] for row in grid[:-1]]


def runs(values: Iterable[int]) -> list[tuple[int, int, int]]:
    seq = list(values)
    if not seq:
        return []
    answer: list[tuple[int, int, int]] = []
    start = 0
    for index in range(1, len(seq) + 1):
        if index == len(seq) or seq[index] != seq[start]:
            answer.append((start, index - start, seq[start]))
            start = index
    return answer


def longest_run_start(values: Iterable[int]) -> int:
    records = runs(values)
    if not records:
        raise ValueError("at least one layer is required")
    # max() would select the latest tie; explicit scan preserves the earliest.
    best = records[0]
    for record in records[1:]:
        if record[1] > best[1]:
            best = record
    return best[0]


def solve(grid: list[list[int]], scope: str = "full") -> list[list[int]]:
    if scope not in ("full", "from_longest_run"):
        raise ValueError("scope must be 'full' or 'from_longest_run'")
    layers = layer_colors(grid)
    if scope == "from_longest_run":
        layers = layers[longest_run_start(layers) :]
    side = 2 * len(layers)
    return [
        [layers[min(r, c, side - 1 - r, side - 1 - c)] for c in range(side)]
        for r in range(side)
    ]


_PROFILES: tuple[tuple[int, ...], ...] = (
    (1, 3, 1, 2),       # seven layers; longest run begins after an outer layer
    (2, 1, 4, 1),       # eight layers; a different crop depth
    (1, 2, 4, 1, 2),
    (2, 1, 3, 2, 1),
    (1, 4, 2, 3, 1),
    (2, 3, 1, 5, 1),
    (3, 1, 2, 4, 3),
    (2, 4, 1, 3, 4),
)
_QUERY_PROFILES: dict[int, tuple[int, ...]] = {
    100: (1, 3, 2, 4),
    101: (2, 1, 4, 2, 3),
    102: (1, 4, 2, 3, 3),
    103: (2, 5, 3, 1, 4),
}


def _profile(index: int) -> tuple[int, ...]:
    if index in _QUERY_PROFILES:
        return _QUERY_PROFILES[index]
    return _PROFILES[index % len(_PROFILES)]


def sample_input(seed: int, index: int, *, stress: bool = False) -> list[list[int]]:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")

    ctx = gen_ctx(seed=seed, sample_index=index, version=VERSION, task_id=TASK)
    profile = _profile(index)
    colors = list(ctx.draw_distinct_colors("layer-run-colors", n=len(profile)))
    # Rotation makes neighboring source indices visually independent while the
    # run-length profile remains the structural teaching variable.
    rotation = ctx.draw_int("palette-rotation", 0, len(colors) - 1)
    colors = colors[rotation:] + colors[:rotation]
    layers = [color for color, length in zip(colors, profile) for _ in range(length)]
    if len(layers) > 15:
        raise RuntimeError("internal profile exceeds the 30x30 output limit")

    is_stress = stress or index == 103
    width = 30 if is_stress else ctx.draw_int("stripe-width", 5, 29)
    grid = [[color] * width for color in layers]
    grid.append(grid[-1][:])
    validate(grid)
    return grid


def analyze(grid: list[list[int]]) -> dict[str, object]:
    layers = layer_colors(grid)
    return {
        "layers": layers,
        "runs": runs(layers),
        "longest_run_start": longest_run_start(layers),
        "canonical_side": 2 * len(layers),
    }
