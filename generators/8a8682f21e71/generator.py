"""Semantic generator for ARC task 8a8682f21e71.

The input is a horizontal row of three or four equal-width framed boxes.  Each
box contains the same connected marker at the same horizontal offset.  Marker
tops form an arithmetic progression.  The output is one fresh framed box with
the marker extrapolated one step farther.  The canonical rule inserts one
additional blank row only when the positive step is taller than the marker.

The schedule deliberately covers all canonical step/shape branches in every
five consecutive examples, including upward motion, positive gap adjustment,
the equal-height no-adjust case, two-color border/marker aliasing, and
canonical-scale 16-row anchors.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a8682f21e71"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "62f8e51d2975"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Three or four equal-width boxes are separated by full-height border "
    "columns.  The same connected marker appears at one shared horizontal "
    "offset while its top row advances by a constant signed step.  Output one "
    "new framed box and extrapolate the marker one more step; add one extra "
    "blank row only when the positive step exceeds the marker height."
)

INVARIANTS = [
    "top, bottom, and every separator column use one nonzero border color",
    "three or four box interiors have equal width four or five",
    "every box contains the same connected marker shape at the same horizontal offset",
    "marker top rows form one nonzero arithmetic progression in {-3, -2, -1, 1, 2, 3}",
    "the box color differs from the marker; the marker may equal the border as in canonical data",
    "the extrapolated marker fits completely inside the fresh output box",
]

MARKER_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "line2": ((0, 0), (0, 1)),
    "square2": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "tee": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "cup": ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
}
SHAPE_BY_CELLS = {cells: name for name, cells in MARKER_SHAPES.items()}

STEP_VALUES = {
    "up3": -3,
    "down1": 1,
    "down2": 2,
    "down3": 3,
}
STEP_BY_VALUE = {value: name for name, value in STEP_VALUES.items()}

# Five consecutive samples cover every decisive canonical branch.  Because the
# lesson builder uses consecutive sample indices, every sliding five-example
# window sees all five profiles regardless of its start residue.
_PROFILE_SPECS = (
    ("down1_line_canonical", "down1", "line2", "canonical"),
    ("down2_line_gap", "down2", "line2", "right"),
    ("down2_tee_no_gap", "down2", "tee", "left"),
    ("down3_square_gap", "down3", "square2", "right"),
    ("up3_cup", "up3", "cup", "left"),
)
SCHEDULE_PROFILES = tuple(spec[0] for spec in _PROFILE_SPECS)

AXES = {
    "box_w": {
        "type": "int",
        "default": "canonical anchor varies 4..5; branch profiles pin 5",
        "valid": "4..5",
    },
    "n_boxes": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "3..4",
    },
    "step": {
        "type": "str",
        "default": "five-sample canonical branch schedule",
        "valid": "up3|down1|down2|down3",
    },
    "marker_shape": {
        "type": "str",
        "default": "five-sample canonical shape schedule",
        "valid": "line2|square2|tee|cup",
    },
    "palette_size": {
        "type": "int",
        "default": "keyed 2..3; the canonical no-gap anchor pins 3",
        "valid": "2..3",
    },
}

# Dynamic height construction makes the full Cartesian override domain lawful.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")


def _shape_dims(cells: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return (
        max(row for row, _ in cells) + 1,
        max(col for _, col in cells) + 1,
    )


def _adjust(step: int, marker_h: int) -> int:
    """The exact canonical asymmetry: only sufficiently large positive steps gap."""
    return 1 if step > marker_h else 0


def _top_offsets(n_boxes: int, step: int, marker_h: int) -> list[int]:
    return [index * step for index in range(n_boxes)] + [
        n_boxes * step + _adjust(step, marker_h)
    ]


def _minimum_height(n_boxes: int, step: int, marker_h: int) -> int:
    offsets = _top_offsets(n_boxes, step, marker_h)
    # The first marker starts at row >=2 so canonical box-color sampling at
    # input[1][1] can never be occluded.  Every input/output marker must remain
    # inside rows 1..h-2.
    start_lo = max(2, 1 - min(offsets))
    return start_lo + max(offsets) + marker_h + 1


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], scheduled: str, overrides):
    if overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=dict(overrides),
    )

    profile_index = sample_index % len(_PROFILE_SPECS)
    _profile_name, scheduled_step, scheduled_shape, offset_mode = _PROFILE_SPECS[
        profile_index
    ]

    if overrides.get("box_w") is not None or profile_index == 0:
        box_w = ctx.draw_int_diff("box_w", 4, 5)
    else:
        # Non-line marker profiles need width five to remain detached from
        # separators; the offset-control profiles also need the sole lawful
        # noncanonical detached offset (relative column two).
        box_w = ctx.draw_int("box_w", 5, 5)
    n_boxes = ctx.draw_int_diff("n_boxes", 3, 4)
    step_name = _scheduled_choice(
        ctx, "step", tuple(STEP_VALUES), scheduled_step, overrides
    )
    shape_name = _scheduled_choice(
        ctx, "marker_shape", tuple(MARKER_SHAPES), scheduled_shape, overrides
    )
    if overrides.get("palette_size") is not None or profile_index != 2:
        palette_size = ctx.draw_int_diff("palette_size", 2, 3)
    else:
        # The no-gap control is also a regular canonical-profile anchor.
        palette_size = ctx.draw_int("palette_size", 3, 3)

    step = STEP_VALUES[step_name]
    marker_cells = MARKER_SHAPES[shape_name]
    marker_h, marker_w = _shape_dims(marker_cells)
    if marker_w > box_w:  # Defensive; the declared Cartesian domain fits.
        raise ValueError(
            f"marker_shape {shape_name!r} width {marker_w} exceeds box_w={box_w}"
        )

    minimum_h = _minimum_height(n_boxes, step, marker_h)
    if profile_index in (0, 2) and minimum_h <= 16:
        # Two guaranteed canonical-scale anchors keep the profile floor
        # count-backed rather than probabilistic, while explicit overrides
        # that need a taller lawful canvas still remain supported.
        height = ctx.draw_int("grid_h_internal", 16, 16)
    else:
        profile_floor = 16 + min(profile_index, 3)
        lo = max(minimum_h, profile_floor)
        extra = {"easy": 1, "medium": 3, "hard": 5}.get(difficulty, 3)
        height = ctx.draw_int_diff("grid_h_internal", lo, min(24, lo + extra))

    offsets = _top_offsets(n_boxes, step, marker_h)
    start_lo = max(2, 1 - min(offsets))
    start_hi = height - marker_h - 1 - max(offsets)
    if start_hi < start_lo:
        raise RuntimeError(
            f"no legal marker start: h={height}, boxes={n_boxes}, "
            f"step={step}, marker_h={marker_h}"
        )
    start_top = ctx.draw_int("start_top_internal", start_lo, start_hi)

    max_left = box_w - marker_w
    detached_lo = 1
    detached_hi = box_w - marker_w - 1
    if detached_hi < detached_lo:
        marker_left = min(1, max_left)
    elif offset_mode == "right":
        marker_left = detached_hi
    else:
        # Both the canonical and "left" profiles use the leftmost detached
        # placement.  This keeps marker components separate from the frame.
        marker_left = detached_lo

    colors = ctx.draw_distinct_colors("colors_internal", n=palette_size, exclude={0})
    border_color, box_color = colors[:2]
    marker_color = border_color if palette_size == 2 else colors[2]

    width = n_boxes * (box_w + 1) + 1
    grid = full_grid(height, width, box_color)
    border_columns = [index * (box_w + 1) for index in range(n_boxes + 1)]

    for col in range(width):
        grid[0][col] = border_color
        grid[height - 1][col] = border_color
    for col in border_columns:
        for row in range(height):
            grid[row][col] = border_color

    for box_index in range(n_boxes):
        left = border_columns[box_index] + 1
        top = start_top + box_index * step
        for dr, dc in marker_cells:
            grid[top + dr][left + marker_left + dc] = marker_color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": dict(overrides)},
    )
    if errors:
        raise RuntimeError("constructed invalid lesson: " + "; ".join(errors))
    return grid


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    height = len(grid)
    errors: list[str] = []
    if not (4 <= height <= 30 and 4 <= width <= 30):
        errors.append(f"grid dimensions must be 4..30, got {height}x{width}")
    invalid = [
        value
        for row in grid
        for value in row
        if isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
    ]
    if invalid:
        errors.append(f"grid contains invalid ARC colors: {invalid[:3]}")
    return errors


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        row, col = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _basic_grid_errors(grid)
    result: dict[str, Any] = {"errors": errors, "facts": None}
    if errors:
        return result

    normalized = [list(row) for row in grid]
    height, width = len(normalized), len(normalized[0])
    border_color = normalized[0][0]
    if border_color == 0:
        errors.append("border color must be nonzero")
    if any(value != border_color for value in normalized[0]):
        errors.append("top row must be a solid border")
    if any(value != border_color for value in normalized[-1]):
        errors.append("bottom row must be a solid border")

    border_columns = [
        col
        for col in range(width)
        if all(normalized[row][col] == border_color for row in range(height))
    ]
    if len(border_columns) < 4:
        errors.append(
            f"expected at least four full-height border columns, found {len(border_columns)}"
        )
        return result
    if border_columns[0] != 0 or border_columns[-1] != width - 1:
        errors.append("outer columns must be full-height borders")

    gaps = [
        border_columns[index + 1] - border_columns[index] - 1
        for index in range(len(border_columns) - 1)
    ]
    if len(set(gaps)) != 1:
        errors.append(f"box interiors must have equal widths, found {gaps}")
        return result
    box_w = gaps[0]
    n_boxes = len(gaps)
    if box_w not in (4, 5):
        errors.append(f"box width must be 4 or 5, found {box_w}")
    if n_boxes not in (3, 4):
        errors.append(f"expected 3 or 4 boxes, found {n_boxes}")
    if width != n_boxes * (box_w + 1) + 1:
        errors.append("border-column count and grid width are inconsistent")

    interior_values = [
        normalized[row][col]
        for row in range(1, height - 1)
        for col in range(width)
        if col not in set(border_columns)
    ]
    if not interior_values:
        errors.append("box interiors are empty")
        return result
    box_color = Counter(interior_values).most_common(1)[0][0]
    if box_color == border_color:
        errors.append("box color must differ from the border color")

    markers: list[dict[str, Any]] = []
    marker_colors: set[int] = set()
    for box_index in range(n_boxes):
        left = border_columns[box_index] + 1
        right = border_columns[box_index + 1]
        cells = [
            (row, col - left, normalized[row][col])
            for row in range(1, height - 1)
            for col in range(left, right)
            if normalized[row][col] != box_color
        ]
        if not cells:
            errors.append(f"box {box_index} has no marker")
            continue
        colors = {color for _, _, color in cells}
        if len(colors) != 1:
            errors.append(
                f"box {box_index} marker uses multiple colors: {sorted(colors)}"
            )
            continue
        marker_color = next(iter(colors))
        marker_colors.add(marker_color)
        top = min(row for row, _, _ in cells)
        marker_left = min(col for _, col, _ in cells)
        shape = tuple(sorted((row - top, col - marker_left) for row, col, _ in cells))
        shape_set = set(shape)
        if not _connected(shape_set):
            errors.append(f"box {box_index} marker is not 4-connected")
        shape_name = SHAPE_BY_CELLS.get(shape)
        if shape_name is None:
            errors.append(f"box {box_index} has unsupported marker shape {shape}")
        markers.append(
            {
                "top": top,
                "left": marker_left,
                "shape": shape,
                "shape_name": shape_name,
                "cells": cells,
                "color": marker_color,
            }
        )

    if len(markers) != n_boxes:
        return result
    if len(marker_colors) != 1:
        errors.append(f"marker color must be shared across boxes, found {marker_colors}")
    marker_color = markers[0]["color"]
    if marker_color == box_color:
        errors.append("marker color must differ from box color")

    shape_names = {marker["shape_name"] for marker in markers}
    shapes = {marker["shape"] for marker in markers}
    lefts = {marker["left"] for marker in markers}
    if len(shapes) != 1:
        errors.append("all boxes must contain the same marker shape")
    if None in shape_names:
        errors.append("marker shape must be one of the canonical four shapes")
    if len(lefts) != 1:
        errors.append("all markers must share one horizontal offset")

    tops = [marker["top"] for marker in markers]
    differences = [tops[index + 1] - tops[index] for index in range(n_boxes - 1)]
    if len(set(differences)) != 1:
        errors.append(f"marker tops must form an arithmetic progression: {tops}")
        step = None
    else:
        step = differences[0]
        if step not in STEP_BY_VALUE:
            errors.append(
                f"marker step must be one of {sorted(STEP_BY_VALUE)}, found {step}"
            )

    shape = markers[0]["shape"]
    marker_h, marker_w = _shape_dims(shape)
    marker_left = markers[0]["left"]
    if marker_left < 0 or marker_left + marker_w > box_w:
        errors.append("marker horizontal offset does not fit the box")

    next_top = None
    if step is not None:
        next_top = tops[-1] + step + _adjust(step, marker_h)
        if next_top < 1 or next_top + marker_h - 1 > height - 2:
            errors.append(
                f"extrapolated marker rows {next_top}..{next_top + marker_h - 1} "
                f"do not fit interior 1..{height - 2}"
            )

    allowed_colors = {border_color, box_color, marker_color}
    actual_colors = {value for row in normalized for value in row}
    if not actual_colors <= allowed_colors:
        errors.append(
            f"unexpected extra colors: {sorted(actual_colors - allowed_colors)}"
        )
    palette_size = len(actual_colors)
    if palette_size not in (2, 3):
        errors.append(f"palette size must be 2 or 3, found {palette_size}")
    if palette_size == 2 and marker_color != border_color:
        errors.append("two-color scenes must alias marker color to border color")
    if palette_size == 3 and len({border_color, box_color, marker_color}) != 3:
        errors.append("three-color scenes must keep border, box, and marker distinct")

    facts = {
        "height": height,
        "width": width,
        "border_color": border_color,
        "box_color": box_color,
        "marker_color": marker_color,
        "palette_size": palette_size,
        "border_columns": border_columns,
        "box_w": box_w,
        "n_boxes": n_boxes,
        "markers": markers,
        "tops": tops,
        "step_value": step,
        "step": STEP_BY_VALUE.get(step),
        "marker_shape": markers[0]["shape_name"],
        "marker_h": marker_h,
        "marker_w": marker_w,
        "marker_left": marker_left,
        "next_top": next_top,
    }
    result["facts"] = facts
    return result


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    facts = analysis.get("facts")
    if facts is None or analysis["errors"]:
        raise ValueError("cannot observe exact axes from malformed grid")
    return {
        "box_w": facts["box_w"],
        "n_boxes": facts["n_boxes"],
        "step": facts["step"],
        "marker_shape": facts["marker_shape"],
        "palette_size": facts["palette_size"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if requested and not errors:
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if observed.get(axis) != value:
                errors.append(
                    f"override {axis} requested {value!r}, observed {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The accepted structural grammar is the task's canonical manifold."""
    return self_check(grid)


