"""Native episode-fixed hole-threshold family for ARC task 14dacb3b518f.

The input grammar keeps the canonical object-topology reasoning.  Every scene has
four separated color-6 components: a non-frame one-hole object, a two-hole
object, a dense zero-hole near-miss with a channel to the exterior, and a solid
zero-hole object.  ``min_holes=1`` is the exact canonical rule;
``min_holes=2`` changes only the threshold applied after the hole-count
intermediate has been computed.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from typing import Any, Callable

TASK_ID = "14dacb3b518f"
VERSION = "hole-threshold-native-v1"
THRESHOLDS = (1, 2)
DEFAULT_THRESHOLD = 1
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)

CANONICAL_PROGRAM = '(rule! (let ((dummy 0)) (define (nonzero-cells grid) (filter (lambda (p) (not (= (at grid (first p) (second p)) 0))) (grid-positions grid))) (define (crop-nonzero grid) (let ((cells (nonzero-cells grid))) (if (empty? cells) (list (list 0)) (let* ((bb (bbox-of-cells cells))) (subgrid grid (first bb) (second bb) (third bb) (fourth bb)))))) (define (f14b-binary-crop grid) (crop-nonzero (grid-from-fn (rows grid) (cols grid) (lambda (r c) (if (= (at grid r c) 0) 0 1))))) (define (f14b-hole-count grid) (let* ((binary (f14b-binary-crop grid)) (regions (find-0-regions binary 0))) (length (filter (lambda (region) (not (any? (lambda (p) (or (= (first p) 0) (= (first p) (- (rows binary) 1)) (= (second p) 0) (= (second p) (- (cols binary) 1)))) region))) regions)))) (define (s17b-object-crop grid obj) (let ((bb (obj-bbox obj))) (subgrid grid (first bb) (second bb) (third bb) (fourth bb)))) (for/fold ((out (empty-grid (rows g) (cols g) 0))) ((obj (in-list (objects g 0)))) (paint-cells out (obj-cells obj) (if (>= (f14b-hole-count (s17b-object-crop g obj)) 1) 8 2)))))'
_THRESHOLD_NEEDLE = "(>= (f14b-hole-count (s17b-object-crop g obj)) 1)"

_DEMO_SIZES = ((10, 12), (11, 13), (12, 14), (13, 15), (14, 16), (16, 18))
_QUERY_SIZES = ((18, 20), (22, 24), (26, 28), (30, 30))
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer; bool is forbidden")
    if not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_count(name: str, value: Any, limits: tuple[int, int]) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not limits[0] <= value <= limits[1]:
        raise ValueError(f"{name} must be in {limits[0]}..{limits[1]}")
    return value


def _validate_threshold(value: Any) -> int:
    if type(value) is not int:
        raise TypeError("min_holes must be an exact integer; bool is forbidden")
    if value not in THRESHOLDS:
        raise ValueError(f"min_holes must be one of {THRESHOLDS}")
    return value


def program_for(min_holes: Any) -> str:
    threshold = _validate_threshold(min_holes)
    if threshold == DEFAULT_THRESHOLD:
        return CANONICAL_PROGRAM
    if CANONICAL_PROGRAM.count(_THRESHOLD_NEEDLE) != 1:
        raise RuntimeError("canonical threshold expression is not uniquely replaceable")
    return CANONICAL_PROGRAM.replace(
        _THRESHOLD_NEEDLE,
        f"(>= (f14b-hole-count (s17b-object-crop g obj)) {threshold})",
        1,
    )


def _grid_error(grid: Any) -> str | None:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return "grid must be a nonempty list of nonempty rows"
    width = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return "grid dimensions must be in 1..30"
    for row in grid:
        if type(row) is not list or len(row) != width:
            return "grid must be rectangular"
        if any(type(cell) is not int or cell not in (0, 6) for cell in row):
            return "input cells must be exact integers in {0,6}"
    return None


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[set[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            start = (row, col)
            if grid[row][col] != 6 or start in seen:
                continue
            stack = [start]
            seen.add(start)
            cells: set[tuple[int, int]] = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in _DIR4:
                    nr, nc = r + dr, c + dc
                    nxt = (nr, nc)
                    if 0 <= nr < height and 0 <= nc < width and nxt not in seen and grid[nr][nc] == 6:
                        seen.add(nxt)
                        stack.append(nxt)
            result.append(cells)
    return result


def _hole_count(cells: set[tuple[int, int]]) -> int:
    r0, c0, r1, c1 = _bbox(cells)
    local_filled = {(r - r0, c - c0) for r, c in cells}
    height, width = r1 - r0 + 1, c1 - c0 + 1
    seen: set[tuple[int, int]] = set()
    holes = 0
    for row in range(height):
        for col in range(width):
            start = (row, col)
            if start in local_filled or start in seen:
                continue
            stack = [start]
            seen.add(start)
            region: set[tuple[int, int]] = set()
            while stack:
                r, c = stack.pop()
                region.add((r, c))
                for dr, dc in _DIR4:
                    nr, nc = r + dr, c + dc
                    nxt = (nr, nc)
                    if 0 <= nr < height and 0 <= nc < width and nxt not in local_filled and nxt not in seen:
                        seen.add(nxt)
                        stack.append(nxt)
            if not any(r in (0, height - 1) or c in (0, width - 1) for r, c in region):
                holes += 1
    return holes


def _is_thin_frame(cells: set[tuple[int, int]]) -> bool:
    r0, c0, r1, c1 = _bbox(cells)
    height, width = r1 - r0 + 1, c1 - c0 + 1
    if height < 3 or width < 3:
        return False
    normalized = {(r - r0, c - c0) for r, c in cells}
    perimeter = {(r, c) for r in range(height) for c in range(width)
                  if r in (0, height - 1) or c in (0, width - 1)}
    return normalized == perimeter


def _has_bbox_gap(cells: set[tuple[int, int]]) -> bool:
    r0, c0, r1, c1 = _bbox(cells)
    return any((r, c) not in cells for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))


def analyze_grid(grid: Any) -> dict[str, Any]:
    error = _grid_error(grid)
    if error:
        return {"errors": [error], "components": []}
    components = []
    for cells in _components(grid):
        components.append({
            "cells": sorted([list(cell) for cell in cells]),
            "size": len(cells),
            "bbox": list(_bbox(cells)),
            "hole_count": _hole_count(cells),
            "thin_frame": _is_thin_frame(cells),
            "bbox_gap": _has_bbox_gap(cells),
        })
    errors: list[str] = []
    if len(components) != 4:
        errors.append(f"expected four separated components, found {len(components)}")
    counts = {component["hole_count"] for component in components}
    if not {0, 1, 2} <= counts:
        errors.append(f"expected zero-, one-, and two-hole components, found {sorted(counts)}")
    if any(component["hole_count"] > 2 for component in components):
        errors.append("components may contain at most two enclosed holes")
    return {"errors": errors, "height": len(grid), "width": len(grid[0]), "components": components}


def _paint_by_predicate(grid: list[list[int]], predicate: Callable[[dict[str, Any]], bool]) -> list[list[int]]:
    facts = analyze_grid(grid)
    if facts["errors"]:
        raise ValueError("grid is outside the parametric grammar: " + "; ".join(facts["errors"]))
    output = [[0 for _ in row] for row in grid]
    for component in facts["components"]:
        color = 8 if predicate(component) else 2
        for row, col in component["cells"]:
            output[row][col] = color
    return output


def apply_rule(grid: list[list[int]], min_holes: Any) -> list[list[int]]:
    threshold = _validate_threshold(min_holes)
    return _paint_by_predicate(grid, lambda component: component["hole_count"] >= threshold)


def _full(height: int, width: int) -> set[tuple[int, int]]:
    return {(row, col) for row in range(height) for col in range(width)}


def _one_hole(height: int, width: int, variant: int) -> set[tuple[int, int]]:
    cells = _full(height, width)
    # Keep at least one filled interior row and column, so this is not merely a thin frame.
    r0 = 1
    r1 = max(1, height - 3)
    c0 = 1 + (variant % 2 if width >= 7 else 0)
    c1 = max(c0, width - 3)
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            cells.discard((row, col))
    return cells


def _two_holes(height: int, width: int, variant: int) -> set[tuple[int, int]]:
    del variant
    cells = _full(height, width)
    split = width // 2
    for row in range(1, max(2, height - 2)):
        for col in range(1, split):
            cells.discard((row, col))
        for col in range(split + 1, width - 1):
            cells.discard((row, col))
    return cells


def _leaky_dense(height: int, width: int, variant: int) -> set[tuple[int, int]]:
    cells = _full(height, width)
    r0, r1 = 1, max(1, height - 3)
    c0, c1 = 1, max(1, width - 3)
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            cells.discard((row, col))
    corridor_col = c0 + ((variant + width) % max(1, c1 - c0 + 1))
    for row in range(0, r0 + 1):
        cells.discard((row, corridor_col))
    return cells


def _solid(height: int, width: int, variant: int) -> set[tuple[int, int]]:
    cells = _full(height, width)
    # A boundary notch varies the silhouette without creating a hole.
    if height >= 6 and width >= 6:
        if variant % 2:
            cells.discard((height - 1, width // 2))
        else:
            cells.discard((height // 2, width - 1))
    return cells


_SHAPES: dict[str, Callable[[int, int, int], set[tuple[int, int]]]] = {
    "one_hole": _one_hole,
    "two_holes": _two_holes,
    "leaky_dense": _leaky_dense,
    "solid": _solid,
}


def _slots(height: int, width: int) -> list[tuple[int, int, int, int]]:
    middle_row, middle_col = height // 2, width // 2
    row_ranges = ((0, middle_row - 2), (middle_row + 1, height - 1))
    col_ranges = ((0, middle_col - 2), (middle_col + 1, width - 1))
    slots = [
        (row_ranges[0][0], col_ranges[0][0], row_ranges[0][1], col_ranges[0][1]),
        (row_ranges[0][0], col_ranges[1][0], row_ranges[0][1], col_ranges[1][1]),
        (row_ranges[1][0], col_ranges[0][0], row_ranges[1][1], col_ranges[0][1]),
        (row_ranges[1][0], col_ranges[1][0], row_ranges[1][1], col_ranges[1][1]),
    ]
    if any(r1 - r0 + 1 < 4 or c1 - c0 + 1 < 5 for r0, c0, r1, c1 in slots):
        raise ValueError("scene dimensions cannot support the four-object grammar")
    return slots


def _scene(seed: int, stream: str, index: int, height: int, width: int) -> list[list[int]]:
    digest = hashlib.sha256(f"{VERSION}:{seed}:{stream}:{index}".encode()).digest()
    rng = random.Random(int.from_bytes(digest[:16], "big"))
    kinds = list(_SHAPES)
    rng.shuffle(kinds)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for slot_index, (kind, slot) in enumerate(zip(kinds, _slots(height, width), strict=True)):
        r0, c0, r1, c1 = slot
        shape = _SHAPES[kind](r1 - r0 + 1, c1 - c0 + 1, rng.randrange(0, 2**31))
        for row, col in shape:
            grid[r0 + row][c0 + col] = 6
    facts = analyze_grid(grid)
    if facts["errors"]:
        raise AssertionError(f"constructed scene is invalid: {facts['errors']}")
    return grid


def episode_inputs(seed: Any, *, demos: Any = 3, queries: Any = 4) -> dict[str, list[list[list[int]]]]:
    seed = _validate_seed(seed)
    demos = _validate_count("demos", demos, DEMO_LIMITS)
    queries = _validate_count("queries", queries, QUERY_LIMITS)
    # Separate streams make the first query independent of the requested demo count,
    # and make both train/test prefixes invariant under their own requested counts.
    train = [_scene(seed, "train", index, *_DEMO_SIZES[index]) for index in range(demos)]
    test = [_scene(seed, "test", index, *_QUERY_SIZES[index]) for index in range(queries)]
    frozen = [json.dumps(grid, separators=(",", ":")) for grid in train + test]
    if len(frozen) != len(set(frozen)):
        raise AssertionError("episode inputs must be distinct")
    return {"train": train, "test": test}


def generate_episode(seed: Any, *, min_holes: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    threshold = _validate_threshold(min_holes)
    inputs = episode_inputs(seed, demos=demos, queries=queries)
    def pairs(grids: list[list[list[int]]]) -> list[dict[str, Any]]:
        return [{"input": copy.deepcopy(grid), "output": apply_rule(grid, threshold)} for grid in grids]
    return {
        "task_id": TASK_ID,
        "version": VERSION,
        "seed": _validate_seed(seed),
        "settings": {"min_holes": threshold},
        "program_solution": program_for(threshold),
        "train": pairs(inputs["train"]),
        "test": pairs(inputs["test"]),
    }


def _rival_thin_frame(grid: list[list[int]]) -> list[list[int]]:
    return _paint_by_predicate(grid, lambda component: component["thin_frame"])


def _rival_bbox_gap(grid: list[list[int]]) -> list[list[int]]:
    return _paint_by_predicate(grid, lambda component: component["bbox_gap"])


def _rival_large_component(grid: list[list[int]]) -> list[list[int]]:
    return _paint_by_predicate(grid, lambda component: component["size"] >= 12)


_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "thin_frame_only": _rival_thin_frame,
    "any_bbox_gap": _rival_bbox_gap,
    "large_component": _rival_large_component,
}


def audit_episode(episode: dict[str, Any]) -> dict[str, Any]:
    train = episode.get("train")
    test = episode.get("test")
    settings = episode.get("settings")
    if type(train) is not list or type(test) is not list or settings not in ({"min_holes": 1}, {"min_holes": 2}):
        raise ValueError("invalid episode")
    survivors = []
    for threshold in THRESHOLDS:
        if all(apply_rule(pair["input"], threshold) == pair["output"] for pair in train):
            survivors.append({"min_holes": threshold})
    rival_rows: dict[str, Any] = {}
    harmful = []
    for name, rival in _RIVALS.items():
        fits = all(rival(pair["input"]) == pair["output"] for pair in train)
        query_differs = any(rival(pair["input"]) != pair["output"] for pair in test)
        rival_rows[name] = {"fits_demonstrations": fits, "query_differs": query_differs}
        if fits and query_differs:
            harmful.append(name)
    return {
        "selected_setting": copy.deepcopy(settings),
        "surviving_settings": survivors,
        "rivals": rival_rows,
        "harmful_ambiguities": harmful,
        "limits": "Finite audit of the other declared threshold and three named shortcut rivals.",
    }


def public_payload(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [{"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
                  for pair in episode["train"]],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return (json.dumps(public_payload(episode), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def public_id(episode: dict[str, Any]) -> str:
    return hashlib.sha256(public_bytes(episode)).hexdigest()
