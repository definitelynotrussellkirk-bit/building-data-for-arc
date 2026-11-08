"""Generator for arc_puzzle_bank_fifteenth21:H101 -- rotation match + label.

Rule: the grid splits into FIVE square panels [shape1, label1, shape2, label2,
query]. The query's shape matches a rotation of shape1 OR shape2. Output: the
query panel recolored to the matching shape's label color (or [[0]] if neither
matches).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "78d1777bede2"
VERSION = "2.1.1"  # shape-locked in/out: panel size n fixed per difficulty (n=5 medium) -> output always 5x5. Rule reads n = rows g (panel size), so n is variable; output = query panel (n x n). Vary n in 3..5 (width 5n+4 = 19/24/29 <= 30) -> input AND output size vary.
TASK_ID = "78d1777bede2"

SUMMARY = (
    "Grid split into FIVE n x n panels (n=4 or 5) by 1-col gaps: panel0 = "
    "SHAPE1, panel1 = a single LABEL1 cell, panel2 = SHAPE2, panel3 = LABEL2 "
    "cell, panel4 = QUERY shape. The query equals a rotation (id/90/180/270) "
    "of exactly one of shape1/shape2. Rule: output the query panel recolored "
    "to the matching shape's label color. Shape colors are distractors -- only "
    "the shape (under rotation) and the label colors matter."
)

INVARIANTS = [
    "five n x n panels separated by single columns (width 5n+4 <= 29)",
    "panel0/panel2 are distinct shapes (not rotations of each other)",
    "panel1/panel3 are single label cells in distinct colors",
    "panel4 (query) equals a rotation of exactly one of panel0/panel2",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_match", "both_match", "single_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_n":        {"type": "int", "default": "4 or 5", "valid": "4|5"},
    "shape_size":     {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "match_index":    {"type": "int", "default": "rng 1|2", "valid": "1|2"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "3..7"},
    "position_bias":  {"type": "str", "default": "five_square_panels",
                       "valid": "five_square_panels"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_match|both_match|single_panel"},
}


def _norm(cells):
    r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rot_cw(cells):
    mr = max(r for r, _ in cells)
    return _norm([(c, mr - r) for r, c in cells])


def _rotations(cells):
    res = set(); cur = _norm(cells)
    for _ in range(4):
        res.add(cur); cur = _rot_cw(cur)
    return res


def _poly(rng, size, n):
    """Connected polyomino of `size` cells whose bbox fits n x n (normalized)."""
    for _ in range(60):
        cells = [(0, 0)]; seen = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nxt = (r + dr, c + dc)
            if nxt not in seen:
                cells.append(nxt); seen.add(nxt)
        norm = _norm(cells)
        if max(r for r, _ in norm) < n and max(c for _, c in norm) < n:
            return list(norm)
    return [(0, 0)]


def _place_shape(g, idx, n, cells, color, rng):
    left = idx * (n + 1)
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    r0 = rng.randint(0, n - sh); c0 = rng.randint(0, n - sw)
    for (r, c) in cells:
        g[r0 + r][left + c0 + c] = color


def _place_label(g, idx, n, color, rng):
    left = idx * (n + 1)
    g[rng.randint(0, n - 1)][left + rng.randint(0, n - 1)] = color


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid width = 5n+4 for some n in {3,4,5}; ≥4 single-col gaps (zeros) separating panels."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Width should be 5*n+4 for n in {3,4,5} → w in {19,24,29}
    valid_widths = {5*n+4 for n in range(3, 6)}
    if w not in valid_widths:
        errs.append(f"grid width {w} not in {sorted(valid_widths)} (5n+4 for n=3..5)")
    # There should be full-height zero columns (separators)
    sep_cols = [c for c in range(w) if all(grid[r][c] == 0 for r in range(h))]
    if len(sep_cols) < 4:
        errs.append(f"only {len(sep_cols)} full-zero separator column(s); expected 4")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        n = ctx.draw_int("panel_n", 3, 4)
    elif difficulty == "hard":
        n = ctx.draw_int("panel_n", 4, 5)
    else:
        n = ctx.draw_int("panel_n", 3, 5)     # width 5n+4 -> 19/24/29 (<=30)
    smax = min(n + 1, 6)

    for _attempt in range(60):
        s1 = _poly(rng, rng.randint(3, smax), n)
        rot1 = _rotations(s1)
        s2 = _poly(rng, rng.randint(3, smax), n)
        if _norm(s2) in rot1:                 # shapes must be in different rotation classes
            continue
        rot2 = _rotations(s2)
        which = int(overrides["match_index"]) if "match_index" in overrides \
            else rng.choice([1, 2])
        target_rots = rot1 if which == 1 else rot2
        q = list(rng.choice(sorted(target_rots)))
        q_n = _norm(q)
        # query must match ONLY the intended shape
        if (which == 1 and q_n in rot2) or (which == 2 and q_n in rot1):
            continue

        W = 5 * n + 4
        g = full_grid(n, W, 0)
        shape_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
        label1 = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        label2 = rng.choice([c for c in range(1, 10) if c != label1])
        _place_shape(g, 0, n, s1, shape_colors[0], rng)
        _place_label(g, 1, n, label1, rng)
        _place_shape(g, 2, n, s2, shape_colors[1], rng)
        _place_label(g, 3, n, label2, rng)
        _place_shape(g, 4, n, q, shape_colors[2], rng)
        return g
    return _draw_from_degenerate("single_panel", rng)   # rare fallback (valid)


def _draw_from_degenerate(name, rng):
    n = 5
    W = 5 * n + 4
    g = full_grid(n, W, 0)
    s1 = [(0, 0), (0, 1), (1, 0)]
    s2 = [(0, 0), (1, 0), (1, 1)]
    _place_shape(g, 0, n, s1, 1, rng)
    g[1][n + 1 + 1] = 3                        # label1
    _place_shape(g, 2, n, s2, 2, rng)
    g[1][3 * (n + 1) + 1] = 4                  # label2
    if name == "no_match":
        _place_shape(g, 4, n, [(0, 0), (0, 1), (0, 2)], 5, rng)  # query matches neither
    elif name == "single_panel":
        pass                                  # query panel empty
    else:  # both_match -> query = s1 (matches panel0; s2 different class)
        _place_shape(g, 4, n, s1, 5, rng)
    return g
