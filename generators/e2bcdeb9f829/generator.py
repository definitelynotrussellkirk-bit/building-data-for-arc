"""Generator for arc_additional_puzzles_21_set22_bundle:M154 — stamp template into matching 8-frame.

Rule: non-0/non-8 cells form a template (cropped to bbox). Find an
8-color rectangle frame whose interior dimensions equal the template's
dimensions, and stamp the template into that frame's interior.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_template, no_frame, frame_dim_mismatch.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame, paint_at
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "e2bcdeb9f829"
VERSION = "2.0.0"  # only ONE 8-frame -> the rule's 'pick the frame whose interior matches the template bbox' was trivial; canonical has MULTIPLE frames of different sizes. Add 1-2 distractor frames of non-matching interior dims + randomize the template shape.
TASK_ID = "e2bcdeb9f829"
SUMMARY = "Small random template (non-0/non-8) + the matching 8-frame (interior == template bbox) + 1-2 distractor 8-frames of different interior size; the rule stamps the template into the matching frame only."

INVARIANTS = [
    "background is 0",
    "the non-0, non-8 cells form one small connected template (2-3 colors)",
    "exactly one 8-color rectangle frame has interior dims matching the template bbox",
    "any distractor 8-frames have different interior dims",
    "template and frame don't touch each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_frame", "frame_dim_mismatch")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 14..17", "valid": "12..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "template_left_8frame_right",
                       "valid": "template_left_8frame_right"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_TEMPLATES = [
    [(0, 0), (0, 1), (1, 0), (1, 2)],
    [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
]


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _free(occ, r0, c0, fh, fw):
    h, w = len(occ), len(occ[0])
    if r0 < 0 or c0 < 0 or r0 + fh > h or c0 + fw > w:
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + fh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + fw + 1)):
            if occ[r][c]:
                return False
    return True


def _mark(occ, r0, c0, fh, fw):
    for r in range(r0, r0 + fh):
        for c in range(c0, c0 + fw):
            occ[r][c] = True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 14, 16)
        n_distract = ctx.draw_int("n_distract", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 17, 20)
        n_distract = ctx.draw_int("n_distract", 1, 2)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 15, 18)
        n_distract = ctx.draw_int("n_distract", 1, 2)
    rng = ctx.draw_rng("layout")

    for _attempt in range(40):
        template = _poly(rng, rng.randint(3, 6))
        th = max(c[0] for c in template) + 1
        tw = max(c[1] for c in template) + 1
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        # place template (2 colors) on the left
        tcells = {(r, c) for r, c in template}
        placed = False
        for _ in range(60):
            tr = rng.randint(0, h - th); tc = rng.randint(0, max(0, w // 2 - tw))
            if _free(occ, tr, tc, th, tw):
                palette = list(random_palette(rng, 2, exclude={8}))
                cwc = [(dr, dc, palette[i % 2]) for i, (dr, dc) in enumerate(template)]
                paint_at(g, tr, tc, cwc)
                _mark(occ, tr, tc, th, tw)
                placed = True; break
        if not placed:
            continue
        # matching frame: interior == (th, tw)
        ok = _place_frame(g, occ, rng, th + 2, tw + 2)
        if not ok:
            continue
        # distractor frames: different interior dims
        for _ in range(n_distract):
            for _t in range(20):
                dh = rng.randint(3, 6); dw = rng.randint(3, 6)
                if (dh - 2, dw - 2) != (th, tw) and dh - 2 >= 1 and dw - 2 >= 1:
                    break
            _place_frame(g, occ, rng, dh, dw)
        return g
    return g


def _place_frame(g, occ, rng, fh, fw):
    h, w = len(g), len(g[0])
    if fh > h or fw > w:
        return False
    for _ in range(80):
        r0 = rng.randint(0, h - fh); c0 = rng.randint(0, w - fw)
        if _free(occ, r0, c0, fh, fw):
            draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, 8)
            _mark(occ, r0, c0, fh, fw)
            return True
    return False


def _draw_from_degenerate(name, rng):
    h, w = 10, 15
    g = full_grid(h, w, 0)
    if name == "no_template":
        # 8-frame but no template cells — rule has no shape to stamp.
        draw_frame(g, 2, 9, 5, 13, 8)
        return g
    if name == "no_frame":
        # Template but no 8-frame — rule has no destination interior
        # to stamp into.
        cells = [(0, 0, 3), (0, 1, 4), (1, 0, 3), (1, 2, 4)]
        paint_at(g, 1, 1, cells)
        return g
    if name == "frame_dim_mismatch":
        # Template + 8-frame whose interior dims do NOT match the
        # template bbox — rule's match-by-dim picker finds no
        # candidate.
        cells = [(0, 0, 3), (0, 1, 4), (1, 0, 3), (1, 2, 4)]
        paint_at(g, 1, 1, cells)
        draw_frame(g, 2, 9, 7, 13, 8)
        return g
    return g


def _components(cells):
    cells = set(cells)
    comps = []
    while cells:
        start = cells.pop()
        stack = [start]
        comp = {start}
        while stack:
            r, c = stack.pop()
            for nb in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nb in cells:
                    cells.remove(nb)
                    comp.add(nb)
                    stack.append(nb)
        comps.append(comp)
    return comps

def _is_rect_frame(grid, comp):
    rs = [r for r, _ in comp]; cs = [c for _, c in comp]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
        return None
    expected = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    if comp != expected:
        return None
    if any(grid[r][c] == 8 for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)):
        return None
    return (r0, c0, r1, c1)

def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not all(isinstance(row, list) and row for row in grid):
        return ["grid is empty or malformed"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["rows are ragged"]
    template_cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 8)}
    if not template_cells:
        errors.append("missing non-0/non-8 template")
    elif len(_components(template_cells)) != 1:
        errors.append("template cells should form one 4-connected component")
    tr0 = min((r for r, _ in template_cells), default=0)
    tr1 = max((r for r, _ in template_cells), default=-1)
    tc0 = min((c for _, c in template_cells), default=0)
    tc1 = max((c for _, c in template_cells), default=-1)
    th, tw = tr1 - tr0 + 1, tc1 - tc0 + 1
    tcolors = {grid[r][c] for r, c in template_cells}
    if template_cells and not (2 <= len(tcolors) <= 3):
        errors.append(f"template should use 2-3 colors, got {sorted(tcolors)}")

    eight_cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8}
    frames = []
    for comp in _components(eight_cells):
        frame = _is_rect_frame(grid, comp)
        if frame is None:
            errors.append("8-cells should form separated rectangle frames")
        else:
            frames.append(frame)
    if not frames:
        errors.append("missing 8-color destination frame")
    matches = [fr for fr in frames if (fr[2] - fr[0] - 1, fr[3] - fr[1] - 1) == (th, tw)]
    if len(matches) != 1:
        errors.append(f"expected exactly one frame matching template bbox {(th, tw)}, got {len(matches)}")
    for r, c in template_cells:
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if grid[rr][cc] == 8:
                    errors.append("template touches an 8-frame")
                    return errors
    return errors
