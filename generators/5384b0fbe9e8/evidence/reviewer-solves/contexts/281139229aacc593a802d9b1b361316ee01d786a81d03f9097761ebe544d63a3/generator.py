"""Semantic generator for ARC task 5384b0fbe9e8.

A centered full-height color-5 divider separates a populated left panel from
an empty right panel.  The output preserves the input and reflects every
non-zero left-panel cell across the divider, preserving its color.

Version 2 replaces a loose, mostly inert axis surface with a small exact one.
Ordinary scenes always contain marks both next to and far from the divider,
span multiple rows, use several colors, and leave the complete right panel
empty.  A pinned canonical-profile branch preserves the demonstrated 7x9,
8x11, 9x11, and 8x13 morphologies while generalized draws vary dimensions,
occupancy, repeated colors, and positions.  Version 2.1 schedules those
canonical anchors so every three-example lesson also includes decisive
counterexamples to one-mark-per-row, one-mark-per-column, and
one-mark-per-color shortcuts.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "5384b0fbe9e8"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "590349f64152"

SUMMARY = (
    "Find the centered full-height color-5 divider. Preserve the input and "
    "copy every non-zero cell from the left panel to the equal-distance cell "
    "on the right, keeping its color."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "the grid has equal-width panels around one centered full-height color-5 divider",
    "color 5 occurs only in the divider column",
    "the right panel is entirely background in every input",
    "the left panel has at least four marks in at least three colors",
    "left marks span multiple rows and include both the outer edge and divider-adjacent column",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed, with canonical-profile anchors",
        "valid": "5..16",
    },
    "panel_w": {
        "type": "int",
        "default": "difficulty-skewed, with canonical-profile anchors",
        "valid": "3..8",
    },
    "palette_size": {
        "type": "int",
        "default": "difficulty-skewed 3..5",
        "valid": "3..5",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_CANONICAL_PROFILES = (
    # (height, panel width, mark count, distinct mark colors)
    (8, 5, 5, 5),
    (7, 4, 4, 4),
    (9, 5, 5, 5),
    (8, 6, 5, 5),
)
_PROFILE_SCHEDULE = (
    "canonical_anchor",
    "general",
    "general",
    "canonical_anchor",
    "general",
    "general",
    "canonical_anchor",
    "general",
    "general",
    "general",
)
SCHEDULE_PROFILES = ("canonical_anchor", "general")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the 30/70 lesson schedule to the semantic gate."""
    del seed, difficulty
    return _PROFILE_SCHEDULE[int(sample_index) % len(_PROFILE_SCHEDULE)]


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    bounds = {"grid_h": (5, 16), "panel_w": (3, 8), "palette_size": (3, 5)}
    for name, (lo, hi) in bounds.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")


def _canonical_positions(h: int, panel_w: int, mark_count: int, rng):
    """One mark per selected column and row, including both reflection extremes."""
    if mark_count > min(h, panel_w):
        raise ValueError("canonical profile cannot place marks on distinct rows and columns")
    if mark_count == panel_w:
        columns = list(range(panel_w))
    else:
        interior = list(range(1, panel_w - 1))
        columns = [0, panel_w - 1]
        columns.extend(rng.sample(interior, mark_count - 2))
        columns.sort()
    rows = rng.sample(list(range(h)), mark_count)
    return list(zip(rows, columns))


