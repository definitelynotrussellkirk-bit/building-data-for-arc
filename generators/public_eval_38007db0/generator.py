#!/usr/bin/env python3
"""Fresh scenes for the public parent 38007db0 row-outlier rule.

Each separator-bounded tile row contains one complete tile that differs from all
of its repeated peers.  The canonical rule extracts those outlier tiles and
stacks them in source-row order while preserving the horizontal separator
bands.  This file is deliberately self-contained so native workers can relocate
it without the authoring workspace.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import random

GENERATOR_ID = TASK_ID = "public_eval_38007db0"
RULE_TASK_ID = "ee_38007db0"
VERSION = "1.0.0"
RULE_HASH = "30cc410873d4"
SUMMARY = (
    "In each separator-bounded tile row, retain the sole tile that differs "
    "from the repeated tile, then stack the retained tiles vertically."
)
INVARIANTS = [
    "complete outer separator frame",
    "uniform tile shape and separator thickness",
    "one outlier and otherwise identical tiles in every tile row",
    "canonical output preserves source-row order",
]
AXES = {}

DEMO_PROFILES = (
    (3, 3, 5, 5, 1),
    (3, 4, 5, 5, 1),
    (4, 3, 4, 5, 1),
    (4, 4, 4, 4, 1),
    (5, 3, 4, 5, 1),
    (5, 4, 4, 4, 1),
)
QUERY_PROFILES = (
    (4, 4, 5, 5, 1),
    (4, 3, 6, 5, 1),
    (3, 5, 6, 4, 1),
    (4, 4, 5, 5, 2),
)
ALL_PROFILES = DEMO_PROFILES + QUERY_PROFILES


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_grid(grid):
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 for value in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")


def _runs(indices):
    if not indices:
        return []
    result = []
    start = previous = indices[0]
    for value in indices[1:]:
        if value != previous + 1:
            result.append((start, previous))
            start = value
        previous = value
    result.append((start, previous))
    return result


def _gaps(runs):
    return [
        (left[1] + 1, right[0] - 1)
        for left, right in zip(runs, runs[1:])
        if left[1] + 1 <= right[0] - 1
    ]


def _tile(grid, row_interval, col_interval):
    r0, r1 = row_interval
    c0, c1 = col_interval
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _key(tile):
    return tuple(tuple(row) for row in tile)


def _analyze(grid):
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    separator = grid[0][0]
    row_runs = _runs(
        [r for r in range(height) if all(grid[r][c] == separator for c in range(width))]
    )
    col_runs = _runs(
        [c for c in range(width) if all(grid[r][c] == separator for r in range(height))]
    )
    if (
        len(row_runs) < 3
        or len(col_runs) < 4
        or row_runs[0][0] != 0
        or row_runs[-1][1] != height - 1
        or col_runs[0][0] != 0
        or col_runs[-1][1] != width - 1
    ):
        raise ValueError("need outer separator frame and at least two tile rows by three columns")
    row_intervals, col_intervals = _gaps(row_runs), _gaps(col_runs)
    if len(row_intervals) != len(row_runs) - 1 or len(col_intervals) != len(col_runs) - 1:
        raise ValueError("separator runs must alternate with nonempty tile bands")
    row_heights = {r1 - r0 + 1 for r0, r1 in row_intervals}
    col_widths = {c1 - c0 + 1 for c0, c1 in col_intervals}
    if len(row_heights) != 1 or len(col_widths) != 1:
        raise ValueError("all tile bands must have a common shape")
    tile_height, tile_width = next(iter(row_heights)), next(iter(col_widths))
    if tile_height < 2 or tile_width < 2:
        raise ValueError("tiles must be at least 2x2")

    records = []
    for row_index, row_interval in enumerate(row_intervals):
        tiles = [_tile(grid, row_interval, interval) for interval in col_intervals]
        keys = [_key(tile) for tile in tiles]
        counts = Counter(keys)
        unique_keys = [key for key, count in counts.items() if count == 1]
        repeated_keys = [key for key, count in counts.items() if count == len(tiles) - 1]
        if len(counts) != 2 or len(unique_keys) != 1 or len(repeated_keys) != 1:
            raise ValueError("each tile row must contain one outlier and otherwise identical tiles")
        unique_key, repeated_key = unique_keys[0], repeated_keys[0]
        unique_column = keys.index(unique_key)
        difference_count = sum(
            a != b
            for row_a, row_b in zip(unique_key, repeated_key)
            for a, b in zip(row_a, row_b)
        )
        if difference_count <= 0:
            raise ValueError("outlier must differ from repeated tile")
        repeated_frequency = Counter(value for row in repeated_key for value in row)
        maximum = max(repeated_frequency.values())
        backgrounds = [color for color, count in repeated_frequency.items() if count == maximum]
        if len(backgrounds) != 1:
            raise ValueError("repeated tile background must be uniquely modal")
        background = backgrounds[0]
        foreground_count = sum(value != background for row in unique_key for value in row)
        records.append(
            {
                "row_index": row_index,
                "unique_column": unique_column,
                "unique": [list(row) for row in unique_key],
                "repeated": [list(row) for row in repeated_key],
                "difference_count": difference_count,
                "foreground_count": foreground_count,
                "tiles": tiles,
            }
        )
    return {
        "separator": separator,
        "row_intervals": row_intervals,
        "tile_width": tile_width,
        "left_separator_width": row_runs[0][1] - row_runs[0][0] + 1,
        "right_separator_width": col_runs[-1][1] - col_runs[-1][0] + 1,
        "col_runs": col_runs,
        "rows": records,
        "height": height,
    }


def _render_source_rows(grid):
    info = _analyze(grid)
    left_width = info["col_runs"][0][1] - info["col_runs"][0][0] + 1
    output_width = left_width + info["tile_width"] + info["right_separator_width"]
    out = [[info["separator"]] * output_width for _ in range(info["height"])]
    for destination_index, row_interval in enumerate(info["row_intervals"]):
        r0, _ = row_interval
        chosen = info["rows"][destination_index]["unique"]
        for dr, source_row in enumerate(chosen):
            out[r0 + dr][left_width : left_width + info["tile_width"]] = source_row[:]
    return out


def _rng(seed, index):
    raw = hashlib.sha256(f"38007db0-row-outlier-v1:{seed}:{index}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _rank_order(values):
    return tuple(sorted(range(len(values)), key=lambda i: (-values[i], i)))


def _make_scene(seed, index, profile):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, 2**31 - 1, "sample_index")
    rows_count, cols_count, tile_height, tile_width, separator_width = profile
    height = rows_count * tile_height + (rows_count + 1) * separator_width
    width = cols_count * tile_width + (cols_count + 1) * separator_width
    if height > 30 or width > 30:
        raise ValueError("profile exceeds ARC limits")
    rng = _rng(seed, index)
    separator, background, ink = rng.sample(range(10), 3)
    area = tile_height * tile_width
    foreground_limit = max(3, area // 2 - 1)

    for _ in range(10000):
        deltas = list(range(1, rows_count + 1))
        rng.shuffle(deltas)
        if _rank_order(deltas) in (tuple(range(rows_count)), tuple(reversed(range(rows_count)))):
            continue
        foregrounds = rng.sample(range(2, foreground_limit + 1), rows_count)
        directions = [1 if (row + index) % 2 == 0 else -1 for row in range(rows_count)]
        repeated_counts = []
        for foreground, delta, direction in zip(foregrounds, deltas, directions):
            repeated = foreground - delta if direction == 1 else foreground + delta
            if not 1 <= repeated <= foreground_limit:
                break
            repeated_counts.append(repeated)
        else:
            difference_order = _rank_order(deltas)
            foreground_desc_order = _rank_order(foregrounds)
            foreground_asc_order = tuple(
                sorted(range(rows_count), key=lambda row: (foregrounds[row], row))
            )
            if difference_order in (foreground_desc_order, foreground_asc_order):
                continue
            if foreground_desc_order in (
                tuple(range(rows_count)),
                tuple(reversed(range(rows_count))),
            ):
                continue
            break
    else:
        raise RuntimeError("unable to construct independent difference/foreground rankings")

    positions = [(r, c) for r in range(tile_height) for c in range(tile_width)]
    difference_order = _rank_order(deltas)
    for _ in range(1000):
        unique_columns = list(range(cols_count))
        rng.shuffle(unique_columns)
        while len(unique_columns) < rows_count:
            extra = list(range(cols_count))
            rng.shuffle(extra)
            unique_columns.extend(extra)
        unique_columns = unique_columns[:rows_count]
        column_order = tuple(
            sorted(range(rows_count), key=lambda row: (unique_columns[row], row))
        )
        if column_order not in (tuple(range(rows_count)), difference_order):
            break
    else:
        raise RuntimeError("unable to separate source, difference, and column rankings")

    row_tiles = []
    seen = set()
    seen_unique = set()
    for row_index in range(rows_count):
        delta = deltas[row_index]
        unique_fg = foregrounds[row_index]
        direction = directions[row_index]
        for _ in range(1000):
            unique_mask = set(rng.sample(positions, unique_fg))
            if direction == 1:
                changed = set(rng.sample(sorted(unique_mask), delta))
                repeated_mask = unique_mask - changed
            else:
                zeros = sorted(set(positions) - unique_mask)
                changed = set(rng.sample(zeros, delta))
                repeated_mask = unique_mask | changed
            unique_key = tuple(sorted(unique_mask))
            key = (unique_key, tuple(sorted(repeated_mask)))
            if key not in seen and unique_key not in seen_unique:
                seen.add(key)
                seen_unique.add(unique_key)
                break
        else:
            raise RuntimeError("tile mask construction exhausted")
        unique_tile = [
            [ink if (r, c) in unique_mask else background for c in range(tile_width)]
            for r in range(tile_height)
        ]
        repeated_tile = [
            [ink if (r, c) in repeated_mask else background for c in range(tile_width)]
            for r in range(tile_height)
        ]
        tiles = [copy.deepcopy(repeated_tile) for _ in range(cols_count)]
        tiles[unique_columns[row_index]] = unique_tile
        row_tiles.append(tiles)

    grid = [[separator] * width for _ in range(height)]
    for tile_row, tiles in enumerate(row_tiles):
        r0 = separator_width + tile_row * (tile_height + separator_width)
        for tile_col, tile in enumerate(tiles):
            c0 = separator_width + tile_col * (tile_width + separator_width)
            for dr, row in enumerate(tile):
                grid[r0 + dr][c0 : c0 + tile_width] = row
    _analyze(grid)
    return grid


def get_info():
    return {
        "task_id": TASK_ID,
        "generator_id": GENERATOR_ID,
        "version": VERSION,
        "summary": SUMMARY,
        "rule_hash": RULE_HASH,
        "invariants": list(INVARIANTS),
        "axes": dict(AXES),
    }


def generate(seed, sample_index=0, *, difficulty=None, **overrides):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(sample_index, 0, 1_000_000, "sample_index")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    if overrides:
        raise ValueError("this generator exposes no overrides")
    if difficulty == "easy":
        profile = DEMO_PROFILES[sample_index % 2]
    elif difficulty == "medium":
        profile = DEMO_PROFILES[2 + sample_index % 3]
    elif difficulty == "hard":
        profile = QUERY_PROFILES[sample_index % len(QUERY_PROFILES)]
    else:
        profile = ALL_PROFILES[sample_index % len(ALL_PROFILES)]
    return _make_scene(seed, sample_index, profile)


def generate_input(ctx):
    return generate(ctx.seed, ctx.sample_index, difficulty=getattr(ctx, "difficulty", None))


def self_check(grid):
    try:
        _analyze(grid)
        return []
    except (ValueError, TypeError, IndexError) as exc:
        return [str(exc)]


def rule_mirror(grid):
    return _render_source_rows(grid)
