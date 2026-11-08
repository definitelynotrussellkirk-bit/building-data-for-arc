"""Generator for 5614dbcf.

Rule: 3*bh × 3*bw grid divided into 3×3 sub-blocks; for each block
output the most common value into a 3×3 result grid.

Combinatorial axes (8): block_h, block_w, n_filled_blocks,
palette_size, stray_density, fill_layout, position_distribution,
stray_color.
Degenerates: empty_grid, all_filled, single_block.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "bbcc617baafb"
VERSION = "1.2.2"  # reviewer fix: cap filled blocks below total and repair zero-mode block if lost
TASK_ID = "bbcc617baafb"
SUMMARY = "Grid of size (3*N) × (3*M) divided into N×M sub-blocks of 3×3 cells each. Each block contains some cells in a dominant color plus stray distractor cells. Rule outputs an N×M grid where each output cell = the most frequent value in the corresponding 3×3 block."

# Rivals: 'output is input' refuted by demos (output is N×M).
# 'output is top-left of each block' refuted by demos where mode
# != top-left. 'output picks first non-zero' refuted by demos where
# 0 is the mode of an empty-dominant block. 'output uses a fixed
# block size = grid size' refuted by demos with N or M > 1. 3 demos
# with varied N, M cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "h % 3 == 0 and w % 3 == 0",
    ">=2 sub-blocks have a STRICTLY dominant non-bg color",
    ">=1 sub-block has mode = 0 (or stray-color minority)",
    "stray cells count is < block-cell-count / 2 (so they don't outvote dominant color)",
]

FILL_LAYOUTS = ("solid", "majority", "ring", "frame")
DEGENERATE_TEXTURES = ("empty_grid", "all_filled", "single_block")
HELPFUL_TEXTURES = FILL_LAYOUTS

AXES = {
    "block_h":            {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "block_w":            {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "n_filled_blocks":    {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "palette_size":       {"type": "int", "default": "= n_filled",
                           "valid": "1..7"},
    "stray_density":      {"type": "float", "default": "rng 0.05..0.15",
                           "valid": "0..0.3"},
    "fill_layout":        {"type": "str", "default": "rng helpful",
                           "valid": "|".join(FILL_LAYOUTS)},
    "stray_color":        {"type": "color", "default": "5", "valid": "1..9"},
    "position_distribution": {"type": "str", "default": "rng spread|corner|diag",
                              "valid": "spread|corner|diag"},
    "texture":            {"type": "str", "default": "alias for fill_layout",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify 3x3 block-mode teaching invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    if h % 3 != 0:
        errs.append(f"grid height {h} not divisible by 3")
    if w % 3 != 0:
        errs.append(f"grid width {w} not divisible by 3")
    if errs:
        return errs
    from collections import Counter
    nonzero_mode_blocks = 0
    zero_mode_blocks = 0
    for r0 in range(0, h, 3):
        for c0 in range(0, w, 3):
            vals = [grid[r][c] for r in range(r0, r0 + 3)
                    for c in range(c0, c0 + 3)]
            counts = Counter(vals)
            top = max(counts.values())
            modes = [v for v, n in counts.items() if n == top]
            if len(modes) != 1:
                errs.append(f"3x3 block at {(r0, c0)} has no strict mode")
                continue
            if modes[0] == 0:
                zero_mode_blocks += 1
            else:
                nonzero_mode_blocks += 1
    if nonzero_mode_blocks < 2:
        errs.append(f"expected >=2 nonzero-mode blocks, got {nonzero_mode_blocks}")
    if zero_mode_blocks < 1:
        errs.append("expected >=1 zero-mode block")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    # n_rows × n_cols blocks, each 3x3 — total grid is (3*n_rows) × (3*n_cols)
    if difficulty == "easy":
        n_rows = rng.randint(2, 3); n_cols = rng.randint(2, 3)
    elif difficulty == "hard":
        n_rows = rng.randint(4, 6); n_cols = rng.randint(4, 6)
    else:
        n_rows = rng.randint(3, 5); n_cols = rng.randint(3, 5)
    bh = n_rows; bw = n_cols  # for backward var names
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], 3, 3, rng)
    h = 3 * n_rows
    w = 3 * n_cols
    n_filled = int(overrides.get("n_filled_blocks",
                                 ctx.draw_int("n_filled_blocks", 3, 6)))
    total_blocks = n_rows * n_cols
    # Keep one empty-majority block in helpful/default layouts.  Earlier easy
    # cases with a 2x2 block lattice could request 6 filled blocks, silently
    # converting every block to nonzero-mode and losing the zero-mode contrast.
    n_filled = max(2, min(total_blocks - 1, n_filled))
    pool = [c for c in range(1, 10) if c not in (0, 5)]
    rng.shuffle(pool)
    pal = pool[:max(1, n_filled)]
    layout = (overrides.get("texture") or overrides.get("fill_layout")
              or ctx.draw_choice("fill_layout", list(FILL_LAYOUTS)))
    stray_density = float(overrides.get("stray_density",
                                        ctx.draw_rng("stray_density")
                                        .uniform(0.05, 0.15)))
    stray_color = int(overrides.get("stray_color", 5))
    pos_dist = overrides.get("position_distribution",
                             ctx.draw_choice("position_distribution",
                                             ["spread", "corner", "diag"]))
    g = full_grid(h, w, 0)
    # 3x3 blocks (per the rule), at positions (0,0), (0,3), (0,6), (3,0), ...
    blocks = [(r0, c0) for r0 in range(0, h, 3) for c0 in range(0, w, 3)]
    chosen = _pick_blocks(pos_dist, blocks, n_filled, rng)
    for i, (r0, c0) in enumerate(chosen):
        color = pal[i % len(pal)]
        _fill_block(g, layout, r0, c0, 3, 3, color, rng)
    n_strays = max(1, int(stray_density * h * w))
    placed = 0
    tries = 0
    while placed < n_strays and tries < 30:
        tries += 1
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] == 0:
            g[r][c] = stray_color
            placed += 1
    from collections import Counter
    def _strict_mode(r0, c0):
        counts = Counter(g[r][c] for r in range(r0, r0 + 3) for c in range(c0, c0 + 3))
        top = max(counts.values())
        modes = [v for v, n in counts.items() if n == top]
        return modes[0] if len(modes) == 1 else None
    if not any(_strict_mode(r0, c0) == 0 for r0, c0 in blocks):
        for r0, c0 in blocks:
            if (r0, c0) not in chosen:
                for rr in range(r0, r0 + 3):
                    for cc in range(c0, c0 + 3):
                        g[rr][cc] = 0
                break
    return g


def _pick_blocks(dist, blocks, n, rng):
    if dist == "corner":
        # corners first
        bh, bw = blocks[-1]
        corners = [(0, 0), (0, bw), (bh, 0), (bh, bw)]
        chosen = [b for b in corners if b in blocks][:n]
        rest = [b for b in blocks if b not in chosen]
        rng.shuffle(rest)
        return chosen + rest[:n - len(chosen)]
    if dist == "diag":
        sz = int(len(blocks) ** 0.5)
        diag = [blocks[i * sz + i] for i in range(sz) if i * sz + i < len(blocks)]
        rest = [b for b in blocks if b not in diag]
        rng.shuffle(rest)
        return (diag + rest)[:n]
    rng.shuffle(blocks)
    return blocks[:n]


def _fill_block(g, layout, r0, c0, bh, bw, color, rng):
    if layout == "solid":
        for r in range(r0, r0 + bh):
            for c in range(c0, c0 + bw):
                g[r][c] = color
        return
    if layout == "majority":
        cells = [(r, c) for r in range(r0, r0 + bh) for c in range(c0, c0 + bw)]
        n_fill = max(1, len(cells) // 2 + 1)
        rng.shuffle(cells)
        for r, c in cells[:n_fill]:
            g[r][c] = color
        return
    if layout == "ring":
        for r in range(r0, r0 + bh):
            for c in range(c0, c0 + bw):
                if r == r0 or r == r0 + bh - 1 or c == c0 or c == c0 + bw - 1:
                    g[r][c] = color
        return
    if layout == "frame":
        for r in range(r0, r0 + bh):
            g[r][c0] = color
            g[r][c0 + bw - 1] = color
        for c in range(c0, c0 + bw):
            g[r0][c] = color
            g[r0 + bh - 1][c] = color
        return
    for r in range(r0, r0 + bh):
        for c in range(c0, c0 + bw):
            g[r][c] = color


def _draw_from_degenerate(name, bh, bw, rng):
    h, w = 3 * bh, 3 * bw
    g = full_grid(h, w, 0)
    color = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
    if name == "empty_grid":
        return g
    if name == "all_filled":
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "single_block":
        for r in range(bh):
            for c in range(bw):
                g[r][c] = color
        return g
    return g
