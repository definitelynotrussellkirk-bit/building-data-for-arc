"""Generator for arc_additional_puzzle_bank_volume13:E86 — line endpoints recolor red.

Rule: endpoints of straight green lines (length ≥3) are recolored red.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_lines,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_lines, length_2, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "22ee9e5c3a9a"
VERSION = "2.1.0"
TASK_ID = "22ee9e5c3a9a"
SUMMARY = (
    "0-bg grid (h, w~8-13) with 2-5 STRAIGHT "
    "COLOR-3 (green) LINES, each of length "
    "3-6 cells, all HORIZONTAL (each on its "
    "own row) or all VERTICAL (each in its "
    "own column) — generator picks "
    "orientation per sample. Lines are placed "
    "on distinct rows/cols with no row/col "
    "overlap (so endpoints are unambiguous). "
    "Rule: identify every GREEN CONNECTED "
    "COMPONENT that is a STRAIGHT LINE of "
    "length ≥3 (horizontal or vertical). For "
    "each such line, find its TWO ENDPOINTS "
    "(the two cells at the ends — col c0 and "
    "col c2 for horizontal, row r0 and row "
    "r2 for vertical). RECOLOR those two "
    "endpoint cells to COLOR 2 (red). The "
    "interior cells of the line stay green. "
    "Net: each green straight line gets its "
    "two ends repainted red; interior stays "
    "green."
)

INVARIANTS = [
    "background is 0",
    "target green components are straight horizontal or vertical lines of length at least 3",
    "line components are separated so endpoints are unambiguous",
    "optional non-line green fragments are not targets",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_lines", "length_2", "single_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_lines":        {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1 (green)", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "axis_aligned_lines",
                       "valid": "axis_aligned_lines"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_lines = ctx.draw_int("n_lines", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        n_lines = ctx.draw_int("n_lines", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
        n_lines = ctx.draw_int("n_lines", 2, 5)
    rng = ctx.draw_rng("placement")
    horizontal = rng.choice([False, True])
    g = full_grid(h, w, 0)
    made = 0
    for _ in range(1200):
        if made >= n_lines:
            break
        if horizontal:
            length = rng.randint(3, min(6, w))
            r = rng.randrange(h)
            c = rng.randint(0, w - length)
            cells = [(r, c + dc) for dc in range(length)]
        else:
            length = rng.randint(3, min(6, h))
            r = rng.randint(0, h - length)
            c = rng.randrange(w)
            cells = [(r + dr, c) for dr in range(length)]
        if not _segment_free(g, cells):
            continue
        for rr, cc in cells:
            g[rr][cc] = 3
        made += 1
    if made >= n_lines:
        return g
    return _construct_lines(h, w, n_lines, horizontal)


def _segment_free(g, cells):
    h, w = len(g), len(g[0]) if g else 0
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w):
            return False
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if g[rr][cc] != 0:
                    return False
    return True


def _construct_lines(h, w, n_lines, horizontal):
    g = full_grid(h, w, 0)
    if horizontal:
        rows = list(range(0, h, 2))
        length = min(4, w)
        starts = [0, max(0, w - length)]
        for i in range(min(n_lines, len(rows))):
            r = rows[i]
            c0 = starts[i % len(starts)]
            for dc in range(length):
                g[r][c0 + dc] = 3
    else:
        cols = list(range(0, w, 2))
        length = min(4, h)
        starts = [0, max(0, h - length)]
        for i in range(min(n_lines, len(cols))):
            c = cols[i]
            r0 = starts[i % len(starts)]
            for dr in range(length):
                g[r0 + dr][c] = 3
    return g


def _green_components(grid):
    h, w = len(grid), len(grid[0]) if grid else 0
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 3 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 3 and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append(cells)
    return out


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    comps = _green_components(grid)
    lo = 2 if difficulty != "hard" else 5
    if len(comps) < lo:
        msgs.append(f"expected at least {lo} separated green lines, got {len(comps)}")
    for cells in comps:
        rs = {r for r, _ in cells}; cs = {c for _, c in cells}
        if len(cells) < 3 or not (len(rs) == 1 or len(cs) == 1):
            msgs.append("green component is not a straight line of length >=3")
    return msgs


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_lines":
        # Empty grid — no green line, no endpoints to recolor.
        return g
    if name == "length_2":
        # Length-2 green segments — too short for the rule's length-3+
        # filter, no endpoints distinguishable from interior.
        for dc in range(2):
            g[2][2 + dc] = 3
        for dc in range(2):
            g[5][6 + dc] = 3
        return g
    if name == "single_cell":
        # Length-1 segments — even shorter, no line at all.
        g[2][2] = 3; g[5][7] = 3; g[8][3] = 3
        return g
    return g
