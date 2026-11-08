"""Generator for fcb5c309.

Rule: most-frequent color = frame; pick the largest frame component;
crop to its bbox; replace frame cells with dot color.

Combinatorial axes (8): grid_h/w, frame_h, frame_w, n_outside, n_inside,
position_bias, palette_kind, anchor_corner.
Degenerates: no_frame, single_frame, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "c1036781e9c5"
VERSION = "2.1.0"  # FIX: small-frame placement now preserves exact, separated frame components.
TASK_ID = "c1036781e9c5"
SUMMARY = (
    "0-bg grid (h, w~10-16) with: (a) 1-2 "
    "RECTANGULAR FRAMES (perimeter outlines) "
    "of size 5×6 to 8×9, in some FRAME_COLOR "
    "(the most frequent non-zero color), "
    "placed by bias (right_lean / centered / "
    "corner / scattered). At least one frame "
    "is LARGER than the other (the largest "
    "is the target); (b) 3-5 SCATTERED DOT "
    "CELLS in a SECOND non-frame color "
    "(DOT_COLOR) outside the largest frame, "
    "plus 1-2 dots INSIDE the largest "
    "frame's interior. Rule: identify the "
    "MOST FREQUENT COLOR (FRAME_COLOR) — its "
    "cells form the rectangular frames. "
    "PICK the LARGEST FRAME component (by "
    "bbox area). CROP the grid to that "
    "frame's bbox. REPLACE the frame's "
    "perimeter cells with the DOT_COLOR. "
    "Net: output is the largest frame "
    "cropped, with its perimeter recolored "
    "to the dot color and its interior "
    "dots preserved."
)

INVARIANTS = [
    "frame_color appears most overall (in the rectangles)",
    "1-2 rectangles of frame_color, the largest is wider+taller than the smaller",
    "scattered dot-color cells (>=3) outside and >=1 inside the largest frame",
]

POSITION_BIASES = ("right_lean", "centered", "corner", "scattered")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frame", "single_frame", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "10..20"},
    "frame_h":        {"type": "int", "default": "rng 5..8", "valid": "4..10"},
    "frame_w":        {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "n_outside":      {"type": "int", "default": "rng 3..5", "valid": "1..8"},
    "n_inside":       {"type": "int", "default": "rng 1..2", "valid": "0..3"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _frame_cells(r0, c0, fh, fw):
    return {(r, c) for r in range(r0, r0 + fh) for c in range(c0, c0 + fw)
            if r in (r0, r0 + fh - 1) or c in (c0, c0 + fw - 1)}


def _can_place_frame(g, r0, c0, fh, fw, frame_c):
    h, w = len(g), len(g[0])
    cells = _frame_cells(r0, c0, fh, fw)
    if r0 < 0 or c0 < 0 or r0 + fh > h or c0 + fw > w:
        return False
    for r, c in cells:
        if g[r][c] != 0:
            return False
        # Keep a one-cell same-colour moat so the smaller frame cannot merge
        # with the target frame into a non-rectangular component.
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if (rr, cc) not in cells and g[rr][cc] == frame_c:
                    return False
    return True


def _place_optional_small_frame(g, rng, frame_c, target_bbox, fh, fw):
    h, w = len(g), len(g[0])
    tr1, tc1, tr2, tc2 = target_bbox
    max_area = (tr2 - tr1 + 1) * (tc2 - tc1 + 1)
    # Choose a strictly smaller frame; skip if the grid is too tight.
    for _ in range(80):
        sh = rng.randint(3, max(3, min(fh - 1, 4)))
        sw = rng.randint(4, max(4, min(fw - 1, 5)))
        if sh * sw >= max_area or sh >= h or sw >= w:
            continue
        r0 = rng.randint(1, h - sh - 1)
        c0 = rng.randint(1, w - sw - 1)
        if _can_place_frame(g, r0, c0, sh, sw, frame_c):
            draw_rect_outline(g, r0, c0, sh, sw, frame_c)
            return True
    return False


def _components_of_color(g, color):
    h, w = len(g), len(g[0])
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or g[r][c] != color:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and g[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append(cells)
    return out


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _is_exact_frame(cells):
    r1, c1, r2, c2 = _bbox(cells)
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return False
    return set(cells) == _frame_cells(r1, c1, r2 - r1 + 1, c2 - c1 + 1)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 8, 10, 10, 12
        no_lo, no_hi = 1, 3
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 14, 18, 16, 20
        no_lo, no_hi = 5, 8
    else:
        h_lo, h_hi, w_lo, w_hi = 10, 14, 12, 16
        no_lo, no_hi = 3, 5
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    pal = _build_palette(palette_kind, rng)
    frame_c, dot_c = pal[0], pal[1]
    fh = int(overrides.get("frame_h",
                           rng.randint(5, min(8, h - 2))))
    fw = int(overrides.get("frame_w",
                           rng.randint(6, min(9, w - 2))))
    fh = max(4, min(fh, h - 2))
    fw = max(5, min(fw, w - 2))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    if bias == "right_lean":
        r0 = rng.randint(1, h - fh - 1)
        c0 = max(1, w - fw - 1)
    elif bias == "centered":
        r0 = max(1, (h - fh) // 2)
        c0 = max(1, (w - fw) // 2)
    elif bias == "corner":
        r0 = rng.choice([1, max(1, h - fh - 1)])
        c0 = rng.choice([1, max(1, w - fw - 1)])
    else:
        r0 = rng.randint(1, max(1, h - fh - 1))
        c0 = rng.randint(1, max(1, w - fw - 1))
    draw_rect_outline(g, r0, c0, fh, fw, frame_c)
    _place_optional_small_frame(g, rng, frame_c, (r0, c0, r0 + fh - 1, c0 + fw - 1), fh, fw)
    n_outside = int(overrides.get("n_outside",
                                  ctx.draw_int("n_outside", no_lo, no_hi)))
    n_outside = max(1, min(10, n_outside))
    placed = 0
    for _ in range(80):
        if placed >= n_outside:
            break
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] == 0 and not (r0 < r < r0 + fh - 1 and c0 < c < c0 + fw - 1):
            g[r][c] = dot_c
            placed += 1
    n_inside = int(overrides.get("n_inside",
                                 ctx.draw_int("n_inside", 1, 2)))
    n_inside = max(1, min(3, n_inside))
    inside_count = 0
    for _ in range(40):
        if inside_count >= n_inside:
            break
        r = rng.randint(r0 + 1, r0 + fh - 2)
        c = rng.randint(c0 + 1, c0 + fw - 2)
        if g[r][c] == 0:
            g[r][c] = dot_c
            inside_count += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """The most-frequent colour should form an exact, uniquely largest frame."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    counts = {}
    for row in grid:
        for v in row:
            if v:
                counts[v] = counts.get(v, 0) + 1
    if len(counts) < 2:
        return ["expected frame colour plus dot colour"]
    frame_c = max(counts, key=lambda c: counts[c])
    frame_comps = [cells for cells in _components_of_color(grid, frame_c) if _is_exact_frame(cells)]
    errors: list[str] = []
    if not frame_comps:
        return ["most-frequent colour has no exact rectangular frame component"]
    areas = []
    for cells in frame_comps:
        r1, c1, r2, c2 = _bbox(cells)
        areas.append((r2 - r1 + 1) * (c2 - c1 + 1))
    if areas.count(max(areas)) != 1:
        errors.append("largest frame is not unique")
    target = frame_comps[areas.index(max(areas))]
    r1, c1, r2, c2 = _bbox(target)
    dot_colors = [c for c in counts if c != frame_c]
    dot_c = max(dot_colors, key=lambda c: counts[c])
    inside = sum(1 for r in range(r1 + 1, r2) for c in range(c1 + 1, c2) if grid[r][c] == dot_c)
    outside = sum(1 for r in range(h) for c in range(w)
                  if grid[r][c] == dot_c and not (r1 <= r <= r2 and c1 <= c <= c2))
    if inside < 1:
        errors.append("largest frame lacks an interior dot-colour witness")
    if outside < 1:
        errors.append("largest frame lacks an outside dot-colour witness")
    return errors


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "no_frame":
        for _ in range(8):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            g[r][c] = 2
        return g
    if name == "single_frame":
        draw_rect_outline(g, 2, 2, 5, 6, 4)
        g[3][4] = 2
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 4
        return g
    return g
