"""Matched-input parametric family for ARC task 91c488d9ffdc.

The canonical setting outlines every rectangle implied by same-color diagonal
endpoints. The alternate orders rectangles by top-left position, measures the
first (anchor) rectangle's area, uses that area as a cyclic selector among the
remaining rectangles, and outlines only the selected rectangle.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "91c488d9ffdc"
MODES = ("all_rectangles", "anchor_area_select")
DEFAULT_MODE = "all_rectangles"
CANONICAL_PROGRAM = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
CANONICAL_SHA256 = hashlib.sha256(CANONICAL_PROGRAM.encode()).hexdigest()

SELECT_PROGRAM = """(rule!
 (lambda (g)
   (let ((dummy 0))
     (define (border-cells bb)
       (append
        (for/list ([c (in-range (second bb) (+ (fourth bb) 1))]) (list (first bb) c))
        (for/list ([c (in-range (second bb) (+ (fourth bb) 1))]) (list (third bb) c))
        (for/list ([r (in-range (+ (first bb) 1) (third bb))]) (list r (second bb)))
        (for/list ([r (in-range (+ (first bb) 1) (third bb))]) (list r (fourth bb)))))
     (define (descriptor color)
       (let* ((bb (bbox-of-cells (find-color g color)))
              (hh (+ 1 (- (third bb) (first bb))))
              (ww (+ 1 (- (fourth bb) (second bb)))))
         (list color bb (* hh ww))))
     (define rects
       (sort (map descriptor (grid-colors g 0))
             (lambda (a b)
               (< (+ (* 100 (first (second a))) (second (second a)))
                  (+ (* 100 (first (second b))) (second (second b)))))))
     (define anchor (first rects))
     (define candidates (rest rects))
     (define target-index (modulo (- (third anchor) 1) (length candidates)))
     (define target (nth candidates target-index))
     (paint-cells (empty-grid (rows g) (cols g) 0)
                  (border-cells (second target))
                  (first target)))))"""

WRONG_PLUS_ONE_PROGRAM = """(rule!
 (lambda (g)
   (let ((dummy 0))
     (define (border-cells bb)
       (append
        (for/list ([c (in-range (second bb) (+ (fourth bb) 1))]) (list (first bb) c))
        (for/list ([c (in-range (second bb) (+ (fourth bb) 1))]) (list (third bb) c))
        (for/list ([r (in-range (+ (first bb) 1) (third bb))]) (list r (second bb)))
        (for/list ([r (in-range (+ (first bb) 1) (third bb))]) (list r (fourth bb)))))
     (define (descriptor color)
       (let* ((bb (bbox-of-cells (find-color g color)))
              (hh (+ 1 (- (third bb) (first bb))))
              (ww (+ 1 (- (fourth bb) (second bb)))))
         (list color bb (* hh ww))))
     (define rects
       (sort (map descriptor (grid-colors g 0))
             (lambda (a b)
               (< (+ (* 100 (first (second a))) (second (second a)))
                  (+ (* 100 (first (second b))) (second (second b)))))))
     (define anchor (first rects))
     (define candidates (rest rects))
     (define target-index (modulo (third anchor) (length candidates)))
     (define target (nth candidates target-index))
     (paint-cells (empty-grid (rows g) (cols g) 0)
                  (border-cells (second target))
                  (first target)))))"""

# Explicit constructive layouts: (height, width, boxes in row-major order).
_DEMO_SPECS = (
    (16, 20, ((0, 0, 3, 3), (0, 10, 4, 14), (8, 0, 12, 5), (9, 11, 15, 19))),
    (18, 22, ((0, 0, 3, 4), (0, 12, 5, 16), (8, 0, 13, 6), (10, 12, 17, 21))),
    (17, 23, ((0, 0, 2, 3), (0, 12, 4, 17), (7, 0, 12, 6), (9, 13, 16, 22))),
    (20, 24, ((0, 0, 4, 4), (0, 13, 5, 18), (10, 0, 15, 7), (11, 14, 19, 23))),
    (22, 26, ((0, 0, 3, 4), (0, 14, 6, 19), (11, 0, 17, 7), (12, 15, 21, 25))),
    (24, 28, ((0, 0, 2, 3), (0, 15, 6, 20), (12, 0, 18, 8), (13, 16, 23, 27))),
)
_QUERY_SPECS = (
    (17, 21, ((0, 0, 2, 4), (0, 11, 4, 15), (8, 0, 13, 5), (9, 12, 16, 20))),
    (19, 23, ((0, 0, 3, 3), (0, 13, 5, 17), (9, 0, 14, 6), (10, 14, 18, 22))),
    (25, 27, ((0, 0, 4, 4), (0, 15, 6, 20), (13, 0, 19, 8), (14, 16, 24, 26))),
    (30, 30, ((0, 0, 4, 5), (0, 12, 5, 17), (0, 23, 6, 29), (11, 0, 17, 6), (12, 12, 20, 19), (21, 21, 29, 29))),
)


def validate_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"outline_mode"}:
        raise ValueError("settings must contain exactly outline_mode")
    mode = settings["outline_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"outline_mode must be one of {MODES}")
    return {"outline_mode": mode}


def rule_text(mode: str) -> str:
    if mode == "all_rectangles":
        return CANONICAL_PROGRAM
    if mode == "anchor_area_select":
        return SELECT_PROGRAM
    raise ValueError(f"unknown outline_mode {mode!r}")


def counterfactual_program() -> str:
    return WRONG_PLUS_ONE_PROGRAM


def _mix(*parts: object) -> int:
    raw = ":".join(map(str, (TASK_ID, "anchor-area-selector-v1", *parts)))
    return int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big")


def border_cells(box):
    r0, c0, r1, c1 = box
    return (
        {(r0, c) for c in range(c0, c1 + 1)}
        | {(r1, c) for c in range(c0, c1 + 1)}
        | {(r, c0) for r in range(r0 + 1, r1)}
        | {(r, c1) for r in range(r0 + 1, r1)}
    )


def analyze(grid) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((r, c))
    if len(positions) < 3:
        raise ValueError("family requires at least three rectangles")
    rectangles = []
    for color, cells in positions.items():
        if len(cells) != 2:
            raise ValueError("each color must appear exactly twice")
        (r0, c0), (r1, c1) = cells
        if r0 == r1 or c0 == c1:
            raise ValueError("endpoints must be diagonal")
        box = (min(r0, r1), min(c0, c1), max(r0, r1), max(c0, c1))
        height = box[2] - box[0] + 1
        width_box = box[3] - box[1] + 1
        if height < 3 or width_box < 3:
            raise ValueError("rectangles must be at least 3x3")
        rectangles.append(
            {
                "color": color,
                "bbox": box,
                "height": height,
                "width": width_box,
                "area": height * width_box,
            }
        )
    rectangles.sort(key=lambda item: (item["bbox"][0], item["bbox"][1], item["color"]))
    borders = [border_cells(item["bbox"]) for item in rectangles]
    for index, first in enumerate(borders):
        for second in borders[index + 1 :]:
            if first & second:
                raise ValueError("rectangle borders must be disjoint")
    anchor = rectangles[0]
    candidates = rectangles[1:]
    target_index = (anchor["area"] - 1) % len(candidates)
    return {
        "rectangles": rectangles,
        "anchor": anchor,
        "anchor_area": anchor["area"],
        "candidates": candidates,
        "target_index": target_index,
        "wrong_target_index": anchor["area"] % len(candidates),
    }


def _empty_like(grid):
    return [[0 for _ in row] for row in grid]


def _paint_border(out, item):
    for r, c in border_cells(item["bbox"]):
        out[r][c] = item["color"]


def apply_mode(grid, mode: str):
    info = analyze(grid)
    out = _empty_like(grid)
    if mode == "all_rectangles":
        for item in info["rectangles"]:
            _paint_border(out, item)
        return out
    if mode == "anchor_area_select":
        _paint_border(out, info["candidates"][info["target_index"]])
        return out
    raise ValueError(f"unknown outline_mode {mode!r}")


def apply_wrong_plus_one(grid):
    info = analyze(grid)
    out = _empty_like(grid)
    _paint_border(out, info["candidates"][info["wrong_target_index"]])
    return out


_SAFE_PATTERNS_4 = (
    (1, 3, 2, 4), (1, 3, 4, 2), (1, 4, 2, 3),
    (2, 1, 3, 4), (2, 3, 1, 4), (2, 3, 4, 1),
    (3, 1, 2, 4), (3, 2, 1, 4), (3, 2, 4, 1),
    (4, 1, 2, 3), (4, 1, 3, 2), (4, 2, 1, 3),
    (4, 3, 1, 2), (4, 3, 2, 1),
)


def _colors(seed: int, split: str, index: int, count: int):
    # Four-rectangle lessons use only relative-rank patterns that make
    # color-order sorting disagree with the intended spatial order.  The
    # concrete palette still varies by seed.
    if count == 4:
        start = _mix(seed, split, index, "palette_start") % 6
        values = list(range(start + 1, start + 5))
        pattern = _SAFE_PATTERNS_4[_mix(seed, split, index, "pattern") % len(_SAFE_PATTERNS_4)]
        return [values[rank - 1] for rank in pattern]
    palette = list(range(1, 10))
    offset = _mix(seed, split, index, "colors") % len(palette)
    rotated = palette[offset:] + palette[:offset]
    if _mix(seed, split, index, "reverse") & 1:
        rotated.reverse()
    return rotated[:count]


def _build_input(seed: int, split: str, index: int, spec):
    height, width, boxes = spec
    colors = _colors(seed, split, index, len(boxes))
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for box_index, (color, box) in enumerate(zip(colors, boxes)):
        r0, c0, r1, c1 = box
        positive = ((_mix(seed, split, index, box_index, "slant") + box_index) & 1) == 0
        endpoints = ((r0, c0), (r1, c1)) if positive else ((r0, c1), (r1, c0))
        for r, c in endpoints:
            if grid[r][c] != 0:
                raise ValueError("endpoint collision")
            grid[r][c] = color
    info = analyze(grid)
    if [item["bbox"] for item in info["rectangles"]] != list(boxes):
        raise ValueError("row-major box order changed")
    return grid


def _pair(seed: int, split: str, index: int, spec, mode: str):
    grid = _build_input(seed, split, index, spec)
    return {"input": grid, "output": apply_mode(grid, mode)}


def generate_episode(seed: int, *, outline_mode: str, demos: int, queries: int):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2**63-1")
    if outline_mode not in MODES:
        raise ValueError(f"unknown outline_mode {outline_mode!r}")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    train = [
        _pair(seed, "train", index, _DEMO_SPECS[index], outline_mode)
        for index in range(demos)
    ]
    test = [
        _pair(seed, "test", index, _QUERY_SPECS[index], outline_mode)
        for index in range(queries)
    ]
    return {"train": train, "test": test, "program_solution": rule_text(outline_mode)}


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select a retained query")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    return (
        json.dumps(
            public_turn(episode, query_index),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()


def public_id(episode: dict[str, Any], query_index: int) -> str:
    return hashlib.sha256(public_bytes(episode, query_index)).hexdigest()


def causal_case(seed: int = 0):
    pair = generate_episode(seed, outline_mode="anchor_area_select", demos=3, queries=4)["test"][0]
    info = analyze(pair["input"])
    return {
        "settings": {"outline_mode": "anchor_area_select"},
        "input": deepcopy(pair["input"]),
        "program": SELECT_PROGRAM,
        "output": deepcopy(pair["output"]),
        "counterfactual_program": WRONG_PLUS_ONE_PROGRAM,
        "counterfactual_output": apply_wrong_plus_one(pair["input"]),
        "intermediate_value": {
            "anchor_bbox": info["anchor"]["bbox"],
            "anchor_area": info["anchor_area"],
            "candidate_bboxes": [item["bbox"] for item in info["candidates"]],
            "correct_target_index": info["target_index"],
            "wrong_target_index": info["wrong_target_index"],
        },
        "ablation": "wrong_intermediate",
    }
