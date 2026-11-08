"""Native finite parametric family for ARC generator bdcb4c9eb6bd.

``all_rectangles`` is the exact canonical rule: fill every one-gap rectangle's
interior red and extend red from its gap to the corresponding canvas edge.
``largest_interior`` first computes the input-dependent interior area of every
rectangle, selects the unique largest one, and applies the same fill-and-ray
operation only to that selected rectangle.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "bdcb4c9eb6bd"
PARAMETER_NAME = "rectangle_scope"
SCOPES = ("all_rectangles", "largest_interior")
DEFAULT_SETTINGS = {PARAMETER_NAME: "all_rectangles"}

_HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (_HOME / "canonical.rkt").read_text(encoding="utf-8")
LARGEST_INTERIOR_PROGRAM = (_HOME / "largest-interior.rkt").read_text(encoding="utf-8")

SHORTCUTS = (
    "smallest_interior",
    "first_rectangle",
    "last_rectangle",
    "largest_outline",
    "all_interiors_no_rays",
    "all_rays_no_interiors",
)
_DIRS = ((-1, 0), (0, -1), (1, 0), (0, 1))
_SIDES = ("up", "right", "down", "left")
_BACKGROUNDS = (3, 4, 5, 6, 7, 8, 9)

# (height, width, rectangles as r,c,h,w)
DEMO_SCENES = (
    (14, 22, ((1, 1, 3, 10), (7, 14, 6, 6))),
    (16, 22, ((1, 1, 7, 5), (10, 12, 4, 9))),
    (18, 24, ((1, 1, 5, 7), (1, 12, 3, 11), (10, 2, 6, 5))),
    (20, 26, ((1, 1, 4, 10), (8, 2, 8, 5), (13, 15, 5, 9))),
    (22, 24, ((0, 1, 6, 6), (8, 0, 5, 12), (15, 15, 6, 8))),
    (24, 28, ((2, 1, 9, 5), (1, 11, 5, 10), (15, 4, 6, 11))),
)
QUERY_SCENES = (
    (15, 25, ((1, 1, 5, 9), (8, 15, 6, 7))),
    (19, 27, ((0, 2, 7, 7), (9, 1, 4, 12), (12, 18, 6, 8))),
    (24, 30, ((1, 1, 8, 6), (2, 13, 5, 12), (15, 4, 7, 10))),
    (30, 30, ((1, 1, 10, 10), (0, 15, 3, 14), (16, 0, 6, 8), (22, 19, 5, 9))),
)


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
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def program(settings: Any) -> str:
    scope = _validate_settings(settings)
    return CANONICAL_PROGRAM if scope == "all_rectangles" else LARGEST_INTERIOR_PROGRAM


def counterfactual_program(kind: str = "largest_outline") -> str:
    if kind != "largest_outline":
        raise ValueError("only largest_outline is retained")
    old = "(selected (pick-max objs (lambda (o) (* (- (obj-h o) 2) (- (obj-w o) 2)))))"
    new = "(selected (pick-max objs obj-size))"
    if LARGEST_INTERIOR_PROGRAM.count(old) != 1:
        raise ValueError("selected-rectangle source guard failed")
    return LARGEST_INTERIOR_PROGRAM.replace(old, new, 1)


def _background(grid: list[list[int]]) -> int:
    counts = Counter(value for row in grid for value in row)
    if not counts:
        raise ValueError("empty grid")
    return counts.most_common(1)[0][0]


def _components_of_one(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1}
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


def rectangle_facts(grid: list[list[int]]) -> list[dict[str, Any]]:
    _validate_grid(grid)
    bg = _background(grid)
    if bg in (1, 2):
        raise ValueError("background must differ from outline 1 and answer 2")
    facts: list[dict[str, Any]] = []
    for cells in _components_of_one(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        height, width = r1 - r0 + 1, c1 - c0 + 1
        if height < 3 or width < 3:
            raise ValueError("rectangle must be at least 3x3")
        perimeter = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        cellset = set(cells)
        missing = sorted(perimeter - cellset)
        if cellset - perimeter or len(missing) != 1:
            raise ValueError("each component must be a rectangle outline with one gap")
        gr, gc = missing[0]
        if gr == r0 and c0 < gc < c1:
            side = "up"
        elif gr == r1 and c0 < gc < c1:
            side = "down"
        elif gc == c0 and r0 < gr < r1:
            side = "left"
        elif gc == c1 and r0 < gr < r1:
            side = "right"
        else:
            raise ValueError("gap must be a non-corner boundary cell")
        facts.append({
            "cells": [list(cell) for cell in cells],
            "bbox": [r0, c0, r1, c1],
            "height": height,
            "width": width,
            "interior_area": (height - 2) * (width - 2),
            "outline_size": len(cells),
            "gap": [gr, gc],
            "open_dir": side,
        })
    facts.sort(key=lambda row: tuple(row["bbox"]))
    if len(facts) < 2:
        raise ValueError("family inputs require at least two rectangles")
    areas = [row["interior_area"] for row in facts]
    if len(areas) != len(set(areas)):
        raise ValueError("family inputs require distinct interior areas")
    return facts


def largest_interior_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    facts = rectangle_facts(grid)
    index = max(range(len(facts)), key=lambda i: facts[i]["interior_area"])
    return {
        "selected_index": index,
        "selected_bbox": facts[index]["bbox"],
        "selected_interior_area": facts[index]["interior_area"],
        "selected_outline_size": facts[index]["outline_size"],
        "rectangles": [
            {
                "bbox": row["bbox"],
                "interior_area": row["interior_area"],
                "outline_size": row["outline_size"],
                "gap": row["gap"],
                "open_dir": row["open_dir"],
            }
            for row in facts
        ],
    }


def _apply_facts(
    grid: list[list[int]],
    facts: list[dict[str, Any]],
    selected_indices: set[int],
    *,
    interiors: bool = True,
    rays: bool = True,
) -> list[list[int]]:
    bg = _background(grid)
    h, w = len(grid), len(grid[0])
    result = copy.deepcopy(grid)
    for index, fact in enumerate(facts):
        if index not in selected_indices:
            continue
        r0, c0, r1, c1 = fact["bbox"]
        if interiors:
            for r in range(r0 + 1, r1):
                for c in range(c0 + 1, c1):
                    if result[r][c] == bg:
                        result[r][c] = 2
        if not rays:
            continue
        gr, gc = fact["gap"]
        side = fact["open_dir"]
        if side == "left":
            points = ((gr, c) for c in range(0, c0 + 1))
        elif side == "right":
            points = ((gr, c) for c in range(c1, w))
        elif side == "up":
            points = ((r, gc) for r in range(0, r0 + 1))
        else:
            points = ((r, gc) for r in range(r1, h))
        for r, c in points:
            if result[r][c] == bg:
                result[r][c] = 2
    return result


def transform(grid: list[list[int]], settings: Any) -> list[list[int]]:
    scope = _validate_settings(settings)
    facts = rectangle_facts(grid)
    if scope == "all_rectangles":
        selected = set(range(len(facts)))
    else:
        selected = {largest_interior_intermediate(grid)["selected_index"]}
    return _apply_facts(grid, facts, selected)


def _draw_rectangle(
    grid: list[list[int]],
    rect: tuple[int, int, int, int],
    side: str,
    offset: int,
    background: int,
) -> None:
    r0, c0, height, width = rect
    r1, c1 = r0 + height - 1, c0 + width - 1
    for c in range(c0, c1 + 1):
        grid[r0][c] = 1
        grid[r1][c] = 1
    for r in range(r0, r1 + 1):
        grid[r][c0] = 1
        grid[r][c1] = 1
    if side == "up":
        gap = (r0, c0 + offset)
    elif side == "down":
        gap = (r1, c0 + offset)
    elif side == "left":
        gap = (r0 + offset, c0)
    elif side == "right":
        gap = (r0 + offset, c1)
    else:
        raise ValueError(side)
    grid[gap[0]][gap[1]] = background


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    scenes = DEMO_SCENES if split == "train" else QUERY_SCENES
    height, width, rectangles = scenes[index]
    rng = random.Random(f"{TASK_ID}:{seed}:{split}:{index}")
    background = _BACKGROUNDS[rng.randrange(len(_BACKGROUNDS))]
    grid = [[background] * width for _ in range(height)]
    side_offset = rng.randrange(4)
    for rect_index, rect in enumerate(rectangles):
        r0, c0, rh, rw = rect
        if r0 < 0 or c0 < 0 or r0 + rh > height or c0 + rw > width:
            raise RuntimeError("rectangle escaped scene")
        side = _SIDES[(side_offset + rect_index + index) % 4]
        span = rw if side in ("up", "down") else rh
        local_rng = random.Random(f"{TASK_ID}:{seed}:{split}:{index}:{rect_index}:gap")
        gap_offset = local_rng.randint(1, span - 2)
        _draw_rectangle(grid, rect, side, gap_offset, background)
    facts = rectangle_facts(grid)
    if len(facts) != len(rectangles):
        raise RuntimeError("rectangle objects touched")
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


def shortcut_output(grid: list[list[int]], shortcut: str) -> list[list[int]]:
    facts = rectangle_facts(grid)
    if shortcut == "smallest_interior":
        selected = {min(range(len(facts)), key=lambda i: facts[i]["interior_area"])}
        return _apply_facts(grid, facts, selected)
    if shortcut == "first_rectangle":
        return _apply_facts(grid, facts, {0})
    if shortcut == "last_rectangle":
        return _apply_facts(grid, facts, {len(facts) - 1})
    if shortcut == "largest_outline":
        selected = {max(range(len(facts)), key=lambda i: facts[i]["outline_size"])}
        return _apply_facts(grid, facts, selected)
    if shortcut == "all_interiors_no_rays":
        return _apply_facts(grid, facts, set(range(len(facts))), interiors=True, rays=False)
    if shortcut == "all_rays_no_interiors":
        return _apply_facts(grid, facts, set(range(len(facts))), interiors=False, rays=True)
    raise ValueError(shortcut)


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
        "scope": "finite two-setting family plus six named shortcuts; not universal uniqueness",
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
