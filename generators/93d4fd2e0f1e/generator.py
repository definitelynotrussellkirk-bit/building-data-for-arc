"""Generator for arc_additional_puzzles_21_set14_bundle:H96 — Tile motif by row 0 cmd sequence.

Rule: motif = subgrid(1,0,3,2). cmds = non-zero values in row 0 (cols ≥ 3).
Output: hconcat of motif transformed by each cmd (1=id, 2=cw, 3=flip-lr,
else=180).

Combinatorial axes (8): grid_h, grid_w, palette_kind, cmd_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_motif, no_cmds, invalid_cmds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "93d4fd2e0f1e"
VERSION = "1.1.2"  # add self_check
TASK_ID = "93d4fd2e0f1e"
SUMMARY = "A 3x3 motif in the lower-left is repeated under the row-0 transform command sequence."

INVARIANTS = [
    "grid has 4 rows and enough columns for the motif plus commands",
    "motif at rows 1..3, cols 0..2",
    "row 0 cols 3 onward has commands in 1..4",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motif", "no_cmds", "invalid_cmds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "4", "valid": "4..4"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "6..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cmd_count":      {"type": "int", "default": "rng 3..5", "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5..5"},
    "position_bias":  {"type": "str", "default": "lower_left_motif_with_cmds",
                       "valid": "lower_left_motif_with_cmds"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: h=4; motif cells in rows 1-3, cols 0-2; row-0 cmds at cols 3+ in {1..4}."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    if h != 4:
        errs.append(f"expected h=4; got h={h}")
    motif_nz = sum(1 for r in range(1, min(4, h)) for c in range(min(3, w)) if grid[r][c] != 0)
    if motif_nz < 1:
        errs.append("motif area (rows 1-3, cols 0-2) is empty")
    if w > 3:
        cmds = [grid[0][c] for c in range(3, w) if grid[0][c] != 0]
        if not cmds:
            errs.append("row 0 cols 3+ has no command values")
        else:
            bad = [v for v in cmds if v not in (1, 2, 3, 4)]
            if bad:
                errs.append(f"command values out of range 1-4: {bad}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        cmd_count = ctx.draw_int("cmd_count", 3, 3)
    elif difficulty == "hard":
        cmd_count = ctx.draw_int("cmd_count", 4, 5)
    else:
        cmd_count = ctx.draw_int("cmd_count", 3, 5)
    motif_color = ctx.draw_color("motif_color", exclude=[0, 1, 2, 3, 4])
    h, w = 4, 3 + cmd_count
    g = full_grid(h, w, 0)
    g[1][0] = motif_color; g[1][1] = motif_color
    g[2][1] = motif_color
    g[3][0] = motif_color; g[3][1] = motif_color; g[3][2] = motif_color
    cmds = [ctx.draw_choice(f"cmd_{i}", [1, 2, 3, 4]) for i in range(cmd_count)]
    if cmd_count >= 2 and len(set(cmds)) == 1:
        # Single-command rows are legal but teach only one transform branch.
        # Deterministically flip the final command to a different branch so every
        # normal example compares at least two transformations of the motif.
        cmds[-1] = 1 + (cmds[-1] % 4)
    for i, cmd in enumerate(cmds):
        g[0][3 + i] = cmd
    return g


def _draw_from_degenerate(name, rng):
    h, w = 4, 7
    g = full_grid(h, w, 0)
    if name == "no_motif":
        # cmds present but motif region is empty → nothing to tile
        g[0][3] = 1; g[0][4] = 2; g[0][5] = 3; g[0][6] = 4
        return g
    if name == "no_cmds":
        # motif drawn but row-0 has no commands → no tiling steps
        g[1][0] = 7; g[1][1] = 7
        g[2][1] = 7
        g[3][0] = 7; g[3][1] = 7; g[3][2] = 7
        return g
    if name == "invalid_cmds":
        # row-0 contains values outside the 1..4 vocabulary
        g[1][0] = 6; g[1][1] = 6
        g[2][1] = 6
        g[3][0] = 6; g[3][1] = 6; g[3][2] = 6
        g[0][3] = 8; g[0][4] = 9; g[0][5] = 5
        return g
    return g
