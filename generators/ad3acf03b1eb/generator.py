"""Generator for puzzle ef135b50.

Rule: fill 0 with 9 if cell has 2 to left AND 2 to right in same row,
AND >=1 row below contains 2.

Combinatorial axes (8): grid_h/w, n_brackets, n_below_rows,
bracket_separation, position_bias, decoy_density, asymmetry,
bottom_row_density.
Degenerates: no_brackets, no_below, all_2s.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ad3acf03b1eb"
VERSION = "1.1.1"
TASK_ID = "ad3acf03b1eb"
SUMMARY = "Sparse 2-cells; rule fills 0s bracketed by 2s with 2 below."

INVARIANTS = [
    "background is 0",
    "only non-bg color is 2",
    ">=2 upper rows have a left-2 and right-2 with bg between",
    ">=1 lower row has >=1 cell of color 2",
    "no color 9 in input (rule writes 9 for output)",
]

POSITION_BIAS = ("center", "spread", "edge")
DEGENERATE_TEXTURES = ("no_brackets", "no_below", "all_2s")
HELPFUL_TEXTURES = POSITION_BIAS

AXES = {
    "grid_h":           {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":           {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "n_brackets":       {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "n_below_rows":     {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "bracket_separation": {"type": "str", "default": "rng near|medium|far",
                           "valid": "near|medium|far"},
    "position_bias":    {"type": "str", "default": "rng helpful",
                         "valid": "|".join(POSITION_BIAS)},
    "bottom_row_density": {"type": "float", "default": "rng 0.3..0.7",
                           "valid": "0.1..1"},
    "extra_decoys":     {"type": "int", "default": "rng 0..3", "valid": "0..6"},
    "texture":          {"type": "str", "default": "alias for position_bias",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, only color-2 cells nonzero, no color-9 in input."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_brackets", "no_below", "all_2s"):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    bad = [grid[r][c] for r in range(h) for c in range(w)
           if grid[r][c] not in (0, 2)]
    if bad:
        errs.append(f"unexpected colors {set(bad)} in input (only 0/2 expected)")
    has_2 = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_2:
        errs.append("no color-2 cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 6, 9, 6, 9
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 13, 18, 13, 18
    else:
        h_lo, h_hi, w_lo, w_hi = 8, 14, 8, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_brackets = int(overrides.get("n_brackets",
                                   ctx.draw_int("n_brackets", 2, 4)))
    n_brackets = max(2, min(6, n_brackets))
    n_below = int(overrides.get("n_below_rows",
                                ctx.draw_int("n_below_rows", 1, 3)))
    n_below = max(1, min(4, n_below))
    sep = overrides.get("bracket_separation",
                        ctx.draw_choice("bracket_separation",
                                        ["near", "medium", "far"]))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIAS)))
    density = float(overrides.get("bottom_row_density",
                                  ctx.draw_rng("bottom_row_density")
                                  .uniform(0.3, 0.7)))
    extra = int(overrides.get("extra_decoys",
                              ctx.draw_int("extra_decoys", 0, 3)))
    g = full_grid(h, w, 0)
    upper_rows = list(range(0, max(2, h // 2)))
    rng.shuffle(upper_rows)
    placed = 0
    for r in upper_rows[:n_brackets]:
        c1, c2 = _bracket_cols(sep, bias, w, rng)
        if c2 - c1 < 2:
            continue
        g[r][c1] = 2
        g[r][c2] = 2
        placed += 1
    bottom_rows = list(range(max(2, h // 2), h))
    rng.shuffle(bottom_rows)
    for r in bottom_rows[:n_below]:
        for c in range(w):
            if rng.random() < density:
                g[r][c] = 2
        if all(g[r][c] == 0 for c in range(w)):
            g[r][w // 2] = 2
    for _ in range(extra):
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if g[r][c] == 0:
            g[r][c] = 2
    if placed < 2:
        # fallback brackets in rows 0, 1
        if h >= 4 and w >= 5:
            g[0][0] = 2; g[0][w - 1] = 2
            g[1][0] = 2; g[1][w - 1] = 2
            for c in range(w):
                g[h - 1][c] = 2
    return g


def _bracket_cols(sep, bias, w, rng):
    target = {"near": 3, "medium": w // 2, "far": w - 2}.get(sep, w // 2)
    target = max(2, min(w - 1, target))
    if bias == "center":
        c1 = max(0, (w - target) // 2)
        c2 = min(w - 1, c1 + target)
    elif bias == "edge":
        c1 = 0; c2 = min(w - 1, target)
    else:
        c1 = rng.randint(0, max(0, w - target - 1))
        c2 = c1 + target
        c2 = min(c2, w - 1)
    return c1, c2


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_brackets":
        for c in range(w):
            g[h - 1][c] = 2
        return g
    if name == "no_below":
        g[0][0] = 2; g[0][w - 1] = 2
        g[1][0] = 2; g[1][w - 1] = 2
        return g
    if name == "all_2s":
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        return g
    return g
