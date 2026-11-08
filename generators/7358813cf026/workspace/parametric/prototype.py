#!/usr/bin/env python3
"""Native two-setting singleton-filter family for 7358813cf026.

``erase_all`` preserves the canonical program byte-for-byte.  The alternative
first finds the unique largest same-colour 4-connected object, carries its
input-dependent colour forward, and protects every singleton of that colour
while erasing all other singleton objects.  Each episode includes deliberately
remote singletons of both the largest and second-largest object colours so the
selector, the nonlocal use of its intermediate, and a wrong-rank ablation are
all observable.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import canonical_path, find_root, normalize_grid

TASK_ID = "7358813cf026"
SETTINGS = (
    {"singleton_policy": "erase_all"},
    {"singleton_policy": "protect_largest_color"},
)
DEFAULT_SETTINGS = SETTINGS[0]
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
DEMO_SHAPES = ((10, 12), (12, 10), (13, 15), (15, 12), (16, 17), (18, 16))
QUERY_SHAPES = ((11, 14), (15, 11), (20, 22), (30, 30))


def _canonical_program() -> str:
    root = find_root(__file__)
    matches: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    matches.append(row["program_solution"])
    if not matches or len(set(matches)) != 1:
        raise RuntimeError(f"expected one stable canonical program for {TASK_ID}")
    return matches[0]


CANONICAL_PROGRAM = _canonical_program()


def _protected_program(which: str) -> str:
    selector = "(first ranked)" if which == "largest" else "(second ranked)"
    return f"""(rule!
 (let* ((objs (objects g 0))
        (ranked (sort objs (lambda (a b) (> (obj-size a) (obj-size b)))))
        (anchor-color (obj-color {selector})))
   (for/fold ((out (empty-grid (rows g) (cols g) 0)))
             ((obj (in-list objs)))
     (if (or (>= (obj-size obj) 2)
             (= (obj-color obj) anchor-color))
         (paint-cells out (obj-cells obj) (obj-color obj))
         out))))"""


LARGEST_COLOR_PROGRAM = _protected_program("largest")
SECOND_COLOR_PROGRAM = _protected_program("second")


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rng(seed: int, stream: str, index: int = 0) -> random.Random:
    _integer(seed, "seed", 0, 2**63 - 1)
    payload = f"{TASK_ID}|{seed}|{stream}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _settings(value: dict[str, Any] | None, *, seed: int | None = None) -> dict[str, str]:
    if value is None:
        if seed is None:
            value = dict(DEFAULT_SETTINGS)
        else:
            value = dict(SETTINGS[_rng(seed, "setting").randrange(len(SETTINGS))])
    if type(value) is not dict or set(value) != {"singleton_policy"}:
        raise ValueError("settings must name exactly singleton_policy")
    policy = value["singleton_policy"]
    if policy not in {"erase_all", "protect_largest_color"}:
        raise ValueError("singleton_policy must be erase_all or protect_largest_color")
    return {"singleton_policy": policy}


def program(settings: dict[str, Any] | None = None) -> str:
    selected = _settings(settings)
    return (
        CANONICAL_PROGRAM
        if selected["singleton_policy"] == "erase_all"
        else LARGEST_COLOR_PROGRAM
    )


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _neighbors4(cell: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    r, c = cell
    return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))


def _objects(grid: list[list[int]]) -> list[dict[str, Any]]:
    grid = normalize_grid(grid)
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while stack:
                cell = stack.pop()
                cells.append(cell)
                for nr, nc in _neighbors4(cell):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({"color": color, "cells": tuple(sorted(cells))})
    result.sort(key=lambda obj: (-len(obj["cells"]), obj["cells"][0], obj["color"]))
    return result


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _orient(shape: tuple[tuple[int, int], ...], code: int) -> tuple[tuple[int, int], ...]:
    cells = list(shape)
    if code & 4:
        cells = [(r, -c) for r, c in cells]
    for _ in range(code & 3):
        cells = [(c, -r) for r, c in cells]
    return _normalize_shape(cells)


def _place_near(
    grid: list[list[int]],
    shape: tuple[tuple[int, int], ...],
    color: int,
    target: tuple[float, float],
    rng: random.Random,
) -> tuple[tuple[int, int], ...]:
    h, w = len(grid), len(grid[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    target_r = target[0] * max(0, h - sh)
    target_c = target[1] * max(0, w - sw)
    candidates: list[tuple[float, tuple[tuple[int, int], ...]]] = []
    for top in range(h - sh + 1):
        for left in range(w - sw + 1):
            cells = tuple((top + r, left + c) for r, c in shape)
            if any(grid[r][c] != 0 for r, c in cells):
                continue
            cell_set = set(cells)
            blocked = False
            for r, c in cells:
                for nr, nc in _neighbors4((r, c)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in cell_set
                        and grid[nr][nc] != 0
                    ):
                        blocked = True
                        break
                if blocked:
                    break
            if blocked:
                continue
            score = (top - target_r) ** 2 + (left - target_c) ** 2 + rng.random() * 1e-4
            candidates.append((score, cells))
    if not candidates:
        raise ValueError(f"could not place shape of size {len(shape)} on {h}x{w}")
    cells = min(candidates, key=lambda row: row[0])[1]
    for r, c in cells:
        grid[r][c] = color
    return cells


ANCHOR_SHAPE = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2))
SECOND_SHAPE = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2))
SHAPES = (
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (0, 1)),
)
TARGETS = (
    (0.16, 0.36), (0.72, 0.70), (0.70, 0.24), (0.34, 0.08),
    (0.10, 0.58), (0.42, 0.84), (0.86, 0.48), (0.55, 0.52),
    (0.28, 0.68), (0.78, 0.08), (0.08, 0.22), (0.90, 0.82),
)


def _build_grid(seed: int, split: str, index: int, h: int, w: int) -> list[list[int]]:
    rng = _rng(seed, split, index)
    grid = [[0] * w for _ in range(h)]
    palette = list(range(1, 10))
    rng.shuffle(palette)
    anchor_color, second_color = palette[0], palette[1]
    flip_r = rng.random() < 0.5
    flip_c = rng.random() < 0.5

    def target(pair: tuple[float, float]) -> tuple[float, float]:
        r, c = pair
        return (1 - r if flip_r else r, 1 - c if flip_c else c)

    _place_near(
        grid,
        _orient(ANCHOR_SHAPE, rng.randrange(8)),
        anchor_color,
        target((0.48, 0.48)),
        rng,
    )
    _place_near(
        grid,
        _orient(SECOND_SHAPE, rng.randrange(8)),
        second_color,
        target((0.08, 0.76)),
        rng,
    )
    _place_near(grid, ((0, 0),), anchor_color, target((0.98, 0.02)), rng)
    _place_near(grid, ((0, 0),), second_color, target((0.02, 0.02)), rng)
    _place_near(grid, ((0, 0),), palette[2], target((0.98, 0.98)), rng)

    extra_count = 3
    if h * w >= 220:
        extra_count = 6
    if h * w >= 500:
        extra_count = 12
    for offset in range(extra_count):
        shape = SHAPES[offset % len(SHAPES)]
        oriented = _orient(shape, rng.randrange(8))
        color = palette[2 + (offset % (len(palette) - 2))]
        _place_near(grid, oriented, color, target(TARGETS[offset]), rng)

    info = analyze(grid)
    if not info["largest_object_unique"] or info["anchor_color_singletons"] < 1:
        raise AssertionError("constructed selector invariants failed")
    if info["second_color_singletons"] < 1:
        raise AssertionError("wrong-anchor witness singleton is missing")
    if transform_with_rank(grid, 1) == transform_with_rank(grid, 2):
        raise AssertionError("wrong-anchor rival accidentally agrees")
    return grid


def transform_with_rank(grid: list[list[int]], rank: int) -> list[list[int]]:
    grid = normalize_grid(grid)
    objects = _objects(grid)
    _integer(rank, "rank", 1, len(objects))
    anchor_color = objects[rank - 1]["color"]
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for obj in objects:
        if len(obj["cells"]) >= 2 or obj["color"] == anchor_color:
            for r, c in obj["cells"]:
                out[r][c] = obj["color"]
    return out


def _erase_all_singletons(grid: list[list[int]]) -> list[list[int]]:
    grid = normalize_grid(grid)
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for obj in _objects(grid):
        if len(obj["cells"]) >= 2:
            for r, c in obj["cells"]:
                out[r][c] = obj["color"]
    return out


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    selected = _settings(settings)
    grid = normalize_grid(grid)
    if selected["singleton_policy"] == "erase_all":
        return _erase_all_singletons(grid)
    return transform_with_rank(grid, 1)


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    grid = normalize_grid(grid)
    objects = _objects(grid)
    if len(objects) < 2:
        raise ValueError("selector family requires at least two objects")
    largest, second = objects[0], objects[1]
    nonzero = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value
    ]
    return {
        "object_count": len(objects),
        "largest_object_color": largest["color"],
        "largest_object_size": len(largest["cells"]),
        "second_object_color": second["color"],
        "second_object_size": len(second["cells"]),
        "largest_object_unique": len(largest["cells"]) > len(second["cells"]),
        "anchor_color_singletons": sum(
            len(obj["cells"]) == 1 and obj["color"] == largest["color"]
            for obj in objects
        ),
        "second_color_singletons": sum(
            len(obj["cells"]) == 1 and obj["color"] == second["color"]
            for obj in objects
        ),
        "singleton_count": sum(len(obj["cells"]) == 1 for obj in objects),
        "nonzero_count": len(nonzero),
        "row_span": max(r for r, _ in nonzero) - min(r for r, _ in nonzero) + 1,
        "col_span": max(c for _, c in nonzero) - min(c for _, c in nonzero) + 1,
    }


def _input(seed: int, split: str, index: int) -> list[list[int]]:
    shapes = DEMO_SHAPES if split == "demo" else QUERY_SHAPES
    h, w = shapes[index]
    return _build_grid(seed, split, index, h, w)


def generate(
    seed: int,
    settings: dict[str, Any] | None = None,
    demos: int = 2,
    queries: int = 4,
) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    demos = _integer(demos, "demos", *DEMO_LIMITS)
    queries = _integer(queries, "queries", *QUERY_LIMITS)
    selected = _settings(settings, seed=seed)
    train_inputs = [_input(seed, "demo", index) for index in range(demos)]
    test_inputs = [_input(seed, "query", index) for index in range(queries)]
    keys = [digest(grid) for grid in train_inputs + test_inputs]
    if len(keys) != len(set(keys)):
        raise ValueError("episode inputs must be distinct")
    return {
        "schema": f"{TASK_ID}-parametric-singleton-policy-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": [
            {"input": grid, "output": transform(grid, selected)} for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": transform(grid, selected)} for grid in test_inputs
        ],
        "program_solution": program(selected),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--singleton-policy",
        choices=("erase_all", "protect_largest_color"),
        default="erase_all",
    )
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    episode = generate(
        args.seed,
        {"singleton_policy": args.singleton_policy},
        args.demos,
        args.queries,
    )
    args.out.write_text(json.dumps(episode, indent=2, sort_keys=True) + "\n")
