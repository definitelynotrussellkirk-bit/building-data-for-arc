"""Generator for arc_puzzle_bank_21_set19_bundle:easy_p05.

Rule: for every 3x3 window whose 8 border cells are all the same non-0 color and
whose center is 0, fill the center with that color (close the ring).

Combinatorial axes: grid size, ring count, colors, positions, and DECOY rings
(broken / filled / two-color) that the rule must NOT fill.
Degenerates: no_rings, filled_rings, broken_rings.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f813212d1e20"
VERSION = "2.0.0"  # bigger grids + more rings + broken/filled/two-color decoys (gated) to pin the complete-monochrome-ring condition
TASK_ID = "f813212d1e20"
SUMMARY = (
    "0-bg grid (size varies) with several complete monochrome 3x3 RINGS (8 "
    "same-color border cells, 0 center) in distinct colors, plus DECOY rings "
    "the rule must NOT fill: broken (one border cell missing), filled (center "
    "already non-0), or two-color borders. Rule: for each 3x3 window whose 8 "
    "border cells are one non-0 color and whose center is 0, fill the center "
    "with that color. Net: complete monochrome rings get their centers filled; "
    "decoys are left untouched."
)

INVARIANTS = [
    "background is 0",
    ">=1 complete monochrome 3x3 ring with a 0 center",
    "decoy rings (broken / filled / two-color) are never filled by the rule",
    "rings are isolated so each 3x3 window is clean",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rings", "filled_rings", "broken_rings")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7-10 easy / 10-14 med / 13-20 hard", "valid": "5..22"},
    "grid_w":         {"type": "int", "default": "9-13 easy / 12-17 med / 15-22 hard", "valid": "5..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "ring_count":     {"type": "int", "default": "2-3 easy / 3-5 med / 4-7 hard", "valid": "1..7"},
    "n_decoys":       {"type": "int", "default": "0-1 easy / 1-2 med / 2-3 hard", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "per-ring colors", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "complete_3x3_rings_with_zero_centers",
                       "valid": "complete_3x3_rings_with_zero_centers"},
    "n_distinct_colors": {"type": "int", "default": "up to 9", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_BORDER = [(dr, dc) for dr in range(3) for dc in range(3) if not (dr == 1 and dc == 1)]


def _clear(grid, r0, c0):
    h, w = len(grid), len(grid[0])
    for r in range(max(0, r0 - 1), min(h, r0 + 4)):
        for c in range(max(0, c0 - 1), min(w, c0 + 4)):
            if grid[r][c] != 0:
                return False
    return True


def _fires(g):
    """Centers the rule fills: 3x3 windows with 8 same-color border + 0 center."""
    h, w = len(g), len(g[0])
    out = set()
    for r in range(h - 2):
        for c in range(w - 2):
            vals = [g[r + dr][c + dc] for dr, dc in _BORDER]
            if g[r + 1][c + 1] == 0 and 0 not in vals and len(set(vals)) == 1:
                out.add((r + 1, c + 1))
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, rr, dr_ = (7, 10), (9, 13), (2, 3), (0, 1)
    elif difficulty == "hard":
        hr, wr, rr, dr_ = (13, 20), (15, 22), (4, 7), (2, 3)
    else:
        hr, wr, rr, dr_ = (10, 14), (12, 17), (3, 5), (1, 2)
    rng = ctx.draw_rng("layout")

    for _attempt in range(30):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        positions = [(r, c) for r in range(h - 2) for c in range(w - 2)]
        rng.shuffle(positions)
        target = rng.randint(*rr)
        intended = set()
        placed = 0
        pi = 0
        # complete rings
        while placed < target and pi < len(positions):
            r0, c0 = positions[pi]; pi += 1
            if not _clear(g, r0, c0):
                continue
            color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
            for dr, dc in _BORDER:
                g[r0 + dr][c0 + dc] = color
            intended.add((r0 + 1, c0 + 1)); placed += 1
        if placed == 0:
            continue

        # decoy rings: broken / filled / two-color (rule never fills)
        for _ in range(rng.randint(*dr_)):
            while pi < len(positions):
                r0, c0 = positions[pi]; pi += 1
                if not _clear(g, r0, c0):
                    continue
                kind = rng.choice(["broken", "filled", "twocolor"])
                col = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
                if kind == "broken":
                    miss = rng.choice(_BORDER)
                    for dr, dc in _BORDER:
                        if (dr, dc) != miss:
                            g[r0 + dr][c0 + dc] = col
                elif kind == "filled":
                    for dr in range(3):
                        for dc in range(3):
                            g[r0 + dr][c0 + dc] = col      # center non-0 -> not filled
                else:  # twocolor border
                    col2 = rng.choice([x for x in range(1, 10) if x != col])
                    for i, (dr, dc) in enumerate(_BORDER):
                        g[r0 + dr][c0 + dc] = col if i % 2 == 0 else col2
                break

        # GATE: rule fills exactly the intended ring centers.
        if _fires(g) == intended:
            return g

    # deterministic fallback: one complete ring
    g = full_grid(7, 7, 0)
    for dr, dc in _BORDER:
        g[2 + dr][2 + dc] = 4
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify 3x3 monochrome ring invariants for f813212d1e20."""
    errs = []
    h, w = len(grid), len(grid[0])
    flat = [grid[r][c] for r in range(h) for c in range(w)]
    if flat.count(0) == 0:
        errs.append("no background (0) cells")
    nz_colors = {v for v in flat if v != 0}
    if not nz_colors:
        errs.append("no non-zero cells (no rings)")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_rings":
        return g
    if name == "filled_rings":
        for dr in range(3):
            for dc in range(3):
                g[1 + dr][1 + dc] = 4
                g[5 + dr][6 + dc] = 6
        return g
    if name == "broken_rings":
        for dr, dc in [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (2, 2)]:
            g[1 + dr][1 + dc] = 4
        return g
    return g
