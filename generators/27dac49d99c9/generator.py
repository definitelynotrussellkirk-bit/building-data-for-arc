"""Generator for arc_puzzle_bank_21_set17_bundle:hard_p07 — BFS through multi-checkpoint path.

Rule: 5-walled grid; BFS from start (2) to goal (3) through checkpoints
(4 and 6) in order. Output paints the full path color 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, n_iw, texture.
Degenerates: no_start, no_goal, no_checkpoints.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "27dac49d99c9"
VERSION = "1.1.0"
TASK_ID = "27dac49d99c9"

SUMMARY = "5-walled grid + start (2), goal (3), checkpoints (4 and 6), and interior 5-walls."

INVARIANTS = [
    "background is 0",
    "outer border is color-5 walls",
    "exactly one each of color-2 start, color-3 goal, color-4 checkpoint, color-6 checkpoint, all interior",
    "some interior color-5 wall cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_start", "no_goal", "no_checkpoints")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_iw":           {"type": "int", "default": "rng 2..4", "valid": "0..8"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5..5"},
    "position_bias":  {"type": "str", "default": "walled_with_4_markers",
                       "valid": "walled_with_4_markers"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
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
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        n_iw = ctx.draw_int("n_iw", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 11, 14)
        n_iw = ctx.draw_int("n_iw", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
        n_iw = ctx.draw_int("n_iw", 2, 4)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    for c in range(w): g[0][c] = 5; g[h - 1][c] = 5
    for r in range(h): g[r][0] = 5; g[r][w - 1] = 5

    def place(value, exclude=None):
        for _ in range(80):
            r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
            if g[r][c] != 0: continue
            if exclude and any(abs(r - er) + abs(c - ec) < 2 for er, ec in exclude): continue
            g[r][c] = value
            return (r, c)
        return None

    placed = []
    for v in (2, 3, 4, 6):
        p = place(v, exclude=placed)
        if p:
            placed.append(p)
    for _ in range(n_iw):
        for _t in range(40):
            r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
            if g[r][c] != 0: continue
            if any(abs(r - er) + abs(c - ec) < 2 for er, ec in placed): continue
            g[r][c] = 5
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    for c in range(w): g[0][c] = 5; g[h - 1][c] = 5
    for r in range(h): g[r][0] = 5; g[r][w - 1] = 5
    if name == "no_start":
        # Goal + checkpoints but no start — BFS has no source node.
        g[2][3] = 4; g[5][7] = 6; g[7][3] = 3
        return g
    if name == "no_goal":
        # Start + checkpoints but no goal — BFS has no terminal.
        g[2][3] = 2; g[4][6] = 4; g[6][7] = 6
        return g
    if name == "no_checkpoints":
        # Start + goal but neither 4 nor 6 — rule's "via checkpoints"
        # routing has no waypoints to enforce.
        g[2][3] = 2; g[6][7] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    h, w = len(grid), len(grid[0])
    if any(grid[0][c] != 5 or grid[h - 1][c] != 5 for c in range(w)) or \
       any(grid[r][0] != 5 or grid[r][w - 1] != 5 for r in range(h)):
        errors.append("outer border must be all color-5 walls")
    pts = {v: [(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x == v]
           for v in (2, 3, 4, 6)}
    for value, cells in pts.items():
        if len(cells) != 1:
            errors.append(f"expected exactly one marker {value}, got {len(cells)}")
    if not any(grid[r][c] == 5 for r in range(1, h - 1) for c in range(1, w - 1)):
        errors.append("expected at least one interior color-5 wall")

    def reachable(a, b):
        q = [a]; seen = {a}
        for r, c in q:
            if (r, c) == b:
                return True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] != 5:
                    seen.add((nr, nc)); q.append((nr, nc))
        return False

    if all(len(cells) == 1 for cells in pts.values()):
        for a, b in ((2, 3), (3, 4), (4, 6)):
            if not reachable(pts[a][0], pts[b][0]):
                errors.append(f"no open path between marker {a} and marker {b}")
    return errors
