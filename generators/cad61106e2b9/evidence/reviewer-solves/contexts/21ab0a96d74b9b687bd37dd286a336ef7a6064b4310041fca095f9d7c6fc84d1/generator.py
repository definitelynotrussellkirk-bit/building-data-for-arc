"""Generator for the nested-frame control-band task ``cad61106e2b9``.

Exactly three disconnected color-4 rectangular frames are nested largest to
smallest.  A unique singleton marker valued 1, 2, or 3 selects the outer,
middle, or inner frame by area rank.  Fill zero cells strictly inside that
frame with color 8, stopping at the bounding box of the next inner frame.  A
second singleton in color 5, 6, 7, or 9 is an irrelevant distractor.

The ordinary three-example schedule contains all three control values.  It also
moves the marker away from the canonical top-left location and alternates which
singleton appears first in row-major order, so lessons refute location-based
shortcuts that fit every published example.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cad61106e2b9"
TASK_ID = "cad61106e2b9"
VERSION = "3.0.0"
RULE_HASH = "a3ad6fb565b1"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Three strictly nested, disconnected color-4 rectangular frames plus a "
    "singleton control marker and an irrelevant singleton distractor. Rank the "
    "frames by area, largest first; control 1/2/3 selects outer/middle/inner. "
    "Fill zero cells inside the selected frame with 8, excluding the complete "
    "bounding box of the next inner frame when one exists."
)

INVARIANTS = [
    "exactly three disconnected color-4 hollow rectangular frames",
    "successive frames are strictly nested with at least one blank-cell moat",
    "exactly one marker valued 1..3 selects a frame by descending area rank",
    "exactly one irrelevant singleton uses color 5, 6, 7, or 9",
    "both singleton cells lie outside the largest frame",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-profile canonical-size schedule",
        "valid": "13..24",
        "doc": "Input-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "five-profile canonical-size schedule",
        "valid": "14..24",
        "doc": "Input-grid width.",
    },
    "ctrl_value": {
        "type": "int",
        "default": "three-example lesson schedule",
        "valid": "1|2|3",
        "doc": "1-indexed descending-area frame rank to fill.",
    },
    "distractor_color": {
        "type": "int",
        "default": "four-color canonical palette schedule",
        "valid": "5|6|7|9",
        "doc": "Color of the irrelevant singleton outside the frame stack.",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
SCHEDULE_PROFILES = ("outer_band", "middle_band", "inner_interior")
MIN_STRICT_FRAC = 1.0

Grid = list[list[int]]
Box = tuple[int, int, int, int]
Cell = tuple[int, int]

_CANONICAL_DIMENSIONS: tuple[tuple[int, int], ...] = (
    (13, 15),
    (14, 16),
    (13, 15),
    (13, 14),
    (14, 15),
)
_DISTRACTOR_COLORS = (5, 6, 7, 9)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % 3]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {unknown}")
    for label, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"override {label!r} must be an int, got {type(value).__name__}")


def _scheduled_int(ctx, label: str, lo: int, hi: int, value: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, value, value)


def _scheduled_choice(ctx, label: str, options: tuple[int, ...], value: int) -> int:
    available = options if label in ctx.overrides and ctx.overrides[label] is not None else (value,)
    return int(ctx.draw_choice(label, available))


def _draw_dimension(
    ctx,
    label: str,
    *,
    full_lo: int,
    full_hi: int,
    canonical_value: int,
    sample_index: int,
    difficulty: str | None,
) -> int:
    """Anchor every fourth sample at canonical scale; broaden other samples.

    Exact overrides always retain the full public range.  The default bands use
    disjoint-ish size envelopes so difficulty is observable without changing
    the task rule, while the canonical anchor keeps every band represented in
    profile-floor and lesson data.
    """
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, full_lo, full_hi)
    if int(sample_index) % 4 == 0:
        return ctx.draw_int(label, canonical_value, canonical_value)
    if label == "grid_h":
        lo, hi = {
            "easy": (13, 16),
            "medium": (15, 20),
            "hard": (19, 24),
            None: (13, 24),
        }[difficulty]
    else:
        lo, hi = {
            "easy": (14, 17),
            "medium": (16, 21),
            "hard": (20, 24),
            None: (14, 24),
        }[difficulty]
    return ctx.draw_int(label, lo, hi)


def _frame_outline(grid: Grid, box: Box, color: int = 4) -> None:
    top, left, bottom, right = box
    for c in range(left, right + 1):
        grid[top][c] = color
        grid[bottom][c] = color
    for r in range(top, bottom + 1):
        grid[r][left] = color
        grid[r][right] = color


def _inset_box(box: Box, min_h: int, min_w: int, rng) -> Box:
    top, left, bottom, right = box
    height = bottom - top + 1
    width = right - left + 1
    max_v_shrink = height - min_h
    max_h_shrink = width - min_w
    if max_v_shrink < 4 or max_h_shrink < 4:
        raise ValueError("frame is too small for a separated nested frame")

    v_shrink = rng.randint(4, max_v_shrink)
    h_shrink = rng.randint(4, max_h_shrink)
    inset_top = rng.randint(2, v_shrink - 2)
    inset_bottom = v_shrink - inset_top
    inset_left = rng.randint(2, h_shrink - 2)
    inset_right = h_shrink - inset_left
    return (
        top + inset_top,
        left + inset_left,
        bottom - inset_bottom,
        right - inset_right,
    )


def _build_frame_boxes(h: int, w: int, rng) -> tuple[Box, Box, Box]:
    outer_h = rng.randint(11, h - 2)
    outer_w = rng.randint(11, w - 2)
    top = rng.randint(1, h - outer_h - 1)
    left = rng.randint(1, w - outer_w - 1)
    outer = (top, left, top + outer_h - 1, left + outer_w - 1)
    middle = _inset_box(outer, 7, 7, rng)
    inner = _inset_box(middle, 3, 3, rng)
    return outer, middle, inner


def _outside_cells(h: int, w: int, outer: Box) -> list[Cell]:
    top, left, bottom, right = outer
    return [
        (r, c)
        for r in range(h)
        for c in range(w)
        if not (top <= r <= bottom and left <= c <= right)
    ]


def _place_singletons(
    grid: Grid,
    outer: Box,
    ctrl: int,
    distractor: int,
    sample_index: int,
    rng,
) -> None:
    h, w = len(grid), len(grid[0])
    available = [cell for cell in _outside_cells(h, w, outer) if cell != (0, 0)]
    if len(available) < 2:
        raise RuntimeError("not enough exterior cells for marker and distractor")

    if int(sample_index) % 2 == 0:
        # Counterexample to both canonical-fitting shortcuts: the distractor is
        # the first row-major singleton while the true marker is elsewhere.
        distractor_cell = (0, 0)
        control_cell = rng.choice(available)
    else:
        first, second = sorted(rng.sample(available, 2))
        control_cell, distractor_cell = first, second

    cr, cc = control_cell
    dr, dc = distractor_cell
    grid[cr][cc] = ctrl
    grid[dr][dc] = distractor


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    """Generate one deterministic, structurally checked teaching input."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    default_h, default_w = _CANONICAL_DIMENSIONS[
        (int(sample_index) // 4) % len(_CANONICAL_DIMENSIONS)
    ]
    h = _draw_dimension(
        ctx,
        "grid_h",
        full_lo=13,
        full_hi=24,
        canonical_value=default_h,
        sample_index=int(sample_index),
        difficulty=difficulty,
    )
    w = _draw_dimension(
        ctx,
        "grid_w",
        full_lo=14,
        full_hi=24,
        canonical_value=default_w,
        sample_index=int(sample_index),
        difficulty=difficulty,
    )
    ctrl = _scheduled_int(ctx, "ctrl_value", 1, 3, int(sample_index) % 3 + 1)
    distractor = _scheduled_choice(
        ctx,
        "distractor_color",
        _DISTRACTOR_COLORS,
        _DISTRACTOR_COLORS[int(sample_index) % len(_DISTRACTOR_COLORS)],
    )

    layout_rng = ctx.draw_rng("frame_layout")
    boxes = _build_frame_boxes(h, w, layout_rng)
    grid = full_grid(h, w, 0)
    for box in boxes:
        _frame_outline(grid, box)
    _place_singletons(
        grid,
        boxes[0],
        ctrl,
        distractor,
        int(sample_index),
        ctx.draw_rng("singleton_layout"),
    )

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise RuntimeError("internal generator invariant failed: " + "; ".join(errors))
    return grid


