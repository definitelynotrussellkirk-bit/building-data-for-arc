"""Generator for arc_puzzle_bank_eighteenth21:E124.

Fill the one missing arm of each partial plus.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_motifs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, full_plus, missing_two_arms.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fc999420d3aa"
VERSION = "2.2.0"  # add executable self_check for partial-plus invariants
TASK_ID = "fc999420d3aa"

SUMMARY = (
    "0-bg grid (h~6-9, w~7-10) with 1-3 "
    "PARTIAL PLUS-SHAPED MOTIFS, each in a "
    "DISTINCT non-zero color from {1..9}. "
    "Each motif has a CENTER cell and EXACTLY "
    "3 of its 4 cardinal arm cells filled "
    "(up, down, left, right) with the same "
    "color — the 4th arm position is "
    "initially 0 (the MISSING ARM, randomly "
    "chosen). Partial pluses are isolated by "
    "≥2-cell margin so they don't interact. "
    "Rule: for EVERY PARTIAL PLUS motif "
    "(center cell with exactly 3 cardinal "
    "same-color neighbors), IDENTIFY the "
    "MISSING ARM (the single in-bounds "
    "cardinal cell that is currently 0). FILL "
    "that missing arm cell with the SAME color "
    "as the rest of the motif. The center and "
    "existing 3 arms STAY. Net: each "
    "3-arm-plus motif gets its missing arm "
    "completed in its color."
)

INVARIANTS = [
    "background is 0",
    "each motif has a center and exactly three matching cardinal arms",
    "the missing in-bounds arm cell is initially zero",
    "partial plus motifs are isolated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "full_plus", "missing_two_arms")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6-8 easy / 7-10 med / 9-14 hard", "valid": "5..18"},
    "grid_w":         {"type": "int", "default": "7-9 easy / 8-12 med / 11-16 hard", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_motifs":       {"type": "int", "default": "1-2 easy / 2-3 med / 3-6 hard", "valid": "1..6"},
    "n_decoys":       {"type": "int", "default": "0-1 easy / 1-2 med / 1-3 hard", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "per-motif colors", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "isolated_partial_pluses + decoys",
                       "valid": "isolated_partial_pluses"},
    "n_distinct_colors": {"type": "int", "default": "up to 9", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_DELTAS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _clear(g, r, c):
    h, w = len(g), len(g[0])
    for rr in range(max(0, r - 2), min(h, r + 3)):
        for cc in range(max(0, c - 2), min(w, c + 3)):
            if g[rr][cc] != 0:
                return False
    return True


def _fires(g):
    """Cells the rule completes: exactly 3 same-value cardinal neighbours + 1 zero."""
    h, w = len(g), len(g[0])
    out = set()
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v == 0:
                continue
            nb = [(r + dr, c + dc) for dr, dc in _DELTAS]
            same = sum(1 for rr, cc in nb if 0 <= rr < h and 0 <= cc < w and g[rr][cc] == v)
            zeros = sum(1 for rr, cc in nb if 0 <= rr < h and 0 <= cc < w and g[rr][cc] == 0)
            if same == 3 and zeros == 1:
                out.add((r, c))
    return out



def self_check(grid, *, difficulty=None, meta=None):
    """Executable input invariants for partial-plus completion."""
    errs = []
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid must be a non-empty rectangular list of rows"]
    w = len(grid[0])
    if w == 0 or any(len(row) != w for row in grid):
        return ["grid must be rectangular and non-empty"]
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if not isinstance(v, int) or not 0 <= v <= 9:
                errs.append(f"cell ({r},{c}) has non-ARC color {v!r}")
    firing = _fires(grid)
    if difficulty not in DEGENERATE_TEXTURES and not firing:
        errs.append("helpful instances should contain at least one completable 3-arm plus")
    h = len(grid)
    for r, c in firing:
        v = grid[r][c]
        zeros = []
        for dr, dc in _DELTAS:
            rr, cc = r + dr, c + dc
            if not (0 <= rr < h and 0 <= cc < w):
                errs.append("firing plus is too close to the border")
                continue
            if grid[rr][cc] == 0:
                zeros.append((rr, cc))
            elif grid[rr][cc] != v:
                errs.append("firing plus has a mismatched arm color")
        if len(zeros) != 1:
            errs.append("firing plus should have exactly one missing zero arm")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 7, 9)
        nm_lo, nm_hi, nd_hi = 1, 2, 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 11, 16)
        nm_lo, nm_hi, nd_hi = 3, 6, 3
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        nm_lo, nm_hi, nd_hi = 2, 3, 2
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    target = rng.randint(nm_lo, nm_hi)
    n_decoy = rng.randint(0, nd_hi)

    def free_center():
        for _ in range(60):
            r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
            if _clear(g, r, c):
                return r, c
        return None

    # TARGET partial pluses: center + 3 arms (1 missing) -> the rule completes them.
    placed = 0
    for _ in range(target * 4):
        if placed >= target:
            break
        pos = free_center()
        if pos is None:
            continue
        r, c = pos
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        missing = rng.choice(_DELTAS)
        g[r][c] = color
        for dr, dc in _DELTAS:
            if (dr, dc) != missing:
                g[r + dr][c + dc] = color
        placed += 1
    if placed == 0:                          # guarantee >=1 completable plus
        g[1][1] = 1; g[0][1] = 1; g[2][1] = 1; g[1][0] = 1   # missing right arm

    # DECOY structures the rule must NOT complete: full plus (4 arms, 0 zero) or a
    # 2-arm partial (only 2 same neighbours). Isolated so they self-determine.
    for _ in range(n_decoy * 4):
        if n_decoy <= 0:
            break
        pos = free_center()
        if pos is None:
            break
        r, c = pos
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        g[r][c] = color
        if rng.random() < 0.5:               # full plus (no missing arm)
            for dr, dc in _DELTAS:
                g[r + dr][c + dc] = color
        else:                                # 2-arm partial
            for dr, dc in rng.sample(_DELTAS, 2):
                g[r + dr][c + dc] = color
        n_decoy -= 1

    # GATE: the rule must fire exactly on the target plus-centers and nowhere else.
    # If a decoy accidentally fires (or layout interaction creates a spurious 3+1),
    # rebuild deterministically with a single clean plus.
    if len(_fires(g)) != placed:
        g = full_grid(h, w, 0)
        g[1][1] = 1; g[0][1] = 1; g[2][1] = 1; g[1][0] = 1   # one missing-right-arm plus
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # blank → no partial pluses to complete
        return g
    if name == "full_plus":
        # complete 5-cell plus → no missing arm to fill, rule is identity
        cr, cc = 3, 4
        g[cr][cc] = 4
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            g[cr + dr][cc + dc] = 4
        return g
    if name == "missing_two_arms":
        # only 2 arms present → "exactly three" precondition fails
        cr, cc = 3, 4
        g[cr][cc] = 4
        g[cr - 1][cc] = 4; g[cr][cc + 1] = 4
        return g
    return g
