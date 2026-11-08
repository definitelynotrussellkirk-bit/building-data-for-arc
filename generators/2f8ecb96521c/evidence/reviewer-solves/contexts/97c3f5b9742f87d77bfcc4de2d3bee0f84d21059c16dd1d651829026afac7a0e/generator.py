"""Input generator for ARC task 694f12f3 / selected task 2f8ecb96521c.

The selected Racket rule finds the two color-4 connected components, orders them
by area, and recolors only their strict bounding-box interiors: smaller -> 1,
larger -> 2.  This module generates inputs only.  Its executable semantic rivals
are curriculum diagnostics, not label authorities.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "2f8ecb96521c"
TASK_ID = GENERATOR_ID
RULE_HASH = "32d5e32db8fe"
VERSION = "2.0.0"
SUMMARY = (
    "Exactly two separated solid color-4 rectangles of distinct area, each at "
    "least 3x3. The selected rule fills the smaller strict interior with 1 and "
    "the larger strict interior with 2 while preserving both color-4 borders."
)
EXPECTED_OUTPUT_CODOMAIN = 4

INVARIANTS = [
    "the input palette is exactly a subset of {0,4}",
    "there are exactly two 4-connected solid color-4 rectangles",
    "both rectangles are at least 3x3 and have distinct areas",
    "generated rectangles have at least one blank row or column between them",
]

SMALL_SHAPES = ("3x3", "3x4", "4x3")
LARGE_SHAPES = ("3x5", "5x3", "4x4", "5x5")
LAYOUTS = ("stacked", "side_by_side", "diagonal")
SMALL_ROLES = ("near", "far")

AXES = {
    "grid_h": {"type": "int", "default": "weighted 10..14; favors 10", "valid": "10..14"},
    "grid_w": {"type": "int", "default": "weighted 10..14; favors 10", "valid": "10..14"},
    "small_shape": {"type": "str", "default": "keyed choice", "valid": "3x3|3x4|4x3"},
    "large_shape": {"type": "str", "default": "keyed choice", "valid": "3x5|5x3|4x4|5x5"},
    "layout": {"type": "str", "default": "five-step teaching schedule", "valid": "stacked|side_by_side|diagonal"},
    "small_role": {"type": "str", "default": "five-step teaching schedule", "valid": "near|far"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
DEGENERATE_TEXTURES = ()
LAWFUL_DEGENERATE_TEXTURES = ()

# Four demonstrations plus one query occupy five consecutive sample indices.
# Stacked and side-by-side each occur twice, and `small_role=far` occurs twice,
# so holding out any one pair still leaves a counterexample to each named
# projection/position shortcut.
EXAMPLES_NEEDED = 4
SCHEDULE_CYCLE = 5
SCHEDULE_PROFILES = ("stacked:near", "side_by_side:far", "diagonal:near")
_SCHEDULE = (
    ("stacked", "near"),
    ("side_by_side", "far"),
    ("stacked", "near"),
    ("side_by_side", "far"),
    ("diagonal", "near"),
)

_SHAPE_DIMS = {
    "3x3": (3, 3),
    "3x4": (3, 4),
    "4x3": (4, 3),
    "3x5": (3, 5),
    "5x3": (5, 3),
    "4x4": (4, 4),
    "5x5": (5, 5),
}
_GRID_CHOICES = (10,) * 16 + (11, 12, 13, 14)
_DIFFICULTY_CHOICES = (None, "easy", "medium", "hard")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the default semantic profile at ``sample_index``.

    ``seed`` and ``difficulty`` are accepted for the shared schedule API; the
    profile itself is deliberately index-periodic so every cyclic start can be
    exhaustively checked.
    """
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _DIFFICULTY_CHOICES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    layout, role = _SCHEDULE[sample_index % SCHEDULE_CYCLE]
    return f"{layout}:{role}"


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _DIFFICULTY_CHOICES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in ("grid_h", "grid_w"):
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer (not bool)")
            if not 10 <= value <= 14:
                raise ValueError(f"{name} must be in 10..14")
        elif name == "small_shape":
            if type(value) is not str or value not in SMALL_SHAPES:
                raise ValueError(f"small_shape must be one of {SMALL_SHAPES}")
        elif name == "large_shape":
            if type(value) is not str or value not in LARGE_SHAPES:
                raise ValueError(f"large_shape must be one of {LARGE_SHAPES}")
        elif name == "layout":
            if type(value) is not str or value not in LAYOUTS:
                raise ValueError(f"layout must be one of {LAYOUTS}")
        elif name == "small_role":
            if type(value) is not str or value not in SMALL_ROLES:
                raise ValueError(f"small_role must be one of {SMALL_ROLES}")


def _weighted_shapes(difficulty):
    if difficulty == "easy":
        return (
            SMALL_SHAPES + ("3x3",) * 3,
            LARGE_SHAPES + ("3x5", "4x4", "5x5"),
        )
    if difficulty == "hard":
        return (
            SMALL_SHAPES + ("3x4", "4x3"),
            LARGE_SHAPES + ("5x3", "4x4", "5x5") * 2,
        )
    return SMALL_SHAPES, LARGE_SHAPES


