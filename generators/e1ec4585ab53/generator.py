"""Generator for arc_additional_puzzles_21_set16_bundle:H112 — row/column command mosaic.

Rule: 6×6 input — (0, 3) and (0, 5) are column commands, (3, 0) and (5, 0) are
row commands; (3..5, 3..5) is a 3×3 source motif. Output is a 2×2 mosaic
where cell[r][c] = col_cmd[c](row_cmd[r](source)), packed with 1-cell gaps.

Combinatorial axes (8): grid_h, grid_w, palette_kind, motif_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_commands, no_motif, empty_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e1ec4585ab53"
VERSION = "2.1.0"  # include command code 8 so the canonical anti-transpose else branch is covered
TASK_ID = "e1ec4585ab53"

SUMMARY = (
    "Fixed 6×6 grid with: (a) "
    "ROW 0 cells (0, 3) and "
    "(0, 5) hold COLUMN command "
    "codes (1..8); (b) COLUMN 0 "
    "cells (3, 0) and (5, 0) "
    "hold ROW command codes "
    "(1..8); (c) rows 3-5 × "
    "cols 3-5 hold a 3×3 SOURCE "
    "MOTIF with 3-6 cells in a "
    "single non-zero color. "
    "Rule (2×2 TRANSFORM "
    "MOSAIC): build a 2×2 grid "
    "of 3×3 mosaics. For each "
    "output position (r, c) in "
    "the 2×2: APPLY col_cmd[c] "
    "to the source, then "
    "row_cmd[r]. PACK the four "
    "3×3 panels with 1-cell "
    "gaps. Output dims: 7×7 "
    "(2×3 + gap). Codes: "
    "1=identity, 2=rotate CW, "
    "3=rotate 180°, 4=transpose, "
    "5=flip-LR, 6=flip-UD, "
    "7=transpose (canonical "
    "duplicate), 8=anti-transpose. "
    "Net: "
    "row × col cmd grid yields "
    "a 2×2 transform mosaic of "
    "the 3×3 source."
)

INVARIANTS = [
    "background is 0",
    "(0, 3) and (0, 5) hold column transform codes (each 1..8)",
    "(3, 0) and (5, 0) hold row transform codes (each 1..8)",
    "rows 3-5, cols 3-5 hold a 3x3 source motif with 3-6 non-zero cells",
    "command cells are non-zero and distinct from row 0/col 0 padding",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_commands", "no_motif", "empty_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6", "valid": "6..6"},
    "grid_w":         {"type": "int", "default": "6", "valid": "6..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "motif_cells":    {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "rng 5..7", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "command_strip_plus_3x3_motif",
                       "valid": "command_strip_plus_3x3_motif"},
    "n_distinct_colors": {"type": "int", "default": "rng 5..7", "valid": "2..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n_motif_lo, n_motif_hi = 3, 4
    elif difficulty == "hard":
        n_motif_lo, n_motif_hi = 5, 6
    else:
        n_motif_lo, n_motif_hi = 3, 6
    rng = ctx.draw_rng("layout")
    g = full_grid(6, 6, 0)
    # commands: codes 1..8. The canonical Racket transform-code dispatch maps
    # 1=id, 2=cw, 3=180, 4=transpose, 5=flip-lr, 6=flip-ud, 7=transpose (again),
    # and ELSE to anti-transpose; code 8 is therefore the ONLY generated way to
    # cover the anti-transpose else branch the real examples exercise.
    cmd_codes = list(range(1, 9))
    g[0][3] = rng.choice(cmd_codes)
    g[0][5] = rng.choice(cmd_codes)
    g[3][0] = rng.choice(cmd_codes)
    g[5][0] = rng.choice(cmd_codes)
    # 3x3 motif
    n_motif = rng.randint(n_motif_lo, n_motif_hi)
    cells = [(r, c) for r in range(3) for c in range(3)]
    chosen = rng.sample(cells, n_motif)
    motif_color = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
    for r, c in chosen:
        g[3 + r][3 + c] = motif_color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(6, 6, 0)
    if name == "no_commands":
        # motif present but no row/col command codes → no transforms defined
        for r in range(3):
            for c in range(3):
                g[3 + r][3 + c] = 4
        return g
    if name == "no_motif":
        # commands present but no source motif → nothing to transform
        g[0][3] = 1; g[0][5] = 8; g[3][0] = 3; g[5][0] = 4
        return g
    if name == "empty_grid":
        # everything blank → no commands and no motif
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if len(grid) != 6 or any(len(row) != 6 for row in grid):
        return ["expected a 6x6 command grid"]
    command_cells = [(0, 3), (0, 5), (3, 0), (5, 0)]
    cmds = [grid[r][c] for r, c in command_cells]
    if not all(1 <= v <= 8 for v in cmds):
        errors.append("command cells must be codes 1..8")
    motif_vals = [grid[r][c] for r in range(3, 6) for c in range(3, 6) if grid[r][c] != 0]
    if not (3 <= len(motif_vals) <= 6):
        errors.append("source motif must expose 3..6 non-zero cells")
    if motif_vals and len(set(motif_vals)) != 1:
        errors.append("source motif must use a single color")
    allowed = set(command_cells) | {(r, c) for r in range(3, 6) for c in range(3, 6)}
    extra = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v and (r, c) not in allowed}
    if extra:
        errors.append("non-zero cells outside command strip/source motif")
    return errors
