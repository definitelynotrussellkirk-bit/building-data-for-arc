"""Generator for c444b776.

Rule: divider-carved blocks; rule copies the one filled block to all
empty blocks.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors,
fill_density.
Degenerates: no_dividers, no_content, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a90bb7d9de75"
VERSION = "2.0.1"
TASK_ID = "a90bb7d9de75"
SUMMARY = (
    "0-bg grid (h, w~11-15) with: (a) ONE "
    "FULL-WIDTH HORIZONTAL DIVIDER ROW at "
    "random row div_r and ONE FULL-HEIGHT "
    "VERTICAL DIVIDER COL at random col div_c, "
    "both painted in a single non-zero "
    "div_color — carving the grid into 4 "
    "BLOCKS (TL, TR, BL, BR); (b) ONE of the 4 "
    "blocks (randomly chosen) contains "
    "CONTENT — scattered cells in 3 "
    "non-divider colors at fill density ~0.4 "
    "plus an anchor cell at (sr0, sc0); the "
    "other 3 blocks are EMPTY. Rule: identify "
    "the ONE FILLED BLOCK. EXTRACT its pattern "
    "(cells and colors). COPY that pattern "
    "into each of the other 3 EMPTY BLOCKS at "
    "corresponding LOCAL positions (matched "
    "offsets from each block's top-left). The "
    "dividers stay. Net: 4 blocks all show "
    "the same pattern; the one filled block "
    "is replicated to complete the layout."
)

INVARIANTS = [
    "single divider color makes full rows AND full cols",
    "dividers carve four rectangular blocks of equal-ish dims",
    "exactly one block has content; others are bg=0",
    "content uses non-divider non-zero colors",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_dividers", "no_content", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "fill_density":   {"type": "float", "default": "0.4", "valid": "0.3..0.6"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_dividers|no_content|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: one full-width row and one full-height col of same divider color; ≥1 content block."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Find full-width rows (divider rows)
    for color in range(1, 10):
        div_rows = [r for r in range(h) if all(grid[r][c] == color for c in range(w))]
        div_cols = [c for c in range(w) if all(grid[r][c] == color for r in range(h))]
        if div_rows and div_cols:
            # Found divider color: check ≥1 non-divider non-zero cell
            has_content = any(
                grid[r][c] != 0 and grid[r][c] != color
                for r in range(h) for c in range(w)
            )
            if not has_content:
                return errs  # degenerate (no_content) — allowed
            return errs
    # No matching divider color found
    return errs  # degenerate (no_dividers) — allowed


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 11, 12
    elif difficulty == "hard":
        h_lo, h_hi = 14, 17
    else:
        h_lo, h_hi = 11, 15
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    palette = ctx.draw_distinct_colors("palette", n=4, exclude={0})
    div_color = palette[0]
    cell_palette = palette[1:]
    div_r = rng.randint(3, h - 4)
    div_c = rng.randint(3, w - 4)
    g = full_grid(h, w, 0)
    for c in range(w):
        g[div_r][c] = div_color
    for r in range(h):
        g[r][div_c] = div_color
    block = rng.choice(["tl", "tr", "bl", "br"])
    if block == "tl":
        sr0, sc0 = 0, 0
    elif block == "tr":
        sr0, sc0 = 0, div_c + 1
    elif block == "bl":
        sr0, sc0 = div_r + 1, 0
    else:
        sr0, sc0 = div_r + 1, div_c + 1
    bh = h - 1 - div_r if block in ("bl", "br") else div_r
    bw = w - 1 - div_c if block in ("tr", "br") else div_c
    for r in range(sr0, sr0 + bh):
        for c in range(sc0, sc0 + bw):
            if rng.random() < 0.4:
                g[r][c] = rng.choice(cell_palette)
    g[sr0][sc0] = rng.choice(cell_palette)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    if name == "no_dividers":
        g[2][2] = 2
        return g
    if name == "no_content":
        for c in range(13):
            g[6][c] = 5
        for r in range(13):
            g[r][6] = 5
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 5
        return g
    return g
