"""Generator for arc_puzzle_bank_eleventh21:E71.

Complete each isolated monochrome L-tromino to its 2x2 square.  Because the
canonical rule groups cells globally by color, every active block must have a
distinct color; the three count controls therefore denote the same quantity and
are validated as aliases rather than silently ignored.
"""
from __future__ import annotations

import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "eca9af4f6c53"
VERSION = "2.2.0"
TASK_ID = "eca9af4f6c53"

SUMMARY = (
    "A 0-background grid with 1-9 isolated 2x2 L-trominoes. Each block has "
    "exactly three corners in its own distinct nonzero color; fill the missing "
    "corner with that same color."
)

INVARIANTS = [
    "background is 0",
    "each active 2x2 window has three same-color corners",
    "the missing corner is initially zero",
    "active blocks are isolated and use distinct colors",
]

PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 4, 7, 9, 1, 3, 5, 6, 8),
    "cool": (1, 3, 6, 8, 2, 4, 5, 7, 9),
    "varied": (9, 1, 6, 3, 8, 2, 7, 4, 5),
}
PALETTE_KINDS = tuple(PALETTES)
DEGENERATE_TEXTURES = ("no_blocks", "full_2x2", "two_corners")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {"type": "int", "default": "rng 7..14 by diff", "valid": "4..14; must fit blocks"},
    "grid_w": {"type": "int", "default": "rng 8..16 by diff", "valid": "4..16; must fit blocks"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "n_blocks": {"type": "int", "default": "rng 2..8 by diff", "valid": "1..9"},
    "palette_size": {"type": "int", "default": "n_blocks", "valid": "1..9; must equal n_blocks"},
    "position_bias": {"type": "str", "default": "isolated_l_trominoes",
                      "valid": "isolated_l_trominoes"},
    "n_distinct_colors": {"type": "int", "default": "n_blocks", "valid": "1..9; must equal n_blocks"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {"type": "str", "default": "alias for palette_kind",
                "valid": "default|warm|cool|varied|no_blocks|full_2x2|two_corners"},
}


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown overrides: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        expected = int if AXES[name]["type"] == "int" else str
        if type(value) is not expected:
            raise TypeError(f"{name} must be {expected.__name__}")


def _required_dimensions(count):
    rows = max(1, math.ceil(math.sqrt(count)))
    cols = max(1, math.ceil(count / rows))
    # Anchors are spaced by three; each block occupies two rows/columns.
    return 3 * (rows - 1) + 2, 3 * (cols - 1) + 2


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        if any(value is not None for name, value in overrides.items() if name != "texture"):
            raise ValueError("degenerate textures do not support additional axis overrides")
        return _draw_from_degenerate(texture, None)

    requested_counts = {
        overrides[name]
        for name in ("n_blocks", "palette_size", "n_distinct_colors")
        if overrides.get(name) is not None
    }
    if len(requested_counts) > 1:
        raise ValueError("n_blocks, palette_size and n_distinct_colors must agree")

    settings = dict(overrides)
    if requested_counts:
        count = requested_counts.pop()
        settings.update(n_blocks=count, palette_size=count, n_distinct_colors=count)
    if texture is not None:
        if texture not in HELPFUL_TEXTURES:
            raise ValueError(f"unknown texture: {texture}")
        if settings.get("palette_kind") not in (None, texture):
            raise ValueError("texture and palette_kind must agree")
        settings["palette_kind"] = texture

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=settings)
    if requested_counts or settings.get("n_blocks") is not None:
        target = ctx.draw_int_strict("n_blocks", 1, 9)
    elif difficulty == "easy":
        target = ctx.draw_int_strict("n_blocks", 2, 3)
    elif difficulty == "hard":
        target = ctx.draw_int_strict("n_blocks", 5, 8)
    else:
        target = ctx.draw_int_strict("n_blocks", 3, 5)
    ctx.draw_int_strict("palette_size", target, target)
    ctx.draw_int_strict("n_distinct_colors", target, target)
    ctx.draw_choice("position_bias", ("isolated_l_trominoes",))
    ctx.draw_choice("density", ("sparse",))
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    required_h, required_w = _required_dimensions(target)
    if difficulty == "easy":
        h = ctx.draw_int_strict("grid_h", max(7, required_h), max(8, required_h))
        w = ctx.draw_int_strict("grid_w", max(8, required_w), max(9, required_w))
    elif difficulty == "hard":
        h = ctx.draw_int_strict("grid_h", max(11, required_h), 14)
        w = ctx.draw_int_strict("grid_w", max(12, required_w), 16)
    else:
        h = ctx.draw_int_strict("grid_h", max(8, required_h), max(11, required_h))
        w = ctx.draw_int_strict("grid_w", max(9, required_w), max(13, required_w))
    if h > 14 or w > 16:
        raise ValueError("requested block count cannot fit within supported dimensions")

    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    anchors = [(r, c) for r in range(0, h - 1, 3) for c in range(0, w - 1, 3)]
    if len(anchors) < target:
        raise ValueError("grid dimensions cannot fit the requested isolated blocks")
    rng.shuffle(anchors)
    colors = list(PALETTES[palette_kind])
    # Preserve the profile's bias while allowing seed variation within it.
    head = colors[:]
    rng.shuffle(head)
    colors = head[:target]
    for (r0, c0), color in zip(anchors[:target], colors, strict=True):
        missing = rng.randrange(4)
        cells = ((r0, c0), (r0, c0 + 1), (r0 + 1, c0), (r0 + 1, c0 + 1))
        for index, (r, c) in enumerate(cells):
            if index != missing:
                grid[r][c] = color
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    messages = []
    if not grid or not grid[0] or len({len(row) for row in grid}) != 1:
        return ["grid must be a nonempty rectangle"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid colors must be exact integers in 0..9"]
    colors = sorted({value for row in grid for value in row if value != 0})
    if not colors:
        messages.append("expected at least one incomplete 2x2 block")
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        if not (len(cells) == 3 and len(rows) == 2 and len(cols) == 2
                and rows[1] - rows[0] == 1 and cols[1] - cols[0] == 1):
            messages.append(f"color {color} is not exactly three corners of one 2x2 block")
            continue
        zeros = [(r, c) for r in rows for c in cols if grid[r][c] == 0]
        if len(zeros) != 1:
            messages.append(f"color {color} should have exactly one missing corner")
    return messages


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    grid = full_grid(h, w, 0)
    if name == "no_blocks":
        return grid
    if name == "full_2x2":
        for dr in range(2):
            for dc in range(2):
                grid[2 + dr][2 + dc] = 4
        return grid
    if name == "two_corners":
        grid[1][1] = 4
        grid[2][2] = 4
        return grid
    return grid
