"""Generator for arc_puzzle_bank_21_set16_s:S16_H2 — crop the odd pair by orientation/length.

Rule (verified from canonical Racket): every colour that appears exactly TWICE is
a PAIR; its two cells are the endpoints of a line whose signature is
(orientation, span-length) — orientation 0=horizontal, 1=vertical, 2=diagonal.
The pair whose signature is UNIQUE among all pairs is the odd one; the rule draws
its full span and crops it, recoloured 8.

The previous body was the generic scatter template, which makes multi-cell
connected motifs (each colour once), so there were no two-cell pairs and the
output never varied (distinct_out=1). This rewrite CONSTRUCTS several colour
pairs: most share one (orientation, length) signature and exactly one is unique
(the odd pair), so the cropped output varies with the odd pair's line.

Axes: pair count, the common signature, the odd pair's orientation/length.
Degenerates: all_same_sig, single_pair, two_unique.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "76c3f9d7128a"
VERSION = "2.2.1"  # distinct=12/out_sh=12: output is the ODD pair's span-line crop; distinct = orientations(3) x odd lengths(2..5 = 4) = 12. Widen odd length to 2..9 (+ bigger grids) -> more line lengths/shapes.
TASK_ID = "76c3f9d7128a"

SUMMARY = ("Several colour pairs (two cells each) form horizontal/vertical/diagonal lines; the "
           "pair with a unique (orientation, length) signature is the odd one, whose line the "
           "rule crops and recolours 8. Pair count, the common signature and the odd pair vary.")

INVARIANTS = [
    "each placed colour appears exactly twice (a pair of line endpoints)",
    "all but one pair share a single (orientation, span-length) signature",
    "exactly one pair has a unique signature (the odd one out)",
]

DEGENERATE_TEXTURES = ("all_same_sig", "single_pair", "two_unique")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "grid_w":     {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "n_pairs":    {"type": "int", "default": "3 easy / 3-4 hard", "valid": "3..5"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "default|warm|cool|varied|all_same_sig|single_pair|two_unique"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥3 distinct non-{0,8} colors each appearing exactly twice (pairs)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    errs = []
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w)
                     if grid[r][c] not in (0, 8))
    if len(counts) < 3:
        errs.append(f"expected ≥3 distinct non-{{0,8}} pair colors, got {len(counts)}")
    bad = [c for c, n in counts.items() if n != 2]
    if bad:
        errs.append(f"colors not appearing exactly twice: {bad[:3]}")
    if any(grid[r][c] == 8 for r in range(h) for c in range(w)):
        errs.append("color-8 appears in input (should only be in output)")
    return errs


_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)   # never 8 (output colour)


def _endpoints(orient, length, r, c):
    """Two endpoints of a line of given orientation (0=h,1=v,2=diag) and span length."""
    d = length - 1
    if orient == 0:
        return (r, c), (r, c + d)
    if orient == 1:
        return (r, c), (r + d, c)
    return (r, c), (r + d, c + d)


def _fits(orient, length, r, c, h, w):
    (r1, c1), (r2, c2) = _endpoints(orient, length, r, c)
    return 0 <= r1 < h and 0 <= c1 < w and 0 <= r2 < h and 0 <= c2 < w


def _place_pair(g, orient, length, color, rng, occupied):
    h, w = len(g), len(g[0])
    for _ in range(200):
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if not _fits(orient, length, r, c, h, w):
            continue
        (r1, c1), (r2, c2) = _endpoints(orient, length, r, c)
        if (r1, c1) in occupied or (r2, c2) in occupied:
            continue
        g[r1][c1] = color; g[r2][c2] = color
        occupied.add((r1, c1)); occupied.add((r2, c2))
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12); w = ctx.draw_int("grid_w", 10, 12)
        n = ctx.draw_int("n_pairs", 3, 3); odd_hi = 6
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 13, 18)
        n = ctx.draw_int("n_pairs", 4, 5); odd_hi = 9
    else:
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 11, 15)
        n = ctx.draw_int("n_pairs", 3, 4); odd_hi = 9
    rng = ctx.draw_rng("layout")

    # common signature for n-1 pairs, and a distinct unique signature for the odd.
    # the odd's (orientation, length) drives the output -> widen its length range.
    common = (rng.randint(0, 2), rng.randint(2, 5))
    odd = common
    while odd == common:
        odd = (rng.randint(0, 2), rng.randint(2, odd_hi))
    sigs = [common] * (n - 1) + [odd]
    rng.shuffle(sigs)
    colors = rng.sample(_COLORS, min(n, len(_COLORS)))

    g = full_grid(h, w, 0)
    occupied = set()
    placed = 0
    for (orient, length), color in zip(sigs, colors):
        if _place_pair(g, orient, length, color, rng, occupied):
            placed += 1
    if placed < n:                       # retry-light fallback: ensure the odd is present
        # if some common pair failed, the odd (unique) may still be well defined;
        # only bail to a clean degenerate if fewer than 2 pairs landed
        if placed < 2:
            return _draw_from_degenerate("single_pair", None)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    occ = set()
    if name == "single_pair":
        # one pair -> its signature is trivially unique
        g[2][2] = 3; g[2][5] = 3
        return g
    if name == "two_unique":
        # two pairs, both signatures unique -> rule takes the first in scan order
        g[1][1] = 3; g[1][4] = 3                 # horizontal len 4
        g[6][2] = 4; g[9][2] = 4                 # vertical len 4
        return g
    # all_same_sig -> every pair shares one signature -> none unique -> first pair wins
    for i, color in enumerate((3, 4, 5)):
        r = 1 + i * 3
        g[r][1] = color; g[r][3] = color         # all horizontal len 3
    return g
