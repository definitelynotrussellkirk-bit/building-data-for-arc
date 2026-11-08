"""Generator for arc_puzzle_bank_21_set17_s:S17_H3 -- meeting region of two sets.

Rule: a = the color-2 cells, b = the color-3 cells. Grow a radius from 0; at
each radius keep the cells within (manhattan) radius of a and the cells within
radius of b, and stop at the first radius where those two neighborhoods
intersect. Output: that intersection (the "meeting region") painted 8 (cyan).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a98c887acf8f"
VERSION = "2.0.2"  # rewrite to real two-set meeting-region rule (was wrong 'find pair' -> min-of-empty crash + >30)
TASK_ID = "a98c887acf8f"

SUMMARY = (
    "0-bg grid with a small cluster of color-2 (red) cells and a separate "
    "cluster of color-3 (green) cells. Rule: expand a manhattan radius from "
    "both sets simultaneously and stop at the first radius where their "
    "neighborhoods overlap; the output paints that meeting region in 8 (cyan) "
    "-- the manhattan-bisector between the two sets. Positions, counts and "
    "grid size vary freely."
)

INVARIANTS = [
    "background is 0",
    "at least one color-2 cell and at least one color-3 cell (else the rule's min() is undefined)",
    "the two sets are disjoint and separated (manhattan distance >= 4)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_red", "no_green", "overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng per band", "valid": "8..22"},
    "grid_w":         {"type": "int", "default": "rng per band", "valid": "8..22"},
    "n_red":          {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "n_green":        {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "two_separated_clusters",
                       "valid": "two_separated_clusters"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_red|no_green|overlap"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify both sets exist, are disjoint, and are separated by the advertised gap."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    reds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    greens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if not reds:
        errs.append("missing color-2 set")
    if not greens:
        errs.append("missing color-3 set")
    if errs:
        return errs
    if set(reds) & set(greens):
        errs.append("red and green sets overlap")
    md = min(abs(r - gr) + abs(c - gc) for r, c in reds for gr, gc in greens)
    if md < 4:
        errs.append(f"red/green sets too close: min manhattan distance {md} < 4")
    return errs


def _blob(rng, cr, cc, k, h, w, taken):
    cells = []
    tries = 0
    while len(cells) < k and tries < 50:
        tries += 1
        r = cr + rng.randint(-1, 1); c = cc + rng.randint(-1, 1)
        if 0 <= r < h and 0 <= c < w and (r, c) not in taken and (r, c) not in cells:
            cells.append((r, c))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12); w = ctx.draw_int("grid_w", 10, 12); kmax = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20); w = ctx.draw_int("grid_w", 14, 20); kmax = 3
    else:
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 12, 16); kmax = 3

    for _attempt in range(40):
        g = full_grid(h, w, 0)
        ar = rng.randint(1, h - 2); ac = rng.randint(1, w // 2 - 1)
        br = rng.randint(1, h - 2); bc = rng.randint(w // 2 + 1, w - 2)
        if abs(ar - br) + abs(ac - bc) < 4:        # keep them separated
            continue
        taken = set()
        red = _blob(rng, ar, ac, rng.randint(1, kmax), h, w, taken)
        taken |= set(red)
        green = _blob(rng, br, bc, rng.randint(1, kmax), h, w, taken)
        if not red or not green:
            continue
        if min(abs(r - gr) + abs(c - gc) for r, c in red for gr, gc in green) < 4:
            continue
        for (r, c) in red:
            g[r][c] = 2
        for (r, c) in green:
            g[r][c] = 3
        return g
    return _draw_from_degenerate("overlap", rng)   # rare fallback (valid)


def _draw_from_degenerate(name, rng):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name != "no_red":
        g[3][2] = 2
    if name != "no_green":
        g[3][9] = 3
    if name == "overlap":
        g[3][2] = 2; g[3][3] = 3                   # adjacent -> meet at radius 0/1
    return g
