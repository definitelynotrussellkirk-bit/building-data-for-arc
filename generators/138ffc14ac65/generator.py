"""Generator for the upward-column projection task.

The public axes are exact and global across difficulty bands.  Helpful textures
change the ordered color population.  Negative fixtures remain explicit
opt-ins and are never sampled by ordinary generation.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import positions

GENERATOR_ID = "138ffc14ac65"
TASK_ID = "138ffc14ac65"
VERSION = "2.0.2"
RULE_HASH = "37bbe278c364"
SUMMARY = "Each singleton seed paints its own column upward to the top edge."

INVARIANTS = [
    "background is 0",
    "ordinary seeds occupy distinct columns and are below the top edge",
    "ordinary seeds use distinct nonzero colors",
    "accepted numeric overrides equal the realized canvas and seed count",
]

HELPFUL_TEXTURES = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seeds", "all_top_row", "full_grid")
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
AXES = {
    "grid_h": {"type": "int", "default": "6..7 easy / 6..11 medium / 9..13 hard", "valid": "4..14"},
    "grid_w": {"type": "int", "default": "6..8 easy / 6..12 medium / 10..13 hard", "valid": "4..14"},
    "seed_count": {"type": "int", "default": "2..3 easy / 2..6 medium / 4..7 hard", "valid": "2..8"},
    "texture": {"type": "str", "default": "keyed helpful palette", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_PALETTES = {
    "warm": (2, 3, 4, 5, 6, 9, 1, 7, 8),
    "cool": (1, 5, 6, 7, 8, 2, 3, 4, 9),
    "broad": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "primary": (1, 2, 4, 8, 3, 5, 6, 7, 9),
}


def _incompatible(message: str, *axes: str):
    exc = ValueError(message)
    exc.incompatible_axes = tuple(axes)
    raise exc


def _validate_exact_override(overrides, name: str, lo: int, hi: int):
    if name not in overrides or overrides[name] is None:
        return None
    value = overrides[name]
    if type(value) is not int or not lo <= value <= hi:
        _incompatible(f"{name} must be an exact integer in {lo}..{hi}", name)
    return value


def _draw_exact_or_default(ctx, name: str, lo: int, hi: int, default: tuple[int, int]) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, *default)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative exact integer")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}; supported: {sorted(AXES)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    requested_count = _validate_exact_override(overrides, "seed_count", 2, 8)
    _validate_exact_override(overrides, "grid_h", 4, 14)
    _validate_exact_override(overrides, "grid_w", 4, 14)
    if "texture" in overrides and overrides["texture"] is not None:
        if type(overrides["texture"]) is not str or overrides["texture"] not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
            raise ValueError(f"unknown texture {overrides['texture']!r}")

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    texture_options = HELPFUL_TEXTURES + DEGENERATE_TEXTURES if overrides.get("texture") is not None else HELPFUL_TEXTURES
    texture = ctx.draw_choice("texture", texture_options)

    if difficulty == "easy":
        hr, wr, cr = (6, 7), (6, 8), (2, 3)
    elif difficulty == "hard":
        hr, wr, cr = (9, 13), (10, 13), (4, 7)
    else:
        hr, wr, cr = (6, 11), (6, 12), (2, 6)

    h = _draw_exact_or_default(ctx, "grid_h", 4, 14, hr)
    if "grid_w" in overrides and overrides["grid_w"] is not None:
        w = ctx.draw_int("grid_w", 4, 14)
    else:
        w_lo = max(wr[0], requested_count or 0)
        w_hi = max(wr[1], requested_count or 0)
        w = ctx.draw_int("grid_w", w_lo, min(14, w_hi))

    if texture in DEGENERATE_TEXTURES:
        if requested_count is not None:
            _incompatible("negative texture fixtures have fixed seed counts", "texture", "seed_count")
        return _draw_from_degenerate(texture, h=h, w=w)

    if requested_count is not None and requested_count > w:
        _incompatible("seed_count cannot exceed grid_w because seed columns are distinct", "seed_count", "grid_w")
    if requested_count is not None:
        count = ctx.draw_int("seed_count", 2, min(8, w))
    else:
        count = ctx.draw_int("seed_count", cr[0], min(cr[1], w, 8))

    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    colors = rng.sample(list(_PALETTES[texture]), count)
    columns = rng.sample(range(w), count)
    for column, color in zip(columns, colors):
        grid[rng.randint(1, h - 1)][column] = color
    return grid


def observe_overrides(grid):
    cells = positions(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "seed_count": len(cells)}


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]
    invalid = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
               if type(value) is not int or not 0 <= value <= 9]
    if invalid:
        r, c, value = invalid[0]
        return [f"out-of-range value {value} at ({r},{c})"]

    explicit_negative = (meta or {}).get("texture") in DEGENERATE_TEXTURES
    if explicit_negative:
        return []
    messages = []
    cells = positions(grid)
    if not cells:
        messages.append("ordinary instance has no seeds")
    columns = [c for _r, c in cells]
    if len(columns) != len(set(columns)):
        messages.append("seed columns are not distinct")
    if any(r == 0 for r, _c in cells):
        messages.append("ordinary instance contains a top-edge seed")
    values = [grid[r][c] for r, c in cells]
    if len(values) != len(set(values)):
        messages.append("ordinary seed colors are not distinct")
    if not (2 <= len(cells) <= 8):
        messages.append("ordinary instance should expose 2..8 singleton seeds")
    return messages


def _draw_from_degenerate(name, rng=None, *, h=7, w=8):
    grid = full_grid(h, w, 0)
    if name == "no_seeds":
        return grid
    if name == "all_top_row":
        for c in range(min(w, 8)):
            grid[0][c] = (c % 8) + 1
        return grid
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                grid[r][c] = 3
        return grid
    raise ValueError(f"unknown negative texture {name!r}")
