"""Matched-input family for bounding-box completion plus post-fill retention.

The default is the exact canonical program.  The alternate first completes all
source components, then recomputes same-color 4-connectivity on that filled
intermediate and retains every uniquely largest post-fill component.  Generated
lessons include components that merge only after completion, so pre-fill ranking
and per-color aggregation are executable but wrong shortcuts.
"""
from __future__ import annotations

from collections import Counter, deque
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "297c05190f7c"
RETENTIONS = ("all", "largest_postfill_component")
DEFAULT_RETENTION = "all"
CANDIDATE_RULES = (
    *RETENTIONS,
    "largest_original_component",
    "largest_original_bbox",
    "largest_prefill_color_total",
    "largest_postfill_color_total",
    "merged_components_only",
    "smallest_postfill_component",
)
ROOT = Path(__file__).resolve().parents[4]
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))

_TRAIN_PROFILES = (
    (10, 12, "horizontal", "merge"),
    (12, 10, "vertical", "single"),
    (15, 16, "vertical", "merge"),
    (18, 20, "horizontal", "single"),
    (24, 22, "horizontal", "merge"),
    (28, 27, "vertical", "single"),
)
_TEST_PROFILES = (
    (11, 15, "vertical", "merge"),
    (17, 19, "horizontal", "single"),
    (24, 28, "vertical", "merge"),
    (30, 30, "horizontal", "single"),
)

Grid = list[list[int]]
Cell = tuple[int, int]


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def validate_retention(value: Any) -> str:
    if type(value) is not str or value not in RETENTIONS:
        raise ValueError(f"retention must be one of {RETENTIONS}")
    return value


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"retention"}:
        raise ValueError("settings must contain exactly retention")
    return validate_retention(settings["retention"])


def validate_request(seed: Any, demos: Any, queries: Any) -> None:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)


def _grid(grid: Any) -> Grid:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 for value in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return [row[:] for row in grid]


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    if len(programs) != 1:
        raise ValueError("require one exact canonical program")
    return programs.pop()


_LARGEST_PROGRAM = r"""(rule!
  (let* ((filled
           (for/fold ([out (empty-grid (rows g) (cols g) 0)])
                     ([obj (in-list (objects g 0))])
             (let ([bb (obj-bbox obj)])
               (paint-cells out
                            (positions-in-rect (first bb) (second bb)
                                               (third bb) (fourth bb))
                            (obj-color obj)))))
         (filled-objects (objects filled 0))
         (maximum-size
           (if (null? filled-objects)
               0
               (apply max (map obj-size filled-objects))))
         (selected
           (filter (lambda (obj) (= (obj-size obj) maximum-size))
                   filled-objects)))
    (for/fold ([out (empty-grid (rows g) (cols g) 0)])
              ([obj (in-list selected)])
      (paint-cells out (obj-cells obj) (obj-color obj)))))"""


def program_for(retention: str) -> str:
    retention = validate_retention(retention)
    return canonical_program() if retention == "all" else _LARGEST_PROGRAM


