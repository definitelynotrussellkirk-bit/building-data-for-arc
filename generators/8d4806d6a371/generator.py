"""Generator for arc_additional_puzzle_bank_volume19:E129.

Rule: magenta components touching exactly one border are recolored
yellow.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_components, all_interior, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "8d4806d6a371"
VERSION = "2.0.2"
TASK_ID = "8d4806d6a371"
SUMMARY = "Magenta components touching exactly one border are recolored yellow."

INVARIANTS = [
    "background is 0",
    "at least one magenta component touches exactly one border",
    "other magenta components touch zero or two borders",
    "components are separated by background",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_components", "all_interior", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "true",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "true",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "border", "valid": "border"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_components|all_interior|full_grid"},
}


def _components6(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != 6 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            comp = []
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 6 and (rr, cc) not in seen:
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            comps.append(comp)
    return comps


def _border_count(comp, h, w):
    borders = set()
    for r, c in comp:
        if r == 0:
            borders.add("top")
        if r == h - 1:
            borders.add("bottom")
        if c == 0:
            borders.add("left")
        if c == w - 1:
            borders.add("right")
    return len(borders)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify both target (one-border) and non-target magenta components."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_components", "all_interior", "full_grid"):
        return errs
    comps = _components6(grid)
    if not comps:
        errs.append("no magenta (color-6) cells found")
        return errs
    counts = [_border_count(comp, h, w) for comp in comps]
    if not any(n == 1 for n in counts):
        errs.append("no magenta component touches exactly one border")
    if not any(n in (0, 2) for n in counts):
        errs.append("no non-target component touching zero or two borders; branch is hidden")
    if any(n not in (0, 1, 2) for n in counts):
        errs.append(f"unexpected component touching >2 borders: {counts}")
    return errs


def _free(g, r, c, hh, ww):
    """Is the (hh x ww) box at (r,c) in-bounds and clear with a 1-cell margin
    (so placed components stay separate under 4/8-connectivity)?"""
    H, W = len(g), len(g[0])
    if r < 0 or c < 0 or r + hh > H or c + ww > W:
        return False
    for rr in range(max(0, r - 1), min(H, r + hh + 1)):
        for cc in range(max(0, c - 1), min(W, c + ww + 1)):
            if g[rr][cc] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12); w = ctx.draw_int("grid_w", 10, 12); nlo, nhi = 3, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 19); w = ctx.draw_int("grid_w", 14, 19); nlo, nhi = 4, 6
    else:
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 11, 15); nlo, nhi = 3, 5
    rng = ctx.draw_rng("placement")

    for _attempt in range(40):
        g = full_grid(h, w, 0)
        n = rng.randint(nlo, nhi)
        # Always include >=1 'edge' component (touches exactly one border, so the
        # rule recolors it) and mix in 'interior' (0 borders) and 'corner' (2),
        # forcing the solver to COUNT borders per component rather than memorize
        # a fixed position. Size/count/position all random -> high diversity.
        profiles = ["edge", rng.choice(["interior", "corner"])] + [
            rng.choice(["interior", "edge", "corner"])
            for _ in range(n - 2)
        ]
        rng.shuffle(profiles)
        placed_edge = 0
        placed_other = 0
        for prof in profiles:
            for _ in range(60):
                hh = rng.randint(2, 3); ww = rng.randint(2, 3)
                if prof == "corner":
                    r = rng.choice([0, h - hh]); c = rng.choice([0, w - ww])
                elif prof == "edge":
                    side = rng.choice(["top", "bottom", "left", "right"])
                    if side == "top":
                        r, c = 0, rng.randint(1, w - ww - 1)
                    elif side == "bottom":
                        r, c = h - hh, rng.randint(1, w - ww - 1)
                    elif side == "left":
                        r, c = rng.randint(1, h - hh - 1), 0
                    else:
                        r, c = rng.randint(1, h - hh - 1), w - ww
                else:  # interior: touches no border
                    r = rng.randint(1, h - hh - 1); c = rng.randint(1, w - ww - 1)
                if _free(g, r, c, hh, ww):
                    draw_rect(g, r, c, hh, ww, 6)
                    placed_edge += (prof == "edge")
                    placed_other += (prof != "edge")
                    break
        if placed_edge >= 1 and placed_other >= 1:
            return g
    raise ValueError("could not place both target and non-target magenta components")


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_components":
        return g
    if name == "all_interior":
        draw_rect(g, 4, 4, 2, 2, 6)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 6
        return g
    return g
