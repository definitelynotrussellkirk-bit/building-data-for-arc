"""Generator for hard_143_overlay_diagonal_visibility_counts_with_walls.

Rule: color-2 cells are diagonal emitters and color-8 cells are walls.
The canonical rule ray-casts diagonally from each emitter until blocked
and writes the wall-aware visibility/count overlay.

Combinatorial axes: grid_h/w, number of emitters, number of walls,
wall placement, and difficulty.  Degenerates keep legacy texture names
but are non-normal branch-hiding cases.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b341e96bd530"
VERSION = "2.2.0"  # color-2 emitters + color-8 walls; old motif-pack generator did not exercise the canonical rule.
TASK_ID = "b341e96bd530"

SUMMARY = (
    "0-bg grid with one or more color-2 diagonal emitters and color-8 "
    "blocking walls.  At least one emitter has an open diagonal ray so the "
    "canonical wall-aware visibility overlay fires.  Normal examples use "
    "only colors 0, 2, and 8 to avoid confusing motifs with emitters/walls."
)

INVARIANTS = [
    "background is 0",
    "color-2 cells are diagonal emitters",
    "color-8 cells are blocking walls",
    "at least one emitter has an open diagonal ray step",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 7..14", "valid": "7..14"},
    "grid_w":            {"type": "int", "default": "rng 9..16", "valid": "9..16"},
    "n_emitters":        {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "n_walls":           {"type": "int", "default": "rng 3..8", "valid": "2..10"},
    "palette_size":      {"type": "int", "default": "3", "valid": "3"},
    "position_bias":     {"type": "str", "default": "emitters_plus_walls",
                          "valid": "emitters_plus_walls"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 9, 11)
        n_emitters = ctx.draw_int("n_emitters", 1, 2)
        n_walls = ctx.draw_int("n_walls", 2, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 14, 16)
        n_emitters = ctx.draw_int("n_emitters", 2, 4)
        n_walls = ctx.draw_int("n_walls", 6, 10)
    else:
        h = ctx.draw_int("grid_h", 7, 14)
        w = ctx.draw_int("grid_w", 9, 16)
        n_emitters = ctx.draw_int("n_emitters", 1, 3)
        n_walls = ctx.draw_int("n_walls", 3, 8)
    rng = ctx.draw_rng("layout")

    for _layout_attempt in range(80):
        g = full_grid(h, w, 0)
        cells = [(r, c) for r in range(h) for c in range(w)]
        rng.shuffle(cells)
        emitters = cells[:n_emitters]
        for r, c in emitters:
            g[r][c] = 2
        # Color 8 is the only blocking wall in the canonical rule.  The previous
        # motif-pack generator sampled colors from 2..9, so many boards had no
        # emitter and many had accidental 8-motifs as walls.
        placed_walls = 0
        for r, c in cells[n_emitters:]:
            if placed_walls >= n_walls:
                break
            # Keep at least one diagonal step clear from every emitter so the
            # example always exercises ray propagation, not just the seed count.
            if any(abs(r - er) == 1 and abs(c - ec) == 1 for er, ec in emitters):
                continue
            g[r][c] = 8
            placed_walls += 1
        if placed_walls >= max(1, n_walls // 2) and _has_open_diagonal_ray(g):
            return g
    raise ValueError("could not realize diagonal-emitter/wall board")


def _has_open_diagonal_ray(g):
    h, w = len(g), len(g[0])
    for r, row in enumerate(g):
        for c, v in enumerate(row):
            if v != 2:
                continue
            for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 8:
                    return True
    return False


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    n_emitters = sum(v == 2 for row in grid for v in row)
    n_walls = sum(v == 8 for row in grid for v in row)
    if n_emitters < 1:
        msgs.append("expected at least one color-2 diagonal emitter")
    if n_walls < 1:
        msgs.append("expected at least one color-8 wall")
    if not _has_open_diagonal_ray(grid):
        msgs.append("expected at least one emitter with a non-wall diagonal ray step")
    stray = {v for row in grid for v in row if v not in (0, 2, 8)}
    if stray:
        msgs.append(f"normal examples should use only 0/2/8 for this rule; got stray colors {sorted(stray)}")
    return msgs

def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        return g
    if name == "single_motif":
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g
