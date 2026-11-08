"""Generate framed line-completion lessons for ARC task f361853c0fcd.

A color-5 rectangular frame contains non-5 markers on its border.  A color
paints an interior column only when equal markers occupy the aligned top and
bottom cells; it paints an interior row only when equal markers occupy the
aligned left and right cells.  Colors are processed in ascending order, with
columns before rows within a color, so the largest color wins every crossing.

Default lessons include lawful unmatched/misaligned border markers.  Those
markers make the canonical-fitting shortcuts "paint from any marker" and
"opposite sides anywhere" observably wrong instead of silently teachable.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "f361853c0fcd"
VERSION = "4.0.0"
RULE_HASH = "cffc010305aa"
SUMMARY = (
    "A zero-background canvas contains one hollow color-5 rectangular frame. "
    "Equal, aligned markers on top/bottom fill their interior column; equal, "
    "aligned markers on left/right fill their interior row. Unmatched and "
    "misaligned border markers remain inert. Colors paint in ascending order "
    "(column then row within a color), so the numerically largest crossing "
    "color wins. Default lessons explicitly refute marker-without-mate and "
    "orientation-priority shortcuts."
)
EXAMPLES_NEEDED = 3
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

INVARIANTS = [
    "background and the untouched frame interior are 0",
    "exactly one hollow color-5 frame with a nonzero border and color-5 corners",
    "aligned equal top/bottom markers define vertical lines",
    "aligned equal left/right markers define horizontal lines",
    "unmatched or misaligned border markers do not define lines",
    "valid pair colors are distinct except a cross color may define one row and one column",
    "colors paint in ascending numeric order; columns precede rows within one color",
]

AXES = {
    "frame_h": {"type": "int", "default": "scheduled 7..11", "valid": "7..11"},
    "frame_w": {"type": "int", "default": "scheduled 8..12", "valid": "8..12"},
    "n_v_only": {"type": "int", "default": "1..3 by difficulty", "valid": "1..3"},
    "n_h_only": {"type": "int", "default": "1..3 by difficulty", "valid": "1..3"},
    "n_cross": {"type": "int", "default": "1", "valid": "0..1"},
    "n_decoys": {"type": "int", "default": "2..4", "valid": "0..4"},
}

_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
# Five public canvas/frame profiles plus one difficulty-dependent expansion.
_CANONICAL_PROFILES = (
    ("canonical_11x13", 8, 10, (1, 2, 1, 2)),
    ("canonical_12x12", 8, 8, (2, 2, 2, 2)),
    ("canonical_12x14", 9, 9, (1, 2, 3, 2)),
    ("canonical_13x12", 9, 9, (2, 2, 1, 2)),
    ("canonical_12x13", 9, 9, (1, 2, 2, 2)),
)
SCHEDULE_PROFILES = tuple(item[0] for item in _CANONICAL_PROFILES) + ("expanded",)


def schedule_profile(seed, sample_index, difficulty=None):
    """Deterministic six-step curriculum; seed/difficulty do not shift starts."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_axis(ctx, name, lo, hi, default_lo, default_hi):
    """Use full advertised bounds for explicit overrides, band bounds otherwise."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default_lo, default_hi)


def _defaults_for_profile(profile, difficulty):
    for name, frame_h, frame_w, margins in _CANONICAL_PROFILES:
        if profile == name:
            return {
                "frame_h": (frame_h, frame_h),
                "frame_w": (frame_w, frame_w),
                "n_v_only": (1, 1),
                "n_h_only": (1, 1),
                "n_cross": (1, 1),
                "n_decoys": (2, 2),
                "margins": margins,
            }
    if difficulty == "easy":
        return {
            "frame_h": (7, 8),
            "frame_w": (8, 9),
            "n_v_only": (1, 1),
            "n_h_only": (1, 1),
            "n_cross": (1, 1),
            "n_decoys": (2, 3),
            "margins": None,
        }
    if difficulty == "hard":
        return {
            "frame_h": (10, 11),
            "frame_w": (11, 12),
            "n_v_only": (2, 3),
            "n_h_only": (2, 3),
            "n_cross": (1, 1),
            "n_decoys": (3, 4),
            "margins": None,
        }
    return {
        "frame_h": (8, 10),
        "frame_w": (9, 11),
        "n_v_only": (1, 2),
        "n_h_only": (1, 2),
        "n_cross": (1, 1),
        "n_decoys": (2, 4),
        "margins": None,
    }


def _role_colors(rng, n_v_only, n_h_only, n_cross):
    """Choose distinct role colors with witnesses for both priority rivals.

    The first vertical-only color is greater than the first horizontal-only
    color, which is greater than the cross color on default n_cross=1 draws.
    Thus neither "rows always win" nor "columns always win" can fit.
    """
    total = n_v_only + n_h_only + n_cross
    chosen = sorted(rng.sample(list(_COLORS), total))
    cross = []
    if n_cross:
        cross.append(chosen.pop(0))
    vertical = [chosen.pop()]
    horizontal = [chosen.pop()]
    rng.shuffle(chosen)
    vertical.extend(chosen[: n_v_only - 1])
    horizontal.extend(chosen[n_v_only - 1 : n_v_only - 1 + n_h_only - 1])
    if len(vertical) != n_v_only or len(horizontal) != n_h_only:
        raise AssertionError("role-color allocation failed")
    return vertical, horizontal, cross


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unsupported override(s): {', '.join(sorted(unknown))}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"override {name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _defaults_for_profile(profile, difficulty)
    frame_h = _draw_axis(ctx, "frame_h", 7, 11, *defaults["frame_h"])
    frame_w = _draw_axis(ctx, "frame_w", 8, 12, *defaults["frame_w"])
    n_v_only = _draw_axis(ctx, "n_v_only", 1, 3, *defaults["n_v_only"])
    n_h_only = _draw_axis(ctx, "n_h_only", 1, 3, *defaults["n_h_only"])
    n_cross = _draw_axis(ctx, "n_cross", 0, 1, *defaults["n_cross"])
    n_decoys = _draw_axis(ctx, "n_decoys", 0, 4, *defaults["n_decoys"])

    rng = ctx.draw_rng("layout")
    margins = defaults["margins"]
    if margins is None:
        margins = tuple(rng.randint(1, 4) for _ in range(4))
    top_margin, bottom_margin, left_margin, right_margin = margins
    height = frame_h + top_margin + bottom_margin
    width = frame_w + left_margin + right_margin
    r1, c1 = top_margin, left_margin
    r2, c2 = r1 + frame_h - 1, c1 + frame_w - 1

    grid = full_grid(height, width, 0)
    for col in range(c1, c2 + 1):
        grid[r1][col] = 5
        grid[r2][col] = 5
    for row in range(r1, r2 + 1):
        grid[row][c1] = 5
        grid[row][c2] = 5

    interior_cols = list(range(c1 + 1, c2))
    interior_rows = list(range(r1 + 1, r2))
    rng.shuffle(interior_cols)
    rng.shuffle(interior_rows)
    needed_cols = n_v_only + n_cross
    needed_rows = n_h_only + n_cross
    # The advertised ranges make these constructive preconditions invariant.
    if len(interior_cols) - needed_cols < 2 or len(interior_rows) - needed_rows < 1:
        raise ValueError("axis combination leaves no room for declared decoys")

    vertical_colors, horizontal_colors, cross_colors = _role_colors(
        rng, n_v_only, n_h_only, n_cross
    )
    vertical_cols = interior_cols[:n_v_only]
    cross_cols = interior_cols[n_v_only:needed_cols]
    free_cols = interior_cols[needed_cols:]
    horizontal_rows = interior_rows[:n_h_only]
    cross_rows = interior_rows[n_h_only:needed_rows]
    free_rows = interior_rows[needed_rows:]

    for color, col in zip(vertical_colors, vertical_cols):
        grid[r1][col] = color
        grid[r2][col] = color
    for color, row in zip(horizontal_colors, horizontal_rows):
        grid[row][c1] = color
        grid[row][c2] = color
    for color, col, row in zip(cross_colors, cross_cols, cross_rows):
        grid[r1][col] = color
        grid[r2][col] = color
        grid[row][c1] = color
        grid[row][c2] = color

    role_colors = vertical_colors + horizontal_colors + cross_colors
    if n_decoys == 1:
        grid[r1][free_cols[0]] = cross_colors[0] if cross_colors else horizontal_colors[0]
    elif n_decoys >= 2:
        # Same color on opposite borders, deliberately shifted by one column.
        # It is not an aligned pair, so the selected rule must ignore both cells.
        decoy_color = cross_colors[0] if cross_colors else horizontal_colors[0]
        grid[r1][free_cols[0]] = decoy_color
        grid[r2][free_cols[1]] = decoy_color
    if n_decoys >= 3:
        grid[free_rows[0]][c1] = vertical_colors[0]
    if n_decoys >= 4:
        # A different color on the opposite side at the same row remains inert.
        right_color = horizontal_colors[0]
        if right_color == vertical_colors[0]:
            right_color = next(color for color in role_colors if color != vertical_colors[0])
        grid[free_rows[0]][c2] = right_color

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"constructive generator violated its contract: {errors}")
    return grid


def _analyze(grid):
    errors = []
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return None, ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["cells must be integer colors 0..9"]
    height = len(grid)
    fives = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if not fives:
        return None, ["missing color-5 frame"]
    r1 = min(row for row, _ in fives)
    c1 = min(col for _, col in fives)
    r2 = max(row for row, _ in fives)
    c2 = max(col for _, col in fives)
    frame_h, frame_w = r2 - r1 + 1, c2 - c1 + 1
    if not (7 <= frame_h <= 11):
        errors.append("frame height outside 7..11")
    if not (8 <= frame_w <= 12):
        errors.append("frame width outside 8..12")
    if r1 < 1 or c1 < 1 or r2 >= height - 1 or c2 >= width - 1:
        errors.append("frame must have a positive background margin")
    if any(grid[row][col] != 0 for row in range(height) for col in range(width)
           if not (r1 <= row <= r2 and c1 <= col <= c2)):
        errors.append("cells outside the frame bbox must be background 0")
    if any(grid[row][col] != 0 for row in range(r1 + 1, r2) for col in range(c1 + 1, c2)):
        errors.append("frame interior must initially be background 0")
    if any(grid[row][col] != 5 for row, col in ((r1, c1), (r1, c2), (r2, c1), (r2, c2))):
        errors.append("frame corners must be color 5")
    if any(grid[r1][col] == 0 or grid[r2][col] == 0 for col in range(c1, c2 + 1)):
        errors.append("top/bottom border contains a zero gap")
    if any(grid[row][c1] == 0 or grid[row][c2] == 0 for row in range(r1, r2 + 1)):
        errors.append("left/right border contains a zero gap")

    vertical = {}
    horizontal = {}
    paired_cells = set()
    for col in range(c1 + 1, c2):
        color = grid[r1][col]
        if color not in (0, 5) and grid[r2][col] == color:
            vertical.setdefault(color, []).append(col)
            paired_cells.update(((r1, col), (r2, col)))
    for row in range(r1 + 1, r2):
        color = grid[row][c1]
        if color not in (0, 5) and grid[row][c2] == color:
            horizontal.setdefault(color, []).append(row)
            paired_cells.update(((row, c1), (row, c2)))
    if any(len(cols) != 1 for cols in vertical.values()):
        errors.append("a valid vertical color may define exactly one column")
    if any(len(rows) != 1 for rows in horizontal.values()):
        errors.append("a valid horizontal color may define exactly one row")

    marker_cells = {
        (row, col)
        for row, col in (
            [(r1, col) for col in range(c1 + 1, c2)]
            + [(r2, col) for col in range(c1 + 1, c2)]
            + [(row, c1) for row in range(r1 + 1, r2)]
            + [(row, c2) for row in range(r1 + 1, r2)]
        )
        if grid[row][col] not in (0, 5)
    }
    decoy_cells = marker_cells - paired_cells
    vertical_colors = set(vertical)
    horizontal_colors = set(horizontal)
    pair_colors = vertical_colors | horizontal_colors
    n_v_only = len(vertical_colors - horizontal_colors)
    n_h_only = len(horizontal_colors - vertical_colors)
    n_cross = len(vertical_colors & horizontal_colors)
    n_decoys = len(decoy_cells)
    if not (1 <= n_v_only <= 3):
        errors.append("vertical-only color count outside 1..3")
    if not (1 <= n_h_only <= 3):
        errors.append("horizontal-only color count outside 1..3")
    if not (0 <= n_cross <= 1):
        errors.append("cross color count outside 0..1")
    if not (0 <= n_decoys <= 4):
        errors.append("unmatched marker count outside 0..4")
    if decoy_cells and any(grid[row][col] not in pair_colors for row, col in decoy_cells):
        errors.append("decoy colors must reuse a valid pair color")

    info = {
        "grid_h": height,
        "grid_w": width,
        "frame_h": frame_h,
        "frame_w": frame_w,
        "frame_bounds": (r1, c1, r2, c2),
        "n_v_only": n_v_only,
        "n_h_only": n_h_only,
        "n_cross": n_cross,
        "n_decoys": n_decoys,
        "vertical_pairs": {color: tuple(cols) for color, cols in vertical.items()},
        "horizontal_pairs": {color: tuple(rows) for color, rows in horizontal.items()},
        "decoy_cells": tuple(sorted(decoy_cells)),
        "pair_colors": tuple(sorted(pair_colors)),
    }
    return info, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analyze(grid)[1]


def strict_canonical_like(grid, *, difficulty=None, meta=None):
    return self_check(grid, difficulty=difficulty, meta=meta)


def observe_overrides(grid):
    info, errors = _analyze(grid)
    if errors:
        raise ValueError(f"grid is outside generator support: {errors}")
    return {name: info[name] for name in AXES}


def _frame_bounds(grid):
    fives = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if not fives:
        raise ValueError("missing color-5 frame")
    return (
        min(row for row, _ in fives),
        min(col for _, col in fives),
        max(row for row, _ in fives),
        max(col for _, col in fives),
    )


def _border_colors(grid, bounds):
    r1, c1, r2, c2 = bounds
    values = (
        [grid[row][c1] for row in range(r1, r2 + 1)]
        + [grid[row][c2] for row in range(r1, r2 + 1)]
        + [grid[r1][col] for col in range(c1, c2 + 1)]
        + [grid[r2][col] for col in range(c1, c2 + 1)]
    )
    return sorted({value for value in values if value not in (0, 5)})


def rule_mirror(grid):
    """Independent-from-construction direct mirror of selected Racket order."""
    r1, c1, r2, c2 = _frame_bounds(grid)
    output = deepcopy(grid)
    for color in _border_colors(grid, (r1, c1, r2, c2)):
        for col in range(c1 + 1, c2):
            if grid[r1][col] == color and grid[r2][col] == color:
                for row in range(r1 + 1, r2):
                    output[row][col] = color
        for row in range(r1 + 1, r2):
            if grid[row][c1] == color and grid[row][c2] == color:
                for col in range(c1 + 1, c2):
                    output[row][col] = color
    return output


def _any_border_marker(grid):
    r1, c1, r2, c2 = _frame_bounds(grid)
    output = deepcopy(grid)
    for color in _border_colors(grid, (r1, c1, r2, c2)):
        for col in range(c1 + 1, c2):
            if grid[r1][col] == color or grid[r2][col] == color:
                for row in range(r1 + 1, r2):
                    output[row][col] = color
        for row in range(r1 + 1, r2):
            if grid[row][c1] == color or grid[row][c2] == color:
                for col in range(c1 + 1, c2):
                    output[row][col] = color
    return output


def _opposite_anywhere(grid):
    r1, c1, r2, c2 = _frame_bounds(grid)
    output = deepcopy(grid)
    for color in _border_colors(grid, (r1, c1, r2, c2)):
        top = [col for col in range(c1 + 1, c2) if grid[r1][col] == color]
        bottom = [col for col in range(c1 + 1, c2) if grid[r2][col] == color]
        if top and bottom:
            for col in sorted(set(top + bottom)):
                for row in range(r1 + 1, r2):
                    output[row][col] = color
        left = [row for row in range(r1 + 1, r2) if grid[row][c1] == color]
        right = [row for row in range(r1 + 1, r2) if grid[row][c2] == color]
        if left and right:
            for row in sorted(set(left + right)):
                for col in range(c1 + 1, c2):
                    output[row][col] = color
    return output


def _rows_always_win(grid):
    r1, c1, r2, c2 = _frame_bounds(grid)
    output = deepcopy(grid)
    colors = _border_colors(grid, (r1, c1, r2, c2))
    for color in colors:
        for col in range(c1 + 1, c2):
            if grid[r1][col] == color and grid[r2][col] == color:
                for row in range(r1 + 1, r2):
                    output[row][col] = color
    for color in colors:
        for row in range(r1 + 1, r2):
            if grid[row][c1] == color and grid[row][c2] == color:
                for col in range(c1 + 1, c2):
                    output[row][col] = color
    return output


def _columns_always_win(grid):
    r1, c1, r2, c2 = _frame_bounds(grid)
    output = deepcopy(grid)
    colors = _border_colors(grid, (r1, c1, r2, c2))
    for color in colors:
        for row in range(r1 + 1, r2):
            if grid[row][c1] == color and grid[row][c2] == color:
                for col in range(c1 + 1, c2):
                    output[row][col] = color
    for color in colors:
        for col in range(c1 + 1, c2):
            if grid[r1][col] == color and grid[r2][col] == color:
                for row in range(r1 + 1, r2):
                    output[row][col] = color
    return output


SEMANTIC_RIVALS = {
    "any_border_marker": _any_border_marker,
    "opposite_anywhere": _opposite_anywhere,
    "rows_always_win": _rows_always_win,
    "columns_always_win": _columns_always_win,
}
CANONICAL_SHORTCUTS = {
    "any_border_marker": _any_border_marker,
    "opposite_anywhere": _opposite_anywhere,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _refutes(grid, names):
    try:
        target = rule_mirror(grid)
        return not self_check(grid) and all(SEMANTIC_RIVALS[name](grid) != target for name in names)
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES = {
    "unmatched_border_markers": lambda grid: (
        not self_check(grid)
        and observe_overrides(grid)["n_decoys"] > 0
        and _refutes(grid, ("any_border_marker",))
    ),
    "misaligned_same_color": lambda grid: (
        not self_check(grid)
        and observe_overrides(grid)["n_decoys"] >= 2
        and _refutes(grid, ("opposite_anywhere",))
    ),
    "mixed_crossing_priority": lambda grid: _refutes(
        grid, ("rows_always_win", "columns_always_win")
    ),
}
WITNESS_RIVALS = {
    "unmatched_border_markers": ("any_border_marker",),
    "misaligned_same_color": ("opposite_anywhere",),
    "mixed_crossing_priority": ("rows_always_win", "columns_always_win"),
}


def lesson_identifiable(demos, query):
    """Reject a lesson only when a declared rival fits demos but changes query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            reasons.append(f"malformed lesson for {name}: {exc}")
            continue
        if fits and changes_query:
            reasons.append(f"declared rival {name} fits every demo but changes the query")
    return reasons
