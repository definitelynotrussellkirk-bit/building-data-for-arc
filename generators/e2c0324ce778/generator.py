"""Generator for ARC task ed74f2f2.

Rule: input is 5 × 9. Compute color from key cells:
  tl = g[1][1], br = g[3][3]
  if tl==5 and br==0: color=1
  elif tl==0 and br==0: color=3
  else: color=2
Output 3 × 3: cell = color if g[r+1][c+5]==5 else 0. (Right panel cols
5-7 carries a mask.)

Combinatorial axes (8):
  * case                — which (tl, br) combo: tl5_br0, none, both5,
                          br5_only, mixed
  * mask_pattern        — random / dense / sparse / cluster / corners
  * mask_density        — fraction of mask cells set to 5
  * left_panel_decoy    — content in cols 0-3 outside key cells
  * left_palette_size   — colors used in left panel
  * separator_col       — content in col 4 (rule ignores)
  * key_cell_anti_corruption — bool: ensure key cells aren't accidentally
                          masked
  * caller-opt-in degenerates: empty_mask (output all 0),
                              full_mask (output 3x3 of color),
                              ambiguous_keys.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e2c0324ce778"
VERSION = "1.3.0"  # fixed 5x9->3x3 is INHERENT/faithful (ed74f2f2 is a fixed-dimension puzzle, so shape-locked is correct). dup-outputs from deterministic mask patterns (corners/diagonal/border/dense always same mask). Bias the auto mask toward random/sparse/cluster to maximize distinct 3x3 outputs.
TASK_ID = "e2c0324ce778"
SUMMARY = "5 × 9 grid with key cells + right-panel mask; rule outputs 3 × 3 colored mask (fixed I/O dims, faithful to canonical)."

INVARIANTS = [
    "input is 5 × 9",
    "g[1][1] and g[3][3] are key cells (in {0, 5})",
    "right panel (rows 1-3, cols 5-7) is the mask of 5s",
    "≥1 mask cell so output has ≥1 colored cell",
]

CASES = ("tl5_br0", "none", "both5", "br5_only", "mixed_other")
MASK_PATTERNS = ("random", "dense", "sparse", "cluster", "corners",
                 "diagonal", "single", "border")
DEGENERATE_TEXTURES = ("empty_mask", "full_mask", "ambiguous_keys")
HELPFUL_TEXTURES = MASK_PATTERNS

AXES = {
    "case":             {"type": "str", "default": "rng helpful",
                         "valid": "|".join(CASES)},
    "mask_pattern":     {"type": "str", "default": "rng helpful",
                         "valid": "|".join(MASK_PATTERNS)},
    "mask_density":     {"type": "float", "default": "rng 0.3..0.8", "valid": "0..1"},
    "left_panel_decoy": {"type": "float", "default": "rng 0..0.3", "valid": "0..0.7"},
    "left_palette_size": {"type": "int", "default": "rng 0..3", "valid": "0..6"},
    "separator_col":    {"type": "color", "default": "rng (≠5)", "valid": "0..9 (≠5)"},
    "anti_corruption":  {"type": "bool", "default": "true", "valid": "true|false"},
    "texture":          {"type": "str", "default": "alias for mask_pattern",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the fixed 5x9 key+mask layout used by ed74f2f2."""
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["empty grid"]
    if len(grid) != 5 or any(len(row) != 9 for row in grid):
        return ["expected fixed 5x9 input grid"]
    errs = []
    if grid[1][1] not in (0, 5, 1, 2, 3, 4, 6, 7, 8, 9):
        errs.append("invalid top-left key cell")
    if grid[3][3] not in (0, 5):
        errs.append("bottom-right key cell should be 0 or 5 in default rows")
    mask_vals = [grid[r][c] for r in range(1, 4) for c in range(5, 8)]
    if any(v not in (0, 5) for v in mask_vals):
        errs.append("right-panel mask contains non-{0,5} values")
    filled = sum(v == 5 for v in mask_vals)
    if filled == 0:
        errs.append("default mask is empty")
    if filled == 9:
        errs.append("default mask is full; use full_mask degenerate explicitly")
    if any(grid[r][4] == 5 for r in range(5)):
        errs.append("separator column should not use mask color 5")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    case = overrides.get("case", ctx.draw_choice("case", list(CASES)))
    # bias the auto mask toward varied (non-deterministic) patterns so the 3x3
    # output space is well-sampled; deterministic patterns stay available via override
    _auto_pool = ["random", "random", "random", "sparse", "cluster", "single"]
    pattern = (overrides.get("texture") or overrides.get("mask_pattern")
               or ctx.draw_choice("mask_pattern", _auto_pool))
    density = float(overrides.get("mask_density",
                                  ctx.draw_rng("mask_density").uniform(0.3, 0.8)))
    decoy_d = float(overrides.get("left_panel_decoy",
                                  ctx.draw_rng("left_panel_decoy").uniform(0.0, 0.3)))
    n_left = int(overrides.get("left_palette_size",
                               ctx.draw_int("left_palette_size", 0, 3)))
    sep = int(overrides.get("separator_col",
                            ctx.draw_color("separator_col", exclude={5})))
    g = full_grid(5, 9, 0)
    # Key cells
    if case == "tl5_br0":
        g[1][1] = 5
    elif case == "none":
        pass
    elif case == "both5":
        g[1][1] = 5; g[3][3] = 5
    elif case == "br5_only":
        g[3][3] = 5
    elif case == "mixed_other":
        # tl is non-5, non-0: rule's "else" branch (color=2)
        g[1][1] = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
    # Mask in cols 5-7, rows 1-3
    _fill_mask(g, pattern, density, rng)
    # Decoys in left panel
    if n_left > 0:
        decoy_palette = list(ctx.draw_distinct_colors(
            "decoy", n=n_left, exclude={0, 5}))
        for r in range(5):
            for c in range(4):
                if (r, c) not in {(1, 1), (3, 3)} and rng.random() < decoy_d:
                    g[r][c] = rng.choice(decoy_palette) if decoy_palette else 0
    # Separator col
    if sep != 0:
        for r in range(5):
            if rng.random() < 0.3:
                g[r][4] = sep
    # Force a non-empty but non-full mask. `full_mask` is an explicit
    # degenerate texture; the normal sampler should not accidentally emit a
    # constant 3x3 output just because a dense random mask filled all 9 cells.
    mask_cells = [(r, c) for r in range(1, 4) for c in range(5, 8)]
    filled = [(r, c) for r, c in mask_cells if g[r][c] == 5]
    if not filled:
        g[1][5] = 5
    elif len(filled) == len(mask_cells):
        r, c = rng.choice(mask_cells)
        g[r][c] = 0
    return g