def _components(grid: Grid) -> list[dict[str, Any]]:
    g = _grid(grid)
    h, w = len(g), len(g[0])
    seen: set[Cell] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = g[r][c]
            if color == 0 or (r, c) in seen:
                continue
            seen.add((r, c))
            queue = deque([(r, c)])
            cells: list[Cell] = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in _DIRS:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and g[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            r0, r1 = min(p[0] for p in cells), max(p[0] for p in cells)
            c0, c1 = min(p[1] for p in cells), max(p[1] for p in cells)
            result.append(
                {
                    "cells": cells,
                    "color": color,
                    "bbox": (r0, c0, r1, c1),
                    "size": len(cells),
                    "bbox_area": (r1 - r0 + 1) * (c1 - c0 + 1),
                }
            )
    return result


def fill_boxes(grid: Grid, components: list[dict[str, Any]] | None = None) -> Grid:
    g = _grid(grid)
    out = [[0] * len(g[0]) for _ in range(len(g))]
    for component in _components(g) if components is None else components:
        r0, c0, r1, c1 = component["bbox"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = component["color"]
    return out


def _keep_components(grid: Grid, predicate: Callable[[dict[str, Any]], bool]) -> Grid:
    g = _grid(grid)
    out = [[0] * len(g[0]) for _ in range(len(g))]
    for component in _components(g):
        if predicate(component):
            for r, c in component["cells"]:
                out[r][c] = component["color"]
    return out


def evaluate(grid: Grid, retention: str = "all") -> Grid:
    retention = validate_retention(retention)
    filled = fill_boxes(grid)
    if retention == "all":
        return filled
    components = _components(filled)
    maximum = max((component["size"] for component in components), default=0)
    return _keep_components(filled, lambda component: component["size"] == maximum)


def _selected_original(grid: Grid, score: Callable[[dict[str, Any]], int]) -> Grid:
    components = _components(grid)
    maximum = max((score(component) for component in components), default=0)
    return fill_boxes(grid, [component for component in components if score(component) == maximum])


def _postfill_overlap_counts(grid: Grid, filled: Grid) -> dict[tuple[Cell, ...], int]:
    original_boxes = [
        {
            (r, c)
            for r in range(component["bbox"][0], component["bbox"][2] + 1)
            for c in range(component["bbox"][1], component["bbox"][3] + 1)
        }
        for component in _components(grid)
    ]
    result = {}
    for component in _components(filled):
        cells = set(component["cells"])
        result[tuple(component["cells"])] = sum(bool(cells & box) for box in original_boxes)
    return result


def evaluate_candidate(grid: Grid, name: str) -> Grid:
    if name in RETENTIONS:
        return evaluate(grid, name)
    if name == "largest_original_component":
        return _selected_original(grid, lambda component: component["size"])
    if name == "largest_original_bbox":
        return _selected_original(grid, lambda component: component["bbox_area"])
    filled = fill_boxes(grid)
    if name == "largest_prefill_color_total":
        totals = Counter(component["color"] for component in [] )
        totals = Counter()
        for component in _components(grid):
            totals[component["color"]] += component["size"]
        maximum = max(totals.values(), default=0)
        winners = {color for color, count in totals.items() if count == maximum}
        return [[value if value in winners else 0 for value in row] for row in filled]
    if name == "largest_postfill_color_total":
        totals = Counter(value for row in filled for value in row if value != 0)
        maximum = max(totals.values(), default=0)
        winners = {color for color, count in totals.items() if count == maximum}
        return [[value if value in winners else 0 for value in row] for row in filled]
    if name == "merged_components_only":
        overlap = _postfill_overlap_counts(grid, filled)
        return _keep_components(
            filled,
            lambda component: overlap.get(tuple(component["cells"]), 0) >= 2,
        )
    if name == "smallest_postfill_component":
        components = _components(filled)
        minimum = min((component["size"] for component in components), default=0)
        return _keep_components(filled, lambda component: component["size"] == minimum)
    raise ValueError(f"unknown candidate {name!r}")


def teaching_survivors(train: list[dict[str, Grid]]) -> list[str]:
    return [
        name
        for name in CANDIDATE_RULES
        if all(evaluate_candidate(pair["input"], name) == pair["output"] for pair in train)
    ]


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _edge_shape(height: int, width: int, corner: str) -> set[Cell]:
    if corner == "tl":
        return {(0, c) for c in range(width)} | {(r, 0) for r in range(height)}
    if corner == "tr":
        return {(0, c) for c in range(width)} | {(r, width - 1) for r in range(height)}
    if corner == "bl":
        return {(height - 1, c) for c in range(width)} | {(r, 0) for r in range(height)}
    if corner == "br":
        return {(height - 1, c) for c in range(width)} | {(r, width - 1) for r in range(height)}
    raise ValueError(corner)


def _dense_shape(height: int, width: int, salt: int) -> set[Cell]:
    holes = {
        (r, c)
        for r in range(1, height - 1)
        for c in range(1, width - 1)
        if (r * 5 + c * 7 + salt) % 11 == 0
    }
    # Keep the object near-solid and connected even in small boxes.
    return {(r, c) for r in range(height) for c in range(width) if (r, c) not in holes}


def _paint(grid: Grid, top: int, left: int, shape: set[Cell], color: int) -> None:
    for r, c in shape:
        if grid[top + r][left + c] != 0:
            raise ValueError("constructed component overlap")
        grid[top + r][left + c] = color


def _transform(grid: Grid, code: int) -> Grid:
    if code == 0:
        return [row[:] for row in grid]
    if code == 1:
        return [list(reversed(row)) for row in grid]
    if code == 2:
        return [row[:] for row in reversed(grid)]
    if code == 3:
        return [list(reversed(row)) for row in reversed(grid)]
    if code == 4:
        return [list(row) for row in zip(*grid)]
    if code == 5:
        return [list(reversed(row)) for row in zip(*grid)]
    raise ValueError(code)


def _scene(seed: int, split: str, index: int, profile: tuple[int, int, str, str]) -> Grid:
    h, w, axis, winner_kind = profile
    rng = _rng(seed, split, index)
    colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 4)
    cluster_color, winner_color, extra_color, other_color = colors
    grid = [[0] * w for _ in range(h)]

    if axis == "horizontal":
        bh = max(3, min(7, h // 4))
        bw = max(3, min(7, (w - 3) // 2))
        top, left = 1, 1
        _paint(grid, top, left, _edge_shape(bh, bw, "tl"), cluster_color)
        _paint(grid, top, left + bw, _edge_shape(bh, bw, "br"), cluster_color)
        cluster_bottom = top + bh - 1
        free_top = cluster_bottom + 2
        if winner_kind == "merge":
            dh, dw = bh + 1, bw + 1
        else:
            dh, dw = h - free_top - 1, w - 2
        if dh < 2 or dw < 2:
            raise ValueError("profile too small")
        dtop = h - dh - 1
        dleft = w - dw - 1
        _paint(grid, dtop, dleft, _dense_shape(dh, dw, index), winner_color)
        if winner_kind == "merge":
            _paint(grid, h - 3, 1, {(0, 0), (1, 0), (1, 1)}, cluster_color)
            if w - (left + 2 * bw) >= 3:
                _paint(grid, 1, w - 3, {(0, 0), (0, 1), (1, 1)}, extra_color)
        else:
            if w - (left + 2 * bw) >= 3:
                _paint(grid, 1, w - 3, {(0, 0), (1, 0), (1, 1)}, other_color)
    else:
        bh = max(3, min(7, (h - 3) // 2))
        bw = max(3, min(7, w // 4))
        top, left = 1, 1
        _paint(grid, top, left, _edge_shape(bh, bw, "tl"), cluster_color)
        _paint(grid, top + bh, left, _edge_shape(bh, bw, "br"), cluster_color)
        cluster_right = left + bw - 1
        free_left = cluster_right + 2
        if winner_kind == "merge":
            dh, dw = bh + 1, bw + 1
        else:
            dh, dw = h - 2, w - free_left - 1
        if dh < 2 or dw < 2:
            raise ValueError("profile too small")
        dtop = h - dh - 1
        dleft = w - dw - 1
        _paint(grid, dtop, dleft, _dense_shape(dh, dw, index), winner_color)
        if winner_kind == "merge":
            _paint(grid, 1, w - 3, {(0, 0), (0, 1), (1, 0)}, cluster_color)
            if h - (top + 2 * bh) >= 3:
                _paint(grid, h - 3, 1, {(0, 0), (1, 0), (1, 1)}, extra_color)
        else:
            if h - (top + 2 * bh) >= 3:
                _paint(grid, h - 3, 1, {(0, 0), (0, 1), (1, 1)}, other_color)

    # A source-only singleton-like distractor prevents fixed component-count rules.
    spot = (h // 2, w // 2)
    if grid[spot[0]][spot[1]] == 0:
        grid[spot[0]][spot[1]] = other_color

    # Palette and orientation are independent of the requested retention.
    transformed = _transform(grid, rng.randrange(6))
    filled = fill_boxes(transformed)
    components = _components(filled)
    sizes = sorted((component["size"] for component in components), reverse=True)
    if len(sizes) < 2 or sizes[0] == sizes[1]:
        raise ValueError("scene must have a unique largest post-fill component")
    if evaluate(transformed, "all") == evaluate(transformed, "largest_postfill_component"):
        raise ValueError("settings must differ on every scene")
    return transformed


def _bank(seed: int, split: str, profiles: tuple[tuple[int, int, str, str], ...]) -> list[Grid]:
    return [_scene(seed, split, index, profile) for index, profile in enumerate(profiles)]


def generate_episode(seed: int, retention: str, *, demos: int, queries: int) -> dict[str, Any]:
    validate_request(seed, demos, queries)
    retention = validate_retention(retention)
    train_inputs = _bank(seed, "train", _TRAIN_PROFILES)
    test_inputs = _bank(seed, "test", _TEST_PROFILES)
    train = [
        {"input": grid, "output": evaluate(grid, retention)}
        for grid in train_inputs[:demos]
    ]
    test = [
        {"input": grid, "output": evaluate(grid, retention)}
        for grid in test_inputs[:queries]
    ]
    if teaching_survivors(train) != [retention]:
        raise RuntimeError("teaching bank does not uniquely identify the requested rule")
    return {
        "train": train,
        "test": test,
        "program_solution": program_for(retention),
        "settings": {"retention": retention},
        "metadata": {
            "source": "matched full-bank prefix",
            "sequential": "complete boxes, recompute post-fill connectivity, then retain",
        },
    }


def _racket_original_selection(score: str) -> str:
    return f"""(rule!
  (let* ((source (objects g 0))
         (score (lambda (obj) {score}))
         (maximum (if (null? source) 0 (apply max (map score source))))
         (selected (filter (lambda (obj) (= (score obj) maximum)) source)))
    (for/fold ([out (empty-grid (rows g) (cols g) 0)])
              ([obj (in-list selected)])
      (let ([bb (obj-bbox obj)])
        (paint-cells out
                     (positions-in-rect (first bb) (second bb)
                                        (third bb) (fourth bb))
                     (obj-color obj))))))"""


def rival_program(name: str) -> str:
    if name in RETENTIONS:
        return program_for(name)
    if name == "largest_original_component":
        return _racket_original_selection("(obj-size obj)")
    if name == "largest_original_bbox":
        return _racket_original_selection(
            "(let ([bb (obj-bbox obj)]) (* (+ 1 (- (third bb) (first bb))) (+ 1 (- (fourth bb) (second bb)))))"
        )
    if name == "largest_prefill_color_total":
        return r"""(rule!
  (let* ((source (objects g 0))
         (colors (remove-duplicates (map obj-color source)))
         (score (lambda (color)
                  (apply + (map obj-size (filter (lambda (obj) (= (obj-color obj) color)) source)))))
         (maximum (if (null? colors) 0 (apply max (map score colors))))
         (winners (filter (lambda (color) (= (score color) maximum)) colors))
         (filled
           (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([obj (in-list source)])
             (let ([bb (obj-bbox obj)])
               (paint-cells out (positions-in-rect (first bb) (second bb) (third bb) (fourth bb))
                            (obj-color obj))))))
    (cellmap filled (r c v) (if (member? v winners) v 0))))"""
    if name == "largest_postfill_color_total":
        return r"""(rule!
  (let* ((filled
           (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([obj (in-list (objects g 0))])
             (let ([bb (obj-bbox obj)])
               (paint-cells out (positions-in-rect (first bb) (second bb) (third bb) (fourth bb))
                            (obj-color obj)))))
         (colors (remove-duplicates (filter (lambda (v) (!= v 0)) (apply append filled))))
         (score (lambda (color) (count-color filled color)))
         (maximum (if (null? colors) 0 (apply max (map score colors))))
         (winners (filter (lambda (color) (= (score color) maximum)) colors)))
    (cellmap filled (r c v) (if (member? v winners) v 0))))"""
    if name == "smallest_postfill_component":
        return _LARGEST_PROGRAM.replace("(apply max", "(apply min").replace("maximum-size", "minimum-size")
    # merged_components_only is kept as a Python audit rival; the protected audit
    # exercises the two strongest pre-fill/order counterfactuals above.
    raise ValueError(f"no standalone Racket rival for {name}")
