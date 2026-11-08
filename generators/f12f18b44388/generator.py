"""Generator for arc_additional_puzzle_bank_volume10:E65.

Rule (canonical): every 2x2 window whose blue (color-1) cells sit on EXACTLY
one diagonal (the other diagonal empty) is filled solid with cyan (8). Every
other configuration is left untouched — including non-diagonal blue configs
(horizontal/vertical pairs, single dots, full 2x2 blocks) and any other-color
shapes. When no diagonal pair exists the output equals the input.

The earlier generator emitted ONLY clean diagonal blue pairs on a blank grid,
so the discriminator was never exercised: no other colors, no negative blue
configs, no identity case. This version restores the canonical distribution.

Degenerates: no_pairs, full_2x2_filled, single_diagonal.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f12f18b44388"
# 2.1.0: the forced ~1/6 "identity flavor" (n_pos=0 -> no diagonal pair -> output
# == input) is a pure no-op demo that never exercises the rule. Every default
# instance now carries >=1 diagonal pair (the discriminator is still exercised by
# the always-present negative blue configs that stay unchanged). Adds self_check.
# 2.0.0: add other-color decoys + negative blue configs (was diagonal pairs only)
VERSION = "2.1.0"
TASK_ID = "f12f18b44388"
SUMMARY = (
    "0-bg grid with: (a) color-1 DIAGONAL 2x2 pairs (the positives the rule "
    "fills solid 8), (b) NEGATIVE blue configs — horizontal/vertical pairs, "
    "single dots, full 2x2 blocks — that must stay unchanged, and (c) "
    "other-color decoy shapes the rule ignores. Every blue feature is "
    "moat-separated so no cross-feature 2x2 window accidentally forms a "
    "diagonal. Counts, sizes, colors, both diagonal orientations and grid "
    "shape (incl. non-square) all vary; some instances have 0 diagonal pairs "
    "(identity output, matching canonical)."
)

INVARIANTS = [
    "background is 0",
    "rule fills with 8 ONLY 2x2 windows where blue is on exactly one diagonal "
    "(off-diagonal corners empty)",
    "non-diagonal blue configs (h/v pairs, singles, full 2x2) and other-color "
    "decoys are present and must remain unchanged",
    "every blue feature is moat-separated (Chebyshev>=2) so no cross-feature "
    "2x2 window forms a diagonal and pair off-diagonals stay 0",
    "both diagonal orientations can appear; some instances have 0 pairs (identity)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "full_2x2_filled", "single_diagonal")
HELPFUL_TEXTURES = PALETTE_KINDS

# decoy colors: anything but bg(0), the blue positive marker(1), the fill(8)
_DECOY_COLORS = (2, 3, 4, 5, 6, 7, 9)

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..18", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..18", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 1..7 (0 on identity)", "valid": "0..10"},
    "n_neg":          {"type": "int", "default": "rng 1..6", "valid": "0..10"},
    "n_decoy":        {"type": "int", "default": "rng 1..7", "valid": "0..10"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "separated_diagonal_blue_pairs",
                       "valid": "separated_diagonal_blue_pairs"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "1..8"},
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
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 7, 9)
        n_pos = ctx.draw_int("n_pairs", 1, 3)
        n_neg = ctx.draw_int("n_neg", 1, 2)
        n_decoy = ctx.draw_int("n_decoy", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 18); w = ctx.draw_int("grid_w", 12, 18)
        n_pos = ctx.draw_int("n_pairs", 3, 7)
        n_neg = ctx.draw_int("n_neg", 3, 6)
        n_decoy = ctx.draw_int("n_decoy", 3, 7)
    else:
        h = ctx.draw_int("grid_h", 9, 13); w = ctx.draw_int("grid_w", 9, 13)
        n_pos = ctx.draw_int("n_pairs", 2, 5)
        n_neg = ctx.draw_int("n_neg", 2, 4)
        n_decoy = ctx.draw_int("n_decoy", 2, 5)
    n_pos = max(1, n_pos)   # always >=1 diagonal pair so the rule fills something

    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    blue: set[tuple[int, int]] = set()

    def blue_moat_ok(cells):
        """cells empty AND Chebyshev>=2 from every existing blue cell, so no
        cross-feature 2x2 window can form a diagonal and the pair's own
        off-diagonal corners stay 0."""
        for r, c in cells:
            if not (0 <= r < h and 0 <= c < w) or g[r][c] != 0:
                return False
            for br, bc in blue:
                if max(abs(r - br), abs(c - bc)) < 2:
                    return False
        return True

    def place_blue(cells):
        if blue_moat_ok(cells):
            for r, c in cells:
                g[r][c] = 1
                blue.add((r, c))
            return True
        return False

    # --- positives: diagonal 2x2 pairs (both orientations) ---
    placed = 0
    for _ in range(300):
        if placed >= n_pos:
            break
        r = rng.randint(0, h - 2); c = rng.randint(0, w - 2)
        cells = ([(r, c), (r + 1, c + 1)] if rng.random() < 0.5
                 else [(r, c + 1), (r + 1, c)])
        if place_blue(cells):
            placed += 1
    # guarantee >=1 diagonal pair so the rule fills (output != input)
    if placed == 0:
        for r in range(h - 1):
            for c in range(w - 1):
                if place_blue([(r, c), (r + 1, c + 1)]):
                    placed = 1; break
            if placed:
                break

    # --- negatives: blue configs the rule must NOT fill ---
    placed = 0
    for _ in range(400):
        if placed >= n_neg:
            break
        r = rng.randint(0, h - 2); c = rng.randint(0, w - 2)
        kind = rng.choice(["hpair", "vpair", "single", "full2x2"])
        if kind == "hpair":
            cells = [(r, c), (r, c + 1)]
        elif kind == "vpair":
            cells = [(r, c), (r + 1, c)]
        elif kind == "single":
            cells = [(r, c)]
        else:
            cells = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
        if place_blue(cells):
            placed += 1

    # --- decoys: other-color shapes the rule ignores (moat>=2 from blue) ---
    n_dc = min(n_decoy, len(_DECOY_COLORS))
    colors = list(_DECOY_COLORS)
    rng.shuffle(colors)
    for color in colors[:n_dc]:
        _place_decoy(g, rng, color, rng.randint(1, 4), blue, h, w)

    if not blue and not any(v for row in g for v in row):
        g[1][1] = 1; g[2][2] = 1   # guarantee non-blank fallback
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """At least one 2x2 window has blue(1) on exactly one diagonal with the other
    diagonal empty (0) — the pattern the rule fills with 8, so output != input."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if (a == 1 and e == 1 and b == 0 and d == 0) or \
               (b == 1 and d == 1 and a == 0 and e == 0):
                return []
    return ["no diagonal blue 2x2 pair — the rule fills nothing (output == input)"]


