"""Generator for 21f83797.

Rule: 2 cells of color 2. Output paints full rows r1, r2 and cols c1,
c2 in 2; cells strictly inside the rectangle become 1.

Combinatorial axes (8): grid_h/w, dot_separation, dot_orientation,
position_bias, n_decoys, decoy_palette_size, anchor_corners,
edge_avoidance.
Degenerates: same_row, same_col, single_dot.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "01023c69fe3c"
VERSION = "1.2.3"
TASK_ID = "01023c69fe3c"
RULE_HASH = "a403765e8e23"
SUMMARY = (
    "Two 2-cells (plus optional non-2 decor the rule wipes); rule "
    "paints their full rows+cols in 2, fills the bbox interior with 1, "
    "and zeroes everything else — output depends ONLY on the two dots."
)

# Rivals: 'preserve other content' refuted by decor demos whose decor
# vanishes. 'draw only the rectangle' refuted by the full-span lines.
# 'fill interior with decor color' refuted (always 1). 'lines stop at
# the dots' refuted by full rows/cols. 3 demos incl. >=1 with decor.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 2 cells of color 2",
    "the 2 cells have distinct rows AND distinct cols (helpful path)",
    "decor cells (if any) avoid color 2 — the rule wipes them anyway",
]

DOT_ORIENTATIONS = ("diagonal", "anti_diagonal", "spread", "near_corners")
POSITION_BIAS = ("center", "spread", "edge")
DEGENERATE_TEXTURES = ("same_row", "same_col", "single_dot")
HELPFUL_TEXTURES = DOT_ORIENTATIONS

AXES = {
    "grid_h":           {"type": "int", "default": "rng 6..14", "valid": "5..18"},
    "grid_w":           {"type": "int", "default": "rng 8..16", "valid": "6..20"},
    "dot_orientation":  {"type": "str", "default": "rng helpful",
                         "valid": "diagonal|anti_diagonal|spread|near_corners"},
    "dot_separation":   {"type": "str", "default": "rng near|medium|far",
                         "valid": "near|medium|far"},
    "edge_avoidance":   {"type": "bool", "default": "false",
                         "valid": "true|false"},
    "n_decor":          {"type": "int", "default": "rng 0..3", "valid": "0..6",
                         "doc": "Non-2 cells the rule wipes — refutes "
                                "'preserve other content'."},
    "texture":          {"type": "str", "default": "alias for dot_orientation",
                         "valid": "diagonal|anti_diagonal|spread|near_corners|"
                                  "same_row|same_col|single_dot"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 5, 8, 6, 10
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 13, 18, 14, 20
    else:
        h_lo, h_hi, w_lo, w_hi = 6, 14, 8, 16
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    orient = (overrides.get("texture") or
              overrides.get("dot_orientation")
              or ctx.draw_choice("dot_orientation",
                                 list(DOT_ORIENTATIONS)))
    sep = overrides.get("dot_separation",
                        ctx.draw_choice("dot_separation",
                                        ["near", "medium", "far"]))
    edge_avoid = bool(overrides.get("edge_avoidance", False))
    inset = 1 if edge_avoid else 0
    rmin, rmax = inset, h - 1 - inset
    cmin, cmax = inset, w - 1 - inset
    if rmax < rmin: rmin, rmax = 0, h - 1
    if cmax < cmin: cmin, cmax = 0, w - 1
    target_dist = {"near": 3, "medium": (h + w) // 3,
                   "far": h + w - 4}.get(sep, 3)
    g = full_grid(h, w, 0)
    if orient == "diagonal":
        d = max(2, min(target_dist, min(rmax - rmin, cmax - cmin)))
        r1 = rng.randint(rmin, max(rmin, rmax - d))
        c1 = rng.randint(cmin, max(cmin, cmax - d))
        g[r1][c1] = 2
        g[r1 + d][c1 + d] = 2
    elif orient == "anti_diagonal":
        d = max(2, min(target_dist, min(rmax - rmin, cmax - cmin)))
        r1 = rng.randint(rmin, max(rmin, rmax - d))
        c1 = rng.randint(cmin + d, cmax)
        g[r1][c1] = 2
        g[r1 + d][c1 - d] = 2
    elif orient == "near_corners":
        choices = [((rmin, cmin), (rmax, cmax)),
                   ((rmin, cmax), (rmax, cmin))]
        inset_pair = ((rmin + 1, cmin + 1), (rmax - 1, cmax - 1))
        if (inset_pair[0][0] != inset_pair[1][0]
                and inset_pair[0][1] != inset_pair[1][1]):
            choices.append(inset_pair)
        (r1, c1), (r2, c2) = rng.choice(choices)
        g[r1][c1] = 2
        g[r2][c2] = 2
    else:  # spread
        for _ in range(40):
            r1, r2 = rng.sample(range(rmin, rmax + 1), 2)
            c1, c2 = rng.sample(range(cmin, cmax + 1), 2)
            if abs(r1 - r2) + abs(c1 - c2) >= 2:
                g[r1][c1] = 2
                g[r2][c2] = 2
                break
        else:
            g[rmin][cmin] = 2
            g[rmax][cmax] = 2

    # decor in non-2 colors: the rule's cellmap zeroes every cell that
    # isn't on the cross or inside the bbox, and overwrites the rest —
    # decor NEVER survives, proving the output reads only the two dots
    if overrides.get("n_decor") is not None:
        # The default sampler remains intentionally light (0..3), while the
        # declared authoring axis permits explicit stress cases up to 6.
        n_decor = ctx.draw_int_strict("n_decor", 0, 6)
    else:
        n_decor = ctx.draw_int("n_decor", 0, 3)
    decor_palette = (1, 3, 4, 5, 6, 7, 8, 9)
    placed = 0
    for _ in range(30):
        if placed >= n_decor:
            break
        r, c = rng.randint(0, h - 1), rng.randint(0, w - 1)
        if g[r][c] == 0:
            g[r][c] = rng.choice(decor_palette)
            placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly 2 cells of color 2, with distinct rows AND distinct cols."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    twos = [(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] == 2]
    errors = []
    if len(twos) != 2:
        errors.append(f"expected exactly 2 cells of color 2, found {len(twos)}")
    elif twos[0][0] == twos[1][0]:
        errors.append("both color-2 cells share the same row (degenerate: rule draws a col-only cross)")
    elif twos[0][1] == twos[1][1]:
        errors.append("both color-2 cells share the same col (degenerate: rule draws a row-only cross)")
    return errors


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "same_row":
        r = h // 2
        g[r][1] = 2
        g[r][w - 2] = 2
        return g
    if name == "same_col":
        c = w // 2
        g[1][c] = 2
        g[h - 2][c] = 2
        return g
    if name == "single_dot":
        g[h // 2][w // 2] = 2
        return g
    return g
