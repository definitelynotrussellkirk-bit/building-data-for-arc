"""Generator for 16b:m106 — crop the only hollow rectangle.

Rule: pick the (single) rect-frame blob, crop it.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, no_distractors, multiple_frames.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "4fa2745b1aa0"
VERSION = "3.0.1"  # distinct=35: output = the cropped hollow-rectangle frame (dims = frame dims), but gen used only fh,fw in {3,4} -> 4 ring shapes. Now frame 3-7 (+ bigger grids) -> output dims + ring shapes vary widely.
TASK_ID = "4fa2745b1aa0"
SUMMARY = (
    "0-bg grid (h~8-11, w~9-12) with: (a) one HOLLOW "
    "RECTANGULAR FRAME (3-4 rows × 3-4 cols, border-only) "
    "in one color; (b) 1-2 small DISTRACTOR BLOBS (2-4 "
    "cells, irregular shapes) in distinct colors. All "
    "components are 4-disconnected. Rule: identify the "
    "UNIQUE rect-frame (hollow rectangular outline) among "
    "the components. Crop that frame to its bounding box. "
    "Output: the cropped rect-frame (h_frame × w_frame "
    "grid showing just the hollow rectangle border). "
    "Distractors discarded."
)

INVARIANTS = [
    "background is 0",
    "exactly one rect-frame ≥3×3",
    "≥1 non-frame blob (distractor)",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_distractors", "multiple_frames")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "frame_with_distractors",
                       "valid": "frame_with_distractors"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 hollow rectangle frame (border only, no interior fill) >= 3x3; >=1 distractor blob."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Find 4-conn components
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
    components = []
    for r in range(h):
        for c in range(w):
            if not visited[r][c] and grid[r][c] != 0:
                components.append(flood(r, c))
    def is_rect_frame(cells):
        if len(cells) < 8:
            return False
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        if r2 - r1 < 2 or c2 - c1 < 2:
            return False
        expected = set()
        for cc in range(c1, c2+1):
            expected.add((r1, cc)); expected.add((r2, cc))
        for rr in range(r1, r2+1):
            expected.add((rr, c1)); expected.add((rr, c2))
        return set(cells) == expected
    frames = [comp for comp in components if is_rect_frame(comp)]
    non_frames = [comp for comp in components if not is_rect_frame(comp)]
    if not frames:
        errs.append("no hollow rectangle frame found")
    if not non_frames:
        errs.append("no distractor blob found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output = the hollow-rectangle frame cropped, so its dims are the frame
    # dims -> widen the frame size range (was 3-4 only -> 4 ring shapes, distinct=35).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 10, 12); flo, fhi = 3, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 14, 20); flo, fhi = 4, 7
    else:
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 12, 16); flo, fhi = 3, 6
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    for _ in range(40):
        fh = rng.randint(flo, min(fhi, h - 2)); fw = rng.randint(flo, min(fhi, w - 2))
        r1 = rng.randint(0, h - fh)
        c1 = rng.randint(0, w - fw)
        r2 = r1 + fh - 1; c2 = c1 + fw - 1
        if _free(g, r1, c1, r2, c2):
            for c in range(c1, c2 + 1):
                g[r1][c] = palette[0]; g[r2][c] = palette[0]
            for r in range(r1, r2 + 1):
                g[r][c1] = palette[0]; g[r][c2] = palette[0]
            break
    used = {(r, c) for r in range(h) for c in range(w) if g[r][c] != 0}
    for color in palette[1:]:
        cells = grow_blob(rng, h, w, used, rng.randint(2, 4), max_attempts=80)
        if cells:
            for r, c in cells: g[r][c] = color
            used |= cells
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # Distractors only — rule has no rect-frame to crop;
        # selection undefined.
        for r, c in [(2, 2), (3, 2), (3, 3)]: g[r][c] = 4
        for r, c in [(6, 7), (6, 8), (7, 7)]: g[r][c] = 6
        return g
    if name == "no_distractors":
        # Rect-frame but no other blobs — rule's selection is
        # trivially the only object.
        for c in range(2, 7): g[2][c] = 4; g[5][c] = 4
        for r in range(2, 6): g[r][2] = 4; g[r][6] = 4
        return g
    if name == "multiple_frames":
        # Two rect-frames — rule's "single rect-frame" tie-break
        # ambiguous; selection undefined.
        for c in range(1, 5): g[1][c] = 4; g[4][c] = 4
        for r in range(1, 5): g[r][1] = 4; g[r][4] = 4
        for c in range(6, 10): g[5][c] = 6; g[8][c] = 6
        for r in range(5, 9): g[r][6] = 6; g[r][9] = 6
        return g
    return g
