"""Generator for puzzle 20818e16.

Rule: bg = (0,0)'s color. Find non-bg colors. Output: largest bbox is
canvas, smaller stacked at top-left.

Combinatorial axes (8): grid_h/w, n_rects, rect_h_min, rect_h_max,
rect_w_min, rect_w_max, palette_kind, position_bias.
Degenerates: tied_areas, single_rect, no_rects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect

GENERATOR_ID = "b16f601b9eb8"
VERSION = "2.1.0"
TASK_ID = "b16f601b9eb8"
SUMMARY = (
    "Grid (h, w ~12-18) filled with background color 8 (cyan) "
    "and 2-3 SOLID RECTANGLES of distinct non-bg colors. "
    "Rectangles have distinct AREAS (so a sort is "
    "unambiguous). Rectangles are placed without overlap. "
    "Rule: bg = color at (0, 0). Find non-bg, non-zero color "
    "components. Compute each component's bbox dimensions "
    "(bh, bw) and area = bh*bw. Sort by area descending. The "
    "LARGEST = canvas (oh × ow). Output: oh × ow grid where "
    "each cell (r, c) takes the color of the SMALLEST rect "
    "whose dims still cover (r, c) (i.e., (r, c) is inside "
    "the smaller rect's dims). Rects stack at top-left from "
    "largest to smallest."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "bg = 8",
    "2-4 solid rects of distinct non-bg colors",
    "areas are strictly distinct (sort unambiguous)",
    "rects don't overlap",
]

POSITION_BIASES = ("scattered", "stacked", "row_aligned", "diagonal")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("tied_areas", "single_rect", "no_rects")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "grid_w":         {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "n_rects":        {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "rect_h_min":     {"type": "int", "default": "2", "valid": "2..5"},
    "rect_h_max":     {"type": "int", "default": "rng 5..7", "valid": "3..9"},
    "rect_w_min":     {"type": "int", "default": "2", "valid": "2..5"},
    "rect_w_max":     {"type": "int", "default": "rng 5..7", "valid": "3..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 10, 13
    elif difficulty == "hard":
        h_lo, h_hi = 18, 22
    else:
        h_lo, h_hi = 12, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_rects = int(overrides.get("n_rects",
                                ctx.draw_int("n_rects", 2, 3)))
    n_rects = max(2, min(4, n_rects))
    rh_min = int(overrides.get("rect_h_min", 2))
    rh_max = int(overrides.get("rect_h_max",
                               ctx.draw_int("rect_h_max", 5, 7)))
    rw_min = int(overrides.get("rect_w_min", 2))
    rw_max = int(overrides.get("rect_w_max",
                               ctx.draw_int("rect_w_max", 5, 7)))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias",
                               list(POSITION_BIASES)))
    palette = _build_palette(palette_kind, n_rects, rng)
    g = [[8] * w for _ in range(h)]
    sizes = []
    used_areas = set()
    while len(sizes) < n_rects:
        rh = rng.randint(rh_min, rh_max); rw = rng.randint(rw_min, rw_max)
        area = rh * rw
        if area in used_areas:
            continue
        sizes.append((rh, rw))
        used_areas.add(area)
    placed: list[tuple[int, int, int, int]] = []
    for idx, (color, (rh, rw)) in enumerate(zip(palette, sizes)):
        placed_here = False
        used_now = {ph * pw for _, _, ph, pw in placed}
        if rh * rw not in used_now:
            for _ in range(120):
                r0, c0 = _pick_position(bias, h, w, rh, rw, idx, rng)
                if r0 is None:
                    continue
                if _rect_touches_any(r0, c0, rh, rw, placed):
                    continue
                draw_rect(g, r0, c0, rh, rw, color)
                placed.append((r0, c0, rh, rw))
                placed_here = True
                break
        if not placed_here and rh * rw not in {ph * pw for _, _, ph, pw in placed}:
            for r0 in range(0, h - rh + 1):
                for c0 in range(0, w - rw + 1):
                    if _rect_touches_any(r0, c0, rh, rw, placed):
                        continue
                    draw_rect(g, r0, c0, rh, rw, color)
                    placed.append((r0, c0, rh, rw))
                    placed_here = True
                    break
                if placed_here:
                    break
        if not placed_here:
            # Last-resort: shrink this rectangle to any unused-area size that
            # fits.  This preserves the core rule signal (distinct-area solid
            # rectangles) instead of silently dropping a rectangle or crashing
            # on tight easy layouts.
            used_now = {ph * pw for _, _, ph, pw in placed}
            for rh2 in range(2, min(h, max(2, rh_max)) + 1):
                for rw2 in range(2, min(w, max(2, rw_max)) + 1):
                    if rh2 * rw2 in used_now:
                        continue
                    for r0 in range(0, h - rh2 + 1):
                        for c0 in range(0, w - rw2 + 1):
                            if _rect_touches_any(r0, c0, rh2, rw2, placed):
                                continue
                            draw_rect(g, r0, c0, rh2, rw2, color)
                            placed.append((r0, c0, rh2, rw2))
                            placed_here = True
                            break
                        if placed_here:
                            break
                    if placed_here:
                        break
                if placed_here:
                    break
        if not placed_here:
            raise RuntimeError("could not place all distinct-area rectangles")
    return g


def _rect_touches_any(r0, c0, rh, rw, placed):
    # Rectangles use distinct colors and the Racket rule groups by color, so
    # adjacency is safe; only true overlap corrupts the component bbox.
    r1, c1 = r0 + rh - 1, c0 + rw - 1
    for pr, pc, ph, pw in placed:
        pr1, pc1 = pr + ph - 1, pc + pw - 1
        if not (r1 < pr or pr1 < r0 or c1 < pc or pc1 < c0):
            return True
    return False


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _pick_position(bias, h, w, rh, rw, idx, rng):
    if h - rh < 0 or w - rw < 0:
        return None, None
    if bias == "stacked":
        rr = idx * (rh + 2)
        if rr + rh > h:
            rr = rng.randint(0, h - rh)
        return rr, max(0, (w - rw) // 2)
    if bias == "row_aligned":
        rr = max(0, (h - rh) // 2)
        rc = idx * (rw + 2)
        if rc + rw > w:
            rc = rng.randint(0, w - rw)
        return rr, rc
    if bias == "diagonal":
        rr = idx * 4
        rc = idx * 4
        if rr + rh > h or rc + rw > w:
            return rng.randint(0, h - rh), rng.randint(0, w - rw)
        return rr, rc
    return rng.randint(0, h - rh), rng.randint(0, w - rw)


def _draw_from_degenerate(name, h, w, rng):
    g = [[8] * w for _ in range(h)]
    if name == "tied_areas":
        # 2 rects same area but different shapes
        draw_rect(g, 1, 1, 3, 4, 3)
        draw_rect(g, h - 5, w - 5, 4, 3, 4)
        return g
    if name == "single_rect":
        draw_rect(g, 2, 2, 4, 4, 3)
        return g
    if name == "no_rects":
        return g
    return g

def _components_non_bg8(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 8:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((color, cells))
    return out

def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v == 0 for row in grid for v in row):
        errs.append("normal instances should not contain color 0")
    comps = _components_non_bg8(grid)
    if not (2 <= len(comps) <= 4):
        errs.append(f"expected 2..4 rectangle components, got {len(comps)}")
    areas = []
    for color, cells in comps:
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
        areas.append(area)
        if len(cells) != area:
            errs.append(f"color {color} component is not a solid rectangle")
    if len(areas) != len(set(areas)):
        errs.append("rectangle areas must be strictly distinct")
    return errs
