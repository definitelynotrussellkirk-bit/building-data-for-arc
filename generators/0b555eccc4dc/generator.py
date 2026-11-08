"""Generator for 9bebae7a — marker-aspect mirror.

Rule: the color-6 marker's BBOX ASPECT picks the axis — wider than
tall -> mirror UP/DOWN across the 4-shape's edge; tall or square ->
mirror LEFT/RIGHT. Direction: AWAY from the marker if the mirrored
copy fits in-bounds, else TOWARD it; if neither fits the copy clips.
Output keeps ONLY 4s: the marker and any decoys are ERASED (the old
SUMMARY said 'marker stays' - doc lie), original 4s stay + mirror.
Missing 4s or 6s CRASHES — never generated. (Old generator only made
2x2 markers, so the entire wide-marker up/down branch was DEAD and
top/bottom-side boards taught nothing.)

Combinatorial axes: grid_h/w, marker aspect/position, shape, texture
(plain|fallback|decoy|square_marker).
Degenerates: none survivable (documented).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0b555eccc4dc"
RULE_HASH = "c117260d0c56"  # canonical rule this generator was written against
VERSION = "3.0.1"
TASK_ID = "0b555eccc4dc"
SUMMARY = (
    "Wide 6-markers mirror the 4-shape up/down; tall or square "
    "markers mirror left/right - the marker's ASPECT picks the axis, "
    "its position picks the away-direction, and it is ERASED from "
    "the output. fallback boards pin the shape to the wall so the "
    "away-mirror would clip and the rule mirrors TOWARD the marker "
    "instead; decoy boards scatter other colors (erased - output is "
    "4s only); square_marker boards confirm square = left/right."
)

# Rivals: 'marker side picks the axis' refuted by aspect-driven
# boards (wide marker below still mirrors up/down). 'marker survives'
# refuted by every demo. 'always mirror away' refuted by fallback.
# 4 demos covering both axes + >=1 fallback.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    ">=1 four-cell and >=1 six-cell (else crash)",
    "shape asymmetric along the mirrored axis (mirror visible)",
    "fallback boards: the away-direction does not fit, toward does",
]

DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ("plain", "fallback", "decoy", "square_marker")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 10..15", "valid": "9..18"},
    "grid_w":  {"type": "int", "default": "rng 10..15", "valid": "9..18"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|fallback|decoy|square_marker",
                "doc": "fallback: away-mirror clips, mirrors toward "
                       "the marker; decoy: non-4/6 colors erased; "
                       "square_marker: square aspect = left/right."},
}

_COLORS_DECOY = (1, 2, 3, 5, 7, 8, 9)


def _grow(rng, k, max_h, max_w):
    cells = [(0, 0)]
    seen = {(0, 0)}
    for _ in range(300):
        if len(cells) >= k:
            break
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        p = (r + dr, c + dc)
        if p in seen:
            continue
        rs = [q[0] for q in seen] + [p[0]]
        cs = [q[1] for q in seen] + [p[1]]
        if max(rs) - min(rs) + 1 > max_h or max(cs) - min(cs) + 1 > max_w:
            continue
        cells.append(p)
        seen.add(p)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _mirror(g):
    h, w = len(g), len(g[0])
    ys = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 4]
    sx = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 6]
    if not ys or not sx:
        return None
    ry1 = min(r for r, _ in ys)
    ry2 = max(r for r, _ in ys)
    cy1 = min(c for _, c in ys)
    cy2 = max(c for _, c in ys)
    rs1 = min(r for r, _ in sx)
    rs2 = max(r for r, _ in sx)
    cs1 = min(c for _, c in sx)
    cs2 = max(c for _, c in sx)
    six_h, six_w = rs2 - rs1 + 1, cs2 - cs1 + 1
    out = [[4 if g[r][c] == 4 else 0 for c in range(w)] for r in range(h)]
    if six_w > six_h:
        six_below = rs1 > ry2
        up_fits = all(0 <= 2 * ry1 - 1 - r < h for r, _ in ys)
        down_fits = all(0 <= 2 * ry2 + 1 - r < h for r, _ in ys)
        if six_below and up_fits:
            up = True
        elif six_below:
            up = False
        elif down_fits:
            up = False
        else:
            up = True
        for r, c in ys:
            nr = 2 * ry1 - 1 - r if up else 2 * ry2 + 1 - r
            if 0 <= nr < h:
                out[nr][c] = 4
    else:
        six_right = cs1 > cy2
        left_fits = all(0 <= 2 * cy1 - 1 - c < w for _, c in ys)
        right_fits = all(0 <= 2 * cy2 + 1 - c < w for _, c in ys)
        if six_right and left_fits:
            left = True
        elif six_right:
            left = False
        elif right_fits:
            left = False
        else:
            left = True
        for r, c in ys:
            nc = 2 * cy1 - 1 - c if left else 2 * cy2 + 1 - c
            if 0 <= nc < w:
                out[r][nc] = 4
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "plain",
                                              "fallback", "decoy",
                                              "square_marker"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 15)
        w = ctx.draw_int("grid_w", 13, 15)
    else:
        h = ctx.draw_int("grid_h", 10, 15)
        w = ctx.draw_int("grid_w", 10, 15)
    rng = ctx.draw_rng("layout")

    for _attempt in range(200):
        g = full_grid(h, w, 0)
        # marker aspect picks the axis
        if texture == "square_marker":
            mh, mw = 2, 2
        elif rng.random() < 0.5:
            mh, mw = 1 if rng.random() < 0.6 else 2, rng.randint(3, 4)
        else:
            mh, mw = rng.randint(3, 4), 1 if rng.random() < 0.6 else 2
        wide = mw > mh
        # shape, asymmetric along the mirrored axis
        shape = _grow(rng, rng.randint(4, 6), 3, 3)
        s = set(shape)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        if wide:
            if all((sh - 1 - r, c) in s for r, c in shape):
                continue  # UD-symmetric, mirror invisible
        else:
            if all((r, sw - 1 - c) in s for r, c in shape):
                continue
        # place shape: fallback pins it to the wall on the away side
        if texture == "fallback":
            if wide:
                # marker below, away=up doesn't fit: shape at top edge
                sr = rng.randint(0, max(0, sh - 2)) if sh > 1 else 0
                sr = min(sr, sh - 1)  # ensure 2*ry1-1-r < 0 for some r
                sr = 0
                sc = rng.randint(0, w - sw)
            else:
                sc = 0
                sr = rng.randint(0, h - sh)
        else:
            lo_r = sh + 1 if wide else 0
            lo_c = 0 if wide else sw + 1
            hi_r = h - sh - (sh + 1 if wide else 0)
            hi_c = w - sw - (0 if wide else sw + 1)
            if hi_r < lo_r or hi_c < lo_c:
                continue
            sr = rng.randint(lo_r, hi_r)
            sc = rng.randint(lo_c, hi_c)
        for r, c in shape:
            g[sr + r][sc + c] = 4
        # place marker: on the away-opposite side
        placed = False
        for _t in range(100):
            if wide:
                below = rng.random() < 0.5 if texture != "fallback" \
                    else True
                mr = rng.randint(sr + sh + 1, h - mh) \
                    if below and sr + sh + 1 <= h - mh else None
                if not below:
                    mr = rng.randint(0, sr - mh - 1) \
                        if sr - mh - 1 >= 0 else None
                if mr is None:
                    continue
                mc = rng.randint(0, w - mw)
            else:
                right = rng.random() < 0.5 if texture != "fallback" \
                    else True
                mc = rng.randint(sc + sw + 1, w - mw) \
                    if right and sc + sw + 1 <= w - mw else None
                if not right:
                    mc = rng.randint(0, sc - mw - 1) \
                        if sc - mw - 1 >= 0 else None
                if mc is None:
                    continue
                mr = rng.randint(0, h - mh)
            cells = [(mr + r, mc + c) for r in range(mh)
                     for c in range(mw)]
            if all(g[r][c] == 0 for r, c in cells):
                for r, c in cells:
                    g[r][c] = 6
                placed = True
                break
        if not placed:
            continue
        if texture == "decoy":
            for _d in range(rng.randint(2, 4)):
                r = rng.randrange(h)
                c = rng.randrange(w)
                if g[r][c] == 0:
                    g[r][c] = rng.choice(_COLORS_DECOY)
        out = _mirror(g)
        if out is None or out == g:
            continue
        if texture == "fallback":
            # confirm the away-direction truly failed (mirror landed
            # on the marker side)
            ys = [(r, c) for r in range(h) for c in range(w)
                  if g[r][c] == 4]
            if wide:
                ry1 = min(r for r, _ in ys)
                if all(0 <= 2 * ry1 - 1 - r < h for r, _ in ys):
                    continue
            else:
                cy1 = min(c for _, c in ys)
                if all(0 <= 2 * cy1 - 1 - c < w for _, c in ys):
                    continue
        return g
    raise ValueError("could not realize aspect-mirror board")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 color-4 cell (the shape) AND >=1 color-6 cell (the marker)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    has4 = any(grid[r][c] == 4 for r in range(len(grid)) for c in range(len(grid[0])))
    has6 = any(grid[r][c] == 6 for r in range(len(grid)) for c in range(len(grid[0])))
    errors = []
    if not has4:
        errors.append("no color-4 cell (shape missing — rule crashes)")
    if not has6:
        errors.append("no color-6 cell (marker missing — rule crashes)")
    return errors
