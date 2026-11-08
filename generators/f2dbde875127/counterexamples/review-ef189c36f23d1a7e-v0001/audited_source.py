"""Generator for arc_puzzle_bank_seventh_21_bundle:hard_48_local_rotate_object_to_key_center.

Rule: each color-1 rectangular frame holds a single-color object in its
interior, and a KEY cell (color 2/3/4/5) sits in the row just above the
frame. The rule rotates the object by (key-2) * 90 degrees CW, clears the
interior, and re-centers the rotated object.

This generator places 1-3 frames with SQUARE interiors (so a rotation
always fits), each with a random object, color and key.

Combinatorial axes: grid size, the number of frames, each frame's size
and position, its object shape/color, and its key.
Degenerates: no_key, no_frame, no_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "f2dbde875127"
VERSION = "2.3.0"  # require requested frames and visibly non-identity rotations
TASK_ID = "f2dbde875127"
SUMMARY = (
    "0-bg grid (size varies). 1-3 color-1 (blue) FRAMES with SQUARE "
    "interiors, each holding a single-color object and a KEY cell (color "
    "2/3/4/5) in the row just above. Rule: rotate each framed object by "
    "(key-2)*90 deg CW and re-center it in the interior. The grid size, "
    "frame count/sizes/positions, object shapes/colors and keys all vary "
    "freely (was a fixed 8x15 two-frame layout, ~13 distinct)."
)

INVARIANTS = [
    "each frame is a color-1 rectangular outline with a square interior",
    "each interior holds one single-color object whose bbox fits the interior",
    "a key cell (2/3/4/5) sits in the row directly above each frame",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "no_frame", "no_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..26"},
    "n_frames":       {"type": "int", "default": "varies", "valid": "1..3"},
    "key":            {"type": "int", "default": "varies visible", "valid": "3|5"},
    "interior":       {"type": "int", "default": "varies", "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "frames_apart", "valid": "frames_apart"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "2..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_key|no_frame|no_object"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size, smax):
    for _ in range(30):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice(_CARD)
            cells.add((r + dr, c + dc))
        nl = _norm(cells)
        h = max(r for r, c in nl) + 1; w = max(c for r, c in nl) + 1
        if h <= smax and w <= smax:
            return nl
    return [(0, 0)]


def _rotate_norm(cells, turns):
    pts = _norm(cells)
    for _ in range(turns % 4):
        hh = max(r for r, _ in pts) + 1
        pts = _norm([(c, hh - 1 - r) for r, c in pts])
    return sorted(pts)


def _visibly_rotates(cells, key):
    return sorted(_norm(cells)) != _rotate_norm(cells, key - 2)


def _reserve(occ, top, left, bh, bw, h, w, margin=1):
    for r in range(top - margin, top + bh + margin):
        for c in range(left - margin, left + bw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nr, sr = (9, 12), (10, 13), (1, 1), (3, 4)
    elif difficulty == "hard":
        hr, wr, nr, sr = (16, 24), (17, 26), (2, 3), (4, 6)
    else:
        hr, wr, nr, sr = (12, 17), (13, 20), (1, 2), (3, 5)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        target_frames = rng.randint(*nr)
        placed = 0
        for _ in range(target_frames):
            S = rng.randint(*sr)               # square interior side
            fh = S + 2                          # frame outer size
            if fh + 1 > h or fh > w:
                continue
            for _t in range(40):
                # reserve the frame plus the key row above it
                top = rng.randint(1, h - fh)    # >=1 so the key row (top-1) exists
                left = rng.randint(0, w - fh)
                if not _reserve(occ, top - 1, left, fh + 1, fh, h, w, margin=1):
                    continue
                r0, c0, r1, c1 = top, left, top + fh - 1, left + fh - 1
                draw_frame(g, r0, c0, r1, c1, 1)
                # object inside the interior.  Normal demos avoid key=2 and
                # 90-degree-symmetric shapes so the canonical keyed rotation is
                # visibly taught instead of sometimes becoming an identity demo.
                ir0, ic0 = r0 + 1, c0 + 1
                key = rng.choice([3, 5])
                for _shape_try in range(30):
                    obj = _poly(rng, rng.randint(2, max(2, S * S // 2)), S)
                    if _visibly_rotates(obj, key):
                        break
                else:
                    obj = [(0, 0), (1, 0), (1, 1)]
                oh = max(r for r, c in obj) + 1; ow = max(c for r, c in obj) + 1
                otop = ir0 + rng.randint(0, S - oh); oleft = ic0 + rng.randint(0, S - ow)
                ocolor = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])  # any non-bg, non-frame color (canonical uses 2/4 too)
                for (r, c) in obj:
                    g[otop + r][oleft + c] = ocolor
                # key cell above the frame
                keycol = rng.randint(c0, c1)
                g[r0 - 1][keycol] = key
                placed += 1
                break
        if placed == target_frames:
            return g

    raise ValueError("could not place requested keyed rotation frames")


def _color1_components(grid):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 1 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    comps = _color1_components(grid)
    min_frames = 2 if difficulty == "hard" else 1
    if len(comps) < min_frames:
        errs.append(f"expected at least {min_frames} color-1 frames, found {len(comps)}")
    if len(comps) > 3:
        errs.append(f"expected at most 3 color-1 frames, found {len(comps)}")
    for cells in comps:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        fh = r1 - r0 + 1
        fw = c1 - c0 + 1
        if fh != fw or fh < 5:
            errs.append(f"frame bbox {(r0, c0, r1, c1)} must be square outer size >=5")
            continue
        border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                  if r in (r0, r1) or c in (c0, c1)}
        if set(cells) != border:
            errs.append(f"color-1 component at {(r0, c0, r1, c1)} is not a hollow rectangular frame")
            continue
        if r0 == 0:
            errs.append("frame has no row above for the key")
            continue
        keys = [(r0 - 1, c, grid[r0 - 1][c]) for c in range(c0, c1 + 1) if grid[r0 - 1][c] in (2, 3, 4, 5)]
        if len(keys) != 1:
            errs.append(f"frame {(r0, c0, r1, c1)} expected exactly one key 2..5 above it, found {len(keys)}")
        elif keys[0][2] == 2:
            errs.append(f"frame {(r0, c0, r1, c1)} uses key=2, which is a zero-rotation identity demo")
        interior = [(r, c, grid[r][c]) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1) if grid[r][c] != 0]
        if not interior:
            errs.append(f"frame {(r0, c0, r1, c1)} has empty interior object")
        colors = {v for _, _, v in interior}
        if len(colors) != 1:
            errs.append(f"frame {(r0, c0, r1, c1)} interior should be one object color, found {sorted(colors)}")
        elif len(keys) == 1 and keys[0][2] in (3, 5):
            norm_obj = _norm([(r - (r0 + 1), c - (c0 + 1)) for r, c, _ in interior])
            if not _visibly_rotates(norm_obj, keys[0][2]):
                errs.append(f"frame {(r0, c0, r1, c1)} interior object is symmetric under its keyed rotation")
    return sorted(set(errs))


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 9, 0)
    shape = [(0, 0), (1, 0), (1, 1), (2, 1)]
    if name == "no_key":
        draw_frame(g, 1, 1, 7, 7, 1)
        for (r, c) in shape:
            g[2 + r][2 + c] = 7
        return g
    if name == "no_frame":
        g[0][3] = 3
        for (r, c) in shape:
            g[2 + r][2 + c] = 7
        return g
    if name == "no_object":
        draw_frame(g, 1, 1, 7, 7, 1)
        g[0][3] = 3
        return g
    return g
