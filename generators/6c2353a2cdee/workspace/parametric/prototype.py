"""Matched-input rotation-direction episodes for 6c2353a2cdee.

The canonical setting interprets code 2 as clockwise and code 4 as
counter-clockwise.  The alternate setting swaps those quarter-turn meanings.
Both derive three transformed panel supports before the common overlap-count
renderer consumes them.  Python outputs are deterministic claims; native
qualification independently executes every label through protected Racket.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "6c2353a2cdee"
HERE = Path(__file__).resolve().parent
SETTING_NAMES = ("clockwise", "counterclockwise")
PANEL_STARTS = (0, 6, 12)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

DEMO_PROFILES = (
    ((7, 17), (2, 4, 1), 0),
    ((7, 17), (4, 2, 3), 0),
    ((9, 19), (1, 2, 4), 1),
    ((12, 20), (3, 4, 2), 1),
    ((18, 24), (2, 3, 4), 2),
    ((24, 27), (4, 1, 2), 2),
)
QUERY_PROFILES = (
    ((12, 20), (2, 4, 3), 2),
    ((18, 24), (4, 2, 1), 3),
    ((24, 27), (2, 3, 4), 4),
    ((30, 30), (4, 3, 2), 5),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"rotation_direction"}:
        raise ValueError("settings must contain exactly rotation_direction")
    value = settings["rotation_direction"]
    if type(value) is not str or value not in SETTING_NAMES:
        raise ValueError(f"rotation_direction must be one of {SETTING_NAMES}")
    return value


def program_for(direction: str) -> str:
    if direction == "clockwise":
        path = HERE / "canonical.rkt"
    elif direction == "counterclockwise":
        path = HERE / "counterclockwise.rkt"
    else:
        raise ValueError("direction has no declared Racket program")
    return path.read_text()


def program(settings: dict[str, Any]) -> str:
    return program_for(_setting(settings))


def _validate_grid(grid: Any) -> tuple[list[list[int]], int, int]:
    if type(grid) is not list or not 7 <= len(grid) <= 30:
        raise ValueError("grid must have 7..30 rows")
    if type(grid[0]) is not list or not 17 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 17..30 columns")
    width = len(grid[0])
    clean: list[list[int]] = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid cells must be exact integer colors 0..9")
        clean.append(list(row))
    return clean, len(clean), width


def rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _transform(panel: list[list[int]], code: int, direction: str) -> list[list[int]]:
    if code == 1:
        return copy.deepcopy(panel)
    if code == 3:
        return rotate_180(panel)
    if code == 2:
        return rotate_cw(panel) if direction == "clockwise" else rotate_ccw(panel)
    if code == 4:
        return rotate_ccw(panel) if direction == "clockwise" else rotate_cw(panel)
    return copy.deepcopy(panel)


def extract(grid: Any) -> tuple[list[list[list[int]]], tuple[int, int, int]]:
    values, _, _ = _validate_grid(grid)
    panels = [
        [list(row[left:left + 5]) for row in values[:5]]
        for left in PANEL_STARTS
    ]
    codes: list[int] = []
    for left in PANEL_STARTS:
        nonzero = [value for value in values[6][left:left + 5] if value != 0]
        if len(nonzero) != 1 or nonzero[0] not in (1, 2, 3, 4):
            raise ValueError("each panel code segment must contain exactly one code in 1..4")
        codes.append(nonzero[0])
    return panels, tuple(codes)  # type: ignore[return-value]


def analyze(grid: Any, direction: str) -> dict[str, Any]:
    if direction not in SETTING_NAMES:
        raise ValueError(f"direction must be one of {SETTING_NAMES}")
    panels, codes = extract(grid)
    transformed = [_transform(panel, code, direction) for panel, code in zip(panels, codes)]
    return {"panels": panels, "codes": codes, "transformed_panels": transformed}


def overlay(transformed_panels: list[list[list[int]]], *, binary_only: bool = False,
            keep: tuple[int, ...] = (0, 1, 2)) -> list[list[int]]:
    if len(transformed_panels) != 3:
        raise ValueError("exactly three transformed panels are required")
    out = [[0] * 5 for _ in range(5)]
    for row in range(5):
        for col in range(5):
            count = sum(transformed_panels[index][row][col] != 0 for index in keep)
            out[row][col] = (2 if count else 0) if binary_only else {0: 0, 1: 2, 2: 4, 3: 8}[count]
    return out


def solve(grid: Any, rule: str) -> list[list[int]]:
    if rule in SETTING_NAMES:
        return overlay(analyze(grid, rule)["transformed_panels"])
    panels, codes = extract(grid)
    if rule == "ignore_codes":
        transformed = [copy.deepcopy(panel) for panel in panels]
        return overlay(transformed)
    if rule == "all_180":
        return overlay([rotate_180(panel) for panel in panels])
    if rule.endswith("_union"):
        direction = rule.removesuffix("_union")
        return overlay(analyze(grid, direction)["transformed_panels"], binary_only=True)
    for suffix, keep in (("_first_two", (0, 1)), ("_last_two", (1, 2))):
        if rule.endswith(suffix):
            direction = rule.removesuffix(suffix)
            return overlay(analyze(grid, direction)["transformed_panels"], keep=keep)
    raise ValueError(f"unknown rule {rule!r}")


CANDIDATE_NAMES = (
    "clockwise",
    "counterclockwise",
    "ignore_codes",
    "all_180",
    "clockwise_union",
    "counterclockwise_union",
    "clockwise_first_two",
    "counterclockwise_first_two",
    "clockwise_last_two",
    "counterclockwise_last_two",
)


def teaching_survivors(demos: list[dict[str, Any]]) -> list[str]:
    survivors = []
    for name in CANDIDATE_NAMES:
        if all(solve(pair["input"], name) == pair["output"] for pair in demos):
            survivors.append(name)
    return survivors


def _shape_grid(cells: set[tuple[int, int]], color: int) -> list[list[int]]:
    grid = [[0] * 5 for _ in range(5)]
    for row, col in cells:
        grid[row][col] = color
    return grid


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {min(cells)}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in CARDINAL:
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _signature(cells: set[tuple[int, int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in _shape_grid(cells, 1))


def _rotation_signatures(cells: set[tuple[int, int]]) -> set[tuple[tuple[int, ...], ...]]:
    grid = _shape_grid(cells, 1)
    return {tuple(tuple(row) for row in variant) for variant in
            (grid, rotate_cw(grid), rotate_180(grid), rotate_ccw(grid))}


def _grow_shape(rng: random.Random, size: int, wide: bool) -> set[tuple[int, int]]:
    for _ in range(1000):
        cols = rng.choice(((0, 1, 2, 3), (1, 2, 3, 4))) if wide else (1, 2, 3)
        allowed = {(row, col) for row in (1, 2, 3) for col in cols}
        cells = {(2, rng.choice(cols))}
        while len(cells) < size:
            frontier = sorted({(row + dr, col + dc) for row, col in cells for dr, dc in CARDINAL
                               if (row + dr, col + dc) in allowed and (row + dr, col + dc) not in cells})
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) != size or {row for row, _ in cells} != {1, 2, 3}:
            continue
        width = max(c for _, c in cells) - min(c for _, c in cells) + 1
        if not 2 <= width <= 4 or not _connected(cells) or len(_rotation_signatures(cells)) != 4:
            continue
        return cells
    raise RuntimeError("bounded shape sampler exhausted")


def _rng(seed: int, split: str, index: int, attempt: int) -> random.Random:
    raw = json.dumps([TASK_ID, "parametric-v1", seed, split, index, attempt], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _add_distractors(grid: list[list[int]], rng: random.Random, density_level: int) -> None:
    height, width = len(grid), len(grid[0])
    if height == 7 and width == 17:
        return
    threshold = min(5, 1 + density_level)
    for row in range(height):
        for col in range(width):
            if row < 7 and col < 17:
                continue
            marker = (row * 17 + col * 31 + rng.randrange(97)) % 11
            if marker < threshold:
                grid[row][col] = 1 + ((row * 3 + col * 5 + marker) % 9)
    # Make the largest profiles exercise every boundary with real decoy content.
    if density_level >= 4:
        for col in range(17, width):
            grid[0][col] = 1 + col % 9
            grid[height - 1][col] = 1 + (col + 3) % 9
        for row in range(7, height):
            grid[row][0] = 1 + row % 9
            grid[row][width - 1] = 1 + (row + 4) % 9


def _build_candidate(seed: int, split: str, index: int, attempt: int,
                     dims: tuple[int, int], codes: tuple[int, int, int], density: int) -> list[list[int]]:
    rng = _rng(seed, split, index, attempt)
    height, width = dims
    grid = [[0] * width for _ in range(height)]
    colors = rng.sample(range(1, 10), 3)
    sizes = [rng.choice((6, 7, 8)) for _ in range(3)]
    for panel_index, (left, color, size) in enumerate(zip(PANEL_STARTS, colors, sizes)):
        cells = _grow_shape(rng, size, wide=((index + panel_index + attempt) % 3 == 0))
        for row, col in cells:
            grid[row][left + col] = color
        code_col = left + rng.randrange(5)
        grid[6][code_col] = codes[panel_index]
    _add_distractors(grid, rng, density)
    return grid


def _strong(grid: list[list[int]]) -> bool:
    intended = {name: solve(grid, name) for name in SETTING_NAMES}
    if intended["clockwise"] == intended["counterclockwise"]:
        return False
    for output in intended.values():
        if not {2, 4, 8}.issubset({value for row in output for value in row}):
            return False
    predictions = {name: solve(grid, name) for name in CANDIDATE_NAMES}
    return all([name for name, prediction in predictions.items() if prediction == intended[setting]] == [setting]
               for setting in SETTING_NAMES)


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES if split == "query" else None
    if profiles is None or type(index) is not int or not 0 <= index < len(profiles):
        raise ValueError("invalid split/index")
    dims, codes, density = profiles[index]
    for attempt in range(4096):
        grid = _build_candidate(seed, split, index, attempt, dims, codes, density)
        if _strong(grid):
            if dims == (30, 30) and sum(value != 0 for row in grid for value in row) < 120:
                continue
            return grid
    raise RuntimeError("bounded rotation-direction sampler exhausted")


def generate_episode(seed: int, direction: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if direction not in SETTING_NAMES:
        raise ValueError(f"direction must be one of {SETTING_NAMES}")
    demo_inputs = [sample_input(seed, "demo", index) for index in range(6)]
    query_inputs = [sample_input(seed, "query", index) for index in range(4)]
    keys = [json.dumps(grid, separators=(",", ":")) for grid in demo_inputs + query_inputs]
    if len(keys) != len(set(keys)):
        raise RuntimeError("input sampler produced duplicates")
    pair: Callable[[list[list[int]]], dict[str, Any]] = lambda grid: {
        "input": copy.deepcopy(grid), "output": solve(grid, direction)
    }
    episode = {
        "train": [pair(grid) for grid in demo_inputs[:demos]],
        "test": [pair(grid) for grid in query_inputs[:queries]],
        "program_solution": program_for(direction),
    }
    if teaching_survivors(episode["train"][:2]) != [direction]:
        raise RuntimeError("first two demonstrations do not identify the selected rule")
    return episode


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    return generate_episode(seed, _setting(settings), demos=demos, queries=queries)
