"""Generator for arc_additional_puzzles_21_set11_bundle:M76.

Rule: the first two objects are normalized to their bboxes; differing
occupancy cells become 8 (XOR of the two normalized shapes).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0c58baa79ba5"
VERSION = "3.2.0"  # fail-closed: exactly two placed objects required
TASK_ID = "0c58baa79ba5"
SUMMARY = (
    "0-bg grid (h~8-11, w~9-13) with EXACTLY TWO separated 4-connected "
    "objects, each a RANDOM polyomino (3-5 cells) of a DISTINCT "
    "normalized shape, in distinct non-bg colours (8 reserved for the "
    "rule output). Rule (XOR OF THE TWO NORMALIZED SHAPES): sort objects "
    "by reading order, take the first two, normalize each to its bbox "
    "top-left, output a max(bbox_h)*max(bbox_w) grid painted 8 where "
    "EXACTLY ONE shape is filled (symmetric difference), 0 elsewhere. "
    "Varied shape pairs -> varied cyan XOR masks."
)

INVARIANTS = [
    "exactly two separated nonzero objects are present",
    "their normalized occupancies differ (XOR is non-empty)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_objects", "identical_shapes", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "7..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "true", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_objects|identical_shapes|full_grid"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_NONBG = [1, 2, 3, 4, 6, 7, 9]   # exclude 0 (bg) and 8 (rule output)


def _poly(rng, n):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _norm_key(cells):
    return tuple(sorted(cells))


def _place(g, cells, color, rng, occ):
    h, w = len(g), len(g[0])
    bh = max(r for r, _ in cells) + 1
    bw = max(c for _, c in cells) + 1
    if bh > h or bw > w:
        return False
    for _ in range(120):
        r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
        ac = [(r0 + r, c0 + c) for r, c in cells]
        if any((r + dr, c + dc) in occ
               for r, c in ac for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            continue
        for r, c in ac:
            g[r][c] = color
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    occ.add((r + dr, c + dc))
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 9, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11); w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 9, 13)
    rng = ctx.draw_rng("layout")

    smax = 6 if difficulty != "easy" else 5
    a = _poly(rng, rng.randint(3, smax))
    b = a
    for _ in range(12):                       # ensure a DIFFERENT normalized shape
        cand = _poly(rng, rng.randint(3, smax))
        if _norm_key(cand) != _norm_key(a):
            b = cand; break
    ca, cb = rng.sample(_NONBG, 2)
    # Previously each _place result was ignored.  Rare easy layouts could return
    # a single component; the canonical XOR rule then crashed while looking up
    # the second object's bbox.  Retry whole placements and fail closed instead
    # of materializing an invalid one-object training example.
    for _layout in range(40):
        g = full_grid(h, w, 0)
        occ = set()
        if _place(g, a, ca, rng, occ) and _place(g, b, cb, rng, occ):
            return g
    raise ValueError("could not place two separated distinct polyomino objects")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly two non-bg 4-connected components with distinct normalized shapes."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    shapes = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or seen[r0][c0]:
                continue
            stack = [(r0, c0)]; seen[r0][c0] = True; cells = []
            while stack:
                r, c = stack.pop(); cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] != 0:
                        seen[nr][nc] = True; stack.append((nr, nc))
            mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
            shapes.append(tuple(sorted((r - mr, c - mc) for r, c in cells)))
    errors = []
    if len(shapes) != 2:
        errors.append(f"expected exactly two non-bg components, got {len(shapes)}")
    elif shapes[0] == shapes[1]:
        errors.append("the two components have identical normalized shapes (XOR is empty)")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 11, 0)
    if name == "no_objects":
        return g
    if name == "identical_shapes":
        from puzzle_generators.helpers.grid import paint_at
        s = [(0, 0), (0, 1), (1, 0)]
        paint_at(g, 1, 1, s, 2)
        paint_at(g, 5, 6, s, 3)
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(11):
                g[r][c] = 2
        return g
    return g
