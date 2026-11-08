"""Matched-input nearest/farthest barrier routing family for 49f2e1c9f51a."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import normalize_grid, public_challenge_bytes


HOME = Path(__file__).resolve().parent
TASK_ID = "49f2e1c9f51a"
MODES = ("nearest", "farthest")
SETTINGS = tuple({"turn_barrier": mode} for mode in MODES)
RIVALS = (
    "middle_barrier",
    "border_pivot",
    "after_nearest",
    "after_farthest",
    "target_axis",
    "nearest_without_restore",
    "farthest_without_restore",
)
CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text(encoding="utf-8")
FARTHEST_PROGRAM = (HOME / "farthest_barrier.rkt").read_text(encoding="utf-8")

# Six demonstrations followed by four independently revealable queries.
_PROFILES = (
    (12, 16, "horizontal", 1),
    (16, 13, "vertical", -1),
    (14, 18, "horizontal", -1),
    (18, 14, "vertical", 1),
    (20, 22, "horizontal", 1),
    (22, 20, "vertical", -1),
    (17, 23, "horizontal", -1),
    (24, 19, "vertical", 1),
    (21, 27, "horizontal", 1),
    (30, 30, "vertical", -1),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def mode_from_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"turn_barrier"}:
        raise ValueError("settings must contain only turn_barrier")
    mode = settings["turn_barrier"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("turn_barrier must be nearest or farthest")
    return mode


def program(settings: Any) -> str:
    return CANONICAL_PROGRAM if mode_from_settings(settings) == "nearest" else FARTHEST_PROGRAM


def _rng(seed: int, index: int) -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}:{seed}:{index}".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def _line_cells(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    r0, c0 = a
    r1, c1 = b
    if r0 == r1:
        return [(r0, c) for c in range(min(c0, c1), max(c0, c1) + 1)]
    if c0 == c1:
        return [(r, c0) for r in range(min(r0, r1), max(r0, r1) + 1)]
    raise ValueError("line endpoints must be cardinally aligned")


def _segment(cells: list[tuple[int, int]]) -> str:
    if len(cells) != 2:
        raise ValueError("source and target must each contain two cells")
    cells = sorted(cells)
    if cells[0][0] == cells[1][0] and cells[0][1] + 1 == cells[1][1]:
        return "horizontal"
    if cells[0][1] == cells[1][1] and cells[0][0] + 1 == cells[1][0]:
        return "vertical"
    raise ValueError("source and target must be straight adjacent segments")


def _facts(grid: list[list[int]]) -> dict[str, Any]:
    grid = normalize_grid(grid)
    height, width = len(grid), len(grid[0])
    threes = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    twos = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    source_orientation = _segment(threes)
    if _segment(twos) != source_orientation:
        raise ValueError("source and target orientations must match")
    r3a, r3b = min(r for r, _ in threes), max(r for r, _ in threes)
    c3a, c3b = min(c for _, c in threes), max(c for _, c in threes)
    r2a, r2b = min(r for r, _ in twos), max(r for r, _ in twos)
    c2a, c2b = min(c for _, c in twos), max(c for _, c in twos)
    horizontal = source_orientation == "horizontal"
    dc = (1 if c2a + c2b >= c3a + c3b else -1) if horizontal else 0
    dr = 0 if horizontal else (1 if r2a + r2b > r3a + r3b else -1)
    start = (r3a, c3b if dc == 1 else c3a) if horizontal else (r3b if dr == 1 else r3a, c3a)
    target = (r2a, c2b if dc == 1 else c2a) if horizontal else (r2a if dr == 1 else r2b, c2a)
    ray = []
    row, col = start
    while True:
        row, col = row + dr, col + dc
        if not (0 <= row < height and 0 <= col < width):
            break
        ray.append((row, col))
    barriers = [cell for cell in ray if grid[cell[0]][cell[1]] != 0]
    if len(barriers) < 3:
        raise ValueError("family inputs require at least three barriers on the source ray")
    return {
        "grid": grid,
        "height": height,
        "width": width,
        "threes": sorted(threes),
        "twos": sorted(twos),
        "orientation": source_orientation,
        "dr": dr,
        "dc": dc,
        "start": start,
        "target": target,
        "ray": ray,
        "barriers": barriers,
    }


def _pivot_before(barrier: tuple[int, int], dr: int, dc: int) -> tuple[int, int]:
    return barrier[0] - dr, barrier[1] - dc


def _solve_policy(grid: list[list[int]], policy: str, *, restore: bool = True) -> tuple[list[list[int]], dict[str, Any]]:
    facts = _facts(grid)
    barriers = facts["barriers"]
    if policy == "nearest":
        selected = barriers[0]
        pivot = _pivot_before(selected, facts["dr"], facts["dc"])
    elif policy == "farthest":
        selected = barriers[-1]
        pivot = _pivot_before(selected, facts["dr"], facts["dc"])
    elif policy == "middle_barrier":
        selected = barriers[len(barriers) // 2]
        pivot = _pivot_before(selected, facts["dr"], facts["dc"])
    elif policy == "border_pivot":
        selected = None
        pivot = facts["ray"][-1]
    elif policy == "after_nearest":
        selected = barriers[0]
        pivot = selected
    elif policy == "after_farthest":
        selected = barriers[-1]
        pivot = selected
    elif policy == "target_axis":
        selected = None
        pivot = ((facts["start"][0], facts["target"][1])
                 if facts["orientation"] == "horizontal"
                 else (facts["target"][0], facts["start"][1]))
    else:
        raise ValueError(f"unknown pivot policy: {policy}")
    corner2 = ((facts["target"][0], pivot[1])
               if facts["orientation"] == "horizontal"
               else (pivot[0], facts["target"][1]))
    path = list(dict.fromkeys(
        _line_cells(facts["start"], pivot)
        + _line_cells(pivot, corner2)
        + _line_cells(corner2, facts["target"])
    ))
    output = deepcopy(facts["grid"])
    for row, col in path:
        output[row][col] = 3
    if restore:
        for row, col in facts["twos"]:
            output[row][col] = 2
    intermediate = {
        "orientation": facts["orientation"],
        "direction": [facts["dr"], facts["dc"]],
        "start": list(facts["start"]),
        "target": list(facts["target"]),
        "barriers": [list(cell) for cell in barriers],
        "selected_barrier": list(selected) if selected is not None else None,
        "pivot": list(pivot),
        "corner2": list(corner2),
        "path_length": len(path),
    }
    return output, intermediate


def solve(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError("mode must be nearest or farthest")
    return _solve_policy(grid, mode)[0]


def dependency_intermediate(grid: list[list[int]], mode: str) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError("mode must be nearest or farthest")
    return _solve_policy(grid, mode)[1]


def rival_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {
        "middle_barrier": _solve_policy(grid, "middle_barrier")[0],
        "border_pivot": _solve_policy(grid, "border_pivot")[0],
        "after_nearest": _solve_policy(grid, "after_nearest")[0],
        "after_farthest": _solve_policy(grid, "after_farthest")[0],
        "target_axis": _solve_policy(grid, "target_axis")[0],
        "nearest_without_restore": _solve_policy(grid, "nearest", restore=False)[0],
        "farthest_without_restore": _solve_policy(grid, "farthest", restore=False)[0],
    }


def _barrier_distances(max_steps: int, rng: random.Random) -> tuple[int, int, int]:
    choices = [
        (a, b, c)
        for a in range(3, max_steps - 3)
        for b in range(a + 2, max_steps - 1)
        for c in range(b + 2, max_steps)
    ]
    if not choices:
        raise ValueError("canvas is too short for three separated barriers")
    return rng.choice(choices)


def _scene(seed: int, index: int) -> list[list[int]]:
    height, width, orientation, direction = _PROFILES[index]
    rng = _rng(seed, index)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    if orientation == "horizontal":
        rows = list(range(2, height - 2))
        source_row = rng.choice(rows)
        target_rows = [r for r in rows if abs(r - source_row) >= 3]
        target_row = rng.choice(target_rows)
        if direction == 1:
            source = [(source_row, 1), (source_row, 2)]
            target = [(target_row, width - 3), (target_row, width - 2)]
            start = source[-1]
        else:
            source = [(source_row, width - 3), (source_row, width - 2)]
            target = [(target_row, 1), (target_row, 2)]
            start = source[0]
        dr, dc = 0, direction
    else:
        cols = list(range(2, width - 2))
        source_col = rng.choice(cols)
        target_cols = [c for c in cols if abs(c - source_col) >= 3]
        target_col = rng.choice(target_cols)
        if direction == 1:
            source = [(1, source_col), (2, source_col)]
            target = [(height - 3, target_col), (height - 2, target_col)]
            start = source[-1]
        else:
            source = [(height - 3, source_col), (height - 2, source_col)]
            target = [(1, target_col), (2, target_col)]
            start = source[0]
        dr, dc = direction, 0
    for row, col in source:
        grid[row][col] = 3
    for row, col in target:
        grid[row][col] = 2

    max_steps = (height - 1 - start[0] if dr == 1 else start[0] if dr == -1
                 else width - 1 - start[1] if dc == 1 else start[1])
    distances = _barrier_distances(max_steps, rng)
    barriers = [(start[0] + dr * d, start[1] + dc * d) for d in distances]
    for row, col in barriers:
        grid[row][col] = 8

    # Put explicit distractors on the second leg for both rule settings.
    for barrier in (barriers[0], barriers[-1]):
        pivot = _pivot_before(barrier, dr, dc)
        if orientation == "horizontal":
            row = (source[0][0] + target[0][0]) // 2
            cell = (row, pivot[1])
        else:
            col = (source[0][1] + target[0][1]) // 2
            cell = (pivot[0], col)
        if cell not in source and cell not in target:
            grid[cell[0]][cell[1]] = 8

    # Preserve the entire source-facing ray so its three authored barriers are exact.
    protected = set(source) | set(target)
    row, col = start
    while True:
        row, col = row + dr, col + dc
        if not (0 <= row < height and 0 <= col < width):
            break
        protected.add((row, col))
    target_noise = max(8, round(height * width * (0.06 if index < 9 else 0.11)))
    candidates = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in protected and grid[r][c] == 0
    ]
    rng.shuffle(candidates)
    current = sum(value == 8 for row_values in grid for value in row_values)
    for row, col in candidates[: max(0, target_noise - current)]:
        grid[row][col] = 8
    if index == 9:
        for cell in ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)):
            if cell not in protected:
                grid[cell[0]][cell[1]] = 8
    # Fail while authoring if any accidental edit made the intended family invalid.
    facts = _facts(grid)
    if len(facts["barriers"]) != 3:
        raise AssertionError((index, facts["barriers"], barriers))
    return grid


@lru_cache(maxsize=128)
def _episode_inputs_cached(seed: int) -> tuple[tuple[tuple[int, ...], ...], ...]:
    return tuple(tuple(tuple(row) for row in _scene(seed, index)) for index in range(len(_PROFILES)))


def episode_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    grids = [[list(row) for row in frozen] for frozen in _episode_inputs_cached(seed)]
    return {"train": grids[:6], "test": grids[6:]}


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    mode = mode_from_settings(settings)
    inputs = episode_inputs(seed)
    train = [{"input": deepcopy(grid), "output": solve(grid, mode)} for grid in inputs["train"][:demos]]
    test = [{"input": deepcopy(grid), "output": solve(grid, mode)} for grid in inputs["test"][:queries]]
    return {"train": train, "test": test, "program_solution": program(settings)}


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    visible = {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
    return json.loads(public_challenge_bytes(visible))


def execute_racket(source: str, grid: list[list[int]], bridge: Any) -> list[list[int]]:
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({wrap_rule(source)} {literal})"))
