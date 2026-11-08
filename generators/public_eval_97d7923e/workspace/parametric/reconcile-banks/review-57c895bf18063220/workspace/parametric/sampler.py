"""Standalone vertical cue/bar generator for public ARC task 97d7923e."""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import random

GENERATOR_ID = TASK_ID = "public_eval_97d7923e"
RULE_TASK_ID = 'ee_97d7923e'
VERSION = "1.0.0"
SUMMARY = "Use each vertical cue height as a one-based rank into matching endpoint bars, then recolor that bar's filler."
INVARIANTS = [
    "dominant background",
    "vertical cue stacks outside bar cells",
    "bars have equal-colored endpoints and a uniform different filler",
    "cue height is a valid one-based bar rank",
]
SETTINGS = ("outer_to_inner", "inner_to_outer")


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _order(value: object) -> str:
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("rank_order must be outer_to_inner or inner_to_outer")
    return value


def _parse_grid(grid: object) -> tuple[list[list[int]], int, int, int]:
    if type(grid) is not list or not 3 <= len(grid) <= 30:
        raise ValueError("grid height must be an exact list in 3..30")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be an exact list in 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("rectangular exact list rows required")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("exact integer ARC colors 0..9 required")
    copied = [row[:] for row in grid]
    bg = Counter(v for row in copied for v in row).most_common(1)[0][0]
    return copied, len(copied), width, bg


def _column_segments(grid: list[list[int]], column: int, background: int) -> list[tuple[int, int]]:
    height = len(grid)
    segments: list[tuple[int, int]] = []
    row = 0
    while row < height:
        if grid[row][column] == background:
            row += 1
            continue
        start = row
        while row + 1 < height and grid[row + 1][column] != background:
            row += 1
        segments.append((start, row))
        row += 1
    return segments


def find_bars(grid: list[list[int]], background: int) -> list[dict[str, int]]:
    height, width = len(grid), len(grid[0])
    bars: list[dict[str, int]] = []
    for column in range(width):
        for top, bottom in _column_segments(grid, column, background):
            if bottom - top < 2:
                continue
            endpoint = grid[top][column]
            if grid[bottom][column] != endpoint:
                continue
            filler = grid[top + 1][column]
            if filler in (background, endpoint):
                continue
            if not all(grid[row][column] == filler for row in range(top + 1, bottom)):
                continue
            bars.append({
                "column": column,
                "top": top,
                "bottom": bottom,
                "color": endpoint,
                "filler": filler,
                "interior_length": bottom - top - 1,
            })
    return bars


def _longest_cue(grid: list[list[int]], color: int, bar_cells: set[tuple[int, int]]) -> int:
    height, width = len(grid), len(grid[0])
    best = 0
    for column in range(width):
        current = 0
        for row in range(height):
            if grid[row][column] == color and (row, column) not in bar_cells:
                current += 1
                best = max(best, current)
            else:
                current = 0
    return best


def analyze(grid: object, rank_order: str = "outer_to_inner") -> dict[str, object]:
    order = _order(rank_order)
    parsed, height, width, background = _parse_grid(grid)
    bars = find_bars(parsed, background)
    if not bars:
        raise ValueError("at least one vertical endpoint/filler bar is required")
    bar_cells = {
        (row, bar["column"])
        for bar in bars
        for row in range(bar["top"], bar["bottom"] + 1)
    }
    groups: dict[int, list[dict[str, int]]] = defaultdict(list)
    for bar in bars:
        groups[bar["color"]].append(bar)
    selections: list[dict[str, object]] = []
    output = [row[:] for row in parsed]
    for color in sorted(groups):
        group = sorted(groups[color], key=lambda bar: (bar["top"], bar["column"]))
        ordered = group if order == "outer_to_inner" else list(reversed(group))
        cue_height = _longest_cue(parsed, color, bar_cells)
        if cue_height < 1 or cue_height > len(ordered):
            raise ValueError(f"color {color} cue height {cue_height} is not a valid rank among {len(ordered)} bars")
        selected = ordered[cue_height - 1]
        for row in range(selected["top"] + 1, selected["bottom"]):
            output[row][selected["column"]] = color
        selections.append({
            "color": color,
            "cue_height": cue_height,
            "rank_order": order,
            "ordered_columns": [bar["column"] for bar in ordered],
            "ordered_lengths": [bar["interior_length"] for bar in ordered],
            "selected": dict(selected),
        })
    return {
        "height": height,
        "width": width,
        "background": background,
        "bars": [dict(bar) for bar in bars],
        "selections": selections,
        "output": output,
    }


