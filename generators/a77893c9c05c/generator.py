"""Generator for arc_puzzle_bank_fourth21:M26 — fill rect-frames + leave non-frames.

Rule: for each blob whose shape is a rect-frame (hollow rect outline),
fill its interior with the frame's color. Non-frame blobs untouched.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, only_2x2, only_distractors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "a77893c9c05c"
VERSION = "1.3.0"  # add executable frame/distractor invariants
TASK_ID = "a77893c9c05c"
SUMMARY = "Each blob whose shape is a hollow rectangle outline gets its interior filled with the frame color. Non-frame blobs (irregular shapes, solid blocks) are left unchanged."

# Rivals: 'fill all blob bboxes' refuted by ≥1 demo where a non-frame
# blob bbox is left alone. 'erase non-frame blob' refuted by ≥1 demo
# where distractor survives. 'use bg(0) for interior' refuted by any
# demo (interior uses frame color). 'apply only to one frame' refuted
# by ≥2 demos with multiple frames all filled.
# 4 demos with varied frame sizes + distractors cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "≥1 rect-frame at least 4x4",
    "≥1 non-frame blob (so rule has both branches)",
    "shapes don't overlap (1-cell padding)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "only_2x2", "only_distractors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..17"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "frame_with_distractor",
                       "valid": "frame_with_distractor"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
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


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 12)
        n_frames = 1
        n_distractors = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 17)
        w = ctx.draw_int("grid_w", 15, 20)
        n_frames = rng.randint(2, 3)
        n_distractors = rng.randint(2, 4)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 16)
        n_frames = rng.randint(1, 2)
        n_distractors = rng.randint(1, 2)
    g = full_grid(h, w, 0)
    color_pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(color_pool)
    # Place frames
    color_idx = 0
    placed_frames = 0
    for _ in range(80):
        if placed_frames >= n_frames or color_idx >= len(color_pool):
            break
        fh = rng.randint(4, max(4, h // 2))
        fw = rng.randint(4, max(4, w // 2))
        r1 = rng.randint(0, h - fh)
        c1 = rng.randint(0, w - fw)
        r2 = r1 + fh - 1; c2 = c1 + fw - 1
        if not _free(g, r1, c1, r2, c2):
            continue
        col = color_pool[color_idx]; color_idx += 1
        for c in range(c1, c2 + 1):
            g[r1][c] = col; g[r2][c] = col
        for r in range(r1, r2 + 1):
            g[r][c1] = col; g[r][c2] = col
        placed_frames += 1
    # Place non-frame distractor blobs (irregular blobs).
    for _ in range(n_distractors):
        if color_idx >= len(color_pool):
            break
        used = {(r, c) for r in range(h) for c in range(w) if g[r][c] != 0}
        cells = grow_blob(rng, h, w, used, rng.randint(3, 6), max_attempts=80)
        if not cells:
            continue
        col = color_pool[color_idx]; color_idx += 1
        for r, c in cells:
            g[r][c] = col
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # Only non-frame blobs — rule's "fill frame interior"
        # branch never fires; output equals input.
        for r, c in [(2, 2), (3, 2), (3, 3)]: g[r][c] = 4
        for r, c in [(7, 8), (7, 9), (8, 8)]: g[r][c] = 6
        return g
    if name == "only_2x2":
        # 2x2 solid blocks (not frames, no interior) — rule's
        # frame filter excludes; output equals input.
        for r in range(2, 4):
            for c in range(2, 4): g[r][c] = 4
        for r in range(7, 9):
            for c in range(8, 10): g[r][c] = 6
        return g
    if name == "only_distractors":
        # Multiple non-rectangular shapes only — rule's frame
        # branch never fires.
        for r, c in [(2, 2), (2, 3), (3, 3), (4, 3)]: g[r][c] = 4
        for r, c in [(6, 7), (7, 6), (7, 7), (7, 8)]: g[r][c] = 6
        return g
    return g



def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _rect_frame(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, r1 = min(rs), max(rs); c0, c1 = min(cs), max(cs)
    hh, ww = r1 - r0 + 1, c1 - c0 + 1
    if hh < 3 or ww < 3:
        return False
    border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
              if r in (r0, r1) or c in (c0, c1)}
    return set(cells) == border


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["empty or ragged grid"]
    comps = _components(grid)
    frames = [cells for _color, cells in comps if _rect_frame(cells)]
    distractors = [cells for _color, cells in comps if not _rect_frame(cells)]
    if not frames:
        errs.append("missing hollow rectangular frame")
    if not distractors:
        errs.append("missing non-frame distractor branch")
    for cells in frames:
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        if max(rs) - min(rs) + 1 < 4 or max(cs) - min(cs) + 1 < 4:
            errs.append("frame should be at least 4x4 to have visible interior")
    return errs
