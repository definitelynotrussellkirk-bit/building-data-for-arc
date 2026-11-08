"""Generator for 099aeda5aa7b: overlay the left-right reflection.

Every ordinary draw has exact public axes and a protected off-axis witness.
Multi-mark draws construct a differently coloured mirrored pair so the canonical
overlay must swap the two source colours rather than preserve the original
destination.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "099aeda5aa7b"
VERSION = "3.0.0"
RULE_HASH = "f48a460c6519"
SUMMARY = "Overlay the horizontal reflection; nonzero reflected cells overwrite destinations."
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "background is 0",
    "ordinary draws include a protected off-axis asymmetry witness",
    "swap_pair contains a differently coloured mutually mirrored pair",
]
HELPFUL_TEXTURES = ("plain", "swap_pair", "on_axis", "dense")
DEGENERATE_TEXTURES = ()
AXES = {
    "grid_h": {"type": "int", "default": "difficulty band within 4..16", "valid": "4..16"},
    "grid_w": {"type": "int", "default": "difficulty band within 5..18", "valid": "5..18"},
    "marks": {"type": "int", "default": "texture/difficulty band within 1..20", "valid": "1..20"},
    "texture": {"type": "str", "default": "rng helpful", "valid": "plain|swap_pair|on_axis|dense"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = (("texture", "grid_w"), ("texture", "marks"))
_COLORS = tuple(range(1, 10))


def _mirror(grid):
    """Python mirror of `(overlay g (flip-lr g))`."""
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value != 0:
                out[r][w - 1 - c] = value
    return out


def rule_mirror(grid):
    return _mirror(grid)


def observe_overrides(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "marks": sum(value != 0 for row in grid for value in row),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid must be a non-empty literal ARC grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        return ["grid must be rectangular with exact integer colours 0..9"]
    errors = []
    if len(grid) > 30 or width > 30:
        errors.append("grid exceeds ARC bounds")
    if width < 2:
        errors.append("width is too small for a horizontal reflection")
    if not any(value != 0 for row in grid for value in row):
        errors.append("ordinary grid needs a nonzero source")
    if _mirror(grid) == grid:
        errors.append("ordinary grid must visibly exercise the reflection overlay")
    observed = observe_overrides(grid)
    for key, expected in (meta or {}).get("overrides", {}).items():
        if key in observed and (type(expected) is not int or observed[key] != expected):
            errors.append(f"override {key} does not match observed value")
    return errors


def _incompatible(message, axes):
    error = ValueError("incompatible overrides: " + message)
    error.incompatible_axes = tuple(axes)
    return error


def _draw_int(ctx, overrides, label, ordinary, full):
    return ctx.draw_int_strict(label, *(full if label in overrides else ordinary))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative exact integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    bands = {
        None: ((6, 12), (7, 14)),
        "easy": ((4, 8), (5, 10)),
        "medium": ((7, 12), (8, 14)),
        "hard": ((11, 16), (13, 18)),
    }
    h_band, w_band = bands[difficulty]
    height = _draw_int(ctx, overrides, "grid_h", h_band, (4, 16))

    if texture == "on_axis" and "grid_w" in overrides and (
            type(overrides["grid_w"]) is not int or overrides["grid_w"] % 2 == 0):
        raise _incompatible("on_axis requires an odd grid_w", ("texture", "grid_w"))
    if texture == "on_axis":
        low, high = (5, 18) if "grid_w" in overrides else w_band
        odd_widths = [value for value in range(low, high + 1) if value % 2]
        width = ctx.draw_choice("grid_w", odd_widths)
    else:
        width = _draw_int(ctx, overrides, "grid_w", w_band, (5, 18))

    default_mark_bands = {
        "plain": {None: (2, 7), "easy": (2, 4), "medium": (3, 8), "hard": (5, 12)},
        "swap_pair": {None: (2, 8), "easy": (2, 5), "medium": (3, 9), "hard": (6, 14)},
        "on_axis": {None: (2, 8), "easy": (2, 5), "medium": (3, 9), "hard": (6, 14)},
        "dense": {None: (8, 16), "easy": (6, 12), "medium": (9, 17), "hard": (12, 20)},
    }
    if texture in ("swap_pair", "on_axis") and "marks" in overrides and (
            type(overrides["marks"]) is not int or overrides["marks"] < 2):
        raise _incompatible(f"{texture} requires marks >= 2", ("texture", "marks"))
    marks = _draw_int(ctx, overrides, "marks", default_mark_bands[texture][difficulty], (1, 20))

    rng = ctx.draw_rng("layout")
    colour_rng = ctx.draw_rng("colours")
    grid = full_grid(height, width, 0)
    used: set[tuple[int, int]] = set()

    def put(r, c, colour=None):
        if (r, c) in used:
            raise AssertionError("constructive placement collision")
        value = colour if colour is not None else colour_rng.choice(_COLORS)
        grid[r][c] = value
        used.add((r, c))
        return value

    # Required witness cells are constructed before generic fill.
    if texture == "swap_pair":
        row = rng.randrange(height)
        column = rng.randrange(width // 2)
        first, second = colour_rng.sample(_COLORS, 2)
        put(row, column, first)
        put(row, width - 1 - column, second)
    elif texture == "on_axis":
        axis = width // 2
        put(rng.randrange(height), axis)
        side = 0 if sample_index % 2 == 0 else width - 1
        candidates = [(r, side) for r in range(height) if (r, side) not in used]
        witness_row, witness_column = rng.choice(candidates)
        first_colour = put(witness_row, witness_column)
        if marks >= 3:
            opposite = width - 1 - witness_column
            second_colour = colour_rng.choice([value for value in _COLORS if value != first_colour])
            put(witness_row, opposite, second_colour)
    else:
        left = rng.randrange(width // 2)
        row = rng.randrange(height)
        first_column = left if sample_index % 2 == 0 else width - 1 - left
        first_colour = put(row, first_column)
        if marks >= 2:
            opposite = width - 1 - first_column
            second_colour = colour_rng.choice([value for value in _COLORS if value != first_colour])
            put(row, opposite, second_colour)

    available = [(r, c) for r in range(height) for c in range(width) if (r, c) not in used]
    rng.shuffle(available)
    for r, c in available[:marks - len(used)]:
        put(r, c)
    if len(used) != marks:
        raise AssertionError("declared mark count does not fit declared grid domain")
    if self_check(grid):
        raise AssertionError("constructive ordinary draw failed self_check: " + "; ".join(self_check(grid)))
    return grid
