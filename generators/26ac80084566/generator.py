"""Cast row-wise horizontal shadows toward a full-height color-8 wall.

The canonical program is authoritative. This module samples its intended grammar:
black background, one interior vertical wall, and one connected monochrome shape
separated from the wall. A shadow keeps each occupied row's own farthest extent.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = TASK_ID = "26ac80084566"
VERSION = "2.0.0"
RULE_HASH = "4397ca98d7a5"
SUMMARY = "A colored shape casts row-wise horizontal shadows toward a movable vertical 8-wall from either side."
INVARIANTS = [
    "literal-0 background and one interior full-height color-8 wall",
    "one connected monochrome nonzero, non-8 shape entirely on one side",
    "at least one empty column separates the shape from the wall",
    "sampled templates contain 3..8 cells; validation accepts other connected shapes",
    "each occupied row fills from its farthest shape cell toward the wall",
]
PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = PALETTE_KINDS
DEGENERATE_TEXTURES = ("no_line", "no_shape", "shape_touching_line")
_PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 9),
    "warm": (2, 4, 6, 9),
    "cool": (1, 3, 5, 7),
    "varied": (1, 2, 3, 4, 5, 6, 7, 9),
}
AXES = {
    "grid_h": {"type": "int", "default": "easy 5..9; medium 9..18; hard 18..30", "valid": "4..30"},
    "grid_w": {"type": "int", "default": "easy 7..12; medium 10..22; hard 18..30", "valid": "6..30"},
    "shape_idx": {"type": "int", "default": "scheduled rich or varied template", "valid": "0..7"},
    "side": {"type": "str", "default": "scheduled left/right", "valid": "left|right"},
    "wall_col": {"type": "int", "default": "uniform over feasible interior columns", "valid": "1..grid_w-2, subject to shape and gap"},
    "gap": {"type": "int", "default": "1..4, conditioned on width, shape, and any pinned wall", "valid": "1..8, subject to fit"},
    "shape_row": {"type": "int", "default": "uniform over feasible rows", "valid": "0..grid_h-shape_height"},
    "shape_color": {"type": "int", "default": "rich slots use 9 when available; varied slots draw below 8", "valid": "1|2|3|4|5|6|7|9, within palette_kind"},
    "palette_kind": {"type": "str", "default": "default", "valid": "|".join(PALETTE_KINDS)},
    "palette_size": {"type": "int", "default": "1 foreground color", "valid": "1..1"},
    "n_distinct_colors": {"type": "int", "default": "2 nonzero colors including wall", "valid": "2..2"},
    "position_bias": {"type": "str", "default": "8line_divides_shape_offset", "valid": "8line_divides_shape_offset"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}
# Preserve the original four indices; add the six-cell canonical query and
# concave shapes. Rich profiles have varying extrema on both sides.
_SHAPES = (
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
)
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("left_rich", "right_rich", "left_varied", "right_varied")


def schedule_profile(seed, sample_index, difficulty=None):
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise ValueError("seed must be an integer; sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    return SCHEDULE_PROFILES[(seed + sample_index) % len(SCHEDULE_PROFILES)]


def _grid_errors(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        return ["grid must be a list containing 1..30 rows"]
    if any(type(row) is not list or not 1 <= len(row) <= 30 for row in grid):
        return ["each row must be a list containing 1..30 cells"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integers in 0..9 (not booleans)"]
    return []


def _analysis(grid):
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    walls = [col for col in range(w) if all(row[col] == 8 for row in grid)]
    if len(walls) != 1:
        return {"errors": ["expected exactly one full-height color-8 column"]}
    wall = walls[0]
    if not 0 < wall < w - 1:
        errors.append("wall must be an interior column")
    if any(value == 8 and col != wall for row in grid for col, value in enumerate(row)):
        errors.append("color 8 may occur only on the wall")
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, 8)]
    if not cells:
        return {"errors": errors + ["foreground shape must be nonempty"]}
    colors = {grid[r][c] for r, c in cells}
    if len(colors) != 1:
        errors.append("foreground must have exactly one color")
    side = "left" if all(c < wall for _, c in cells) else "right" if all(c > wall for _, c in cells) else None
    if side is None:
        errors.append("foreground must lie entirely on one side of the wall")
    remaining = set(cells)
    stack = [remaining.pop()]
    while stack:
        r, c = stack.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in remaining:
                remaining.remove(neighbor)
                stack.append(neighbor)
    if remaining:
        errors.append("foreground must be one 4-connected component")
    gap = wall - max(c for _, c in cells) - 1 if side == "left" else min(c for _, c in cells) - wall - 1
    if side is not None and gap < 1:
        errors.append("foreground must be separated from the wall by at least one empty column")
    return {"errors": errors, "height": h, "width": w, "wall": wall,
            "cells": cells, "color": grid[cells[0][0]][cells[0][1]], "side": side, "gap": gap}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the intended input grammar, not the narrower template catalog."""
    return _analysis(grid)["errors"]


