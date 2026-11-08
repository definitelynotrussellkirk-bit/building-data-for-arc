"""Generator for arc_puzzle_bank_21_set17_bundle:easy_p06.

Rule: horizontal monochrome runs are reduced to their middle cell.

Combinatorial axes (8): grid_h, grid_w, palette_kind, run_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_singletons, even_length_runs, vertical_runs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "feec9520847d"
VERSION = "1.4.0"
TASK_ID = "feec9520847d"
SUMMARY = "Horizontal monochrome runs reduced to middle cell; vertical/diagonal shapes erased."

# Rivals: 'keep entire run' refuted by any demo (only middle survives).
# 'keep left end' refuted by ≥1 demo where middle differs from left end
# (length ≥3). 'reduce all objects (incl. vertical)' refuted by ≥1 demo
# where vertical runs are erased entirely. 'keep right half' refuted by
# ≥2 demos.
# 4 demos with varied run lengths + distractors cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "surviving horizontal run objects have odd length >=3",
    "horizontal runs are separated by zeros",
    "vertical/blob distractors may exist but are non-hline objects",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_singletons", "even_length_runs", "vertical_runs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "run_count":      {"type": "int", "default": "rng 3..5", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "row_runs",
                       "valid": "row_runs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
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
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 8, 11)
        run_count = ctx.draw_int("run_count", 2, 4)
        max_len = 5
        n_distractors_lo, n_distractors_hi = 0, 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 14, 18)
        run_count = ctx.draw_int("run_count", 5, 8)
        max_len = 9
        n_distractors_lo, n_distractors_hi = 2, 4
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 11, 15)
        run_count = ctx.draw_int("run_count", 3, 5)
        max_len = 7
        n_distractors_lo, n_distractors_hi = 1, 3
    colors = ctx.draw_distinct_colors("colors", n=min(9, run_count), exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    for color in colors:
        for _ in range(300):
            odd_lengths = [L for L in range(3, min(max_len, w) + 1, 2)]
            length = rng.choice(odd_lengths)
            r = rng.randrange(h)
            c = rng.randint(0, w - length)
            # Need 1-cell padding around (above, below, left, right) so
            # objects don't merge into multi-row shapes that fail hline?.
            ok = True
            for rr in range(max(0, r - 1), min(h, r + 2)):
                for cc in range(max(0, c - 1), min(w, c + length + 1)):
                    if g[rr][cc] != 0:
                        ok = False; break
                if not ok: break
            if ok:
                for cc in range(c, c + length):
                    g[r][cc] = color
                break
    # Vertical-run distractors — rule's hline? rejects them so they
    # don't survive. Vital for the "only horizontal" hypothesis.
    n_distractors = rng.randint(n_distractors_lo, n_distractors_hi)
    dist_pool = [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c not in colors]
    for _ in range(200):
        if n_distractors <= 0 or not dist_pool:
            break
        vlen = rng.randint(2, min(4, h))
        r = rng.randint(0, h - vlen)
        c = rng.randint(0, w - 1)
        ok = True
        for rr in range(max(0, r - 1), min(h, r + vlen + 1)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if g[rr][cc] != 0:
                    ok = False; break
            if not ok: break
        if ok:
            col = rng.choice(dist_pool)
            for rr in range(r, r + vlen):
                g[rr][c] = col
            n_distractors -= 1

    # BLOB distractors — multi-row non-line shapes (2x2 / L / T). The rule keeps
    # ONLY hline objects, so any 2D blob is erased too; this non-vertical non-hline
    # class makes the "horizontal-line-only" precondition more robust (was tested
    # only by vertical runs). Rule-safe distractors, isolated from everything else.
    blob_shapes = [[(0, 0), (0, 1), (1, 0), (1, 1)], [(0, 0), (1, 0), (1, 1)],
                   [(0, 0), (0, 1), (1, 1)], [(0, 0), (0, 1), (0, 2), (1, 1)]]
    n_blob = rng.randint(0, 2)
    for _ in range(150):
        if n_blob <= 0 or not dist_pool:
            break
        shape = rng.choice(blob_shapes)
        bh = max(dr for dr, _ in shape) + 1
        bw = max(dc for _, dc in shape) + 1
        if bh > h or bw > w:
            continue
        r = rng.randint(0, h - bh)
        c = rng.randint(0, w - bw)
        cells = [(r + dr, c + dc) for dr, dc in shape]
        guard = [(rr, cc) for br, bc in cells
                 for rr in range(br - 1, br + 2) for cc in range(bc - 1, bc + 2)]
        if any(0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0 for rr, cc in guard):
            continue
        col = rng.choice(dist_pool)
        for br, bc in cells:
            g[br][bc] = col
        n_blob -= 1
    return g


def _components_by_color(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                x, y = stack.pop(); cells.append((x, y))
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < h and 0 <= ny < w and (nx, ny) not in seen and grid[nx][ny] == color:
                        seen.add((nx, ny)); stack.append((nx, ny))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errs = []
    hlines = []
    for color, cells in _components_by_color(grid):
        rows = {r for r, _ in cells}
        if len(rows) == 1 and len(cells) > 1:
            hlines.append(cells)
            if len(cells) < 3 or len(cells) % 2 == 0:
                errs.append(f"horizontal survivor run must have odd length >=3, got {len(cells)}")
                break
    if len(hlines) < 2:
        errs.append(f"expected at least two horizontal teaching runs, found {len(hlines)}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 7, 11
    g = full_grid(h, w, 0)
    if name == "all_singletons":
        # length-1 runs only → "middle of a 1-cell run" is identity, rule has no effect
        g[1][2] = 4; g[3][6] = 6; g[5][1] = 3; g[5][8] = 8
        return g
    if name == "even_length_runs":
        # length-2/4 runs → no integer middle (ambiguous which cell to keep)
        for c in range(1, 3): g[1][c] = 4   # length 2
        for c in range(4, 8): g[3][c] = 6   # length 4
        for c in range(2, 6): g[5][c] = 3   # length 4
        return g
    if name == "vertical_runs":
        # vertical runs (col-aligned) → rule scans rows, sees only length-1 horizontal runs
        for r in range(1, 4): g[r][2] = 4
        for r in range(2, 6): g[r][7] = 6
        for r in range(4, 7): g[r][9] = 3
        return g
    return g
