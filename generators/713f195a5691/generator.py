"""Generator for arc_puzzle_bank_21_set3:S3_H6.

The number of color-1 cells in the left panel selects the green object of that
size in the right panel; the rule draws a cyan bounding box around it.

Combinatorial axes (8): grid_h, grid_w, palette_kind, marker_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, no_size_match, multiple_size_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "713f195a5691"
VERSION = "2.1.0"  # fix crash: center the separator and require a unique matching-size right-panel object
TASK_ID = "713f195a5691"
SUMMARY = "Left-panel marker count selects the matching-size green object on the right."

INVARIANTS = [
    "one empty separator column divides the grid",
    "left-panel color-1 marker count is between 4 and 6",
    "right panel has exactly one color-3 object with that size",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_size_match", "multiple_size_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "marker_count":   {"type": "int", "default": "rng 4..6", "valid": "3..7"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "left_count_plus_right_blobs",
                       "valid": "left_count_plus_right_blobs"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_markers|no_size_match|multiple_size_match"},
}

_SHAPES = {
    3: [(0, 0), (1, 0), (1, 1)],
    4: [(0, 0), (1, 0), (1, 1), (2, 1)],
    5: [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
    6: [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2)],
    7: [(0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (3, 0), (3, 1)],
}


def _paint(g, top, left, cells):
    for r, c in cells:
        g[top + r][left + c] = 3


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]



def _components_color(grid, color, *, c_min=0, c_max=None):
    h, w = len(grid), len(grid[0])
    if c_max is None:
        c_max = w - 1
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(c_min, c_max + 1):
            if (sr, sc) in seen or grid[sr][sc] != color:
                continue
            comp = []
            stack = [(sr, sc)]
            seen.add((sr, sc))
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and c_min <= nc <= c_max and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def _choose_sep_col(grid):
    h, w = len(grid), len(grid[0])
    mid = w // 2
    cands = []
    for c in range(w):
        if any(grid[r][c] != 0 for r in range(h)):
            continue
        left = any(grid[r][cc] != 0 for r in range(h) for cc in range(c))
        right = any(grid[r][cc] != 0 for r in range(h) for cc in range(c + 1, w))
        if left and right:
            cands.append(c)
    if not cands:
        return None
    return sorted(cands, key=lambda c: (abs(c - mid), c))[0]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    sep = _choose_sep_col(grid)
    if sep is None:
        return ["no all-zero separator column with content on both sides"]
    k = sum(grid[r][c] == 1 for r in range(h) for c in range(sep))
    if not (3 <= k <= 7):
        errs.append(f"left marker count {k} outside expected 3..7")
    comps = _components_color(grid, 3, c_min=sep + 1, c_max=w - 1)
    sizes = [len(c) for c in comps]
    if sizes.count(k) != 1:
        errs.append(f"expected exactly one right-panel color-3 object of size {k}, saw sizes {sizes}")
    if any(grid[r][sep] != 0 for r in range(h)):
        errs.append("separator column is not empty")
    return errs

def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12); w = ctx.draw_int("grid_w", 12, 14)
        k = ctx.draw_int("marker_count", 3, 4); n_dist = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18); w = ctx.draw_int("grid_w", 16, 20)
        k = ctx.draw_int("marker_count", 5, 7); n_dist = ctx.draw_int("n_dist", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 14, 18)
        k = ctx.draw_int("marker_count", 4, 6); n_dist = ctx.draw_int("n_dist", 1, 2)

    # The rule does not use our declared separator; it chooses the all-zero
    # column closest to mid. Put the separator exactly at mid so sparse empty
    # columns elsewhere cannot steal the role and make the target disappear.
    sep = w // 2

    for _attempt in range(80):
        g = full_grid(h, w, 0)

        # LEFT panel: exactly k color-1 marker cells (the rule counts them).
        left_cells = [(r, c) for r in range(h) for c in range(sep)]
        for r, c in rng.sample(left_cells, min(k, len(left_cells))):
            g[r][c] = 1

        # RIGHT panel: one color-3 target of size k + distractors of OTHER
        # sizes, all separated so they are distinct components.
        used = set()

        def place_right(size):
            poly = _rand_poly(rng, size)
            ph = max(r for r, _ in poly) + 1; pw = max(c for _, c in poly) + 1
            if pw > w - sep - 1 or ph > h:
                return False
            for _ in range(160):
                r0 = rng.randint(0, h - ph); c0 = rng.randint(sep + 1, w - pw)
                cells = [(r0 + dr, c0 + dc) for dr, dc in poly]
                halo = {(r + dr, c + dc) for (r, c) in cells
                        for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
                if halo & used:
                    continue
                for r, c in cells:
                    g[r][c] = 3
                used.update(halo)
                return True
            return False

        if not place_right(k):
            continue
        dsizes = [s for s in range(2, k + 5) if s != k]
        rng.shuffle(dsizes)
        for s in dsizes[:n_dist]:
            place_right(s)
        if not self_check(g, difficulty=difficulty):
            return g

    raise ValueError("could not realize a unique matching-size right-panel object")


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    if name == "no_markers":
        # right-panel blobs without left-panel markers → no count to select with
        _paint(g, 2, 6, _SHAPES[4])
        _paint(g, 8, 9, _SHAPES[3])
        return g
    if name == "no_size_match":
        # k=5 markers but no right-panel object has size 5
        for r in [1, 3, 5, 7, 9]: g[r][1] = 1  # k=5
        _paint(g, 2, 6, _SHAPES[3])
        _paint(g, 8, 9, _SHAPES[7])
        return g
    if name == "multiple_size_match":
        # 2 right-panel objects share size k → ambiguous winner
        for r in [1, 3, 5, 7]: g[r][1] = 1  # k=4
        _paint(g, 2, 6, _SHAPES[4])
        _paint(g, 8, 9, _SHAPES[4])  # also size 4
        return g
    return g
