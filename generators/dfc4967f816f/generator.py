"""Input sampler for the vertical-symmetry flag strip, task dfc4967f816f.

The canonical Racket authority splits a one-row strip into 3x3 tiles separated
by color-9 columns and emits 8 exactly for tiles equal to their left-right flip.
This module generates inputs only; labels remain owned by the pinned authority.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.lattice import assemble_tiles

GENERATOR_ID = "dfc4967f816f"
TASK_ID = GENERATOR_ID
RULE_HASH = "136bfe841cf2"
VERSION = "2.0.0"
SUMMARY = (
    "A one-row strip of 3x3 tiles is classified by vertical mirror symmetry; "
    "the output contains 8 for symmetric tiles and 0 otherwise."
)
EXAMPLES_NEEDED = 2
EXPECTED_OUTPUT_CODOMAIN = (0, 8)

INVARIANTS = [
    "the input is one row of 3x3 tiles separated by full color-9 columns",
    "all tile cells use background 0 and one shared foreground color 1..8",
    "every normal input contains both symmetric and asymmetric tiles",
    "every normal input contains an asymmetric tile whose top row is symmetric",
    "normal labels differ from the canonical fixed even-position shortcut",
]

AXES = {
    "tile_cols": {
        "type": "int",
        "default": "weighted toward canonical 4",
        "valid": "3..6",
        "doc": "Number of 3x3 tiles in the one-row strip.",
    },
    "foreground_color": {
        "type": "color",
        "default": "uniform 1..8",
        "valid": "1..8",
        "doc": "Shared nonzero tile color; 0 is background and 9 is divider.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise ValueError("seed must be a Python int")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative Python int")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if "tile_cols" in overrides and overrides["tile_cols"] is not None:
        value = overrides["tile_cols"]
        if type(value) is not int or not 3 <= value <= 6:
            raise ValueError("tile_cols must be a Python int in 3..6")
    if "foreground_color" in overrides and overrides["foreground_color"] is not None:
        value = overrides["foreground_color"]
        if type(value) is not int or not 1 <= value <= 8:
            raise ValueError("foreground_color must be a Python int in 1..8")


def _bits_to_tile(bits, color):
    return [
        [color if bits[3 * row + col] else 0 for col in range(3)]
        for row in range(3)
    ]


def _is_vertical_bits(bits):
    return all(bits[3 * row] == bits[3 * row + 2] for row in range(3))


@lru_cache(maxsize=1)
def _pattern_pools():
    symmetric = []
    asymmetric = []
    top_row_asymmetric = []
    deep_asymmetric = []
    for bits in product((0, 1), repeat=9):
        if not any(bits):
            continue
        vertical = _is_vertical_bits(bits)
        top_symmetric = bits[0] == bits[2]
        if vertical:
            # Exclude the fully filled tile so every positive has visible structure.
            if not all(bits):
                symmetric.append(bits)
        else:
            asymmetric.append(bits)
            if top_symmetric and any(bits[:3]):
                deep_asymmetric.append(bits)
            if not top_symmetric:
                top_row_asymmetric.append(bits)
    return (
        tuple(symmetric),
        tuple(asymmetric),
        tuple(top_row_asymmetric),
        tuple(deep_asymmetric),
    )


@lru_cache(maxsize=4)
def _flag_patterns(tile_cols):
    canonical_shortcut = tuple(index % 2 == 0 for index in range(tile_cols))
    return tuple(
        pattern
        for pattern in product((False, True), repeat=tile_cols)
        if any(pattern)
        and not all(pattern)
        and pattern != canonical_shortcut
    )


def _draw_tile_cols(ctx):
    # Repeated 4s retain broad 3..6 support while making the exact canonical
    # 3x15 profile frequent in every pinned 20-draw band census.
    return ctx.draw_choice("tile_cols", (3, 4, 4, 4, 4, 5, 6))


def _build_tiles(ctx, tile_cols, color, difficulty):
    rng = ctx.draw_rng("tile_layout")
    flags = rng.choice(_flag_patterns(tile_cols))
    false_indices = [index for index, flag in enumerate(flags) if not flag]
    hard_negative_index = rng.choice(false_indices)
    symmetric, asymmetric, top_row_asymmetric, deep_asymmetric = _pattern_pools()

    tiles = []
    for index, symmetric_flag in enumerate(flags):
        if symmetric_flag:
            bits = rng.choice(symmetric)
        elif index == hard_negative_index:
            # This tile refutes the canonical-content shortcut "inspect only
            # the top row": its top row is symmetric, but a lower row is not.
            bits = rng.choice(deep_asymmetric)
        elif difficulty == "easy":
            bits = rng.choice(top_row_asymmetric)
        elif difficulty == "hard":
            bits = rng.choice(deep_asymmetric)
        else:
            bits = rng.choice(asymmetric)
        tiles.append(_bits_to_tile(bits, color))
    return tiles


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    tile_cols = _draw_tile_cols(ctx)
    foreground_color = ctx.draw_choice("foreground_color", tuple(range(1, 9)))
    tiles = _build_tiles(ctx, tile_cols, foreground_color, difficulty)
    return assemble_tiles([tiles], divider_color=9)


def _parse_tiles(grid):
    if not isinstance(grid, (list, tuple)) or len(grid) != 3:
        raise ValueError("expected exactly three input rows")
    if not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    if width < 11 or (width + 1) % 4:
        raise ValueError("width must encode 3..6 width-3 tiles with one-column dividers")
    tile_cols = (width + 1) // 4
    if not 3 <= tile_cols <= 6:
        raise ValueError("tile count must be in 3..6")
    for value in (value for row in grid for value in row):
        if type(value) is not int or not 0 <= value <= 9:
            raise ValueError("cells must be integer ARC colors 0..9")
    for divider in range(3, width, 4):
        if any(row[divider] != 9 for row in grid):
            raise ValueError("every divider column must be fully color 9")
    tiles = [
        [list(row[left:left + 3]) for row in grid]
        for left in range(0, width, 4)
    ]
    if any(9 in row for tile in tiles for row in tile):
        raise ValueError("divider color 9 may not occur inside a tile")
    return tiles


def _is_vertical_tile(tile):
    return all(row == row[::-1] for row in tile)


def _tile_flags(grid):
    return [_is_vertical_tile(tile) for tile in _parse_tiles(grid)]


def rule_mirror(grid):
    """Independent Python mirror for tests and named rivals, not label authority."""
    return [[8 if flag else 0 for flag in _tile_flags(grid)]]


def self_check(grid, *, difficulty=None, meta=None):
    try:
        tiles = _parse_tiles(grid)
    except (TypeError, ValueError, IndexError) as exc:
        return [str(exc)]

    errors = []
    tile_values = {value for tile in tiles for row in tile for value in row}
    foreground = tile_values - {0}
    if len(foreground) != 1:
        errors.append("tiles must use background 0 and exactly one shared foreground color")
        return errors
    color = next(iter(foreground))
    if not 1 <= color <= 8:
        errors.append("foreground color must be in 1..8")
    for index, tile in enumerate(tiles):
        values = {value for row in tile for value in row}
        if values - {0, color}:
            errors.append(f"tile {index} contains an undeclared color")
        if values == {0}:
            errors.append(f"tile {index} is blank")
    flags = [_is_vertical_tile(tile) for tile in tiles]
    if not any(flags):
        errors.append("at least one tile must be vertically symmetric")
    if all(flags):
        errors.append("at least one tile must be vertically asymmetric")
    return errors


def strict_canonical_like(grid):
    """Accept the canonical manifold and this sampler's lawful one-row extension."""
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    tiles = _parse_tiles(grid)
    foreground = next(
        value for tile in tiles for row in tile for value in row if value != 0
    )
    return {"tile_cols": len(tiles), "foreground_color": foreground}


def _top_row_only(grid):
    """WRONG: flag a tile when only its first row is mirror-symmetric."""
    return [[8 if tile[0] == tile[0][::-1] else 0 for tile in _parse_tiles(grid)]]


def _fixed_even_positions(grid):
    """WRONG: replay the canonical 8,0,8,0 positional pattern."""
    return [[8 if index % 2 == 0 else 0 for index, _ in enumerate(_parse_tiles(grid))]]


def _has_deep_row_asymmetry(grid):
    return any(
        tile[0] == tile[0][::-1] and not _is_vertical_tile(tile)
        for tile in _parse_tiles(grid)
    )


def _has_noncanonical_positions(grid):
    return rule_mirror(grid) != _fixed_even_positions(grid)


SEMANTIC_WITNESSES = {
    "deep_row_asymmetry": _has_deep_row_asymmetry,
    "noncanonical_positions": _has_noncanonical_positions,
}
SEMANTIC_RIVALS = {
    "top_row_only": _top_row_only,
    "fixed_even_positions": _fixed_even_positions,
}
WITNESS_RIVALS = {
    "deep_row_asymmetry": ["top_row_only"],
    "noncanonical_positions": ["fixed_even_positions"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
