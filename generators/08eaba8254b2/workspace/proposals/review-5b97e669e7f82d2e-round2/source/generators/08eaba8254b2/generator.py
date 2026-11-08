"""Generator for ARC task 99b1bc43 / content hash 08eaba8254b2.

The input has two 4xW panels separated by one full nonzero row.  The canonical
output is a 4xW color-3 mask of the cells whose zero/nonzero occupancy differs
between the panels (Boolean XOR).  The generator constructs an exact requested
XOR count while retaining both equal-empty and equal-filled negative examples.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "08eaba8254b2"
TASK_ID = GENERATOR_ID
RULE_HASH = "5679cfe5ff27"
VERSION = "3.0.0"

SUMMARY = (
    "A 9xW input (W=3..30) contains a 4-row top panel, one full nonzero "
    "separator row, and a 4-row bottom panel. Each panel uses zero plus one "
    "foreground color. Produce a fresh 4xW grid: paint color 3 exactly where "
    "one panel cell is zero and the aligned cell in the other panel is nonzero; "
    "paint 0 where both aligned cells have equal zero/nonzero occupancy."
)

INVARIANTS = [
    "input height is exactly 9 and width is 3..30",
    "row 4 is one uniform nonzero separator color",
    "each 4-row panel uses zero plus exactly one nonzero foreground color",
    "ordinary examples contain XOR-positive, both-zero, and both-filled alignments",
]

AXES = {
    "grid_w": {"type": "int", "default": "difficulty-keyed", "valid": "3..30"},
    "xor_target": {"type": "int", "default": "difficulty-keyed", "valid": "1..8"},
    "top_color": {"type": "color", "default": "keyed nonzero", "valid": "1..9"},
    "bot_color": {"type": "color", "default": "keyed nonzero", "valid": "1..9"},
    "sep_color": {"type": "color", "default": "keyed nonzero", "valid": "1..9"},
    "texture": {"type": "str", "default": "standard", "valid": "standard"},
}

HELPFUL_TEXTURES = ("standard",)
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
_DIFFICULTIES = (None, "easy", "medium", "hard")


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    for name, lo, hi in (("grid_w", 3, 30), ("xor_target", 1, 8)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")

    for name in ("top_color", "bot_color", "sep_color"):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer ARC color (not bool)")
        if not 1 <= value <= 9:
            raise ValueError(f"{name} must be a nonzero ARC color 1..9")

    if "texture" in overrides and overrides["texture"] is not None:
        value = overrides["texture"]
        if type(value) is not str:
            raise TypeError("texture override must be a string")
        if value != "standard":
            raise ValueError("texture must be 'standard'")


def _draw_int_axis(ctx, name: str, default_bounds: tuple[int, int], full_bounds: tuple[int, int]) -> int:
    bounds = full_bounds if name in ctx.overrides and ctx.overrides[name] is not None else default_bounds
    return int(ctx.draw_int_strict(name, *bounds))


def _construct(
    width: int,
    xor_target: int,
    top_color: int,
    bot_color: int,
    sep_color: int,
    rng,
) -> list[list[int]]:
    positions = [(r, c) for r in range(4) for c in range(width)]
    rng.shuffle(positions)
    xor_cells = set(positions[:xor_target])
    equal_cells = positions[xor_target:]
    if len(equal_cells) < 2:
        raise ValueError("construction needs both equal-empty and equal-filled cells")

    both_empty = {equal_cells[0]}
    both_filled = {equal_cells[1]}
    for cell in equal_cells[2:]:
        (both_filled if rng.randrange(2) else both_empty).add(cell)

    grid = full_grid(9, width, 0)
    for c in range(width):
        grid[4][c] = sep_color

    top_first = bool(rng.randrange(2))
    for index, (r, c) in enumerate(positions):
        if (r, c) in both_filled:
            grid[r][c] = top_color
            grid[r + 5][c] = bot_color
        elif (r, c) in xor_cells:
            top_occupied = (index % 2 == 0) == top_first
            if top_occupied:
                grid[r][c] = top_color
            else:
                grid[r + 5][c] = bot_color
    return grid


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

    if difficulty == "easy":
        width_bounds, xor_bounds = (3, 8), (1, 3)
    elif difficulty == "hard":
        width_bounds, xor_bounds = (15, 30), (5, 8)
    elif difficulty == "medium":
        width_bounds, xor_bounds = (8, 20), (3, 7)
    else:
        width_bounds, xor_bounds = (3, 14), (2, 6)

    width = _draw_int_axis(ctx, "grid_w", width_bounds, (3, 30))
    xor_target = _draw_int_axis(ctx, "xor_target", xor_bounds, (1, 8))
    top_color = int(ctx.draw_color_strict("top_color", exclude={0}))
    bot_color = int(ctx.draw_color_strict("bot_color", exclude={0}))
    sep_color = int(ctx.draw_color_strict("sep_color", exclude={0}))
    texture_options = ("standard",) if "texture" not in ctx.overrides else HELPFUL_TEXTURES
    ctx.draw_choice("texture", texture_options)

    grid = _construct(width, xor_target, top_color, bot_color, sep_color, ctx.draw_rng("occupancy"))
    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid panel scene: " + "; ".join(errors))
    return grid


def _shape_error(grid) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a nonempty sequence of rows"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "grid rows must be nonempty sequences"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "grid must be rectangular"
    return None


def _panel_colors(grid: Sequence[Sequence[int]], rows: range) -> set[int]:
    return {int(grid[r][c]) for r in rows for c in range(len(grid[0])) if grid[r][c] != 0}


def occupancy_classes(grid: Sequence[Sequence[int]]) -> dict[str, list[tuple[int, int]]]:
    """Return the canonical A-stage occupancy partition."""
    classes = {"xor": [], "both_zero": [], "both_filled": []}
    for r in range(4):
        for c in range(len(grid[0])):
            top = grid[r][c] != 0
            bottom = grid[r + 5][c] != 0
            if top != bottom:
                classes["xor"].append((r, c))
            elif top:
                classes["both_filled"].append((r, c))
            else:
                classes["both_zero"].append((r, c))
    return classes


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full stacked-panel grammar and informative negatives."""
    del difficulty, meta
    shape_error = _shape_error(grid)
    if shape_error:
        return [shape_error]
    errors: list[str] = []
    h, w = len(grid), len(grid[0])
    if h != 9:
        errors.append(f"expected height 9, got {h}")
        return errors
    if not 3 <= w <= 30:
        errors.append(f"panel width {w} must be in 3..30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be exact integer ARC colors 0..9")
        return errors

    separator = list(grid[4])
    if not separator or separator[0] == 0 or any(value != separator[0] for value in separator):
        errors.append("separator row must be one uniform nonzero color")

    top_colors = _panel_colors(grid, range(0, 4))
    bottom_colors = _panel_colors(grid, range(5, 9))
    if len(top_colors) != 1:
        errors.append(f"top panel must use exactly one nonzero foreground color, found {sorted(top_colors)}")
    if len(bottom_colors) != 1:
        errors.append(f"bottom panel must use exactly one nonzero foreground color, found {sorted(bottom_colors)}")

    classes = occupancy_classes(grid)
    if not classes["xor"]:
        errors.append("panels need at least one XOR-different occupancy cell")
    if not classes["both_zero"]:
        errors.append("panels need at least one aligned both-zero negative cell")
    if not classes["both_filled"]:
        errors.append("panels need at least one aligned both-filled negative cell")
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides from invalid grid: " + "; ".join(errors))
    top_colors = _panel_colors(grid, range(0, 4))
    bottom_colors = _panel_colors(grid, range(5, 9))
    return {
        "grid_w": len(grid[0]),
        "xor_target": len(occupancy_classes(grid)["xor"]),
        "top_color": next(iter(top_colors)),
        "bot_color": next(iter(bottom_colors)),
        "sep_color": int(grid[4][0]),
        "texture": "standard",
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror; protected Racket remains label authority."""
    if _shape_error(grid) or len(grid) != 9:
        raise ValueError("expected a rectangular 9-row input")
    width = len(grid[0])
    output = full_grid(4, width, 0)
    for r, c in occupancy_classes(grid)["xor"]:
        output[r][c] = 3
    return output
