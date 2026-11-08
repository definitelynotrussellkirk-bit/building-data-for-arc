"""Generator for arc_additional_puzzle_bank_volume6:M37.

Rule: take normalized cells of the 8-blob as template. For each
2-blob, if normalized cells == template, recolor to 3.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, shape_spread, texture.
Degenerates: no_template, all_match, no_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "50a81742b154"
VERSION = "2.0.1"
TASK_ID = "50a81742b154"
SUMMARY = (
    "0-bg grid (h~9-12, w~11-14) with FOUR FIXED-"
    "POSITION OBJECTS at the corner-like slots: "
    "(a) TEMPLATE OBJECT at (1, 1) — a 4-cell L "
    "shape [(0,0),(1,0),(2,0),(2,1)] painted in COLOR "
    "8 (cyan, the template color); (b) MATCHING 2-"
    "BLOB at (1, w-4) — the SAME 4-cell L shape "
    "painted in COLOR 2 (this is the candidate that "
    "the rule should recolor); (c) DIFFERENT 2-BLOB "
    "at (h-4, 1) — a 2×2 SQUARE shape [(0,0),(0,1),"
    "(1,0),(1,1)] painted in COLOR 2; (d) DIFFERENT-"
    "2 2-BLOB at (h-4, w-4) — a 3-cell VERTICAL bar "
    "[(0,0),(1,0),(2,0)] painted in COLOR 2. Exactly "
    "one 2-blob (b) shares the 8-blob's normalized "
    "shape; the other two have distinct shapes. "
    "Rule (RECOLOR 2-BLOBS WHOSE NORMALIZED SHAPE "
    "MATCHES THE 8-BLOB TEMPLATE TO COLOR 3): find "
    "the unique 8-BLOB, extract its NORMALIZED CELLS "
    "(subtract min row/col from each cell so the "
    "shape sits in its own local coordinates). For "
    "EACH 2-BLOB: extract its NORMALIZED CELLS. If "
    "the 2-blob's normalized shape EQUALS the 8-"
    "blob's normalized shape: RECOLOR every cell of "
    "that 2-blob to COLOR 3. Other 2-blobs stay "
    "color 2; the 8-blob stays color 8. Net: the one "
    "2-blob matching the 8-shape becomes color-3 "
    "(green); the rest remain as color-2 decoys."
)

INVARIANTS = [
    "exactly one 8-blob",
    "between 2 and 3 2-blobs",
    "exactly one 2-blob has same normalized shape as 8-blob",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "all_match", "no_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "4", "valid": "3..4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "spread_corners",
                       "valid": "spread_corners"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "shape_spread":   {"type": "str", "default": "one_match_others_diff",
                       "valid": "one_match_others_diff"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 1 color-8 blob; >=2 color-2 blobs."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    visited = [[False] * w for _ in range(h)]
    def flood(r0, c0):
        cells = []
        stack = [(r0, c0)]
        visited[r0][c0] = True
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                rr, cc = r+dr, c+dc
                if 0 <= rr < h and 0 <= cc < w and not visited[rr][cc] and grid[rr][cc] != 0:
                    visited[rr][cc] = True
                    stack.append((rr, cc))
        return cells
    blobs_8 = []; blobs_2 = []
    for r in range(h):
        for c in range(w):
            if not visited[r][c] and grid[r][c] != 0:
                comp = flood(r, c)
                color = grid[comp[0][0]][comp[0][1]]
                if color == 8:
                    blobs_8.append(comp)
                elif color == 2:
                    blobs_2.append(comp)
    if len(blobs_8) != 1:
        errs.append(f"expected exactly 1 color-8 blob (template), found {len(blobs_8)}")
    if len(blobs_2) < 2:
        errs.append(f"expected >=2 color-2 blobs, found {len(blobs_2)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
    rng = ctx.draw_rng("layout")
    shape_bank = [
        [(0, 0), (1, 0), (2, 0), (2, 1)],          # L-tet
        [(0, 0), (0, 1), (1, 0), (1, 1)],          # 2×2 square
        [(0, 0), (1, 0), (2, 0)],                  # vertical bar
        [(0, 0), (0, 1), (0, 2)],                  # horizontal bar
        [(0, 0), (0, 1), (1, 1), (2, 1)],          # Z-tet
        [(0, 0), (0, 1), (0, 2), (1, 1)],          # T-tet
        [(0, 0), (1, 0), (1, 1)],                  # L-tri
        [(0, 1), (1, 0), (1, 1), (1, 2)],          # T-pent
    ]
    for _ in range(60):
        g = full_grid(h, w, 0)
        template = rng.choice(shape_bank)
        # Pick 1-2 distractors with different shapes
        distractors = rng.sample(
            [s for s in shape_bank if set(s) != set(template)],
            rng.randint(1, 2),
        )
        all_shapes = [(template, 8), (template, 2)] + [(d, 2) for d in distractors]
        rng.shuffle(all_shapes)
        placed_bboxes = []
        ok = True
        for shape, color in all_shapes:
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            placed = False
            for _ in range(40):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                bb = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
                if any(not (bb[2] < pb[0] or pb[2] < bb[0]
                            or bb[3] < pb[1] or pb[3] < bb[1])
                       for pb in placed_bboxes):
                    continue
                paint_at(g, r0, c0, shape, color)
                placed_bboxes.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            return g
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    template = [(0, 0), (1, 0), (2, 0), (2, 1)]
    different = [(0, 0), (0, 1), (1, 0), (1, 1)]
    different2 = [(0, 0), (1, 0), (2, 0)]
    if name == "no_template":
        # no 8-blob → template is undefined, no 2-blob can be matched
        paint_at(g, 1, w - 4, template, 2)
        paint_at(g, h - 4, 1, different, 2)
        paint_at(g, h - 4, w - 4, different2, 2)
        return g
    if name == "all_match":
        # every 2-blob matches the 8 template → all 2s become 3s, no decoy
        paint_at(g, 1, 1, template, 8)
        paint_at(g, 1, w - 4, template, 2)
        paint_at(g, h - 4, 1, template, 2)
        paint_at(g, h - 4, w - 4, template, 2)
        return g
    if name == "no_match":
        # no 2-blob matches the template → rule recolors nothing, output equals input
        paint_at(g, 1, 1, template, 8)
        paint_at(g, 1, w - 4, different, 2)
        paint_at(g, h - 4, 1, different2, 2)
        return g
    return g
