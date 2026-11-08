#!/usr/bin/env python3
"""Episode-level symmetric-key / successor-object family.

The canonical setting crops the unique object whose bbox-normalized binary
mask is invariant under left/right reflection.  The alternative is genuinely
sequential:

A. identify that unique LR-symmetric object;
I. read its colour;
B. crop the object whose colour is the cyclic successor (9 wraps to 1).

Normal lessons contain four objects and make the key/partner quadrants, colours,
and shapes vary.  Their colour sets contain no other successor pair, so the
relationship is recoverable from as few as two demonstrations.  The final
query is a 30x30 nine-object stress case using every nonzero colour and all four
canvas boundaries; only the symmetry-derived intermediate disambiguates its
many consecutive-colour pairs.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import random
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root

TASK_ID = "edf83166c155"
ALLOWED_MODES = ("symmetric_object", "successor_of_symmetric")
DEFAULT_MODE = "symmetric_object"
ROOT = find_root(__file__)

_SUCCESSOR_PROGRAM = r'''(rule! (let ((dummy 0))
  (define (component-grid obj)
    (let* ((bb (obj-bbox obj))
           (h (+ 1 (- (third bb) (first bb))))
           (w (+ 1 (- (fourth bb) (second bb)))))
      (for/fold ((out (empty-grid h w 0)))
                ((p (in-list (obj-cells obj))))
        (set-cell out
                  (- (first p) (first bb))
                  (- (second p) (second bb))
                  (obj-color obj)))))
  (define (binary-grid grid)
    (grid-from-fn (rows grid) (cols grid)
                  (lambda (r c) (if (= (at grid r c) 0) 0 1))))
  (let* ((objs (objects g 0))
         (key
          (first
           (filter
            (lambda (obj)
              (equal? (binary-grid (component-grid obj))
                      (flip-lr (binary-grid (component-grid obj)))))
            objs)))
         (wanted (if (= (obj-color key) 9) 1 (+ (obj-color key) 1)))
         (hit (first (filter (lambda (obj) (= (obj-color obj) wanted)) objs))))
    (component-grid hit))))'''

# Connected, non-solid, LR-symmetric masks.  Width is always at least three.
_U = ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2))
_T = ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))
_PLUS = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_H = ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2))
_BOWL5 = (
    (0, 0), (0, 4),
    (1, 0), (1, 4),
    (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
)
_DIAMOND5 = (
    (0, 2),
    (1, 1), (1, 2), (1, 3),
    (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
    (3, 2),
)
_SYMMETRIC_SHAPES = (_U, _T, _PLUS, _H, _BOWL5, _DIAMOND5)

# Connected masks that are deliberately not LR-symmetric.
_L4_TALL = ((0, 0), (1, 0), (2, 0), (2, 1))
_J4_WIDE = ((0, 0), (0, 1), (0, 2), (1, 0))
_S4_WIDE = ((0, 0), (0, 1), (1, 1), (1, 2))
_Z5_DIAG = ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2))
_STAIR5 = ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2))
_ASYM6 = ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2))
_ROT180_ONLY = ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3))
_UD_ONLY = (
    (0, 0), (0, 1), (0, 3),
    (1, 0), (1, 1), (1, 2), (1, 3),
    (2, 0), (2, 1), (2, 3),
)
_ASYMMETRIC_SHAPES = (
    _L4_TALL,
    _J4_WIDE,
    _S4_WIDE,
    _Z5_DIAG,
    _STAIR5,
    _ASYM6,
    _ROT180_ONLY,
    _UD_ONLY,
)

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_mode(output_mode: str) -> None:
    if type(output_mode) is not str or output_mode not in ALLOWED_MODES:
        raise ValueError(f"output_mode must be one of {ALLOWED_MODES}, got {output_mode!r}")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def canonical_source(*, root: Path = ROOT) -> str:
    sources: set[str] = set()
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            source = row.get("program_solution")
            if isinstance(source, str) and source.strip():
                sources.add(source)
    if len(sources) != 1:
        raise ValueError(f"expected one canonical source for {TASK_ID}, found {len(sources)}")
    return next(iter(sources))


def program_for(output_mode: str, *, root: Path = ROOT) -> str:
    _validate_mode(output_mode)
    return canonical_source(root=root) if output_mode == DEFAULT_MODE else _SUCCESSOR_PROGRAM


def _rng(seed: int, index: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{index}:{label}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _dimensions(seed: int, index: int) -> tuple[int, int]:
    return 14 + ((seed + 2 * index) % 5), 16 + ((3 * seed + index) % 5)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    normalized = _normalize(shape)
    if not normalized:
        raise ValueError("shape must contain at least one cell")
    return max(r for r, _ in normalized) + 1, max(c for _, c in normalized) + 1


def _is_lr_symmetric(shape: Iterable[tuple[int, int]]) -> bool:
    normalized = _normalize(shape)
    if not normalized:
        return False
    _, width = _shape_dims(normalized)
    reflected = tuple(sorted((row, width - 1 - col) for row, col in normalized))
    return normalized == reflected


def _connected4(shape: Iterable[tuple[int, int]]) -> bool:
    cells = set(shape)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for drow, dcol in _DIR4:
            neighbor = (row + drow, col + dcol)
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == cells


def successor_color(color: int) -> int:
    if type(color) is not int or not 1 <= color <= 9:
        raise ValueError("color must be an exact integer in 1..9")
    return 1 if color == 9 else color + 1


def components(grid: list[list[int]]) -> list[dict[str, Any]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            start = (start_row, start_col)
            if color == 0 or start in seen:
                continue
            stack = [start]
            seen.add(start)
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in _DIR4:
                    neighbor = (row + drow, col + dcol)
                    nrow, ncol = neighbor
                    if (
                        0 <= nrow < height
                        and 0 <= ncol < width
                        and neighbor not in seen
                        and grid[nrow][ncol] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            normalized = _normalize(cells)
            bbox_h, bbox_w = _shape_dims(normalized)
            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "norm": normalized,
                    "top": top,
                    "left": left,
                    "bottom": max(r for r, _ in cells),
                    "right": max(c for _, c in cells),
                    "bbox_h": bbox_h,
                    "bbox_w": bbox_w,
                    "area": len(cells),
                    "lr": _is_lr_symmetric(normalized),
                }
            )
    return sorted(result, key=lambda component: (component["top"], component["left"]))


def crop_component(grid: list[list[int]], component: dict[str, Any]) -> list[list[int]]:
    output = [
        [0 for _ in range(component["bbox_w"])]
        for _ in range(component["bbox_h"])
    ]
    for row, col in component["cells"]:
        output[row - component["top"]][col - component["left"]] = component["color"]
    return output


def find_symmetric_component(grid: list[list[int]]) -> dict[str, Any]:
    hits = [component for component in components(grid) if component["lr"]]
    if len(hits) != 1:
        raise ValueError(f"expected one LR-symmetric object, found {len(hits)}")
    return hits[0]


def find_successor_component(
    grid: list[list[int]], key: dict[str, Any] | None = None
) -> dict[str, Any]:
    key = find_symmetric_component(grid) if key is None else key
    wanted = successor_color(key["color"])
    hits = [component for component in components(grid) if component["color"] == wanted]
    if len(hits) != 1:
        raise ValueError(f"expected one successor-colour object, found {len(hits)}")
    return hits[0]


def _choose_normal_decoy_colors(key_color: int, count: int, rng: random.Random) -> list[int]:
    partner_color = successor_color(key_color)
    candidates = [c for c in range(1, 10) if c not in {key_color, partner_color}]
    valid: list[tuple[int, ...]] = []
    for combo in itertools.combinations(candidates, count):
        present = {key_color, partner_color, *combo}
        extra_pairs = [
            color
            for color in present
            if successor_color(color) in present and color != key_color
        ]
        if not extra_pairs:
            valid.append(combo)
    if not valid:
        raise AssertionError("could not choose relation-clean decoy colours")
    return list(valid[rng.randrange(len(valid))])


def _paint(
    grid: list[list[int]],
    top: int,
    left: int,
    shape: Iterable[tuple[int, int]],
    color: int,
) -> None:
    for row, col in shape:
        if grid[top + row][left + col] != 0:
            raise AssertionError("object placement collision")
        grid[top + row][left + col] = color


def _normal_regions(height: int, width: int) -> list[tuple[int, int, int, int]]:
    mid_row, mid_col = height // 2, width // 2
    return [
        (0, mid_row, 0, mid_col),
        (0, mid_row, mid_col, width),
        (mid_row, height, 0, mid_col),
        (mid_row, height, mid_col, width),
    ]


def _place_in_region(
    grid: list[list[int]],
    region: tuple[int, int, int, int],
    shape: tuple[tuple[int, int], ...],
    color: int,
    rng: random.Random,
) -> None:
    row0, row1, col0, col1 = region
    shape_h, shape_w = _shape_dims(shape)
    min_top, max_top = row0 + 1, row1 - shape_h - 1
    min_left, max_left = col0 + 1, col1 - shape_w - 1
    if min_top > max_top or min_left > max_left:
        raise ValueError("shape does not fit its isolated region")
    # Share a deterministic row anchor inside each horizontal band so the
    # left slot is always first in reading order.  Horizontal jitter remains,
    # while a top-right object can no longer become an accidental "first
    # object" merely because its independent vertical jitter was smaller.
    top = min_top
    left = rng.randint(min_left, max_left)
    _paint(grid, top, left, shape, color)


def _make_normal_input(seed: int, index: int, height: int, width: int) -> list[list[int]]:
    if height < 14 or width < 16:
        raise ValueError("normal scenes require at least 14x16")
    rng = _rng(seed, index, "normal-layout")
    key_color = 1 + ((seed + 2 * index) % 9)
    partner_color = successor_color(key_color)
    decoy_colors = _choose_normal_decoy_colors(key_color, 2, rng)

    key_shape = _SYMMETRIC_SHAPES[(seed + index) % len(_SYMMETRIC_SHAPES)]
    asym_order = list(_ASYMMETRIC_SHAPES)
    rng.shuffle(asym_order)
    partner_shape, decoy_shape_a, decoy_shape_b = asym_order[:3]

    key_slot = index % 4
    partner_slot = (index + 2 + ((index // 4) % 2)) % 4
    if partner_slot == key_slot:
        raise AssertionError("key and partner slots must differ")
    remaining_slots = [slot for slot in range(4) if slot not in {key_slot, partner_slot}]
    slot_payloads = {
        key_slot: (key_shape, key_color),
        partner_slot: (partner_shape, partner_color),
        remaining_slots[0]: (decoy_shape_a, decoy_colors[0]),
        remaining_slots[1]: (decoy_shape_b, decoy_colors[1]),
    }

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for slot, region in enumerate(_normal_regions(height, width)):
        shape, color = slot_payloads[slot]
        _place_in_region(grid, region, shape, color, rng)
    return grid


def _stress_regions() -> list[tuple[int, int, int, int]]:
    return [
        (row * 10, (row + 1) * 10, col * 10, (col + 1) * 10)
        for row in range(3)
        for col in range(3)
    ]


def _place_stress(
    grid: list[list[int]],
    slot: int,
    shape: tuple[tuple[int, int], ...],
    color: int,
) -> None:
    row0, row1, col0, col1 = _stress_regions()[slot]
    shape_h, shape_w = _shape_dims(shape)
    slot_row, slot_col = divmod(slot, 3)
    if slot_row == 0:
        top = row0
    elif slot_row == 2:
        top = row1 - shape_h
    else:
        top = row0 + (10 - shape_h) // 2
    if slot_col == 0:
        left = col0
    elif slot_col == 2:
        left = col1 - shape_w
    else:
        left = col0 + (10 - shape_w) // 2
    _paint(grid, top, left, shape, color)


def _make_stress_input(seed: int, index: int) -> list[list[int]]:
    rng = _rng(seed, index, "stress-layout")
    key_color = 1 + ((seed + 2 * index) % 9)
    partner_color = successor_color(key_color)
    key_shape = _SYMMETRIC_SHAPES[(seed + index) % len(_SYMMETRIC_SHAPES)]
    asym_shapes = list(_ASYMMETRIC_SHAPES)
    shift = (seed + index) % len(asym_shapes)
    asym_shapes = asym_shapes[shift:] + asym_shapes[:shift]

    key_slot = (seed + index) % 9
    partner_slot = (key_slot + 4 + (index % 2)) % 9
    if partner_slot == key_slot:
        partner_slot = (partner_slot + 1) % 9
    remaining_slots = [slot for slot in range(9) if slot not in {key_slot, partner_slot}]
    remaining_colors = [c for c in range(1, 10) if c not in {key_color, partner_color}]
    rng.shuffle(remaining_colors)

    payloads: dict[int, tuple[tuple[tuple[int, int], ...], int]] = {
        key_slot: (key_shape, key_color),
        partner_slot: (asym_shapes[0], partner_color),
    }
    for position, slot in enumerate(remaining_slots):
        payloads[slot] = (asym_shapes[position + 1], remaining_colors[position])

    grid = [[0 for _ in range(30)] for _ in range(30)]
    for slot in range(9):
        shape, color = payloads[slot]
        _place_stress(grid, slot, shape, color)
    return grid


def _validate_constructed(grid: list[list[int]], *, expected_objects: int) -> None:
    found = components(grid)
    if len(found) != expected_objects:
        raise AssertionError(f"expected {expected_objects} objects, found {len(found)}")
    if len({component["color"] for component in found}) != expected_objects:
        raise AssertionError("constructed object colours are not unique")
    if sum(component["lr"] for component in found) != 1:
        raise AssertionError("constructed scene lost unique LR symmetry")
    key = find_symmetric_component(grid)
    find_successor_component(grid, key)
    if python_mirror(grid, output_mode=DEFAULT_MODE) == python_mirror(
        grid, output_mode="successor_of_symmetric"
    ):
        raise AssertionError("declared settings do not disagree")


def make_input(
    seed: int,
    index: int,
    *,
    height: int | None = None,
    width: int | None = None,
) -> list[list[int]]:
    _validate_seed(seed)
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")
    if height is None or width is None:
        default_h, default_w = _dimensions(seed, index)
        height = default_h if height is None else height
        width = default_w if width is None else width
    if type(height) is not int or type(width) is not int:
        raise ValueError("height and width must be exact integers")
    if (height, width) == (30, 30):
        grid = _make_stress_input(seed, index)
        _validate_constructed(grid, expected_objects=9)
        return grid
    if not 14 <= height <= 29 or not 16 <= width <= 29:
        raise ValueError("normal height must be 14..29 and width must be 16..29")
    grid = _make_normal_input(seed, index, height, width)
    _validate_constructed(grid, expected_objects=4)
    return grid


def python_mirror(grid: list[list[int]], *, output_mode: str) -> list[list[int]]:
    _validate_mode(output_mode)
    key = find_symmetric_component(grid)
    selected = key if output_mode == DEFAULT_MODE else find_successor_component(grid, key)
    return crop_component(grid, selected)


def execute_rule(program: str, grid: list[list[int]], *, bridge: RacketBridge) -> list[list[int]]:
    wrapped = wrap_rule(program)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrapped} {literal})")


def make_episode(
    seed: int,
    *,
    output_mode: str,
    demos: int = 2,
    queries: int = 4,
    root: Path = ROOT,
) -> dict[str, Any]:
    _validate_seed(seed)
    _validate_mode(output_mode)
    _validate_counts(demos, queries)
    pairs: list[dict[str, list[list[int]]]] = []
    total = demos + queries
    for index in range(total):
        if index == total - 1:
            grid = make_input(seed, index, height=30, width=30)
        else:
            height, width = _dimensions(seed, index)
            grid = make_input(seed, index, height=height, width=width)
        pairs.append({"input": grid, "output": python_mirror(grid, output_mode=output_mode)})
    return {
        "task_id": TASK_ID,
        "parameters": {"output_mode": output_mode},
        "selection_scope": "once_per_episode",
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program": program_for(output_mode, root=root),
    }


def generate_claims(
    seed: int,
    *,
    output_mode: str,
    demos: int = 2,
    queries: int = 4,
    root: Path = ROOT,
) -> dict[str, Any]:
    episode = make_episode(
        seed,
        output_mode=output_mode,
        demos=demos,
        queries=queries,
        root=root,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program"],
    }


# Fail fast if a future edit accidentally changes the promised morphology bank.
assert all(_connected4(shape) and _is_lr_symmetric(shape) for shape in _SYMMETRIC_SHAPES)
assert all(_connected4(shape) and not _is_lr_symmetric(shape) for shape in _ASYMMETRIC_SHAPES)