def _fill_mask(g, pattern, density, rng):
    if pattern == "random":
        for r in range(1, 4):
            for c in range(5, 8):
                if rng.random() < density:
                    g[r][c] = 5
    elif pattern == "dense":
        for r in range(1, 4):
            for c in range(5, 8):
                g[r][c] = 5
    elif pattern == "sparse":
        for r in range(1, 4):
            for c in range(5, 8):
                if rng.random() < density * 0.4:
                    g[r][c] = 5
    elif pattern == "cluster":
        cr = rng.randint(1, 3); cc = rng.randint(5, 7)
        for r in range(1, 4):
            for c in range(5, 8):
                if abs(r - cr) + abs(c - cc) <= 1:
                    g[r][c] = 5
    elif pattern == "corners":
        for r, c in [(1, 5), (1, 7), (3, 5), (3, 7)]:
            g[r][c] = 5
    elif pattern == "diagonal":
        for k in range(3):
            g[1 + k][5 + k] = 5
    elif pattern == "single":
        r = rng.randint(1, 3); c = rng.randint(5, 7)
        g[r][c] = 5
    elif pattern == "border":
        for c in range(5, 8):
            g[1][c] = 5; g[3][c] = 5
        g[2][5] = 5; g[2][7] = 5


def _draw_from_degenerate(name, rng):
    g = full_grid(5, 9, 0)
    if name == "empty_mask":
        g[1][1] = 5  # set key but no mask cells
        return g
    if name == "full_mask":
        g[1][1] = 5
        for r in range(1, 4):
            for c in range(5, 8):
                g[r][c] = 5
        return g
    if name == "ambiguous_keys":
        # Both key cells = 5, mask present — rule's else branch → color=2
        g[1][1] = 5; g[3][3] = 5
        for r in range(1, 4):
            for c in range(5, 8):
                if rng.random() < 0.5:
                    g[r][c] = 5
        g[1][5] = 5
        return g
    return g
