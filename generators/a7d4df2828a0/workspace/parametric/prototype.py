"""Native placement family for a7d4df2828a0.

The canonical setting applies the control-coded transform and anchors its tight
bounding box at the source bounding-box top-left.  The nearby setting tracks the
row-major first motif cell through the transform, then translates the transformed
motif so that derived cell remains at its original absolute position.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "a7d4df2828a0"
PLACEMENTS = ("bbox_top_left", "preserve_first_cell")
SETTINGS = tuple({"placement": value} for value in PLACEMENTS)
HERE = Path(__file__).resolve().parent
CANONICAL_PATH = HERE / "canonical.rkt"
PIVOT_PATH = HERE / "preserve_first_cell.rkt"
CARDINAL = ((-1, 0), (0, -1), (0, 1), (1, 0))

SMALL_SHAPES = (
    frozenset({(0, 0), (1, 0), (1, 1), (2, 1)}),
    frozenset({(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)}),
    frozenset({(0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 2)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (3, 1)}),
    frozenset({(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3), (4, 3)}),
    frozenset({(0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2), (4, 2), (4, 3)}),
)
DEMO_DIMS = ((9, 10), (10, 11), (12, 13), (13, 15), (15, 17), (17, 19))
DEMO_CODES = (1, 3, 2, 4, 1, 2)
QUERY_DIMS = ((12, 15), (18, 20), (24, 27), (30, 30))
QUERY_CODES = (1, 2, 3, 4)
QUERY_BOXES = ((5, 6), (7, 8), (9, 10), (11, 13))


def _plain_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a plain Python int in [{low}, {high}]")
    return value


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"placement"}:
        raise ValueError("settings must contain exactly placement")
    placement = settings["placement"]
    if type(placement) is not str or placement not in PLACEMENTS:
        raise ValueError(f"placement must be one of {PLACEMENTS}")
    return {"placement": placement}


def program(settings: Any) -> str:
    placement = _settings(settings)["placement"]
    return (CANONICAL_PATH if placement == "bbox_top_left" else PIVOT_PATH).read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}|placement-v1|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _transform_point(point: tuple[int, int], code: int, maxr: int, maxc: int) -> tuple[int, int]:
    r, c = point
    if code == 1:
        return c, maxr - r
    if code == 2:
        return maxr - r, maxc - c
    if code == 3:
        return r, maxc - c
    if code == 4:
        return maxr - r, c
    raise ValueError("code must be in 1..4")


def _transform(cells: Iterable[tuple[int, int]], code: int) -> tuple[tuple[int, int], ...]:
    norm = _normalize(cells)
    maxr = max(r for r, _ in norm)
    maxc = max(c for _, c in norm)
    return _normalize(_transform_point(point, code, maxr, maxc) for point in norm)


def analyze(grid: Any) -> dict[str, Any]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if len(grid) > 30 or width > 30 or any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("expected a rectangular ARC grid no larger than 30x30")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid cells must be plain integer ARC colors")
    code = grid[0][0]
    if code not in (1, 2, 3, 4):
        raise ValueError("control code must be in 1..4")
    cells = sorted((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value and (r, c) != (0, 0))
    if not cells:
        raise ValueError("motif is empty")
    colors = {grid[r][c] for r, c in cells}
    if len(colors) != 1 or code in colors:
        raise ValueError("motif must use one color distinct from the control")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    local = _normalize(cells)
    maxr = max(r for r, _ in local)
    maxc = max(c for _, c in local)
    pivot = local[0]
    transformed = _transform(local, code)
    transformed_pivot = _transform_point(pivot, code, maxr, maxc)
    return {
        "code": code,
        "color": next(iter(colors)),
        "cells": tuple(cells),
        "bbox_origin": (r0, c0),
        "local_cells": local,
        "pivot_local": pivot,
        "transformed_cells": transformed,
        "transformed_pivot_local": transformed_pivot,
        "pivot_absolute": (r0 + pivot[0], c0 + pivot[1]),
    }


def _render(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int, *, clip: bool = False) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    output = [[0] * width for _ in range(height)]
    for r, c in cells:
        if 0 <= r < height and 0 <= c < width:
            output[r][c] = color
        elif not clip:
            raise ValueError("transformed motif leaves the canvas")
    return output


def _solve_with_placement(grid: Any, placement: str, *, pivot_kind: str = "first") -> list[list[int]]:
    data = analyze(grid)
    r0, c0 = data["bbox_origin"]
    transformed = data["transformed_cells"]
    if placement == "bbox_top_left":
        dr, dc = r0, c0
    elif placement == "preserve_first_cell":
        pivot = data["pivot_local"]
        transformed_pivot = data["transformed_pivot_local"]
        dr, dc = r0 + pivot[0] - transformed_pivot[0], c0 + pivot[1] - transformed_pivot[1]
    elif placement == "bbox_bottom_right":
        in_h = max(r for r, _ in data["local_cells"]) + 1
        in_w = max(c for _, c in data["local_cells"]) + 1
        out_h = max(r for r, _ in transformed) + 1
        out_w = max(c for _, c in transformed) + 1
        dr, dc = r0 + in_h - out_h, c0 + in_w - out_w
    elif placement == "preserve_last_cell":
        pivot = data["local_cells"][-1]
        maxr = max(r for r, _ in data["local_cells"])
        maxc = max(c for _, c in data["local_cells"])
        transformed_pivot = _transform_point(pivot, data["code"], maxr, maxc)
        dr, dc = r0 + pivot[0] - transformed_pivot[0], c0 + pivot[1] - transformed_pivot[1]
    else:
        raise ValueError("unknown placement")
    return _render(grid, ((dr + r, dc + c) for r, c in transformed), data["color"], clip=True)


def solve(grid: Any, settings: Any) -> list[list[int]]:
    return _solve_with_placement(grid, _settings(settings)["placement"])


def _dense_shape(height: int, width: int, phase: int) -> frozenset[tuple[int, int]]:
    cells = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if r in (0, height - 1)
        or c in (0, width - 1)
        or ((3 * r + 5 * c + phase) % 5 not in (0, 1))
    }
    # An asymmetric bite in the upper-right interior keeps every transform visible.
    cells.discard((1, width - 2))
    cells.discard((2, width - 2))
    return frozenset(cells)


def _shape_for(seed: int, split: str, index: int) -> frozenset[tuple[int, int]]:
    rng = _rng(seed, split, index)
    if split == "train" and index < 2:
        return SMALL_SHAPES[index]
    if split == "train":
        base = SMALL_SHAPES[index % len(SMALL_SHAPES)]
        if rng.randrange(2):
            maxr = max(r for r, _ in base)
            base = frozenset((r, max(c for _, c in base) - c) for r, c in base)
        return frozenset(_normalize(base))
    bh, bw = QUERY_BOXES[index]
    return _dense_shape(bh, bw, int.from_bytes(hashlib.sha256(f"{seed}:{index}".encode()).digest()[:2], "big"))


def _legal_anchors(height: int, width: int, shape: frozenset[tuple[int, int]], code: int) -> list[tuple[int, int]]:
    local = _normalize(shape)
    transformed = _transform(local, code)
    maxr = max(r for r, _ in local)
    maxc = max(c for _, c in local)
    pivot = local[0]
    tp = _transform_point(pivot, code, maxr, maxc)
    anchors = []
    for r0 in range(height):
        for c0 in range(width):
            input_cells = [(r0 + r, c0 + c) for r, c in local]
            canonical = [(r0 + r, c0 + c) for r, c in transformed]
            pivoted = [(r0 + pivot[0] - tp[0] + r, c0 + pivot[1] - tp[1] + c) for r, c in transformed]
            all_cells = input_cells + canonical + pivoted
            if all(0 <= r < height and 0 <= c < width for r, c in all_cells) and all(r > 1 or c > 1 for r, c in input_cells):
                anchors.append((r0, c0))
    return anchors


def scene(seed: int, split: str, index: int) -> list[list[int]]:
    rng = _rng(seed, split, index)
    if split == "train":
        height, width = DEMO_DIMS[index]
        code = DEMO_CODES[index]
    elif split == "test":
        height, width = QUERY_DIMS[index]
        code = QUERY_CODES[index]
    else:
        raise ValueError("split must be train or test")
    shape = _shape_for(seed, split, index)
    anchors = _legal_anchors(height, width, shape, code)
    if not anchors:
        raise RuntimeError("no anchor supports both placement policies")
    if split == "test" and index == 3:
        # Maximize input contact with the lower/right canvas boundary.
        anchor = max(anchors, key=lambda p: (p[0] + max(r for r, _ in shape), p[1] + max(c for _, c in shape), p))
    else:
        anchor = anchors[rng.randrange(len(anchors))]
    color = rng.choice([value for value in range(1, 10) if value != code])
    grid = [[0] * width for _ in range(height)]
    grid[0][0] = code
    for r, c in shape:
        grid[anchor[0] + r][anchor[1] + c] = color
    # Construction must be total for both admitted settings.
    for setting in SETTINGS:
        solve(grid, setting)
    return grid


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    _plain_int("seed", seed, 0, 2**63 - 1)
    _plain_int("demos", demos, 2, 6)
    _plain_int("queries", queries, 1, 4)
    normalized = _settings(settings)
    result = {"settings": normalized, "program_solution": program(normalized), "train": [], "test": []}
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = scene(seed, split, index)
            result[split].append({"input": grid, "output": solve(grid, normalized)})
    return result


def public_turn(episode: dict[str, Any], query_index: Any = 0) -> dict[str, Any]:
    _plain_int("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in episode["train"]],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def fit_settings(train: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [setting for setting in SETTINGS if all(solve(pair["input"], setting) == pair["output"] for pair in train)]


def _identity_output(grid: list[list[int]]) -> list[list[int]]:
    data = analyze(grid)
    return _render(grid, data["cells"], data["color"], clip=True)


def _fixed_code(grid: list[list[int]], code: int) -> list[list[int]]:
    data = analyze(grid)
    transformed = _transform(data["local_cells"], code)
    r0, c0 = data["bbox_origin"]
    return _render(
        grid,
        ((r0 + r, c0 + c) for r, c in transformed),
        data["color"],
        clip=True,
    )


def rival_predictions(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    data = analyze(grid)
    canonical = solve(grid, {"placement": "bbox_top_left"})
    with_control = deepcopy(canonical)
    with_control[0][0] = data["code"]
    results = {f"setting:{name}": solve(grid, {"placement": name}) for name in PLACEMENTS}
    results.update(
        {
            "identity_no_transform": _identity_output(grid),
            "bbox_bottom_right": _solve_with_placement(grid, "bbox_bottom_right"),
            "preserve_last_cell": _solve_with_placement(grid, "preserve_last_cell"),
            "leave_control": with_control,
        }
    )
    for code in range(1, 5):
        results[f"fixed_code_{code}"] = _fixed_code(grid, code)
    return results


def self_review(episode: dict[str, Any]) -> dict[str, Any]:
    predictions = {name: [] for name in rival_predictions(episode["train"][0]["input"])}
    for pair in episode["train"]:
        current = rival_predictions(pair["input"])
        for name, output in current.items():
            predictions[name].append(output == pair["output"])
    query_pairs = episode["test"]
    harmful = []
    for name, matches in predictions.items():
        if all(matches) and any(rival_predictions(pair["input"])[name] != pair["output"] for pair in query_pairs):
            if not name.startswith("setting:"):
                harmful.append(name)
    intended = [name.split(":", 1)[1] for name, matches in predictions.items() if name.startswith("setting:") and all(matches)]
    return {"intended_survivors": intended, "harmful_survivors": harmful, "rivals_checked": len(predictions)}


def diff_cells(left: list[list[int]], right: list[list[int]]) -> int:
    height = max(len(left), len(right))
    width = max(max((len(row) for row in left), default=0), max((len(row) for row in right), default=0))
    return sum(
        (left[r][c] if r < len(left) and c < len(left[r]) else None)
        != (right[r][c] if r < len(right) and c < len(right[r]) else None)
        for r in range(height)
        for c in range(width)
    )


def causal_case() -> dict[str, Any]:
    grid = scene(0, "train", 0)
    data = analyze(grid)
    correct = solve(grid, {"placement": "preserve_first_cell"})
    wrong = solve(grid, {"placement": "bbox_top_left"})
    return {
        "input": grid,
        "settings": {"placement": "preserve_first_cell"},
        "intermediate_value": {
            "pivot_local": list(data["pivot_local"]),
            "transformed_pivot_local": list(data["transformed_pivot_local"]),
            "pivot_absolute": list(data["pivot_absolute"]),
        },
        "output": correct,
        "counterfactual_output": wrong,
        "difference_cells": diff_cells(correct, wrong),
        "ablation": "wrong_intermediate",
    }


def episode_digest(episode: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(episode, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
