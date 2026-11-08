"""Generator for arc_puzzle_bank_eighth_21_bundle:hard_56_frame_transform_gallery.

Rule (transform gallery): find the four hollow color-8 frames (sorted into
reading order TL,TR,BL,BR). Each frame is 5x5 -> a 3x3 interior. The
bottom-right interior corner is a CONTROL KEY that selects a transform applied
to the rest of the interior (the motif):
  key 1 = identity, 2 = flip-lr, 3 = flip-ud, anything else = rotate-cw.
Each transformed motif is centered in a 3x3 tile; the four tiles are assembled
into a 7x7 output (tiles at (0,0),(0,4),(4,0),(4,4), 0 dividers at index 3).

The earlier generator used 5x6 frames (3x4 interior -> motif could clip the 3x3
tile) and NEVER placed a key cell, so the transform was whatever a random motif
cell happened to land in the bottom-right corner (uncontrolled; the rule
silently strips that corner from the motif). This version uses 5x5 frames and
explicitly places a key (a permutation of {1,2,3,4} -> all four transforms
appear) plus an asymmetric motif in the other interior cells.

Degenerates: empty_motifs, all_same_motif, single_cell_motifs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "efb13f46eb7a"
VERSION = "3.0.0"  # 5x5 frames + explicit key cell driving transform (was 5x6, no key); vary positions
TASK_ID = "efb13f46eb7a"

SUMMARY = (
    "0-bg grid with FOUR hollow 5x5 COLOR-8 frames in a 2x2 reading-order "
    "layout (positions/spacing vary). Each frame's 3x3 interior holds: a "
    "CONTROL KEY at the bottom-right corner (value in {1,2,3,4}) and an "
    "asymmetric MOTIF (2-4 cells, distinct non-{0,8} color) in the other cells. "
    "Rule: per frame, transform the motif by the key (1=identity, 2=flip-lr, "
    "3=flip-ud, else=rotate-cw), center each in a 3x3 tile, assemble a 7x7 "
    "output. Keys are a permutation of {1,2,3,4} so all four transforms appear; "
    "motifs, colors and frame positions vary."
)

INVARIANTS = [
    "background is 0",
    "exactly 4 hollow 5x5 color-8 frames in 2x2 reading order",
    "each frame's bottom-right interior corner holds a key in {1,2,3,4}",
    "each frame's motif (2-4 cells) occupies interior cells other than the corner",
    "keys across the 4 frames cover all four transforms (permutation of 1..4)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_motifs", "all_same_motif", "single_cell_motifs")
HELPFUL_TEXTURES = PALETTE_KINDS

# asymmetric motifs within the 3x3 interior, none using the (2,2) key corner
_MOTIFS = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 0), (2, 0)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 0), (1, 0), (1, 1), (1, 2)],
]

AXES = {
    "grid_h":         {"type": "int", "default": "rng 13..18", "valid": "12..20"},
    "grid_w":         {"type": "int", "default": "rng 13..18", "valid": "12..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "four_frames_2x2",
                       "valid": "four_frames_2x2"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "1..8"},
    "density":        {"type": "str", "default": "fixed_layout", "valid": "fixed_layout"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|empty_motifs|all_same_motif|single_cell_motifs"},
}


def _draw_frame(g, r0, c0):
    for c in range(c0, c0 + 5):
        g[r0][c] = 8
        g[r0 + 4][c] = 8
    for r in range(r0, r0 + 5):
        g[r][c0] = 8
        g[r][c0 + 4] = 8


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 13, 14); w = ctx.draw_int("grid_w", 13, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 20); w = ctx.draw_int("grid_w", 16, 20)
    else:
        h = ctx.draw_int("grid_h", 14, 17); w = ctx.draw_int("grid_w", 14, 17)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    # clean 2x2 grid of frames with varied position/spacing (keeps reading order)
    top_r = rng.randint(0, max(0, (h - 10) // 2))
    left_c = rng.randint(0, max(0, (w - 10) // 2))
    bottom_r = rng.randint(top_r + 5 + 1, h - 5)
    right_c = rng.randint(left_c + 5 + 1, w - 5)
    positions = [(top_r, left_c), (top_r, right_c),
                 (bottom_r, left_c), (bottom_r, right_c)]

    keys = [1, 2, 3, 4]
    rng.shuffle(keys)                                  # all four transforms appear
    for (r0, c0), key in zip(positions, keys):
        _draw_frame(g, r0, c0)
        motif = rng.choice(_MOTIFS)
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
        for (dr, dc) in motif:                         # interior top-left = (r0+1, c0+1)
            g[r0 + 1 + dr][c0 + 1 + dc] = color
        g[r0 + 3][c0 + 3] = key                        # control key at interior corner
    return g


def _draw_from_degenerate(name, rng):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    positions = [(1, 1), (1, 8), (8, 1), (8, 8)]
    for r0, c0 in positions:
        _draw_frame(g, r0, c0)
    if name == "empty_motifs":
        # frames + keys only, no motif -> tiles empty
        for r0, c0 in positions:
            g[r0 + 3][c0 + 3] = 1
        return g
    if name == "all_same_motif":
        for r0, c0 in positions:
            for dr, dc in [(0, 0), (0, 1), (1, 0)]:
                g[r0 + 1 + dr][c0 + 1 + dc] = 3
            g[r0 + 3][c0 + 3] = 1
        return g
    if name == "single_cell_motifs":
        for (r0, c0), color in zip(positions, [1, 2, 4, 6]):
            g[r0 + 1][c0 + 1] = color
            g[r0 + 3][c0 + 3] = 2
        return g
    return g
