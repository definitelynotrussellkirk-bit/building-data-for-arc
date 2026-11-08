"""Generator for arc_additional_puzzle_bank_volume4:H24.

Rule: the pivot is the first color-2 cell. Each color-1 cell is reflected
4-fold about the pivot (itself + vertical mirror + horizontal mirror +
both), painting 1 at every in-bounds reflection.

Combinatorial axes: grid size, pivot position, and the 1-cells (count +
positions in one quadrant so all reflections are distinct and in-bounds).
Degenerates: no_pivot, no_cells, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ef4af8761400"
VERSION = "2.1.0"  # connected-blob source (canonical has shapes, not scattered singles); drop dead axes
TASK_ID = "ef4af8761400"
SUMMARY = (
    "0-bg grid (size varies) with ONE color-2 (red) PIVOT (interior, "
    "clear of edges) and 1-5 color-1 (blue) cells in ONE quadrant "
    "relative to the pivot (off both pivot axes, within reflectable "
    "range). Rule: reflect each 1-cell 4-fold about the pivot (self + "
    "vertical + horizontal + both mirrors), painting 1 at every in-bounds "
    "reflection. The grid size, pivot position and the 1-cells all vary "
    "freely (was a fixed center pivot + 3 fixed cells, ~9 distinct)."
)

INVARIANTS = [
    "exactly one color-2 pivot, away from the grid edges",
    "1-5 color-1 cells in one quadrant, off both pivot axes",
    "every 4-fold reflection of every 1-cell lands in-bounds",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_pivot", "no_cells", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "blob_size":      {"type": "int", "default": "rng 2..6 (connected source)", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "2 (colors 1,2 rule-locked)", "valid": "2"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_pivot|no_cells|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, ncr = (8, 10), (8, 10), (1, 2)
    elif difficulty == "hard":
        hr, wr, ncr = (11, 16), (11, 16), (3, 5)
    else:
        hr, wr, ncr = (9, 13), (9, 13), (2, 4)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        # pivot interior with reflectable room on both sides
        pr = rng.randint(2, h - 3); pc = rng.randint(2, w - 3)
        ra = min(pr, h - 1 - pr)        # max row offset that reflects in-bounds
        ca = min(pc, w - 1 - pc)        # max col offset
        if ra < 1 or ca < 1:
            continue
        g = full_grid(h, w, 0)
        g[pr][pc] = 2
        # connected blob of offsets (a,b) with a,b >= 1 (up-left quadrant, off both
        # pivot axes so all 4 mirrors are distinct and in-bounds)
        k = min(rng.randint(*ncr), ra * ca)
        offsets = _grow_offsets(rng, ra, ca, k)
        for (a, b) in offsets:
            g[pr - a][pc - b] = 1
        return g

    return g   # fallback (rare)


def _grow_offsets(rng, ra, ca, k):
    """Connected (4-conn) set of k offsets within [1..ra] x [1..ca]."""
    cells = {(1, 1)}
    tries = 0
    while len(cells) < k and tries < 40:
        tries += 1
        a, b = rng.choice(list(cells))
        da, db = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        na, nb = a + da, b + db
        if 1 <= na <= ra and 1 <= nb <= ca:
            cells.add((na, nb))
    return list(cells)


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    if name == "no_pivot":
        g[2][2] = 1
        return g
    if name == "no_cells":
        g[4][4] = 2
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(9):
                g[r][c] = 1
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or len({len(row) for row in grid}) != 1:
        return ["grid must be a nonempty rectangle"]
    h, w = len(grid), len(grid[0])
    pivots = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    ones = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    if len(pivots) != 1:
        msgs.append(f"expected exactly one color-2 pivot, found {len(pivots)}")
        return msgs
    if not ones:
        msgs.append("expected at least one color-1 source cell")
    pr, pc = pivots[0]
    if not (1 <= pr < h - 1 and 1 <= pc < w - 1):
        msgs.append(f"pivot should be interior, got {(pr, pc)}")
    for r, c in ones:
        if r == pr or c == pc:
            msgs.append(f"source cell {(r, c)} lies on pivot row/col, hiding one reflection axis")
            break
        for rr, cc in ((r, c), (2 * pr - r, c), (r, 2 * pc - c), (2 * pr - r, 2 * pc - c)):
            if not (0 <= rr < h and 0 <= cc < w):
                msgs.append(f"reflection of {(r, c)} about {(pr, pc)} leaves grid at {(rr, cc)}")
                return msgs
    return msgs
