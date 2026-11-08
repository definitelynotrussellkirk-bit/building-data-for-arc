"""Generator for 11b:m71 — singleton+blob census picks the crop.

Rule: for each color in reading order (first cell appearance), count
its 4-conn objects. A color HITS iff it has EXACTLY one singleton
(size 1) and EXACTLY one bigger object. Output = raw subgrid crop of
the FIRST hit color's big object bbox — intruding cells of other
colors inside that bbox appear in the crop. No hit color -> [[0]].

Combinatorial axes: grid_h/w, blob sizes/colors, texture
(plain|near_miss|two_hits|intrusion).
Degenerates: no_hit (census never satisfied -> [[0]]), blank.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0a444f80387e"
VERSION = "3.1.0"  # diversity: wider hit-blob size (3-9 cells) to lift output crop-shape variety
TASK_ID = "0a444f80387e"
SUMMARY = (
    "A color with exactly one singleton + one blob gets its blob "
    "cropped (raw subgrid: intrusion boards put another color's cell "
    "INSIDE the bbox and it shows in the output). Markers sit "
    "anywhere (was: frozen at the bottom-right corner). near_miss "
    "boards carry colors with 2 singletons or 2 blobs (no hit); "
    "two_hits boards have two qualifying colors - first in reading "
    "order wins."
)

# Rivals: 'corner cell is the selector' refuted by free marker
# positions. 'any marked color qualifies' refuted by near_miss
# censuses. 'crop is the blob only' refuted by intrusion boards.
# 'last/biggest hit wins' refuted by two_hits. 3-4 demos.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly one hit color minimum on non-degenerate boards",
    "same-color pieces separated >=2 so censuses stay exact",
    "intrusion boards: a foreign cell inside the hit blob's bbox",
]

DEGENERATE_TEXTURES = ("no_hit", "blank")
HELPFUL_TEXTURES = ("plain", "near_miss", "two_hits", "intrusion")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 8..13", "valid": "7..16"},
    "grid_w":  {"type": "int", "default": "rng 9..14", "valid": "8..16"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|near_miss|two_hits|intrusion|no_hit|blank",
                "doc": "near_miss: 2-singleton and 2-blob colors don't "
                       "hit; two_hits: reading-order-first wins; "
                       "intrusion: foreign cell inside the crop bbox."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def _grow(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _mirror(g):
    h, w = len(g), len(g[0])
    order = []
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v != 0 and v not in order:
                order.append(v)
    seen = set()
    comps = {}
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w \
                            and (nr, nc) not in seen and g[nr][nc] == v:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.setdefault(v, []).append(cells)
    for color in order:
        arr = comps.get(color, [])
        single = [o for o in arr if len(o) == 1]
        big = [o for o in arr if len(o) > 1]
        if len(single) == 1 and len(big) == 1:
            cells = big[0]
            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)
            return [row[c1:c2 + 1] for row in g[r1:r2 + 1]]
    return [[0]]


def _place(g, rng, shape, color, occupied, h, w, forbid=None):
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _t in range(150):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        cells = [(r0 + r, c0 + c) for r, c in shape]
        if forbid and any(p in forbid for p in cells):
            continue
        if all(all(abs(r - orr) > 1 or abs(c - occ) > 1
                   for orr, occ in occupied.get(color, []))
               for r, c in cells) and \
           all(g[r][c] == 0 for r, c in cells):
            for r, c in cells:
                g[r][c] = color
            occupied.setdefault(color, []).extend(cells)
            return cells
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "near_miss",
                                              "two_hits", "intrusion"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 14)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 9, 14)
    rng = ctx.draw_rng("layout")

    for _attempt in range(80):
        g = full_grid(h, w, 0)
        occupied = {}
        n_colors = 4 if texture in ("near_miss", "two_hits") else 3
        colors = rng.sample(_COLORS, n_colors)
        hit, rest = colors[0], colors[1:]

        blob = _place(g, rng, _grow(rng, rng.randint(3, 9)), hit,
                      occupied, h, w)
        if not blob or not _place(g, rng, [(0, 0)], hit, occupied, h, w):
            continue
        if texture == "two_hits":
            c2 = rest[0]
            if not _place(g, rng, _grow(rng, rng.randint(3, 6)), c2,
                          occupied, h, w):
                continue
            if not _place(g, rng, [(0, 0)], c2, occupied, h, w):
                continue
            rest = rest[1:]
        if texture == "near_miss":
            # one color with TWO singletons + a blob; one with 1
            # singleton + TWO blobs - neither hits
            ca, cb = rest[0], rest[1]
            ok = (_place(g, rng, _grow(rng, 3), ca, occupied, h, w) and
                  _place(g, rng, [(0, 0)], ca, occupied, h, w) and
                  _place(g, rng, [(0, 0)], ca, occupied, h, w) and
                  _place(g, rng, _grow(rng, 3), cb, occupied, h, w) and
                  _place(g, rng, _grow(rng, 3), cb, occupied, h, w) and
                  _place(g, rng, [(0, 0)], cb, occupied, h, w))
            if not ok:
                continue
            rest = rest[2:]
        for c in rest:
            # plain decoys: blob only (no singleton)
            _place(g, rng, _grow(rng, rng.randint(2, 4)), c, occupied, h, w)
        if texture == "intrusion":
            r1 = min(r for r, _ in blob)
            r2 = max(r for r, _ in blob)
            c1 = min(c for _, c in blob)
            c2 = max(c for _, c in blob)
            holes = [(r, c) for r in range(r1, r2 + 1)
                     for c in range(c1, c2 + 1) if g[r][c] == 0]
            if not holes:
                continue
            ic = rng.choice([c for c in _COLORS if c not in colors])
            rr, cc = rng.choice(holes)
            g[rr][cc] = ic
        out = _mirror(g)
        if out == [[0]]:
            continue
        return g
    raise ValueError("could not realize census board")


def _draw_from_degenerate(name, ctx):
    """no_hit — blob-only and singleton-only colors, censuses never
    1+1: output [[0]]. blank — empty grid: [[0]]. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 8, 11)
    w = ctx.draw_int("grid_w", 9, 12)
    g = full_grid(h, w, 0)
    if name == "blank":
        return g
    occupied = {}
    ca, cb = rng.sample(_COLORS, 2)
    _place(g, rng, _grow(rng, rng.randint(3, 5)), ca, occupied, h, w)
    _place(g, rng, [(0, 0)], cb, occupied, h, w)
    _place(g, rng, [(0, 0)], cb, occupied, h, w)
    return g


def _selfcheck_components_by_color(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); out = {}
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            q = [(r, c)]; seen.add((r, c)); cells = []
            while q:
                rr, cc = q.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); q.append((nr, nc))
            out.setdefault(color, []).append(cells)
    return out

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    by = _selfcheck_components_by_color(grid)
    hit_colors = []
    for color, comps in by.items():
        singles = [c for c in comps if len(c) == 1]
        blobs = [c for c in comps if len(c) > 1]
        if len(singles) == 1 and len(blobs) == 1:
            hit_colors.append(color)
    if not hit_colors:
        return ["expected at least one color with exactly one singleton and one larger blob"]
    return []
