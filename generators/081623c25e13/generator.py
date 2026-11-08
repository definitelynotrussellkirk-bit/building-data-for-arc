"""Generator for arc_additional_puzzle_bank_volume3:H19 — Crop n-th largest.

Rule: n = at(0,0); set (0,0)=0; sort objs by (size desc, r1, c1); take
n-th object; output bbox-cropped normalized cells.

Combinatorial axes: grid_h, grid_w, n_objects, n, texture
(plain|tie_break|repeat_color).
Degenerates: tied_sizes (rank falls to r1/c1, deterministic).
no_n / n_out_of_range were dropped: list-ref outside range crashes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "081623c25e13"
VERSION = "3.0.1"
TASK_ID = "081623c25e13"
SUMMARY = (
    "Cell (0,0) holds rank n; objects sort by (size desc, r1, c1) and "
    "the n-th is cropped. 3-5 random grown blobs of strictly distinct "
    "sizes 2-7 (tie_break boards share a size so r1/c1 decide); blob "
    "colors may repeat and may equal n. (Was: the same square/domino/"
    "line trio at fixed spots - outputs were 3 shapes in different "
    "colors; no_n and n_out_of_range degenerates crashed the rule.)"
)

# Rivals: 'crop the largest' refuted by n>1 boards. 'rank ascending'
# refuted by n=1 picking the BIGGEST. 'ties are ambiguous' refuted by
# tie_break boards resolved by topmost-then-leftmost bbox. 'n is a
# color cue' refuted by blobs sharing n's color. 4 demos with
# different n values.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "(0,0) holds n with 1 <= n <= number of objects (outside crashes the rule)",
    "blob sizes strictly distinct except in tie_break boards",
    "blobs never touch (halo-separated) and never occupy (0,0) or its right/down neighbors",
]

DEGENERATE_TEXTURES = ("tied_sizes",)
HELPFUL_TEXTURES = ("plain", "tie_break", "repeat_color")

AXES = {
    "grid_h":    {"type": "int", "default": "rng 7..11", "valid": "6..14"},
    "grid_w":    {"type": "int", "default": "rng 10..14", "valid": "7..16"},
    "n_objects": {"type": "int", "default": "rng 3..5", "valid": "2..5"},
    "n":         {"type": "int", "default": "rng 1..n_objects", "valid": "1..5"},
    "texture":   {"type": "str", "default": "rng helpful",
                  "valid": "plain|tie_break|repeat_color|tied_sizes",
                  "doc": "tie_break: two blobs share a size, bbox r1/c1 "
                         "orders them; repeat_color: blob colors repeat "
                         "(incl. n's value as a color)."},
}


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
    n = g[0][0]
    g2 = [row[:] for row in g]
    g2[0][0] = 0
    seen = [[False] * w for _ in range(h)]
    objs = []
    for r0 in range(h):
        for c0 in range(w):
            v = g2[r0][c0]
            if v == 0 or seen[r0][c0]:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and not seen[rr][cc] \
                            and g2[rr][cc] == v:
                        seen[rr][cc] = True
                        stack.append((rr, cc))
            objs.append((v, sorted(cells)))
    objs.sort(key=lambda vc: (-len(vc[1]),
                              min(r for r, _ in vc[1]),
                              min(c for _, c in vc[1])))
    if not (1 <= n <= len(objs)):
        return None
    v, cells = objs[n - 1]
    r1 = min(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    hh = max(r for r, _ in cells) - r1 + 1
    ww = max(c for _, c in cells) - c1 + 1
    out = [[0] * ww for _ in range(hh)]
    for r, c in cells:
        out[r - r1][c - c1] = v
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "tie_break", "repeat_color"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 10, 11)
        n_obj = ctx.draw_int("n_objects", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 12, 14)
        n_obj = ctx.draw_int("n_objects", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 10, 14)
        n_obj = ctx.draw_int("n_objects", 3, 5)
    rng = ctx.draw_rng("layout")
    n = int(overrides.get("n") or rng.randint(1, n_obj))
    n = max(1, min(n, n_obj))

    for _attempt in range(80):
        g = full_grid(h, w, 0)
        g[0][0] = n
        sizes = rng.sample([2, 3, 4, 5, 6, 7], n_obj)
        if texture == "tie_break":
            sizes[1] = sizes[0]  # bbox r1/c1 must order the pair
        if texture == "repeat_color":
            base = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
            colors = [base] * n_obj
        else:
            colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_obj)
        taken = {(0, 0), (0, 1), (1, 0), (1, 1)}  # keep the n cell isolated
        ok = True
        for size, color in zip(sizes, colors):
            shape = _grow(rng, size)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            placed = False
            for _try in range(120):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                cells = {(r0 + r, c0 + c) for r, c in shape}
                halo = {(r + dr, c + dc) for r, c in cells
                        for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
                if halo & taken:
                    continue
                for r, c in cells:
                    g[r][c] = color
                taken |= cells
                placed = True
                break
            if not placed:
                ok = False
                break
        if not ok:
            continue
        if _mirror(g) is None:
            continue
        return g
    raise ValueError("could not realize rank-crop board")


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: (0,0) holds a rank n in 1..n_objects; >=n non-bg
    4-connected objects exist outside (0,0)."""
    msgs = []
    h, w = len(grid), len(grid[0])
    n = grid[0][0]
    if n < 1:
        msgs.append(f"cell (0,0) = {n} is not a valid rank (must be >=1)")
        return msgs
    # Count objects excluding the n-marker at (0,0)
    seen = set()
    comps = []
    for r0 in range(h):
        for c0 in range(w):
            if (r0, c0) in seen:
                continue
            v = grid[r0][c0]
            if v == 0 or (r0 == 0 and c0 == 0):
                seen.add((r0, c0))
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] != 0 and not (nr == 0 and nc == 0)):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    if len(comps) < n:
        msgs.append(
            f"rank n={n} but only {len(comps)} objects found "
            f"(rule would crash on out-of-range list-ref)"
        )
    return msgs


def _draw_from_degenerate(name, ctx):
    """tied_sizes — every blob the same size: ranking falls entirely
    to (r1, c1), still deterministic. rng-varied.
    (no_n / n_out_of_range dropped: list-ref outside 0..len-1 crashes.)
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 10)
    w = ctx.draw_int("grid_w", 10, 13)
    g = full_grid(h, w, 0)
    n_obj = rng.randint(3, 4)
    g[0][0] = rng.randint(1, n_obj)
    size = rng.randint(3, 4)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_obj)
    taken = {(0, 0), (0, 1), (1, 0), (1, 1)}
    for color in colors:
        shape = _grow(rng, size)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        for _try in range(120):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            cells = {(r0 + r, c0 + c) for r, c in shape}
            halo = {(r + dr, c + dc) for r, c in cells
                    for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
            if halo & taken:
                continue
            for r, c in cells:
                g[r][c] = color
            taken |= cells
            break
    return g