def _valid_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty list of nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    if not 13 <= len(grid) <= 24 or not 14 <= width <= 24:
        errors.append(f"grid dimensions {len(grid)}x{width} lie outside 13..24 by 14..24")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    return errors


def _color4_components(grid: Grid) -> list[set[Cell]]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[set[Cell]] = []
    for start_r in range(h):
        for start_c in range(w):
            if grid[start_r][start_c] != 4 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: set[Cell] = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 4
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _rect_frame_box(cells: set[Cell]) -> tuple[bool, Box]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    expected = {
        (r, c)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if r in (top, bottom) or c in (left, right)
    }
    return cells == expected and bottom - top >= 2 and right - left >= 2, (
        top,
        left,
        bottom,
        right,
    )


def _boxes_by_area(grid: Grid) -> list[Box]:
    boxes: list[Box] = []
    for cells in _color4_components(grid):
        ok, box = _rect_frame_box(cells)
        if ok:
            boxes.append(box)
    return sorted(
        boxes,
        key=lambda box: (box[2] - box[0] + 1) * (box[3] - box[1] + 1),
        reverse=True,
    )


def _control(grid: Grid) -> int:
    return next(value for row in grid for value in row if value in (1, 2, 3))


def _apply_band(grid: Grid, control: int, *, whole_interior: bool = False) -> Grid:
    output = [row[:] for row in grid]
    boxes = _boxes_by_area(grid)
    index = int(control) - 1
    if not 0 <= index < len(boxes):
        return output
    selected = boxes[index]
    inner = boxes[index + 1] if index + 1 < len(boxes) else None
    top, left, bottom, right = selected
    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            if grid[r][c] != 0:
                continue
            if not whole_interior and inner is not None:
                it, il, ib, ir = inner
                if it <= r <= ib and il <= c <= ir:
                    continue
            output[r][c] = 8
    return output


