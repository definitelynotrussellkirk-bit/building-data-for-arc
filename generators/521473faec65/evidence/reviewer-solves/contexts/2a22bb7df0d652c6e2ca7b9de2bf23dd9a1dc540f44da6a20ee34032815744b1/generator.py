"""Generator for ARC task 521473faec65 (checkerboard every solid rectangle).

Each lawful input contains two or three separated, solid, monochrome rectangles
on a black background.  The output keeps the rectangle colour on cells whose
row-plus-column offset from that rectangle's own top-left corner is even and
clears the alternating cells to black.

The four-step teaching schedule alternates two semantic distinctions:

* two versus three rectangles, so a "transform only the first two" shortcut
  cannot survive any three-demo leave-one-out rotation; and
* even versus odd top-left anchors, so a checkerboard tied to the global origin
  cannot survive any three-demo leave-one-out rotation.

Public overrides are intentionally small and exact: grid height, grid width,
and rectangle count are all directly recoverable from returned pixels.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "521473faec65"
TASK_ID = "521473faec65"
VERSION = "3.1.0"
RULE_HASH = "4409288b0253"

SUMMARY = (
    "A black grid contains two or three separated solid monochrome rectangles "
    "in distinct nonzero colours. For each rectangle independently, start a "
    "checkerboard at its own top-left cell: retain the rectangle colour where "
    "(row - top + column - left) is even and clear the alternating cells to 0. "
    "A four-sample teaching schedule alternates two/three rectangles and "
    "even/odd rectangle anchors to rule out first-two-only and global-origin "
    "checkerboard shortcuts."
)

INVARIANTS = [
    "two or three solid monochrome rectangles",
    "rectangle colours are distinct and nonzero",
    "every rectangle is at least 2x2",
    "rectangle bounding boxes have at least one blank row or column between them",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled/rng 6..12", "valid": "6..12"},
    "grid_w": {"type": "int", "default": "scheduled/rng 8..14", "valid": "8..14"},
    "n_rects": {"type": "int", "default": "sample_index schedule", "valid": "2..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "three_odd_anchor",
    "two_even_anchor",
    "three_even_anchor",
    "two_odd_anchor",
)
_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
EXAMPLES_NEEDED = 3

# Preserve a substantial public-like size component without replaying any
# canonical layout.  The remaining schedule slots range over the full domain.
_CANONICAL_SHAPES = ((7, 9), (8, 8), (6, 10), (8, 10))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic semantic profile for ``sample_index``."""
    del seed, difficulty
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    return SCHEDULE_PROFILES[sample_index % _SCHEDULE_PERIOD]


def _validate_call(seed, sample_index, difficulty, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, easy, medium, hard")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    bounds = {"grid_h": (6, 12), "grid_w": (8, 14), "n_rects": (2, 3)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override must be in {lo}..{hi}")


