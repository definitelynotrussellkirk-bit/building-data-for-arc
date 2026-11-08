"""Generator for v3_rich_schema:easy_03_recolor_L_by_key — recolor L-triominoes.

Rule: a single 'key' marker (a single-cell color appearing exactly once).
Each L-triomino in color 3 is recolored to the key color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_key (no single-cell key marker → rule's key-color
selector returns nothing, target color undefined), no_L (no color-3
L-triominoes → rule has nothing to recolor, output equals input),
key_is_3 (key marker is color 3 → recolor target == source, rule's
recolor is identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9eb815d36de7"
VERSION = "2.0.1"
TASK_ID = "9eb815d36de7"

SUMMARY = (
    "0-bg grid (h~6-8, w~8-10) containing: (a) "
    "ONE SINGLE-CELL KEY MARKER in some unique "
    "non-{0, 3} color (this color appears "
    "EXACTLY ONCE in the grid — it's the "
    "distinguishing marker); (b) 1-2 L-TRIOMINOES "
    "(3-cell L-shapes, all 4 rotations) painted "
    "in color 3 (green), placed at distinct "
    "positions, isolated from each other and "
    "from the key (8-neighborhood clearance). "
    "Rule: identify the KEY COLOR (the unique "
    "single-cell color that's not 0 or 3). For "
    "every L-triomino painted in color 3, "
    "RECOLOR all 3 of its cells to the KEY "
    "COLOR. The key marker itself stays. Net: "
    "green L-triominoes get recolored to match "
    "the single key cell's color."
)

INVARIANTS = [
    "background is 0",
    "exactly one single-cell key marker in a non-{0, 3} color (unique color in the grid)",
    "1-2 L-triominoes (3 cells in L-shape) in color 3 at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "no_L", "key_is_3")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":            {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "n_L":               {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "position_bias":     {"type": "str", "default": "key_plus_L_triominoes",
                          "valid": "key_plus_L_triominoes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; exactly one single-cell key marker (non-0, non-3); 1-2 L-triominoes in color 3."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Find single-cell key: a non-{0,3} color that appears exactly once
    from collections import Counter
    freq = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] not in (0, 3))
    single_colors = [v for v, cnt in freq.items() if cnt == 1]
    if len(single_colors) != 1:
        errs.append(f"expected exactly 1 single-cell key marker (non-0, non-3), found {len(single_colors)}: {single_colors}")
    # Count color-3 cells; should be 3 or 6 (1-2 L-triominoes each with 3 cells)
    c3_count = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 3)
    if c3_count not in (3, 6):
        errs.append(f"expected 3 or 6 color-3 cells (1-2 L-triominoes × 3 cells), found {c3_count}")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


L_SHAPES = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (0, 1)],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 6)
        w = ctx.draw_int("grid_w", 8, 8)
        n = ctx.draw_int("n_L", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 10, 10)
        n = ctx.draw_int("n_L", 2, 2)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
        n = ctx.draw_int("n_L", 1, 2)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        key_color = rng.choice([1, 2, 4, 5, 6, 7, 8, 9])
        for _ in range(80):
            kr = rng.randint(0, h - 1); kc = rng.randint(0, w - 1)
            if g[kr][kc] != 0: continue
            g[kr][kc] = key_color
            break
        ok = True
        for _ in range(n):
            placed = False
            for _ in range(80):
                shape = rng.choice(L_SHAPES)
                rs = [r for r, _ in shape]; cs = [c for _, c in shape]
                sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                cells_p = [(r0 + r, c0 + c) for r, c in shape]
                if not all(g[r][c] == 0 for r, c in cells_p): continue
                pad_ok = True
                for r, c in cells_p:
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in cells_p and g[nr][nc] != 0:
                                pad_ok = False; break
                        if not pad_ok: break
                    if not pad_ok: break
                if not pad_ok: continue
                for r, c in cells_p:
                    g[r][c] = 3
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_key":
        # No key marker — rule's key-color selector returns nothing;
        # target color is undefined.
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[1 + dr][1 + dc] = 3
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[4 + dr][5 + dc] = 3
        return g
    if name == "no_L":
        # No L-triominoes in color 3 — rule has nothing to recolor;
        # output equals input.
        g[3][4] = 6
        return g
    if name == "key_is_3":
        # Key is itself color 3 — recolor target == source; rule's
        # recolor is identity.
        g[1][1] = 3
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[4 + dr][5 + dc] = 3
        return g
    return g