def solve(grid: object, rank_order: str = "outer_to_inner") -> list[list[int]]:
    return deepcopy(analyze(grid, rank_order)["output"])


def self_check(grid: object, **_: object) -> list[str]:
    try:
        analyze(grid, "outer_to_inner")
    except (TypeError, ValueError) as error:
        return [str(error)]
    return []


def _rng(seed: int, label: str) -> random.Random:
    raw = hashlib.sha256(f"97d7923e/{seed}/{label}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


# (height, width, group count, bars per group). Profiles 0..5 are teaching
# candidates and 6..9 are the four query sources; profile 9 is real 30x30 stress.
PROFILES: tuple[tuple[int, int, int, tuple[int, ...]], ...] = (
    (12, 16, 2, (3, 3)),
    (14, 18, 3, (3, 4, 3)),
    (16, 20, 2, (4, 4)),
    (18, 22, 3, (4, 3, 4)),
    (20, 24, 3, (4, 4, 3)),
    (22, 26, 4, (3, 3, 3, 3)),
    (15, 17, 2, (4, 3)),
    (19, 23, 3, (3, 4, 4)),
    (24, 27, 4, (4, 3, 4, 3)),
    (30, 30, 4, (4, 4, 4, 4)),
)


def _scene(seed: int, profile: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(profile, 0, len(PROFILES) - 1, "profile")
    height, width, group_count, bars_per_group = PROFILES[profile]
    rng = _rng(seed, f"scene-{profile}")
    background = 0
    palette = list(range(1, 10))
    rng.shuffle(palette)
    endpoints = palette[:group_count]
    filler_pool = palette[group_count:]
    grid = [[background] * width for _ in range(height)]

    # One cue column per endpoint color. Heights deliberately avoid the central
    # rank so the two admitted rank orders disagree in every generated pair.
    cue_columns = list(range(0, group_count * 2, 2))
    reserved = set(cue_columns)
    available = [c for c in range(width) if c not in reserved and c >= group_count * 2 + 1]
    total_bars = sum(bars_per_group)
    if len(available) < total_bars:
        available = [c for c in range(width) if c not in reserved]
    rng.shuffle(available)
    columns = iter(available[:total_bars])

    for group_index, (endpoint, count) in enumerate(zip(endpoints, bars_per_group, strict=True)):
        candidates = [rank for rank in range(1, count + 1) if rank != count - rank + 1]
        cue_height = candidates[(profile + group_index + seed) % len(candidates)]
        cue_column = cue_columns[group_index]
        for row in range(cue_height):
            grid[row][cue_column] = endpoint

        baseline = height - 1 - (group_index % 2)
        max_length = baseline - max(cue_height + 2, 3) - 1
        if max_length < count:
            raise ValueError("profile does not leave enough vertical room for ranked bars")
        # Unique increasing interior lengths; all bars in a group share a bottom
        # so ascending top row is the visual outer-to-inner order.
        step = max(1, max_length // (count + 1))
        lengths = sorted({min(max_length, step * (i + 1) + (i % 2)) for i in range(count)})
        while len(lengths) < count:
            for value in range(1, max_length + 1):
                if value not in lengths:
                    lengths.append(value)
                    if len(lengths) == count:
                        break
        lengths = sorted(lengths[:count], reverse=True)
        fillers = [filler_pool[(group_index + i) % len(filler_pool)] for i in range(count)]
        rng.shuffle(fillers)
        for length, filler in zip(lengths, fillers, strict=True):
            column = next(columns)
            top = baseline - length - 1
            grid[top][column] = endpoint
            for row in range(top + 1, baseline):
                grid[row][column] = filler
            grid[baseline][column] = endpoint

    if self_check(grid):
        raise ValueError(f"generated invalid scene: {self_check(grid)}")
    return grid


def lesson_inputs(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    demos = [_scene(seed, i) for i in range(6)]
    queries = [_scene(seed, i) for i in range(6, 10)]
    return demos, queries


def generate(seed: int, sample_index: int = 0, *, difficulty: object = None, **overrides: object) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(sample_index, 0, 2**63 - 1, "sample_index")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("unsupported difficulty")
    if overrides:
        raise ValueError("no caller overrides are supported")
    return _scene(seed, sample_index % len(PROFILES))
