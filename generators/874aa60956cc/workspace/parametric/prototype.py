"""Native matched-input border family for ARC task 874aa60956cc.

The exact canonical setting paints every exactly-twice color's bounding border
in first-appearance order.  The alternate first paints the first paired color,
counts how many later paired colors have an original clue on that derived
border, then uses that count to select one later paired color to paint.
"""
from __future__ import annotations

from copy import deepcopy
from collections import OrderedDict
import hashlib
import json
from pathlib import Path
import random
from typing import Callable

HERE = Path(__file__).resolve().parent
TASK_ID = "874aa60956cc"
PARAMETER = "border_mode"
MODES = ("all", "touch_count_relay")

# size, candidate touch multiplicities (0=no clue on controller border,
# 1=one clue, 2=both clues), and whether the controller spans the canvas edge.
_DEMO_PROFILES = (
    ((9, 10),  (2, 0, 0), False),
    ((11, 12), (1, 1, 0), False),
    ((13, 15), (1, 1, 1), False),
    ((16, 18), (0, 1, 0), False),
    ((20, 22), (1, 0, 1), False),
    ((24, 26), (1, 1, 1), False),
)
_QUERY_PROFILES = (
    ((8, 9),   (0, 1, 0), False),
    ((14, 17), (1, 0, 1), False),
    ((22, 24), (2, 1, 0), False),
    ((30, 30), (1, 1, 1), True),
)


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _mode(settings: dict[str, str]) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {PARAMETER}
        or type(settings[PARAMETER]) is not str
        or settings[PARAMETER] not in MODES
    ):
        raise ValueError(
            "settings must be exactly "
            "{'border_mode': 'all'|'touch_count_relay'}"
        )
    return settings[PARAMETER]