def _place_decoy(g, rng, color, size, blue, h, w):
    """Place a small connected blob of `color`, not overlapping anything and
    Chebyshev>=2 from any blue cell (so it never touches a diagonal pair's
    off-diagonal corners and can't alter the rule's fills)."""
    for _ in range(60):
        sr = rng.randint(0, h - 1); sc = rng.randint(0, w - 1)
        cells = {(sr, sc)}
        while len(cells) < size:
            br, bc = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            nr, nc = br + dr, bc + dc
            if 0 <= nr < h and 0 <= nc < w:
                cells.add((nr, nc))
            else:
                break
        ok = True
        for r, c in cells:
            if g[r][c] != 0:
                ok = False; break
            for br, bc in blue:
                if max(abs(r - br), abs(c - bc)) < 2:
                    ok = False; break
            if not ok:
                break
        if ok:
            for r, c in cells:
                g[r][c] = color
            return True
    return False


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank -> no diagonal pairs to expand into solid blocks
        return g
    if name == "full_2x2_filled":
        # 2x2 already solid blue -> "exactly one diagonal" precondition fails
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 1
        return g
    if name == "single_diagonal":
        # only one cell of pair -> "diagonal pair" precondition fails
        g[1][1] = 1  # missing (2,2)
        g[4][5] = 1
        return g
    return g
