"""Collision-free inputs for the fixed main-diagonal reflection authority.

Four exact controls: size, occupied cell count, foreground color count and
source side. Ordinary four-pair windows contain two mixed-side witnesses.
Labels are produced by the canonical Racket rule, never by this sampler.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e58027e9749f"
VERSION = "1.4.0"
TASK_ID = "e58027e9749f"
RULE_HASH = "2b970065d6a3"
SUMMARY = "Echo every nonzero source across the main diagonal, retaining the originals."
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "square grid with integer colors 0..9 and background 0",
    "at least one off-diagonal source; every reflected target is initially zero",
    "sources may be above, below, or on both sides of the main diagonal",
]
POSITION_BIASES = ("above_diagonal", "below_diagonal", "mixed")
AXES = {
    "size": {"type": "int", "default": "weighted 4..18, retaining 5..7 in every band", "valid": "4..18"},
    "cell_count": {"type": "int", "default": "weighted feasible 1..16", "valid": "1..16"},
    "n_distinct_colors": {"type": "int", "default": "weighted feasible 1..9 foreground colors", "valid": "1..9"},
    "position_bias": {"type": "str", "default": "seed-offset above,mixed,below,mixed cycle", "valid": "|".join(POSITION_BIASES)},
}
# Empty declaration selects strict rejection accounting. Each actual joint
# incompatibility supplies precisely the conflicting caller-specified axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
DEGENERATE_TEXTURES = ("already_symmetric", "on_diagonal", "empty_grid")
HELPFUL_TEXTURES = ()
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = POSITION_BIASES


def _validate_identity(seed, sample_index, difficulty):
    if type(seed) is not int:
        raise ValueError("seed must be a Python integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative Python integer")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium, or hard")


def schedule_profile(seed, sample_index, difficulty=None):
    """Default consecutive draws, independent of difficulty and layout RNG."""
    _validate_identity(seed, sample_index, difficulty)
    cycle = ("above_diagonal", "mixed", "below_diagonal", "mixed")
    return cycle[(seed + sample_index) % len(cycle)]


def _incompatible(message, *axes):
    error = ValueError(message)
    error.incompatible_axes = tuple(axes)
    raise error


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"Unknown override axes: {sorted(unknown)}")
    for name, lo, hi in (("size", 4, 18), ("cell_count", 1, 16), ("n_distinct_colors", 1, 9)):
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}, not {value!r}")
    side = overrides.get("position_bias")
    if side is not None and side not in POSITION_BIASES:
        raise ValueError(f"position_bias must be one of {POSITION_BIASES}")
    texture = overrides.get("texture")
    if texture is not None and texture not in DEGENERATE_TEXTURES:
        raise ValueError("texture is reserved for named diagnostic degenerates")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_identity(seed, sample_index, difficulty)
    _validate_overrides(overrides)
    if overrides.get("texture") is not None:
        if any(overrides.get(axis) is not None for axis in AXES):
            raise ValueError("Diagnostic texture cannot be combined with production controls")
        return _draw_from_degenerate(overrides["texture"], None)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    requested_count = overrides.get("cell_count")
    requested_colors = overrides.get("n_distinct_colors")
    requested_size = overrides.get("size")
    requested_side = overrides.get("position_bias")
    if requested_count is not None and requested_colors is not None and requested_colors > requested_count:
        _incompatible("n_distinct_colors exceeds cell_count", "cell_count", "n_distinct_colors")
    if requested_count == 1 and requested_side == "mixed":
        _incompatible("mixed position_bias needs cell_count >= 2", "cell_count", "position_bias")
    if requested_size is not None:
        capacity = requested_size * (requested_size - 1) // 2
        for axis, value in (("cell_count", requested_count), ("n_distinct_colors", requested_colors)):
            if value is not None and value > capacity:
                _incompatible(f"{axis} exceeds size's unoccupied transpose-pair capacity", "size", axis)

    scheduled_side = schedule_profile(seed, sample_index, difficulty)
    # A one-cell exact request can select an unforced single side; it must not
    # be rejected merely because this index normally teaches both directions.
    if requested_count == 1 and requested_side is None and scheduled_side == "mixed":
        scheduled_side = POSITION_BIASES[seed % 2]
    side = ctx.draw_choice("position_bias", POSITION_BIASES if requested_side is not None else (scheduled_side,))
    minimum_count = max(requested_count or 1, requested_colors or 1, 2 if side == "mixed" else 1)
    legal_sizes = [n for n in range(4, 19) if n * (n - 1) // 2 >= minimum_count]
    preferred_sizes = {"easy": [4, 5, 6, 7], "medium": [7, 8, 9, 10, 11], "hard": list(range(12, 19))}.get(difficulty, [6, 7, 8, 9])
    # Canonical scale is supported in every band, alongside the larger layouts.
    size_options = legal_sizes + [n for n in ([5, 6, 7] * 10 + preferred_sizes * 2) if n in legal_sizes]
    size = ctx.draw_choice("size", size_options)
    capacity = min(16, size * (size - 1) // 2)
    minimum_count = max(requested_colors or 1, 2 if side == "mixed" else 1)
    legal_counts = list(range(minimum_count, capacity + 1))
    preferred_counts = {"easy": [2, 3, 4], "medium": [4, 5, 6, 7], "hard": list(range(8, 17))}.get(difficulty, [3, 4, 5, 6])
    count_options = legal_counts + [n for n in ([3, 4] * 8 + preferred_counts * 2) if n in legal_counts]
    count = ctx.draw_choice("cell_count", count_options)
    legal_colors = list(range(1, min(count, 9) + 1))
    preferred_colors = [3] if size == 5 else [4] if size == 7 else [3, 4]
    color_options = legal_colors + [n for n in preferred_colors * 12 if n in legal_colors]
    color_count = ctx.draw_choice("n_distinct_colors", color_options)

    rng = ctx.draw_rng("layout")
    pairs = [(r, c) for r in range(size) for c in range(r + 1, size)]
    rng.shuffle(pairs)
    if side == "mixed":
        lower = [False, True] + [bool(rng.randrange(2)) for _ in range(count - 2)]
        rng.shuffle(lower)
    else:
        lower = [side == "below_diagonal"] * count
    palette = rng.sample(list(range(1, 10)), color_count)
    colors = palette + [rng.choice(palette) for _ in range(count - color_count)]
    rng.shuffle(colors)
    grid = full_grid(size, size, 0)
    for (r, c), reverse, color in zip(pairs[:count], lower, colors):
        if reverse:
            r, c = c, r
        grid[r][c] = color
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the collision-free teaching domain, including all zero cells."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty or non-sequence grid"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["grid rows must be sequences"]
    size = len(grid)
    if any(len(row) != size for row in grid):
        return ["grid must be nonempty and square"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["every cell, including background, must be a Python integer in 0..9"]
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not occupied:
        return ["no source cells; reflection is hidden"]
    if any(r == c for r, c in occupied):
        return ["diagnostic diagonal cells are outside the nontrivial teaching domain"]
    if any(grid[c][r] != 0 for r, c in occupied):
        return ["reflected target already occupied; collision precedence is outside this domain"]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    cells = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    above = any(r < c for r, c, _ in cells)
    below = any(r > c for r, c, _ in cells)
    side = "mixed" if above and below else "above_diagonal" if above else "below_diagonal"
    return {"size": len(grid), "cell_count": len(cells),
            "n_distinct_colors": len({v for _, _, v in cells}), "position_bias": side}


def _upper_only(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if r < c and value:
                out[c][r] = value
    return out


def _lower_only(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if r > c and value:
                out[c][r] = value
    return out


def _transpose_only(grid):
    return [list(column) for column in zip(*grid)]


def _anti_diagonal_echo(grid):
    size = len(grid)
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                out[size - 1 - c][size - 1 - r] = value
    return out


def _unchanged(grid):
    return [list(row) for row in grid]


def _has_above(grid):
    return not self_check(grid) and any(value for r, row in enumerate(grid) for c, value in enumerate(row) if r < c)


def _has_below(grid):
    return not self_check(grid) and any(value for r, row in enumerate(grid) for c, value in enumerate(row) if r > c)


SEMANTIC_WITNESSES = {"above_source": _has_above, "below_source": _has_below}
SEMANTIC_RIVALS = {"upper_only": _upper_only, "lower_only": _lower_only}
WITNESS_RIVALS = {"above_source": ["lower_only"], "below_source": ["upper_only"]}
CANONICAL_SHORTCUTS = {"upper_only": _upper_only}
LESSON_COMPETITORS = {**SEMANTIC_RIVALS, "transpose_only": _transpose_only,
                      "anti_diagonal_echo": _anti_diagonal_echo, "unchanged": _unchanged}


def _draw_from_degenerate(name, rng):
    grid = full_grid(7, 7, 0)
    if name == "already_symmetric":
        grid[1][4] = grid[4][1] = 5
    elif name == "on_diagonal":
        grid[2][2] = 4
    elif name != "empty_grid":
        raise ValueError(f"Unknown diagnostic texture: {name}")
    return grid