def _base_output(facts: dict[str, Any], *, height: int | None = None):
    out_h = facts["height"] if height is None else height
    out_w = facts["box_w"] + 2
    output = full_grid(out_h, out_w, facts["box_color"])
    for col in range(out_w):
        output[0][col] = facts["border_color"]
        output[out_h - 1][col] = facts["border_color"]
    for row in range(out_h):
        output[row][0] = facts["border_color"]
        output[row][out_w - 1] = facts["border_color"]
    return output


def _render_marker(
    facts: dict[str, Any],
    top: int,
    *,
    marker_left: int | None = None,
    height: int | None = None,
):
    output = _base_output(facts, height=height)
    left = facts["marker_left"] if marker_left is None else marker_left
    for dr, dc in facts["markers"][0]["shape"]:
        row = top + dr
        col = 1 + left + dc
        if 0 <= row < len(output) and 0 <= col < len(output[0]):
            output[row][col] = facts["marker_color"]
    return output


def rule_mirror(grid):
    """Independent Python mirror used only for tests and rival construction."""
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"] is None:
        raise ValueError("; ".join(analysis["errors"]) or "malformed grid")
    facts = analysis["facts"]
    return _render_marker(facts, facts["next_top"])


def _facts(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"] is None:
        raise ValueError("; ".join(analysis["errors"]) or "malformed grid")
    return analysis["facts"]


def _rival_copy_last_box(grid):
    facts = _facts(grid)
    return _render_marker(facts, facts["tops"][-1])


def _rival_no_gap_adjust(grid):
    facts = _facts(grid)
    return _render_marker(facts, facts["tops"][-1] + facts["step_value"])


def _rival_always_positive_gap(grid):
    facts = _facts(grid)
    extra = 1 if facts["step_value"] > 0 else 0
    return _render_marker(
        facts, facts["tops"][-1] + facts["step_value"] + extra
    )


def _rival_force_downward(grid):
    facts = _facts(grid)
    step = abs(facts["step_value"])
    top = facts["tops"][-1] + step + _adjust(step, facts["marker_h"])
    return _render_marker(facts, top)


def _rival_fixed_step_one(grid):
    facts = _facts(grid)
    signed_one = 1 if facts["step_value"] > 0 else -1
    return _render_marker(facts, facts["tops"][-1] + signed_one)


def _rival_fixed_column_one(grid):
    facts = _facts(grid)
    return _render_marker(facts, facts["next_top"], marker_left=1)


def _rival_fixed_height_16(grid):
    facts = _facts(grid)
    true_output = _render_marker(facts, facts["next_top"])
    if len(true_output) == 16:
        return true_output
    if len(true_output) > 16:
        cropped = deepcopy(true_output[:16])
        cropped[-1] = [facts["border_color"]] * len(cropped[-1])
        return cropped
    padded = deepcopy(true_output[:-1])
    while len(padded) < 15:
        row = [facts["border_color"]]
        row += [facts["box_color"]] * facts["box_w"]
        row += [facts["border_color"]]
        padded.append(row)
    padded.append([facts["border_color"]] * (facts["box_w"] + 2))
    return padded


def _rival_marker_only(grid):
    facts = _facts(grid)
    output = full_grid(facts["marker_h"], facts["marker_w"], facts["box_color"])
    for dr, dc in facts["markers"][0]["shape"]:
        output[dr][dc] = facts["marker_color"]
    return output


SEMANTIC_RIVALS: dict[str, Callable] = {
    "copy_last_box": _rival_copy_last_box,
    "no_gap_adjust": _rival_no_gap_adjust,
    "always_positive_gap": _rival_always_positive_gap,
    "force_downward": _rival_force_downward,
    "fixed_step_one": _rival_fixed_step_one,
    "fixed_column_one": _rival_fixed_column_one,
    "fixed_height_16": _rival_fixed_height_16,
    "marker_only": _rival_marker_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # Every official pair is 16 rows and places the marker at relative column 1.
    # Generated left/right witnesses are therefore the only honest refutation.
    "fixed_column_one": _rival_fixed_column_one,
    "fixed_height_16": _rival_fixed_height_16,
}


def _witness(predicate: Callable[[dict[str, Any]], bool]):
    def wrapped(grid) -> bool:
        try:
            return bool(predicate(_facts(grid)))
        except Exception:
            return False

    return wrapped


SEMANTIC_WITNESSES = {
    "positive_gap_adjust": _witness(
        lambda facts: facts["step_value"] > facts["marker_h"]
    ),
    "positive_no_gap": _witness(
        lambda facts: 0 < facts["step_value"] <= facts["marker_h"]
    ),
    "upward_progression": _witness(lambda facts: facts["step_value"] < 0),
    "magnitude_gt_one": _witness(lambda facts: abs(facts["step_value"]) > 1),
    "offset_not_one": _witness(lambda facts: facts["marker_left"] != 1),
    "height_not_16": _witness(lambda facts: facts["height"] != 16),
}
WITNESS_RIVALS = {
    "positive_gap_adjust": ["no_gap_adjust"],
    "positive_no_gap": ["always_positive_gap"],
    "upward_progression": ["force_downward"],
    "magnitude_gt_one": ["fixed_step_one"],
    "offset_not_one": ["fixed_column_one"],
    "height_not_16": ["fixed_height_16"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson whenever a named plausible rival survives its demos."""
    reasons: list[str] = []
    query_input = query["input"]
    query_output = query.get("output")
    if query_output is None:
        query_output = rule_mirror(query_input)
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
            if not fits:
                continue
            if competitor(query_input) != query_output:
                reasons.append(f"{name} fits every demo but changes the query answer")
            else:
                reasons.append(f"{name} survives every demo and the query")
        except Exception as exc:
            reasons.append(f"{name} could not be evaluated: {type(exc).__name__}: {exc}")
    return reasons


def mutation_fixtures():
    """Targeted structural near-misses that must all be rejected."""
    base = generate(
        8675309,
        2,
        difficulty="medium",
        box_w=5,
        n_boxes=4,
        step="down2",
        marker_shape="tee",
        palette_size=3,
    )
    facts = _facts(base)
    box_color = facts["box_color"]
    marker_color = facts["marker_color"]

    broken_separator = deepcopy(base)
    separator = facts["border_columns"][2]
    broken_separator[len(base) // 2][separator] = box_color

    missing_marker = deepcopy(base)
    last = facts["markers"][-1]
    last_left = facts["border_columns"][-2] + 1
    for row, rel_col, _ in last["cells"]:
        missing_marker[row][last_left + rel_col] = box_color

    inconsistent_shape = deepcopy(base)
    second = facts["markers"][1]
    second_left = facts["border_columns"][1] + 1
    row, rel_col, _ = second["cells"][0]
    inconsistent_shape[row][second_left + rel_col] = box_color

    broken_progression = deepcopy(base)
    third = facts["markers"][2]
    third_left = facts["border_columns"][2] + 1
    for row, rel_col, _ in third["cells"]:
        broken_progression[row][third_left + rel_col] = box_color
    for row, rel_col, _ in third["cells"]:
        broken_progression[row + 1][third_left + rel_col] = marker_color

    extra_color = deepcopy(base)
    extra_color[1][2] = next(
        color
        for color in range(1, 10)
        if color not in {
            facts["border_color"], facts["box_color"], facts["marker_color"]
        }
    )

    return [
        ("broken_separator", broken_separator),
        ("missing_marker", missing_marker),
        ("inconsistent_shape", inconsistent_shape),
        ("broken_progression", broken_progression),
        ("extra_interior_color", extra_color),
    ]
