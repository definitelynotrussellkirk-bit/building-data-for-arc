"""Generator for arc_puzzle_bank_21_set9_e:medium_i11 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b7be00fa3529"
# 2.0.0: WRONG task (docstring claimed vertical-motif gallery, and color 5 was
# used as an ordinary motif color). Actual rule is PER-COLUMN SEGMENT GRAVITY:
# color-5 cells are floors/walls; non-{0,5} cells fall to the bottom of their
# 5-bounded segment (order preserved). Rebuilt to that structure: a vertical
# 5-axis/floor scaffold + scattered single colored cells per column.
VERSION = "2.0.1"
TASK_ID = "b7be00fa3529"

SUMMARY = (
    "0-bg grid with COLOR-5 cells acting as FLOORS/WALLS (some full-height "
    "5-columns plus scattered 5-cells inside other columns) and SCATTERED "
    "SINGLE non-{0,5} colored cells. Rule (PER-COLUMN SEGMENT GRAVITY): the "
    "output keeps every 5-cell in place; within each column, the 5-cells "
    "split it into segments, and each segment's non-{0,5} values fall to the "
    "BOTTOM of that segment preserving their top-to-bottom order. Net: loose "
    "colored cells drop within their 5-bounded segment."
)

INVARIANTS = [
    "background is 0",
    "color 5 marks floors/walls (kept fixed by the rule)",
    "non-{0,5} cells are loose values that fall within their column segment",
    ">=1 column has a loose value above empty space (so gravity is visible)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "6..16"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
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


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: if ≥2 distinct nonzero values exist, color-5 (wall/floor) must be among them."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    nz_vals = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(nz_vals) >= 2 and 5 not in nz_vals:
        return [f"multiple nonzero values {sorted(nz_vals)} but no color-5 (wall/floor)"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 6, 9)
        n_loose = (4, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 10, 16)
        n_loose = (10, 22)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 7, 13)
        n_loose = (6, 14)
    rng = ctx.draw_rng("layout")

    colors = [c for c in [1, 2, 3, 4, 6, 7, 8, 9]]  # non-{0,5} loose values
    for _outer in range(40):
        g = full_grid(h, w, 0)
        # (a) 1-3 full-height 5-WALL columns (like the canonical divider cols)
        n_walls = rng.randint(1, min(3, max(1, w // 3)))
        wall_cols = rng.sample(range(w), n_walls)
        for c in wall_cols:
            for r in range(h):
                g[r][c] = 5
        # (b) scattered interior 5-FLOOR cells in non-wall columns
        non_wall = [c for c in range(w) if c not in wall_cols]
        n_floors = rng.randint(0, max(0, len(non_wall)))
        for _ in range(n_floors):
            c = rng.choice(non_wall)
            r = rng.randint(1, h - 1)   # leave room above for falling values
            if g[r][c] == 0:
                g[r][c] = 5
        # (c) scattered loose non-{0,5} single cells in non-wall columns
        loose = rng.randint(*n_loose)
        placed_loose = 0
        for _ in range(loose * 4):
            if placed_loose >= loose:
                break
            c = rng.choice(non_wall)
            r = rng.randint(0, h - 1)
            if g[r][c] == 0:
                g[r][c] = rng.choice(colors)
                placed_loose += 1
        # need at least one loose cell with empty space below it in its segment
        if _has_visible_gravity(g, non_wall, h):
            return g
    return g


def _has_visible_gravity(g, cols, h):
    for c in cols:
        # within each 5-bounded segment, is there a loose value with a 0 below?
        seg_floor = h  # exclusive bottom of current segment going up
        for r in range(h - 1, -1, -1):
            v = g[r][c]
            if v == 5:
                seg_floor = r
                continue
            if v != 0:
                # look below within the same segment for an empty cell
                for rr in range(r + 1, seg_floor):
                    if g[rr][c] == 0:
                        return True
    return False


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no motifs to gather.
        return g
    if name == "single_motif":
        # Only 1 motif — rule's gallery is trivial.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color — rule's per-color gather treats
        # them as one big component.
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g
