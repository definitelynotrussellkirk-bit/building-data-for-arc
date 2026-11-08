"""Generator for arc_additional_puzzles_21_set14_bundle:M94.

Rule: the command at (0,0) selects a transform (1=identity, 2=rotate-cw,
3=rotate-180, 4=transpose, 5=flip-lr, 6=flip-ud, else=transpose) applied to
the crop-to-content of the rest of the grid. Output = the transformed motif.

The old generator picked from only TWO fixed motifs (rng.choice of 2 shapes),
so distinct collapsed to ~12. Now: a RANDOM multi-color motif with a
NON-SQUARE bounding box (so rotate/transpose are visibly different from
identity/flip) and the full cmd range -> output shape + colors + dims all vary.

Combinatorial axes: motif shape/size (non-square bbox), motif colors, the
command, grid size, motif position.
Degenerates: missing_command, no_motif, square_motif.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "58f520283ae2"
VERSION = "2.0.1"  # distinct=12: gen picked from only 2 fixed motifs. Rule transforms the cropped motif by cmd 1-7. Now random non-square multi-color motif + full cmd range -> output shape/colors/dims vary.
TASK_ID = "58f520283ae2"
SUMMARY = (
    "0-bg grid (size varies). Cell (0,0) holds a COMMAND in {1..7}; the rest "
    "of the grid holds ONE MOTIF: a random multi-color pattern with a "
    "NON-SQUARE bounding box (bh != bw, each 2-4, 2-3 colors, every bbox edge "
    "touched so the crop is exact). Rule: read the command; crop-to-content of "
    "the rest; apply the transform (1=identity, 2=rotate-cw, 3=rotate-180, "
    "4=transpose, 5=flip-lr, 6=flip-ud, else=transpose). Output = the "
    "transformed motif (dims swap under rotate/transpose). The non-square bbox "
    "makes every command distinguishable."
)

INVARIANTS = [
    "the command cell at (0,0) is in {1..7} and is separate from the motif",
    "the motif has a non-square bounding box so transforms are visible",
    "the motif touches every edge of its bbox (crop-to-content is exact)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_command", "no_motif", "square_motif")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "cmd":            {"type": "int", "default": "rng 1..7", "valid": "1..7"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "command_top_left",
                       "valid": "command_top_left"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|missing_command|no_motif|square_motif"},
}

MOTIFS = (
    ((0, 0, 4), (0, 1, 4), (1, 1, 5), (2, 1, 5)),
    ((0, 2, 6), (1, 0, 7), (1, 1, 7), (1, 2, 6)),
)


def _rand_motif(rng):
    """Random multi-color cell list with a NON-SQUARE bbox (bh != bw)."""
    while True:
        bh = rng.randint(2, 4)
        bw = rng.randint(2, 4)
        if bh == bw:
            continue
        cells = {(r, c) for r in range(bh) for c in range(bw) if rng.random() < 0.6}
        if len(cells) < 2:
            continue
        if not any(r == 0 for r, _ in cells):
            cells.add((0, rng.randint(0, bw - 1)))
        if not any(r == bh - 1 for r, _ in cells):
            cells.add((bh - 1, rng.randint(0, bw - 1)))
        if not any(c == 0 for _, c in cells):
            cells.add((rng.randint(0, bh - 1), 0))
        if not any(c == bw - 1 for _, c in cells):
            cells.add((rng.randint(0, bh - 1), bw - 1))
        palette = rng.sample([1, 3, 4, 5, 6, 7, 8, 9], rng.randint(2, 3))
        return bh, bw, [(r, c, rng.choice(palette)) for (r, c) in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 15)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 13)
    cmd = ctx.draw_int("cmd", 1, 7)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    g[0][0] = cmd
    bh, bw, motif = _rand_motif(rng)
    top = rng.randint(1, h - bh)
    left = rng.randint(1, w - bw)
    for dr, dc, color in motif:
        g[top + dr][left + dc] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: cell (0,0) is a valid command {1..7}, plus at least one non-zero motif cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    cmd = grid[0][0]
    if cmd not in range(1, 8):
        errs.append(f"command at (0,0) is {cmd}, expected 1..7")
    motif_cells = sum(1 for r in range(h) for c in range(w) if (r, c) != (0, 0) and grid[r][c] != 0)
    if motif_cells == 0:
        errs.append("no motif cells found outside (0,0)")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "missing_command":
        for dr, dc, color in MOTIFS[0]:
            g[3 + dr][4 + dc] = color
        return g
    if name == "no_motif":
        g[0][0] = 3
        return g
    if name == "square_motif":
        g[0][0] = 4
        for dr in range(3):
            for dc in range(3):
                if (dr + dc) % 2 == 0:
                    g[3 + dr][4 + dc] = 6
        return g
    return g
