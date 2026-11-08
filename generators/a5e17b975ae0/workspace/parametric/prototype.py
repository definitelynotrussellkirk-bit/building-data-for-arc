"""Native matched-input family for ``a5e17b975ae0``.

``local_keys`` is the exact canonical rule. ``largest_chamber_key`` first
measures every keyed chamber, selects the uniquely largest keyed chamber, and
then uses that chamber's key color to flood every keyed chamber.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "a5e17b975ae0"
HERE = Path(__file__).resolve().parent
SETTINGS = ("local_keys", "largest_chamber_key")
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
KEY_COLORS = (1, 2, 3, 4, 6, 7, 8)
WALL_COLORS = (5, 9)
ALLOWED_COLORS = {0, *KEY_COLORS, *WALL_COLORS}

RIVALS = (
    "local_keys",
    "largest_chamber_key",
    "smallest_chamber_key",
    "first_seed_key",
    "last_seed_key",
    "lowest_color",
    "highest_color",
    "leftmost_key",
    "rightmost_key",
    "identity",
)

# (height, width, frame specs, winner ref, decoy refs)
# frame spec: top, left, height, width, horizontal-wall offset, vertical-wall offset
# region ref: frame index, TL|TR|BL|BR
_DEMO_PROFILES = (
    (12, 18, ((1, 1, 10, 7, 7, 4), (1, 10, 10, 7, 3, 2)), (0, "TL"), ((1, "BL"), (0, "BR"))),
    (13, 20, ((1, 1, 11, 8, 3, 2), (1, 11, 11, 8, 7, 5)), (1, "TL"), ((0, "TL"), (0, "BL"))),
    (15, 22, ((1, 1, 13, 9, 9, 6), (1, 12, 13, 9, 4, 3)), (1, "BR"), ((0, "TR"), (1, "TL"))),
    (18, 24, ((1, 1, 16, 10, 5, 3), (1, 13, 16, 10, 11, 7)), (1, "TL"), ((0, "TL"), (1, "BR"))),
    (21, 26, ((1, 1, 19, 11, 14, 7), (1, 14, 19, 11, 6, 3)), (0, "TL"), ((0, "BR"), (1, "TL"))),
    (26, 29, ((1, 1, 24, 12, 7, 3), (1, 16, 24, 12, 17, 8)), (1, "TL"), ((0, "TL"), (1, "BR"))),
)
_QUERY_PROFILES = (
    (12, 19, ((1, 1, 10, 7, 6, 2), (1, 11, 10, 7, 3, 4)), (0, "TR"), ((0, "BL"), (1, "TR"))),
    (18, 23, ((1, 1, 16, 9, 11, 6), (1, 13, 16, 9, 5, 3)), (0, "TL"), ((0, "BR"), (1, "TL"))),
    (24, 28, ((1, 1, 22, 11, 7, 3), (1, 16, 22, 11, 15, 7)), (1, "TL"), ((0, "TL"), (1, "BR"))),
    (30, 30, ((1, 1, 28, 12, 20, 8), (1, 17, 28, 12, 8, 4)), (0, "TL"), ((0, "BR"), (1, "TL"))),
)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _policy(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"fill_color_policy"}:
        raise ValueError("settings must contain only fill_color_policy")
    value = settings["fill_color_policy"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("fill_color_policy must be local_keys or largest_chamber_key")
    return value


def program(settings: Any) -> str:
    policy = _policy(settings)
    filename = "canonical.rkt" if policy == "local_keys" else "largest_chamber_key.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _validate_grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or cell not in ALLOWED_COLORS for cell in row)
        for row in value
    ):
        raise ValueError("input must be rectangular with exact supported ARC colors")
    return value


def _neighbors(row: int, col: int, height: int, width: int):
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = row + dr, col + dc
        if 0 <= rr < height and 0 <= cc < width:
            yield rr, cc


def _seed_region(grid: list[list[int]], seed: tuple[int, int, int]) -> set[tuple[int, int]]:
    sr, sc, color = seed
    height, width = len(grid), len(grid[0])
    seen = {(sr, sc)}
    pending = [(sr, sc)]
    while pending:
        row, col = pending.pop()
        for rr, cc in _neighbors(row, col, height, width):
            if (rr, cc) in seen:
                continue
            value = grid[rr][cc]
            if value in WALL_COLORS or value not in (0, color):
                continue
            seen.add((rr, cc))
            pending.append((rr, cc))
    return seen


def analyze(value: Any) -> dict[str, Any]:
    grid = _validate_grid(value)
    seeds = sorted(
        (row, col, color)
        for row, values in enumerate(grid)
        for col, color in enumerate(values)
        if color not in (0, *WALL_COLORS)
    )
    if len(seeds) < 2:
        raise ValueError("parametric grammar requires at least two key cells")
    if len({color for _, _, color in seeds}) != len(seeds):
        raise ValueError("key colors must be distinct")
    regions = []
    claimed: set[tuple[int, int]] = set()
    for seed in seeds:
        cells = _seed_region(grid, seed)
        if claimed & cells:
            raise ValueError("keyed chambers must be disjoint")
        claimed.update(cells)
        regions.append(
            {
                "seed": (seed[0], seed[1]),
                "row": seed[0],
                "col": seed[1],
                "color": seed[2],
                "cells": cells,
                "size": len(cells),
            }
        )
    ranked = sorted(regions, key=lambda row: (-row["size"], row["row"], row["col"]))
    if ranked[0]["size"] == ranked[1]["size"]:
        raise ValueError("largest keyed chamber must be unique")
    smallest = min(regions, key=lambda row: (row["size"], row["row"], row["col"]))
    nonzero = sum(cell != 0 for row in grid for cell in row)
    wall_count = sum(cell in WALL_COLORS for row in grid for cell in row)
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "keyed_regions": regions,
        "largest_region": ranked[0],
        "smallest_region": smallest,
        "second_largest_size": ranked[1]["size"],
        "nonzero_count": nonzero,
        "wall_count": wall_count,
        "touches_boundary": any(
            grid[row][col] != 0
            for row, col in (
                *((0, col) for col in range(len(grid[0]))),
                *((len(grid) - 1, col) for col in range(len(grid[0]))),
                *((row, 0) for row in range(len(grid))),
                *((row, len(grid[0]) - 1) for row in range(len(grid))),
            )
        ),
    }


def _selected_color(summary: dict[str, Any], hypothesis: str) -> int | None:
    regions = summary["keyed_regions"]
    if hypothesis == "largest_chamber_key":
        return summary["largest_region"]["color"]
    if hypothesis == "smallest_chamber_key":
        return summary["smallest_region"]["color"]
    if hypothesis == "first_seed_key":
        return min(regions, key=lambda row: (row["row"], row["col"]))["color"]
    if hypothesis == "last_seed_key":
        return max(regions, key=lambda row: (row["row"], row["col"]))["color"]
    if hypothesis == "lowest_color":
        return min(row["color"] for row in regions)
    if hypothesis == "highest_color":
        return max(row["color"] for row in regions)
    if hypothesis == "leftmost_key":
        return min(regions, key=lambda row: (row["col"], row["row"]))["color"]
    if hypothesis == "rightmost_key":
        return max(regions, key=lambda row: (row["col"], row["row"]))["color"]
    return None


def apply_rule(value: Any, hypothesis: str) -> list[list[int]]:
    if type(hypothesis) is not str or hypothesis not in RIVALS:
        raise ValueError("unknown declared hypothesis")
    grid = _validate_grid(value)
    summary = analyze(grid)
    out = deepcopy(grid)
    if hypothesis == "identity":
        return out
    shared_color = _selected_color(summary, hypothesis)
    for region in summary["keyed_regions"]:
        color = region["color"] if hypothesis == "local_keys" else shared_color
        assert color is not None
        for row, col in region["cells"]:
            out[row][col] = color
    return out


def changed_cells(left: list[list[int]], right: list[list[int]]) -> int:
    if len(left) != len(right) or len(left[0]) != len(right[0]):
        raise ValueError("grids must have equal dimensions")
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def _blank(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _draw_frame(grid: list[list[int]], spec: tuple[int, int, int, int, int, int]) -> None:
    top, left, height, width, hsplit, vsplit = spec
    bottom, right = top + height - 1, left + width - 1
    for col in range(left, right + 1):
        grid[top][col] = 9
        grid[bottom][col] = 9
    for row in range(top, bottom + 1):
        grid[row][left] = 9
        grid[row][right] = 9
    wall_row, wall_col = top + hsplit, left + vsplit
    for col in range(left + 1, right):
        grid[wall_row][col] = 5
    for row in range(top + 1, bottom):
        grid[row][wall_col] = 5


def _region_cells(spec: tuple[int, int, int, int, int, int], quadrant: str) -> list[tuple[int, int]]:
    top, left, height, width, hsplit, vsplit = spec
    if quadrant == "TL":
        rows, cols = range(top + 1, top + hsplit), range(left + 1, left + vsplit)
    elif quadrant == "TR":
        rows, cols = range(top + 1, top + hsplit), range(left + vsplit + 1, left + width - 1)
    elif quadrant == "BL":
        rows, cols = range(top + hsplit + 1, top + height - 1), range(left + 1, left + vsplit)
    elif quadrant == "BR":
        rows, cols = range(top + hsplit + 1, top + height - 1), range(left + vsplit + 1, left + width - 1)
    else:
        raise ValueError("unknown chamber quadrant")
    cells = [(row, col) for row in rows for col in cols]
    if not cells:
        raise ValueError("empty chamber in profile")
    return cells


def _stream_seed(seed: int, split: str, index: int) -> int:
    raw = f"{TASK_ID}:fill-color-v1:{seed}:{split}:{index}".encode()
    return int(hashlib.sha256(raw).hexdigest()[:16], 16)


def _color_triplet(seed: int, split: str, index: int) -> tuple[int, int, int]:
    rng = random.Random(_stream_seed(seed, split + ":colors", index))
    chosen = sorted(rng.sample(KEY_COLORS, 3))
    mode = index % 3
    if mode == 0:
        return chosen[0], chosen[2], chosen[1]  # winner is numerically lowest
    if mode == 1:
        return chosen[2], chosen[0], chosen[1]  # winner is numerically highest
    return chosen[1], chosen[0], chosen[2]      # winner is in the middle


def _seed_point(cells: list[tuple[int, int]], rng: random.Random, salt: int) -> tuple[int, int]:
    ordered = sorted(cells)
    center = len(ordered) // 2
    span = min(3, max(1, len(ordered) // 4))
    offset = rng.randrange(-span, span + 1)
    return ordered[(center + offset + salt) % len(ordered)]


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    height, width, frames, winner_ref, decoy_refs = profiles[index]
    grid = _blank(height, width)
    for frame in frames:
        _draw_frame(grid, frame)
    rng = random.Random(_stream_seed(seed, split, index))
    refs = (winner_ref, *decoy_refs)
    colors = _color_triplet(seed, split, index)
    for salt, ((frame_index, quadrant), color) in enumerate(zip(refs, colors)):
        cells = _region_cells(frames[frame_index], quadrant)
        row, col = _seed_point(cells, rng, salt)
        grid[row][col] = color
    summary = analyze(grid)
    intended_winner_cells = set(_region_cells(frames[winner_ref[0]], winner_ref[1]))
    if summary["largest_region"]["cells"] != intended_winner_cells:
        raise RuntimeError("profile failed to make the designated keyed chamber uniquely largest")
    if summary["smallest_region"]["color"] == summary["largest_region"]["color"]:
        raise RuntimeError("winner and smallest chamber colors must differ")
    return grid


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _exact_int(seed, "seed", 0, 2**63 - 1)
    policy = _policy(settings)
    demos = _exact_int(demos, "demos", MIN_DEMOS, MAX_DEMOS)
    queries = _exact_int(queries, "queries", MIN_QUERIES, MAX_QUERIES)
    train_inputs = [_scene(seed, "train", index) for index in range(demos)]
    test_inputs = [_scene(seed, "test", index) for index in range(queries)]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in train_inputs + test_inputs]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("episode inputs must be distinct")
    return {
        "train": [{"input": grid, "output": apply_rule(grid, policy)} for grid in train_inputs],
        "test": [{"input": grid, "output": apply_rule(grid, policy)} for grid in test_inputs],
        "program_solution": program({"fill_color_policy": policy}),
    }


def audit_episode(episode: dict[str, Any], selected_setting: str) -> dict[str, Any]:
    if selected_setting not in SETTINGS:
        raise ValueError("selected setting is undeclared")
    survivors = []
    for hypothesis in RIVALS:
        if all(apply_rule(pair["input"], hypothesis) == pair["output"] for pair in episode["train"]):
            survivors.append(hypothesis)
    harmful = [
        hypothesis
        for hypothesis in survivors
        if hypothesis != selected_setting
        and any(apply_rule(pair["input"], hypothesis) != pair["output"] for pair in episode["test"])
    ]
    return {
        "selected_setting": selected_setting,
        "survivors": survivors,
        "harmful_survivors": harmful,
        "queries_checked": len(episode["test"]),
    }
