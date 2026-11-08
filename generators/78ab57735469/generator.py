"""Input generator for the 3x3 kaleidoscope tiling task.

The unchanged authority expands an N x N tile into a 3N x 3N grid.  Block rows
0 and 2 use an up/down-flipped tile, and block columns 0 and 2 use a
left/right-flipped tile.  Ordinary generated tiles expose both flip axes.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.textures import fill_texture

GENERATOR_ID = "78ab57735469"
TASK_ID = GENERATOR_ID
RULE_HASH = "18918c7192ef"
VERSION = "2.0.1"
SUMMARY = (
    "An asymmetric square tile is expanded into a 3-by-3 block mosaic. "
    "Even-numbered block rows flip the tile up/down and even-numbered block "
    "columns flip it left/right, so corner blocks are rotated 180 degrees "
    "and the center block is unchanged."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (0, 1, 2, 3)

INVARIANTS = [
    "input is a square tile with side 3..5, so the output fits within 15x15",
    "the tile contains exactly 3 or 4 integer colors from 0..9",
    "the tile is neither left/right symmetric nor up/down symmetric",
    "two of every four default schedule phases use side 3 and two use side 4 or 5",
]

AXES = {
    "side": {
        "type": "int",
        "default": "period-4 canonical anchor at 3; otherwise band-weighted 4..5",
        "valid": "3..5",
    },
    "palette_size": {
        "type": "int",
        "default": "band-weighted 3..4",
        "valid": "3..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_TEXTURES = (
    "noise",
    "sparse",
    "blob",
    "stripes",
    "gradient",
    "checkerboard",
    "frame",
    "ring",
    "plus",
)


def _is_lr_sym(grid):
    width = len(grid[0])
    return all(
        row[col] == row[width - 1 - col]
        for row in grid
        for col in range(width)
    )


def _is_ud_sym(grid):
    height = len(grid)
    return all(grid[row] == grid[height - 1 - row] for row in range(height))


def schedule_profile(seed, sample_index, difficulty=None):
    """Finite semantic schedule used by ordinary lessons."""
    del seed, difficulty
    return sample_index % LESSON_SCHEDULE_PERIOD


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if "side" in overrides and overrides["side"] is not None:
        if not 3 <= overrides["side"] <= 5:
            raise ValueError("side must be in 3..5")
    if "palette_size" in overrides and overrides["palette_size"] is not None:
        if not 3 <= overrides["palette_size"] <= 4:
            raise ValueError("palette_size must be in 3..4")


def _draw_side(ctx, sample_index, band, overridden):
    if overridden:
        return ctx.draw_int("side", 3, 5)
    phase = sample_index % LESSON_SCHEDULE_PERIOD
    if phase in (0, 2):
        return ctx.draw_int("side", 3, 3)
    choices = {
        "easy": (4, 4, 4, 5),
        "medium": (4, 4, 5),
        "hard": (4, 5, 5, 5),
    }[band]
    return ctx.draw_choice("side", choices)


def _draw_palette_size(ctx, band, overridden):
    if overridden:
        return ctx.draw_int("palette_size", 3, 4)
    choices = {
        "easy": (3, 3, 3, 4),
        "medium": (3, 3, 4, 4),
        "hard": (3, 4, 4, 4),
    }[band]
    return ctx.draw_choice("palette_size", choices)


def _ensure_palette_used(grid, palette, rng):
    """Realize every requested color without deleting another last occurrence."""
    counts = Counter(value for row in grid for value in row)
    for missing in palette:
        if counts[missing]:
            continue
        candidates = [
            (row, col)
            for row in range(len(grid))
            for col in range(len(grid[0]))
            if counts[grid[row][col]] > 1
        ]
        if not candidates:
            raise RuntimeError("cannot realize the requested palette")
        row, col = rng.choice(candidates)
        old = grid[row][col]
        grid[row][col] = missing
        counts[old] -= 1
        counts[missing] += 1
    return grid


def _force_axis_asymmetry(grid, palette, rng):
    """Make both flips visible while preserving the realized palette exactly."""
    if not _is_lr_sym(grid) and not _is_ud_sym(grid):
        return grid

    counts = Counter(value for row in grid for value in row)
    edits = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            old = grid[row][col]
            if counts[old] <= 1:
                continue
            for new in palette:
                if new == old:
                    continue
                grid[row][col] = new
                if not _is_lr_sym(grid) and not _is_ud_sym(grid):
                    edits.append((row, col, old, new))
                grid[row][col] = old
    if edits:
        row, col, _old, new = rng.choice(edits)
        grid[row][col] = new
        return grid

    # A swap preserves every color count and handles the rare all-singleton
    # arrangement where no one-cell recoloring is legal.
    cells = [(r, c) for r in range(len(grid)) for c in range(len(grid[0]))]
    swaps = []
    for left_index, (row_a, col_a) in enumerate(cells):
        for row_b, col_b in cells[left_index + 1 :]:
            if grid[row_a][col_a] == grid[row_b][col_b]:
                continue
            grid[row_a][col_a], grid[row_b][col_b] = (
                grid[row_b][col_b],
                grid[row_a][col_a],
            )
            if not _is_lr_sym(grid) and not _is_ud_sym(grid):
                swaps.append((row_a, col_a, row_b, col_b))
            grid[row_a][col_a], grid[row_b][col_b] = (
                grid[row_b][col_b],
                grid[row_a][col_a],
            )
    if swaps:
        row_a, col_a, row_b, col_b = rng.choice(swaps)
        grid[row_a][col_a], grid[row_b][col_b] = (
            grid[row_b][col_b],
            grid[row_a][col_a],
        )
        return grid

    # Constructive fallback.  It is lawful for every declared side/palette and
    # is deliberately not symmetric on either axis.
    side = len(grid)
    fallback = [[palette[0] for _ in range(side)] for _ in range(side)]
    fallback[0][0] = palette[1]
    fallback[0][1] = palette[2]
    if len(palette) == 4:
        fallback[1][0] = palette[3]
    return fallback


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    side = _draw_side(ctx, sample_index, band, overrides.get("side") is not None)
    palette_size = _draw_palette_size(
        ctx,
        band,
        overrides.get("palette_size") is not None,
    )
    palette = list(ctx.draw_distinct_colors("palette", n=palette_size))
    texture = ctx.draw_choice("internal_texture", _TEXTURES)
    rng = ctx.draw_rng("cells")
    grid = fill_texture(texture, side, side, palette, rng)
    grid = _ensure_palette_used(grid, palette, rng)
    grid = _force_axis_asymmetry(grid, palette, rng)
    return grid


def observe_overrides(grid):
    return {
        "side": len(grid),
        "palette_size": len({value for row in grid for value in row}),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors = []
    height = len(grid)
    if height != width or not 3 <= height <= 5:
        errors.append(f"expected a square tile with side 3..5, got {height}x{width}")
    flat = [value for row in grid for value in row]
    if any(type(value) is not int or not 0 <= value <= 9 for value in flat):
        errors.append("cells must be integer colors in 0..9")
    palette_size = len(set(flat))
    if not 3 <= palette_size <= 4:
        errors.append(f"expected exactly 3 or 4 colors, got {palette_size}")
    if height == width and width > 0:
        if _is_lr_sym(grid):
            errors.append("tile is left/right symmetric, hiding horizontal flips")
        if _is_ud_sym(grid):
            errors.append("tile is up/down symmetric, hiding vertical flips")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if len(grid) != 3:
        return ["canonical examples use a 3x3 input tile"]
    return []


def rule_mirror(grid):
    """Independent Python mirror of the unchanged Racket authority."""
    side = len(grid)
    return [
        [
            grid[
                side - 1 - (row % side)
                if (row // side) % 2 == 0
                else row % side
            ][
                side - 1 - (col % side)
                if (col // side) % 2 == 0
                else col % side
            ]
            for col in range(3 * side)
        ]
        for row in range(3 * side)
    ]


def _ignore_horizontal_flips(grid):
    side = len(grid)
    return [
        [
            grid[
                side - 1 - (row % side)
                if (row // side) % 2 == 0
                else row % side
            ][col % side]
            for col in range(3 * side)
        ]
        for row in range(3 * side)
    ]


def _ignore_vertical_flips(grid):
    side = len(grid)
    return [
        [
            grid[row % side][
                side - 1 - (col % side)
                if (col // side) % 2 == 0
                else col % side
            ]
            for col in range(3 * side)
        ]
        for row in range(3 * side)
    ]


def _fixed_3x3(grid):
    """Wrong canonical-fitting shortcut: crop/assume a fixed 3x3 tile."""
    tile = [list(row[:3]) for row in grid[:3]]
    return rule_mirror(tile)


def _horizontal_flip_visible(grid):
    return not _is_lr_sym(grid)


def _vertical_flip_visible(grid):
    return not _is_ud_sym(grid)


def _noncanonical_side(grid):
    return len(grid) != 3


SEMANTIC_RIVALS = {
    "ignore_horizontal_flips": _ignore_horizontal_flips,
    "ignore_vertical_flips": _ignore_vertical_flips,
    "fixed_3x3": _fixed_3x3,
}
SEMANTIC_WITNESSES = {
    "horizontal_flip_visible": _horizontal_flip_visible,
    "vertical_flip_visible": _vertical_flip_visible,
    "noncanonical_side": _noncanonical_side,
}
WITNESS_RIVALS = {
    "horizontal_flip_visible": ["ignore_horizontal_flips"],
    "vertical_flip_visible": ["ignore_vertical_flips"],
    "noncanonical_side": ["fixed_3x3"],
}
CANONICAL_SHORTCUTS = {"fixed_3x3": _fixed_3x3}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Report any declared wrong rule that fits all demos but changes the query."""
    reasons = []
    query_output = query.get("output") if isinstance(query, dict) else None
    if query_output is None and isinstance(query, dict):
        query_output = rule_mirror(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        fits = all(
            rival(deepcopy(demo["input"])) == demo["output"]
            for demo in demos
        )
        if fits and query_output is not None:
            prediction = rival(deepcopy(query["input"]))
            if prediction != query_output:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
