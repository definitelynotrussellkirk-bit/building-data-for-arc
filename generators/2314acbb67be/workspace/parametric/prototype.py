"""Matched-input family for motif ranking followed by horizontal packing.

``cell_count`` is the byte-identical canonical rule. ``bounding_box_area``
changes only step A: it ranks each discovered motif by its crop area instead of
its occupied-cell count. Step B consumes the resulting ordered crop list and
packs those crops left-to-right with a one-column gap.
"""
from __future__ import annotations

from collections import deque
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "2314acbb67be"
PARAMETER = "order_key"
MODES = ("cell_count", "bounding_box_area")
_DIR = Path(__file__).resolve().parent
_PROGRAMS = {
    "cell_count": (_DIR / "canonical.rkt").read_text(encoding="utf-8"),
    "bounding_box_area": (_DIR / "bounding_box_area.rkt").read_text(encoding="utf-8"),
}
_DEMO_DIMS = ((10, 14), (12, 17), (15, 20), (18, 23), (24, 27), (30, 30))
_QUERY_DIMS = ((10, 14), (16, 20), (24, 27), (30, 30))
_PALETTE = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError("settings must name exactly order_key")
    mode = settings[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"order_key must be one of {MODES}")
    return mode


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
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


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    objects: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        queue = deque([start])
        cells = [start]
        while queue:
            r, c = queue.popleft()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                    unseen.remove(nxt)
                    queue.append(nxt)
                    cells.append(nxt)
        r1 = min(r for r, _ in cells)
        r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        c2 = max(c for _, c in cells)
        crop = [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]
        objects.append({
            "color": color,
            "cells": [list(cell) for cell in sorted(cells)],
            "cell_count": len(cells),
            "bbox_area": (r2 - r1 + 1) * (c2 - c1 + 1),
            "r1": r1,
            "c1": c1,
            "height": r2 - r1 + 1,
            "width": c2 - c1 + 1,
            "crop": crop,
        })
    if not objects:
        raise ValueError("input must contain motifs")
    return objects


def _ordered(objects: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    score_name = "cell_count" if mode == "cell_count" else "bbox_area"
    return sorted(objects, key=lambda obj: (-obj[score_name], obj["c1"], obj["r1"], obj["color"]))


def _pack(objects: list[dict[str, Any]], *, gap: int = 1) -> list[list[int]]:
    if not objects:
        raise ValueError("cannot pack an empty object list")
    out_h = max(obj["height"] for obj in objects)
    out_w = sum(obj["width"] for obj in objects) + gap * (len(objects) - 1)
    if out_h > 30 or out_w > 30:
        raise ValueError("packed output must fit within 30x30")
    output = [[0] * out_w for _ in range(out_h)]
    c0 = 0
    for obj in objects:
        for r, row in enumerate(obj["crop"]):
            for c, value in enumerate(row):
                if value:
                    output[r][c0 + c] = value
        c0 += obj["width"] + gap
    return output


def solve(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = _mode(settings)
    return _pack(_ordered(_components(grid), mode))


def intermediate(grid: list[list[int]], settings: dict[str, Any]) -> dict[str, Any]:
    mode = _mode(settings)
    objects = _components(grid)
    ordered = _ordered(objects, mode)
    return {
        "mode": mode,
        "score_name": "cell_count" if mode == "cell_count" else "bbox_area",
        "objects": copy.deepcopy(objects),
        "ordered_objects": copy.deepcopy(ordered),
        "ordered_colors": [obj["color"] for obj in ordered],
        "ordered_scores": [obj["cell_count"] if mode == "cell_count" else obj["bbox_area"] for obj in ordered],
    }


def output_from_intermediate(value: dict[str, Any]) -> list[list[int]]:
    if type(value) is not dict or type(value.get("ordered_objects")) is not list:
        raise ValueError("intermediate must contain ordered_objects")
    objects = value["ordered_objects"]
    required = {"height", "width", "crop"}
    if any(type(obj) is not dict or not required <= set(obj) for obj in objects):
        raise ValueError("each ordered object needs height, width, and crop")
    return _pack(copy.deepcopy(objects))


def validate_input(grid: Any) -> list[str]:
    try:
        objects = _components(grid)
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    if not 3 <= len(objects) <= 4:
        errors.append(f"parametric grammar requires 3..4 motifs, found {len(objects)}")
    colors = [obj["color"] for obj in objects]
    if len(colors) != len(set(colors)):
        errors.append("each motif must have a distinct color")
    for key in ("cell_count", "bbox_area"):
        scores = [obj[key] for obj in objects]
        if len(scores) != len(set(scores)):
            errors.append(f"motif {key} values must be distinct: {scores}")
    if not errors and solve(grid, {PARAMETER: MODES[0]}) == solve(grid, {PARAMETER: MODES[1]}):
        errors.append("declared ranking keys must change the packed output")
    return errors


def _normalize(cells: list[tuple[int, int]]) -> list[tuple[int, int]]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _flip(cells: list[tuple[int, int]], horizontal: bool, vertical: bool) -> list[tuple[int, int]]:
    height = max(r for r, _ in cells) + 1
    width = max(c for _, c in cells) + 1
    transformed = [
        (height - 1 - r if vertical else r, width - 1 - c if horizontal else c)
        for r, c in cells
    ]
    return _normalize(transformed)


def _shapes(large: bool) -> dict[str, list[tuple[int, int]]]:
    if large:
        return {
            "A": [(r, c) for r in range(5) for c in range(5)],
            "B": [(0, c) for c in range(6)] + [(r, 0) for r in range(1, 7)],
            "C": [(0, c) for c in range(5)] + [(r, 2) for r in range(1, 6)],
            "D": [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3)],
        }
    return {
        "A": [(r, c) for r in range(3) for c in range(4)],
        "B": [(0, c) for c in range(5)] + [(r, 0) for r in range(1, 5)],
        "C": [(0, c) for c in range(4)] + [(r, 1) for r in range(1, 4)],
        "D": [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)],
    }


