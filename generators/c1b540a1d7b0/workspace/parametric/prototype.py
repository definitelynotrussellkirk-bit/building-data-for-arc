"""Native finite parametric family for ARC generator c1b540a1d7b0.

``all_components`` is the exact canonical rule: identify straight three-cell
arms in every gray component, paint arms red (2), and paint the remaining gray
cells cyan (8). ``largest_component`` first recovers the uniquely largest gray
component by occupied-cell count, then applies the same room/arm classification
only to that selected component while leaving the other gray components intact.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "c1b540a1d7b0"
PARAMETER_NAME = "component_scope"
SCOPES = ("all_components", "largest_component")
DEFAULT_SETTINGS = {PARAMETER_NAME: "all_components"}

_HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (_HOME / "canonical.rkt").read_text(encoding="utf-8")
LARGEST_COMPONENT_PROGRAM = (_HOME / "largest-component.rkt").read_text(encoding="utf-8")

SHORTCUTS = (
    "smallest_component",
    "first_component",
    "last_component",
    "topmost_component",
    "bottommost_component",
    "all_red",
    "all_cyan",
)

_DIRS = ((-1, 0), (0, -1), (1, 0), (0, 1))


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain only {PARAMETER_NAME}")
    scope = settings[PARAMETER_NAME]
    if type(scope) is not str or scope not in SCOPES:
        raise ValueError(f"{PARAMETER_NAME} must be one of {SCOPES}")
    return scope


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or cell not in (0, 5) for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular over colors {0,5}")
    return grid


def program(settings: Any) -> str:
    scope = _validate_settings(settings)
    return CANONICAL_PROGRAM if scope == "all_components" else LARGEST_COMPONENT_PROGRAM


def counterfactual_program(kind: str = "smallest_component") -> str:
    if kind != "smallest_component":
        raise ValueError("only smallest_component is retained")
    old = "(selected (pick-max components obj-size))"
    new = "(selected (pick-min components obj-size))"
    if LARGEST_COMPONENT_PROGRAM.count(old) != 1:
        raise ValueError("selected-component source guard failed")
    return LARGEST_COMPONENT_PROGRAM.replace(old, new, 1)


def components5(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    _validate_grid(grid)
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    result: list[list[tuple[int, int]]] = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        stack = [first]
        cells: list[tuple[int, int]] = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in _DIRS:
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    stack.append(point)
        result.append(sorted(cells))
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = list(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def largest_component_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    comps = components5(grid)
    if len(comps) < 2:
        raise ValueError("family inputs require at least two gray components")
    sizes = [len(comp) for comp in comps]
    if len(sizes) != len(set(sizes)):
        raise ValueError("family inputs require distinct component sizes")
    index = max(range(len(comps)), key=lambda i: sizes[i])
    return {
        "selected_index": index,
        "selected_size": sizes[index],
        "selected_bbox": list(_bbox(comps[index])),
        "component_sizes": sizes,
        "selected_cells": [list(cell) for cell in comps[index]],
    }


def _canonical_transform(grid: list[list[int]]) -> list[list[int]]:
    _validate_grid(grid)
    h, w = len(grid), len(grid[0])

    def sh(r: int, c: int) -> bool:
        return 0 <= r < h and 0 <= c < w and grid[r][c] == 5

    def in2x2(r: int, c: int) -> bool:
        return any(
            sh(r + dr, c + dc)
            and sh(r + dr, c + dc + 1)
            and sh(r + dr + 1, c + dc)
            and sh(r + dr + 1, c + dc + 1)
            for dr in (-1, 0)
            for dc in (-1, 0)
        )

    red: set[tuple[int, int]] = set()

    def add_arm(r: int, c: int, dr: int, dc: int) -> None:
        for k in range(3):
            point = (r + dr * k, c + dc * k)
            if sh(*point):
                red.add(point)

    for r in range(h):
        for c in range(w):
            if sh(r, c):
                neighbors = [(dr, dc) for dr, dc in _DIRS if sh(r + dr, c + dc)]
                if len(neighbors) == 1:
                    add_arm(r, c, *neighbors[0])
    for r in range(h):
        for c in range(w):
            if sh(r, c) and not in2x2(r, c) and (r, c) not in red:
                chosen = next(
                    (
                        (dr, dc)
                        for dr, dc in _DIRS
                        if sh(r + dr, c + dc) and in2x2(r + dr, c + dc)
                    ),
                    None,
                )
                if chosen is not None:
                    add_arm(r, c, *chosen)
    return [
        [2 if (r, c) in red else (8 if grid[r][c] == 5 else grid[r][c]) for c in range(w)]
        for r in range(h)
    ]


def _transform_selected(grid: list[list[int]], selected: list[tuple[int, int]]) -> list[list[int]]:
    canonical = _canonical_transform(grid)
    selected_set = set(selected)
    return [
        [
            canonical[r][c] if (r, c) in selected_set else grid[r][c]
            for c in range(len(grid[0]))
        ]
        for r in range(len(grid))
    ]


def transform(grid: list[list[int]], settings: Any) -> list[list[int]]:
    scope = _validate_settings(settings)
    if scope == "all_components":
        return _canonical_transform(grid)
    intermediate = largest_component_intermediate(grid)
    selected = [tuple(cell) for cell in intermediate["selected_cells"]]
    return _transform_selected(grid, selected)


def _normalise(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = list(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _room(cells: set[tuple[int, int]], r: int, c: int) -> None:
    cells.update({(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)})


def _templates() -> dict[str, tuple[tuple[int, int], ...]]:
    result: dict[str, tuple[tuple[int, int], ...]] = {}

    small: set[tuple[int, int]] = set()
    _room(small, 0, 0)
    small.update({(0, 2), (0, 3), (0, 4)})
    result["small"] = _normalise(small)

    medium: set[tuple[int, int]] = set()
    _room(medium, 3, 3)
    medium.update({(2, 3), (1, 3), (0, 3)})
    medium.update({(4, 2), (4, 1), (4, 0)})
    medium.update({(3, 5), (3, 6), (3, 7)})
    result["medium"] = _normalise(medium)

    chain2: set[tuple[int, int]] = set()
    _room(chain2, 3, 3)
    _room(chain2, 3, 8)
    chain2.update({(3, 5), (3, 6), (3, 7)})
    chain2.update({(2, 3), (1, 3), (0, 3)})
    chain2.update({(5, 9), (6, 9), (7, 9)})
    chain2.update({(4, 10), (4, 11), (4, 12)})
    result["chain2"] = _normalise(chain2)

    chain3: set[tuple[int, int]] = set()
    for c in (3, 8, 13):
        _room(chain3, 3, c)
    chain3.update({(3, 5), (3, 6), (3, 7), (3, 10), (3, 11), (3, 12)})
    chain3.update({(2, 3), (1, 3), (0, 3)})
    chain3.update({(5, 9), (6, 9), (7, 9)})
    chain3.update({(4, 15), (4, 16), (4, 17)})
    chain3.update({(4, 2), (4, 1), (4, 0)})
    result["chain3"] = _normalise(chain3)

    mega: set[tuple[int, int]] = set()
    for r in (3, 8):
        for c in (3, 8, 13):
            _room(mega, r, c)
    for r in (3, 8):
        mega.update({(r, 5), (r, 6), (r, 7), (r, 10), (r, 11), (r, 12)})
    for c in (3, 8, 13):
        mega.update({(5, c), (6, c), (7, c)})
    mega.update({(2, 3), (1, 3), (0, 3)})
    mega.update({(3, 15), (3, 16), (3, 17)})
    mega.update({(9, 2), (9, 1), (9, 0)})
    mega.update({(10, 14), (11, 14), (12, 14)})
    result["mega"] = _normalise(mega)
    return result


TEMPLATES = _templates()

# (height, width, ((template, row, col), ...))
DEMO_SCENES = (
    (16, 26, (("small", 0, 0), ("chain3", 8, 8))),
    (18, 26, (("chain2", 0, 0), ("small", 11, 21))),
    (20, 28, (("medium", 0, 20), ("chain3", 12, 0))),
    (20, 30, (("chain3", 0, 0), ("medium", 12, 22))),
    (22, 28, (("small", 0, 23), ("chain2", 10, 0), ("medium", 12, 20))),
    (24, 30, (("chain3", 0, 12), ("chain2", 14, 0), ("small", 20, 25))),
)
QUERY_SCENES = (
    (18, 28, (("chain2", 0, 15), ("small", 13, 0))),
    (22, 30, (("chain3", 0, 0), ("medium", 13, 22), ("small", 19, 0))),
    (26, 30, (("medium", 0, 0), ("chain2", 9, 0), ("chain3", 18, 12))),
    (30, 30, (("mega", 0, 0), ("medium", 15, 0), ("chain3", 22, 12))),
)


def _transform_cells(cells: tuple[tuple[int, int], ...], variant: int) -> tuple[tuple[int, int], ...]:
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    if variant % 4 == 0:
        changed = cells
    elif variant % 4 == 1:
        changed = tuple((r, w - 1 - c) for r, c in cells)
    elif variant % 4 == 2:
        changed = tuple((h - 1 - r, c) for r, c in cells)
    else:
        changed = tuple((h - 1 - r, w - 1 - c) for r, c in cells)
    return _normalise(changed)


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    scenes = DEMO_SCENES if split == "train" else QUERY_SCENES
    h, w, placements = scenes[index]
    grid = [[0] * w for _ in range(h)]
    for part_index, (name, r0, c0) in enumerate(placements):
        rng = random.Random(f"{TASK_ID}:{seed}:{split}:{index}:{part_index}")
        cells = _transform_cells(TEMPLATES[name], rng.randrange(4))
        for dr, dc in cells:
            r, c = r0 + dr, c0 + dc
            if not (0 <= r < h and 0 <= c < w):
                raise RuntimeError(f"{name} placement escaped {h}x{w}")
            if grid[r][c] != 0:
                raise RuntimeError("component placement overlap")
            grid[r][c] = 5
    comps = components5(grid)
    if len(comps) != len(placements):
        raise RuntimeError(f"components touched: expected {len(placements)}, got {len(comps)}")
    sizes = [len(comp) for comp in comps]
    if len(sizes) != len(set(sizes)):
        raise RuntimeError("component sizes must be unique")
    return grid


def sample_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    return {
        "train": [_scene(seed, "train", i) for i in range(len(DEMO_SCENES))],
        "test": [_scene(seed, "test", i) for i in range(len(QUERY_SCENES))],
    }


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)
    _validate_settings(settings)
    sampled = sample_inputs(seed)
    return {
        "train": [
            {"input": copy.deepcopy(grid), "output": transform(grid, settings)}
            for grid in sampled["train"][:demos]
        ],
        "test": [
            {"input": copy.deepcopy(grid), "output": transform(grid, settings)}
            for grid in sampled["test"][:queries]
        ],
        "program_solution": program(settings),
    }


def _select_shortcut(grid: list[list[int]], shortcut: str) -> list[tuple[int, int]]:
    comps = components5(grid)
    if shortcut == "smallest_component":
        return min(comps, key=len)
    if shortcut == "first_component":
        return comps[0]
    if shortcut == "last_component":
        return comps[-1]
    if shortcut == "topmost_component":
        return min(comps, key=lambda c: _bbox(c)[0])
    if shortcut == "bottommost_component":
        return max(comps, key=lambda c: _bbox(c)[2])
    raise ValueError(shortcut)


def shortcut_output(grid: list[list[int]], shortcut: str) -> list[list[int]]:
    if shortcut in {
        "smallest_component",
        "first_component",
        "last_component",
        "topmost_component",
        "bottommost_component",
    }:
        return _transform_selected(grid, _select_shortcut(grid, shortcut))
    if shortcut == "all_red":
        return [[2 if value == 5 else value for value in row] for row in grid]
    if shortcut == "all_cyan":
        return [[8 if value == 5 else value for value in row] for row in grid]
    raise ValueError(f"unknown shortcut: {shortcut}")


def lesson_certificate(train: list[dict[str, Any]], query_inputs: list[list[list[int]]]) -> dict[str, Any]:
    if type(train) is not list or not train:
        raise ValueError("train must contain demonstrations")
    if type(query_inputs) is not list or not query_inputs:
        raise ValueError("query_inputs must contain at least one grid")
    candidates = [{PARAMETER_NAME: value} for value in SCOPES]
    survivors: list[dict[str, str]] = []
    settings_rows: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        predictions = [transform(pair["input"], candidate) for pair in train]
        fits = all(pred == pair["output"] for pred, pair in zip(predictions, train))
        key = candidate[PARAMETER_NAME]
        settings_rows[key] = {
            "fits_all_demos": fits,
            "first_eliminating_demo": next(
                (i for i, (pred, pair) in enumerate(zip(predictions, train)) if pred != pair["output"]),
                None,
            ),
        }
        if fits:
            survivors.append(copy.deepcopy(candidate))
    intended = survivors[0] if len(survivors) == 1 else None
    surviving_shortcuts: list[str] = []
    shortcut_rows: dict[str, dict[str, Any]] = {}
    for shortcut in SHORTCUTS:
        predictions = [shortcut_output(pair["input"], shortcut) for pair in train]
        fits = all(pred == pair["output"] for pred, pair in zip(predictions, train))
        if fits:
            surviving_shortcuts.append(shortcut)
        disagreements = None
        if intended is not None:
            disagreements = sum(
                shortcut_output(grid, shortcut) != transform(grid, intended)
                for grid in query_inputs
            )
        shortcut_rows[shortcut] = {
            "fits_all_demos": fits,
            "first_eliminating_demo": next(
                (i for i, (pred, pair) in enumerate(zip(predictions, train)) if pred != pair["output"]),
                None,
            ),
            "query_disagreements": disagreements,
        }
    return {
        "surviving_settings": survivors,
        "declared_settings": settings_rows,
        "surviving_shortcuts": surviving_shortcuts,
        "shortcuts": shortcut_rows,
        "query_outputs_consulted": False,
        "scope": "finite two-setting family plus seven named shortcuts; not universal uniqueness",
    }


def public_projection(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return (json.dumps(public_projection(episode), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def public_id(episode: dict[str, Any]) -> str:
    return hashlib.sha256(public_bytes(episode)).hexdigest()


def visible_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    _exact_int(query_index, "query_index", 0, len(episode["test"]) - 1)
    return public_projection({"train": episode["train"], "test": [episode["test"][query_index]]})


def visible_turn_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    return (json.dumps(visible_turn(episode, query_index), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
