"""Generator for arc_additional_puzzle_bank_volume12:M84.

Rule: arrows (1=up, 2=right, 3=down, 4=left) shoot rays in their
direction, painting empty (0) cells COLOR 7 until the ray hits a 5-wall
or the grid edge. Arrows and walls stay.

Combinatorial axes: grid size, the arrows (positions + directions), and
the walls (positions / orientations).
Degenerates: no_arrows, arrow_against_wall, no_walls.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ce1f031345df"
VERSION = "2.0.1"  # diversity: N random arrows + walls + grid (was fixed full-col wall + 3 arrows, ~9)
TASK_ID = "ce1f031345df"
SUMMARY = (
    "0-bg grid (size varies) with 2-5 ARROWS (colors 1/2/3/4 = "
    "up/right/down/left) at random positions, plus 1-4 COLOR-5 (gray) "
    "WALL segments. Rule: each arrow shoots a ray in its direction, "
    "painting empty cells COLOR 7 (orange) until it hits a 5-wall or the "
    "grid edge (rays pass through other arrows). The grid size, the "
    "arrows' positions/directions and the walls all vary freely (was a "
    "fixed full-column wall + 3 fixed arrows, ~9 distinct)."
)

INVARIANTS = [
    "2-5 arrows of colors 1/2/3/4, each with empty space ahead to paint",
    "1-4 color-5 wall segments; at least one ray reaches a wall or edge",
    "arrows and walls are preserved; only 0-cells on rays become 7",
]

PALETTE_KINDS = ("default", "vertical_walls", "horizontal_walls", "few_walls")
DEGENERATE_TEXTURES = ("no_arrows", "arrow_against_wall", "no_walls")
HELPFUL_TEXTURES = PALETTE_KINDS

_DIRS = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|vertical_walls|horizontal_walls|few_walls"},
    "num_arrows":     {"type": "int", "default": "varies", "valid": "2..5"},
    "num_walls":      {"type": "int", "default": "varies", "valid": "1..4"},
    "wall_orientation": {"type": "str", "default": "varied", "valid": "varied"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|vertical_walls|horizontal_walls|few_walls|"
                                "no_arrows|arrow_against_wall|no_walls"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; arrow cells are 1-4; wall cells are 5; no other values."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
        return errs
    allowed = {0, 1, 2, 3, 4, 5}
    bad = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
           if grid[r][c] not in allowed]
    if bad:
        errs.append(f"unexpected cell values (expected 0/1-4 arrows/5 walls): {bad[:3]}")
    arrows = [grid[r][c] for r in range(h) for c in range(w) if 1 <= grid[r][c] <= 4]
    if not arrows and sum(v != 0 for row in grid for v in row) > 0:
        return errs  # degenerate no_arrows — allow
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nar, nwr = (9, 11), (11, 13), (2, 3), (1, 2)
    elif difficulty == "hard":
        hr, wr, nar, nwr = (12, 16), (13, 18), (4, 5), (2, 4)
    else:
        hr, wr, nar, nwr = (10, 14), (12, 16), (3, 4), (2, 3)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)

        # walls: short vertical/horizontal segments of 5
        for _ in range(rng.randint(*nwr)):
            for _t in range(20):
                vert = rng.random() < 0.5
                ln = rng.randint(2, 4)
                if vert:
                    if ln > h:
                        continue
                    r0 = rng.randint(0, h - ln); c0 = rng.randint(0, w - 1)
                    seg = [(r0 + i, c0) for i in range(ln)]
                else:
                    if ln > w:
                        continue
                    r0 = rng.randint(0, h - 1); c0 = rng.randint(0, w - ln)
                    seg = [(r0, c0 + i) for i in range(ln)]
                if all(g[r][c] == 0 for r, c in seg):
                    for r, c in seg:
                        g[r][c] = 5
                    break

        # arrows: random pos + dir, with >=1 empty cell ahead before a wall/edge
        n_arrows = rng.randint(*nar)
        placed = 0; painters = 0
        for _ in range(n_arrows):
            for _t in range(30):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0:
                    continue
                d = rng.randint(1, 4); dr, dc = _DIRS[d]
                nr, nc = r + dr, c + dc
                if not (0 <= nr < h and 0 <= nc < w):
                    continue          # points straight off the grid
                g[r][c] = d
                # does it paint at least one cell? (next cell empty)
                if g[nr][nc] == 0:
                    painters += 1
                placed += 1
                break
        if placed >= 2 and painters >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_arrows":
        for r in range(h):
            g[r][5] = 5
        return g
    if name == "arrow_against_wall":
        for r in range(h):
            g[r][5] = 5
        g[3][4] = 2
        g[6][6] = 4
        return g
    if name == "no_walls":
        g[1][3] = 3
        g[4][10] = 4
        g[8][1] = 1
        return g
    return g
