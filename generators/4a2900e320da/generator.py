"""Generator for arc_puzzle_bank_21_set20_bundle:hard_p03 — fill frames by piece hole-count.

Rule: color-2 and color-3 cells form hollow rectangular FRAMES. Among the
other (non-frame) components, the rule pairs each frame to a piece by HOLE
COUNT — a color-2 frame takes the first piece with 0 holes (a solid), a
color-3 frame takes the first piece with 1 hole (a ring) — recolors that piece
to the frame's color and centers it inside the frame's interior. The output is
a blank grid holding each frame outline with its centered piece.

The old generator paired frames to solids by SIZE and drew frames in RANDOM
colors; since the rule only treats color-2/3 rect outlines as frames, ~7/12
instances produced BLANK output (no frame matched), and color-3 frames had no
1-hole piece to take. This rewrite builds the real structure: a color-2 frame
+ a 0-hole solid piece, and a color-3 frame + a 1-hole ring piece (pieces in
rule-ignored colors 6/7, matching the canonical {0,2,3,6,7} input).

Combinatorial axes: frame counts/sizes/positions, the solid piece shape, the
ring piece size, piece colors, grid size.
Degenerates: no_frames, no_solid, no_ring.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4a2900e320da"
VERSION = "3.0.1"  # WRONG-TASK (paired by size, random frame colours -> ~7/12 BLANK outputs): real rule pairs color-2 frame->0-hole piece and color-3 frame->1-hole piece by HOLE COUNT, recolours+centers. Now builds color-2/3 frames + a 0-hole solid piece + a 1-hole ring piece in rule-ignored colours {6,7} (canonical {0,2,3,6,7}).
TASK_ID = "4a2900e320da"

SUMMARY = (
    "0-bg grid with color-2 and color-3 hollow rectangular FRAMES, plus two "
    "non-frame PIECES in rule-ignored colors {6,7}: one SOLID (0 holes) and "
    "one RING (1 enclosed hole). Rule: each color-2 frame takes the 0-hole "
    "piece, each color-3 frame the 1-hole piece; the piece is recolored to "
    "the frame color and centered in its interior. Output = frames with their "
    "centered pieces on a blank grid."
)

INVARIANTS = [
    "background is 0",
    ">=1 color-2 or color-3 hollow rectangular frame",
    "exactly one 0-hole (solid) piece and one 1-hole (ring) piece, colors not in {2,3}",
    "each frame interior fits its paired piece",
    "all objects are isolated",
]

PALETTE_KINDS = ("default",)
DEGENERATE_TEXTURES = ("no_frames", "no_solid", "no_ring")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..22"},
    "n_frame2":       {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "n_frame3":       {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "frames_and_pieces",
                       "valid": "frames_and_pieces"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5"},
    "texture":        {"type": "str", "default": "default",
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


def _outline(g, r0, c0, r1, c1, color):
    for c in range(c0, c1 + 1):
        g[r0][c] = color; g[r1][c] = color
    for r in range(r0, r1 + 1):
        g[r][c0] = color; g[r][c1] = color


def _fill(g, r0, c0, r1, c1, color):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            g[r][c] = color


def _place_box(g, rng, bh, bw, draw):
    """Find a free bh x bw spot (8-gap isolated) and call draw(top,left)."""
    h, w = len(g), len(g[0])
    for _ in range(200):
        top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
        if _free(g, top, left, top + bh - 1, left + bw - 1):
            draw(top, left)
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12); w = ctx.draw_int("grid_w", 13, 15)
        n2 = ctx.draw_int("n_frame2", 1, 1); n3 = ctx.draw_int("n_frame3", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18); w = ctx.draw_int("grid_w", 17, 22)
        n2 = ctx.draw_int("n_frame2", 1, 2); n3 = ctx.draw_int("n_frame3", 2, 2)
    else:
        h = ctx.draw_int("grid_h", 12, 15); w = ctx.draw_int("grid_w", 14, 18)
        n2 = ctx.draw_int("n_frame2", 1, 2); n3 = ctx.draw_int("n_frame3", 1, 2)
    rng = ctx.draw_rng("layout")

    # piece colors are rule-IGNORED (recolored to the frame color) -> restrict
    # to the canonical decoy colors {6,7} so the input distribution matches.
    solid_color, ring_color = rng.sample([6, 7], 2)
    for _outer in range(40):
        g = full_grid(h, w, 0)
        # solid piece (0 holes): filled rect 2..3 x 2..3
        sh = rng.randint(2, 3); sw = rng.randint(2, 3)
        ok = _place_box(g, rng, sh, sw,
                        lambda t, l: _fill(g, t, l, t + sh - 1, l + sw - 1, solid_color))
        # ring piece (1 hole): rect outline >=3 x >=3
        rh = rng.randint(3, 4); rw = rng.randint(3, 4)
        ok = ok and _place_box(g, rng, rh, rw,
                               lambda t, l: _outline(g, t, l, t + rh - 1, l + rw - 1, ring_color))
        if not ok:
            continue
        # color-2 frames (interior fits the solid), color-3 frames (fit the ring)
        placed = 0
        for _i in range(n2):
            pad_h = rng.randint(0, 2); pad_w = rng.randint(0, 2)
            fh = sh + pad_h + 2; fw = sw + pad_w + 2
            if _place_box(g, rng, fh, fw,
                          lambda t, l, fh=fh, fw=fw: _outline(g, t, l, t + fh - 1, l + fw - 1, 2)):
                placed += 1
        for _i in range(n3):
            pad_h = rng.randint(0, 2); pad_w = rng.randint(0, 2)
            fh = rh + pad_h + 2; fw = rw + pad_w + 2
            if _place_box(g, rng, fh, fw,
                          lambda t, l, fh=fh, fw=fw: _outline(g, t, l, t + fh - 1, l + fw - 1, 3)):
                placed += 1
        if placed >= 1:
            return g
    raise ValueError("could not realize 4a2900 layout")


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    # base: a color-2 frame + solid(6), a color-3 frame + ring(7)
    if name != "no_solid":
        _fill(g, 1, 1, 2, 2, 6)
    if name != "no_ring":
        _outline(g, 1, 9, 3, 11, 7)
    if name != "no_frames":
        _outline(g, 6, 1, 10, 5, 2)
        _outline(g, 6, 8, 10, 12, 3)
    return g

def _components_for_self_check(grid, colors=None):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (colors is not None and color not in colors) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out

def _hole_count_for_self_check(cells):
    r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
    r1 = max(r for r, _ in cells); c1 = max(c for _, c in cells)
    occ = {(r - r0 + 1, c - c0 + 1) for r, c in cells}
    h = r1 - r0 + 3; w = c1 - c0 + 3
    seen = set(); holes = 0
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in occ or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]; seen.add((sr, sc)); touches_border = False
            while stack:
                r, c = stack.pop()
                if r in (0, h - 1) or c in (0, w - 1):
                    touches_border = True
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in occ and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
            if not touches_border:
                holes += 1
    return holes

def _rect_frame_for_self_check(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
        return False
    border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
              if r in (r0, r1) or c in (c0, c1)}
    return set(cells) == border


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    comps = _components_for_self_check(grid)
    msgs = []
    frames = [(color, cells) for color, cells in comps if color in (2, 3) and _rect_frame_for_self_check(cells)]
    if not frames:
        msgs.append("expected at least one color-2 or color-3 hollow rectangular frame")
    pieces = [(color, cells, _hole_count_for_self_check(cells)) for color, cells in comps if color in (6, 7)]
    if len(pieces) != 2:
        msgs.append(f"expected exactly two non-frame pieces in colors 6/7, got {len(pieces)}")
    else:
        hole_counts = sorted(h for _, _, h in pieces)
        if hole_counts != [0, 1]:
            msgs.append(f"expected one solid 0-hole piece and one ring 1-hole piece, got {hole_counts}")
    return msgs