def _intervals_overlap(start_a, length_a, start_b, length_b):
    return max(start_a, start_b) <= min(
        start_a + length_a - 1, start_b + length_b - 1
    )


def _legal_placements(h, w, near_size, far_size, layout):
    """Enumerate all constructive near/far top-left placements."""
    nh, nw = near_size
    fh, fw = far_size
    placements = []
    for nr in range(h - nh + 1):
        for nc in range(w - nw + 1):
            for fr in range(h - fh + 1):
                for fc in range(w - fw + 1):
                    if layout == "stacked":
                        lawful = (
                            nr + nh + 1 <= fr
                            and _intervals_overlap(nc, nw, fc, fw)
                        )
                    elif layout == "side_by_side":
                        # Keep the near rectangle first in row-major order as
                        # well as leftmost.  Then small_role="far" is a real,
                        # deterministic counterexample to a first-object rule.
                        lawful = (
                            nc + nw + 1 <= fc
                            and nr <= fr
                            and _intervals_overlap(nr, nh, fr, fh)
                        )
                    else:  # diagonal: near is north-west, far is south-east
                        lawful = nr + nh + 1 <= fr and nc + nw + 1 <= fc
                    if lawful:
                        placements.append(((nr, nc), (fr, fc)))
    return placements


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    scheduled_layout, scheduled_role = _SCHEDULE[
        sample_index % SCHEDULE_CYCLE
    ]
    effective = dict(overrides)
    if effective.get("layout") is None:
        effective["layout"] = scheduled_layout
    if effective.get("small_role") is None:
        effective["small_role"] = scheduled_role

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_choice("grid_h", _GRID_CHOICES)
    w = ctx.draw_choice("grid_w", _GRID_CHOICES)
    small_choices, large_choices = _weighted_shapes(difficulty)
    small_shape = ctx.draw_choice("small_shape", small_choices)
    large_shape = ctx.draw_choice("large_shape", large_choices)
    layout = ctx.draw_choice("layout", LAYOUTS)
    small_role = ctx.draw_choice("small_role", SMALL_ROLES)

    small_size = _SHAPE_DIMS[small_shape]
    large_size = _SHAPE_DIMS[large_shape]
    if small_role == "near":
        near_size, far_size = small_size, large_size
    else:
        near_size, far_size = large_size, small_size
    placements = _legal_placements(h, w, near_size, far_size, layout)
    if not placements:
        raise RuntimeError(
            f"no constructive placement for {h}x{w}, {small_shape}, "
            f"{large_shape}, {layout}, {small_role}"
        )
    near_pos, far_pos = ctx.draw_rng("placement").choice(placements)
    if small_role == "near":
        small_pos, large_pos = near_pos, far_pos
    else:
        large_pos, small_pos = near_pos, far_pos

    grid = full_grid(h, w, 0)
    draw_rect(grid, small_pos[0], small_pos[1], small_size[0], small_size[1], 4)
    draw_rect(grid, large_pos[0], large_pos[1], large_size[0], large_size[1], 4)
    findings = self_check(grid)
    if findings:
        raise RuntimeError("constructive generator violated its contract: " + "; ".join(findings))
    return grid


def _components4(grid, color=4):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != color or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _analysis(grid):
    components = _components4(grid, 4)
    rows = []
    for cells in components:
        r1, c1, r2, c2 = _bbox(cells)
        rows.append(
            {
                "cells": cells,
                "area": len(cells),
                "r1": r1,
                "c1": c1,
                "r2": r2,
                "c2": c2,
                "h": r2 - r1 + 1,
                "w": c2 - c1 + 1,
            }
        )
    return rows


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["every row must be a sequence"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    bad_values = sorted(
        {
            value
            for row in grid
            for value in row
            if type(value) is not int or value not in (0, 4)
        },
        key=repr,
    )
    if bad_values:
        errors.append(f"input values must be integer colors 0 or 4, got {bad_values[:5]}")
        return errors

    components = _analysis(grid)
    if len(components) != 2:
        errors.append(f"expected exactly two color-4 components, got {len(components)}")
    for index, component in enumerate(components):
        if component["h"] < 3 or component["w"] < 3:
            errors.append(f"component {index} must be at least 3x3")
        if component["area"] != component["h"] * component["w"]:
            errors.append(f"component {index} must be a solid rectangle")
    if len(components) == 2 and components[0]["area"] == components[1]["area"]:
        errors.append("the two color-4 rectangles must have distinct areas")
    return errors


def strict_canonical_like(grid):
    """The strict task manifold is the complete lawful two-rectangle domain."""
    return self_check(grid)


MIN_STRICT_FRAC = 1.0


def _layout_and_role(rows):
    small, large = sorted(rows, key=lambda row: row["area"])
    row_separated = small["r2"] < large["r1"] or large["r2"] < small["r1"]
    col_separated = small["c2"] < large["c1"] or large["c2"] < small["c1"]
    if row_separated and col_separated:
        layout = "diagonal"
        small_near = small["r1"] < large["r1"] and small["c1"] < large["c1"]
    elif row_separated:
        layout = "stacked"
        small_near = small["r1"] < large["r1"]
    elif col_separated:
        layout = "side_by_side"
        small_near = small["c1"] < large["c1"]
    else:
        raise ValueError("rectangles overlap in both row and column projections")
    return layout, ("near" if small_near else "far"), small, large


def observe_overrides(grid):
    findings = self_check(grid)
    if findings:
        raise ValueError("cannot observe invalid grid: " + "; ".join(findings))
    layout, small_role, small, large = _layout_and_role(_analysis(grid))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "small_shape": f"{small['h']}x{small['w']}",
        "large_shape": f"{large['h']}x{large['w']}",
        "layout": layout,
        "small_role": small_role,
    }


