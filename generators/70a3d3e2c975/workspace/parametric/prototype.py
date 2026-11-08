"""Parametric copy-policy family for central-axis reflection.

The canonical setting mirrors every nonzero, non-axis source cell.  The
alternative first measures source-color frequencies and mirrors only the unique
least-frequent color.  Input sampling is independent of the private setting.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Callable

TASK_ID = "70a3d3e2c975"
POLICIES = ("all_colors", "rarest_color")
DEFAULT_SETTINGS = {"copy_policy": "all_colors"}
HERE = Path(__file__).resolve().parent

# (height, half-width, ((color, count), ...)).  Width is 2*half+1.
_DEMO_PROFILES = (
    (7, 4, ((7, 1), (2, 5), (5, 3))),
    (9, 5, ((3, 2), (8, 6), (6, 4))),
    (11, 6, ((7, 2), (4, 7), (1, 5), (5, 4))),
    (13, 7, ((6, 3), (2, 8), (8, 5), (4, 7))),
    (15, 8, ((3, 2), (1, 9), (5, 5), (8, 7), (6, 4))),
    (17, 9, ((4, 3), (7, 7), (2, 10), (6, 6), (1, 8))),
)
_QUERY_PROFILES = (
    (14, 7, ((5, 3), (1, 12), (8, 7), (3, 5))),
    (18, 9, ((6, 2), (2, 15), (7, 10), (4, 6), (1, 9))),
    (24, 12, ((8, 4), (3, 25), (6, 16), (1, 9), (5, 13))),
    (30, 14, ((4, 7), (8, 40), (2, 22), (6, 13), (1, 30))),
)


def _literal_int(name: str, value: object, lower: int, upper: int) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be a literal integer in {lower}..{upper}")
    return value


def normalize_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"copy_policy"}:
        raise ValueError("settings must contain exactly copy_policy")
    policy = settings["copy_policy"]
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError(f"copy_policy must be one of {POLICIES!r}")
    return {"copy_policy": policy}


@lru_cache(maxsize=1)
def canonical_program() -> str:
    return (HERE / "canonical.rkt").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def rarest_program() -> str:
    return (HERE / "rarest_color.rkt").read_text(encoding="utf-8")


def program(settings: object) -> str:
    policy = normalize_settings(settings)["copy_policy"]
    return canonical_program() if policy == "all_colors" else rarest_program()


def _copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def validate_input(value: object) -> list[list[int]]:
    if type(value) is not list or not 1 <= len(value) <= 30:
        raise ValueError("grid height must be 1..30")
    if not value or type(value[0]) is not list or not 3 <= len(value[0]) <= 30:
        raise ValueError("grid width must be 3..30")
    width = len(value[0])
    if width % 2 != 1:
        raise ValueError("reflection grammar requires odd width")
    grid: list[list[int]] = []
    for row in value:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid cells must be literal integers in 0..9")
        grid.append(row[:])
    axis = width // 2
    if any(row[axis] != 9 for row in grid):
        raise ValueError("center column must be a full-height 9 axis")
    if any(row[c] == 9 for row in grid for c in range(width) if c != axis):
        raise ValueError("9 may appear only on the center axis")
    if any(row[c] != 0 for row in grid for c in range(axis + 1, width)):
        raise ValueError("right half must start blank")
    source = [row[c] for row in grid for c in range(axis) if row[c] != 0]
    if not source or any(not 1 <= cell <= 8 for cell in source):
        raise ValueError("left half needs at least one source color in 1..8")
    return grid


def source_counts(value: object) -> Counter[int]:
    grid = validate_input(value)
    axis = len(grid[0]) // 2
    return Counter(row[c] for row in grid for c in range(axis) if row[c] != 0)


def rarest_color(value: object) -> int:
    counts = source_counts(value)
    return min(counts, key=lambda color: (counts[color], color))


def _eligible_colors(grid: list[list[int]], policy: str) -> set[int]:
    counts = source_counts(grid)
    if policy == "all_colors":
        return set(counts)
    if policy == "rarest_color":
        return {min(counts, key=lambda color: (counts[color], color))}
    raise ValueError(f"unknown copy policy {policy!r}")


def _reflect_with_colors(value: object, colors: set[int]) -> list[list[int]]:
    grid = validate_input(value)
    out = _copy_grid(grid)
    axis = len(grid[0]) // 2
    for r, row in enumerate(grid):
        for c in range(axis):
            if row[c] in colors:
                out[r][2 * axis - c] = row[c]
    return out


def transform(value: object, policy: object) -> list[list[int]]:
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError(f"copy policy must be one of {POLICIES!r}")
    grid = validate_input(value)
    return _reflect_with_colors(grid, _eligible_colors(grid, policy))


def _rng(seed: int, split: str, slot: int) -> random.Random:
    digest = hashlib.sha256(f"70a-copy-policy-v1:{seed}:{split}:{slot}".encode()).digest()
    return random.Random(digest)


def _connected_prefix(height: int, half: int, anchor: tuple[int, int], count: int) -> list[tuple[int, int]]:
    queue = deque([anchor])
    seen = {anchor}
    result: list[tuple[int, int]] = []
    while queue and len(result) < count:
        r, c = queue.popleft()
        result.append((r, c))
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            nxt = (r + dr, c + dc)
            if 0 <= nxt[0] < height and 0 <= nxt[1] < half and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    if len(result) != count:
        raise ValueError("profile does not fit its rare-color connected shape")
    return result


def _first_free(candidates: list[tuple[int, int]], occupied: set[tuple[int, int]]) -> tuple[int, int]:
    for cell in candidates:
        if cell not in occupied:
            return cell
    raise ValueError("no free forced placement cell")


def _build_input(seed: int, split: str, slot: int, profile: tuple) -> list[list[int]]:
    height, half, raw_counts = profile
    counts = dict(raw_counts)
    if len(counts) < 3 or len(set(counts.values())) != len(counts):
        raise ValueError("profiles need at least three colors with distinct frequencies")
    rare = min(counts, key=lambda color: (counts[color], color))
    width = 2 * half + 1
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row in grid:
        row[half] = 9

    anchor_options = (
        (height // 2, max(1, half // 2)),
        (max(1, height - 3), 1),
        (1, max(1, half - 3)),
        (max(1, height // 3), 0),
    )
    anchor = anchor_options[slot % len(anchor_options)]
    rare_cells = _connected_prefix(height, half, anchor, counts[rare])
    occupied = set(rare_cells)
    for r, c in rare_cells:
        grid[r][c] = rare

    other_colors = [color for color in counts if color != rare]
    forced_groups = [
        [(0, 0), (1, 0), (height - 1, 0)],
        [(0, half - 1), (1, half - 1), (height - 1, half - 1)],
        [(height - 1, 0), (height - 1, 1), (height - 2, 0)],
        [(0, max(0, half // 2)), (height - 1, max(0, half // 2))],
    ]
    rng = _rng(seed, split, slot)
    all_cells = [(r, c) for r in range(height) for c in range(half)]
    for index, color in enumerate(other_colors):
        forced = _first_free(forced_groups[index % len(forced_groups)] + all_cells, occupied)
        cells = [forced]
        occupied.add(forced)
        available = [cell for cell in all_cells if cell not in occupied]
        extra = rng.sample(available, counts[color] - 1)
        cells.extend(extra)
        occupied.update(extra)
        for r, c in cells:
            grid[r][c] = color
    return validate_input(grid)


def _schedule(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demos = [_build_input(seed, "demo", index, profile) for index, profile in enumerate(_DEMO_PROFILES)]
    queries = [_build_input(seed, "query", index, profile) for index, profile in enumerate(_QUERY_PROFILES)]
    frozen = [json.dumps(grid, separators=(",", ":")) for grid in demos + queries]
    if len(frozen) != len(set(frozen)):
        raise ValueError("parametric schedule produced duplicate inputs")
    return demos, queries


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, object]:
    checked_seed = _literal_int("seed", seed, 0, 2**63 - 1)
    checked_demos = _literal_int("demos", demos, 2, 6)
    checked_queries = _literal_int("queries", queries, 1, 4)
    policy = normalize_settings(settings)["copy_policy"]
    demo_inputs, query_inputs = _schedule(checked_seed)

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": deepcopy(grid), "output": transform(grid, policy)}

    train = [pair(grid) for grid in demo_inputs[:checked_demos]]
    test = [pair(grid) for grid in query_inputs[:checked_queries]]
    if setting_survivors(train) != [policy]:
        raise ValueError("demonstrations do not uniquely identify copy_policy")
    return {"train": train, "test": test, "program_solution": program({"copy_policy": policy})}


def setting_survivors(demonstrations: object) -> list[str]:
    if type(demonstrations) is not list or not demonstrations:
        raise ValueError("demonstrations must be a nonempty list")
    survivors = []
    for policy in POLICIES:
        if all(transform(pair["input"], policy) == pair["output"] for pair in demonstrations):
            survivors.append(policy)
    return survivors


def _first_seen(grid: list[list[int]]) -> int:
    axis = len(grid[0]) // 2
    for row in grid:
        for value in row[:axis]:
            if value:
                return value
    raise ValueError("empty source")


def _nearest_axis(grid: list[list[int]]) -> int:
    axis = len(grid[0]) // 2
    positions: dict[int, int] = {}
    for row in grid:
        for c, value in enumerate(row[:axis]):
            if value:
                positions[value] = min(positions.get(value, axis), axis - c)
    return min(positions, key=lambda color: (positions[color], color))


def _farthest_axis(grid: list[list[int]]) -> int:
    axis = len(grid[0]) // 2
    positions: dict[int, int] = {}
    for row in grid:
        for c, value in enumerate(row[:axis]):
            if value:
                positions[value] = max(positions.get(value, -1), axis - c)
    return max(positions, key=lambda color: (positions[color], -color))


def predict_rival(value: object, name: str) -> list[list[int]]:
    grid = validate_input(value)
    counts = source_counts(grid)
    if name == "identity":
        return _copy_grid(grid)
    if name == "most_frequent_color":
        selected = {max(counts, key=lambda color: (counts[color], -color))}
    elif name == "smallest_numeric_color":
        selected = {min(counts)}
    elif name == "largest_numeric_color":
        selected = {max(counts)}
    elif name == "singleton_colors":
        selected = {color for color, count in counts.items() if count == 1}
    elif name == "first_seen_color":
        selected = {_first_seen(grid)}
    elif name == "nearest_axis_color":
        selected = {_nearest_axis(grid)}
    elif name == "farthest_axis_color":
        selected = {_farthest_axis(grid)}
    elif name == "axis_adjacent_colors":
        axis = len(grid[0]) // 2
        selected = {row[axis - 1] for row in grid if row[axis - 1] not in (0, 9)}
    else:
        raise ValueError(f"unknown rival {name!r}")
    return _reflect_with_colors(grid, selected)


RIVALS = (
    "identity",
    "most_frequent_color",
    "smallest_numeric_color",
    "largest_numeric_color",
    "singleton_colors",
    "first_seen_color",
    "nearest_axis_color",
    "farthest_axis_color",
    "axis_adjacent_colors",
)


def rival_survivors(demonstrations: object, *, selected_policy: str) -> list[str]:
    if selected_policy not in POLICIES:
        raise ValueError("unknown selected policy")
    return [
        name
        for name in RIVALS
        if all(predict_rival(pair["input"], name) == pair["output"] for pair in demonstrations)
    ]


def dependency(value: object, policy: object) -> dict[str, object]:
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError("unknown policy")
    grid = validate_input(value)
    counts = source_counts(grid)
    rare = min(counts, key=lambda color: (counts[color], color))
    eligible = sorted(counts) if policy == "all_colors" else [rare]
    return {
        "step_a": "scan the source half, count each nonzero non-axis color, and produce the policy-selected eligible color set",
        "source_counts": dict(sorted(counts.items())),
        "rarest_color": rare,
        "eligible_colors": eligible,
        "step_b": "reflect exactly the source cells whose colors are in the eligible set across the discovered 9 axis",
        "final": _reflect_with_colors(grid, set(eligible)),
    }