def rule_mirror(grid: Grid) -> Grid:
    """Independent-use Python mirror; the pinned Racket program is authority."""
    return _apply_band(grid, _control(grid))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the bounded teaching grammar, including all canonical inputs."""
    del difficulty, meta
    errors = _valid_grid_errors(grid)
    if errors:
        return errors

    control_cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in (1, 2, 3)
    ]
    if len(control_cells) != 1:
        errors.append(f"expected exactly one control singleton, got {len(control_cells)}")
        return errors
    control_r, control_c, control = control_cells[0]

    distractor_cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in _DISTRACTOR_COLORS
    ]
    if len(distractor_cells) != 1:
        errors.append(f"expected exactly one distractor singleton, got {len(distractor_cells)}")
        return errors
    distractor_r, distractor_c, distractor = distractor_cells[0]

    allowed = {0, 4, control, distractor}
    unexpected = sorted({value for row in grid for value in row if value not in allowed})
    if unexpected:
        errors.append(f"unexpected input colors: {unexpected}")

    raw_components = _color4_components(grid)
    if len(raw_components) != 3:
        errors.append(f"expected exactly three disconnected color-4 frames, got {len(raw_components)}")
        return errors

    boxes: list[Box] = []
    for cells in raw_components:
        ok, box = _rect_frame_box(cells)
        if not ok:
            errors.append(f"color-4 component is not an exact hollow rectangle: {box}")
        boxes.append(box)
    if errors:
        return errors

    boxes.sort(
        key=lambda box: (box[2] - box[0] + 1) * (box[3] - box[1] + 1),
        reverse=True,
    )
    for outer, inner in zip(boxes, boxes[1:]):
        if not (
            inner[0] - outer[0] >= 2
            and inner[1] - outer[1] >= 2
            and outer[2] - inner[2] >= 2
            and outer[3] - inner[3] >= 2
        ):
            errors.append("successive frames must be nested behind a one-cell blank moat")
            break

    outer = boxes[0]
    for label, r, c in (
        ("control", control_r, control_c),
        ("distractor", distractor_r, distractor_c),
    ):
        if outer[0] <= r <= outer[2] and outer[1] <= c <= outer[3]:
            errors.append(f"{label} singleton must lie outside the largest frame")

    if not errors and rule_mirror(grid) == grid:
        errors.append("selected frame must expose at least one zero cell to fill")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    distractor = next(
        value for row in grid for value in row if value in _DISTRACTOR_COLORS
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "ctrl_value": _control(grid),
        "distractor_color": distractor,
    }


# -- Executable rivals -----------------------------------------------------

def _always_outer(grid: Grid) -> Grid:
    return _apply_band(grid, 1)


def _always_middle(grid: Grid) -> Grid:
    return _apply_band(grid, 2)


def _always_inner(grid: Grid) -> Grid:
    return _apply_band(grid, 3)


def _reverse_area_rank(grid: Grid) -> Grid:
    return _apply_band(grid, 4 - _control(grid))


def _cyclic_zero_based_control(grid: Grid) -> Grid:
    return _apply_band(grid, _control(grid) % 3 + 1)


def _fill_entire_selected_interior(grid: Grid) -> Grid:
    return _apply_band(grid, _control(grid), whole_interior=True)


def _top_left_is_control(grid: Grid) -> Grid:
    value = grid[0][0]
    return _apply_band(grid, value) if value in (1, 2, 3) else [row[:] for row in grid]


def _first_singleton_is_control(grid: Grid) -> Grid:
    counts = Counter(value for row in grid for value in row if value != 0)
    for row in grid:
        for value in row:
            if value != 0 and counts[value] == 1:
                return _apply_band(grid, value) if value in (1, 2, 3) else [r[:] for r in grid]
    return [row[:] for row in grid]


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "always_outer_band": _always_outer,
    "always_middle_band": _always_middle,
    "always_inner_interior": _always_inner,
    "reverse_area_rank": _reverse_area_rank,
    "cyclic_zero_based_control": _cyclic_zero_based_control,
    "fill_entire_selected_interior": _fill_entire_selected_interior,
    "top_left_cell_is_control": _top_left_is_control,
    "first_singleton_is_control": _first_singleton_is_control,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "top_left_cell_is_control": _top_left_is_control,
    "first_singleton_is_control": _first_singleton_is_control,
}


def _singleton_positions(grid: Grid) -> tuple[Cell, Cell]:
    control_pos = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in (1, 2, 3)
    )
    distractor_pos = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in _DISTRACTOR_COLORS
    )
    return control_pos, distractor_pos


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "outer_band_selected": lambda grid: (
        _control(grid) == 1 and _always_middle(grid) != rule_mirror(grid)
    ),
    "middle_band_selected": lambda grid: (
        _control(grid) == 2 and _always_outer(grid) != rule_mirror(grid)
    ),
    "inner_interior_selected": lambda grid: (
        _control(grid) == 3 and _always_outer(grid) != rule_mirror(grid)
    ),
    "descending_area_rank_is_decisive": lambda grid: (
        _reverse_area_rank(grid) != rule_mirror(grid)
    ),
    "next_inner_box_stops_fill": lambda grid: (
        _fill_entire_selected_interior(grid) != rule_mirror(grid)
    ),
    "control_not_fixed_at_top_left": lambda grid: (
        grid[0][0] not in (1, 2, 3) and _top_left_is_control(grid) != rule_mirror(grid)
    ),
    "distractor_precedes_control": lambda grid: (
        _singleton_positions(grid)[1] < _singleton_positions(grid)[0]
        and _first_singleton_is_control(grid) != rule_mirror(grid)
    ),
}

WITNESS_RIVALS = {
    "outer_band_selected": ["always_middle_band"],
    "middle_band_selected": ["always_outer_band"],
    "inner_interior_selected": ["always_outer_band"],
    "descending_area_rank_is_decisive": ["reverse_area_rank"],
    "next_inner_box_stops_fill": ["fill_entire_selected_interior"],
    "control_not_fixed_at_top_left": ["top_left_cell_is_control"],
    "distractor_precedes_control": ["first_singleton_is_control"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson whenever a named plausible wrong rule survives demos."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is missing input"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is missing input/output")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with nested-frame rule")

    query_expected = query.get("output", rule_mirror(query["input"]))
    if query_expected != rule_mirror(query["input"]):
        reasons.append("query output disagrees with nested-frame rule")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        except Exception as exc:  # pragma: no cover - surfaced as a contract failure
            reasons.append(f"competitor {name!r} raised: {exc}")
            continue
        if survives:
            if rival(query["input"]) != query_expected:
                reasons.append(f"demonstrations do not refute competitor: {name}")
            else:
                reasons.append(f"demonstrations leave competitor answer-equivalent on query: {name}")
    return reasons
