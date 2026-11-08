"""Generator for arc_puzzle_bank_21_set9_e:hard_i21 — keyed boolean of two shapes.

Rule (verified from canonical Racket): cell (0,0) is a KEY (1=union, 2=intersection,
3=xor, else none). The two objects (other than the size-1 key cell at (0,0)) are
cropped, top-left aligned, padded to a common size, and combined by the keyed
boolean, painted colour 8, then cropped.

The previous body was the generic scatter template; its (0,0) was usually not in
{1,2,3} (so op='none' -> [[0]]) and it rarely had exactly two clean shapes, so the
output was degenerate (distinct_out=1, fired=0). This rewrite CONSTRUCTS an isolated
key cell at (0,0) plus exactly two shapes that share a common core (so intersection
is non-empty) with per-shape extras (so union/xor differ).

Axes: grid size, key (operation), the two shapes' core + extras, positions.
Degenerates: op_none, disjoint_shapes, identical_shapes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cd38ccccfca6"
VERSION = "2.4.1"  # ensure boolean operands are distinct so xor/union/intersection teach
TASK_ID = "cd38ccccfca6"

SUMMARY = ("Cell (0,0) keys a boolean op (1=union, 2=intersection, 3=xor); two shapes sharing a "
           "common core (plus per-shape extras) are combined by that op and painted 8. Key, core "
           "shape and extras vary.")

INVARIANTS = [
    "cell (0,0) is an isolated key in {1,2,3}",
    "exactly two connected shapes (objects) besides the key cell",
    "the two shapes share a top-left-anchored core so the boolean is non-trivial",
]

DEGENERATE_TEXTURES = ("op_none", "disjoint_shapes", "identical_shapes")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 9..12", "valid": "7..16"},
    "grid_w":     {"type": "int", "default": "rng 12..16", "valid": "9..20"},
    "key":        {"type": "int", "default": "rng 1..3 (union/intersection/xor)", "valid": "1..3"},
    "core_k":     {"type": "int", "default": "rng 2..4 shared core cells", "valid": "1..6"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "default|warm|cool|varied|op_none|disjoint_shapes|identical_shapes"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _grow(cells, rng, n_extra, s):
    cells = set(cells)
    for _ in range(n_extra):
        frontier = [(r + dr, c + dc) for (r, c) in cells for dr, dc in _CARD
                    if 0 <= r + dr < s and 0 <= c + dc < s and (r + dr, c + dc) not in cells]
        if not frontier:
            break
        cells.add(rng.choice(frontier))
    return cells


def _place(g, cells, r0, c0, color, occupied):
    h, w = len(g), len(g[0])
    abs_cells = [(r0 + r, c0 + c) for r, c in cells]
    for (r, c) in abs_cells:
        if not (0 <= r < h and 0 <= c < w):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (r + dr, c + dc) in occupied:
                    return False
    for (r, c) in abs_cells:
        g[r][c] = color
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                occupied.add((r + dr, c + dc))
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 12, 14)
        core_k = ctx.draw_int("core_k", 1, 3); s = 5; ex_hi = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16); w = ctx.draw_int("grid_w", 16, 20)
        core_k = ctx.draw_int("core_k", 1, 3); s = 6; ex_hi = 6
    else:
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 14, 18)
        core_k = ctx.draw_int("core_k", 1, 3); s = 6; ex_hi = 5
    key = ctx.draw_int("key", 1, 3)
    rng = ctx.draw_rng("layout")

    # shared core (top-left anchored so the two shapes align under crop+pad)
    core = _grow({(0, 0)}, rng, core_k - 1, s)
    shape_a = _grow(set(core), rng, rng.randint(1, ex_hi), s)
    shape_b = _grow(set(core), rng, rng.randint(1, ex_hi), s)
    # If both operands grow the same extra cells, xor becomes empty and the
    # boolean branch collapses.  Retry shape_b, then force one legal extra.
    for _ in range(40):
        if shape_b != shape_a:
            break
        shape_b = _grow(set(core), rng, rng.randint(1, ex_hi), s)
    if shape_b == shape_a:
        frontier = [(r + dr, c + dc) for (r, c) in shape_b for dr, dc in _CARD
                    if 0 <= r + dr < s and 0 <= c + dc < s and (r + dr, c + dc) not in shape_b]
        if frontier:
            shape_b = set(shape_b)
            shape_b.add(rng.choice(frontier))

    g = full_grid(h, w, 0)
    g[0][0] = key
    occupied = {(0, 0), (0, 1), (1, 0), (1, 1)}    # isolate the key cell
    ca, cb = rng.sample([2, 3, 4, 5, 6, 7, 8], 2)
    placed = 0
    for cells, color in ((shape_a, ca), (shape_b, cb)):
        for _ in range(200):
            r0 = rng.randint(0, h - s); c0 = rng.randint(0, w - s)
            if _place(g, cells, r0, c0, color, occupied):
                placed += 1
                break
    if placed < 2:
        return _draw_valid_fallback(key)
    return g


def _draw_valid_fallback(key):
    g = full_grid(10, 14, 0)
    g[0][0] = key
    a = [(0, 0), (0, 1), (1, 0)]
    b = [(0, 0), (1, 0), (1, 1), (2, 1)]
    for r, c in a:
        g[3 + r][3 + c] = 4
    for r, c in b:
        g[3 + r][9 + c] = 6
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    a = [(0, 0), (0, 1), (1, 0)]
    b = [(0, 0), (1, 0), (1, 1)]
    if name == "op_none":
        g[0][0] = 5                               # key not in {1,2,3} -> op none -> [[0]]
    elif name == "identical_shapes":
        g[0][0] = 3                               # xor of identical shapes -> empty
        b = a
    else:                                         # disjoint_shapes -> intersection empty
        g[0][0] = 2
        a = [(0, 0), (0, 1)]; b = [(2, 2), (2, 3)]
    for r, c in a:
        g[3 + r][3 + c] = 4
    for r, c in b:
        g[3 + r][8 + c] = 6
    return g

def _components(grid):
    h = len(grid); w = len(grid[0]) if h else 0; seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or grid[0][0] not in (1, 2, 3):
        msgs.append("cell (0,0) is not a valid boolean key")
    nonkey = [(color, cells) for color, cells in _components(grid) if set(cells) != {(0, 0)}]
    if len(nonkey) != 2:
        msgs.append(f"expected exactly two non-key objects, found {len(nonkey)}")
    elif len({color for color, _ in nonkey}) != 2:
        msgs.append("the two boolean operands do not have distinct colors")
    else:
        norm_a = set(_norm(nonkey[0][1]))
        norm_b = set(_norm(nonkey[1][1]))
        if norm_a == norm_b:
            msgs.append("the two boolean operands have identical normalized support")
        if not (norm_a & norm_b):
            msgs.append("the two boolean operands have empty aligned intersection")
    return msgs


def _norm(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))
