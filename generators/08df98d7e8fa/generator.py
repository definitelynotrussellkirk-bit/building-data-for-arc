"""Generator for d282b262.

Rule: multicolor 8-connected objects on bg=0; rule slides each rightward
(rightmost first), each as far as possible until blocked.

Combinatorial axes: grid_h/w, n_objs, texture
(plain|interlock|rect_blocks).
Degenerates: single_object (still slides), no_room (identity),
full_grid (identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "08df98d7e8fa"
VERSION = "3.1.1"
TASK_ID = "08df98d7e8fa"
SUMMARY = (
    "Multicolor blobs slide rightward, rightmost-first, with PER-CELL "
    "blocking — non-rectangular shapes INTERLOCK when they pack (each "
    "cell scans rightward in the output and the object stops at the "
    "minimum). (Was: rectangular blocks only, so packing was always "
    "bbox-flush and the interlocking semantics never showed.)"
)

# Rivals: 'objects pack bbox-to-bbox' refuted by interlocking blob
# boards (an L slides INTO a C's mouth). 'leftmost first' refuted by
# the rightmost-first order (a left object can pass the lane another
# object vacated... it cannot - it stops at the slid object's cells).
# 'colors merge' refuted by per-cell color preservation. 3-4 demos.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    ">=2 multicolor 8-connected blobs with room to their right",
    "objects pairwise non-touching (8-conn halo)",
]

DEGENERATE_TEXTURES = ("single_object", "no_room", "full_grid")
HELPFUL_TEXTURES = ("plain", "interlock", "rect_blocks")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "grid_w":  {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "n_objs":  {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|interlock|rect_blocks|"
                         "single_object|no_room|full_grid",
                "doc": "interlock: shapes with concavities that mesh when "
                       "packed; rect_blocks: the legacy rectangular look."},
}


def _grow(rng, k, max_h=4):
    cells = [(0, 0)]
    seen = {(0, 0)}
    for _ in range(200):
        if len(cells) >= k:
            break
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        p = (r + dr, c + dc)
        if p in seen:
            continue
        rs = [q[0] for q in seen] + [p[0]]
        if max(rs) - min(rs) + 1 > max_h:
            continue
        cells.append(p)
        seen.add(p)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _components_8(g):
    """Return nonzero 8-connected components as lists of (r, c) cells."""
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r0 in range(h):
        for c0 in range(w):
            if g[r0][c0] == 0 or seen[r0][c0]:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = r + dr, c + dc
                        if (0 <= rr < h and 0 <= cc < w and not seen[rr][cc]
                                and g[rr][cc] != 0):
                            seen[rr][cc] = True
                            stack.append((rr, cc))
            comps.append(sorted(cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """Executable input invariants for the slide-right task."""
    errs = []
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid must be a non-empty rectangular list of rows"]
    w = len(grid[0])
    if w == 0 or any(len(row) != w for row in grid):
        return ["grid must be rectangular and non-empty"]
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if not isinstance(v, int) or not 0 <= v <= 9:
                errs.append(f"cell ({r},{c}) has non-ARC color {v!r}")
    comps = _components_8(grid)
    if difficulty not in DEGENERATE_TEXTURES and len(comps) < 2:
        errs.append("helpful instances should contain at least two 8-connected objects")
    if comps and _mirror(grid) == grid and difficulty not in ("no_room", "full_grid"):
        errs.append("helpful instances should require a non-identity rightward slide")
    return errs


def _mirror(g):
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    objs = []
    for r0 in range(h):
        for c0 in range(w):
            if g[r0][c0] == 0 or seen[r0][c0]:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < h and 0 <= cc < w \
                                and not seen[rr][cc] and g[rr][cc] != 0:
                            seen[rr][cc] = True
                            stack.append((rr, cc))
            objs.append(sorted(cells))
    objs.sort(key=lambda cs: -max(c for _, c in cs))
    out = [[0] * w for _ in range(h)]
    for cells in objs:
        shift = None
        for r, c in cells:
            blocked = None
            for dc in range(1, w - c + 1):
                nc = c + dc
                if nc >= w or out[r][nc] != 0:
                    blocked = dc
                    break
            d = (blocked - 1) if blocked is not None else (w - 1 - c)
            shift = d if shift is None else min(shift, d)
        for r, c in cells:
            out[r][c + shift] = g[r][c]
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "interlock", "rect_blocks"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 14, 16)
        n_objs = ctx.draw_int("n_objs", 2, 3)
        size_range = (6, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 15, 18)
        w = ctx.draw_int("grid_w", 18, 22)
        n_objs = ctx.draw_int("n_objs", 4, 5)
        size_range = (8, 11)
    else:
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 15, 18)
        n_objs = ctx.draw_int("n_objs", 3, 4)
        size_range = (7, 10)
    pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    palette = pool[:7]

    for _attempt in range(160):
        g = full_grid(h, w, 0)
        taken: set = set()
        placed = 0
        for i in range(n_objs):
            if texture == "rect_blocks":
                rh, rw = rng.randint(3, 4), rng.randint(2, 4)
                shape = [(r, c) for r in range(rh) for c in range(rw)]
            elif texture == "interlock" and i == 0:
                # a C-shape opening rightward: later blobs mesh into it
                rh = rng.choice((3, 4))
                shape = [(r, 0) for r in range(rh)]
                shape += [(0, 1), (0, 2), (rh - 1, 1), (rh - 1, 2)]
            else:
                shape = _grow(rng, rng.randint(*size_range))
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            if sh > h or sw > w - 3:
                continue
            ok = False
            for _try in range(240):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, max(0, w // 2 - sw))
                cells = {(r0 + r, c0 + c) for r, c in shape}
                halo = {(r + dr, c + dc) for r, c in cells
                        for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
                if halo & taken:
                    continue
                for r, c in cells:
                    # Use a checker-like multicolor texture so same-color 4-connected
                    # object counts match the canonical sparse/multicolor task instead
                    # of collapsing each blob into only a few color components.
                    g[r][c] = palette[(r + c + i) % len(palette)]
                taken |= cells
                ok = True
                placed += 1
                break
            if not ok:
                break
        if placed != n_objs:
            continue
        if sum(v != 0 for row in g for v in row) < 12:
            continue
        out = _mirror(g)
        if out == g:
            continue
        return g
    raise ValueError("could not realize slide board")


def _draw_from_degenerate(name, ctx):
    """single_object — one blob still slides to the wall. no_room —
    already flush against the right edge: identity. full_grid — one
    object spanning everything: identity. rng-varied."""
    rng = ctx.draw_rng("degenerate_placement")
    h = ctx.draw_int("grid_h", 10, 13)
    w = ctx.draw_int("grid_w", 13, 16)
    g = full_grid(h, w, 0)
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = (r + c) % 4 + 1
        return g
    shape = _grow(rng, rng.randint(4, 6))
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    if name == "no_room":
        r0 = rng.randint(0, h - sh)
        # flush right: every row's rightmost cell at w-1? Simplest:
        # place so the shape's max column sits at w-1 AND pad the rest
        # of each occupied row to the wall so no cell can move
        c0 = w - sw
        for r, c in shape:
            g[r0 + r][c0 + c] = rng.choice(pool)
        for r in range(sh):
            row_cells = [c for rr, c in shape if rr == r]
            if row_cells:
                for c in range(max(row_cells), sw):
                    g[r0 + r][c0 + c] = rng.choice(pool)
        return g
    r0 = rng.randint(0, h - sh)
    c0 = rng.randint(0, max(0, w // 2 - sw))
    for r, c in shape:
        g[r0 + r][c0 + c] = rng.choice(pool)
    return g
