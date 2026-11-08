"""Generator for arc_puzzle_bank_twentieth21:M139 — pack components by size.

Rule: extract every 4-connected non-bg component; sort by (size DESC,
color ASC); pack each component's bbox crop left-to-right with one bg
column between them. Output height = tallest crop; width = sum of crop
widths + (n-1) gaps.

Combinatorial axes: grid_h, grid_w, n_motifs, motif sizes/shapes,
distinct colors. Degenerates: empty (no components -> [[0]]),
single_component (packing trivial), size_tie (two equal-size components
exercise the color tiebreak).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a3342a9df65d"
VERSION = "3.0.1"  # WRONG-TASK + POISON rewrite: canonical has NO color-9 dividers (just small motifs on a bg-0 grid); the rule packs ALL 4-connected components sorted by (size DESC, color ASC). The old 'find matching panel pair' docstring + full-height color-9 divider columns were fiction -- the dividers became giant components the rule packed. Now scatter 2-5 isolated random-polyomino motifs in distinct colors with varied sizes (+ natural size ties exercising the color tiebreak)."
TASK_ID = "a3342a9df65d"

SUMMARY = (
    "0-bg grid (~6-12 by ~8-16) holding 2-5 ISOLATED 4-connected "
    "MOTIFS (random polyominoes of 1-6 cells) in DISTINCT non-0 colors, "
    "each separated from the others by >=1 bg cell on all sides so they "
    "stay distinct components. Rule (PACK COMPONENTS BY SIZE): extract "
    "every 4-connected non-bg component; CROP each to its bbox; SORT by "
    "(cell-count DESC, color ASC); PACK the crops left-to-right with one "
    "bg column between consecutive crops. Output height = tallest crop; "
    "width = sum of crop widths + (n-1). Net: the motifs are lined up "
    "largest-first into a compact gallery row, ties broken by color."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-5 isolated 4-connected motifs in distinct non-bg colors",
    "motifs separated by >=1 bg cell on all sides (so they stay distinct components)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty", "single_component", "size_tie")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 7..10", "valid": "5..16"},
    "grid_w":            {"type": "int", "default": "rng 10..14", "valid": "6..20"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "n_motifs":          {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "motif_size":        {"type": "int", "default": "rng 1..6", "valid": "1..6"},
    "palette_size":      {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":     {"type": "str", "default": "isolated_motifs",
                          "valid": "isolated_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_poly(rng, k):
    """Random connected polyomino, normalized to min (0,0)."""
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _free(g, r1, c1, r2, c2):
    """True if the bbox + a 1-cell border around it is entirely bg-0."""
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; 2-5 isolated non-bg components in distinct colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    seen = [[False] * w for _ in range(h)]
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 0 and not seen[sr][sc]:
                stack = [(sr, sc)]
                comp_cells = []
                color = grid[sr][sc]
                while stack:
                    r, c = stack.pop()
                    if r < 0 or r >= h or c < 0 or c >= w or seen[r][c]:
                        continue
                    if grid[r][c] == 0:
                        continue
                    seen[r][c] = True
                    comp_cells.append((r, c))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        stack.append((r + dr, c + dc))
                comps.append((color, comp_cells))
    if len(comps) < 2:
        errs.append(f"fewer than 2 components found: {len(comps)}")
        return errs
    if len(comps) > 5:
        errs.append(f"more than 5 components found: {len(comps)}")
    colors = [color for color, _ in comps]
    if len(set(colors)) != len(colors):
        errs.append(f"components share colors: {colors}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], ctx.draw_rng("degen"))
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 6, 8, 8, 11, 2, 3
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 9, 12, 12, 16, 4, 5
    else:
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 7, 10, 10, 14, 3, 4
    rng = ctx.draw_rng("layout")
    n = ctx.draw_int("n_motifs", n_lo, n_hi)
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    # Random motif sizes; natural collisions exercise the color tiebreak in the
    # rule's (size DESC, color ASC) sort.
    sizes = [rng.randint(1, 6) for _ in range(n)]
    for _outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for color, k in zip(colors, sizes):
            shape = _rand_poly(rng, k)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            placed = False
            for _ in range(80):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                    continue
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = color
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not place isolated motifs in 40 attempts")


def _draw_from_degenerate(name, rng):
    h, w = 8, 12
    g = full_grid(h, w, 0)
    if name == "empty":
        # No components -> rule's pack-pieces returns [[0]].
        return g
    if name == "single_component":
        # One motif -> packing is trivial (the crop itself).
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][3 + dc] = 4
        return g
    if name == "size_tie":
        # Two equal-size (3-cell) components -> color tiebreak decides order.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[1 + dr][1 + dc] = 6
        for dr, dc in [(0, 0), (0, 1), (1, 1)]:
            g[5 + dr][8 + dc] = 3
        return g
    return g
