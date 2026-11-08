"""Generator for ARC task 99b1bc43.

The input is 9 x w: a four-row top panel, one uniform separator row,
and a four-row bottom panel.  The canonical output marks in color 3 the
symmetric difference of the two panels' zero/nonzero occupancy masks.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "08eaba8254b2"
TASK_ID = GENERATOR_ID
VERSION = "2.3.0"
RULE_HASH = "5679cfe5ff27"
SUMMARY = (
    "A 9 x w grid contains two four-row occupancy panels separated by one "
    "uniform nonzero row.  The output is 4 x w and paints color 3 exactly "
    "where one panel cell is zero and the corresponding cell in the other "
    "panel is nonzero."
)
INVARIANTS = [
    "input height is 9 and width is 3..30",
    "row 4 is a uniform nonzero separator",
    "both four-row panels contain foreground",
    "the occupancy XOR has between 1 and 4*w-1 marked cells",
]

PANEL_PATTERNS = (
    "random", "blob", "stripes", "checker", "border", "diagonal", "multicolor"
)
AXES = {
    "grid_w": {"type": "int", "default": "difficulty-aware rng 3..14", "valid": "3..30"},
    "top_color": {"type": "color", "default": "rng nonzero", "valid": "1..9"},
    "bot_color": {"type": "color", "default": "rng nonzero distinct from top", "valid": "1..9"},
    "sep_color": {"type": "color", "default": "rng nonzero distinct from panel colors", "valid": "1..9"},
    "panel_pattern": {
        "type": "str",
        "default": "rng helpful",
        "valid": "random|blob|stripes|checker|border|diagonal|multicolor",
    },
    "xor_target": {"type": "int", "default": "rng 1..11", "valid": "1..11"},
}
_ALLOWED_OVERRIDES = frozenset(AXES)


def _validate_override_keys(overrides: dict) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(unknown))


def _draw_width(ctx, difficulty, overrides) -> int:
    if overrides.get("grid_w") is not None:
        return ctx.draw_int_strict("grid_w", 3, 30)
    if difficulty == "easy":
        lo, hi = 3, 5
    elif difficulty == "hard":
        lo, hi = 10, 14
    else:
        lo, hi = 3, 14
    return ctx.draw_int("grid_w", lo, hi)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the source grammar rather than only checking for a nonblank XOR."""
    if type(grid) is not list or not grid:
        return ["empty grid"]
    if type(grid[0]) is not list or not grid[0]:
        return ["empty first row"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if h != 9:
        return [f"expected height 9, got {h}"]
    if not 3 <= w <= 30:
        errors.append(f"expected width 3..30, got {w}")
    if any(type(row) is not list or len(row) != w for row in grid):
        return errors + ["ragged grid"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"invalid cell {value!r} at ({r},{c})")
    if errors:
        return errors
    separator = grid[4]
    if separator[0] == 0 or any(value != separator[0] for value in separator):
        errors.append("separator row must be uniform and nonzero")
    top_nonzero = sum(grid[r][c] != 0 for r in range(4) for c in range(w))
    bottom_nonzero = sum(grid[5 + r][c] != 0 for r in range(4) for c in range(w))
    if top_nonzero == 0:
        errors.append("top panel has no foreground")
    if bottom_nonzero == 0:
        errors.append("bottom panel has no foreground")
    differences = sum(
        (grid[r][c] == 0) != (grid[5 + r][c] == 0)
        for r in range(4) for c in range(w)
    )
    if differences == 0:
        errors.append("panels have identical zero-occupancy: XOR output is blank")
    elif differences == 4 * w:
        errors.append("panels are perfect complements: XOR output is a solid block")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    w = _draw_width(ctx, difficulty, overrides)
    top_color = ctx.draw_color_strict("top_color", exclude={0})
    bot_color = ctx.draw_color_strict("bot_color", exclude={0, top_color})
    separator = ctx.draw_color_strict("sep_color", exclude={0, top_color, bot_color})
    pattern = ctx.draw_choice("panel_pattern", PANEL_PATTERNS)
    target = ctx.draw_int_strict("xor_target", 1, 11)
    rng = ctx.draw_rng("panels")
    top_density = ctx.draw_rng("top_density_internal").uniform(0.3, 0.7)
    bottom_density = ctx.draw_rng("bottom_density_internal").uniform(0.3, 0.7)

    grid = full_grid(9, w, 0)
    grid[4] = [separator] * w
    if pattern == "multicolor":
        for r in range(4):
            for c in range(w):
                if rng.random() < top_density:
                    grid[r][c] = rng.randint(1, 9)
                if rng.random() < bottom_density:
                    grid[5 + r][c] = rng.randint(1, 9)
    else:
        _fill_panel(grid, 0, 4, w, pattern, top_density, top_color, rng)
        _fill_panel(grid, 5, 9, w, pattern, bottom_density, bot_color, rng)

    _set_xor_count(grid, w, target, top_color, bot_color, rng)
    _ensure_panel_foreground(grid, w, top_color, bot_color)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("generated invalid grid: " + "; ".join(errors))
    return grid


def _fill_panel(grid, r0, r1, width, pattern, density, color, rng):
    height = r1 - r0
    if pattern == "random":
        for r in range(r0, r1):
            for c in range(width):
                grid[r][c] = color if rng.random() < density else 0
    elif pattern == "blob":
        bh = max(1, min(height, round(height * density)))
        bw = max(1, min(width, round(width * density)))
        rr = rng.randint(r0, r1 - bh)
        cc = rng.randint(0, width - bw)
        for r in range(rr, rr + bh):
            for c in range(cc, cc + bw):
                grid[r][c] = color
    elif pattern == "stripes":
        for r in range(r0, r1):
            if (r - r0) % 2 == 0:
                grid[r] = [color] * width
    elif pattern == "checker":
        for r in range(r0, r1):
            for c in range(width):
                if (r + c) % 2 == 0:
                    grid[r][c] = color
    elif pattern == "border":
        for c in range(width):
            grid[r0][c] = color
            grid[r1 - 1][c] = color
        for r in range(r0, r1):
            grid[r][0] = color
            grid[r][width - 1] = color
    elif pattern == "diagonal":
        for offset in range(min(height, width)):
            grid[r0 + offset][offset] = color
    else:
        raise ValueError(f"unsupported panel pattern: {pattern}")


def _set_xor_count(grid, width, target, top_color, bottom_color, rng):
    cells = [(r, c) for r in range(4) for c in range(width)]
    differing = [
        cell for cell in cells
        if (grid[cell[0]][cell[1]] == 0) != (grid[5 + cell[0]][cell[1]] == 0)
    ]
    same = [cell for cell in cells if cell not in set(differing)]
    rng.shuffle(differing)
    rng.shuffle(same)
    while len(differing) > target:
        r, c = differing.pop()
        if grid[r][c] == 0:
            grid[5 + r][c] = 0
        else:
            grid[5 + r][c] = bottom_color
    while len(differing) < target:
        r, c = same.pop()
        if grid[r][c] == 0 and grid[5 + r][c] == 0:
            grid[r][c] = top_color
        else:
            grid[5 + r][c] = 0
        differing.append((r, c))


def _ensure_panel_foreground(grid, width, top_color, bottom_color):
    """Add paired foreground on an equal-occupancy cell without changing XOR."""
    top_has = any(grid[r][c] != 0 for r in range(4) for c in range(width))
    bottom_has = any(grid[5 + r][c] != 0 for r in range(4) for c in range(width))
    if top_has and bottom_has:
        return
    for r in range(4):
        for c in range(width):
            if (grid[r][c] == 0) == (grid[5 + r][c] == 0):
                grid[r][c] = top_color
                grid[5 + r][c] = bottom_color
                return
    raise ValueError("could not preserve XOR while adding panel foreground")
