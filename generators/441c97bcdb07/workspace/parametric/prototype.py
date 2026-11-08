"""Matched-input completion-transform family for task 441c97bcdb07.

The canonical setting copies the pivot shape unchanged to the missing fourth
corner.  The alternative first infers whether the rectangle of source copies is
wider or taller, then turns the copied shape clockwise for a horizontal dominant
span and counterclockwise for a vertical dominant span.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable


TASK_ID = "441c97bcdb07"
FAMILY_VERSION = "1.0.0"
CANONICAL = "translate"
ALTERNATE = "span_directed_turn"
ALLOWED_TRANSFORMS = (CANONICAL, ALTERNATE)
CANONICAL_SHA256 = "a51bdd8a29a68d931403ff3d56792b2c53d8d8920dd22fecb3aa7af91c1abda7"
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)

# (height, width, shape_id, top, left, row_span, col_span)
# The first two demos deliberately cover both dominant spans, so even the
# minimum two-example lesson identifies the hidden setting and rejects fixed
# clockwise/counterclockwise shortcuts.
DEMO_PROFILES = (
    (11, 15, 0, 0, 0, 5, 9),
    (18, 14, 5, 0, 1, 10, 6),
    (14, 20, 1, 1, 0, 7, 12),
    (22, 16, 6, 0, 0, 12, 8),
    (20, 26, 4, 0, 1, 11, 18),
    (26, 20, 7, 0, 0, 17, 9),
)
QUERY_PROFILES = (
    (12, 18, 2, 0, 0, 6, 13),
    (20, 15, 4, 1, 0, 13, 8),
    (24, 29, 6, 0, 1, 14, 20),
    (30, 30, 7, 0, 0, 22, 18),
)

# Connected asymmetric shapes.  The final profile is a 25-cell 8x7 motif, so
# the 30x30 query exercises the real object extraction and transformation logic
# rather than padding a tiny canonical puzzle.
_SHAPE_MASKS = (
    ("111", "100", "110"),
    ("1110", "0010", "0011"),
    ("1100", "0110", "0011", "0001"),
    ("11100", "00110", "00010", "00011"),
    ("11000", "01110", "00010", "00011", "00001"),
    ("11100", "00100", "00110", "00010", "00011", "00001"),
    ("111000", "001000", "001100", "000100", "000110", "000010", "000011"),
    (
        "1111000",
        "0111000",
        "0011110",
        "0011110",
        "0001111",
        "0000111",
        "0000011",
        "0000001",
    ),
)

DECLARED_SHORTCUTS = (
    "always_cw",
    "always_ccw",
    "reverse_span_turn",
    "always_180",
    "wide_only_turn",
    "tall_only_turn",
    "turn_large_only",
    "turn_small_only",
)

_CANONICAL_PAINT = (
    "(paint-cells g (map (lambda (p) (list (+ mr (first p)) "
    "(+ mc (second p)))) (second pivot)) (first pivot))"
)
_ALTERNATE_PAINT = """(let* ((row-span (- mr prow))
             (col-span (- mc pcol))
             (sh (third pivot))
             (sw (fourth pivot))
             (turned
               (if (> col-span row-span)
                   (map (lambda (p)
                          (list (second p) (- sh 1 (first p))))
                        (second pivot))
                   (map (lambda (p)
                          (list (- sw 1 (second p)) (first p)))
                        (second pivot)))))
        (paint-cells g
          (map (lambda (p)
                 (list (+ mr (first p)) (+ mc (second p))))
               turned)
          (first pivot)))"""


def _cells(mask: tuple[str, ...]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (row, col)
        for row, line in enumerate(mask)
        for col, value in enumerate(line)
        if value == "1"
    )


SHAPES = tuple(_cells(mask) for mask in _SHAPE_MASKS)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    materialized = tuple(cells)
    row0 = min(row for row, _ in materialized)
    col0 = min(col for _, col in materialized)
    return tuple(sorted((row - row0, col - col0) for row, col in materialized))


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _rotate_cw(shape: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    height, _width = _shape_dims(shape)
    return _normalize((col, height - 1 - row) for row, col in shape)


def _rotate_ccw(shape: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    _height, width = _shape_dims(shape)
    return _normalize((width - 1 - col, row) for row, col in shape)


def _rotate_180(shape: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    height, width = _shape_dims(shape)
    return _normalize((height - 1 - row, width - 1 - col) for row, col in shape)


def _flip_lr(shape: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    _height, width = _shape_dims(shape)
    return _normalize((row, width - 1 - col) for row, col in shape)


def _validate_shape_bank() -> None:
    for index, shape in enumerate(SHAPES):
        if not shape:
            raise RuntimeError(f"shape {index} is empty")
        cells = set(shape)
        seen = {next(iter(cells))}
        stack = list(seen)
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in cells and neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        if seen != cells:
            raise RuntimeError(f"shape {index} is not 4-connected")
        if shape == _rotate_cw(shape) or shape == _rotate_ccw(shape):
            raise RuntimeError(f"shape {index} does not distinguish a quarter turn")
        if _rotate_cw(shape) == _rotate_ccw(shape):
            raise RuntimeError(f"shape {index} does not distinguish dominant-span direction")


_validate_shape_bank()


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer; bool is forbidden")
    if not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_counts(demos: Any, queries: Any) -> tuple[int, int]:
    for name, value in (("demos", demos), ("queries", queries)):
        if type(value) is not int:
            raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not DEMO_LIMITS[0] <= demos <= DEMO_LIMITS[1]:
        raise ValueError(f"demos must be in {DEMO_LIMITS[0]}..{DEMO_LIMITS[1]}")
    if not QUERY_LIMITS[0] <= queries <= QUERY_LIMITS[1]:
        raise ValueError(f"queries must be in {QUERY_LIMITS[0]}..{QUERY_LIMITS[1]}")
    return demos, queries


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"completion_transform"}:
        raise ValueError("settings must contain exactly completion_transform")
    selected = settings["completion_transform"]
    if type(selected) is not str or selected not in ALLOWED_TRANSFORMS:
        raise ValueError(f"completion_transform must be one of {list(ALLOWED_TRANSFORMS)}")
    return selected


@lru_cache(maxsize=1)
def canonical_program() -> str:
    raw = Path(__file__).with_name("canonical.rkt").read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != CANONICAL_SHA256:
        raise ValueError(f"canonical.rkt drifted: {digest}")
    source = raw.decode("utf-8")
    if source.count(_CANONICAL_PAINT) != 1:
        raise ValueError("canonical paint site is not uniquely replaceable")
    return source


@lru_cache(maxsize=1)
def alternate_program() -> str:
    return canonical_program().replace(_CANONICAL_PAINT, _ALTERNATE_PAINT, 1)


@lru_cache(maxsize=1)
def wrong_intermediate_program() -> str:
    source = alternate_program()
    marker = "(> col-span row-span)"
    if source.count(marker) != 1:
        raise ValueError("dominant-span predicate is not uniquely replaceable")
    return source.replace(marker, "(< col-span row-span)", 1)


def program_for(selected: str) -> str:
    if selected == CANONICAL:
        return canonical_program()
    if selected == ALTERNATE:
        return alternate_program()
    raise ValueError(f"unknown completion transform {selected!r}")


def _stream_rng(seed: int, split: str, index: int) -> random.Random:
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    material = f"{TASK_ID}|{FAMILY_VERSION}|{seed}|{split}|{index}".encode()
    digest = hashlib.sha256(material).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _dimension_preserving_variant(
    shape: tuple[tuple[int, int], ...], variant: int
) -> tuple[tuple[int, int], ...]:
    if variant == 0:
        return shape
    if variant == 1:
        return _rotate_180(shape)
    if variant == 2:
        return _flip_lr(shape)
    if variant == 3:
        return _rotate_180(_flip_lr(shape))
    raise ValueError("variant must be 0..3")


def _paint(
    grid: list[list[int]],
    shape: tuple[tuple[int, int], ...],
    origin: tuple[int, int],
    color: int,
) -> None:
    row0, col0 = origin
    for row, col in shape:
        target_row, target_col = row0 + row, col0 + col
        if not (0 <= target_row < len(grid) and 0 <= target_col < len(grid[0])):
            raise ValueError("shape paint would leave the grid")
        if grid[target_row][target_col] != 0:
            raise ValueError("shape paint overlaps an existing object")
        grid[target_row][target_col] = color


def _profile(split: str, index: int) -> tuple[int, int, int, int, int, int, int]:
    profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
    if type(index) is not int or not 0 <= index < len(profiles):
        raise ValueError(f"{split} index is outside the supported profile range")
    return profiles[index]


def build_input(seed: Any, split: str, index: Any) -> list[list[int]]:
    seed = _validate_seed(seed)
    if type(index) is not int:
        raise TypeError("index must be an exact integer; bool is forbidden")
    height, width, shape_id, top, left, row_span, col_span = _profile(split, index)
    rng = _stream_rng(seed, split, index)
    shape = _dimension_preserving_variant(SHAPES[shape_id], rng.randrange(4))
    color = 1 + rng.randrange(9)

    # Small span jitter adds layout variety without changing the scheduled
    # dominant axis or the exact query dimensions.  The 30x30 stress case stays
    # boundary-pinned so its bottom contact is guaranteed.
    if not (split == "query" and index == 3):
        height_shape, width_shape = _shape_dims(shape)
        max_dim = max(height_shape, width_shape)
        candidates: list[tuple[int, int]] = []
        for row_delta in (-1, 0, 1):
            for col_delta in (-1, 0, 1):
                candidate_row = row_span + row_delta
                candidate_col = col_span + col_delta
                if candidate_row < height_shape + 1 or candidate_col < width_shape + 1:
                    continue
                if top + candidate_row + max_dim > height:
                    continue
                if left + candidate_col + max_dim > width:
                    continue
                if (col_span > row_span) != (candidate_col > candidate_row):
                    continue
                candidates.append((candidate_row, candidate_col))
        if not candidates:
            raise RuntimeError("profile has no legal jittered spans")
        row_span, col_span = candidates[rng.randrange(len(candidates))]

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for origin in ((top, left), (top, left + col_span), (top + row_span, left)):
        _paint(grid, shape, origin, color)
    analysis = analyze_input(grid)
    expected = "horizontal" if col_span > row_span else "vertical"
    if analysis["dominant_span"] != expected:
        raise RuntimeError("constructed input did not preserve its scheduled dominant span")
    return grid


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def analyze_input(grid: Any) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) and row for row in grid):
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if len(grid) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30")

    by_color: dict[int, set[tuple[int, int]]] = {}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("every cell must be an exact ARC color 0..9")
            if value:
                by_color.setdefault(value, set()).add((row_index, col_index))
    if len(by_color) != 1:
        raise ValueError("input must use exactly one nonzero color")
    color, cells = next(iter(by_color.items()))
    components = _components(cells)
    if len(components) != 3:
        raise ValueError("input must contain exactly three four-connected copies")
    shapes = [_normalize(component) for component in components]
    if len(set(shapes)) != 1:
        raise ValueError("the three components must be identical translated shapes")
    shape = shapes[0]
    origins = {
        (min(row for row, _ in component), min(col for _, col in component))
        for component in components
    }
    origin_rows = sorted({row for row, _ in origins})
    origin_cols = sorted({col for _, col in origins})
    if len(origin_rows) != 2 or len(origin_cols) != 2:
        raise ValueError("component origins must define two rectangle rows and columns")
    top, bottom = origin_rows
    left, right = origin_cols
    if origins != {(top, left), (top, right), (bottom, left)}:
        raise ValueError("copies must occupy top-left, top-right, and bottom-left")
    row_span = bottom - top
    col_span = right - left
    if row_span == col_span:
        raise ValueError("span-directed family excludes square source rectangles")
    shape_height, shape_width = _shape_dims(shape)
    if row_span < shape_height + 1 or col_span < shape_width + 1:
        raise ValueError("source copies must be separated by a blank gap")
    target = (bottom, right)
    for candidate in (shape, _rotate_cw(shape), _rotate_ccw(shape)):
        candidate_height, candidate_width = _shape_dims(candidate)
        if target[0] + candidate_height > len(grid) or target[1] + candidate_width > width:
            raise ValueError("the translated/turned target would leave the grid")
    return {
        "height": len(grid),
        "width": width,
        "color": color,
        "shape": shape,
        "shape_height": shape_height,
        "shape_width": shape_width,
        "shape_cells": len(shape),
        "top": top,
        "left": left,
        "bottom": bottom,
        "right": right,
        "row_span": row_span,
        "col_span": col_span,
        "dominant_span": "horizontal" if col_span > row_span else "vertical",
        "target": target,
        "components": components,
    }


def _shape_for_mode(shape: tuple[tuple[int, int], ...], dominant: str, mode: str):
    if mode == CANONICAL:
        return shape
    if mode == ALTERNATE:
        return _rotate_cw(shape) if dominant == "horizontal" else _rotate_ccw(shape)
    if mode == "always_cw":
        return _rotate_cw(shape)
    if mode == "always_ccw":
        return _rotate_ccw(shape)
    if mode == "reverse_span_turn":
        return _rotate_ccw(shape) if dominant == "horizontal" else _rotate_cw(shape)
    if mode == "always_180":
        return _rotate_180(shape)
    if mode == "wide_only_turn":
        return _rotate_cw(shape) if dominant == "horizontal" else shape
    if mode == "tall_only_turn":
        return shape if dominant == "horizontal" else _rotate_ccw(shape)
    if mode == "turn_large_only":
        return (_rotate_cw(shape) if dominant == "horizontal" else _rotate_ccw(shape)) if len(shape) >= 9 else shape
    if mode == "turn_small_only":
        return (_rotate_cw(shape) if dominant == "horizontal" else _rotate_ccw(shape)) if len(shape) < 9 else shape
    raise ValueError(f"unknown solve mode {mode!r}")


def solve(grid: list[list[int]], mode: str) -> list[list[int]]:
    analysis = analyze_input(grid)
    target_shape = _shape_for_mode(analysis["shape"], analysis["dominant_span"], mode)
    output = deepcopy(grid)
    _paint(output, target_shape, analysis["target"], analysis["color"])
    return output


def _pair(seed: int, split: str, index: int, selected: str) -> dict[str, Any]:
    grid = build_input(seed, split, index)
    return {"input": grid, "output": solve(grid, selected)}


def generate_episode(seed: Any, selected: str, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _validate_seed(seed)
    selected = validate_settings({"completion_transform": selected})
    demos, queries = _validate_counts(demos, queries)
    train = [_pair(seed, "demo", index, selected) for index in range(demos)]
    test = [_pair(seed, "query", index, selected) for index in range(queries)]
    signatures = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(signatures) != len(set(signatures)):
        raise RuntimeError("episode inputs are not distinct")
    return {"train": train, "test": test, "program_solution": program_for(selected)}


def audit_episode(episode: dict[str, Any], selected: str) -> dict[str, Any]:
    selected = validate_settings({"completion_transform": selected})
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train and test lists")
    declared = [
        mode
        for mode in ALLOWED_TRANSFORMS
        if all(solve(pair["input"], mode) == pair["output"] for pair in train)
    ]
    shortcuts = [
        mode
        for mode in DECLARED_SHORTCUTS
        if all(solve(pair["input"], mode) == pair["output"] for pair in train)
    ]
    other = ALTERNATE if selected == CANONICAL else CANONICAL
    query_disagreements = sum(
        solve(pair["input"], other) != pair["output"] for pair in test
    )
    return {
        "selected": selected,
        "surviving_declared_rules": declared,
        "surviving_shortcuts": shortcuts,
        "query_disagreements_against_other_setting": query_disagreements,
        "demonstration_dominant_spans": [analyze_input(pair["input"])["dominant_span"] for pair in train],
    }


def input_metrics(grid: list[list[int]]) -> dict[str, Any]:
    analysis = analyze_input(grid)
    colored = {
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value != 0
    }
    boundary_sides = []
    if any(row == 0 for row, _ in colored):
        boundary_sides.append("top")
    if any(row == len(grid) - 1 for row, _ in colored):
        boundary_sides.append("bottom")
    if any(col == 0 for _, col in colored):
        boundary_sides.append("left")
    if any(col == len(grid[0]) - 1 for _, col in colored):
        boundary_sides.append("right")
    return {
        "height": analysis["height"],
        "width": analysis["width"],
        "shape_cells": analysis["shape_cells"],
        "occupied_cells": len(colored),
        "row_span": analysis["row_span"],
        "col_span": analysis["col_span"],
        "dominant_span": analysis["dominant_span"],
        "boundary_sides": boundary_sides,
    }


def public_turn(episode: dict[str, Any], query_index: Any) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select an existing query; bool is forbidden")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def causal_witness(seed: Any = 0) -> dict[str, Any]:
    seed = _validate_seed(seed)
    grid = build_input(seed, "query", 2)
    analysis = analyze_input(grid)
    correct = solve(grid, ALTERNATE)
    wrong = solve(grid, "reverse_span_turn")
    differing = sum(
        left != right
        for left_row, right_row in zip(correct, wrong, strict=True)
        for left, right in zip(left_row, right_row, strict=True)
    )
    return {
        "step_a": "locate the three source copies and compare their row and column spans",
        "intermediate": analysis["dominant_span"],
        "step_b": "choose clockwise for horizontal or counterclockwise for vertical, then paint the fourth copy",
        "wrong_intermediate": "vertical" if analysis["dominant_span"] == "horizontal" else "horizontal",
        "input": grid,
        "correct_output": correct,
        "wrong_output": wrong,
        "differing_cells": differing,
    }
