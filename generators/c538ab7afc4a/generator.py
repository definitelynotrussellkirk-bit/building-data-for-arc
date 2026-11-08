"""Generator for arc_puzzle_bank_next21:H11 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, motifs_touching.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c538ab7afc4a"
VERSION = "2.0.0"  # wrong 'gallery pack' docstring + dup 42%: rule outputs the MOST-COMMON shape (recoloured 8); random independent motifs rarely repeated -> collapsed to largest. Now place a WINNER shape m>=2 times + distinct distractors (count 1) so the winner is unambiguous + varied.
TASK_ID = "c538ab7afc4a"

SUMMARY = "3-4 motifs in distinct colors at distinct positions."

INVARIANTS = [
    "background is 0",
    "3-4 connected motifs in distinct non-zero colors at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "motifs_touching")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_isolated_motifs",
                       "valid": "scattered_isolated_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_motifs|single_motif|motifs_touching"},
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
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 11, 13)
        m = 2; n_d = ctx.draw_int("n_distract", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 14, 20)
        m = ctx.draw_int("n_win", 2, 3); n_d = ctx.draw_int("n_distract", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 12, 16)
        m = ctx.draw_int("n_win", 2, 3); n_d = ctx.draw_int("n_distract", 1, 3)
    rng = ctx.draw_rng("layout")

    def _norm(cells):
        r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
        return sorted((r - r0, c - c0) for r, c in cells)

    for outer in range(60):
        g = full_grid(h, w, 0)
        # the rule outputs the MOST-COMMON shape (recoloured 8). Place a WINNER shape
        # m>=2 times + distinct distractors (count 1) so the winner is unambiguous.
        winner = _norm(_build_motif(rng, rng.randint(3, 7)))
        seen = {tuple(winner)}
        objs = [winner] * m
        for _ in range(n_d * 6):
            if len(objs) >= m + n_d:
                break
            d = _norm(_build_motif(rng, rng.randint(3, 6)))
            if tuple(d) not in seen:
                seen.add(tuple(d)); objs.append(d)
        colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], len(objs))
        ok = True
        for cells, color in zip(objs, colors):
            sh = max(r for r, _ in cells) + 1; sw = max(c for _, c in cells) + 1
            placed = False
            for _ in range(150):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                    continue
                for r, c in cells:
                    g[r0 + r][c0 + c] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — gallery has nothing to pack.
        return g
    if name == "single_motif":
        # Only one motif — rule's pack-multiple operation is trivial.
        for r, c in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 4
        return g
    if name == "motifs_touching":
        # Two motifs touching — connected-component merge breaks "distinct positions".
        g[2][2] = 4; g[2][3] = 4; g[3][3] = 4
        g[3][4] = 5; g[4][4] = 5
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    from collections import Counter
    from puzzle_generators.helpers.selfcheck import components_cells, normalize
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    comps = components_cells(grid, same_color=True)
    if len(comps) < 3:
        errs.append("need at least three isolated motifs")
    colors = [grid[cells[0][0]][cells[0][1]] for cells in comps]
    if len(colors) != len(set(colors)):
        errs.append("motif colors should be distinct")
    counts = Counter(tuple(normalize(cells)) for cells in comps)
    if counts:
        best = counts.most_common()
        if best[0][1] < 2:
            errs.append("need a repeated winner motif shape")
        if len(best) > 1 and best[1][1] >= best[0][1]:
            errs.append("winner motif shape must be uniquely most common")
    return errs
