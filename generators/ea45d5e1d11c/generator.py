"""Generator for 522fdd07.

Rule: each colored square shrinks by two cells per side while keeping
center fixed.

Combinatorial axes (8): grid_size, square_count, palette_kind, bg_color,
anchor_corner, asymmetry_force, palette_size, position_bias.
Degenerates: no_squares, single_square, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ea45d5e1d11c"
VERSION = "2.1.0"  # include size-1 squares (rule GROWS them to 9 -- branch never hit; gen only used sizes 3/5) + size-7; random positions; varied grid (was fixed 18x18/4 slots). v2.1.0: retry until all requested squares are placed, fix bg_color override label, add self_check.
TASK_ID = "ea45d5e1d11c"
SUMMARY = "Several separated solid ODD-sized squares (sizes 1,3,5,7) of distinct colors on a mode-color background. Rule: redraw each square centered, with side N-2 -- EXCEPT a size-1 square GROWS to a 9x9 square. Sizes, count, positions, grid size and bg all vary."

INVARIANTS = [
    "the mode color is the background",
    "foreground objects are separated solid odd-sized squares (sizes 1,3,5,7)",
    "each square's center stays fixed; the rule redraws side N-2 (size-1 -> 9)",
    "squares are separated by >=1 bg cell (distinct components)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_squares", "single_square", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_size":      {"type": "int", "default": "rng 14..22 by diff", "valid": "14..22"},
    "square_count":   {"type": "int", "default": "rng 2..5 by diff", "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "bg_color":       {"type": "color", "default": "rng",
                       "valid": "0..9"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        n = ctx.draw_int("grid_size", 14, 16)
        square_count = ctx.draw_int("square_count", 2, 3); size_pool = [1, 3, 5]
    elif difficulty == "hard":
        n = ctx.draw_int("grid_size", 18, 22)
        square_count = ctx.draw_int("square_count", 4, 5); size_pool = [1, 3, 5, 7]
    else:
        n = ctx.draw_int("grid_size", 16, 19)
        square_count = ctx.draw_int("square_count", 3, 4); size_pool = [1, 3, 5, 7]
    bg = ctx.draw_color("bg_color", exclude=set())
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    pool = _build_palette(palette_kind, bg, rng)
    pool = pool + [c for c in range(1, 10) if c not in pool and c != bg]
    colors = pool[:square_count]
    for _layout_attempt in range(80):
        g = full_grid(n, n, bg)
        placed = []   # (r0, c0, size)

        def _free(r0, c0, sz):
            if r0 < 0 or c0 < 0 or r0 + sz > n or c0 + sz > n:
                return False
            for (pr, pc, ps) in placed:        # >=1 bg-cell gap (no touch/merge)
                if not (r0 > pr + ps or r0 + sz < pr or
                        c0 > pc + ps or c0 + sz < pc):
                    return False
            return True

        ok = True
        for color in colors:
            size = rng.choice(size_pool)
            for _ in range(120):
                r0 = rng.randint(0, n - size); c0 = rng.randint(0, n - size)
                if _free(r0, c0, size):
                    for r in range(size):
                        for c in range(size):
                            g[r0 + r][c0 + c] = color
                    placed.append((r0, c0, size))
                    break
            else:
                ok = False
                break
        if ok and len(placed) == square_count:
            return g
    raise ValueError("could not place separated odd squares")


def _build_palette(kind, bg, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c != bg]
    rng.shuffle(pool)
    return pool


def _mode_color(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _components_except_bg(grid, bg):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == bg:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _bbox_gap_ok(a, b):
    ar1, ac1, ar2, ac2 = a
    br1, bc1, br2, bc2 = b
    return (ar1 > br2 + 1 or br1 > ar2 + 1 or
            ac1 > bc2 + 1 or bc1 > ac2 + 1)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for separated solid odd-sized squares."""
    errs: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    bg = _mode_color(grid)
    comps = _components_except_bg(grid, bg)
    if difficulty == "easy":
        lo, hi = 2, 3
    elif difficulty == "hard":
        lo, hi = 4, 5
    else:
        lo, hi = 3, 4
    if not (lo <= len(comps) <= hi):
        errs.append(f"expected {lo}-{hi} foreground squares for difficulty={difficulty}, got {len(comps)}")
    if len({color for color, _ in comps}) != len(comps):
        errs.append("foreground square colors should be distinct")
    bboxes = []
    for color, cells in comps:
        r1, c1, r2, c2 = _bbox(cells)
        side_h = r2 - r1 + 1
        side_w = c2 - c1 + 1
        if side_h != side_w or side_h not in (1, 3, 5, 7):
            errs.append(f"color {color} component bbox should be odd square 1/3/5/7, got {side_h}x{side_w}")
        if len(cells) != side_h * side_w:
            errs.append(f"color {color} square bbox is not solid")
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if grid[r][c] != color:
                    errs.append(f"color {color} square bbox contains a non-matching cell")
                    break
            else:
                continue
            break
        bboxes.append((r1, c1, r2, c2))
    for i, bb in enumerate(bboxes):
        for other in bboxes[i + 1:]:
            if not _bbox_gap_ok(bb, other):
                errs.append("squares must have at least one background-cell gap")
                return errs
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(18, 18, 0)
    if name == "no_squares":
        return g
    if name == "single_square":
        for r in range(5):
            for c in range(5):
                g[1 + r][1 + c] = 2
        return g
    if name == "full_grid":
        for r in range(18):
            for c in range(18):
                g[r][c] = 2
        return g
    return g