def _general_positions(h: int, panel_w: int, mark_count: int, rng):
    """Choose marks with explicit reflection and anti-shortcut witnesses."""
    all_spots = [(r, c) for r in range(h) for c in range(panel_w)]
    far_row = rng.randrange(h)
    near_choices = [r for r in range(h) if r != far_row]
    near_row = rng.choice(near_choices)
    third_rows = [r for r in range(h) if r not in (far_row, near_row)]
    third_row = rng.choice(third_rows)
    interior_col = rng.randint(1, panel_w - 2)

    # The far row has two marks and the interior column has two marks.  Since
    # generalized draws also use more marks than colors, one draw refutes the
    # three canonical-set shortcuts declared below.
    chosen = {
        (far_row, 0),
        (near_row, panel_w - 1),
        (far_row, interior_col),
        (third_row, interior_col),
    }
    # Keep the same-row opposite extremes empty.  This makes the official
    # reflection disagree deterministically with a non-reflecting panel copy.
    reserved_empty = {(far_row, panel_w - 1), (near_row, 0)}

    remaining = [
        spot for spot in all_spots
        if spot not in chosen and spot not in reserved_empty
    ]
    chosen.update(rng.sample(remaining, mark_count - len(chosen)))
    return sorted(chosen)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    has_override = any(overrides.get(name) is not None for name in AXES)
    canonical_anchor = (
        not has_override
        and schedule_profile(seed, sample_index, difficulty) == "canonical_anchor"
    )

    if canonical_anchor:
        profile = ctx.draw_rng("canonical_profile").choice(_CANONICAL_PROFILES)
        h, panel_w, mark_count, palette_size = profile
        h = ctx.draw_int("grid_h", h, h)
        panel_w = ctx.draw_int("panel_w", panel_w, panel_w)
        palette_size = ctx.draw_int("palette_size", palette_size, palette_size)
    else:
        h = ctx.draw_int_diff("grid_h", 5, 16)
        panel_w = ctx.draw_int_diff("panel_w", 3, 8)
        palette_size = ctx.draw_int_diff("palette_size", 3, 5)
        capacity = h * panel_w
        if difficulty == "easy":
            lo, hi = palette_size + 1, min(8, capacity - 2)
        elif difficulty == "hard":
            lo, hi = max(9, palette_size + 1), min(15, capacity - 2)
        else:
            lo, hi = max(6, palette_size + 1), min(12, capacity - 2)
        mark_count = ctx.draw_rng("mark_count").randint(lo, hi)

    rng = ctx.draw_rng("layout")
    positions = (
        _canonical_positions(h, panel_w, mark_count, rng)
        if canonical_anchor
        else _general_positions(h, panel_w, mark_count, rng)
    )

    palette = rng.sample(list(_COLORS), palette_size)
    values = list(palette)
    values.extend(rng.choice(palette) for _ in range(mark_count - palette_size))
    rng.shuffle(values)

    width = 2 * panel_w + 1
    grid = full_grid(h, width, 0)
    for row in range(h):
        grid[row][panel_w] = 5
    for (row, col), value in zip(positions, values):
        grid[row][col] = value
    return grid


def semantic_observables(grid) -> dict:
    """Recover task-linked facts from the returned input grid."""
    h = len(grid) if isinstance(grid, (list, tuple)) else 0
    width = len(grid[0]) if h and isinstance(grid[0], (list, tuple)) else 0
    divider_columns = []
    if h and width and all(isinstance(row, (list, tuple)) and len(row) == width for row in grid):
        divider_columns = [
            col for col in range(width)
            if all(grid[row][col] == 5 for row in range(h))
        ]
    divider = divider_columns[0] if len(divider_columns) == 1 else None
    marks = []
    if divider is not None:
        marks = [
            (row, col, grid[row][col])
            for row in range(h)
            for col in range(divider)
            if grid[row][col] not in (0, 5)
        ]
    colors = {value for _, _, value in marks}
    row_counts = {
        row: sum(mark_row == row for mark_row, _, _ in marks)
        for row in {mark_row for mark_row, _, _ in marks}
    }
    column_counts = {
        col: sum(mark_col == col for _, mark_col, _ in marks)
        for col in {mark_col for _, mark_col, _ in marks}
    }
    color_counts = {
        value: sum(mark_value == value for _, _, mark_value in marks)
        for value in colors
    }
    right_nonzero = None
    if divider is not None:
        right_nonzero = sum(
            grid[row][col] != 0
            for row in range(h)
            for col in range(divider + 1, width)
        )
    return {
        "grid_h": h,
        "grid_w": width,
        "panel_w": divider,
        "palette_size": len(colors),
        "mark_count": len(marks),
        "mark_rows": len({row for row, _, _ in marks}),
        "mark_columns": len({col for _, col, _ in marks}),
        "max_marks_per_row": max(row_counts.values(), default=0),
        "max_marks_per_column": max(column_counts.values(), default=0),
        "max_marks_per_color": max(color_counts.values(), default=0),
        "has_far_edge_mark": bool(marks) and any(col == 0 for _, col, _ in marks),
        "has_near_divider_mark": bool(marks) and any(col == divider - 1 for _, col, _ in marks),
        "right_nonzero": right_nonzero,
        "divider_columns": divider_columns,
    }