def _scheduled_overrides(sample_index: int, overrides: dict[str, Any]) -> dict[str, Any]:
    """Apply semantic and canonical-size anchors, then caller overrides."""
    profile = SCHEDULE_PROFILES[sample_index % _SCHEDULE_PERIOD]
    default_count = 3 if profile.startswith("three_") else 2
    scheduled: dict[str, Any] = {"n_rects": default_count}
    # Every default two-rectangle lesson has a canonical (height, width,
    # palette-size) profile.  Three-rectangle lessons retain the full size
    # range, so this anchor is substantial without collapsing broad support.
    if default_count == 2:
        shape_slot = (sample_index // 2) % len(_CANONICAL_SHAPES)
        scheduled["grid_h"], scheduled["grid_w"] = _CANONICAL_SHAPES[shape_slot]
    scheduled.update({name: value for name, value in overrides.items() if value is not None})
    return scheduled


def _padded_separated(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    """True when the boxes have at least one complete blank row or column."""
    ar1, ac1, ar2, ac2 = a
    br1, bc1, br2, bc2 = b
    return (
        ar2 + 1 < br1
        or br2 + 1 < ar1
        or ac2 + 1 < bc1
        or bc2 + 1 < ac1
    )


def _partition_slots(length: int, count: int, rng) -> list[tuple[int, int]]:
    """Partition one axis into ``count`` >=2-cell slots separated by gaps."""
    minimum = 2 * count + (count - 1)
    if length < minimum:
        raise ValueError(f"axis length {length} cannot fit {count} separated rectangles")

    # Buckets are: left margin, each slot's extra width, each gap's extra width,
    # and right margin.  Randomly distributing every spare cell gives varied
    # sizes and offsets while preserving feasibility by construction.
    extras = [0] * (2 * count + 1)
    for _ in range(length - minimum):
        extras[rng.randrange(len(extras))] += 1

    left_margin = extras[0]
    slot_extras = extras[1 : count + 1]
    gap_extras = extras[count + 1 : 2 * count]
    position = left_margin
    slots: list[tuple[int, int]] = []
    for index in range(count):
        slot_length = 2 + slot_extras[index]
        slots.append((position, position + slot_length - 1))
        position += slot_length
        if index < count - 1:
            position += 1 + gap_extras[index]
    return slots


def _candidate_boxes(
    height: int,
    width: int,
    orientation: str,
    slot: tuple[int, int],
) -> list[tuple[int, int, int, int]]:
    """Enumerate all 2..5 sided rectangles contained in one separated slot."""
    boxes: list[tuple[int, int, int, int]] = []
    if orientation == "horizontal":
        col_lo, col_hi = slot
        for rect_h in range(2, min(5, height) + 1):
            for rect_w in range(2, min(5, col_hi - col_lo + 1) + 1):
                for row1 in range(0, height - rect_h + 1):
                    for col1 in range(col_lo, col_hi - rect_w + 2):
                        boxes.append((row1, col1, row1 + rect_h - 1, col1 + rect_w - 1))
    elif orientation == "vertical":
        row_lo, row_hi = slot
        for rect_h in range(2, min(5, row_hi - row_lo + 1) + 1):
            for rect_w in range(2, min(5, width) + 1):
                for row1 in range(row_lo, row_hi - rect_h + 2):
                    for col1 in range(0, width - rect_w + 1):
                        boxes.append((row1, col1, row1 + rect_h - 1, col1 + rect_w - 1))
    else:  # pragma: no cover - internal assertion guard
        raise ValueError(f"unknown orientation {orientation!r}")
    return boxes


def _touches_border(box: tuple[int, int, int, int], height: int, width: int) -> bool:
    row1, col1, row2, col2 = box
    return row1 == 0 or col1 == 0 or row2 == height - 1 or col2 == width - 1


def _choose_boxes(ctx, height: int, width: int, count: int, desired_parity: int):
    feasible_orientations = ["horizontal"]
    if height >= 3 * count - 1:
        feasible_orientations.append("vertical")
    band_key = ctx.difficulty or "default"
    if ctx.difficulty == "easy":
        orientation = "horizontal"
    elif ctx.difficulty == "hard" and "vertical" in feasible_orientations:
        orientation = "vertical"
    else:
        orientation = ctx.draw_rng(f"slot_orientation:{band_key}").choice(feasible_orientations)
    primary_length = width if orientation == "horizontal" else height
    slots = _partition_slots(
        primary_length,
        count,
        ctx.draw_rng(f"slot_partition:{band_key}"),
    )

    boxes: list[tuple[int, int, int, int]] = []
    for index, slot in enumerate(slots):
        candidates = _candidate_boxes(height, width, orientation, slot)
        if index == 0:
            candidates = [box for box in candidates if (box[0] + box[1]) % 2 == desired_parity]
        if not candidates:
            raise AssertionError("constructive slot unexpectedly lacks a legal rectangle")

        # Deterministically alternate a border/interior preference.  If a tiny
        # slot cannot realize the preference, fall back to the full legal set.
        want_border = (ctx.sample_index + index) % 3 == 0
        preferred = [
            box for box in candidates
            if _touches_border(box, height, width) == want_border
        ]
        pool = preferred or candidates
        boxes.append(ctx.draw_rng(f"rectangle_{index}:{band_key}").choice(pool))
    return boxes


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    scheduled = _scheduled_overrides(sample_index, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=scheduled,
    )

    height = ctx.draw_int_strict("grid_h", 6, 12)
    width = ctx.draw_int_strict("grid_w", 8, 14)
    count = ctx.draw_int_strict("n_rects", 2, 3)
    profile = schedule_profile(seed, sample_index, difficulty)
    desired_parity = 1 if profile.endswith("odd_anchor") else 0

    boxes = _choose_boxes(ctx, height, width, count, desired_parity)
    colors = ctx.draw_distinct_colors("rectangle_colors", n=count, exclude={0})
    grid = full_grid(height, width, 0)
    for box, color in zip(boxes, colors):
        row1, col1, row2, col2 = box
        draw_rect(grid, row1, col1, row2 - row1 + 1, col2 - col1 + 1, color)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    expected = {"grid_h": height, "grid_w": width, "n_rects": count}
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(f"axis realization mismatch: expected {expected}, observed {observed}")
    if (boxes[0][0] + boxes[0][1]) % 2 != desired_parity:
        raise AssertionError("scheduled anchor parity was not realized")
    return grid


def _same_color_components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for delta_row, delta_col in _CARDINAL:
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    point = (next_row, next_col)
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and point not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add(point)
                        queue.append(point)
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "box": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def _analyze(grid) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {
        "errors": errors,
        "height": 0,
        "width": 0,
        "components": [],
    }
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("grid must be a nonempty sequence of rows")
        return result
    if any(not isinstance(row, (list, tuple)) for row in grid):
        errors.append("every row must be a list or tuple")
        return result
    if not grid[0]:
        errors.append("grid rows must be nonempty")
        return result
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return result

    height = len(grid)
    result["height"], result["width"] = height, width
    if not 6 <= height <= 12:
        errors.append(f"height {height} is outside 6..12")
    if not 8 <= width <= 14:
        errors.append(f"width {width} is outside 8..14")

    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int:
                errors.append(f"cell ({row_index},{col_index}) must be an integer color")
                return result
            if not 0 <= value <= 9:
                errors.append(f"cell ({row_index},{col_index}) has color {value} outside 0..9")
                return result

    components = _same_color_components(grid)
    result["components"] = components
    if not 2 <= len(components) <= 3:
        errors.append(f"expected two or three rectangles, got {len(components)} components")

    colors = [component["color"] for component in components]
    if len(set(colors)) != len(colors):
        errors.append("rectangle colors must be pairwise distinct")

    boxes: list[tuple[int, int, int, int]] = []
    for index, component in enumerate(components):
        row1, col1, row2, col2 = component["box"]
        rect_h, rect_w = row2 - row1 + 1, col2 - col1 + 1
        if rect_h < 2 or rect_w < 2:
            errors.append(f"rectangle {index} must be at least 2x2")
        color = component["color"]
        if any(
            grid[row][col] != color
            for row in range(row1, row2 + 1)
            for col in range(col1, col2 + 1)
        ):
            errors.append(f"component {index} is not a solid filled rectangle")
        boxes.append(component["box"])

    for left in range(len(boxes)):
        for right in range(left + 1, len(boxes)):
            if not _padded_separated(boxes[left], boxes[right]):
                errors.append(
                    f"rectangles {left} and {right} need at least one blank row or column between them"
                )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Accept the declared broad grammar, including every canonical input."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every public exact axis from returned pixels."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_rects": len(analysis["components"]),
    }


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    components = analysis["components"]
    return {
        **observe_overrides(grid),
        "rectangle_dimensions": sorted(
            (box[2] - box[0] + 1, box[3] - box[1] + 1)
            for box in (component["box"] for component in components)
        ),
        "anchor_parities": sorted(
            (component["box"][0] + component["box"][1]) % 2
            for component in components
        ),
        "border_rectangles": sum(
            _touches_border(component["box"], analysis["height"], analysis["width"])
            for component in components
        ),
    }


def _render_components(grid, components) -> list[list[int]]:
    output = full_grid(len(grid), len(grid[0]), 0)
    for component in components:
        row1, col1, row2, col2 = component["box"]
        color = component["color"]
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                if (row - row1 + col - col1) % 2 == 0:
                    output[row][col] = color
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python test mirror; the selected Racket source remains authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _render_components(grid, analysis["components"])


def _rival_first_two_rectangles_only(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _render_components(grid, analysis["components"][:2])


def _rival_absolute_even_checkerboard(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["components"]:
        row1, col1, row2, col2 = component["box"]
        color = component["color"]
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                if (row + col) % 2 == 0:
                    output[row][col] = color
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "first_two_rectangles_only": _rival_first_two_rectangles_only,
    "absolute_even_checkerboard": _rival_absolute_even_checkerboard,
}
CANONICAL_SHORTCUTS = {
    "first_two_rectangles_only": _rival_first_two_rectangles_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _lawful_analysis(grid):
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _rival_differs(grid, rival_name: str) -> bool:
    try:
        return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


def _witness_third_rectangle(grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(
        analysis is not None
        and len(analysis["components"]) == 3
        and _rival_differs(grid, "first_two_rectangles_only")
    )


def _witness_odd_anchor(grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(
        analysis is not None
        and any((component["box"][0] + component["box"][1]) % 2 for component in analysis["components"])
        and _rival_differs(grid, "absolute_even_checkerboard")
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "third_rectangle_transformed": _witness_third_rectangle,
    "local_phase_from_odd_anchor": _witness_odd_anchor,
}
WITNESS_RIVALS = {
    "third_rectangle_transformed": ["first_two_rectangles_only"],
    "local_phase_from_odd_anchor": ["absolute_even_checkerboard"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """A valid three-demo lesson must falsify every declared rival program."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]

    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(demo["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with local checkerboarding")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        try:
            expected_query = rule_mirror(query["input"])
            if query.get("output") is not None and query["output"] != expected_query:
                reasons.append("query output disagrees with local checkerboarding")
        except (TypeError, ValueError) as exc:
            reasons.append(f"query is outside the task grammar: {exc}")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"competitor {name!r} fits every demonstration")
        except Exception as exc:  # pragma: no cover - defensive contract reporting
            reasons.append(f"competitor {name!r} errored: {type(exc).__name__}: {exc}")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local malformed inputs for structural and reviewer probes."""
    valid = generate(99173, 1, difficulty="medium")
    fixtures: list[tuple[str, list[list[int]]]] = []

    hole = [row[:] for row in valid]
    first = _analyze(hole)["components"][0]
    row1, col1, row2, col2 = first["box"]
    hole[(row1 + row2) // 2][(col1 + col2) // 2] = 0
    fixtures.append(("rectangle_hole", hole))

    touching = full_grid(6, 8, 0)
    draw_rect(touching, 0, 0, 2, 2, 2)
    draw_rect(touching, 0, 2, 2, 2, 3)
    fixtures.append(("touching_rectangles", touching))

    bad_color = [row[:] for row in valid]
    bad_color[0][0] = 10
    fixtures.append(("color_out_of_range", bad_color))
    return fixtures
