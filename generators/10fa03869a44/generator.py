"""Generator for arc_additional_puzzle_bank_volume6:E37.

Rule: empty diagonal midpoints between yellow pairs are filled cyan.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_gaps,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, partial_pair, midpoint_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "10fa03869a44"
VERSION = "1.2.1"  # +self_check
TASK_ID = "10fa03869a44"
SUMMARY = "Empty diagonal midpoints between yellow pairs are filled cyan. Grids also carry decoy color-5 markers (ignored by the rule) and lone scattered 4s with no diagonal partner (not filled)."

INVARIANTS = [
    "background is 0",
    "each target gap has yellow cells on opposite diagonal corners",
    "the midpoint starts empty",
    "target triples are separated so fills do not interact",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "partial_pair", "midpoint_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_gaps":         {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "spaced_diagonal_pairs",
                       "valid": "spaced_diagonal_pairs"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..2"},
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
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_gaps = ctx.draw_int("n_gaps", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 11, 13)
        n_gaps = ctx.draw_int("n_gaps", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
        n_gaps = ctx.draw_int("n_gaps", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    centers: list[tuple[int, int]] = []
    for _ in range(220):
        if len(centers) >= n_gaps:
            break
        r = rng.randint(1, h - 2)
        c = rng.randint(1, w - 2)
        if any(abs(r - rr) < 3 and abs(c - cc) < 3 for rr, cc in centers):
            continue
        if rng.choice([False, True]):
            g[r - 1][c - 1] = 4
            g[r + 1][c + 1] = 4
        else:
            g[r - 1][c + 1] = 4
            g[r + 1][c - 1] = 4
        centers.append((r, c))
    if not centers:
        g[1][1] = 4
        g[3][3] = 4
    # Decoy color-5 markers (rule ignores them) + lone scattered 4s (no
    # diagonal partner -> rule never fills near them). Place them only on
    # currently-empty cells whose 4 diagonal neighbors are all empty, so they
    # can't accidentally complete a diagonal triple.
    def _safe_lone(r, c):
        if g[r][c] != 0:
            return False
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                return False
        return True
    for _ in range(rng.randint(1, 3)):
        for _t in range(20):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if _safe_lone(r, c):
                g[r][c] = 5
                break
    for _ in range(rng.randint(0, 2)):
        for _t in range(20):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if _safe_lone(r, c):
                g[r][c] = 4
                break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """At least 2 yellow (4) cells and at least one pair shares a valid diagonal midpoint."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    fours = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    if len(fours) < 2:
        errors.append(f"need >=2 yellow (4) cells for diagonal pairs, got {len(fours)}")
        return errors
    # Check at least one pair with a valid diagonal midpoint (empty center)
    found = False
    for i in range(len(fours)):
        r1, c1 = fours[i]
        for j in range(i + 1, len(fours)):
            r2, c2 = fours[j]
            if abs(r2 - r1) == 2 and abs(c2 - c1) == 2:
                mr, mc = (r1 + r2) // 2, (c1 + c2) // 2
                if grid[mr][mc] == 0:
                    found = True
                    break
        if found:
            break
    if not found:
        errors.append("no diagonal pair with empty midpoint found")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no diagonal pairs, rule has no midpoints to fill
        return g
    if name == "partial_pair":
        # single yellow cell with no diagonal partner → predicate "pair" fails
        g[2][2] = 4
        g[5][5] = 4
        g[7][7] = 4
        return g
    if name == "midpoint_filled":
        # diagonal pair with midpoint already non-zero → predicate "empty midpoint" fails
        g[2][2] = 4; g[4][4] = 4
        g[3][3] = 6  # midpoint already filled
        g[5][7] = 4; g[7][5] = 4
        g[6][6] = 8
        return g
    return g
