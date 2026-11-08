"""Generator for arc_additional_puzzles_21_set19_bundle:H132 — Cmd-grid 2x2 motif tiling.

Rule: row commands at (2,0)/(4,0); col commands at (0,1)/(0,3); motif =
subgrid(2,1,4,3). Output: 2x2 tiles of motif transformed by row+col cmds.

Combinatorial axes (8): grid_h, grid_w, palette_kind, rc1/rc2/cc1/cc2,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_motif, all_same_cmd, missing_cmd.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a6ff53f3e600"
VERSION = "2.1.1"
TASK_ID = "a6ff53f3e600"
SUMMARY = (
    "FIXED 5×5 grid with: "
    "(a) FOUR COMMAND CELLS"
    " — at fixed positions "
    "(2, 0) = rc1 (row "
    "command 1), (4, 0) = "
    "rc2 (row command 2), "
    "(0, 1) = cc1 (col "
    "command 1), (0, 3) = "
    "cc2 (col command 2), "
    "each ∈ {1, 2, 3}; (b) "
    "3×3 MOTIF — at "
    "subgrid (2, 1)..(4, 3) "
    "filled with COLOR 4 "
    "in a specific shape "
    "pattern: cells (3, 2), "
    "(3, 3), (4, 1), (4, "
    "2), (4, 3) all = 4 "
    "(an inverted L shape)"
    ". Rule (2×2 META-"
    "TILE TRANSFORM PER "
    "(ROW CMD, COL CMD) "
    "PAIR): output is a "
    "2×2 GRID of TILES, "
    "each a COPY of the "
    "3×3 motif "
    "transformed by the "
    "(row_cmd, col_cmd) "
    "pair at that tile "
    "position: tile (0, 0)"
    " uses (rc1, cc1); "
    "tile (0, 1) uses "
    "(rc1, cc2); tile "
    "(1, 0) uses (rc2, "
    "cc1); tile (1, 1) "
    "uses (rc2, cc2). "
    "Each cmd ∈ {1, 2, 3} "
    "applies a specific "
    "transform (identity, "
    "horizontal-flip, "
    "vertical-flip per "
    "puzzle convention). "
    "Net: 4 transformed "
    "copies of the motif "
    "tiled together by "
    "command-pair lookup."
)

INVARIANTS = [
    "grid is 5 rows × 5 cols",
    "(2,0), (4,0), (0,1), (0,3) are cmd cells ∈ {1,2,3}",
    "subgrid(2,1)..(4,3) is the motif",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_motif", "all_same_cmd", "missing_cmd")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "5", "valid": "5..5"},
    "grid_w":         {"type": "int", "default": "5", "valid": "5..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "rc1":            {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "rc2":            {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "cc1":            {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "cc2":            {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "4", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "fixed_5x5_cmd_grid",
                       "valid": "fixed_5x5_cmd_grid"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: 5×5 grid; cmd cells at (2,0),(4,0),(0,1),(0,3) each in {1,2,3}."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h != 5 or w != 5:
        errs.append(f"expected 5×5 grid; got {h}×{w}")
        return errs
    cmd_positions = [(2, 0), (4, 0), (0, 1), (0, 3)]
    for r, c in cmd_positions:
        v = grid[r][c]
        if v not in (1, 2, 3):
            errs.append(f"cmd cell ({r},{c}) expected value 1-3; got {v}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        rc1 = ctx.draw_int("rc1", 1, 1); rc2 = ctx.draw_int("rc2", 1, 1)
        cc1 = ctx.draw_int("cc1", 1, 1); cc2 = ctx.draw_int("cc2", 1, 1)
    elif difficulty == "hard":
        rc1 = ctx.draw_int("rc1", 2, 3); rc2 = ctx.draw_int("rc2", 2, 3)
        cc1 = ctx.draw_int("cc1", 2, 3); cc2 = ctx.draw_int("cc2", 2, 3)
    else:
        rc1 = ctx.draw_int("rc1", 1, 3); rc2 = ctx.draw_int("rc2", 1, 3)
        cc1 = ctx.draw_int("cc1", 1, 3); cc2 = ctx.draw_int("cc2", 1, 3)
    h, w = 5, 5
    g = full_grid(h, w, 0)
    g[2][0] = rc1
    g[4][0] = rc2
    g[0][1] = cc1
    g[0][3] = cc2
    # motif = the 3x3 region rows 2-4 x cols 1-3. v1.x hardcoded a fixed L of
    # color 4 (only the commands varied) -> dup-inputs/outputs ~45%. Randomize the
    # motif content so the tiled+transformed 6x6 output varies widely.
    rng = ctx.draw_rng("motif")
    mcolors = rng.sample([1, 2, 3, 5, 6, 7, 8, 9], rng.randint(1, 3))
    mcells = [(r, c) for r in range(2, 5) for c in range(1, 4)]
    for (r, c) in rng.sample(mcells, rng.randint(3, 8)):
        g[r][c] = rng.choice(mcolors)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 5, 5
    g = full_grid(h, w, 0)
    if name == "empty_motif":
        # cmds present but motif region is empty → tiling produces all-bg
        g[2][0] = 1; g[4][0] = 2; g[0][1] = 3; g[0][3] = 1
        return g
    if name == "all_same_cmd":
        # all 4 cmds identical → output tiles uniformly (no row/col distinction)
        g[2][0] = 2; g[4][0] = 2; g[0][1] = 2; g[0][3] = 2
        g[3][2] = 4; g[3][3] = 4
        g[4][1] = 4; g[4][2] = 4; g[4][3] = 4
        return g
    if name == "missing_cmd":
        # one cmd cell is 0 → command set incomplete, transform underdetermined
        g[2][0] = 1; g[4][0] = 0  # missing
        g[0][1] = 2; g[0][3] = 3
        g[3][2] = 4; g[3][3] = 4
        g[4][1] = 4; g[4][2] = 4; g[4][3] = 4
        return g
    return g
