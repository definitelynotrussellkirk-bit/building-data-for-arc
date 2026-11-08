"""Native midpoint-only / complete-X family for 69927005ac25.

Inputs are setting-neutral.  The alternate performs the canonical midpoint
bridge (Step A), then treats each newly completed three-cell diagonal as the
input-dependent intermediate consumed by Step B to paint the other two corners
of its 3x3 box, yielding an X while preserving blockers.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

HERE = Path(__file__).resolve().parent
MODES = ("midpoint_only", "complete_x")
PROGRAMS = {
    "midpoint_only": HERE / "canonical.rkt",
    "complete_x": HERE / "complete_x.rkt",
}
PAIR_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
DEMO_PROFILES = (
    (7, 8, 2, True),
    (9, 10, 3, False),
    (12, 12, 4, True),
    (16, 18, 8, False),
    (22, 24, 12, True),
    (26, 28, 16, False),
)
QUERY_PROFILES = (
    (10, 11, 4, True),
    (18, 20, 8, False),
    (24, 27, 14, True),
    (30, 30, 24, True),
)


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _mode(settings: Any) -> str:
    if (type(settings) is not dict or set(settings) != {"completion_mode"}
            or type(settings["completion_mode"]) is not str
            or settings["completion_mode"] not in MODES):
        raise ValueError("settings must contain exactly one supported completion_mode")
    return settings["completion_mode"]


def program(settings: Any) -> str:
    return PROGRAMS[_mode(settings)].read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"69927005ac25-parametric-v1|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _bridge_sites(grid):
    height, width = len(grid), len(grid[0])
    sites = []
    for row in range(height):
        for column in range(width):
            value = grid[row][column]
            if value == 0:
                continue
            for dc in (-2, 2):
                er, ec = row + 2, column + dc
                mr, mc = row + 1, column + dc // 2
                if (0 <= er < height and 0 <= ec < width
                        and grid[er][ec] == value and grid[mr][mc] == 0):
                    sites.append((row, column, mr, mc, er, ec, value))
    return sites


def bridge(grid):
    out = deepcopy(grid)
    for _, _, mr, mc, _, _, value in _bridge_sites(grid):
        if out[mr][mc] == 0:
            out[mr][mc] = value
    return out


def complete_x(grid):
    bridged = bridge(grid)
    out = deepcopy(bridged)
    height, width = len(grid), len(grid[0])
    for row in range(height - 2):
        for column in range(width):
            value = bridged[row][column]
            if value == 0:
                continue
            for dc in (-1, 1):
                ec = column + 2 * dc
                if not 0 <= ec < width:
                    continue
                if (bridged[row + 1][column + dc] == value
                        and bridged[row + 2][ec] == value):
                    for rr, cc in ((row, ec), (row + 2, column)):
                        if out[rr][cc] == 0:
                            out[rr][cc] = value
    return out


def _origins(height: int, width: int):
    return [(row, column) for row in range(0, height - 2, 4)
            for column in range(0, width - 2, 4)]


def _build_input(seed: int, split: str, index: int, profile):
    height, width, pair_count, blocked = profile
    rng = _rng(seed, split, index)
    origins = _origins(height, width)
    if len(origins) < pair_count:
        raise RuntimeError("profile does not have enough separated 3x3 cells")
    rng.shuffle(origins)
    chosen = origins[:pair_count]
    grid = [[0] * width for _ in range(height)]
    endpoints_by_color = {color: [] for color in PAIR_COLORS}
    intended_midpoints = set()
    blocker_cell = None

    for ordinal, (row, column) in enumerate(chosen):
        orientation = rng.choice((1, -1))
        if orientation == 1:
            first, midpoint, second = (row, column), (row + 1, column + 1), (row + 2, column + 2)
            opposites = ((row, column + 2), (row + 2, column))
        else:
            first, midpoint, second = (row, column + 2), (row + 1, column + 1), (row + 2, column)
            opposites = ((row, column), (row + 2, column + 2))

        candidates = list(PAIR_COLORS)
        rng.shuffle(candidates)
        color = None
        for candidate in candidates:
            prior = endpoints_by_color[candidate]
            if all(not (abs(rr - r) == 2 and abs(cc - c) == 2)
                   for rr, cc in (first, second) for r, c in prior):
                color = candidate
                break
        if color is None:
            raise RuntimeError("could not color separated diagonal pairs without cross-pairs")
        for rr, cc in (first, second):
            grid[rr][cc] = color
            endpoints_by_color[color].append((rr, cc))
        intended_midpoints.add(midpoint)

        if blocked and blocker_cell is None and ordinal == pair_count // 2:
            blocker_cell = opposites[(seed + index) % 2]
            grid[blocker_cell[0]][blocker_cell[1]] = 5

    sites = _bridge_sites(grid)
    actual_midpoints = {(mr, mc) for _, _, mr, mc, _, _, _ in sites}
    if actual_midpoints != intended_midpoints or len(sites) != pair_count:
        raise RuntimeError(("unexpected diagonal interaction", len(sites), pair_count,
                            sorted(actual_midpoints), sorted(intended_midpoints)))
    return grid


def _pair(grid, mode):
    output = bridge(grid) if mode == "midpoint_only" else complete_x(grid)
    return {"input": deepcopy(grid), "output": output}


def generate(seed: Any, settings: Any, demos: Any, queries: Any):
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    mode = _mode(settings)
    demo_inputs = [_build_input(seed, "train", index, profile)
                   for index, profile in enumerate(DEMO_PROFILES[:demos])]
    query_bank = [_build_input(seed, "test", index, profile)
                  for index, profile in enumerate(QUERY_PROFILES)]
    selected_queries = query_bank[:queries]
    all_inputs = demo_inputs + selected_queries
    if len({repr(grid) for grid in all_inputs}) != len(all_inputs):
        raise RuntimeError("episode inputs must be distinct")
    return {
        "train": [_pair(grid, mode) for grid in demo_inputs],
        "test": [_pair(grid, mode) for grid in selected_queries],
        "program_solution": program(settings),
        "seed": seed,
        "settings": deepcopy(settings),
    }


def public_turn(episode, query_index):
    query_index = _integer("query_index", query_index, 0, 3)
    if (type(episode) is not dict or type(episode.get("train")) is not list
            or type(episode.get("test")) is not list or query_index >= len(episode["test"])):
        raise ValueError("episode does not contain the requested query")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
