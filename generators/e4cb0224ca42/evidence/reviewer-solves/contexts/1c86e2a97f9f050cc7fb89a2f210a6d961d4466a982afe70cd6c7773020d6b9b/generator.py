"""Generator for ARC task ``e4cb0224ca42``.

Each foreground object is a solid monochromatic rectangle whose height and
width are odd.  On a fresh zero canvas, the output keeps the rectangle's full
middle row and full middle column in the original color.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "e4cb0224ca42"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "7798fb9f1ac0"
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Place one to three separated, distinctly colored, solid odd-by-odd "
    "rectangles on a zero background. Replace every rectangle by the union "
    "of its geometric middle row and middle column on a fresh zero canvas."
)

INVARIANTS = [
    "background is 0 and all foreground values are ARC colors 1..9",
    "there are exactly 1..3 four-connected foreground rectangles",
    "every rectangle is solid and has both dimensions in {3,5,7}",
    "rectangle colors are distinct",
    "rectangles have no cardinal contact; diagonal corner contact is lawful",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "keyed draw 7..14", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "keyed draw 9..16", "valid": "9..16"},
    "n_rects": {"type": "int", "default": "keyed draw 1..3", "valid": "1..3"},
}
_ALLOWED_OVERRIDES = frozenset(AXES)
_ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

SCHEDULE_PROFILES = (
    "canonical_7x9",
    "canonical_9x11",
    "canonical_8x10",
    "canonical_test_9x11",
)
_TEMPLATE_LAYOUTS = {
    "canonical_7x9": (7, 9, ((1, 1, 3, 5), (4, 6, 3, 3))),
    "canonical_9x11": (9, 11, ((0, 0, 5, 3), (3, 5, 3, 5))),
    "canonical_8x10": (8, 10, ((0, 6, 5, 3), (2, 1, 3, 3))),
    "canonical_test_9x11": (9, 11, ((1, 2, 5, 5), (5, 8, 3, 3))),
}

COUNTER_HYPOTHESES = [
    "keep only each rectangle center",
    "keep only the middle row",
    "keep only the middle column",
    "transform square rectangles but ignore non-square odd rectangles",
    "transform only the first rectangle in reading order",
]


def _nonnegative_int(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (not bool)")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_scheduled_int(
    ctx,
    label: str,
    lo: int,
    hi: int,
    scheduled: int,
    overrides: dict[str, Any],
) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return int(ctx.draw_choice(label, [scheduled]))


def _quadrant_slots(h: int, w: int) -> list[tuple[int, int, int, int]]:
    """Four disjoint slots separated by a central background row/column."""
    top_h = (h - 1) // 2
    bottom_start = h - top_h
    left_w = (w - 1) // 2
    right_start = w - left_w
    return [
        (0, 0, top_h, left_w),
        (0, right_start, top_h, left_w),
        (bottom_start, 0, top_h, left_w),
        (bottom_start, right_start, top_h, left_w),
    ]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have a nonempty first row"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid cells must be ARC color integers 0..9"]
    return []


def _components4(grid: list[list[int]] | tuple[tuple[int, ...], ...]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            start = (row, col)
            if color == 0 or start in seen:
                continue
            seen.add(start)
            queue = deque([start])
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _ORTHOGONAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            r1, c1, r2, c2 = min(rows), min(cols), max(rows), max(cols)
            result.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "bbox": (r1, c1, r2, c2),
                    "height": r2 - r1 + 1,
                    "width": c2 - c1 + 1,
                }
            )
    result.sort(key=lambda item: item["bbox"])
    return result


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "rects": (), "height": 0, "width": 0}
    height, width = len(grid), len(grid[0])
    rects = _components4(grid)
    if not 1 <= len(rects) <= 3:
        errors.append(f"expected 1..3 foreground rectangles, found {len(rects)}")

    colors = [rect["color"] for rect in rects]
    if len(set(colors)) != len(colors):
        errors.append(f"rectangle colors must be distinct, got {colors}")

    occupied: list[set[tuple[int, int]]] = []
    for index, rect in enumerate(rects):
        r1, c1, r2, c2 = rect["bbox"]
        expected = {
            (row, col)
            for row in range(r1, r2 + 1)
            for col in range(c1, c2 + 1)
        }
        cells = set(rect["cells"])
        occupied.append(cells)
        if cells != expected:
            errors.append(f"rectangle {index} is not a solid filled bbox")
        if rect["height"] not in (3, 5, 7) or rect["width"] not in (3, 5, 7):
            errors.append(
                f"rectangle {index} dimensions must be in {{3,5,7}}, "
                f"got {rect['height']}x{rect['width']}"
            )

    for index, left in enumerate(occupied):
        for other_index in range(index + 1, len(occupied)):
            right = occupied[other_index]
            if any(
                (row + dr, col + dc) in right
                for row, col in left
                for dr, dc in _ORTHOGONAL
            ):
                errors.append(
                    f"rectangles {index} and {other_index} have cardinal contact"
                )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "rects": tuple(rects),
        "n_rects": len(rects),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid: Any) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if not 7 <= analysis["height"] <= 14 or not 9 <= analysis["width"] <= 16:
        errors.append(
            "canonical-like dimensions must be within 7..14 by 9..16, "
            f"got {analysis['height']}x{analysis['width']}"
        )
    return errors


def observe_overrides(grid: Any) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_rects": analysis["n_rects"],
    }


def rule_mirror(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for rect in analysis["rects"]:
        r1, c1, r2, c2 = rect["bbox"]
        middle_row = (r1 + r2) // 2
        middle_col = (c1 + c2) // 2
        for col in range(c1, c2 + 1):
            output[middle_row][col] = rect["color"]
        for row in range(r1, r2 + 1):
            output[row][middle_col] = rect["color"]
    return output


def _cross_rule_filtered(grid: Any, keep) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for rect in analysis["rects"]:
        if not keep(rect):
            continue
        r1, c1, r2, c2 = rect["bbox"]
        middle_row = (r1 + r2) // 2
        middle_col = (c1 + c2) // 2
        for col in range(c1, c2 + 1):
            output[middle_row][col] = rect["color"]
        for row in range(r1, r2 + 1):
            output[row][middle_col] = rect["color"]
    return output


def _rival_center_only(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for rect in analysis["rects"]:
        r1, c1, r2, c2 = rect["bbox"]
        output[(r1 + r2) // 2][(c1 + c2) // 2] = rect["color"]
    return output


def _rival_middle_row_only(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for rect in analysis["rects"]:
        r1, c1, r2, c2 = rect["bbox"]
        middle_row = (r1 + r2) // 2
        for col in range(c1, c2 + 1):
            output[middle_row][col] = rect["color"]
    return output


def _rival_middle_column_only(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for rect in analysis["rects"]:
        r1, c1, r2, c2 = rect["bbox"]
        middle_col = (c1 + c2) // 2
        for row in range(r1, r2 + 1):
            output[row][middle_col] = rect["color"]
    return output


def _rival_squares_only(grid: Any) -> list[list[int]]:
    return _cross_rule_filtered(grid, lambda rect: rect["height"] == rect["width"])


def _rival_first_rectangle_only(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    first_bbox = analysis["rects"][0]["bbox"]
    return _cross_rule_filtered(grid, lambda rect: rect["bbox"] == first_bbox)


SEMANTIC_RIVALS = {
    "center_only": _rival_center_only,
    "middle_row_only": _rival_middle_row_only,
    "middle_column_only": _rival_middle_column_only,
    "squares_only": _rival_squares_only,
    "first_rectangle_only": _rival_first_rectangle_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "center_only": _rival_center_only,
    "squares_only": _rival_squares_only,
    "first_rectangle_only": _rival_first_rectangle_only,
}


def _witness_full_two_axis_cross(grid: Any) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and bool(analysis["rects"])


def _witness_non_square_rectangle(grid: Any) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        rect["height"] != rect["width"] for rect in analysis["rects"]
    )


def _witness_multiple_rectangles(grid: Any) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["n_rects"] >= 2


SEMANTIC_WITNESSES = {
    "full_two_axis_cross": _witness_full_two_axis_cross,
    "non_square_rectangle": _witness_non_square_rectangle,
    "multiple_rectangles": _witness_multiple_rectangles,
}
WITNESS_RIVALS = {
    "full_two_axis_cross": [
        "center_only",
        "middle_row_only",
        "middle_column_only",
    ],
    "non_square_rectangle": ["squares_only"],
    "multiple_rectangles": ["first_rectangle_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output does not match the cross rule")
            continue
        valid_demos.append(pair)

    for name, rival in SEMANTIC_RIVALS.items():
        if valid_demos and all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
            reasons.append(f"rival survives all demonstrations: {name}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        errors = strict_canonical_like(query["input"])
        if errors:
            reasons.append(f"query malformed: {errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the cross rule")
    return reasons


def _reflect_layout(
    height: int,
    width: int,
    layout: tuple[tuple[int, int, int, int], ...],
    *,
    flip_vertical: bool,
    flip_horizontal: bool,
) -> list[tuple[int, int, int, int]]:
    result = []
    for row0, col0, rect_h, rect_w in layout:
        if flip_vertical:
            row0 = height - row0 - rect_h
        if flip_horizontal:
            col0 = width - col0 - rect_w
        result.append((row0, col0, rect_h, rect_w))
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    seed = _nonnegative_int("seed", seed)
    sample_index = _nonnegative_int("sample_index", sample_index)
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _band(difficulty)
    profile = schedule_profile(seed, sample_index, band)
    scheduled_h, scheduled_w, template = _TEMPLATE_LAYOUTS[profile]

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height = _draw_scheduled_int(ctx, "grid_h", 7, 14, scheduled_h, overrides)
    width = _draw_scheduled_int(ctx, "grid_w", 9, 16, scheduled_w, overrides)
    count = _draw_scheduled_int(ctx, "n_rects", 1, 3, 2, overrides)

    grid = full_grid(height, width, 0)
    rng = ctx.draw_rng("layout")
    base_colors = rng.sample(range(1, 10), count)
    color_offset = {"easy": 0, "medium": 3, "hard": 6}[band]
    colors = [((color - 1 + color_offset) % 9) + 1 for color in base_colors]
    has_effective_override = any(value is not None for value in overrides.values())

    if not has_effective_override:
        layout = _reflect_layout(
            height,
            width,
            template,
            flip_vertical=bool(rng.randrange(2)),
            flip_horizontal=bool(rng.randrange(2)),
        )
        for (row0, col0, rect_h, rect_w), color in zip(layout, colors):
            draw_rect(grid, row0, col0, rect_h, rect_w, color)
    else:
        slots = rng.sample(_quadrant_slots(height, width), count)
        for slot, color in zip(slots, colors):
            slot_row, slot_col, slot_h, slot_w = slot
            rect_h = rng.choice([size for size in (3, 5, 7) if size <= slot_h])
            rect_w = rng.choice([size for size in (3, 5, 7) if size <= slot_w])
            row0 = rng.randint(slot_row, slot_row + slot_h - rect_h)
            col0 = rng.randint(slot_col, slot_col + slot_w - rect_w)
            draw_rect(grid, row0, col0, rect_h, rect_w, color)

    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator invariant failure: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"grid_h": height, "grid_w": width, "n_rects": count}
    if observed != expected:
        raise RuntimeError(f"internal axis observation mismatch: {observed} != {expected}")
    return grid