def strict_canonical_like(grid, **kwargs) -> list[str]:
    return self_check(grid, **kwargs)


def _geometry(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return info


def _blank_with_wall(info):
    output = [[0] * info["width"] for _ in range(info["height"])]
    for row in output:
        row[info["wall"]] = 8
    return output


def _row_shadow(grid, direction=None):
    info = _geometry(grid)
    output = _blank_with_wall(info)
    direction = direction or ("right" if info["side"] == "left" else "left")
    for r in sorted({r for r, _ in info["cells"]}):
        columns = [c for rr, c in info["cells"] if rr == r]
        span = range(min(columns), info["wall"]) if direction == "right" else range(info["wall"] + 1, max(columns) + 1)
        for c in span:
            output[r][c] = info["color"]
    return output


def rule_mirror(grid):
    """Small audit oracle; canonical Racket, not this helper, supplies labels."""
    return _row_shadow(grid)


def _bbox_fill(grid):
    info = _geometry(grid)
    output = _blank_with_wall(info)
    rows, cols = zip(*info["cells"])
    span = range(min(cols), info["wall"]) if info["side"] == "left" else range(info["wall"] + 1, max(cols) + 1)
    for r in range(min(rows), max(rows) + 1):
        for c in span:
            output[r][c] = info["color"]
    return output


def _always_right(grid):
    return _row_shadow(grid, "right")


def _always_left(grid):
    return _row_shadow(grid, "left")


def _identity(grid):
    _geometry(grid)
    return [row[:] for row in grid]


def _lowest_color_only(grid):
    info = _geometry(grid)
    return rule_mirror(grid) if info["color"] < 8 else _identity(grid)


def _highest_color_only(grid):
    info = _geometry(grid)
    return rule_mirror(grid) if info["color"] > 8 else _identity(grid)


def _whole_side_rows(grid):
    info = _geometry(grid)
    output = _blank_with_wall(info)
    span = range(info["wall"]) if info["side"] == "left" else range(info["wall"] + 1, info["width"])
    for r in {r for r, _ in info["cells"]}:
        for c in span:
            output[r][c] = info["color"]
    return output


SEMANTIC_RIVALS = {
    "bbox_fill": _bbox_fill, "always_right": _always_right,
    "always_left": _always_left, "identity": _identity,
    "whole_side_rows": _whole_side_rows,
    "lowest_color_only": _lowest_color_only,
    "highest_color_only": _highest_color_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_report(demos, query):
    """Compare actual demos and query input against a declared finite rival set.

    Never reads query.output. Distinct surviving programs may pass if their query
    predictions agree. This is not a proof against all possible ARC programs.
    """
    report = {"errors": [], "survivors": [], "query_prediction_count": 0,
              "scope": f"intended rule plus {len(LESSON_COMPETITORS)} declared rivals"}
    if type(demos) is not list or not demos:
        report["errors"].append("at least one labeled demonstration is required")
        return report
    if type(query) is not dict or "input" not in query:
        report["errors"].append("query must contain an input grid")
        return report
    for index, pair in enumerate(demos):
        if type(pair) is not dict or "input" not in pair or "output" not in pair:
            report["errors"].append(f"demo {index} must contain input and output grids")
            continue
        if self_check(pair["input"]) or _grid_errors(pair["output"]):
            report["errors"].append(f"demo {index} has an invalid input or output")
        elif rule_mirror(pair["input"]) != pair["output"]:
            report["errors"].append(f"demo {index} disagrees with the intended rule")
    report["errors"].extend(self_check(query["input"]))
    if report["errors"]:
        return report
    predictions = []
    for name, function in {"intended": rule_mirror, **LESSON_COMPETITORS}.items():
        try:
            if all(function(pair["input"]) == pair["output"] for pair in demos):
                prediction = function(query["input"])
                report["survivors"].append(name)
                if prediction not in predictions:
                    predictions.append(prediction)
        except Exception as exc:
            report["errors"].append(f"rival {name} could not be evaluated: {type(exc).__name__}")
    report["query_prediction_count"] = len(predictions)
    if len(predictions) != 1:
        report["errors"].append(f"demonstrations leave {len(predictions)} distinct query predictions")
    return report


def lesson_identifiable(demos, query) -> list[str]:
    return lesson_report(demos, query)["errors"]


def _left(grid):
    return not self_check(grid) and _geometry(grid)["side"] == "left"


def _right(grid):
    return not self_check(grid) and _geometry(grid)["side"] == "right"


def _row_specific(grid):
    return not self_check(grid) and rule_mirror(grid) != _bbox_fill(grid)


SEMANTIC_WITNESSES = {"left_side": _left, "right_side": _right, "row_specific_shadow": _row_specific}
BRANCH_WITNESSES = {"left_side": _left, "right_side": _right}
WITNESS_RIVALS = {"row_specific_shadow": ["bbox_fill"]}


def observe_overrides(grid):
    info = _geometry(grid)
    top = min(r for r, _ in info["cells"])
    left = min(c for _, c in info["cells"])
    shape = {(r - top, c - left) for r, c in info["cells"]}
    result = {"grid_h": info["height"], "grid_w": info["width"], "wall_col": info["wall"],
              "side": info["side"], "gap": info["gap"], "shape_row": top,
              "shape_color": info["color"], "palette_size": 1, "n_distinct_colors": 2}
    for index, template in enumerate(_SHAPES):
        if shape == set(template):
            result["shape_idx"] = index
            break
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    profile = schedule_profile(seed, sample_index, difficulty)
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(sorted(unknown))}")
    for name, value in overrides.items():
        required = int if AXES[name]["type"] == "int" else str
        if type(value) is not required:
            raise ValueError(f"{name} must be an exact {required.__name__}")
    normalized = dict(overrides)
    texture = normalized.get("texture")
    if texture is not None and texture not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError("unknown texture")
    if texture in HELPFUL_TEXTURES:
        if "palette_kind" in normalized and normalized["palette_kind"] != texture:
            raise ValueError("texture palette alias conflicts with palette_kind")
        normalized["palette_kind"] = texture
    # Normalize aliases before all keyed draws; no spelling-dependent layout.
    normalized["texture"] = texture if texture in DEGENERATE_TEXTURES else normalized.get("palette_kind", "default")
    band = difficulty or "medium"
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=band, overrides=normalized)
    h_ranges = {"easy": (5, 9), "medium": (9, 18), "hard": (18, 30)}
    w_ranges = {"easy": (7, 12), "medium": (10, 22), "hard": (18, 30)}
    h = ctx.draw_int_strict("grid_h", *( (4, 30) if "grid_h" in normalized else h_ranges[band]))
    w = ctx.draw_int_strict("grid_w", *( (6, 30) if "grid_w" in normalized else w_ranges[band]))
    shape_options = tuple(range(len(_SHAPES))) if "shape_idx" in normalized or profile.endswith("varied") else (0, 4)
    shape_idx = ctx.draw_choice("shape_idx", shape_options)
    side = ctx.draw_choice("side", ("left", "right") if "side" in normalized else (profile.split("_")[0],))
    palette = ctx.draw_choice("palette_kind", PALETTE_KINDS if "palette_kind" in normalized else ("default",))
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES)
    ctx.draw_int_strict("palette_size", 1, 1)
    ctx.draw_int_strict("n_distinct_colors", 2, 2)
    ctx.draw_choice("position_bias", ("8line_divides_shape_offset",))
    ctx.draw_choice("density", ("sparse",))
    colors = _PALETTES[palette]
    if "shape_color" not in normalized and 9 in colors:
        # In any three consecutive default draws, both color orders relative
        # to the 8-wall occur. Both survive a holdout from a complete four-slot
        # block. A cool-only palette has no color above 8; its support is local.
        colors = (9,) if profile.endswith("rich") else tuple(c for c in colors if c < 8)
    color = ctx.draw_choice("shape_color", colors)
    shape = _SHAPES[shape_idx]
    shape_h = 1 + max(r for r, _ in shape)
    shape_w = 1 + max(c for _, c in shape)
    gap_max = 8 if "gap" in normalized else min(4, w - shape_w - 2)
    if "gap" not in normalized and "wall_col" in normalized:
        # A feasible pinned wall must not be rejected because an omitted gap
        # happened to be sampled too large. Explicit gaps still fail on conflict.
        pinned_wall = normalized["wall_col"]
        available = pinned_wall - shape_w if side == "left" else w - pinned_wall - shape_w - 1
        gap_max = min(gap_max, available)
    if gap_max < 1:
        raise ValueError("selected shape cannot fit beside the requested wall with a positive gap")
    gap = ctx.draw_int_strict("gap", 1, gap_max)
    wall_lo, wall_hi = (shape_w + gap, w - 2) if side == "left" else (1, w - shape_w - gap - 1)
    if wall_lo > wall_hi:
        raise ValueError("shape, gap, and interior wall do not fit the requested width")
    wall = ctx.draw_int_strict("wall_col", wall_lo, wall_hi)
    top = ctx.draw_int_strict("shape_row", 0, h - shape_h)
    left = wall - gap - shape_w if side == "left" else wall + gap + 1
    grid = [[0] * w for _ in range(h)]
    for row in grid:
        row[wall] = 8
    for r, c in shape:
        grid[top + r][left + c] = color
    if texture == "no_line":
        for row in grid:
            row[wall] = 0
    elif texture in ("no_shape", "shape_touching_line"):
        for r, c in shape:
            grid[top + r][left + c] = 0
        if texture == "shape_touching_line":
            col = wall - 1 if side == "left" else wall + 1
            for r in range(top, min(h, top + 3)):
                grid[r][col] = color
    elif self_check(grid):
        raise ValueError("internal generator error: " + "; ".join(self_check(grid)))
    return grid
