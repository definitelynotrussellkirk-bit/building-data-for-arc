"""Generator for 694386b5a151 — pick largest same-shape family, pack horizontally.

Rule: group all connected components by their normalized shape (after
shifting min row/col to 0). The largest family wins (most members). Sort
those members by bbox top-left (row, col). Pack them horizontally with
1-cell gap. Each member's cells in the pack use its own color. Output
height = component bbox height.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "694386b5a151"
VERSION = "2.0.0"
TASK_ID = "694386b5a151"

SUMMARY = (
    "0-bg grid (h×w, ~9-13 by ~11-16) with: (a) a 'WINNING "
    "FAMILY' of 2-4 connected components that SHARE the same "
    "normalized shape (e.g., all L-shaped, all 2×2 squares), "
    "each in a DIFFERENT non-zero color; (b) 1-2 'distractor' "
    "components in OTHER normalized shapes (and distinct colors). "
    "All components are 8-conn isolated. The winning family is "
    "strictly larger than any other family. Rule: group "
    "components by normalized shape. Pick the family with the "
    "MOST members. Sort the family by bbox top-left (row asc, "
    "col asc). Pack them horizontally with 1-cell gaps. Output "
    "height = max bbox height of family members. Each member's "
    "color is preserved in its slot."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-4 winning-family components share the same normalized shape, distinct colors",
    "1-2 distractor components have different shapes (smaller family)",
    "winning family strictly larger than any other family",
    "components 8-conn isolated",
]

PALETTE_KINDS = ("default",)
DEGENERATE_TEXTURES = ("no_family", "tied_families", "single_component")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..16", "valid": "9..18"},
    "n_family":       {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "n_distractor":   {"type": "int", "default": "rng 1..2", "valid": "0..3"},
    "palette_kind":   {"type": "str", "default": "default", "valid": "default"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "3..6"},
    "position_bias":  {"type": "str", "default": "scattered_shape_family",
                       "valid": "scattered_shape_family"},
    "n_distinct_colors":{"type": "int", "default": "rng 3..5", "valid": "3..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],          # L
    [(0, 0), (0, 1), (1, 1)],          # mirror-L
    [(0, 0), (1, 0), (1, 1)],          # other-L
    [(0, 0), (0, 1), (1, 0), (1, 1)],  # 2x2
    [(0, 0), (0, 1), (0, 2)],          # 3-row
    [(0, 0), (1, 0), (2, 0)],          # 3-col
    [(0, 0), (0, 1), (1, 1), (2, 1)],  # Z
    [(0, 0), (1, 0), (1, 1), (2, 1)],  # S
]


def _norm(cells):
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return frozenset((r - minr, c - minc) for r, c in cells)


def _free(g, cells_abs, h, w):
    cell_set = set(cells_abs)
    for r, c in cells_abs:
        if not (0 <= r < h and 0 <= c < w):
            return False
        if g[r][c] != 0:
            return False
    for r, c in cells_abs:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    if g[nr][nc] != 0 and (nr, nc) not in cell_set:
                        return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        n_family = ctx.draw_int("n_family", 2, 2)
        n_distractor = ctx.draw_int("n_distractor", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 14, 17)
        n_family = ctx.draw_int("n_family", 3, 4)
        n_distractor = ctx.draw_int("n_distractor", 2, 2)
    else:
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 12, 14)
        n_family = ctx.draw_int("n_family", 2, 3)
        n_distractor = ctx.draw_int("n_distractor", 1, 2)

    # Family must be strictly larger than distractor count
    if n_family <= n_distractor:
        n_distractor = n_family - 1

    for _outer in range(80):
        g = full_grid(h, w, 0)
        family_shape = rng.choice(_SHAPES)
        sh = max(r for r, _ in family_shape) + 1
        sw = max(c for _, c in family_shape) + 1

        # Pick colors
        all_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9],
                                n_family + n_distractor)
        family_colors = all_colors[:n_family]
        distractor_colors = all_colors[n_family:]

        # Place family members
        ok = True
        for color in family_colors:
            placed = False
            for _try in range(120):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                cells_abs = [(r0 + dr, c0 + dc) for dr, dc in family_shape]
                if _free(g, cells_abs, h, w):
                    for r, c in cells_abs:
                        g[r][c] = color
                    placed = True
                    break
            if not placed:
                ok = False
                break
        if not ok:
            continue

        # Place distractors with DIFFERENT normalized shapes
        family_norm = _norm(family_shape)
        ok = True
        for color in distractor_colors:
            placed = False
            for _try in range(40):
                d_shape = rng.choice(_SHAPES)
                d_norm = _norm(d_shape)
                if d_norm == family_norm:
                    continue
                dh = max(r for r, _ in d_shape) + 1
                dw = max(c for _, c in d_shape) + 1
                for _try2 in range(60):
                    r0 = rng.randint(0, h - dh)
                    c0 = rng.randint(0, w - dw)
                    cells_abs = [(r0 + dr, c0 + dc) for dr, dc in d_shape]
                    if _free(g, cells_abs, h, w):
                        for r, c in cells_abs:
                            g[r][c] = color
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                ok = False
                break
        if not ok:
            continue
        return g
    raise ValueError("could not realize family + distractors layout")


def _components8(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            colors = set()
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                colors.add(grid[rr][cc])
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and
                                grid[nr][nc] != 0 and (nr, nc) not in seen):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            comps.append((cells, colors))
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    comps = _components8(grid)
    if len(comps) < 3:
        errs.append("need winning family plus at least one distractor component")
    colors = []
    by_shape = {}
    for cells, comp_colors in comps:
        if len(comp_colors) != 1:
            errs.append("8-connected components must not merge multiple colors")
        colors.extend(comp_colors)
        by_shape.setdefault(_norm(cells), 0)
        by_shape[_norm(cells)] += 1
    if len(colors) != len(set(colors)):
        errs.append("component colors must be distinct")
    if by_shape:
        max_n = max(by_shape.values())
        winners = [s for s, n in by_shape.items() if n == max_n]
        if max_n < 2:
            errs.append("no repeated normalized-shape family")
        if len(winners) != 1:
            errs.append("winning normalized-shape family must be unique")
        if any(n >= max_n for s, n in by_shape.items() if s not in winners):
            errs.append("winning family must be strictly larger than distractor families")
        if len(by_shape) < 2:
            errs.append("need at least one distractor shape different from the winning family")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_family":
        # All distinct shapes — no family with ≥2 members
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 4
        for r, c in [(4, 5), (4, 6), (4, 7)]: g[r][c] = 6
        for r, c in [(7, 9), (8, 9)]: g[r][c] = 8
        return g
    if name == "tied_families":
        # Two families tied at 2 members each — ambiguous winner
        for r, c in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4
        for r, c in [(4, 5), (4, 6), (5, 5)]: g[r][c] = 6
        for r, c in [(7, 1), (7, 2)]: g[r][c] = 8
        for r, c in [(7, 9), (8, 9)]: g[r][c] = 3
        return g
    if name == "single_component":
        for r, c in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 4
        return g
    return g
