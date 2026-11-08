"""Generator for puzzle 7f4411dc.

Rule: keep cells that are part of a 2×2 same-color block; erase others.

Combinatorial axes (8): grid_h/w, n_blocks, n_isolated, palette_size,
block_position_bias, isolated_position_bias, isolated_separation,
block_size_kind.
Degenerates: no_blocks, all_isolated, single_block.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "5c6b3679aff9"
VERSION = "2.1.0"
TASK_ID = "5c6b3679aff9"
SUMMARY = (
    "0-bg grid (h, w ∈ 6-18, by "
    "difficulty) with: (a) N_BLOCKS "
    "∈ 1-4 SOLID 2×2 BLOCKS, each "
    "in a color drawn from a 2-7 "
    "color palette, placed per "
    "BLOCK_POSITION_BIAS ∈ {spread, "
    "center, edge} with ≥2-cell "
    "separation between blocks; "
    "(b) N_ISOLATED ∈ 2-10 SCATTERED "
    "SINGLE CELLS, each in a random "
    "palette color, placed at "
    "positions where they have NO "
    "same-color neighbor within "
    "ISOLATED_SEPARATION (default 1) "
    "— so each isolated cell is "
    "TRULY ISOLATED (not part of a "
    "2×2 same-color block). Rule "
    "(KEEP CELLS THAT ARE PART OF "
    "A 2×2 SAME-COLOR BLOCK; ERASE "
    "ALL OTHER NON-BG CELLS TO 0): "
    "SCAN every 2×2 window of the "
    "grid. IF a 2×2 window has all "
    "4 cells of the SAME non-bg "
    "color: MARK those 4 cells as "
    "'keep'. After scanning all "
    "windows: PAINT non-kept "
    "non-bg cells to 0. Net: "
    "solid 2×2 blocks survive in "
    "their color; isolated cells "
    "vanish."
)

INVARIANTS = [
    "background is 0",
    ">=1 solid 2×2 block of a single non-bg color",
    ">=2 isolated non-bg cells (not in any 2×2 same-color block)",
    "isolated cells separated from same-color cells by 1 step",
]

DEGENERATE_TEXTURES = ("no_blocks", "all_isolated", "single_block")
HELPFUL_TEXTURES = ("balanced", "many_blocks", "many_isolated", "tight")

AXES = {
    "grid_h":              {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":              {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "n_blocks":            {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "n_isolated":          {"type": "int", "default": "rng 3..6", "valid": "1..10"},
    "palette_size":        {"type": "int", "default": "rng 2..4", "valid": "2..7"},
    "block_position_bias": {"type": "str", "default": "rng spread|center|edge",
                            "valid": "spread|center|edge"},
    "isolated_separation": {"type": "int", "default": "1", "valid": "1..3"},
    "block_size_kind":     {"type": "str", "default": "2x2", "valid": "2x2"},
    "texture":             {"type": "str", "default": "rng helpful",
                            "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 6, 9
    elif difficulty == "hard":
        h_lo, h_hi = 13, 18
    else:
        h_lo, h_hi = 8, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    texture = overrides.get("texture",
                            ctx.draw_choice("texture", list(HELPFUL_TEXTURES)))
    if texture == "many_blocks":
        n_blocks, n_iso = 3, 3
    elif texture == "many_isolated":
        n_blocks, n_iso = 1, 6
    elif texture == "tight":
        n_blocks, n_iso = 2, 4
    else:
        n_blocks = int(overrides.get("n_blocks",
                                     ctx.draw_int("n_blocks", 1, 3)))
        n_iso = int(overrides.get("n_isolated",
                                  ctx.draw_int("n_isolated", 3, 6)))
    n_blocks = max(1, min(4, n_blocks))
    n_iso = max(2, min(10, n_iso))
    n_palette = int(overrides.get("palette_size",
                                  ctx.draw_int("palette_size", 2, 4)))
    palette = list(ctx.draw_distinct_colors("palette",
                                            n=max(2, n_palette),
                                            exclude={0}))
    bias = overrides.get("block_position_bias",
                         ctx.draw_choice("block_position_bias",
                                         ["spread", "center", "edge"]))
    sep = int(overrides.get("isolated_separation", 1))
    g = full_grid(h, w, 0)
    placed_blocks = []
    for i in range(n_blocks):
        for _ in range(20):
            rr, rc = _pick_block_pos(bias, h, w, rng)
            if any(abs(rr - br) <= 2 and abs(rc - bc) <= 2
                   for br, bc in placed_blocks):
                continue
            color = palette[i % len(palette)]
            draw_rect(g, rr, rc, 2, 2, color)
            placed_blocks.append((rr, rc))
            break
    placed_iso = 0
    for _ in range(n_iso * 4):
        if placed_iso >= n_iso:
            break
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0:
            continue
        color = rng.choice(palette)
        adjacent_same = False
        for dr in range(-sep, sep + 1):
            for dc in range(-sep, sep + 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] == color:
                    adjacent_same = True
                    break
            if adjacent_same:
                break
        if not adjacent_same:
            g[r][c] = color
            placed_iso += 1
    if not placed_blocks:
        draw_rect(g, h // 2, w // 2, 2, 2, palette[0])
    return g


def _pick_block_pos(bias, h, w, rng):
    if bias == "center":
        return (max(1, h // 2 - 1 + rng.randint(-1, 1)),
                max(1, w // 2 - 1 + rng.randint(-1, 1)))
    if bias == "edge":
        choices = [(1, rng.randint(1, w - 3)),
                   (h - 3, rng.randint(1, w - 3)),
                   (rng.randint(1, h - 3), 1),
                   (rng.randint(1, h - 3), w - 3)]
        return rng.choice(choices)
    return rng.randint(1, h - 3), rng.randint(1, w - 3)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=1 solid 2x2 block (4 same-color cells in a 2x2), >=1 isolated cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    # Check for at least one 2x2 block
    has_block = False
    for r in range(h - 1):
        for c in range(w - 1):
            v = grid[r][c]
            if v != 0 and grid[r][c+1] == v and grid[r+1][c] == v and grid[r+1][c+1] == v:
                has_block = True
                break
        if has_block:
            break
    if not has_block:
        errs.append("no 2x2 same-color block found")
    # Check for at least one isolated non-zero cell
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errs.append("no non-zero cells found")
    return errs


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    if name == "no_blocks":
        for r in range(0, h, 3):
            for c in range(0, w, 3):
                g[r][c] = color
        return g
    if name == "all_isolated":
        for r in range(0, h, 3):
            for c in range(0, w, 3):
                g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        return g
    if name == "single_block":
        draw_rect(g, h // 2, w // 2, 2, 2, color)
        return g
    return g
