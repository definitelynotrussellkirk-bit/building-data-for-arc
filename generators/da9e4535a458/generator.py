"""Generator for 11b:hard_72 — boolean operation by marker.

Rule: a marker cell with value 4 (OR), 5 (AND), or 6 (XOR) selects the
op. Two 9-frames with binary contents inside; output is the cropped
op-result colored 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker (no op marker → rule has no op);
no_frames (marker but no 9-frames → rule has no operands);
identical_frames (two frame contents identical → AND/OR == A,
XOR is empty).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "da9e4535a458"
VERSION = "2.1.0"  # add executable invariant self_check
TASK_ID = "da9e4535a458"
SUMMARY = (
    "0-bg grid (h ∈ 11-13, w ∈ 14-18) "
    "with: (a) ONE ISOLATED MARKER "
    "CELL — random position, value "
    "∈ {4, 5, 6} (op_marker, with 4=OR, "
    "5=AND, 6=XOR), placed with 1-cell "
    "padding from all other non-bg "
    "cells; (b) TWO HOLLOW COLOR-9 "
    "FRAMES — each is a rectangular "
    "ring of color 9 with the same "
    "interior dimensions (ih × iw, "
    "ih ∈ 3-4, iw ∈ 3-4), placed at "
    "non-overlapping positions with "
    "1-cell padding; each frame's "
    "INTERIOR is sprinkled with 3 to "
    "(interior_size - 1) cells of one "
    "non-9 color (the two frames use "
    "DIFFERENT interior colors drawn "
    "from {1,2,3,7,8}). Generation "
    "retries until the op result has "
    "≥1 hit cell. Rule (READ THE "
    "MARKER, COMPUTE THE BOOLEAN "
    "COMBINATION OF THE TWO FRAMES' "
    "INTERIOR MASKS, OUTPUT AS COLOR "
    "8): READ the marker value (4/5/6) "
    "→ choose op ∈ {OR, AND, XOR}. "
    "BUILD binary mask A from frame "
    "1's interior (1 where non-bg, 0 "
    "else) and binary mask B from "
    "frame 2's interior. COMPUTE the "
    "elementwise boolean combination "
    "A op B. OUTPUT an ih × iw GRID: "
    "PAINT COLOR 8 where the result "
    "is true, COLOR 0 elsewhere. Net: "
    "marker selects an operator; two "
    "frame interiors are unioned/"
    "intersected/xored into a small "
    "cyan-8 mask."
)

INVARIANTS = [
    "background is 0",
    "exactly one isolated marker cell with value in {4, 5, 6}",
    "exactly 2 hollow 9-frames with the same interior dimensions",
    "each frame's interior holds 3-6 non-bg cells in distinct colors per frame",
    "the marker-selected boolean op result has at least 1 non-bg cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_frames", "identical_frames")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "grid_w":            {"type": "int", "default": "rng 14..18", "valid": "13..22"},
    "frame_ih":          {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "frame_iw":          {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "position_bias":     {"type": "str", "default": "marker_plus_two_frames",
                          "valid": "marker_plus_two_frames"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 14, 15)
        ih = ctx.draw_int("frame_ih", 3, 3)
        iw = ctx.draw_int("frame_iw", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 16, 18)
        ih = ctx.draw_int("frame_ih", 4, 4)
        iw = ctx.draw_int("frame_iw", 4, 4)
    else:
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 14, 18)
        ih = ctx.draw_int("frame_ih", 3, 4)
        iw = ctx.draw_int("frame_iw", 3, 4)
    rng = ctx.draw_rng("layout")
    fh = ih + 2; fw = iw + 2
    op = rng.choice([4, 5, 6])
    for _ in range(40):
        g = full_grid(h, w, 0)
        for _ in range(40):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0: continue
            bad = False
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                        bad = True; break
                if bad: break
            if bad: continue
            g[r][c] = op; break
        masks = []
        ok = True
        colors_inner = rng.sample([1, 2, 3, 7, 8], 2)
        for color in colors_inner:
            placed = False
            for _ in range(60):
                r0 = rng.randint(0, h - fh); c0 = rng.randint(0, w - fw)
                if not _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1): continue
                for c in range(c0, c0 + fw): g[r0][c] = 9; g[r0 + fh - 1][c] = 9
                for r in range(r0, r0 + fh): g[r][c0] = 9; g[r][c0 + fw - 1] = 9
                interior = [(r, c) for r in range(r0 + 1, r0 + fh - 1)
                            for c in range(c0 + 1, c0 + fw - 1)]
                n = rng.randint(3, max(3, len(interior) - 1))
                slots = rng.sample(interior, n)
                mask = [[0] * iw for _ in range(ih)]
                for r, c in slots:
                    g[r][c] = color
                    mask[r - r0 - 1][c - c0 - 1] = 1
                masks.append(mask)
                placed = True; break
            if not placed: ok = False; break
        if not ok or len(masks) < 2: continue
        a, b = masks
        any_hit = False
        for r in range(ih):
            for c in range(iw):
                aa, bb = bool(a[r][c]), bool(b[r][c])
                if op == 4: hit = aa or bb
                elif op == 5: hit = aa and bb
                else: hit = aa != bb
                if hit: any_hit = True; break
            if any_hit: break
        if not any_hit: continue
        return g
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 15
    g = full_grid(h, w, 0)
    ih, iw = 3, 3; fh, fw = ih + 2, iw + 2
    if name == "no_marker":
        # No marker — rule has no op.
        for c in range(2, 7): g[1][c] = 9; g[5][c] = 9
        for r in range(1, 6): g[r][2] = 9; g[r][6] = 9
        g[2][3] = 1; g[3][4] = 1
        for c in range(8, 13): g[1][c] = 9; g[5][c] = 9
        for r in range(1, 6): g[r][8] = 9; g[r][12] = 9
        g[2][9] = 2; g[3][10] = 2
        return g
    if name == "no_frames":
        # Marker but no frames.
        g[10][7] = 4
        return g
    if name == "identical_frames":
        # Both frames have identical contents — XOR empty.
        g[10][7] = 6
        for c in range(2, 7): g[1][c] = 9; g[5][c] = 9
        for r in range(1, 6): g[r][2] = 9; g[r][6] = 9
        g[2][3] = 1; g[3][4] = 1; g[3][5] = 1
        for c in range(8, 13): g[1][c] = 9; g[5][c] = 9
        for r in range(1, 6): g[r][8] = 9; g[r][12] = 9
        g[2][9] = 2; g[3][10] = 2; g[3][11] = 2
        return g
    return g

def _components_of_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); comp = []
            while stack:
                rr, cc = stack.pop(); comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(comp)
    return comps


def _frame_info(grid, comp):
    rs = [r for r, c in comp]; cs = [c for r, c in comp]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    if r1 - r0 < 2 or c1 - c0 < 2:
        return None
    want = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)}
    if set(comp) != want:
        return None
    ih, iw = r1 - r0 - 1, c1 - c0 - 1
    mask = []
    nonzero = 0
    for r in range(r0 + 1, r1):
        row = []
        for c in range(c0 + 1, c1):
            hit = grid[r][c] != 0
            row.append(1 if hit else 0)
            nonzero += int(hit)
            if grid[r][c] == 9:
                return None
        mask.append(row)
    return (r0, c0, ih, iw, mask, nonzero)


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    markers = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] in (4, 5, 6)]
    if len(markers) != 1:
        errs.append(f"expected exactly one op marker, found {len(markers)}")
    elif any(0 <= markers[0][0] + dr < h and 0 <= markers[0][1] + dc < w
             and (dr or dc) and grid[markers[0][0] + dr][markers[0][1] + dc] != 0
             for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
        errs.append("op marker is not isolated by a zero moat")
    frames = [_frame_info(grid, comp) for comp in _components_of_color(grid, 9)]
    frames = [f for f in frames if f is not None]
    if len(frames) != 2:
        errs.append(f"expected exactly two hollow 9-frames, found {len(frames)}")
        return sorted(set(errs))
    if len({(f[2], f[3]) for f in frames}) != 1:
        errs.append("the two frames do not share the same interior dimensions")
    if any(f[5] < 3 for f in frames):
        errs.append("each frame interior should contain at least three active cells")
    if len(markers) == 1 and len({(f[2], f[3]) for f in frames}) == 1:
        op = markers[0][2]
        a, b = frames[0][4], frames[1][4]
        any_hit = False
        for r in range(len(a)):
            for c in range(len(a[0])):
                aa, bb = bool(a[r][c]), bool(b[r][c])
                if (op == 4 and (aa or bb)) or (op == 5 and (aa and bb)) or (op == 6 and (aa != bb)):
                    any_hit = True
        if not any_hit:
            errs.append("marker-selected boolean result is empty")
    return sorted(set(errs))
