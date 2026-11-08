"""Generator for 9f5f939b.

Rule: each color-8 cell shoots rays in the four cardinal directions to
the first color-1 cell. It becomes 4 iff all four first-hits are at the
SAME distance d, the up/down hits lie on VERTICAL bars and the left/right
hits lie on HORIZONTAL bars. Otherwise it stays 8.

This generator places 1-3 self-contained "bar-plus" configurations: a
color-8 centre with a vertical bar above and below and a horizontal bar
left and right, each at distance d (near end exactly at d, extending
away). Every centre qualifies and becomes 4.

Combinatorial axes: grid size, the number of configs, each config's
distance, bar lengths and position.
Degenerates: no_bars, no_center, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9656e61f0d19"
VERSION = "3.0.1"  # add self_check; diversity: multiple configs, random distance/bar-len/position/grid (was 1 center, sized-to-fit ~13)
TASK_ID = "9656e61f0d19"
SUMMARY = (
    "0-bg grid (size varies). 1-3 BAR-PLUS configs, each a color-8 (cyan) "
    "centre with a color-1 (blue) VERTICAL bar at distance d above and "
    "below and a HORIZONTAL bar at distance d left and right (near end at "
    "exactly d, bars extend away). Rule: a centre becomes 4 (yellow) iff "
    "all four first-hit 1s are equidistant and correctly oriented "
    "(vertical rays -> vertical bars, horizontal rays -> horizontal bars). "
    "Each config qualifies. The grid size, config count, and each config's "
    "distance/bar-lengths/position all vary freely (was one centre on a "
    "sized-to-fit grid, ~13 distinct)."
)

INVARIANTS = [
    "background is 0; centres are color 8, bars are color 1",
    "each config: vertical bars above/below and horizontal bars left/right, all at the same distance d",
    "each config's bars have clear ray paths (near end exactly at d)",
]

DEGENERATE_TEXTURES = ("no_bars", "no_center", "full_grid")
HELPFUL_TEXTURES = ("close", "mid", "far")

AXES = {
    "distance":       {"type": "int", "default": "varies", "valid": "2..6"},
    "grid_h":         {"type": "int", "default": "varies", "valid": "13..28"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "13..30"},
    "n_centers":      {"type": "int", "default": "varies", "valid": "1..3"},
    "bar_len":        {"type": "int", "default": "varies", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "configs_apart", "valid": "configs_apart"},
    "texture":        {"type": "str", "default": "alias for distance",
                       "valid": "close|mid|far|no_bars|no_center|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 color-8 center; ≥4 color-1 bar cells (each config needs at least 4)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    n8 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 8)
    n1 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    if n8 < 1:
        errs.append(f"expected ≥1 color-8 center; got {n8}")
    if n1 < 4:
        errs.append(f"expected ≥4 color-1 bar cells (min per config); got {n1}")
    return errs


def _reserve(occ, top, left, bh, bw, h, w, margin=1):
    for r in range(top - margin, top + bh + margin):
        for c in range(left - margin, left + bw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, dr, nr = (13, 16), (13, 16), (2, 3), (1, 1)
    elif difficulty == "hard":
        hr, wr, dr, nr = (20, 28), (22, 30), (2, 6), (2, 3)
    else:
        hr, wr, dr, nr = (16, 22), (16, 24), (2, 4), (1, 2)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        placed = 0
        for _ in range(rng.randint(*nr)):
            d = rng.randint(*dr)
            L = rng.randint(2, 3)
            half = d + L - 1                   # arm reaches center +/- half
            box = 2 * half + 1
            if box + 2 > h or box + 2 > w:
                continue
            for _t in range(40):
                top = rng.randint(0, h - box); left = rng.randint(0, w - box)
                if not _reserve(occ, top, left, box, box, h, w, margin=1):
                    continue
                r = top + half; c = left + half      # centre
                g[r][c] = 8
                for i in range(L):                   # up bar (extends away/up)
                    g[r - d - i][c] = 1
                    g[r + d + i][c] = 1              # down bar
                    g[r][c - d - i] = 1              # left bar
                    g[r][c + d + i] = 1              # right bar
                placed += 1
                break
        if placed >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 13, 13
    g = full_grid(h, w, 0)
    if name == "no_bars":
        g[6][6] = 8
        return g
    if name == "no_center":
        g[3][6] = 1; g[9][6] = 1
        g[6][3] = 1; g[6][9] = 1
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 1
        return g
    return g
