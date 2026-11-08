"""Generator for arc_puzzle_bank_third_21_bundle:easy_15_exact_descending_diagonal_pairs.

Rule: red down-right diagonal runs of exact length 2 are recolored cyan.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, only_distractor, anti_diag_pair.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "20eea223d645"
VERSION = "1.2.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: has color-2 cells; at least one isolated down-right diagonal pair of length 2."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    two_set = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2}
    if not two_set:
        errs.append("no color-2 cells found")
        return errs
    # Check for at least one isolated length-2 diagonal pair (start of a pair, no extension)
    pairs = [(r, c) for r, c in two_set
             if (r+1, c+1) in two_set
             and (r-1, c-1) not in two_set
             and (r+2, c+2) not in two_set]
    if not pairs:
        errs.append("no isolated length-2 down-right diagonal pair (target for recolor)")
    return errs
TASK_ID = "20eea223d645"

SUMMARY = "Color-2 cells form down-right diagonal runs of various lengths. Rule recolors EXACTLY the runs of length 2 (down-right diagonal: (r,c)+(r+1,c+1)) to color 8. Length-1 isolated 2s and length-3+ longer runs stay as 2. Off-diagonal 2s (e.g. horizontal/vertical/anti-diagonal pairs) stay too."

# Rivals: 'output is input' refuted by any demo with a length-2 run.
# 'recolor all 2s' refuted by ≥1 demo where length-1 or length-3
# stay 2. 'recolor down-right runs of any length' refuted by ≥1
# demo with a length-3 run that stays 2. 'recolor anti-diagonal
# pairs too' refuted by ≥1 demo with such pair staying 2. 3 demos
# with mix of lengths cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "target clues are isolated down-right red pairs",
    "distractor red runs have length one or three",
    "all red runs are separated so exact-run detection is unambiguous",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "only_distractor", "anti_diag_pair")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..18"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "5..22"},
    "pairs":          {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "scattered_diagonal_runs",
                       "valid": "scattered_diagonal_runs"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _can_place(g, cells):
    h, w = len(g), len(g[0])
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w) or g[r][c] != 0:
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(7, 9); w = rng.randint(8, 11)
        target = rng.randint(1, 2)
        n_distractor_short = rng.randint(0, 1); n_distractor_long = rng.randint(0, 1)
    elif difficulty == "hard":
        h = rng.randint(12, 18); w = rng.randint(14, 22)
        target = rng.randint(4, 7)
        n_distractor_short = rng.randint(2, 4); n_distractor_long = rng.randint(1, 3)
    else:
        h = rng.randint(9, 12); w = rng.randint(10, 14)
        target = rng.randint(2, 4)
        n_distractor_short = rng.randint(1, 2); n_distractor_long = rng.randint(0, 2)

    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(180):
        if placed >= target:
            break
        r = rng.randint(0, h - 2)
        c = rng.randint(0, w - 2)
        cells = [(r, c), (r + 1, c + 1)]
        if _can_place(g, cells):
            for rr, cc in cells:
                g[rr][cc] = 2
            placed += 1
    # Place length-1 distractors.
    for _ in range(80):
        if n_distractor_short <= 0:
            break
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if _can_place(g, [(r, c)]):
            g[r][c] = 2
            n_distractor_short -= 1
    # Place length-3 distractors.
    for _ in range(100):
        if n_distractor_long <= 0:
            break
        length = rng.choice([3, 4])
        if h - length < 0 or w - length < 0:
            continue
        r = rng.randint(0, h - length)
        c = rng.randint(0, w - length)
        cells = [(r + i, c + i) for i in range(length)]
        if _can_place(g, cells):
            for rr, cc in cells:
                g[rr][cc] = 2
            n_distractor_long -= 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Empty grid — rule has no length-2 down-right pairs.
        return g
    if name == "only_distractor":
        # Only length-1 and length-3 down-right runs (no length-2)
        # — rule's exact-length filter excludes; output equals input.
        g[2][2] = 2
        for i in range(3): g[5 + i][5 + i] = 2
        return g
    if name == "anti_diag_pair":
        # Anti-diagonal (down-left) red pair — rule's "down-right"
        # direction filter excludes; rule's effect invisible.
        g[2][7] = 2; g[3][6] = 2
        return g
    return g
