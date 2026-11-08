"""Setting-independent native input banks for column-top selection.

The first three examples construct a plurality, a partial modal tie, and an
all-unique tie.  They teach which cells are counted before color selection.
Only inputs are sampled here.  The adapter computes Python output claims;
protected-Racket qualification and audit execution check those labels.
Every call constructs the complete six-demo/four-query bank, then shuffles all
four queries with its own stream before taking either requested prefix.
"""
from __future__ import annotations

import hashlib
import json
import random


def _rng(seed: int, split: str, slot: int, purpose: str) -> random.Random:
    encoded = json.dumps(
        ["b1e6ee6856bf-native-inputs-v1", seed, split, slot, purpose],
        separators=(",", ":"),
    ).encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(encoded).digest(), "big"))


def _palette(seed: int, split: str, slot: int) -> list[int]:
    colors = list(range(1, 10))
    _rng(seed, split, slot, "palette").shuffle(colors)
    return colors


def _teaching_scatter(seed: int, slot: int) -> list[list[int]]:
    """Keep frequency and connected-component rivals observably different."""
    rng = _rng(seed, "train", slot, "layout")
    a, b, c, d, clutter, *unused = _palette(seed, "train", slot)
    height = rng.randint(10, 14)
    width = rng.randint(13, 14)
    adjacent_row = rng.randint(1, 2)
    if slot == 0:
        # A: four cells in two components; B: three isolated cells.  A has a
        # strict plurality below one half, so neither majority nor component
        # frequency can substitute for counting the column tops.
        skyline = [
            (adjacent_row, 0, a), (adjacent_row, 1, a), (adjacent_row, 2, a),
            (4, 8, a), (0, 4, b), (3, 7, b), (2, 12, b),
            (5, 5, c), (1, 10, c), (4, 9, d),
        ]
        singleton_columns = {9}
    else:
        # Both A and B win; C and D must disappear.  The singleton A is still
        # counted, refuting a rule that silently ignores depth-one columns.
        skyline = [
            (adjacent_row, 0, a), (adjacent_row, 1, a), (4, 8, a),
            (0, 4, b), (3, 7, b), (2, 12, b),
            (5, 5, c), (1, 10, c), (4, 9, d),
        ]
        singleton_columns = {8, 9}
    grid = [[0] * width for _ in range(height)]
    for top, col, color in skyline:
        grid[top][col] = color
        if col in singleton_columns:
            continue
        count = rng.randint(3, min(5, height - top - 1))
        lower_rows = rng.sample(range(top + 1, height), count)
        for row in lower_rows:
            grid[row][col] = clutter
    # A lower A is not a column top: retaining every cell of a selected color
    # gives a different answer even after selecting the correct skyline mode.
    grid[height - 1][4] = a
    if rng.randrange(2):
        grid = [list(reversed(row)) for row in grid]
    return grid


def _canonical_scale(seed: int) -> list[list[int]]:
    rng = _rng(seed, "train", 2, "layout")
    colors = iter(_palette(seed, "train", 2))
    grid = [[0] * 5 for _ in range(5)]
    # Five distinct tops; four distinct lower cells make all nine foreground
    # colors visible.  The depth-three column rejects one-erasure shortcuts.
    columns = list(range(5))
    rng.shuffle(columns)
    row_sets = [(0, 2, 4), (1, 4), (2, 3), (3,), (0,)]
    for col, rows in zip(columns, row_sets):
        for row in rows:
            grid[row][col] = next(colors)
    return grid


def _dense_scatter(seed: int, split: str, slot: int,
                   height: int, width: int, gap_count: int) -> list[list[int]]:
    """Substantive content across all four edges, with varied column tops."""
    rng = _rng(seed, split, slot, "layout")
    palette = _palette(seed, split, slot)
    gaps = set(rng.sample(range(1, width - 1), gap_count))
    columns = [col for col in range(width) if col not in gaps]
    color_count = rng.randint(3, 7)
    colors = palette[:color_count]
    top_colors = [colors[index % color_count] for index in range(len(columns))]
    # Periodic counts are paired with random column assignments, so tops cover
    # ties as well as unique pluralities without making position a color cue.
    rng.shuffle(top_colors)
    top_rows = [rng.randrange(height // 3 + 1) for _ in columns]
    top_rows[:3] = [0, height // 3, max(1, height // 6)]
    grid = [[0] * width for _ in range(height)]
    for col, top, color in zip(columns, top_rows, top_colors):
        grid[top][col] = color
        available = list(range(top + 1, height - 1))
        # At least two thirds of the lower column is occupied.  A bottom cell
        # in every occupied column gives a genuine full-height stress case.
        lower_count = (2 * len(available) + 2) // 3
        lower_count = rng.randint(lower_count, len(available))
        lower_rows = rng.sample(available, lower_count) + [height - 1]
        for row in lower_rows:
            grid[row][col] = rng.choice(palette[:rng.randint(color_count, 9)])
    if (split == "test" and (height, width) == (30, 30)
            and len({top_colors.count(color) for color in colors}) == 1):
        # The maximum-size query must exercise the additional filtering step.
        # Recolor just one top after construction, preserving its geometry,
        # lower scatter, density, and every represented skyline color.
        index = rng.randrange(len(columns))
        replacement = rng.choice([color for color in colors if color != top_colors[index]])
        grid[top_rows[index]][columns[index]] = replacement
    return grid


def _tiny(seed: int) -> list[list[int]]:
    rng = _rng(seed, "test", 0, "layout")
    height, width = rng.choice(((1, 1), (1, 3), (3, 1), (2, 3), (3, 3)))
    colors = _palette(seed, "test", 0)
    return [[rng.choice([0, 0, *colors[:3]]) for _ in range(width)]
            for _ in range(height)]


def _exact_int(name: str, value: int, minimum: int, maximum: int) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be in {minimum}..{maximum}")


def sample_inputs(seed: int, demos: int = 3, queries: int = 4) -> dict:
    """Return fresh unlabeled grids, with stable independent count prefixes."""
    _exact_int("seed", seed, 0, 2**63 - 1)
    _exact_int("demos", demos, 3, 6)
    _exact_int("queries", queries, 1, 4)
    train = [_teaching_scatter(seed, 0), _teaching_scatter(seed, 1),
             _canonical_scale(seed)]
    for slot, (height, width) in enumerate(((9, 15), (17, 20), (20, 23)), start=3):
        train.append(_dense_scatter(seed, "train", slot, height, width, 2))
    test = [
        _tiny(seed),
        _dense_scatter(seed, "test", 1, 14, 18, 2),
        _dense_scatter(seed, "test", 2, 24, 26, 2),
        _dense_scatter(seed, "test", 3, 30, 30, 0),
    ]
    _rng(seed, "test", 0, "presentation").shuffle(test)
    return {"train": train[:demos], "test": test[:queries]}
