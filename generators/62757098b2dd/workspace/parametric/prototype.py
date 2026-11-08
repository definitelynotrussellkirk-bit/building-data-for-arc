"""Matched-input palette-scope family for corner-marked gray rectangles.

``local`` is the exact canonical rule: every rectangle reads its own four
markers. ``largest_rectangle`` first finds A: the unique largest gray rectangle
and reads its ordered corner-marker palette, producing that input-dependent
palette as an intermediate. B then erases every marker and fills every
rectangle's quadrants with the selected palette.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "62757098b2dd"
PARAMETER = "palette_scope"
MODES = ("local", "largest_rectangle")
_DIR = Path(__file__).resolve().parent
_PROGRAMS = {
    "local": (_DIR / "canonical.rkt").read_text(encoding="utf-8"),
    "largest_rectangle": (_DIR / "largest_rectangle.rkt").read_text(encoding="utf-8"),
}
_DEMO_DIMS = ((17, 22), (19, 24), (23, 27), (25, 29), (28, 30), (30, 30))
_QUERY_DIMS = ((16, 20), (21, 25), (27, 29), (30, 30))
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError("settings must name exactly palette_scope")
    mode = settings[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"palette_scope must be one of {MODES}")
    return mode


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def program(settings: dict[str, Any]) -> str:
    return _PROGRAMS[_mode(settings)]


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30:
        raise ValueError("grid must fit within 30x30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def _gray_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    }
    components: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells: list[tuple[int, int]] = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in _NEIGHBORS:
                neighbor = (r + dr, c + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
        components.append(sorted(cells))
    return sorted(components, key=min)


def scene_facts(grid: list[list[int]]) -> dict[str, Any]:
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    rectangles: list[dict[str, Any]] = []
    expected_markers: set[tuple[int, int]] = set()
    for cells in _gray_components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
        rh, rw = r2 - r1 + 1, c2 - c1 + 1
        if rh < 2 or rw < 2 or len(cells) != rh * rw:
            raise ValueError("every gray component must be a solid rectangle at least 2x2")
        marker_cells = (
            (r1 - 1, c1 - 1),
            (r1 - 1, c2 + 1),
            (r2 + 1, c1 - 1),
            (r2 + 1, c2 + 1),
        )
        if any(not (0 <= r < height and 0 <= c < width) for r, c in marker_cells):
            raise ValueError("every rectangle needs four in-bounds diagonal markers")
        marker_colors = tuple(grid[r][c] for r, c in marker_cells)
        if any(color in (0, 5) for color in marker_colors) or len(set(marker_colors)) != 4:
            raise ValueError("each rectangle needs four distinct non-{0,5} marker colors")
        if expected_markers.intersection(marker_cells):
            raise ValueError("marker cells may not be shared")
        expected_markers.update(marker_cells)
        rectangles.append({
            "bbox": (r1, c1, r2, c2),
            "height": rh,
            "width": rw,
            "area": rh * rw,
            "perimeter": 2 * (rh + rw),
            "cells": cells,
            "marker_cells": marker_cells,
            "marker_colors": marker_colors,
        })
    rectangles.sort(key=lambda item: item["bbox"][:2])
    actual_markers = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    }
    if actual_markers != expected_markers:
        raise ValueError("non-{0,5} cells must be exactly the rectangle markers")
    if not rectangles:
        raise ValueError("scene requires at least one gray rectangle")
    return {
        "height": height,
        "width": width,
        "rectangles": rectangles,
        "marker_cells": sorted(expected_markers),
    }


def _apply(
    grid: list[list[int]],
    palette_for: Callable[[int, list[dict[str, Any]]], tuple[int, int, int, int]],
    *,
    keep_markers: bool = False,
    ceil_split: bool = False,
    only_anchor: int | None = None,
) -> list[list[int]]:
    facts = scene_facts(grid)
    rectangles = facts["rectangles"]
    output = [row[:] for row in grid]
    for index, rect in enumerate(rectangles):
        if only_anchor is not None and index != only_anchor:
            continue
        if not keep_markers:
            for r, c in rect["marker_cells"]:
                output[r][c] = 0
        r1, c1, r2, c2 = rect["bbox"]
        split_r = r1 + ((rect["height"] + 1) // 2 if ceil_split else rect["height"] // 2)
        split_c = c1 + ((rect["width"] + 1) // 2 if ceil_split else rect["width"] // 2)
        tl, tr, bl, br = palette_for(index, rectangles)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if r < split_r and c < split_c:
                    output[r][c] = tl
                elif r < split_r:
                    output[r][c] = tr
                elif c < split_c:
                    output[r][c] = bl
                else:
                    output[r][c] = br
    return output


def solve_with_anchor(grid: list[list[int]], anchor_index: int) -> list[list[int]]:
    facts = scene_facts(grid)
    _integer("anchor_index", anchor_index, 0, len(facts["rectangles"]) - 1)
    palette = tuple(facts["rectangles"][anchor_index]["marker_colors"])
    return _apply(grid, lambda _index, _rectangles: palette)


def solve(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = _mode(settings)
    facts = scene_facts(grid)
    if mode == "local":
        return _apply(grid, lambda index, rectangles: tuple(rectangles[index]["marker_colors"]))
    anchor = max(range(len(facts["rectangles"])), key=lambda i: facts["rectangles"][i]["area"])
    return solve_with_anchor(grid, anchor)


def quadrant_colors(grid: list[list[int]], bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    r1, c1, r2, c2 = bbox
    return grid[r1][c1], grid[r1][c2], grid[r2][c1], grid[r2][c2]


def intermediate(grid: list[list[int]]) -> dict[str, Any]:
    facts = scene_facts(grid)
    areas = [rect["area"] for rect in facts["rectangles"]]
    anchor = max(range(len(areas)), key=areas.__getitem__)
    return {
        "anchor_index": anchor,
        "anchor_bbox": facts["rectangles"][anchor]["bbox"],
        "marker_colors": facts["rectangles"][anchor]["marker_colors"],
        "areas": areas,
        "rectangles": copy.deepcopy(facts["rectangles"]),
    }


def validate_input(grid: Any) -> list[str]:
    try:
        facts = scene_facts(grid)
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    rects = facts["rectangles"]
    if len(rects) != 3:
        errors.append("parametric grammar requires exactly three rectangles")
    if len(rects) == 3:
        areas = [rect["area"] for rect in rects]
        if areas.count(max(areas)) != 1 or areas.index(max(areas)) != 1:
            errors.append("the unique largest rectangle must be the middle row-major object")
        if rects[0]["perimeter"] <= rects[1]["perimeter"]:
            errors.append("the first rectangle must be a larger-perimeter decoy")
        if len({rect["marker_colors"] for rect in rects}) != 3:
            errors.append("rectangles need distinct ordered marker palettes")
    try:
        if solve(grid, {PARAMETER: "local"}) == solve(grid, {PARAMETER: "largest_rectangle"}):
            errors.append("declared settings must change the output")
    except ValueError as exc:  # pragma: no cover
        errors.append(str(exc))
    return errors


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _shapes(height: int, width: int) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if height >= 30 and width >= 30:
        return (4, 12), (7, 8), (5, 5)
    if height >= 27:
        return (4, 11), (6, 8), (5, 5)
    if height >= 23:
        return (3, 10), (5, 7), (4, 5)
    if height >= 21:
        return (3, 9), (5, 6), (4, 4)
    if height >= 19:
        return (2, 9), (4, 6), (3, 4)
    return (2, 8), (4, 5), (3, 3)


def _paint_rect(
    grid: list[list[int]],
    spec: tuple[int, int, int, int],
    colors: list[int],
) -> None:
    r1, c1, rh, rw = spec
    r2, c2 = r1 + rh - 1, c1 + rw - 1
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if grid[r][c] != 0:
                raise AssertionError("rectangle collision")
            grid[r][c] = 5
    marker_cells = ((r1 - 1, c1 - 1), (r1 - 1, c2 + 1), (r2 + 1, c1 - 1), (r2 + 1, c2 + 1))
    for (r, c), color in zip(marker_cells, colors):
        if grid[r][c] != 0:
            raise AssertionError("marker collision")
        grid[r][c] = color


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    dims = _DEMO_DIMS if split == "train" else _QUERY_DIMS
    if not 0 <= index < len(dims):
        raise ValueError(f"unsupported {split} index {index}")
    height, width = dims[index]
    rng = _rng(seed, split, index)
    first_shape, anchor_shape, last_shape = _shapes(height, width)
    f_h, f_w = first_shape
    a_h, a_w = anchor_shape
    l_h, l_w = last_shape
    first = (1, 1, f_h, f_w)
    anchor_r = max(f_h + 3, height // 2 - a_h // 2)
    anchor = (anchor_r, width - a_w - 2, a_h, a_w)
    last = (height - l_h - 2, 2, l_h, l_w)

    palettes = [[6, 7, 8, 9], [1, 2, 3, 4], [1, 6, 2, 7]]
    for colors in palettes:
        rng.shuffle(colors)
    grid = [[0] * width for _ in range(height)]
    for spec, colors in zip((first, anchor, last), palettes):
        _paint_rect(grid, spec, colors)
    # Horizontal reflection preserves the row-major anchor position while
    # varying boundary contacts and corner roles.
    if rng.randrange(2):
        grid = [list(reversed(row)) for row in grid]
    errors = validate_input(grid)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    mode = _mode(settings)
    train: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []
    seen: set[bytes] = set()
    for split, count, target in (("train", demos, train), ("test", queries, test)):
        for index in range(count):
            grid = _scene(seed, split, index)
            key = json.dumps(grid, separators=(",", ":")).encode()
            if key in seen:
                raise AssertionError("deterministic schedule emitted a duplicate input")
            seen.add(key)
            target.append({"input": grid, "output": solve(grid, {PARAMETER: mode})})
    return {"train": train, "test": test, "program_solution": program({PARAMETER: mode})}


def public_view(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }


def _anchor_by(grid: list[list[int]], key: Callable[[dict[str, Any]], Any], *, reverse: bool = False) -> list[list[int]]:
    rects = scene_facts(grid)["rectangles"]
    anchor = sorted(range(len(rects)), key=lambda i: key(rects[i]), reverse=reverse)[0]
    return solve_with_anchor(grid, anchor)


def _keep_markers_local(grid: list[list[int]]) -> list[list[int]]:
    return _apply(grid, lambda index, rects: tuple(rects[index]["marker_colors"]), keep_markers=True)


def _ceil_split_local(grid: list[list[int]]) -> list[list[int]]:
    return _apply(grid, lambda index, rects: tuple(rects[index]["marker_colors"]), ceil_split=True)


def _largest_only(grid: list[list[int]]) -> list[list[int]]:
    rects = scene_facts(grid)["rectangles"]
    anchor = max(range(len(rects)), key=lambda i: rects[i]["area"])
    palette = tuple(rects[anchor]["marker_colors"])
    return _apply(grid, lambda _index, _rects: palette, only_anchor=anchor)


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "local": lambda grid: solve(grid, {PARAMETER: "local"}),
    "largest_rectangle": lambda grid: solve(grid, {PARAMETER: "largest_rectangle"}),
    "first_rectangle": lambda grid: solve_with_anchor(grid, 0),
    "last_rectangle": lambda grid: solve_with_anchor(grid, 2),
    "largest_perimeter": lambda grid: _anchor_by(grid, lambda rect: rect["perimeter"], reverse=True),
    "smallest_rectangle": lambda grid: _anchor_by(grid, lambda rect: rect["area"]),
    "keep_markers_local": _keep_markers_local,
    "ceil_split_local": _ceil_split_local,
    "largest_only": _largest_only,
}


def audit_episode(seed: int, mode: str, *, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    episode = generate(seed, {PARAMETER: mode}, demos, queries)
    survivors: list[str] = []
    harmful: list[str] = []
    for name, rival in RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in episode["train"]):
            survivors.append(name)
            if any(rival(pair["input"]) != pair["output"] for pair in episode["test"]):
                harmful.append(name)
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {PARAMETER: mode},
        "fit_uses": "demonstrations_only",
        "rivals": sorted(RIVALS),
        "survivors": survivors,
        "harmful_survivors": harmful,
        "query_shapes": [[len(p["input"]), len(p["input"][0])] for p in episode["test"]],
        "intermediate": intermediate(episode["test"][0]["input"]),
    }
