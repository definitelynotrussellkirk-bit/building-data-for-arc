"""Generator for arc_puzzle_bank_21_set17_bundle:hard_p02 — sel + transform + frame.

Rule: (0, 0)=sel color, (0, w-1)=transform code, (h-1, 0)=frame color. Find an
object in sel color; transform; center-place into the frame's interior. The
canonical Racket rule only distinguishes codes 1..4: identity, rotate-CW,
rotate-180, and flip-LR.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_anchors, no_frame, no_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "df19226c9807"
VERSION = "2.2.0"  # v2.2 restricts codes to the canonical 1..4 and adds executable self_check invariants.
TASK_ID = "df19226c9807"

SUMMARY = (
    "0-bg grid (h×w, ~10-18 by ~13-22) with THREE CORNER ANCHORS: "
    "(0, 0) = SEL color (color of the object to select); (0, "
    "w-1) = CODE (transform 1..4: id/rot-cw/rot-180/flip-lr); "
    "(h-1, 0) = FRAME color (color of the "
    "target hollow rectangular frame). Body contains: (a) ONE "
    "hollow rectangular frame in FRAME color (6-7 per side); "
    "(b) ONE connected object (2-4 cells) in SEL color (NOT at "
    "(0, 0)). Rule: read 3 anchors. Find sel-colored object "
    "(excluding (0, 0)) and frame-colored rectangular frame. "
    "Transform object by CODE. Fresh 0-canvas with only the "
    "frame redrawn. Center-paste transformed object inside the "
    "frame interior."
)

# Rivals: 'no transform' refuted by ≥2 demos with non-1 codes. 'use
# sel color for frame fill' refuted by any demo where frame stays
# hollow. 'output input verbatim' refuted by any demo where object
# moves into frame interior. 'discard anchors' refuted by any demo
# where anchors remain in output.
# 4 demos with varied codes + objects + frames cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "(0, 0) holds sel color, (0, w-1) holds transform code (1..4), (h-1, 0) holds frame color",
    "body has 1 hollow rectangular frame in frame-color and 1 small object in sel-color",
    "the object's bbox fits inside the frame's interior",
    "frame and object are isolated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_anchors", "no_frame", "no_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..13", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "rng 14..16", "valid": "12..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "corner_anchors_body_frame",
                       "valid": "corner_anchors_body_frame"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_anchors|no_frame|no_object"},
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
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 13, 15)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 15, 18)
        w = ctx.draw_int("grid_w", 18, 22)
    else:
        h = ctx.draw_int("grid_h", 12, 15)
        w = ctx.draw_int("grid_w", 15, 19)
    rng = ctx.draw_rng("layout")

    sel_color, frame_color = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)

    for outer in range(40):
        g = full_grid(h, w, 0)
        g[0][0] = sel_color
        g[0][w - 1] = rng.randint(1, 4)
        g[h - 1][0] = frame_color
        # The canonical rule centers the transformed object inside the frame
        # interior. A 4-cell line is a legal object, so keep both interior axes
        # at least 4 cells wide (outer side >=6) for every transform branch.
        fh, fw = rng.choice([(6, 6), (6, 7), (7, 6), (7, 7)])
        placed_f = False
        frame_box = None
        for _ in range(120):
            r0 = rng.randint(2, h - fh - 1); c0 = rng.randint(2, w - fw - 1)
            if not _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1): continue
            draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, frame_color)
            placed_f = True
            frame_box = (r0, c0, r0 + fh - 1, c0 + fw - 1)
            break
        if not placed_f:
            continue
        cells = [(0, 0)]; seen = {(0, 0)}
        target = rng.randint(2, 4)
        while len(cells) < target:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if (nr, nc) not in seen:
                cells.append((nr, nc)); seen.add((nr, nc))
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1
        sw = max(cs) - min(cs) + 1
        placed_o = False
        for _ in range(120):
            r0 = rng.randint(2, h - sh - 2); c0 = rng.randint(2, w - sw - 2)
            fr1, fc1, fr2, fc2 = frame_box
            if not (r0 + sh - 1 < fr1 or r0 > fr2 or c0 + sw - 1 < fc1 or c0 > fc2):
                continue
            if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
            for r, c in cells:
                g[r0 + r - min(rs)][c0 + c - min(cs)] = sel_color
            placed_o = True; break
        if placed_o:
            return g
    # graceful fallback: guaranteed valid layout (never raise)
    H, W = max(h, 12), max(w, 16)
    g = full_grid(H, W, 0)
    g[0][0] = sel_color
    g[0][W - 1] = 1
    g[H - 1][0] = frame_color
    draw_frame(g, 3, 3, 7, 7, frame_color)
    for r, c in [(0, 0), (1, 0), (1, 1)]:
        g[H - 4 + r][W - 4 + c] = sel_color
    return g


def _components(cells):
    remaining = set(cells)
    comps = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        comp = {start}
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in remaining:
                    remaining.remove((nr, nc))
                    comp.add((nr, nc))
                    stack.append((nr, nc))
        comps.append(comp)
    return comps


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _rect_border(r1, c1, r2, c2):
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }


def _norm_cells(cells):
    cells = list(cells)
    r0, c0, _, _ = _bbox(cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _rot_cw(cells):
    h = max(r for r, _ in cells) + 1
    return _norm_cells((c, h - 1 - r) for r, c in cells)


def _flip_lr(cells):
    w = max(c for _, c in cells) + 1
    return _norm_cells((r, w - 1 - c) for r, c in cells)


def _transform_cells(cells, code):
    cells = _norm_cells(cells)
    if code == 1:
        return cells
    if code == 2:
        return _rot_cw(cells)
    if code == 3:
        return _rot_cw(_rot_cw(cells))
    return _flip_lr(cells)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the keyed select/transform/frame task.

    The critical regression this guards is the old 1..6 code draw: codes 5/6
    collapse to the rule's fallback identity branch and make demos lie about the
    transform vocabulary. Normal instances must expose only the canonical 1..4
    codes and contain exactly one body object plus one hollow rectangular frame.
    """
    if not grid or not isinstance(grid[0], list):
        return ["empty or malformed grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]

    errs = []
    anchors = {(0, 0), (0, w - 1), (h - 1, 0)}
    sel = grid[0][0]
    code = grid[0][w - 1]
    frame_color = grid[h - 1][0]
    if not (1 <= sel <= 9):
        errs.append(f"selector color must be 1..9, got {sel}")
    if code not in (1, 2, 3, 4):
        errs.append(f"transform code must be canonical 1..4, got {code}")
    if not (1 <= frame_color <= 9):
        errs.append(f"frame color must be 1..9, got {frame_color}")
    if sel == frame_color:
        errs.append("selector and frame colors should be distinct")

    sel_cells = {
        (r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
        if v == sel and (r, c) not in anchors
    }
    obj_comps = _components(sel_cells)
    if len(obj_comps) != 1:
        errs.append(f"expected exactly one selected body object, found {len(obj_comps)}")
        return errs
    obj = obj_comps[0]
    if not (2 <= len(obj) <= 4):
        errs.append(f"selected object should have 2..4 cells, got {len(obj)}")

    frame_cells = {
        (r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
        if v == frame_color and (r, c) not in anchors
    }
    frame_comps = _components(frame_cells)
    rect_frames = []
    for comp in frame_comps:
        r1, c1, r2, c2 = _bbox(comp)
        border = _rect_border(r1, c1, r2, c2)
        if comp == border and r2 - r1 >= 2 and c2 - c1 >= 2:
            rect_frames.append((comp, (r1, c1, r2, c2)))
    if len(rect_frames) != 1:
        errs.append(f"expected exactly one hollow rectangular frame, found {len(rect_frames)}")
        return errs

    frame, (r1, c1, r2, c2) = rect_frames[0]
    if obj & frame:
        errs.append("selected object overlaps the frame")
    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            if grid[r][c] != 0:
                errs.append("frame interior is not empty in the input")
                break
        if errs and errs[-1] == "frame interior is not empty in the input":
            break

    transformed = _transform_cells(obj, code if code in (1, 2, 3, 4) else 1)
    th = max(r for r, _ in transformed) + 1
    tw = max(c for _, c in transformed) + 1
    if th > (r2 - r1 - 1) or tw > (c2 - c1 - 1):
        errs.append(
            f"transformed object {th}x{tw} does not fit frame interior "
            f"{r2 - r1 - 1}x{c2 - c1 - 1}"
        )
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 12, 15
    g = full_grid(h, w, 0)
    if name == "no_anchors":
        # Corner anchors empty — rule has no sel/code/frame-color spec.
        draw_frame(g, 2, 5, 7, 11, 4)
        for dr, dc in [(0, 0), (1, 0), (1, 1)]: g[3 + dr][1 + dc] = 5
        return g
    if name == "no_frame":
        # Anchors set but no frame in body — rule has nowhere to place transformed object.
        g[0][0] = 5; g[0][w - 1] = 2; g[h - 1][0] = 4
        for dr, dc in [(0, 0), (1, 0), (1, 1)]: g[3 + dr][1 + dc] = 5
        return g
    if name == "no_object":
        # Frame + anchors but no sel-color object — rule has nothing to transform.
        g[0][0] = 5; g[0][w - 1] = 2; g[h - 1][0] = 4
        draw_frame(g, 2, 5, 7, 11, 4)
        return g
    return g
