"""Generator for arc_puzzle_bank_eleventh21:M71 — translate by the
8->9 vector.

Rule: vector = first-9 minus first-8 (scan order). ALL non-0/8/9
content translates by it onto a BLANK canvas; out-of-bounds cells
clip; the markers are erased. Missing 8 or 9 CRASHES ((first '())) —
never generated.

Combinatorial axes: grid_h/w, vector direction, texture
(plain|clip|multi_shape|multicolor|extra_markers).
Degenerates: no_blob (markers only -> blank output).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0b8631a5fc70"
VERSION = "2.0.1"
TASK_ID = "0b8631a5fc70"
SUMMARY = (
    "8->9 vector translates everything else; vectors now point in ANY "
    "direction (was: always down-right). clip boards push content "
    "partially off-grid; multi_shape boards translate several blobs "
    "by the same vector; multicolor blobs keep per-cell colors; "
    "extra_markers boards add later 8s/9s (only the FIRST of each "
    "counts - all are erased)."
)

# Rivals: 'vector always down-right' refuted by up/left vectors.
# 'content must fit' refuted by clip. 'one object only' refuted by
# multi_shape. 'all 8s/9s pair up' refuted by extra_markers. 3-4
# demos with varied directions.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly the FIRST 8 and FIRST 9 define the vector",
    "plain boards translate fully in-bounds; clip boards lose >=1 "
    "cell and keep >=1",
    "markers never adjacent to payload of the same scan position",
]

DEGENERATE_TEXTURES = ("no_blob",)
HELPFUL_TEXTURES = ("plain", "clip", "multi_shape", "multicolor",
                    "extra_markers")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 7..12", "valid": "6..16"},
    "grid_w":  {"type": "int", "default": "rng 8..13", "valid": "7..16"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|clip|multi_shape|multicolor|"
                         "extra_markers|no_blob",
                "doc": "clip: partial off-grid translation; "
                       "extra_markers: spare 8s/9s ignored (first of "
                       "each wins) and erased."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7)


def _grow(rng, k, max_h=3, max_w=3):
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
    p8 = next(((r, c) for r in range(h) for c in range(w)
               if g[r][c] == 8), None)
    p9 = next(((r, c) for r in range(h) for c in range(w)
               if g[r][c] == 9), None)
    if p8 is None or p9 is None:
        return None
    dr, dc = p9[0] - p8[0], p9[1] - p8[1]
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v in (0, 8, 9):
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = v
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "clip",
                                              "multi_shape", "multicolor",
                                              "extra_markers"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 8, 13)
    rng = ctx.draw_rng("layout")

    for _attempt in range(200):
        g = full_grid(h, w, 0)
        r8, c8 = rng.randrange(h), rng.randrange(w)
        for _t in range(60):
            r9, c9 = rng.randrange(h), rng.randrange(w)
            if (r9, c9) != (r8, c8) and (abs(r9 - r8) + abs(c9 - c8)) >= 2:
                break
        else:
            continue
        g[r8][c8] = 8
        g[r9][c9] = 9
        dr, dc = r9 - r8, c9 - c8
        n_shapes = rng.randint(2, 3) if texture == "multi_shape" else 1
        placed = 0
        clipped = False
        for i in range(n_shapes):
            colors = rng.sample(list(_COLORS), 2) \
                if texture == "multicolor" else [rng.choice(_COLORS)]
            shape = _grow(rng, rng.randint(2, 5))
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            for _t in range(120):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                cells = [(r0 + r, c0 + c) for r, c in shape]
                if any(g[r][c] != 0 for r, c in cells):
                    continue
                tgt = [(r + dr, c + dc) for r, c in cells]
                inb = [p for p in tgt if 0 <= p[0] < h and 0 <= p[1] < w]
                if texture == "clip" and not clipped:
                    if len(inb) == len(tgt) or not inb:
                        continue
                    clipped = True
                elif len(inb) != len(tgt):
                    if texture != "clip":
                        continue
                for r, c in cells:
                    g[r][c] = rng.choice(colors)
                placed += 1
                break
        if placed < n_shapes:
            continue
        if texture == "extra_markers":
            for v in (8, 9):
                for _t in range(60):
                    r, c = rng.randrange(h), rng.randrange(w)
                    if g[r][c] == 0 and (r, c) > ((r8, c8) if v == 8
                                                  else (r9, c9)):
                        g[r][c] = v
                        break
        out = _mirror(g)
        if out is None or all(v == 0 for row in out for v in row):
            continue
        return g
    raise ValueError("could not realize vector-translate board")


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: exactly one 8 and at least one 9 are present (missing
    either causes the rule to crash at (first '()))."""
    msgs = []
    h, w = len(grid), len(grid[0])
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    nines = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if not eights:
        msgs.append("no color-8 marker (rule crashes at (first '()) on missing 8)")
    if not nines:
        msgs.append("no color-9 marker (rule crashes at (first '()) on missing 9)")
    if eights and nines:
        # Payload: non-0/8/9 cells
        payload = [(r, c) for r in range(h) for c in range(w)
                   if grid[r][c] not in (0, 8, 9)]
        if not payload:
            msgs.append(
                "no payload cells (non-0/8/9); "
                "output would be blank (degenerate no_blob board?)"
            )
    return msgs


def _draw_from_degenerate(name, ctx):
    """no_blob — only the two markers: nothing translates, the output
    is blank. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 10)
    w = ctx.draw_int("grid_w", 8, 11)
    g = full_grid(h, w, 0)
    r8, c8 = rng.randrange(h), rng.randrange(w)
    g[r8][c8] = 8
    while True:
        r9, c9 = rng.randrange(h), rng.randrange(w)
        if (r9, c9) != (r8, c8):
            break
    g[r9][c9] = 9
    return g
