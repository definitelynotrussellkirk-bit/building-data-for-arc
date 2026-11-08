"""Generator for arc_puzzle_bank_21_set9_s:S9_H4.

Use area and width legends to select one object and recolor it to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, variant,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_legends, no_match, multiple_matches.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1620d15035b5"
# 2.1.0: was a fixed 10x12 grid, 3 fixed target shapes at fixed positions,
#        1 distractor (shape-locked in+out, distinct_out=3, dup-inputs 49%).
#        Now randomize grid size, target polyomino (size K, width W), its
#        position, and 1-3 distractors that fail the (size,width) match.
#        Legends K/W derived from the target. Output shape/position now varies.
VERSION = "2.1.1"
TASK_ID = "1620d15035b5"
SUMMARY = (
    "0-bg grid where: (a) row 0 has K color-1 cells (the AREA target K); "
    "(b) col 0 has W color-3 cells (the WIDTH target W); (c) 2-4 "
    "OBJECTS in non-{1, 3} colors scattered in interior cells (not in "
    "row 0 or col 0). EXACTLY ONE object has size == K AND bbox width "
    "== W. Other objects are distractors with size != K OR width != W. "
    "Rule: read K from row 0 (count of 1s), W from col 0 (count of 3s). "
    "Find the unique object with size K AND width W. Paint it in color "
    "8 on a fresh canvas; all else becomes 0."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "row 0 has K color-1 cells (1 ≤ K ≤ 8)",
    "col 0 has W color-3 cells (1 ≤ W ≤ 5)",
    "2-4 objects in non-{1, 3} colors, placed in interior cells",
    "exactly ONE object has size == K AND bbox width == W (the target)",
    "other objects fail to match (different size or different width)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legends", "no_match", "multiple_matches")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "10", "valid": "10..10"},
    "grid_w":         {"type": "int", "default": "12", "valid": "12..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "variant":        {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "legends_plus_target_distractor",
                       "valid": "legends_plus_target_distractor"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_legends|no_match|multiple_matches"},
}

_TARGETS = [
    [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
    [(0, 0), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)],
]
_DISTRACTORS = [
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (0, 3)],
    [(0, 0), (1, 0), (2, 0), (3, 0)],
]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: row 0 has color-1 area legend, col 0 has color-3 width legend."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_legends", "no_match", "multiple_matches"):
        return errs  # degenerate — skip structural check
    ones_in_row0 = [c for c in range(w) if grid[0][c] == 1]
    threes_in_col0 = [r for r in range(h) if grid[r][0] == 3]
    if not ones_in_row0:
        errs.append("row 0 has no color-1 area legend cells")
    if not threes_in_col0:
        errs.append("col 0 has no color-3 width legend cells")
    return errs


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _grow(rng, size, max_dim=5):
    """Grow a connected polyomino of `size` cells within max_dim x max_dim."""
    for _ in range(60):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        n = _norm(list(cells))
        if (max(r for r, _ in n) < max_dim) and (max(c for _, c in n) < max_dim):
            return n
    return _norm(list(cells))


def _dims(cells):
    return (max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        h, w = rng.randint(9, 11), rng.randint(11, 13)
        n_dist = rng.randint(1, 1)
    elif difficulty == "hard":
        h, w = rng.randint(12, 16), rng.randint(13, 17)
        n_dist = rng.randint(2, 3)
    else:
        h, w = rng.randint(10, 14), rng.randint(12, 16)
        n_dist = rng.randint(1, 3)

    # Target: random polyomino. K = size, W = bbox width.
    K = rng.randint(3, 6)
    target = _grow(rng, K)
    th, tw = _dims(target)
    W = tw
    # Legends must fit: K 1s in row 0 (cols 1..K) and W 3s in col 0 (rows 1..W).
    if K + 1 > w or W + 1 > h:
        # shrink and retry conservatively
        K = min(K, w - 2)
        target = _grow(rng, max(3, K))
        th, tw = _dims(target)
        W = tw

    occ = set()
    g = full_grid(h, w, 0)
    # Row-0 area legend, col-0 width legend.
    for c in range(K):
        g[0][c + 1] = 1; occ.add((0, c + 1))
    for r in range(W):
        g[r + 1][0] = 3; occ.add((r + 1, 0))

    colors = rng.sample([2, 4, 5, 6, 7, 9], min(1 + n_dist, 6))

    def _place(cells, color):
        ch, cw = _dims(cells)
        for _ in range(120):
            # interior placement: avoid row 0 and col 0 entirely
            top = rng.randint(1, h - ch)
            left = rng.randint(1, w - cw)
            ok = True
            for (r, c) in cells:
                rr, cc = top + r, left + c
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if (rr + dr, cc + dc) in occ:
                            ok = False; break
                    if not ok: break
                if not ok: break
            if not ok:
                continue
            for (r, c) in cells:
                g[top + r][left + c] = color
                occ.add((top + r, left + c))
            return True
        return False

    if not _place(target, colors[0]):
        # fall back to a guaranteed small layout
        return _draw_from_degenerate("multiple_matches", None)

    # Distractors: each must FAIL the match (size != K OR width != W).
    ci = 1
    for _ in range(n_dist):
        for _try in range(20):
            dk = rng.randint(2, 6)
            dshape = _grow(rng, dk)
            _, dw = _dims(dshape)
            if len(dshape) == K and dw == W:
                continue  # would also match -> reject
            if _place(dshape, colors[ci % len(colors)]):
                ci += 1
            break
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "no_legends":
        # objects without row-0/col-0 legends → no selection signal
        _paint(g, 3, 3, _TARGETS[0], 4)
        _paint(g, 7, 6, _DISTRACTORS[0], 6)
        return g
    if name == "no_match":
        # legends specify (area, width) but no object matches both
        for c in range(5): g[0][c + 1] = 1  # area = 5
        for r in range(3): g[r + 1][0] = 3  # width = 3
        _paint(g, 3, 3, _DISTRACTORS[0], 4)  # area 3 width 2
        _paint(g, 7, 6, _DISTRACTORS[1], 6)  # area 4 width 4
        return g
    if name == "multiple_matches":
        # 2 objects match both features → ambiguous winner
        for c in range(4): g[0][c + 1] = 1  # area = 4
        for r in range(2): g[r + 1][0] = 3  # width = 2
        _paint(g, 3, 3, [(0, 0), (1, 0), (1, 1), (2, 1)], 4)  # area 4 width 2
        _paint(g, 7, 8, [(0, 0), (1, 0), (1, 1), (2, 1)], 6)  # also matches
        return g
    return g
