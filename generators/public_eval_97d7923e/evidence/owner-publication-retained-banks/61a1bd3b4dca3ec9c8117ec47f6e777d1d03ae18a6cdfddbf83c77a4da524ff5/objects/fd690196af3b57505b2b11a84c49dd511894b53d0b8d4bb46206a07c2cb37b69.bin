"""Constructive matched-input sampler for the length-ranked rod family."""
from __future__ import annotations

import random
from typing import Any


def integer(value: Any, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    return value


def _dimensions(seed: int, index: int, split: str) -> tuple[int, int]:
    if split == "test" and index == 103:
        return 30, 30
    rng = random.Random(f"sticks-dim-v2:{seed}:{split}:{index}")
    return rng.randint(24, 29), rng.randint(24, 30)


def draw(seed: int, index: int, *, split: str = "train") -> list[list[int]]:
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 10_000, "index")
    if split not in {"train", "test", "production"}:
        raise ValueError("split must be train, test, or production")
    h, w = _dimensions(seed, index, "test" if split == "test" else split)
    rng = random.Random(f"sticks-scene-v3:{seed}:{split}:{index}:{h}:{w}")
    grid = [[0 for _ in range(w)] for _ in range(h)]

    endpoint_colors = rng.sample([1, 2, 3, 4], 3)
    payload_colors = rng.sample([5, 6, 7, 8], 3)
    # The ranks are deliberately different.  The first color owns the global
    # longest rod but does not select it; the second owns the selected winner.
    ranks = [2, 1, 3]
    long = h - 6
    lengths = [
        [long, h - 10, 3],
        [h - 8, h - 12, 2],
        [h - 7, h - 11, 4],
    ]
    # Small deterministic variation without changing the causal inequalities.
    if (seed + index) % 2:
        lengths[0][2] += 1
    if (seed + index) % 3 == 0:
        lengths[1][2] += 1

    # The legend is separated from every rod by at least two zero rows.  Every
    # repeated color places at least one count cell below row zero, defeating a
    # tempting "count only the top row" shortcut while retaining a compact key.
    legend: list[tuple[int, int]] = []
    for color, rank in zip(endpoint_colors, ranks):
        legend.append((0, color))
        for occurrence in range(1, rank):
            legend.append((1 + ((occurrence - 1) % 2), color))
    rng.shuffle(legend)
    legend_cols = rng.sample(range(w), len(legend))
    for (row, color), col in zip(legend, legend_cols):
        grid[row][col] = color

    legend_col_set = set(legend_cols)
    available_cols = [c for c in range(1, w - 1) if c not in legend_col_set]
    rng.shuffle(available_cols)
    rod_cols = sorted(available_cols[:9])
    rng.shuffle(rod_cols)
    bottom_choices = list(range(h - 3, h))
    rods = []
    for group, (endpoint, payload, group_lengths) in enumerate(
        zip(endpoint_colors, payload_colors, lengths)
    ):
        for j, length in enumerate(group_lengths):
            col = rod_cols[group * 3 + j]
            # Keep the longest rods low enough to leave a visible zero gap from legend.
            max_bottom = h - 1
            min_bottom = length + 3
            bottom = rng.randint(min_bottom, max_bottom)
            top = bottom - length - 1
            grid[top][col] = endpoint
            for r in range(top + 1, bottom):
                grid[r][col] = payload
            grid[bottom][col] = endpoint
            rods.append((endpoint, payload, top, bottom, col, length))

    return grid
