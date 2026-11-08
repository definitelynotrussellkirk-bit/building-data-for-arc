"""Matched-input symmetry lessons with an input-derived signal rank.

The canonical setting classifies every nonzero monochrome four-connected object
by tight-mask left/right and up/down symmetry.  The alternative first counts the
unique blue signal object, uses that count as a one-based rank among the other
objects in row-major discovery order, then symmetry-classifies only the selected
payload.  Native qualification re-executes all claim labels through protected
Racket.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "aa0b08801e61"
MODES = ("classify_all", "signal_rank")
PARAMETER = "selection"
_DIR = Path(__file__).resolve().parent
_PROGRAMS = {
    "classify_all": (_DIR / "canonical.rkt").read_text(encoding="utf-8"),
    "signal_rank": (_DIR / "signal_rank.rkt").read_text(encoding="utf-8"),
}
_ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CLASS_COLOR = {"both": 8, "lr": 2, "ud": 3, "none": 4}

Shape = tuple[tuple[int, int], ...]


def _shape(*cells: tuple[int, int]) -> Shape:
    return tuple(sorted(cells))


# Multiple connected masks per semantic class.  The selected payload always
# uses a five-cell representative; nonselected payloads include both smaller
# and larger masks so size extrema cannot stand in for the signal rank.
_SHAPES: dict[str, tuple[Shape, ...]] = {
    "both": (
        _shape((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        _shape((0, 0), (0, 1), (1, 0), (1, 1)),
        _shape((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
    "lr": (
        _shape((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
        _shape((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
        _shape((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
    ),
    "ud": (
        _shape((0, 0), (1, 0), (2, 0), (1, 1), (1, 2)),
        _shape((0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 1)),
        _shape((0, 1), (0, 2), (1, 0), (1, 1), (2, 1), (2, 2)),
    ),
    "none": (
        _shape((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
        _shape((0, 0), (1, 0), (1, 1)),
        _shape((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
}
_SIGNAL_SHAPES: dict[int, Shape] = {
    1: _shape((0, 0)),
    2: _shape((0, 0), (0, 1)),
    3: _shape((0, 0), (1, 0), (1, 1)),
    4: _shape((0, 0), (0, 1), (0, 2), (1, 1)),
    5: _shape((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
}

_DEMO_PROFILES = (
    # height, width, payload count, signal rank, selected symmetry class
    (15, 18, 6, 2, "lr"),
    (17, 20, 6, 4, "ud"),
    (18, 22, 7, 3, "both"),
    (20, 24, 7, 1, "none"),
    (22, 26, 8, 5, "lr"),
    (24, 28, 8, 2, "ud"),
)
_QUERY_PROFILES = (
    (15, 17, 6, 3, "none"),
    (19, 22, 7, 1, "both"),
    (24, 27, 7, 5, "ud"),
    (30, 30, 8, 2, "lr"),
)


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError("settings must name exactly selection")
    mode = settings[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"selection must be one of {MODES}")
    return mode


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def program(settings: dict[str, Any]) -> str:
    return _PROGRAMS[_mode(settings)]


def _validate_grid(grid: Any) -> list[list[int]]:
    if (type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]
            or len(grid) > 30 or len(grid[0]) > 30):
        raise ValueError("grid must be a nonempty rectangle no larger than 30x30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(cells)
    if not cells:
        return ()
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def symmetry_class(cells: Iterable[tuple[int, int]]) -> str:
    mask = set(_normalize(cells))
    if not mask:
        raise ValueError("cannot classify an empty object")
    max_row = max(row for row, _ in mask)
    max_col = max(col for _, col in mask)
    lr = {(row, max_col - col) for row, col in mask} == mask
    ud = {(max_row - row, col) for row, col in mask} == mask
    if lr and ud:
        return "both"
    if lr:
        return "lr"
    if ud:
        return "ud"
    return "none"


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _ORTHOGONAL:
                    nxt = (rr + dr, cc + dc)
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and nxt not in seen and grid[nxt[0]][nxt[1]] == color):
                        seen.add(nxt)
                        stack.append(nxt)
            cells.sort()
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            cls = symmetry_class(cells)
            result.append({
                "color": color,
                "cells": cells,
                "size": len(cells),
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
                "mask": _normalize(cells),
                "class": cls,
                "class_color": _CLASS_COLOR[cls],
            })
    return result


def paint_objects(grid: list[list[int]], objects: list[dict[str, Any]], *, source_color: bool = False):
    _validate_grid(grid)
    output = [[0] * len(grid[0]) for _ in grid]
    for obj in objects:
        color = obj["color"] if source_color else obj["class_color"]
        for row, col in obj["cells"]:
            output[row][col] = color
    return output


def paint_selected(grid: list[list[int]], selected: dict[str, Any]):
    return paint_objects(grid, [selected])


def observables(grid: list[list[int]]) -> dict[str, Any]:
    objects = _components(grid)
    signals = [obj for obj in objects if obj["color"] == 1]
    if len(signals) != 1:
        raise ValueError("generated scene must contain exactly one blue signal")
    signal = signals[0]
    payloads = [obj for obj in objects if obj["color"] != 1]
    rank = signal["size"]
    if not 1 <= rank <= len(payloads):
        raise ValueError("signal rank exceeds payload count")
    selected = payloads[rank - 1]
    height, width = len(grid), len(grid[0])
    touched = set()
    for obj in objects:
        for row, col in obj["cells"]:
            if row == 0:
                touched.add("top")
            if row == height - 1:
                touched.add("bottom")
            if col == 0:
                touched.add("left")
            if col == width - 1:
                touched.add("right")
    return {
        "objects": copy.deepcopy(objects),
        "signal": copy.deepcopy(signal),
        "payloads": copy.deepcopy(payloads),
        "payload_count": len(payloads),
        "signal_color": signal["color"],
        "signal_rank": rank,
        "selected_rank": rank,
        "selected_source_color": selected["color"],
        "selected_class": selected["class"],
        "selected_class_color": selected["class_color"],
        "touched_edges": sorted(touched),
    }


def solve(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = _mode(settings)
    if mode == "classify_all":
        return paint_objects(grid, _components(grid))
    facts = observables(grid)
    return paint_selected(grid, facts["payloads"][facts["signal_rank"] - 1])


def _paint_one(grid, obj, color=None):
    output = [[0] * len(grid[0]) for _ in grid]
    chosen = obj["class_color"] if color is None else color
    for row, col in obj["cells"]:
        output[row][col] = chosen
    return output


def solve_rival(grid: list[list[int]], name: str) -> list[list[int]]:
    facts = observables(grid)
    payloads = facts["payloads"]
    rank = facts["signal_rank"]
    if name == "first_payload":
        return _paint_one(grid, payloads[0])
    if name == "last_payload":
        return _paint_one(grid, payloads[-1])
    if name == "fixed_rank_2":
        return _paint_one(grid, payloads[1])
    if name == "fixed_rank_4":
        return _paint_one(grid, payloads[3])
    if name == "reverse_rank":
        return _paint_one(grid, list(reversed(payloads))[rank - 1])
    if name == "column_major_rank":
        ordered = sorted(payloads, key=lambda obj: (obj["bbox"][1], obj["bbox"][0], obj["bbox"][3], obj["bbox"][2]))
        return _paint_one(grid, ordered[rank - 1])
    if name == "smallest_payload":
        return _paint_one(grid, min(payloads, key=lambda obj: (obj["size"], obj["bbox"])))
    if name == "largest_payload":
        return _paint_one(grid, max(payloads, key=lambda obj: (obj["size"], tuple(-v for v in obj["bbox"]))))
    if name == "signal_size_match":
        return paint_objects(grid, [obj for obj in payloads if obj["size"] == rank])
    if name == "signal_class_match":
        return paint_objects(grid, [obj for obj in payloads if obj["class"] == facts["signal"]["class"]])
    if name == "source_color_selected":
        return _paint_one(grid, payloads[rank - 1], payloads[rank - 1]["color"])
    if name == "fixed_output_8":
        return _paint_one(grid, payloads[rank - 1], 8)
    raise ValueError(f"unknown rival: {name}")


RIVAL_NAMES = (
    "first_payload",
    "last_payload",
    "fixed_rank_2",
    "fixed_rank_4",
    "reverse_rank",
    "column_major_rank",
    "smallest_payload",
    "largest_payload",
    "signal_size_match",
    "signal_class_match",
    "source_color_selected",
    "fixed_output_8",
)


def _derived_rng(seed: int, split: str, index: int | str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _query_order(seed: int) -> list[int]:
    order = list(range(len(_QUERY_PROFILES)))
    _derived_rng(seed, "query-order", 0).shuffle(order)
    return order


def _slot_positions(height: int, width: int, count: int) -> list[tuple[int, int]]:
    columns = (count + 1) // 2
    if columns < 2:
        raise AssertionError("payload grammar requires at least four objects")
    max_left = width - 3
    col_positions = [round(index * max_left / (columns - 1)) for index in range(columns)]
    row_positions = [4, height - 3]
    return [(row, col) for row in row_positions for col in col_positions][:count]


def _class_sequence(count: int, rank: int, target: str, rng: random.Random) -> list[str]:
    base = (["both", "lr", "ud", "none"] * 2)[:count]
    rng.shuffle(base)
    target_index = base.index(target)
    base[target_index], base[rank - 1] = base[rank - 1], base[target_index]
    return base


def _shape_choices(classes: list[str], rank: int, rng: random.Random) -> list[Shape]:
    shapes: list[Shape] = []
    for index, cls in enumerate(classes):
        if index == rank - 1:
            shapes.append(_SHAPES[cls][0])  # every selected representative has five cells
        else:
            shapes.append(rng.choice(_SHAPES[cls]))
    # Force one small and one large nonselected witness when those classes exist.
    for cls, variant in (("none", 1), ("both", 2)):
        candidates = [i for i, value in enumerate(classes) if value == cls and i != rank - 1]
        if candidates:
            shapes[candidates[0]] = _SHAPES[cls][variant]
    return shapes


def _source_colors(classes: list[str], rng: random.Random) -> list[int]:
    colors = list(range(2, 10))[:len(classes)]
    for _ in range(256):
        rng.shuffle(colors)
        if all(color != _CLASS_COLOR[cls] for color, cls in zip(colors, classes, strict=True)):
            return list(colors)
    raise AssertionError("failed to construct source/class color derangement")


def _place(grid: list[list[int]], shape: Shape, top: int, left: int, color: int) -> None:
    for dr, dc in shape:
        row, col = top + dr, left + dc
        if not (0 <= row < len(grid) and 0 <= col < len(grid[0])):
            raise AssertionError("shape placement escaped the grid")
        if grid[row][col] != 0:
            raise AssertionError("shape placement overlapped")
        grid[row][col] = color


def _scene_from_profile(seed: int, split: str, profile_index: int, profile) -> list[list[int]]:
    height, width, count, rank, target = profile
    rng = _derived_rng(seed, split, profile_index)
    grid = [[0] * width for _ in range(height)]
    signal = _SIGNAL_SHAPES[rank]
    signal_width = max(col for _, col in signal) + 1
    center = width // 2 - signal_width // 2
    jitter = rng.choice((-2, -1, 0, 1, 2))
    signal_left = max(4, min(width - signal_width - 4, center + jitter))
    _place(grid, signal, 0, signal_left, 1)

    classes = _class_sequence(count, rank, target, rng)
    shapes = _shape_choices(classes, rank, rng)
    colors = _source_colors(classes, rng)
    slots = _slot_positions(height, width, count)
    # A narrow mask in the right-edge slot would leave the boundary untouched.
    # Choose an equivalent-class width-three mask there; likewise retain a
    # height-three mask on the bottom edge.  This changes geometry, not labels.
    for index, ((top, left), cls) in enumerate(zip(slots, classes, strict=True)):
        if left == width - 3 and max(col for _, col in shapes[index]) < 2:
            shapes[index] = min(
                (shape for shape in _SHAPES[cls] if max(col for _, col in shape) == 2),
                key=len,
            )
    bottom_indices = [index for index, (top, _left) in enumerate(slots) if top == height - 3]
    if not any(max(row for row, _ in shapes[index]) == 2 for index in bottom_indices):
        index = bottom_indices[-1]
        cls = classes[index]
        shapes[index] = next(shape for shape in _SHAPES[cls]
                             if max(row for row, _ in shape) == 2)
    for (top, left), shape, color in zip(slots, shapes, colors, strict=True):
        _place(grid, shape, top, left, color)

    facts = observables(grid)
    if (facts["payload_count"] != count or facts["signal_rank"] != rank
            or facts["selected_class"] != target
            or facts["selected_source_color"] == facts["selected_class_color"]
            or set(facts["touched_edges"]) != {"top", "bottom", "left", "right"}
            or solve(grid, {PARAMETER: MODES[0]}) == solve(grid, {PARAMETER: MODES[1]})):
        raise AssertionError("constructed scene violates the parametric grammar")
    return grid


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    if split == "train":
        return _scene_from_profile(seed, split, index, _DEMO_PROFILES[index])
    if split == "test":
        profile_index = _query_order(seed)[index]
        return _scene_from_profile(seed, split, profile_index, _QUERY_PROFILES[profile_index])
    raise ValueError(split)


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    mode = _mode(settings)
    train_inputs = [_scene(seed, "train", index) for index in range(demos)]
    test_inputs = [_scene(seed, "test", index) for index in range(queries)]
    chosen = {PARAMETER: mode}
    return {
        "train": [{"input": grid, "output": solve(grid, chosen)} for grid in train_inputs],
        "test": [{"input": grid, "output": solve(grid, chosen)} for grid in test_inputs],
        "program_solution": _PROGRAMS[mode],
    }


def audit_episode(seed: int, mode: str, demos: int = 2, queries: int = 4) -> dict[str, Any]:
    episode = generate(seed, {PARAMETER: mode}, demos, queries)
    other = MODES[1 - MODES.index(mode)]
    findings = []
    if all(solve(pair["input"], {PARAMETER: other}) == pair["output"] for pair in episode["train"]):
        findings.append({"rival": other, "reason": "declared alternate survives demonstrations"})
    for rival in RIVAL_NAMES:
        fits = all(solve_rival(pair["input"], rival) == pair["output"] for pair in episode["train"])
        harmful = any(solve_rival(pair["input"], rival) != pair["output"] for pair in episode["test"])
        if fits and harmful:
            findings.append({"rival": rival, "reason": "fits demos and changes a query"})
    return {
        "seed": seed,
        "settings": {PARAMETER: mode},
        "demos": demos,
        "queries": queries,
        "findings": findings,
        "query_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]],
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--selection", choices=MODES, default=MODES[0])
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(generate(args.seed, {PARAMETER: args.selection}, args.demos, args.queries), indent=2))
