"""Semantic generator for ARC task 5b18a320e97b.

Ignore background zero and gray (5).  If every remaining color occupies one
row, order those colors by row and emit an N x N grid of solid color rows.
Otherwise, order the colors by the column of their first cell and emit an
N x N grid whose every row is that ordered color list.  The canonical gray
N x N square may occlude and split the visible colored lines.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "5b18a320e97b"
TASK_ID = "5b18a320e97b"
VERSION = "4.0.0"
RULE_HASH = "9a2961f7f72d"
SUMMARY = "Ignore the gray square, order visible line colors along their common orientation, and emit the ordered colors as an N x N stripe grid."
INVARIANTS = [
    "zero is background and gray (5) is ignored by the ordering rule",
    "two through seven distinct non-gray colors define the output size",
    "horizontal scenes place each line color on exactly one distinct row",
    "vertical scenes place each line color on exactly one distinct column",
    "the gray square has side length equal to the number of line colors",
    "gray and its zero moat may occlude or split a colored line without changing its order key",
    "horizontal outputs use solid ordered rows and vertical outputs repeat the ordered color columns",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "horizontal_n2",
    "horizontal_n3",
    "horizontal_n4",
    "horizontal_n5",
    "horizontal_n6",
    "horizontal_n7",
    "vertical_n2",
    "vertical_n3",
    "vertical_n4",
    "vertical_n5",
    "vertical_n6",
    "vertical_n7",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and twelve recoverable orientation/count lessons",
        "valid": "public_1|public_2|public_3|public_4|horizontal_n2|horizontal_n3|horizontal_n4|horizontal_n5|horizontal_n6|horizontal_n7|vertical_n2|vertical_n3|vertical_n4|vertical_n5|vertical_n6|vertical_n7",
    }
}

_PUBLIC_ROWS = (
    "0000020040/0555020040/0555020040/0555020040/0000020040/0010020040/0010020040/0010020040/0010020040/0010020040/0010020040/0010020040",
    "000000000000000/000000000000000/222222222222222/000000000000000/000000000000000/111111111111111/000000000000000/000000000000000/333333333333333/000000000000000/055555500000000/055555504444444/055555500000000/055555500000000/055555508888888/055555500000000/000000000000000/666666666666666",
    "000000000000/222220555502/000000555500/000000555500/888880555508/000000000000/000000000000/444444444444/000000000000/000000000000/111111111111/000000000000",
    "2222222000000000222/0000000055555550000/0000000055555550000/3333333055555550333/0000000055555550000/0000000055555550000/8888888055555550888/0000000055555550000/0000000000000000000/4444444444444444444/0000000000000000000/0000000000000000000/6666666666666666666/0000000000000000000/0000000000000000000/1111111111111111111/0000000000000000000/0000000000000000000/7777777777777777777",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 7 <= len(grid) <= 30 or not 7 <= width <= 30:
        return ["input dimensions must be between 7 and 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["input cells must be literal integers from zero through nine"]
    return []


def _line_cells_by_color(grid):
    colors = sorted({value for row in grid for value in row if value not in (0, 5)})
    return {
        color: tuple((row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == color)
        for color in colors
    }


def _orientation(cells_by_color):
    horizontal = all(len({row for row, _ in cells}) == 1 for cells in cells_by_color.values())
    return "horizontal" if horizontal else "vertical"


def _ordered_colors(cells_by_color, orientation):
    axis = 0 if orientation == "horizontal" else 1
    return tuple(sorted(cells_by_color, key=lambda color: cells_by_color[color][0][axis]))


def _apply_rule(grid, cells_by_color):
    orientation = _orientation(cells_by_color)
    ordered = _ordered_colors(cells_by_color, orientation)
    size = len(ordered)
    if orientation == "horizontal":
        output = [[ordered[row] for _ in range(size)] for row in range(size)]
    else:
        output = [list(ordered) for _ in range(size)]
    return output, orientation, ordered


def rule_mirror(grid):
    """Exact Python mirror of canonical orientation detection and ordering."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    cells_by_color = _line_cells_by_color(grid)
    if not cells_by_color:
        raise ValueError("no non-gray line colors")
    return _apply_rule(grid, cells_by_color)[0]