# ---------------------------------------------------------------------------
# Executable semantic diagnostics.  These never generate labels.


def _paint_interiors(grid, ordered_rows, colors):
    output = deepcopy(grid)
    for row, color in zip(ordered_rows, colors):
        for r in range(row["r1"] + 1, row["r2"]):
            for c in range(row["c1"] + 1, row["c2"]):
                output[r][c] = color
    return output


def _expected_output(grid):
    return _paint_interiors(
        grid, sorted(_analysis(grid), key=lambda row: row["area"]), (1, 2)
    )


def _occupied_runs(flags):
    runs = []
    start = None
    for index, present in enumerate(list(flags) + [False]):
        if present and start is None:
            start = index
        elif not present and start is not None:
            runs.append((start, index - 1))
            start = None
    return runs


def _projection_rival(grid, axis):
    h, w = len(grid), len(grid[0])
    count = w if axis == "column" else h
    flags = []
    for index in range(count):
        flags.append(
            any(
                grid[r][c] == 4
                for r in range(h)
                for c in range(w)
                if (c if axis == "column" else r) == index
            )
        )
    runs = _occupied_runs(flags)
    if len(runs) != 2:
        return deepcopy(grid)
    groups = []
    for lo, hi in runs:
        cells = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if grid[r][c] == 4 and lo <= (c if axis == "column" else r) <= hi
        ]
        r1, c1, r2, c2 = _bbox(cells)
        groups.append(
            {
                "cells": cells,
                "area": len(cells),
                "r1": r1,
                "c1": c1,
                "r2": r2,
                "c2": c2,
                "h": r2 - r1 + 1,
                "w": c2 - c1 + 1,
            }
        )
    return _paint_interiors(grid, sorted(groups, key=lambda row: row["area"]), (1, 2))


def _column_projection(grid):
    return _projection_rival(grid, "column")


def _row_projection(grid):
    return _projection_rival(grid, "row")


def _position_order(grid):
    return _paint_interiors(
        grid, sorted(_analysis(grid), key=lambda row: (row["r1"], row["c1"])), (1, 2)
    )


def _same_color(grid):
    return _paint_interiors(grid, _analysis(grid), (1, 1))


def _reverse_area(grid):
    return _paint_interiors(
        grid, sorted(_analysis(grid), key=lambda row: row["area"], reverse=True), (1, 2)
    )


SEMANTIC_RIVALS: dict[str, Callable] = {
    "column_projection": _column_projection,
    "row_projection": _row_projection,
    "position_order": _position_order,
    "same_color": _same_color,
    "reverse_area": _reverse_area,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {}


def _is_stacked(grid):
    return observe_overrides(grid)["layout"] == "stacked"


def _is_side_by_side(grid):
    return observe_overrides(grid)["layout"] == "side_by_side"


def _small_is_far(grid):
    return observe_overrides(grid)["small_role"] == "far"


def _ranked_interiors_visible(grid):
    return not self_check(grid) and _expected_output(grid) != grid


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "column_overlap_refutes_column_projection": _is_stacked,
    "row_overlap_refutes_row_projection": _is_side_by_side,
    "smaller_is_later_refutes_position_order": _small_is_far,
    "ranked_interiors_use_distinct_colors": _ranked_interiors_visible,
}
WITNESS_RIVALS = {
    "column_overlap_refutes_column_projection": ["column_projection"],
    "row_overlap_refutes_row_projection": ["row_projection"],
    "smaller_is_later_refutes_position_order": ["position_order"],
    "ranked_interiors_use_distinct_colors": ["same_color", "reverse_area"],
}


def _pair_errors(pair, label):
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    findings = self_check(pair["input"])
    if findings:
        return [f"{label} input: {finding}" for finding in findings]
    if pair["output"] != _expected_output(pair["input"]):
        return [f"{label} output disagrees with area-ranked interior recoloring"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}"))
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
        return reasons
    query_findings = self_check(query["input"])
    reasons.extend(f"query input: {finding}" for finding in query_findings)
    if reasons:
        return reasons
    expected_query = _expected_output(query["input"])
    if query.get("output") is not None and query["output"] != expected_query:
        reasons.append("query output disagrees with area-ranked interior recoloring")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != expected_query:
                reasons.append(
                    f"demonstrations remain consistent with shortcut: {name}"
                )
    return reasons
