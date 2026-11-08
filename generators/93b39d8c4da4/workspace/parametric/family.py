"""Matched-input parametric stamp family for ARC task 93b39d8c4da4.

The exact canonical rule is ``template_transform=identity``.  Alternatives
mirror or rotate the input-derived, tight-normalized template before stamping it
at every visible color-3 marker.  Python outputs are deterministic claims;
native qualification independently re-executes every label through protected
Racket.
"""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
from itertools import combinations
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "93b39d8c4da4"
TRANSFORMS = ("identity", "mirror_lr", "rotate_cw")
SETTINGS = tuple({"template_transform": value} for value in TRANSFORMS)
DEMO_SIZES = ((12, 14), (15, 16), (18, 20), (21, 22), (24, 24), (27, 28))
QUERY_SIZES = ((30, 30), (24, 30), (30, 24), (27, 29))


def _settings(settings) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"template_transform"}
        or type(settings["template_transform"]) is not str
        or settings["template_transform"] not in TRANSFORMS
    ):
        raise ValueError(
            "settings must be exactly template_transform="
            "identity|mirror_lr|rotate_cw"
        )
    return settings["template_transform"]


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("shape cannot be empty")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((c, -r) for r, c in cells)


def _flip_lr(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((r, -c) for r, c in cells)


def _transform(cells: Iterable[tuple[int, int]], mode: str) -> tuple[tuple[int, int], ...]:
    cells = _normalize(cells)
    if mode == "identity":
        return cells
    if mode == "mirror_lr":
        return _flip_lr(cells)
    if mode == "rotate_cw":
        return _rotate(cells)
    raise ValueError(f"unknown transform {mode!r}")


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    seen = {next(iter(remaining))}
    todo = list(seen)
    while todo:
        r, c = todo.pop()
        for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if q in remaining and q not in seen:
                seen.add(q)
                todo.append(q)
    return seen == remaining


def _orbit(cells: Iterable[tuple[int, int]]) -> set[tuple[tuple[int, int], ...]]:
    cells = _normalize(cells)
    result = set()
    for reflected in (False, True):
        current = _flip_lr(cells) if reflected else cells
        for _ in range(4):
            result.add(current)
            current = _rotate(current)
    return result


@lru_cache(maxsize=3)
def _shape_bank(count: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    universe = tuple((r, c) for r in range(3) for c in range(3))
    shapes = {
        _normalize(cells)
        for cells in combinations(universe, count)
        if _connected(cells)
    }
    result = tuple(
        sorted(
            shape
            for shape in shapes
            if max(r for r, _ in shape) == 2
            and max(c for _, c in shape) == 2
            and len(_orbit(shape)) == 8
        )
    )
    if not result:
        raise RuntimeError(f"no asymmetric 3x3 shape with {count} cells")
    return result


def _rng(seed: int, split: str, index: int, label: str = "scene") -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}:{seed}:{split}:{index}:{label}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _overlap_delta(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    cells = set(shape)
    candidates = []
    for a in cells:
        for b in cells:
            dr, dc = b[0] - a[0], b[1] - a[1]
            if dr >= 0 and dc >= 0 and 2 <= dr + dc <= 3 and (dr, dc) != (0, 0):
                candidates.append((dr, dc))
    if not candidates:
        raise RuntimeError("asymmetric teaching shape lacks a nonadjacent overlap delta")
    return min(candidates, key=lambda p: (p[0] + p[1], p))


def _marker_pool(height: int, width: int, delta: tuple[int, int]) -> list[tuple[int, int]]:
    raw = [
        (0, 0),
        delta,
        (0, width - 3),
        (height - 3, 0),
        (0, width // 2 - 1),
        (height // 2 - 1, 0),
        (height - 3, width // 2 - 1),
        (height // 2 - 1, width - 3),
        (height - 3, width - 3),
        (height // 2 - 1, width // 2 - 1),
        (2, width - 3),
        (height - 3, 2),
    ]
    result = []
    for r, c in raw:
        r = max(0, min(height - 3, r))
        c = max(0, min(width - 3, c))
        if (r, c) not in result:
            result.append((r, c))
    return result


def _template_origin(seed: int, split: str, index: int, height: int, width: int) -> tuple[int, int]:
    if split == "query" and index == 0:
        return height - 3, width - 3
    rows = tuple(range(3, height - 5))
    cols = tuple(range(3, width - 5))
    if not rows or not cols:
        raise ValueError("canvas is too small for the parametric grammar")
    rng = _rng(seed, split, index, "template-origin")
    return rng.choice(rows), rng.choice(cols)


def sample_input(seed: int, split: str, index: int, *, height: int, width: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("demo", "query"):
        raise ValueError("split must be demo or query")
    _integer(index, 0, 63, "index")
    _integer(height, 9, 30, "height")
    _integer(width, 9, 30, "width")

    count = (5, 6, 7)[(index + (1 if split == "query" else 0)) % 3]
    bank = _shape_bank(count)
    rng = _rng(seed, split, index)
    start = rng.randrange(len(bank))
    template_origin = _template_origin(seed, split, index, height, width)

    for offset in range(len(bank)):
        shape = bank[(start + offset) % len(bank)]
        delta = _overlap_delta(shape)
        marker_count = 6 + ((index + (2 if split == "query" else 0)) % 3)
        pool = _marker_pool(height, width, delta)
        tr, tc = template_origin
        template_box = {
            (r, c)
            for r in range(tr, tr + 3)
            for c in range(tc, tc + 3)
        }
        forced = [pool[0], pool[1]]
        tail = [p for p in pool[2:] if p not in template_box]
        _rng(seed, split, index, "marker-order").shuffle(tail)
        anchors = [p for p in forced if p not in template_box] + tail
        anchors = anchors[:marker_count]
        if len(anchors) < marker_count:
            continue
        grid = [[0 for _ in range(width)] for _ in range(height)]
        for dr, dc in shape:
            grid[tr + dr][tc + dc] = 2
        if any(grid[r][c] != 0 for r, c in anchors):
            continue
        for r, c in anchors:
            grid[r][c] = 3
        facts = analyze(grid)
        if facts["valid_for_all_settings"] and facts["setting_outputs_distinct"]:
            return grid
    raise RuntimeError("failed to construct a setting-distinguishing stamp scene")


def _grid(grid) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must be a list with 1..30 rows")
    if not grid or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    rows = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular list-of-lists")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid cells must be exact integer ARC colors 0..9")
        rows.append(list(row))
    return rows


def _parts(grid) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    rows = _grid(grid)
    template = tuple((r, c) for r, row in enumerate(rows) for c, v in enumerate(row) if v == 2)
    marks = tuple((r, c) for r, row in enumerate(rows) for c, v in enumerate(row) if v == 3)
    return template, marks


def _shape_size(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    shape = tuple(shape)
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def solve_with_shape(grid, settings, shape: Iterable[tuple[int, int]]) -> list[list[int]]:
    mode = _settings(settings)
    rows = _grid(grid)
    transformed = _transform(shape, mode)
    _, marks = _parts(rows)
    out = [[0 for _ in row] for row in rows]
    for ar, ac in marks:
        for dr, dc in transformed:
            rr, cc = ar + dr, ac + dc
            if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                out[rr][cc] = 8
    return out


def solve(grid, settings) -> list[list[int]]:
    template, _ = _parts(grid)
    if not template or not _connected(template):
        raise ValueError("one connected color-2 template is required")
    return solve_with_shape(grid, settings, _normalize(template))


def analyze(grid) -> dict:
    rows = _grid(grid)
    height, width = len(rows), len(rows[0])
    template, marks = _parts(rows)
    colors = {v for row in rows for v in row}
    valid = colors <= {0, 2, 3} and bool(template) and _connected(template) and len(marks) >= 2
    shape = _normalize(template) if template else ()
    if shape:
        sh, sw = _shape_size(shape)
        valid = valid and sh == 3 and sw == 3 and len(_orbit(shape)) == 8
    transformed_shapes = []
    if shape:
        for mode in TRANSFORMS:
            transformed = _transform(shape, mode)
            transformed_shapes.append(transformed)
            th, tw = _shape_size(transformed)
            if any(not (0 <= r <= height - th and 0 <= c <= width - tw) for r, c in marks):
                valid = False
    stamp_sets = []
    if shape:
        for r, c in marks:
            stamp_sets.append({(r + dr, c + dc) for dr, dc in shape})
    overlapping = any(stamp_sets[i] & stamp_sets[j]
                      for i in range(len(stamp_sets)) for j in range(i + 1, len(stamp_sets)))
    outputs = []
    if valid:
        outputs = [solve(rows, setting) for setting in SETTINGS]
    return {
        "height": height,
        "width": width,
        "template_cells": len(template),
        "template_bbox": list(_shape_size(shape)) if shape else [0, 0],
        "template_orbit": len(_orbit(shape)) if shape else 0,
        "marker_count": len(marks),
        "overlapping_stamp_pair": overlapping,
        "setting_outputs_distinct": len({repr(output) for output in outputs}) == len(SETTINGS),
        "valid_for_all_settings": bool(valid),
    }


def program(settings) -> str:
    mode = _settings(settings)
    name = {
        "identity": "canonical.rkt",
        "mirror_lr": "mirror_lr.rkt",
        "rotate_cw": "rotate_cw.rkt",
    }[mode]
    return Path(__file__).resolve().with_name(name).read_text(encoding="utf-8")


def generate(seed, settings, demos=2, queries=4) -> dict:
    _settings(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train_inputs = [
        sample_input(seed, "demo", i, height=h, width=w)
        for i, (h, w) in enumerate(DEMO_SIZES[:demos])
    ]
    query_bank = [
        sample_input(seed, "query", i, height=h, width=w)
        for i, (h, w) in enumerate(QUERY_SIZES)
    ]
    return {
        "train": [{"input": grid, "output": solve(grid, settings)} for grid in train_inputs],
        "test": [
            {"input": grid, "output": solve(grid, settings)}
            for grid in query_bank[:queries]
        ],
        "program_solution": program(settings),
    }


def public_turn(episode, query_index=0) -> dict:
    if type(query_index) is not int:
        raise ValueError("query_index must be an exact integer")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("episode needs visible train pairs and the selected query")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[query_index]["input"])}],
    }


def _rival_first_marker(mode: str) -> str:
    transform = {
        "identity": "(normalize-cells shape)",
        "mirror_lr": "(normalize-cells (flip-cells-lr shape))",
        "rotate_cw": "(normalize-cells (rotate-cells-cw shape))",
    }[mode]
    return f"""(rule!
  (let ((dummy 0))
    (define shape (normalize-cells (find-color g 2)))
    (define transformed {transform})
    (define mark (first (find-color g 3)))
    (define cells
      (map (lambda (p) (list (+ (first mark) (first p))
                             (+ (second mark) (second p)))) transformed))
    (paint-cells (empty-grid (rows g) (cols g) 0) cells 8)))"""


def _rival_bbox_fill() -> str:
    return """(rule!
  (let ((dummy 0))
    (define shape (normalize-cells (find-color g 2)))
    (define bb (bbox-of-cells shape))
    (define sh (+ 1 (- (third bb) (first bb))))
    (define sw (+ 1 (- (fourth bb) (second bb))))
    (grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (if (any?
              (lambda (mark)
                (and (<= (first mark) r) (< r (+ (first mark) sh))
                     (<= (second mark) c) (< c (+ (second mark) sw))))
              (find-color g 3))
            8 0)))))"""


def _rival_fixed_l(mode: str) -> str:
    transform = {
        "identity": "base",
        "mirror_lr": "(normalize-cells (flip-cells-lr base))",
        "rotate_cw": "(normalize-cells (rotate-cells-cw base))",
    }[mode]
    return f"""(rule!
  (let ((dummy 0))
    (define base (list (list 0 0) (list 1 0) (list 2 0) (list 2 1)))
    (define shape {transform})
    (define stamps
      (flatmap
        (lambda (mark)
          (map (lambda (p) (list (+ (first mark) (first p))
                                 (+ (second mark) (second p)))) shape))
        (find-color g 3)))
    (paint-cells (empty-grid (rows g) (cols g) 0) stamps 8)))"""


def rival_programs(settings) -> dict[str, str]:
    mode = _settings(settings)
    result = {
        "first_marker_only": _rival_first_marker(mode),
        "bbox_fill": _rival_bbox_fill(),
        "fixed_l_intermediate": _rival_fixed_l(mode),
        "preserve_input": "(rule! (let ((dummy 0)) g))",
    }
    for other in SETTINGS:
        other_mode = other["template_transform"]
        if other_mode != mode:
            result[f"other_setting_{other_mode}"] = program(other)
    return result
