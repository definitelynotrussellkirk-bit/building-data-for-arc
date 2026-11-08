"""Generator for 810b9b61.

Rule: each blob whose bbox border is entirely the obj's color (closed
frame) → recolor to 3.

Combinatorial axes (8): grid_h/w, n_frames, n_open_blobs, frame_size_kind,
open_shape_kind, palette_size, position_bias, inter_object_margin.
Degenerates: all_frames, all_open, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "2d83f4efc3e7"
VERSION = "1.2.1"
TASK_ID = "2d83f4efc3e7"
SUMMARY = "Mix of color-1 objects: closed rectangular frames (the 4 border cells of their bbox are all 1) and partial/open shapes (L, T, lines, blobs whose bbox border has gaps). Rule recolors closed frames to color 3; partial shapes stay color 1."

# Rivals: 'output is input' refuted by demos with ≥1 closed frame.
# 'recolor all 1-blobs' refuted by demos with partial shapes that
# stay 1. 'fill frame interior' refuted by demos (interior stays
# 0). 'use color 8 instead' refuted by demos (always 3). 3 demos
# with mix of ≥1 frame and ≥1 open shape cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    ">=1 closed 1-frame of side >=3 (will be recolored)",
    ">=1 partial 1-blob (line or open shape, won't qualify)",
    "no color 3 in input (rule writes 3 for output)",
]

FRAME_SIZE_KINDS = ("small", "medium", "large", "rect_3x3",
                   "rect_4x4", "rect_5x5")
OPEN_SHAPE_KINDS = ("line_h", "line_v", "L_shape", "T_shape",
                    "single", "diag")
DEGENERATE_TEXTURES = ("all_frames", "all_open", "no_blobs")
HELPFUL_TEXTURES = FRAME_SIZE_KINDS

AXES = {
    "grid_h":              {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":              {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "n_frames":            {"type": "int", "default": "rng 1..2", "valid": "1..4"},
    "n_open_blobs":        {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "frame_size_kind":     {"type": "str", "default": "rng helpful",
                            "valid": "small|medium|large|rect_3x3|rect_4x4|rect_5x5"},
    "open_shape_kind":     {"type": "str", "default": "rng helpful",
                            "valid": "line_h|line_v|L_shape|T_shape|single|diag"},
    "position_bias":       {"type": "str", "default": "rng spread|center|edge",
                            "valid": "spread|center|edge"},
    "inter_object_margin": {"type": "int", "default": "1", "valid": "1..3"},
    "texture":             {"type": "str", "default": "alias for frame_size_kind",
                            "valid": "small|medium|large|rect_3x3|rect_4x4|rect_5x5|all_frames|all_open|no_blobs"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, has color-1 cells, and no color-3 in input (rule writes 3 in output)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    ones = sum(grid[r][c] == 1 for r in range(h) for c in range(w))
    if ones == 0:
        errs.append("no color-1 cells found")
    threes = sum(grid[r][c] == 3 for r in range(h) for c in range(w))
    if threes > 0:
        errs.append(f"color-3 should not be in input, found {threes} cells")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 6, 9, 10, 13
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 13, 18, 17, 22
    else:
        h_lo, h_hi, w_lo, w_hi = 8, 14, 12, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_frames = int(overrides.get("n_frames",
                                 ctx.draw_int("n_frames", 1, 2)))
    n_open = int(overrides.get("n_open_blobs",
                               ctx.draw_int("n_open_blobs", 1, 3)))
    n_frames = max(1, min(4, n_frames))
    n_open = max(1, min(5, n_open))
    frame_kind = (overrides.get("texture") or
                  overrides.get("frame_size_kind")
                  or ctx.draw_choice("frame_size_kind",
                                     list(FRAME_SIZE_KINDS)))
    open_kind = overrides.get("open_shape_kind",
                              ctx.draw_choice("open_shape_kind",
                                              list(OPEN_SHAPE_KINDS)))
    margin = int(overrides.get("inter_object_margin", 1))
    g = full_grid(h, w, 0)
    used = set()
    placed_frames = 0
    for _ in range(n_frames * 5):
        if placed_frames >= n_frames:
            break
        fr, fc = _frame_dims(frame_kind, rng)
        if fr > h - 1 or fc > w - 1:
            continue
        for _try in range(20):
            r0 = rng.randint(0, h - fr - 1)
            c0 = rng.randint(0, max(0, w // 2 - fc - 1))
            cells = {(r0 + dr, c0 + dc) for dr in range(fr) for dc in range(fc)
                     if dr in (0, fr - 1) or dc in (0, fc - 1)}
            if not _free_with_margin(used, cells, margin, h, w):
                continue
            for r, c in cells:
                g[r][c] = 1
            used |= cells
            placed_frames += 1
            break
    placed_open = 0
    for _ in range(n_open * 5):
        if placed_open >= n_open:
            break
        cells = _open_shape(open_kind, rng)
        for _try in range(20):
            r0 = rng.randint(0, h - 4)
            c0 = rng.randint(max(0, w // 2 + 1), w - 4)
            placed_cells = {(r0 + dr, c0 + dc) for dr, dc in cells
                            if 0 <= r0 + dr < h and 0 <= c0 + dc < w}
            if not _free_with_margin(used, placed_cells, margin, h, w):
                continue
            for r, c in placed_cells:
                g[r][c] = 1
            used |= placed_cells
            placed_open += 1
            break
    if placed_frames < 1:
        if h >= 4 and w >= 4:
            draw_rect_outline(g, 1, 1, 3, 3, 1)
    if placed_open < 1:
        if h >= 4 and w >= 4:
            g[h - 2][w - 2] = 1
    return g


def _frame_dims(kind, rng):
    if kind == "small":
        return 3, 3
    if kind == "medium":
        return rng.randint(3, 4), rng.randint(3, 4)
    if kind == "large":
        return rng.randint(4, 5), rng.randint(4, 5)
    if kind == "rect_3x3":
        return 3, 3
    if kind == "rect_4x4":
        return 4, 4
    if kind == "rect_5x5":
        return 5, 5
    return rng.randint(3, 5), rng.randint(3, 5)


def _open_shape(kind, rng):
    if kind == "line_h":
        return [(0, c) for c in range(rng.randint(2, 4))]
    if kind == "line_v":
        return [(r, 0) for r in range(rng.randint(2, 4))]
    if kind == "L_shape":
        return [(0, 0), (1, 0), (1, 1)]
    if kind == "T_shape":
        return [(0, 0), (0, 1), (0, 2), (1, 1)]
    if kind == "single":
        return [(0, 0)]
    if kind == "diag":
        n = rng.randint(2, 3)
        return [(i, i) for i in range(n)]
    return [(0, 0)]


def _free_with_margin(used, cells, margin, h, w):
    for r, c in cells:
        if (r, c) in used:
            return False
    for r, c in cells:
        for dr in range(-margin, margin + 1):
            for dc in range(-margin, margin + 1):
                nr, nc = r + dr, c + dc
                if (nr, nc) in used and (nr, nc) not in cells:
                    return False
    return True


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "all_frames":
        if h >= 4 and w >= 4:
            draw_rect_outline(g, 1, 1, 3, 3, 1)
        if h >= 4 and w >= 8:
            draw_rect_outline(g, 1, 5, 3, 3, 1)
        return g
    if name == "all_open":
        for c in range(min(3, w)):
            g[1][c] = 1
        if h >= 4 and w >= 4:
            g[3][1] = 1; g[3][2] = 1
        return g
    if name == "no_blobs":
        return g
    return g