def program(settings: dict[str, str]) -> str:
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "all" else "touch_count_relay.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = json.dumps(
        [TASK_ID, "touch-count-relay-v1", seed, split, index],
        separators=(",", ":"),
    ).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _border(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    r0, r1 = sorted((a[0], b[0]))
    c0, c1 = sorted((a[1], b[1]))
    return [
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    ]


def _groups(grid: list[list[int]]) -> OrderedDict[int, list[tuple[int, int]]]:
    groups: OrderedDict[int, list[tuple[int, int]]] = OrderedDict()
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                groups.setdefault(color, []).append((r, c))
    return groups


def _validate_grid(grid: list[list[int]]) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("grid must have 1..30 rows")
    width = len(grid[0])
    if not 1 <= width <= 30:
        raise ValueError("grid must have 1..30 columns")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integer ARC colors 0..9")
    return [row[:] for row in grid]


def analyze_input(grid: list[list[int]]) -> dict:
    source = _validate_grid(grid)
    groups = _groups(source)
    paired = [color for color, cells in groups.items() if len(cells) == 2]
    if not paired:
        return {
            "paired_colors": [],
            "controller_color": None,
            "candidate_colors": [],
            "controller_border": [],
            "touched_candidate_colors": [],
            "touch_count": 0,
            "selected_color": None,
        }
    controller = paired[0]
    candidates = paired[1:]
    controller_border = set(_border(*groups[controller]))
    touched = [
        color for color in candidates
        if any(cell in controller_border for cell in groups[color])
    ]
    k = len(touched)
    selected = candidates[k - 1] if 1 <= k <= len(candidates) else None
    return {
        "paired_colors": paired,
        "controller_color": controller,
        "candidate_colors": candidates,
        "controller_border": sorted(controller_border),
        "touched_candidate_colors": touched,
        "touch_count": k,
        "touched_clue_count": sum(
            cell in controller_border for color in candidates for cell in groups[color]
        ),
        "selected_color": selected,
        "candidate_first_positions": [groups[color][0] for color in candidates],
        "candidate_second_positions": [groups[color][1] for color in candidates],
    }


def _paint(out: list[list[int]], source: list[list[int]], color: int) -> None:
    groups = _groups(source)
    for r, c in _border(*groups[color]):
        out[r][c] = color


def solve(grid: list[list[int]], policy: str = "all") -> list[list[int]]:
    source = _validate_grid(grid)
    groups = _groups(source)
    paired = [color for color, cells in groups.items() if len(cells) == 2]
    out = deepcopy(source)
    if policy == "all":
        for color in paired:
            _paint(out, source, color)
        return out
    if not paired:
        return out
    controller, candidates = paired[0], paired[1:]
    controller_border = set(_border(*groups[controller]))
    touched = [color for color in candidates
               if any(cell in controller_border for cell in groups[color])]
    distinct_k = len(touched)
    touched_cells = sum(cell in controller_border
                        for color in candidates for cell in groups[color])

    ordered = list(candidates)
    if policy == "completion_order":
        ordered.sort(key=lambda color: groups[color][1])
    elif policy == "numeric_order":
        ordered.sort()

    if policy in {"controller_only"}:
        _paint(out, source, controller)
        return out
    if policy == "last_touched":
        selected = touched[-1] if touched else None
    else:
        if policy in {"touch_count_relay", "selected_only", "completion_order", "numeric_order"}:
            k = distinct_k
        elif policy == "touched_cell_count":
            k = touched_cells
        elif policy.startswith("fixed_") and policy[-1:] in {"1", "2", "3"}:
            k = int(policy[-1])
        else:
            raise ValueError(f"unknown solve policy: {policy}")
        selected = ordered[k - 1] if 1 <= k <= len(ordered) else None

    if policy != "selected_only":
        _paint(out, source, controller)
    if selected is not None:
        _paint(out, source, selected)
    return out


RIVAL_SOLVERS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "all_pairs": lambda grid: solve(grid, "all"),
    "controller_only": lambda grid: solve(grid, "controller_only"),
    "skip_a_selected_only": lambda grid: solve(grid, "selected_only"),
    "fixed_intermediate_1": lambda grid: solve(grid, "fixed_1"),
    "fixed_intermediate_2": lambda grid: solve(grid, "fixed_2"),
    "fixed_intermediate_3": lambda grid: solve(grid, "fixed_3"),
    "count_touched_clue_cells": lambda grid: solve(grid, "touched_cell_count"),
    "select_last_touched_color": lambda grid: solve(grid, "last_touched"),
    "candidate_completion_order": lambda grid: solve(grid, "completion_order"),
    "numeric_color_order": lambda grid: solve(grid, "numeric_order"),
}


def _sample_pair(
    kind: int,
    border_cells: list[tuple[int, int]],
    other_cells: list[tuple[int, int]],
    used: set[tuple[int, int]],
    rng: random.Random,
) -> tuple[tuple[int, int], tuple[int, int]] | None:
    pools = {
        0: (other_cells, other_cells),
        1: (border_cells, other_cells),
        2: (border_cells, border_cells),
    }
    first_pool, second_pool = pools[kind]
    for _ in range(600):
        a = rng.choice(first_pool)
        b = rng.choice(second_pool)
        if a == b or a in used or b in used:
            continue
        if a[0] == b[0] or a[1] == b[1]:
            continue
        return a, b
    return None


