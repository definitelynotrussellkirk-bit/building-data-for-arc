"""Parametric exact-four rectangle family for task ``42fb6b33deea``.

The default is the exact canonical rule.  The alternative first measures the
bounding-box area of the unique three-cell selector, then fills only exactly-four
colors whose bounding-box area is at least that input-derived threshold.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable


TASK_ID = "42fb6b33deea"
FILL_POLICIES = ("all_exact_four", "selector_area_gate")
DEFAULT_POLICY = FILL_POLICIES[0]
_HERE = Path(__file__).resolve().parent
_PROGRAM_PATHS = {
    "all_exact_four": _HERE / "canonical.rkt",
    "selector_area_gate": _HERE / "selector_area_gate.rkt",
}
_PROGRAMS = {name: path.read_text(encoding="utf-8") for name, path in _PROGRAM_PATHS.items()}

# Every profile has one three-cell selector and targets below, equal to and above
# the selector bbox area.  Query 3 is an exact 30x30 stress case with four targets.
_DEMO_PROFILES = (
    (10, 12, (2, 3), ((2, 2), (2, 3), (3, 3))),
    (12, 15, (3, 3), ((2, 3), (3, 3), (3, 4))),
    (14, 18, (3, 4), ((2, 4), (3, 4), (4, 4))),
    (16, 18, (3, 5), ((2, 5), (3, 5), (4, 5))),
    (18, 21, (4, 4), ((3, 4), (4, 4), (4, 5))),
    (20, 24, (4, 5), ((3, 5), (4, 5), (5, 5))),
)
_QUERY_PROFILES = (
    (11, 14, (2, 4), ((2, 3), (2, 4), (3, 4))),
    (17, 20, (3, 5), ((3, 4), (3, 5), (4, 5))),
    (24, 27, (4, 6), ((4, 5), (4, 6), (5, 6))),
    (30, 30, (5, 6), ((4, 6), (5, 6), (5, 7), (7, 8))),
)

Grid = list[list[int]]
Cell = tuple[int, int]
BBox = tuple[int, int, int, int]


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def validate_policy(value: Any) -> str:
    if type(value) is not str:
        raise TypeError("fill_policy must be a string")
    if value not in FILL_POLICIES:
        raise ValueError(f"fill_policy must be one of {list(FILL_POLICIES)}")
    return value


def program_for(fill_policy: Any) -> str:
    return _PROGRAMS[validate_policy(fill_policy)]


def _rng(seed: int, stream: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}|parametric-v1|{seed}|{stream}|{index}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _bbox(cells: list[Cell] | set[Cell]) -> BBox:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_cells(box: BBox) -> list[Cell]:
    top, left, bottom, right = box
    return [
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    ]


def _corners(box: BBox) -> tuple[Cell, Cell, Cell, Cell]:
    top, left, bottom, right = box
    return (top, left), (top, right), (bottom, left), (bottom, right)


def _area(box: BBox) -> int:
    top, left, bottom, right = box
    return (bottom - top + 1) * (right - left + 1)


def _slots(height: int, width: int) -> list[BBox]:
    row_edges = (0, height // 2, height)
    col_edges = (0, width // 3, (2 * width) // 3, width)
    return [
        (row_edges[r], col_edges[c], row_edges[r + 1] - 1, col_edges[c + 1] - 1)
        for r in range(2)
        for c in range(3)
    ]


def _place_shape(slot: BBox, shape: tuple[int, int], rng: random.Random) -> BBox:
    slot_top, slot_left, slot_bottom, slot_right = slot
    rect_h, rect_w = shape
    slot_h = slot_bottom - slot_top + 1
    slot_w = slot_right - slot_left + 1
    if rect_h > slot_h or rect_w > slot_w:
        raise ValueError(f"shape {shape} does not fit slot {slot}")
    top = slot_top + rng.randrange(slot_h - rect_h + 1)
    left = slot_left + rng.randrange(slot_w - rect_w + 1)
    return top, left, top + rect_h - 1, left + rect_w - 1


def _selector_cells(box: BBox, rng: random.Random) -> set[Cell]:
    corners = list(_corners(box))
    del corners[rng.randrange(len(corners))]
    return set(corners)


def _exact_four_cells(box: BBox, rng: random.Random, *, noncorner: bool) -> set[Cell]:
    corners = set(_corners(box))
    if not noncorner:
        return corners
    candidates: list[set[Cell]] = []
    for removed in corners:
        for replacement in set(_bbox_cells(box)) - corners:
            cells = (corners - {removed}) | {replacement}
            if _bbox(cells) == box:
                candidates.append(cells)
    if not candidates:
        return corners
    return set(rng.choice(candidates))


def _distractor_cells(box: BBox, rng: random.Random) -> set[Cell]:
    corners = set(_corners(box))
    extras = list(set(_bbox_cells(box)) - corners)
    if not extras:
        raise ValueError("distractor box needs a non-corner cell")
    return corners | {rng.choice(extras)}


def _scene(seed: int, stream: str, index: int, profile: tuple) -> Grid:
    height, width, selector_shape, target_shapes = profile
    rng = _rng(seed, stream, index)
    slots = _slots(height, width)
    rng.shuffle(slots)
    object_shapes = [selector_shape, *target_shapes, (3, 3)]
    if len(object_shapes) > len(slots):
        raise RuntimeError("profile needs more objects than available slots")
    boxes = [_place_shape(slot, shape, rng) for slot, shape in zip(slots, object_shapes)]
    palette = list(range(1, 10))
    rng.shuffle(palette)
    colors = palette[: len(object_shapes)]
    grid = [[0 for _ in range(width)] for _ in range(height)]

    selector = _selector_cells(boxes[0], rng)
    for row, col in selector:
        grid[row][col] = colors[0]

    for target_index, box in enumerate(boxes[1 : 1 + len(target_shapes)]):
        # The equal and above-threshold targets are non-corner witnesses.  The
        # below-threshold target remains an ordinary four-corner rectangle.
        cells = _exact_four_cells(box, rng, noncorner=target_index >= 1)
        for row, col in cells:
            grid[row][col] = colors[1 + target_index]

    distractor_box = boxes[-1]
    for row, col in _distractor_cells(distractor_box, rng):
        grid[row][col] = colors[-1]
    return grid


def episode_inputs(seed: int, demos: int = 3, queries: int = 4) -> dict[str, list[Grid]]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    # Materialize the whole supported schedule before slicing.  Thus query 0 and
    # every earlier demonstration are independent of requested suffix lengths.
    train = [_scene(seed, "demo", i, profile) for i, profile in enumerate(_DEMO_PROFILES)]
    test = [_scene(seed, "query", i, profile) for i, profile in enumerate(_QUERY_PROFILES)]
    all_inputs = train + test
    keys = [json.dumps(grid, separators=(",", ":")) for grid in all_inputs]
    if len(keys) != len(set(keys)):
        raise RuntimeError("constructed parametric inputs are not distinct")
    return {"train": copy.deepcopy(train[:demos]), "test": copy.deepcopy(test[:queries])}


def analyze_input(grid: Grid) -> dict[str, Any]:
    errors: list[str] = []
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
        or any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row)
    ):
        return {"errors": ["grid must be a rectangular exact-integer ARC grid"]}
    positions: dict[int, list[Cell]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                positions.setdefault(value, []).append((row, col))
    selectors = [(color, cells) for color, cells in positions.items() if len(cells) == 3]
    if len(selectors) != 1:
        errors.append("exactly one three-cell selector is required")
        selector_color, selector_cells = (None, []) if not selectors else selectors[0]
    else:
        selector_color, selector_cells = selectors[0]
    selector_box = _bbox(selector_cells) if selector_cells else None
    selector_area = _area(selector_box) if selector_box else None
    targets = []
    for color, cells in sorted(positions.items()):
        if len(cells) != 4:
            continue
        box = _bbox(cells)
        targets.append(
            {
                "color": color,
                "cells": copy.deepcopy(cells),
                "bbox": box,
                "area": _area(box),
                "literal_corners": set(cells) == set(_corners(box)),
            }
        )
    if not targets:
        errors.append("at least one exactly-four target is required")
    return {
        "errors": errors,
        "selector_color": selector_color,
        "selector_cells": copy.deepcopy(selector_cells),
        "selector_bbox": selector_box,
        "selector_area": selector_area,
        "targets": targets,
        "positions": positions,
    }


def _paint_box(output: Grid, box: BBox, color: int) -> None:
    top, left, bottom, right = box
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            output[row][col] = color


def _solve_with_predicate(grid: Grid, predicate: Callable[[dict[str, Any], dict[str, Any]], bool]) -> Grid:
    analysis = analyze_input(grid)
    if analysis["errors"]:
        raise ValueError("invalid parametric input: " + "; ".join(analysis["errors"]))
    output = [[0 for _ in row] for row in grid]
    for target in analysis["targets"]:
        if predicate(target, analysis):
            _paint_box(output, target["bbox"], target["color"])
    return output


def solve(grid: Grid, fill_policy: Any) -> Grid:
    policy = validate_policy(fill_policy)
    if policy == "all_exact_four":
        return _solve_with_predicate(grid, lambda target, analysis: True)
    return _solve_with_predicate(
        grid, lambda target, analysis: target["area"] >= analysis["selector_area"]
    )


def _solve_literal_corners(grid: Grid) -> Grid:
    return _solve_with_predicate(grid, lambda target, analysis: target["literal_corners"])


def _solve_strict_gate(grid: Grid) -> Grid:
    return _solve_with_predicate(
        grid, lambda target, analysis: target["area"] > analysis["selector_area"]
    )


def _solve_at_most_gate(grid: Grid) -> Grid:
    return _solve_with_predicate(
        grid, lambda target, analysis: target["area"] <= analysis["selector_area"]
    )


def _solve_largest_only(grid: Grid) -> Grid:
    analysis = analyze_input(grid)
    if analysis["errors"]:
        raise ValueError("invalid parametric input: " + "; ".join(analysis["errors"]))
    largest = max(target["area"] for target in analysis["targets"])
    return _solve_with_predicate(grid, lambda target, _: target["area"] == largest)


def _solve_all_nonzero_bboxes(grid: Grid) -> Grid:
    analysis = analyze_input(grid)
    if analysis["errors"]:
        raise ValueError("invalid parametric input: " + "; ".join(analysis["errors"]))
    output = [[0 for _ in row] for row in grid]
    for color, cells in sorted(analysis["positions"].items()):
        _paint_box(output, _bbox(cells), color)
    return output


_CANDIDATE_SOLVERS: dict[str, Callable[[Grid], Grid]] = {
    "all_exact_four": lambda grid: solve(grid, "all_exact_four"),
    "selector_area_gate": lambda grid: solve(grid, "selector_area_gate"),
    "literal_corners_only": _solve_literal_corners,
    "selector_area_strict": _solve_strict_gate,
    "selector_area_at_most": _solve_at_most_gate,
    "largest_bbox_only": _solve_largest_only,
    "all_nonzero_bboxes": _solve_all_nonzero_bboxes,
}
CANDIDATE_POLICIES = tuple(_CANDIDATE_SOLVERS)


def solve_candidate(grid: Grid, name: Any) -> Grid:
    if type(name) is not str:
        raise TypeError("candidate name must be a string")
    try:
        solver = _CANDIDATE_SOLVERS[name]
    except KeyError as exc:
        raise ValueError(f"unknown candidate: {name}") from exc
    return solver(copy.deepcopy(grid))


def generate_episode(
    seed: int,
    fill_policy: Any,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    policy = validate_policy(fill_policy)
    selected = episode_inputs(seed, demos=demos, queries=queries)
    return {
        "train": [
            {"input": grid, "output": solve(grid, policy)} for grid in selected["train"]
        ],
        "test": [
            {"input": grid, "output": solve(grid, policy)} for grid in selected["test"]
        ],
        "program_solution": program_for(policy),
    }


def public_view(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(episode) is not dict or not isinstance(episode.get("train"), list) or not isinstance(episode.get("test"), list):
        raise TypeError("episode must contain train and test lists")
    query_index = _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }


def public_id(public: dict[str, Any]) -> str:
    raw = json.dumps(public, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _candidate_rule(condition: str, *, extra_definitions: str = "") -> str:
    """Build a small executable rival over the same lawful input grammar."""
    return f"""(rule!
  (let ()
    (define (bbox-area cells)
      (let ((bb (bbox-of-cells cells)))
        (length
          (positions-in-rect
            (first bb) (second bb) (third bb) (fourth bb)))))
{extra_definitions}    (let* ((colors (grid-colors g 0))
           (selector-color
             (first
               (filter
                 (lambda (color)
                   (= (length (find-color g color)) 3))
                 colors)))
           (selector-area
             (bbox-area (find-color g selector-color)))
           (target-colors
             (filter
               (lambda (color)
                 (= (length (find-color g color)) 4))
               colors))
           (largest-area
             (max-list
               (map
                 (lambda (color)
                   (bbox-area (find-color g color)))
                 target-colors))))
      (for/fold ([out (empty-grid (rows g) (cols g) 0)])
                ([color (in-list colors)])
        (let ((cells (find-color g color)))
          (if {condition}
              (let ((bb (bbox-of-cells cells)))
                (paint-cells
                  out
                  (positions-in-rect
                    (first bb) (second bb) (third bb) (fourth bb))
                  color))
              out))))))"""


_LITERAL_CORNERS_DEFINITION = """    (define (literal-corners? cells)
      (let* ((bb (bbox-of-cells cells))
             (corners
               (list
                 (list (first bb) (second bb))
                 (list (first bb) (fourth bb))
                 (list (third bb) (second bb))
                 (list (third bb) (fourth bb)))))
        (andmap (lambda (cell) (member cell corners)) cells)))
"""

_CANDIDATE_PROGRAMS = {
    "all_exact_four": _PROGRAMS["all_exact_four"],
    "selector_area_gate": _PROGRAMS["selector_area_gate"],
    "literal_corners_only": _candidate_rule(
        "(and (= (length cells) 4) (literal-corners? cells))",
        extra_definitions=_LITERAL_CORNERS_DEFINITION,
    ),
    "selector_area_strict": _candidate_rule(
        "(and (= (length cells) 4) (> (bbox-area cells) selector-area))"
    ),
    "selector_area_at_most": _candidate_rule(
        "(and (= (length cells) 4) (<= (bbox-area cells) selector-area))"
    ),
    "largest_bbox_only": _candidate_rule(
        "(and (= (length cells) 4) (= (bbox-area cells) largest-area))"
    ),
    "all_nonzero_bboxes": _candidate_rule("#t"),
}


def candidate_program(name: Any) -> str:
    if type(name) is not str:
        raise TypeError("candidate name must be a string")
    try:
        return _CANDIDATE_PROGRAMS[name]
    except KeyError as exc:
        raise ValueError(f"unknown candidate: {name}") from exc
