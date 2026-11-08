"""Generator for arc_additional_puzzle_bank_volume6:M42 — Recolor red objects of target size.

Rule:
  - target = count of color-1 cells in row 0
  - For each red(2) object: if size == target, recolor to 3.

Combinatorial axes (8): grid_h, grid_w, palette_kind, target, n_red,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_target, no_match, all_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "5fd7ea0a8e2a"
VERSION = "1.2.0"  # place the target-size red blob FIRST (shuffled order could fail it -> no match -> identity demo)
TASK_ID = "5fd7ea0a8e2a"
SUMMARY = "Color-1 cells in row 0 set target size; red(2) objects of that size recolor to 3."

INVARIANTS = [
    "between 2 and 5 color-1 cells in row 0 (the target count)",
    "between 2 and 4 red(2) objects",
    "AT LEAST one red object has size == target (so output != input)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_target", "no_match", "all_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "target":         {"type": "int", "default": "rng 2..5", "valid": "1..6"},
    "n_red":          {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "row0_legend_with_red_objects",
                       "valid": "row0_legend_with_red_objects"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
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
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 10, 11)
        target = ctx.draw_int("target", 2, 3)
        n_red = ctx.draw_int("n_red", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 13, 14)
        target = ctx.draw_int("target", 4, 5)
        n_red = ctx.draw_int("n_red", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 10, 14)
        target = ctx.draw_int("target", 2, 5)
        n_red = ctx.draw_int("n_red", 2, 4)

    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    cols = list(range(w)); rng.shuffle(cols)
    for c in cols[:target]:
        g[0][c] = 1

    used = set()
    # non-target sizes for the remaining red objects (distinct from target)
    other_sizes = []
    for _ in range(n_red - 1):
        s = rng.randint(1, 5)
        if s == target:
            s = target + 1 if target < 5 else target - 1
        other_sizes.append(s)

    def _place_blob(size):
        # grow_blob works in the (h-1, w) region (rows 0..h-2); each blob is then
        # shifted DOWN one row so row 0 stays free for the legend. `used` MUST be kept
        # in the SAME unshifted space grow_blob checks, else isolation is off-by-one
        # and adjacent blobs merge (corrupting component sizes -> target never matches).
        for _ in range(20):
            blob = grow_blob(rng, h - 1, w, used, size)
            if blob is None:
                continue
            used.update(blob)
            for r, c in blob:
                g[r + 1][c] = 2
            return True
        return False

    # Place the TARGET-size blob FIRST on the (nearly) empty grid so it always lands
    # and the rule has a match (output != input). Then scatter the non-matching reds.
    if not _place_blob(target):
        # extreme fallback: shrink target so it fits, and mirror it into row-0 legend
        target = min(target, 2)
        g[0] = [0] * w
        cols2 = list(range(w)); rng.shuffle(cols2)
        for c in cols2[:target]:
            g[0][c] = 1
        _place_blob(target)
    for size in other_sizes:
        _place_blob(size)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """The rule recolors red(2) objects whose size == (count of 1s in row 0). Ensure
    >=1 red object matches the target, else the rule is a no-op (identity demo)."""
    errs = []
    h = len(grid); w = len(grid[0]) if h else 0
    target = sum(1 for v in grid[0] if v == 1)
    if target == 0:
        errs.append("no color-1 legend in row 0 (target == 0)")
    # 4-connected red component sizes
    seen = [[False] * w for _ in range(h)]
    sizes = []
    for sr in range(1, h):
        for sc in range(w):
            if grid[sr][sc] != 2 or seen[sr][sc]:
                continue
            st = [(sr, sc)]; seen[sr][sc] = True; n = 0
            while st:
                r, c = st.pop(); n += 1
                for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] == 2:
                        seen[nr][nc] = True; st.append((nr, nc))
            sizes.append(n)
    if not sizes:
        errs.append("no red(2) objects")
    elif target not in sizes:
        errs.append(f"no red object of size == target {target} (sizes {sizes}) — rule no-ops")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_target":
        # row 0 has no color-1 cells → target = 0; no red object can match (size > 0)
        # rule fires zero times
        for (r, c) in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 2   # red size 3
        for (r, c) in [(5, 6), (5, 7)]: g[r][c] = 2          # red size 2
        return g
    if name == "no_match":
        # target is set but no red object has that size → rule fires zero times
        g[0][2] = 1; g[0][5] = 1; g[0][8] = 1   # target = 3
        for (r, c) in [(2, 2), (2, 3)]: g[r][c] = 2          # size 2
        for (r, c) in [(5, 6), (5, 7), (5, 8), (6, 7)]: g[r][c] = 2  # size 4
        return g
    if name == "all_match":
        # every red object has size == target → all reds recolored to 3, no contrast
        g[0][2] = 1; g[0][5] = 1   # target = 2
        for (r, c) in [(2, 2), (2, 3)]: g[r][c] = 2
        for (r, c) in [(4, 5), (4, 6)]: g[r][c] = 2
        for (r, c) in [(7, 8), (7, 9)]: g[r][c] = 2
        return g
    return g