def _profile(split: str, index: int):
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    _integer("index", index, 0, len(profiles) - 1)
    return profiles[index]


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    (height, width), touch_multiplicities, boundary_controller = _profile(split, index)
    rng = _rng(seed, split, index)
    for _attempt in range(2000):
        if boundary_controller:
            controller_pair = ((0, 0), (height - 1, width - 1))
        else:
            r0 = rng.randrange(0, min(3, height - 5))
            c0 = rng.randrange(0, min(3, width - 5))
            r1 = rng.randrange(max(r0 + 4, height - 4), height)
            c1 = rng.randrange(max(c0 + 4, width - 4), width)
            controller_pair = ((r0, c0), (r1, c1))
        controller_border = set(_border(*controller_pair))
        used = set(controller_pair)
        all_cells = [(r, c) for r in range(height) for c in range(width)]
        border_cells = [cell for cell in controller_border if cell not in used]
        other_cells = [cell for cell in all_cells if cell not in controller_border]
        rng.shuffle(border_cells)
        rng.shuffle(other_cells)

        raw_pairs = []
        ok = True
        kinds = list(touch_multiplicities)
        rng.shuffle(kinds)
        for kind in kinds:
            pair = _sample_pair(kind, border_cells, other_cells, used, rng)
            if pair is None:
                ok = False
                break
            raw_pairs.append(pair)
            used.update(pair)
        if not ok:
            continue
        candidate_pairs = sorted(raw_pairs, key=lambda pair: min(pair))
        if min(controller_pair) >= min(min(pair) for pair in candidate_pairs):
            continue

        free = [cell for cell in all_cells if cell not in used]
        if len(free) < 4:
            continue
        rng.shuffle(free)
        singleton = [free.pop()]
        triple = [free.pop(), free.pop(), free.pop()]

        colors = rng.sample(range(1, 10), 6)
        controller_color = colors[0]
        candidate_colors = colors[1:4]
        # The first two lessons deliberately make numeric color order a bad proxy.
        if split == "train" and index < 2:
            k = sum(any(cell in controller_border for cell in pair)
                    for pair in candidate_pairs)
            if sorted(candidate_colors)[k - 1] == candidate_colors[k - 1]:
                continue

        grid = [[0] * width for _ in range(height)]
        for color, cells in [
            (controller_color, controller_pair),
            *zip(candidate_colors, candidate_pairs, strict=True),
            (colors[4], singleton),
            (colors[5], triple),
        ]:
            for r, c in cells:
                grid[r][c] = color

        analysis = analyze_input(grid)
        if len(analysis["paired_colors"]) != 4:
            continue
        expected_k = sum(kind > 0 for kind in touch_multiplicities)
        if analysis["touch_count"] != expected_k:
            continue
        intended = solve(grid, "touch_count_relay")
        if intended == solve(grid, "all"):
            continue
        if split == "train" and index == 0:
            # One dense teaching case separates every declared shortcut except
            # fixed-k=1, which the second demonstration separates.
            if any(
                rival(grid) == intended
                for name, rival in RIVAL_SOLVERS.items()
                if name != "fixed_intermediate_1"
            ):
                continue
        if split == "train" and index == 1:
            if RIVAL_SOLVERS["fixed_intermediate_1"](grid) == intended:
                continue
        return grid
    raise RuntimeError(f"could not construct {split}[{index}] after 2000 attempts")


def claimed_output(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    return solve(grid, _mode(settings))


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4) -> dict:
    _integer("seed", seed, 0, 2**63 - 1)
    mode = _mode(settings)
    _integer("demos", demos, 2, len(_DEMO_PROFILES))
    _integer("queries", queries, 1, len(_QUERY_PROFILES))
    train = []
    test = []
    for split, count, target in (("train", demos, train), ("test", queries, test)):
        for index in range(count):
            grid = _scene(seed, split, index)
            target.append({"input": grid, "output": solve(grid, mode)})
    return {"train": train, "test": test, "program_solution": program(settings)}


def public_turn(episode: dict, query_index: int) -> dict:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    train = [
        {"input": _validate_grid(pair["input"]), "output": _validate_grid(pair["output"])}
        for pair in episode["train"]
    ]
    query = {"input": _validate_grid(episode["test"][query_index]["input"])}
    return {"train": train, "test": [query]}


def public_turn_bytes(episode: dict, query_index: int) -> bytes:
    return (
        json.dumps(public_turn(episode, query_index), sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode()


def public_turn_id(episode: dict, query_index: int) -> str:
    return hashlib.sha256(public_turn_bytes(episode, query_index)).hexdigest()
