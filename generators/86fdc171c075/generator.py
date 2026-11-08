"""Generator for next_b:hard_11 — intersection of two frame interiors.

Rule: 2 hollow rectangular frames (component size ≥ 8 ≈ frame
perimeter ≥ 8). Output paints the intersection of their interior bbox
rectangles in color 7.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: single_frame, no_overlap, identical_frames.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "86fdc171c075"
VERSION = "1.1.1"
TASK_ID = "86fdc171c075"

SUMMARY = "2 hollow rectangular frames in distinct colors with overlapping interior bboxes."

INVARIANTS = [
    "background is 0",
    "exactly 2 hollow rectangular frames in distinct non-bg colors",
    "their interior bboxes overlap by at least 1 cell",
    "frames don't share cells or touch (≥1 bg gap between bboxes is NOT required — they may overlap)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_frame", "no_overlap", "identical_frames")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..14", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "rng 12..15", "valid": "11..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "two_overlapping_frames",
                       "valid": "two_overlapping_frames"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|single_frame|no_overlap|identical_frames"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 2 distinct non-zero colors; each forms a hollow rectangular frame."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    colors = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not colors:
        return []  # empty grid — allowed
    if len(colors) < 2:
        return []  # degenerate single_frame — allowed
    errs = []
    if len(colors) != 2:
        errs.append(f"expected exactly 2 frame colors; found {len(colors)}: {colors}")
        return errs
    # Verify each color forms a rectangular frame (border of a rect)
    for color in colors:
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        rs = [r for r, c in cells]; cs = [c for r, c in cells]
        r1, r2 = min(rs), max(rs); c1, c2 = min(cs), max(cs)
        if r2 - r1 < 2 or c2 - c1 < 2:
            errs.append(f"color {color}: frame too small ({r2-r1+1}x{c2-c1+1})")
            continue
        expected_border = set()
        for c in range(c1, c2 + 1): expected_border.add((r1, c)); expected_border.add((r2, c))
        for r in range(r1 + 1, r2): expected_border.add((r, c1)); expected_border.add((r, c2))
        if set(cells) != expected_border:
            errs.append(f"color {color}: cells don't form a hollow rectangular frame")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 11)
        w = ctx.draw_int("grid_w", 12, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 17)
        w = ctx.draw_int("grid_w", 15, 18)
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 15)
    rng = ctx.draw_rng("layout")
    palette = sorted(rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2))
    for outer in range(40):
        g = full_grid(h, w, 0)
        fa_h = rng.randint(7, 9); fa_w = rng.randint(7, 9)
        if fa_h > h or fa_w > w: continue
        ar1 = rng.randint(0, h - fa_h); ac1 = rng.randint(0, w - fa_w)
        ar2 = ar1 + fa_h - 1; ac2 = ac1 + fa_w - 1
        max_fb_h = fa_h - 2 - 2
        max_fb_w = fa_w - 2 - 2
        if max_fb_h < 4 or max_fb_w < 4: continue
        fb_h = rng.randint(4, max_fb_h)
        fb_w = rng.randint(4, max_fb_w)
        br1 = rng.randint(ar1 + 2, ar2 - fb_h)
        bc1 = rng.randint(ac1 + 2, ac2 - fb_w)
        br2 = br1 + fb_h - 1; bc2 = bc1 + fb_w - 1
        for c in range(ac1, ac2 + 1): g[ar1][c] = palette[0]; g[ar2][c] = palette[0]
        for r in range(ar1, ar2 + 1): g[r][ac1] = palette[0]; g[r][ac2] = palette[0]
        for c in range(bc1, bc2 + 1): g[br1][c] = palette[1]; g[br2][c] = palette[1]
        for r in range(br1, br2 + 1): g[r][bc1] = palette[1]; g[r][bc2] = palette[1]
        return g
    raise ValueError("could not realize nested frames in 40 attempts")


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "single_frame":
        # Only one frame — rule's "intersection of two interiors"
        # has no second operand.
        for c in range(2, 10): g[2][c] = 3; g[8][c] = 3
        for r in range(2, 9): g[r][2] = 3; g[r][9] = 3
        return g
    if name == "no_overlap":
        # Two frames whose interior bboxes are disjoint — rule's
        # intersection is empty; output has no 7-cells.
        for c in range(0, 5): g[1][c] = 3; g[5][c] = 3
        for r in range(1, 6): g[r][0] = 3; g[r][4] = 3
        for c in range(8, 13): g[7][c] = 4; g[10][c] = 4
        for r in range(7, 11): g[r][8] = 4; g[r][12] = 4
        return g
    if name == "identical_frames":
        # Two frames at the same coordinates (same outline) — interior
        # intersection equals each interior; rule's effect just paints
        # the whole interior, lacking the multi-frame signal.
        for c in range(2, 11): g[2][c] = 3; g[8][c] = 3
        for r in range(2, 9): g[r][2] = 3; g[r][10] = 3
        for c in range(2, 11): g[2][c] = 4; g[8][c] = 4
        for r in range(2, 9): g[r][2] = 4; g[r][10] = 4
        return g
    return g



def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            color = grid[r0][c0]
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out


def _is_frame(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
    if r2 - r1 + 1 < 4 or c2 - c1 + 1 < 4:
        return False
    want = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)}
    return set(cells) == want


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    comps = _components(grid)
    if len(comps) != 2:
        errors.append(f"expected exactly two frame components, got {len(comps)}")
    if len({color for color, _ in comps}) != len(comps):
        errors.append("the two frames must use distinct colors")
    frames = []
    for _color, cells in comps:
        if not _is_frame(cells):
            errors.append("component is not an exact hollow rectangular frame")
            continue
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        frames.append((min(rs) + 1, min(cs) + 1, max(rs) - 1, max(cs) - 1))
    if len(frames) == 2:
        r1, c1 = max(frames[0][0], frames[1][0]), max(frames[0][1], frames[1][1])
        r2, c2 = min(frames[0][2], frames[1][2]), min(frames[0][3], frames[1][3])
        if r1 > r2 or c1 > c2:
            errors.append("frame interiors must overlap")
    return errors
