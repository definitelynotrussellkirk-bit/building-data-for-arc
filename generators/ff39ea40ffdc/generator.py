"""Generator for arc_additional_puzzle_bank_volume4:H22.

Rule: corner controls select a size-ranked colored object and transform
its tight crop.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_objects,
palette_size, position_bias, n_distinct_colors, transform_kind, texture.
Degenerates: no_size_control, no_transform_control, equal_sizes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "ff39ea40ffdc"
VERSION = "3.0.0"
TASK_ID = "ff39ea40ffdc"
SUMMARY = (
    "0-bg grid (size varies) with: (a) TOP-LEFT CONTROL "
    "at (0, 0) — a SIZE RANK in {1=smallest, 2=middle, "
    "3=largest}; (b) TOP-RIGHT CONTROL at (0, w-1) — a "
    "TRANSFORM in {4=identity, 5=mirror, 6=rotate-CW}; "
    "(c) THREE candidate objects, each a RANDOM "
    "polyomino of a DISTINCT size, in a shuffled "
    "size->color assignment over {7, 8, 9}, scattered at "
    "random positions. Rule: read the rank, pick that "
    "size-ranked 7/8/9 object, crop it tight, apply the "
    "transform from the top-right control, and OUTPUT "
    "the transformed crop in the object's color (other "
    "objects and controls discarded)."
)

INVARIANTS = [
    "top-left control selects smallest, middle, or largest object",
    "top-right control selects identity, mirror, or rotation",
    "candidate objects use colors 7, 8, and 9",
    "candidate sizes are distinct",
]

PALETTE_KINDS = ("default", "rank_smallest", "rank_middle", "rank_largest")
DEGENERATE_TEXTURES = ("no_size_control", "no_transform_control", "equal_sizes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..15", "valid": "9..24"},
    "grid_w":         {"type": "int", "default": "rng 12..17", "valid": "10..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objects":      {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5"},
    "position_bias":  {"type": "str", "default": "corners_plus_objects",
                       "valid": "corners_plus_objects"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5"},
    "transform_kind": {"type": "str", "default": "rng", "valid": "rng"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_poly(rng, size):
    """Random 4-connected polyomino of `size` cells, normalized to origin."""
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    cells = [(0, 0)]
    guard = 0
    while len(cells) < size and guard < 200:
        guard += 1
        gr, gc = rng.choice(cells)
        for dr, dc in rng.sample(dirs, 4):
            p = (gr + dr, gc + dc)
            if p not in cells:
                cells.append(p)
                break
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 15)
        smax = 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20)
        w = ctx.draw_int("grid_w", 16, 24)
        smax = 8
    else:
        h = ctx.draw_int("grid_h", 12, 17)
        w = ctx.draw_int("grid_w", 13, 20)
        smax = 7
    rng = ctx.draw_rng("layout")

    # THREE candidate objects: random polyominoes of DISTINCT sizes, in a SHUFFLED
    # size->color assignment over {7,8,9} (so the rank-selected output color varies).
    # Random shapes are the whole point: the rule just filters 7/8/9 objects, sorts
    # by size, picks by the (0,0) rank, transforms by the (0,w-1) code -> so random
    # shapes/sizes/colors/positions multiply the output space (was a fixed 3-shape bank).
    sizes = sorted(rng.sample(range(2, smax + 1), 3))
    cand_colors = [7, 8, 9]; rng.shuffle(cand_colors)
    shapes = [_rand_poly(rng, s) for s in sizes]
    dims = [(max(r for r, _ in sh) + 1, max(c for _, c in sh) + 1) for sh in shapes]

    # Size the grid so a row-pack of all three always fits (guaranteed placement).
    need_w = sum(d[1] for d in dims) + 4
    need_h = max(d[0] for d in dims) + 3
    w = min(30, max(w, need_w))
    h = min(30, max(h, need_h))

    g = full_grid(h, w, 0)
    g[0][0] = rng.choice([1, 2, 3])          # rank control
    g[0][w - 1] = rng.choice([4, 5, 6])      # transform control

    occ = [[False] * w for _ in range(h)]
    occ[0][0] = occ[0][w - 1] = True

    def place(shape, sh, sw, color):
        for _t in range(120):
            top = rng.randint(1, h - sh)     # rows >=1 keep the control row clear
            left = rng.randint(0, w - sw)
            cells = [(top + dr, left + dc) for dr, dc in shape]
            guard = [(r, c) for rr, cc in cells
                     for r in range(rr - 1, rr + 2) for c in range(cc - 1, cc + 2)]
            if any(0 <= r < h and 0 <= c < w and occ[r][c] for r, c in guard):
                continue
            for r, c in cells:
                g[r][c] = color
            for r, c in guard:
                if 0 <= r < h and 0 <= c < w:
                    occ[r][c] = True
            return True
        return False

    if not all(place(sh, d[0], d[1], col)
               for sh, d, col in zip(shapes, dims, cand_colors)):
        # deterministic row-pack fallback (fits by the grid sizing above)
        g = full_grid(h, w, 0)
        g[0][0] = rng.choice([1, 2, 3]); g[0][w - 1] = rng.choice([4, 5, 6])
        left = 1
        for sh, d, col in zip(shapes, dims, cand_colors):
            for dr, dc in sh:
                g[2 + dr][left + dc] = col
            left += d[1] + 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "no_size_control":
        # transform control + objects but no size-ranking control → which obj undefined
        g[0][w - 1] = 4
        paint_at(g, 2, 1, [(0, 0), (1, 0)], 8)
        paint_at(g, 2, w - 5, [(0, 0), (0, 1), (1, 1)], 7)
        paint_at(g, h - 5, w // 2, [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)], 9)
        return g
    if name == "no_transform_control":
        # size control + objects but no transform control → action undefined
        g[0][0] = 2
        paint_at(g, 2, 1, [(0, 0), (1, 0)], 8)
        paint_at(g, 2, w - 5, [(0, 0), (0, 1), (1, 1)], 7)
        paint_at(g, h - 5, w // 2, [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)], 9)
        return g
    if name == "equal_sizes":
        # all candidate objects have the same size → ranking is ambiguous
        g[0][0] = 1
        g[0][w - 1] = 5
        for top, left, color in [(2, 1, 8), (2, w - 5, 7), (h - 5, w // 2, 9)]:
            paint_at(g, top, left, [(0, 0), (1, 0)], color)
        return g
    return g

def _components_by_color(grid, colors):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] not in colors or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 1 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if grid[0][0] not in (1, 2, 3):
        errs.append(f"bad size-rank control {grid[0][0]!r}")
    if grid[0][w - 1] not in (4, 5, 6):
        errs.append(f"bad transform control {grid[0][w - 1]!r}")
    if any(v != 0 for v in grid[0][1:w - 1]):
        errs.append("control row should be empty except for the two corner controls")
    comps = _components_by_color(grid, {7, 8, 9})
    by_color = {c: [] for c in (7, 8, 9)}
    for color, cells in comps:
        by_color[color].append(cells)
    for color, groups in by_color.items():
        if len(groups) != 1:
            errs.append(f"candidate color {color} should have exactly one object, got {len(groups)}")
    sizes = [len(groups[0]) for groups in by_color.values() if len(groups) == 1]
    if len(sizes) == 3 and len(set(sizes)) != 3:
        errs.append(f"candidate object sizes should be distinct, got {sizes}")
    return errs

