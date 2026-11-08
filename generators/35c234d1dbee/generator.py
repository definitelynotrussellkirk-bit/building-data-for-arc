"""Generator for 35c234d1dbee — mark centres of isolated (no-rotation) template matches.

Rule (verified from canonical Racket): split on full color-9 columns into a
TEMPLATE panel (first) and a BOARD panel (second). Find every place the template
occurs on the board in its ORIGINAL orientation only (mode 0), where the match
is BORDER-CLEAR (its 1-cell halo holds no other non-zero cells). The output is a
board-sized grid with color-8 at the centre of each such match.

The previous body was the generic "6 panels, find the matching pair" template,
whose sparse random motifs never matched, so the rule found 0 matches and
returned a blank board (rule_smoke fired=0, distinct_out=2 -- a no-op). This
2.2.0 rewrite CONSTRUCTS valid inputs: a template in panel 1, and a board with
several IDENTITY copies of it, each separated by >=1 background cell (so they are
border-clear), giving varying match centres.

Axes: template shape/colour, board size, copy count.
Degenerates: one_copy, dense, large_template.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "35c234d1dbee"
VERSION = "2.2.0"  # REWRITE: isolated template-match centres (was find-pair template; rule no-op, fired=0 distinct=2)
TASK_ID = "35c234d1dbee"

SUMMARY = (
    "Panel 1 is a template shape; panel 2 a board with several separated "
    "identity copies of it (color-9 column between). Rule: mark color-8 at the "
    "centre of every border-clear template match (no rotation). Template, "
    "colour, board size and copy count vary."
)

INVARIANTS = [
    "a full color-9 column separates the template panel from the board panel",
    "the board holds >=1 copy of the template in its original orientation",
    "copies are separated by >=1 background cell (border-clear)",
]

DEGENERATE_TEXTURES = ("one_copy", "dense", "large_template")
HELPFUL_TEXTURES = ("varied", "wide", "tall")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "board_w":    {"type": "int", "default": "rng 9..14", "valid": "7..20"},
    "shape_size": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "n_inst":     {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "texture":    {"type": "str", "default": "rng helpful",
                   "valid": "varied|wide|tall|one_copy|dense|large_template"},
}


def _walk(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}; tries = 0
    while len(cells) < k and tries < 40:
        tries += 1
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nc = (r + dr, c + dc)
        if nc not in seen:
            cells.append(nc); seen.add(nc)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _dims(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _build(rng, h, p1w, bw, k_shape, n_inst):
    W = p1w + 1 + bw
    g = full_grid(h, W, 0)
    for r in range(h):
        g[r][p1w] = 9
    shape = _walk(rng, k_shape)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7])      # non-0/8/9
    sh, sw = _dims(shape)
    if h - sh >= 0 and p1w - sw >= 0:
        tr = rng.randint(0, h - sh); tc = rng.randint(0, p1w - sw)
        for (dr, dc) in shape:
            g[tr + dr][tc + dc] = color
    placed = set()
    made = 0
    for _ in range(n_inst):
        for _ in range(30):
            br = rng.randint(0, h - sh)
            bc = rng.randint(p1w + 1, W - sw)
            cells = {(br + dr, bc + dc) for dr, dc in shape}
            halo = {(r + a, c + b) for (r, c) in cells for a in (-1, 0, 1) for b in (-1, 0, 1)}
            if halo & placed:
                continue
            for (r, c) in cells:
                g[r][c] = color
            placed |= halo
            made += 1
            break
    if made == 0:
        for (dr, dc) in shape:
            if dr < h and p1w + 1 + dc < W:
                g[dr][p1w + 1 + dc] = color
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        h_lo, h_hi, bw_lo, bw_hi, k_lo, k_hi, n_lo, n_hi = 7, 9, 8, 11, 2, 3, 2, 3
    elif difficulty == "hard":
        h_lo, h_hi, bw_lo, bw_hi, k_lo, k_hi, n_lo, n_hi = 10, 16, 12, 20, 3, 5, 3, 5
    else:
        h_lo, h_hi, bw_lo, bw_hi, k_lo, k_hi, n_lo, n_hi = 8, 12, 9, 14, 2, 4, 2, 4

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    bw = ctx.draw_int("board_w", bw_lo, bw_hi)
    k = ctx.draw_int("shape_size", k_lo, k_hi)
    n = ctx.draw_int("n_inst", n_lo, n_hi)
    return _build(rng, h, 5, bw, k, n)


def _draw_from_degenerate(name, rng):
    if name == "one_copy":
        return _build(rng, 9, 5, 10, 3, 1)
    if name == "large_template":
        return _build(rng, 12, 6, 14, 5, 2)
    return _build(rng, 14, 5, 16, 3, 5)            # dense

def _sc_norm(cells):
    cells = list(cells)
    if not cells: return ()
    r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))

def _sc_components(grid):
    h, w = len(grid), len(grid[0]); seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0: continue
            col = grid[r][c]; stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == col:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((col, cells))
    return out

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    h, w = len(grid), len(grid[0])
    divs = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(divs) != 1: return [f"expected one separator, got {len(divs)}"]
    sep = divs[0]
    left = [(r, c, grid[r][c]) for r in range(h) for c in range(sep) if grid[r][c] not in (0, 9)]
    if not left: return ["missing template"]
    pat = _sc_norm((r, c) for r, c, _ in left); color = left[0][2]
    board = [[grid[r][c] if c > sep else 0 for c in range(w)] for r in range(h)]
    matches = 0
    for comp_color, cells in _sc_components(board):
        if comp_color == color and _sc_norm((r, c - sep - 1) for r, c in cells) == pat:
            matches += 1
    if matches < 1: return ["board has no identity copy of template"]
    return []
