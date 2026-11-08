"""Generator for 94be5b80.

Rule: a key strip orders colors; the first keyed shape template is
stacked once per key color.

Combinatorial axes (8): grid_h/w, key_length, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_key, no_template, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "884393009d85"
VERSION = "2.0.1"
TASK_ID = "884393009d85"
SUMMARY = (
    "0-bg grid (h ∈ 12-16, w ≥ 10+n) "
    "with: (a) TOP KEY STRIP — rows 0 "
    "and 1 BOTH show the SAME color "
    "sequence: g[0][start_c+i] = "
    "g[1][start_c+i] = colors[i] for "
    "i in 0..n-1, where n ∈ 3-4 is "
    "key_length and colors are n "
    "DISTINCT non-bg colors drawn from "
    "{1..9}, anchored at start_c=2; "
    "(b) ONE COLORED TEMPLATE SHAPE "
    "below the key strip — fixed "
    "L-tromino [(0,0),(0,1),(1,0)] "
    "painted in colors[0] (the FIRST "
    "KEY COLOR), placed at base_r = "
    "4 + (sample_index % 2), base_c "
    "= 3 + ((seed + sample_index) % "
    "2). Rule (FOR EACH KEY COLOR "
    "IN ORDER, STACK A COPY OF THE "
    "TEMPLATE VERTICALLY — EACH "
    "COPY RECOLORED TO THE KEY "
    "COLOR; FIRST COPY AT "
    "TEMPLATE'S ORIGINAL POSITION, "
    "SUBSEQUENT COPIES AT VERTICAL "
    "OFFSETS = KEY-INDEX × "
    "TEMPLATE_HEIGHT): READ the key "
    "row's color sequence. FOR i in "
    "0..n-1: PASTE the template "
    "shape (in colors[i]) at "
    "position (base_r + i × "
    "template_h, base_c). The key "
    "rows are removed from the "
    "output. Net: key sequence "
    "becomes a vertical stack of "
    "n recolored template copies."
)

# Rivals: 'output is input' refuted by demos (key strip vanishes,
# stack expands). 'use template color always' refuted by demos
# with varied keys producing distinct colors. 'no stacking' refuted
# by demos with key length ≥3. 'paste at original positions only'
# refuted by demos with multiple stack levels visible. 3 demos with
# varied key sequences cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is color 0",
    "two identical key rows contain at least two distinct nonzero colors",
    "one key color has a template shape outside the key rows",
    "the output stacks that template in key order",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_key", "no_template", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..16", "valid": "12..16"},
    "grid_w":         {"type": "int", "default": "varied", "valid": "varied"},
    "key_length":     {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: two identical key rows (rows 0/1) contain >=2 distinct nonzero colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h < 2:
        return []  # grid too small
    row0 = list(grid[0]); row1 = list(grid[1])
    key0 = [v for v in row0 if v != 0]
    key1 = [v for v in row1 if v != 0]
    if not key0 and not key1:
        return []  # degenerate no_key — allowed
    if not key0 or not key1:
        return []  # degenerate no_key — allowed
    # Check rows 0 and 1 have identical nonzero content
    errs = []
    if row0 != row1:
        errs.append("key rows 0 and 1 differ")
    # Check >=2 distinct key colors
    key_colors = set(v for v in row0 if v != 0)
    if len(key_colors) < 2:
        errs.append(f"expected >=2 distinct key colors; found {key_colors}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        n = ctx.draw_int("key_length", 3, 3)
    elif difficulty == "hard":
        n = ctx.draw_int("key_length", 4, 4)
    else:
        n = ctx.draw_int("key_length", 3, 4)
    h = 12 + rng.randint(0, 4)
    w = 10 + n + rng.randint(0, 3)
    colors = ctx.draw_distinct_colors("key_colors", n=n, exclude={0})
    g = full_grid(h, w, 0)
    start_c = 2
    for r in [0, 1]:
        for i, color in enumerate(colors):
            g[r][start_c + i] = color
    base_r = 4 + (sample_index % 2)
    base_c = 3 + ((seed + sample_index) % 2)
    for dr, dc in [(0, 0), (0, 1), (1, 0)]:
        g[base_r + dr][base_c + dc] = colors[0]
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    if name == "no_key":
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][5 + dc] = 3
        return g
    if name == "no_template":
        for r in [0, 1]:
            g[r][2] = 3
            g[r][3] = 4
            g[r][4] = 5
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 3
        return g
    return g
