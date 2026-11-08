"""Generator for arc_additional_puzzle_bank_volume19:H127.

Rule: normalize each of the color-1/2/3 shapes to its own bbox; output
the cells that appear in EXACTLY 2 of the 3 normalized sets, bbox-cropped,
in color 8.

Combinatorial axes: grid size, the three shapes (a random per-cell
membership over a k x k frame), and their positions.
Degenerates: shapes_disjoint, all_three_overlap, single_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "c2badae666ad"
VERSION = "2.1.0"  # diversity: random per-cell membership shapes + positions + grid (was 3 fixed shapes)
TASK_ID = "c2badae666ad"
SUMMARY = (
    "0-bg grid (size varies). THREE shapes in colors 1, 2 and 3, placed "
    "apart. They are defined over a shared k x k frame by a random "
    "per-cell MEMBERSHIP: each cell belongs to some subset of the three "
    "shapes, every shape spans the full frame (so the rule's independent "
    "normalization keeps them aligned), and at least one cell belongs to "
    "EXACTLY 2 shapes. Rule: normalize each color's cells to its bbox and "
    "output the cells that appear in exactly 2 of the 3 normalized sets, "
    "bbox-cropped, in COLOR 8 (cyan). The grid size, the three shapes and "
    "their positions all vary freely (was 3 fixed shapes + grid padding)."
)

INVARIANTS = [
    "exactly one blob each of color 1, 2, 3",
    "each shape spans its k x k frame so normalization keeps them aligned",
    "at least one cell belongs to exactly 2 of the 3 shapes",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("shapes_disjoint", "all_three_overlap", "single_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_shapes":       {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "tri_spread", "valid": "tri_spread"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|shapes_disjoint|all_three_overlap|single_shape"},
}


def _spans(cells, k):
    rs = [r for r, c in cells]; cs = [c for r, c in cells]
    return min(rs) == 0 and max(rs) == k - 1 and min(cs) == 0 and max(cs) == k - 1


def _membership(rng, k):
    """Per-cell subset of {1,2,3}; each shape spans the k x k frame and
    >=1 cell is in exactly 2 shapes."""
    cells = [(r, c) for r in range(k) for c in range(k)]
    for _ in range(400):
        sub = {cell: frozenset(i for i in (1, 2, 3) if rng.random() < 0.5) for cell in cells}
        shapes = {i: [cell for cell in cells if i in sub[cell]] for i in (1, 2, 3)}
        if any(not shapes[i] or not _spans(shapes[i], k) for i in (1, 2, 3)):
            continue
        if not any(len(sub[cell]) == 2 for cell in cells):
            continue
        if not any(len(sub[cell]) == 1 for cell in cells):
            continue
        if not any(len(sub[cell]) == 3 for cell in cells):
            continue
        return shapes
    return None


def _free(occ, cells, top, left, h, w):
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = top + r + dr, left + c + dc
                if dr == 0 and dc == 0:
                    if not (0 <= rr < h and 0 <= cc < w):
                        return False
                    if occ[rr][cc]:
                        return False
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, k = (8, 10), (11, 13), 3
    elif difficulty == "hard":
        hr, wr, k = (11, 16), (13, 18), rng.choice([3, 4])
    else:
        hr, wr, k = (9, 12), (11, 15), rng.choice([3, 4])

    for _attempt in range(40):
        shapes = _membership(rng, k)
        if shapes is None:
            continue
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)
        ok = True
        for i in (1, 2, 3):
            cells = shapes[i]
            placed = False
            for _t in range(40):
                top = rng.randint(0, h - k); left = rng.randint(0, w - k)
                if _free(occ, cells, top, left, h, w):
                    paint_at(g, top, left, cells, i)
                    for r, c in cells:
                        occ[top + r][left + c] = True
                    placed = True
                    break
            if not placed:
                ok = False
                break
        if ok:
            return g

    return _fallback_layout(max(h, 8), max(w, 11))


def _fallback_layout(h, w):
    g = full_grid(h, w, 0)
    shapes = {
        1: [(0, 0), (0, 1), (1, 0), (2, 0), (2, 2)],
        2: [(0, 0), (0, 1), (1, 1), (0, 2), (2, 2)],
        3: [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
    }
    # Three 3x3 bboxes with one empty column between them fit the easy lower
    # bound (8 x 11); colors stay separated, while their normalized cells have
    # exact-one, exact-two, and exact-three witnesses.
    for color, left in [(1, 0), (2, 4), (3, 8)]:
        paint_at(g, 1, left, shapes[color], color)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "shapes_disjoint":
        paint_at(g, 1, 1, [(0, 0), (0, 1)], 1)
        paint_at(g, 1, w - 4, [(2, 0), (2, 1)], 2)
        paint_at(g, h - 4, 3, [(0, 2), (1, 2)], 3)
        return g
    if name == "all_three_overlap":
        common = [(0, 0), (1, 0), (2, 0)]
        paint_at(g, 1, 1, common, 1)
        paint_at(g, 1, w - 4, common, 2)
        paint_at(g, h - 4, 3, common, 3)
        return g
    if name == "single_shape":
        paint_at(g, 3, 4, [(0, 0), (0, 1), (1, 0)], 1)
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    by = {i: [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == i]
          for i in (1, 2, 3)}
    if any(not cells for cells in by.values()):
        msgs.append("missing one of colors 1, 2, 3")
        return msgs
    normalized = []
    for color, cells in by.items():
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        normed = {(r - min(rs), c - min(cs)) for r, c in cells}
        normalized.append(normed)
        if len(normed) < 2:
            msgs.append(f"color {color} normalized shape is too small")
    all_cells = set().union(*normalized)
    exact2 = [cell for cell in all_cells if sum(cell in s for s in normalized) == 2]
    exact1 = [cell for cell in all_cells if sum(cell in s for s in normalized) == 1]
    exact3 = [cell for cell in all_cells if sum(cell in s for s in normalized) == 3]
    if not exact2:
        msgs.append("no normalized cell belongs to exactly two shapes")
    if not exact1:
        msgs.append("no normalized single-shape witness")
    if not exact3:
        msgs.append("no normalized all-three/negative exact-two witness")
    return msgs
