"""Generator for 110177dcbe3a:M114 -- stamp a prototype into size-matching frames.

Rule: the only non-5 object is a PROTOTYPE shape. Among the color-5 hollow
rectangle frames, those whose INTERIOR dimensions equal the prototype's bbox
(h x w) receive a copy of the prototype (in the prototype's color) painted
into their interior; frames of other sizes stay empty.

This generator draws one prototype polyomino, at least one frame whose
interior matches its bbox, and distractor frames of other interior sizes.

Combinatorial axes: grid size, the prototype shape/color, the number of
matching/distractor frames and their positions.
Degenerates: no_frames, no_proto, all_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e71b8db9e07b"
VERSION = "2.1.0"  # diversity + executable invariant coverage
TASK_ID = "e71b8db9e07b"
SUMMARY = (
    "0-bg grid (size varies) with one non-5 PROTOTYPE shape and several "
    "color-5 hollow rectangle frames. Rule: frames whose interior matches the "
    "prototype's bbox get the prototype stamped inside (in its color); other "
    "frames stay empty. The grid size, prototype shape/color and frame "
    "sizes/positions vary freely (was a fixed setup, ~27 distinct)."
)

INVARIANTS = [
    "exactly one non-5 object (the prototype); frames are color-5 rect outlines",
    "frames with interior == proto bbox receive a copy of the proto",
    "at least one matching frame and one distractor frame are present",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_proto", "all_match")
HELPFUL_TEXTURES = PALETTE_KINDS

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "14..28"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "14..28"},
    "proto_size":     {"type": "int", "default": "varies", "valid": "2..7"},
    "n_match":        {"type": "int", "default": "varies", "valid": "1..3"},
    "n_distract":     {"type": "int", "default": "varies", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frames|no_proto|all_match"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _frame_cells(top, left, h, w):
    """color-5 hollow rectangle outline cells of an h x w frame at (top,left)."""
    cells = []
    for r in range(top, top + h):
        for c in range(left, left + w):
            if r in (top, top + h - 1) or c in (left, left + w - 1):
                cells.append((r, c))
    return cells


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def _place(rng, occ, sh, sw, h, w):
    for _t in range(40):
        top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
        if _reserve(occ, top, left, sh, sw, h, w):
            return top, left
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"])

    if difficulty == "easy":
        hr, wr, sr, mr, dr_ = (14, 17), (14, 18), (2, 4), (1, 1), (1, 2)
    elif difficulty == "hard":
        hr, wr, sr, mr, dr_ = (22, 28), (22, 28), (5, 7), (2, 3), (2, 3)
    else:
        hr, wr, sr, mr, dr_ = (17, 22), (17, 23), (3, 5), (1, 2), (1, 3)

    pcolor = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])

    for _attempt in range(80):
        shape = _poly(rng, rng.randint(*sr))
        ph = max(r for r, c in shape) + 1; pw = max(c for r, c in shape) + 1
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]

        # proto placement
        pp = _place(rng, occ, ph, pw, h, w)
        if pp is None:
            continue
        ptop, pleft = pp

        # matching frames: outer (ph+2) x (pw+2)
        matches = []
        for _ in range(rng.randint(*mr)):
            fp = _place(rng, occ, ph + 2, pw + 2, h, w)
            if fp:
                matches.append((fp[0], fp[1], ph + 2, pw + 2))
        # distractor frames: interior dims != (ph,pw), each frame >=3x3
        distract = []
        for _ in range(rng.randint(*dr_)):
            for _t in range(20):
                ih = rng.randint(1, max(1, ph + 2)); iw = rng.randint(1, max(1, pw + 2))
                if (ih, iw) == (ph, pw):
                    continue
                fp = _place(rng, occ, ih + 2, iw + 2, h, w)
                if fp:
                    distract.append((fp[0], fp[1], ih + 2, iw + 2)); break
        if not matches or not distract:
            continue

        g = full_grid(h, w, 0)
        for (r, c) in shape:
            g[ptop + r][pleft + c] = pcolor
        for (ft, fl, fh, fw) in matches + distract:
            for (r, c) in _frame_cells(ft, fl, fh, fw):
                g[r][c] = 5
        return g

    raise ValueError("could not place prototype plus matching and distractor frames")


def _draw_from_degenerate(name):
    h, w = 16, 18
    g = full_grid(h, w, 0)
    shape = [(0, 0), (0, 1), (1, 0)]
    for (r, c) in shape:
        g[2 + r][2 + c] = 3
    if name != "no_proto":
        for (r, c) in _frame_cells(8, 3, 4, 4):   # interior 2x2 matches
            g[r][c] = 5
    if name == "no_proto":
        for (r, c) in _frame_cells(8, 3, 4, 4):
            g[r][c] = 5
        g2 = full_grid(h, w, 0)
        for (r, c) in _frame_cells(8, 3, 4, 4):
            g2[r][c] = 5
        return g2
    if name == "no_frames":
        g3 = full_grid(h, w, 0)
        for (r, c) in shape:
            g3[2 + r][2 + c] = 3
        return g3
    if name == "all_match":
        for (r, c) in _frame_cells(8, 10, 4, 4):
            g[r][c] = 5
    return g



def _components(grid, bg=0):
    h = len(grid); w = len(grid[0]) if h else 0
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == bg or seen[r][c]:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen[r][c] = True; cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in _CARD:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] == color:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _bbox_dims(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return max(rs) - min(rs) + 1, max(cs) - min(cs) + 1


def _is_rect_frame(cells):
    if not cells:
        return False
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, r1 = min(rs), max(rs); c0, c1 = min(cs), max(cs)
    h = r1 - r0 + 1; w = c1 - c0 + 1
    if h < 3 or w < 3:
        return False
    expected = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                if r in (r0, r1) or c in (c0, c1)}
    return set(cells) == expected


def self_check(grid, *, difficulty=None, meta=None):
    """Check one prototype plus at least one matching and one distractor 5-frame."""
    errs = []
    comps = _components(grid, 0)
    proto = [(color, cells) for color, cells in comps if color != 5]
    frames = [(color, cells) for color, cells in comps if color == 5]
    if len(proto) != 1:
        errs.append(f"expected exactly one non-5 prototype object, found {len(proto)}")
        return errs
    pcolor, pcells = proto[0]
    ph, pw = _bbox_dims(pcells)
    if ph < 1 or pw < 1:
        errs.append("prototype bbox is empty")
    match = 0; distract = 0
    for _, cells in frames:
        if not _is_rect_frame(cells):
            errs.append("color-5 component is not a hollow rectangular frame")
            continue
        fh, fw = _bbox_dims(cells)
        ih, iw = fh - 2, fw - 2
        if (ih, iw) == (ph, pw):
            match += 1
        else:
            distract += 1
    if match < 1:
        errs.append("no frame has an interior matching the prototype bbox")
    if distract < 1:
        errs.append("no distractor frame with different interior size")
    return errs