def _rng(seed: int, split: str, index: int, attempt: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}|motif-order-v1|{seed}|{split}|{index}|{attempt}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _candidate_scene(seed: int, split: str, index: int, attempt: int) -> list[list[int]]:
    dims = _DEMO_DIMS if split == "train" else _QUERY_DIMS
    height, width = dims[index]
    large = (height, width) == (30, 30)
    shapes = _shapes(large)
    labels = ["A", "B", "C"] if index == 0 else ["A", "B", "C", "D"]
    rng = _rng(seed, split, index, attempt)
    for label in labels:
        shapes[label] = _flip(shapes[label], bool(rng.randrange(2)), bool(rng.randrange(2)))

    chosen = sorted(rng.sample(list(_PALETTE), len(labels)))
    color_order = [label for label in ("C", "A", "B", "D") if label in labels]
    colors = {label: color for label, color in zip(color_order, chosen, strict=True)}

    def dims_of(label):
        cells = shapes[label]
        return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1

    anchors: dict[str, tuple[int, int]] = {}
    if len(labels) == 3:
        ah, _ = dims_of("A")
        _, bw = dims_of("B")
        anchors = {
            "C": (rng.randrange(0, 2), 0),
            "A": (height - ah - rng.randrange(0, 2), 3),
            "B": (rng.randrange(0, 2), width - bw),
        }
    else:
        ah, _ = dims_of("A")
        bh, bw = dims_of("B")
        anchors = {
            "D": (rng.randrange(0, 2), 0),
            "A": (height - ah - rng.randrange(0, 2), 2 if not large else 4),
            "C": (rng.randrange(0, 2), 5 if not large else 11),
            "B": (height - bh - rng.randrange(0, 2), width - bw),
        }

    grid = [[0] * width for _ in range(height)]
    occupied: dict[tuple[int, int], str] = {}
    for label in labels:
        r0, c0 = anchors[label]
        for r, c in shapes[label]:
            rr, cc = r0 + r, c0 + c
            if not (0 <= rr < height and 0 <= cc < width) or (rr, cc) in occupied:
                raise AssertionError("motif slot overlap")
            occupied[(rr, cc)] = label
            grid[rr][cc] = colors[label]
    # Different motifs must not be 8-neighbor adjacent, matching the generator's
    # unambiguous separated-object grammar.
    for (r, c), label in occupied.items():
        for rr in range(max(0, r - 1), min(height, r + 2)):
            for cc in range(max(0, c - 1), min(width, c + 2)):
                other = occupied.get((rr, cc))
                if other is not None and other != label:
                    raise AssertionError("motif slots touch")
    return grid


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    dims = _DEMO_DIMS if split == "train" else _QUERY_DIMS
    if not 0 <= index < len(dims):
        raise ValueError(f"unsupported {split} index {index}")
    for attempt in range(256):
        try:
            grid = _candidate_scene(seed, split, index, attempt)
        except AssertionError:
            continue
        if validate_input(grid):
            continue
        if dims[index] == (30, 30) and sum(v != 0 for row in grid for v in row) < 50:
            continue
        return grid
    raise RuntimeError(f"failed to construct a lawful distinguishing {split} scene {index}")


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


def _solve_by(grid, key: Callable[[dict[str, Any]], tuple], *, gap: int = 1) -> list[list[int]]:
    return _pack(sorted(_components(grid), key=key), gap=gap)


def _left_to_right(grid):
    return _solve_by(grid, lambda obj: (obj["c1"], obj["r1"], obj["color"]))


def _color_order(grid):
    return _solve_by(grid, lambda obj: (obj["color"],))


def _cell_ascending(grid):
    return _solve_by(grid, lambda obj: (obj["cell_count"], obj["c1"], obj["r1"], obj["color"]))


def _area_ascending(grid):
    return _solve_by(grid, lambda obj: (obj["bbox_area"], obj["c1"], obj["r1"], obj["color"]))


def _width_descending(grid):
    return _solve_by(grid, lambda obj: (-obj["width"], obj["c1"], obj["r1"], obj["color"]))


def _perimeter_descending(grid):
    return _solve_by(grid, lambda obj: (-(2 * (obj["height"] + obj["width"])), obj["c1"], obj["r1"], obj["color"]))


def _cell_no_gap(grid):
    return _pack(_ordered(_components(grid), "cell_count"), gap=0)


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    MODES[0]: lambda grid: solve(grid, {PARAMETER: MODES[0]}),
    MODES[1]: lambda grid: solve(grid, {PARAMETER: MODES[1]}),
    "left_to_right": _left_to_right,
    "color_order": _color_order,
    "cell_count_ascending": _cell_ascending,
    "area_ascending": _area_ascending,
    "width_descending": _width_descending,
    "perimeter_descending": _perimeter_descending,
    "cell_count_no_gap": _cell_no_gap,
}


def audit_episode(seed: int, mode: str, *, demos: int = 2, queries: int = 4) -> dict[str, Any]:
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
        "query_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]],
        "intermediate": intermediate(episode["test"][0]["input"], {PARAMETER: mode}),
    }