def observe_overrides(grid) -> dict:
    facts = semantic_observables(grid)
    return {name: facts[name] for name in AXES}


def strict_canonical_like(grid) -> bool:
    """Linked canonical morphology used by the count-backed semantic census."""
    if self_check(grid):
        return False
    facts = semantic_observables(grid)
    profile = (
        facts["grid_h"],
        facts["panel_w"],
        facts["mark_count"],
        facts["palette_size"],
    )
    return profile in _CANONICAL_PROFILES and facts["mark_rows"] == facts["mark_count"]


def rule_mirror(grid):
    """Independent Python diagnostic mirror; canonical Racket remains authority."""
    shape_errors = _grid_shape_errors(grid)
    if shape_errors:
        raise ValueError(shape_errors[0])
    h, width = len(grid), len(grid[0])
    dividers = [
        col for col in range(width)
        if all(grid[row][col] == 5 for row in range(h))
    ]
    if len(dividers) != 1:
        raise ValueError(f"expected exactly one full-height color-5 divider; got {dividers}")
    divider = dividers[0]
    output = [list(row) for row in grid]
    for row in range(h):
        for col in range(divider):
            value = grid[row][col]
            mirror_col = 2 * divider - col
            if value != 0 and 0 <= mirror_col < width:
                output[row][mirror_col] = value
    return output


def _rival_one_mark_per_row(grid):
    """Wrong rule fitting canonical pairs: mirror only the first mark per row."""
    shape_errors = _grid_shape_errors(grid)
    if shape_errors:
        raise ValueError(shape_errors[0])
    h, width = len(grid), len(grid[0])
    dividers = [
        col for col in range(width)
        if all(grid[row][col] == 5 for row in range(h))
    ]
    if len(dividers) != 1:
        raise ValueError(f"expected exactly one full-height color-5 divider; got {dividers}")
    divider = dividers[0]
    output = [list(row) for row in grid]
    for row in range(h):
        for col in range(divider):
            value = grid[row][col]
            if value != 0:
                output[row][2 * divider - col] = value
                break
    return output


def _rival_one_mark_per_column(grid):
    """Wrong rule fitting canonical pairs: mirror only the first mark per column."""
    shape_errors = _grid_shape_errors(grid)
    if shape_errors:
        raise ValueError(shape_errors[0])
    h, width = len(grid), len(grid[0])
    dividers = [
        col for col in range(width)
        if all(grid[row][col] == 5 for row in range(h))
    ]
    if len(dividers) != 1:
        raise ValueError(f"expected exactly one full-height color-5 divider; got {dividers}")
    divider = dividers[0]
    output = [list(row) for row in grid]
    for col in range(divider):
        for row in range(h):
            value = grid[row][col]
            if value != 0:
                output[row][2 * divider - col] = value
                break
    return output


def _rival_one_mark_per_color(grid):
    """Wrong rule fitting canonical pairs: mirror only one mark of each color."""
    shape_errors = _grid_shape_errors(grid)
    if shape_errors:
        raise ValueError(shape_errors[0])
    h, width = len(grid), len(grid[0])
    dividers = [
        col for col in range(width)
        if all(grid[row][col] == 5 for row in range(h))
    ]
    if len(dividers) != 1:
        raise ValueError(f"expected exactly one full-height color-5 divider; got {dividers}")
    divider = dividers[0]
    output = [list(row) for row in grid]
    seen: set[int] = set()
    for row in range(h):
        for col in range(divider):
            value = grid[row][col]
            if value != 0 and value not in seen:
                seen.add(value)
                output[row][2 * divider - col] = value
    return output