def _gray_square(grid, expected_side):
    gray = [(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 5]
    if not gray:
        return None
    row0, row1 = min(row for row, _ in gray), max(row for row, _ in gray)
    col0, col1 = min(col for _, col in gray), max(col for _, col in gray)
    if row1 - row0 + 1 != expected_side or col1 - col0 + 1 != expected_side:
        return None
    if len(gray) != expected_side * expected_side:
        return None
    if any(grid[row][col] != 5 for row in range(row0, row1 + 1) for col in range(col0, col1 + 1)):
        return None
    return row0, col0, expected_side


def _profile_for(grid, orientation, count):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    candidate = f"{orientation}_n{count}"
    return candidate if candidate in GENERAL_PROFILES else None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    cells_by_color = _line_cells_by_color(grid)
    count = len(cells_by_color)
    if not 2 <= count <= 7:
        errors.append("exactly two through seven non-gray line colors are required")
    if any(not cells for cells in cells_by_color.values()):
        errors.append("every declared line color must be visible")
    orientation = _orientation(cells_by_color) if cells_by_color else None
    if orientation == "horizontal":
        axes = [next(iter({row for row, _ in cells})) for cells in cells_by_color.values()]
        if len(set(axes)) != len(axes):
            errors.append("horizontal line colors must occupy distinct rows")
    elif orientation == "vertical":
        if any(len({col for _, col in cells}) != 1 for cells in cells_by_color.values()):
            errors.append("non-horizontal scenes must place each line color in one column")
        axes = [next(iter({col for _, col in cells})) for cells in cells_by_color.values() if len({col for _, col in cells}) == 1]
        if len(set(axes)) != len(cells_by_color):
            errors.append("vertical line colors must occupy distinct columns")
    if any(len(cells) < 2 for cells in cells_by_color.values()):
        errors.append("every line color must retain at least two visible cells after occlusion")
    gray_square = _gray_square(grid, count)
    if gray_square is None:
        errors.append("gray cells must form one N by N square where N is the line-color count")
    output, detected_orientation, ordered = _apply_rule(grid, cells_by_color) if cells_by_color else (None, None, ())
    profile = _profile_for(grid, detected_orientation, count) if cells_by_color else None
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared orientation/count profile")
    facts = {
        "cells_by_color": cells_by_color,
        "orientation": detected_orientation,
        "ordered_colors": ordered,
        "gray_square": gray_square,
        "scene_profile": profile,
    }
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _dimension_limits(difficulty):
    if difficulty == "easy":
        return 10, 14
    if difficulty == "medium":
        return 14, 20
    if difficulty == "hard":
        return 20, 28
    return 12, 22


def _gray_origin(orientation, axes, side, height, width, rng):
    occlude = rng.random() < 0.75
    if orientation == "horizontal" and occlude:
        target = rng.choice(axes)
        row0 = max(1, min(height - side - 1, target - rng.randint(0, side - 1)))
    else:
        row0 = rng.randint(1, height - side - 1)
    if orientation == "vertical" and occlude:
        target = rng.choice(axes)
        col0 = max(1, min(width - side - 1, target - rng.randint(0, side - 1)))
    else:
        col0 = rng.randint(1, width - side - 1)
    return row0, col0


def _general_scene(profile, difficulty, rng):
    orientation, count_text = profile.split("_n")
    count = int(count_text)
    low, high = _dimension_limits(difficulty)
    low = max(low, count + 4)
    for _ in range(100):
        height, width = rng.randint(low, high), rng.randint(low, high)
        grid = [[0 for _ in range(width)] for _ in range(height)]
        colors = rng.sample((1, 2, 3, 4, 6, 7, 8, 9), count)
        axis_size = height if orientation == "horizontal" else width
        axes = sorted(rng.sample(range(axis_size), count))
        for axis, color in zip(axes, colors):
            span = width if orientation == "horizontal" else height
            length = span if rng.random() < 0.5 else rng.randint(max(3, span // 2), span)
            start = rng.randint(0, span - length)
            for offset in range(start, start + length):
                row, col = (axis, offset) if orientation == "horizontal" else (offset, axis)
                grid[row][col] = color
        gray_row, gray_col = _gray_origin(orientation, axes, count, height, width, rng)
        for row in range(gray_row - 1, gray_row + count + 1):
            for col in range(gray_col - 1, gray_col + count + 1):
                grid[row][col] = 0
        for row in range(gray_row, gray_row + count):
            for col in range(gray_col, gray_col + count):
                grid[row][col] = 5
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES * 2 + GENERAL_PROFILES * 5)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(profile, difficulty, ctx.draw_rng("scene"))
