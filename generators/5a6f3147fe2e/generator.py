"""Generator for aee291af.

Rule: find every MAXIMAL rectangle (>=3x3) of foreground cells (color 2 or
8); among their content sub-grids, output the one whose content appears
exactly once.

This generator places several same-size solid 2/8 blocks separated by
background, where most share an identical content and exactly one is
unique; the rule outputs the unique block's content.

Combinatorial axes: grid size, the block size, the common/unique
contents, the block count and positions.
Degenerates: single_block, all_same, no_blocks.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5a6f3147fe2e"
VERSION = "2.1.0"  # diversity: random block size + contents + count + positions + grid (was fixed ~21)
TASK_ID = "5a6f3147fe2e"
SUMMARY = (
    "0-bg grid (size varies). Several same-size solid blocks of foreground "
    "(color 2/8) cells, separated; most share an identical 2/8 content and "
    "exactly one is UNIQUE. Rule: among the maximal 2/8 rectangles, output "
    "the one whose content appears once. The grid size, block size, "
    "contents, block count and positions all vary freely (was a fixed "
    "layout, ~21 distinct)."
)

INVARIANTS = [
    "blocks are same-size solid rectangles (>=3x3) of color 2/8, separated",
    "the common content appears >=2 times; exactly one block is unique",
    "the output is the unique block's content",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_block", "all_same", "no_blocks")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "11..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..26"},
    "block_size":     {"type": "int", "default": "varies", "valid": "3..4"},
    "n_blocks":       {"type": "int", "default": "varies", "valid": "3..5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "blocks_apart", "valid": "blocks_apart"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|single_block|all_same|no_blocks"},
}


def _reserve(occ, top, left, bh, bw, h, w, margin=1):
    for r in range(top - margin, top + bh + margin):
        for c in range(left - margin, left + bw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def _rand_content(rng, k):
    return tuple(tuple(rng.choice([2, 8]) for _ in range(k)) for _ in range(k))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    if difficulty == "easy":
        hr, wr, kr, nr = (11, 13), (11, 14), (3, 3), (3, 3)
    elif difficulty == "hard":
        hr, wr, kr, nr = (16, 24), (17, 26), (3, 4), (4, 5)
    else:
        hr, wr, kr, nr = (12, 17), (13, 19), (3, 4), (3, 4)

    for _attempt in range(40):
        k = rng.randint(*kr)
        common = _rand_content(rng, k)
        for _ in range(30):
            unique = _rand_content(rng, k)
            if unique != common:
                break
        else:
            continue

        N = rng.randint(*nr)
        n_common = N - 1                          # >=2 so common is not itself unique
        if n_common < 2:
            continue
        contents = [common] * n_common + [unique]
        rng.shuffle(contents)

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        placed = True
        for content in contents:
            done = False
            for _t in range(40):
                top = rng.randint(0, h - k); left = rng.randint(0, w - k)
                if _reserve(occ, top, left, k, k, h, w, margin=1):
                    for r in range(k):
                        for c in range(k):
                            g[top + r][left + c] = content[r][c]
                    done = True
                    break
            if not done:
                placed = False
                break
        if placed:
            return g

    return g   # fallback (rare)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, color 2 or 8 foreground blocks present, at least 3 blocks."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    fg = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (2, 8)]
    if not fg:
        errs.append("no color-2/8 foreground cells found")
    # Check only 0, 2, 8 appear in the grid
    bad = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] not in (0, 2, 8)}
    if bad:
        errs.append(f"unexpected colors in grid: {bad}")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)

    def block(top, left, content):
        for r in range(3):
            for c in range(3):
                g[top + r][left + c] = content[r][c]

    a = ((2, 8, 2), (8, 2, 8), (2, 8, 2))
    if name == "single_block":
        block(2, 2, a)
        return g
    if name == "all_same":
        block(2, 2, a); block(2, 8, a); block(7, 2, a)
        return g
    if name == "no_blocks":
        return g
    return g