SEMANTIC_RIVALS = {
    "one_mark_per_row": _rival_one_mark_per_row,
    "one_mark_per_column": _rival_one_mark_per_column,
    "one_mark_per_color": _rival_one_mark_per_color,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "multiple_marks_in_one_row": (
        lambda grid: semantic_observables(grid)["max_marks_per_row"] >= 2
    ),
    "multiple_marks_in_one_column": (
        lambda grid: semantic_observables(grid)["max_marks_per_column"] >= 2
    ),
    "repeated_mark_color": (
        lambda grid: semantic_observables(grid)["max_marks_per_color"] >= 2
    ),
}
WITNESS_RIVALS = {
    "multiple_marks_in_one_row": ["one_mark_per_row"],
    "multiple_marks_in_one_column": ["one_mark_per_column"],
    "repeated_mark_color": ["one_mark_per_color"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave a query-changing rival alive."""
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {index} input is invalid: {type(exc).__name__}: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the canonical rule")

    if not isinstance(query, dict) or "input" not in query:
        return reasons + ["query is not an input pair"]
    try:
        query_truth = rule_mirror(query["input"])
    except Exception as exc:
        return reasons + [f"query input is invalid: {type(exc).__name__}: {exc}"]
    if "output" in query and query["output"] != query_truth:
        reasons.append("query output disagrees with the canonical rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = competitor(query["input"]) != query_truth
        except Exception as exc:
            reasons.append(
                f"competitor {name!r} raised {type(exc).__name__}: {exc}"
            )
            continue
        if survives and changes_query:
            reasons.append(
                f"demos do not refute query-changing competitor {name!r}"
            )
    return reasons


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the complete teaching grammar, including canonical inputs."""
    errors = _grid_shape_errors(grid)
    if errors:
        return errors

    h, width = len(grid), len(grid[0])
    if not 5 <= h <= 16:
        errors.append(f"height {h} outside 5..16")
    if width % 2 == 0 or not 7 <= width <= 17:
        errors.append(f"width {width} must be odd and in 7..17")

    divider_columns = [
        col for col in range(width)
        if all(grid[row][col] == 5 for row in range(h))
    ]
    if len(divider_columns) != 1:
        errors.append(f"expected exactly one full-height color-5 divider; got {divider_columns}")
        return errors
    divider = divider_columns[0]
    if divider != width // 2:
        errors.append("divider must be centered between equal-width panels")
    if not 3 <= divider <= 8:
        errors.append(f"panel width {divider} outside 3..8")
    if any(
        grid[row][col] == 5
        for row in range(h)
        for col in range(width)
        if col != divider
    ):
        errors.append("color 5 may occur only in the divider column")
    if any(
        grid[row][col] != 0
        for row in range(h)
        for col in range(divider + 1, width)
    ):
        errors.append("right panel must be entirely background before reflection")

    marks = [
        (row, col, grid[row][col])
        for row in range(h)
        for col in range(divider)
        if grid[row][col] not in (0, 5)
    ]
    colors = {value for _, _, value in marks}
    if not 4 <= len(marks) <= 15:
        errors.append(f"expected 4..15 left-panel marks; found {len(marks)}")
    if not 3 <= len(colors) <= 5:
        errors.append(f"expected 3..5 left-panel colors; found {len(colors)}")
    if len({row for row, _, _ in marks}) < 2:
        errors.append("left marks must span at least two rows")
    if len({col for _, col, _ in marks}) < 2:
        errors.append("left marks must span at least two columns")
    if marks and not any(col == 0 for _, col, _ in marks):
        errors.append("missing far-edge reflection witness in left column 0")
    if marks and not any(col == divider - 1 for _, col, _ in marks):
        errors.append("missing divider-adjacent reflection witness")
    return errors
