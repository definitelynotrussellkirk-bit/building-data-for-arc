"""Generator for puzzle 834ec97d.

Rule: bg + 1 seed cell. Rule scans for first non-zero cell. Output:
- (cr+1, cc): seed value
- cells where r ≤ cr and c % 2 == (cc % 2): paint 4
- else: 0

Combinatorial axes (8): grid_h/w, fg_color, seed_position,
position_bias, palette_size, decoy_density, parity_force,
edge_avoidance.
Degenerates: no_seed, multiple_seeds, seed_at_bottom_row.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "033db13a9d37"
VERSION = "1.2.0"
TASK_ID = "033db13a9d37"
SUMMARY = (
    "1 seed cell on bg (sometimes plus decoy cells LATER in scan "
    "order, which the rule ignores and erases); rule renders the "
    "parity-keyed pattern from the FIRST non-zero cell."
)

# Rivals: 'every non-zero cell seeds a pattern' refuted by decoy
# boards where later cells vanish. 'pattern from the largest/special
# cell' refuted likewise (scan order decides). 'output keeps the
# seed in place' refuted (echo appears at cr+1). 3 demos incl. >=1
# decoy board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 (rule's bg)",
    ">=1 non-bg cell; the FIRST in scan order is the seed",
    "decoy boards: extra cells strictly AFTER the seed in scan order "
    "(ignored and erased by the rule)",
    "seed at row r <= h-2 (so the r+1 echo is in-bounds)",
    "no color 4 in input (rule writes 4 for output)",
]

POSITION_BIAS = ("center", "spread", "edge", "corners")
DEGENERATE_TEXTURES = ("seed_at_bottom_row",)
HELPFUL_TEXTURES = POSITION_BIAS + ("decoy_cells",)

AXES = {
    "grid_h":          {"type": "int", "default": "rng 5..14", "valid": "3..18"},
    "grid_w":          {"type": "int", "default": "rng 5..14", "valid": "3..18"},
    "fg_color":        {"type": "color", "default": "rng (≠0,4)",
                        "valid": "1..9 (≠4)"},
    "seed_row":        {"type": "int", "default": "rng 0..h-2",
                        "valid": "0..h-2"},
    "seed_col":        {"type": "int", "default": "rng 0..w-1",
                        "valid": "0..w-1"},
    "position_bias":   {"type": "str", "default": "rng helpful",
                        "valid": "center|spread|edge|corners"},
    "edge_avoidance":  {"type": "bool", "default": "false",
                        "valid": "true|false"},
    "texture":         {"type": "str", "default": "alias for position_bias",
                        "valid": "center|spread|edge|corners|decoy_cells|"
                                 "seed_at_bottom_row"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 3, 6
    elif difficulty == "hard":
        h_lo, h_hi = 12, 18
    else:
        h_lo, h_hi = 5, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    fgc = int(overrides.get("fg_color",
                            ctx.draw_color("fg_color", exclude={0, 4})))
    pos_bias = (overrides.get("texture") or
                overrides.get("position_bias")
                or ctx.draw_choice("position_bias",
                                   list(POSITION_BIAS)))
    edge_avoid = bool(overrides.get("edge_avoidance", False))
    inset = 1 if edge_avoid else 0
    rmin = inset
    rmax = h - 2 - inset
    cmin = inset
    cmax = w - 1 - inset
    if rmax < rmin: rmin, rmax = 0, h - 2
    if cmax < cmin: cmin, cmax = 0, w - 1
    if pos_bias == "center":
        loci = (rmin + rmax) // 2
        locj = (cmin + cmax) // 2
    elif pos_bias == "edge":
        loci = rng.choice([rmin, rmax])
        locj = rng.choice([cmin, cmax])
    elif pos_bias == "corners":
        loci, locj = rng.choice([(rmin, cmin), (rmin, cmax),
                                 (rmax, cmin), (rmax, cmax)])
    else:
        loci = rng.randint(rmin, rmax)
        locj = rng.randint(cmin, cmax)
    if "seed_row" in overrides:
        loci = max(0, min(h - 2, int(overrides["seed_row"])))
    if "seed_col" in overrides:
        locj = max(0, min(w - 1, int(overrides["seed_col"])))
    g = full_grid(h, w, 0)
    g[loci][locj] = fgc
    if overrides.get("texture") == "decoy_cells" or (
            "texture" not in overrides
            and ctx.draw_int("decoy_roll", 0, 99) < 25):
        # extra cells strictly AFTER the seed in scan order: the rule
        # reads only the FIRST non-zero cell — these vanish
        placed = 0
        for _ in range(40):
            if placed >= rng.randint(1, 2):
                break
            r = rng.randint(loci, h - 1)
            c = rng.randint(0, w - 1)
            if (r > loci or c > locj) and g[r][c] == 0:
                g[r][c] = rng.choice([v for v in (1, 2, 3, 5, 6, 7, 8, 9)
                                      if v != fgc])
                placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """bg=0; ≥1 non-bg cell; no color 4 in input (rule writes 4 for output)."""
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    if not any(grid[r][c] != 0 for r in range(h) for c in range(w)):
        errs.append("no non-bg cell found (all zeros)")
    if any(grid[r][c] == 4 for r in range(h) for c in range(w)):
        errs.append("color 4 present in input (rule writes 4 for output)")
    return errs


def _draw_from_degenerate(name, h, w, rng):
    """seed_at_bottom_row — the seed echo at cr+1 falls off-board and
    silently vanishes (cellmap never reaches row h). rng-varied.
    (no_seed was dropped: an all-zero grid makes the rule's find return
    #f and (first #f) crashes; multiple_seeds was PROMOTED to the
    helpful decoy_cells texture — later cells are ignored, that's
    teachable, not degenerate.)"""
    g = full_grid(h, w, 0)
    color = rng.choice([1, 2, 3, 5, 6, 7, 8, 9])
    g[h - 1][rng.randrange(w)] = color
    return g
