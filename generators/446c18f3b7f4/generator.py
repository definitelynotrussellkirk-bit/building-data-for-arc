"""Generator for arc_additional_puzzle_bank_volume5:E30.

Corners of hollow green rectangles are recolored yellow.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, solid_rects, length_2_frames.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "446c18f3b7f4"
VERSION = "1.2.0"  # QUALITY: bigger grids + more/larger frames on hard (was 2-3 on 13-14); AXES literals
TASK_ID = "446c18f3b7f4"
SUMMARY = ("Corners of hollow GREEN (colour-3) rectangle frames are recolored yellow. "
           "Frame count, sizes and positions scale with difficulty; frame colour is "
           "fixed green because the rule keys on colour 3.")

INVARIANTS = [
    "background is 0",
    "green components are hollow rectangular frames",
    "frames have height and width at least three",
    "frames are separated and not nested",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "solid_rects", "length_2_frames")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "5..22"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "5..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_frames":       {"type": "int", "default": "1 easy / 1-3 med / 3-5 hard", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "1 (frames are green)", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "separated_hollow_frames",
                       "valid": "separated_hollow_frames"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frames|solid_rects|length_2_frames"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
        n_frames = ctx.draw_int("n_frames", 1, 1)
        rh_max = 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 22)
        w = ctx.draw_int("grid_w", 16, 22)
        n_frames = ctx.draw_int("n_frames", 3, 5)
        rh_max = 7
    else:
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 11, 15)
        n_frames = ctx.draw_int("n_frames", 1, 3)
        rh_max = 6
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    boxes: list[tuple[int, int, int, int]] = []
    for _ in range(400):
        if len(boxes) >= n_frames:
            break
        rh = rng.randint(3, min(rh_max, h))
        rw = rng.randint(3, min(rh_max, w))
        r = rng.randint(0, h - rh)
        c = rng.randint(0, w - rw)
        if any(not (r + rh + 1 < ar or ar + ah + 1 < r or c + rw + 1 < ac or ac + aw + 1 < c)
               for ar, ac, ah, aw in boxes):
            continue
        draw_rect_outline(g, r, c, rh, rw, 3)
        boxes.append((r, c, rh, rw))
    if not boxes:
        draw_rect_outline(g, 1, 1, 4, 4, 3)
    return g


def _green_components(grid):
    h, w = len(grid), len(grid[0]); todo = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3}; out = []
    while todo:
        start = todo.pop(); cells = [start]; stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (r + dr, c + dc)
                if p in todo:
                    todo.remove(p); stack.append(p); cells.append(p)
        out.append(cells)
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v not in (0, 3) for row in grid for v in row):
        errors.append("input should contain only background 0 and green frames")
    comps = _green_components(grid)
    if not comps:
        errors.append("expected at least one hollow green frame")
    for cells in comps:
        r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
        if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
            errors.append("frame bbox must be at least 3x3")
        cellset = set(cells)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                border = r in (r1, r2) or c in (c1, c2)
                if border and (r, c) not in cellset:
                    errors.append("frame border must be complete")
                    break
                if not border and (r, c) in cellset:
                    errors.append("frame interior must be hollow")
                    break
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # blank → no frames to recolor corners of
        return g
    if name == "solid_rects":
        # solid rectangles (not hollow frames) → "hollow" precondition fails
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = 3
        for r in range(6, 9):
            for c in range(6, 9):
                g[r][c] = 3
        return g
    if name == "length_2_frames":
        # 2x2 frames → "h,w ≥ 3" precondition fails (also no distinct corners)
        g[1][1] = 3; g[1][2] = 3
        g[2][1] = 3; g[2][2] = 3
        return g
    return g
