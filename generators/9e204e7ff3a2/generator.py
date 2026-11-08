"""Generator for puzzle 496994bd.

Rule: complete vertical (UD) symmetry. Output cell (r, c) = input cell
if non-zero; else its UD mirror's value if non-zero; else 0.

Combinatorial axes: grid_h/w, fg_palette, fg_density, fg_layout,
ud_asymmetric (must be UD-asymmetric so rule has visible effect).
Degenerates: ud_symmetric (rule no-op), all_zero, monochrome.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9e204e7ff3a2"
VERSION = "2.1.0"  # normal path now enforces >=2 visible fg colors, not a monochrome degenerate
TASK_ID = "9e204e7ff3a2"
SUMMARY = (
    "0-bg grid (h ∈ 5-14, w ∈ 5-14, by "
    "difficulty) with: SPARSE NON-BG "
    "CELLS in 1-4 DISTINCT COLORS, "
    "placed at density 15-40% via "
    "fg_layout ∈ {random / cluster "
    "(Manhattan-centered) / row (one "
    "full row picked) / column / "
    "diagonal / blob (Chebyshev) / "
    "scattered (every other (r+c))} "
    "in candidates filtered by "
    "row_bias ∈ {top / bottom / "
    "spread}. The grid is "
    "INTENTIONALLY UD-ASYMMETRIC — "
    "at least one cell exists where "
    "the UD mirror position "
    "(h-1-r, c) is currently 0 (so "
    "the rule has visible effect). "
    "If natural placement happens "
    "to be UD-symmetric, the "
    "generator forces one "
    "asymmetric cell. Rule "
    "(COMPLETE TOP-BOTTOM (UD) "
    "SYMMETRY — FILL EVERY BG "
    "CELL WHOSE UD MIRROR IS NON-"
    "BG WITH THE MIRROR'S COLOR): "
    "For EACH (r, c) where "
    "g[r][c] == 0: COMPUTE the UD "
    "mirror (h-1-r, c). IF the "
    "mirror cell is non-bg: PAINT "
    "g[r][c] with the mirror's "
    "color. ORIGINAL non-bg cells "
    "preserved. Net: every cell "
    "gets the color of itself OR "
    "its UD mirror (whichever is "
    "non-bg first); the grid "
    "becomes UD-symmetric — gaps "
    "in the top half are filled "
    "from the bottom half and "
    "vice versa."
)

INVARIANTS = [
    "background is 0",
    "≥1 cell where the UD mirror is bg (so rule fills it)",
    "≥2 distinct fg colors so output diversity is meaningful",
]

FG_LAYOUTS = ("random", "cluster", "row", "column", "diagonal", "blob", "scattered")
DEGENERATE_TEXTURES = ("ud_symmetric", "all_zero", "monochrome")
HELPFUL_TEXTURES = FG_LAYOUTS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..14", "valid": "3..18"},
    "grid_w":         {"type": "int", "default": "rng 5..14", "valid": "3..18"},
    "fg_palette_size": {"type": "int", "default": "rng 1..4", "valid": "1..6"},
    "fg_density":     {"type": "float", "default": "rng 0.15..0.4", "valid": "0..0.7"},
    "fg_layout":      {"type": "str", "default": "rng helpful",
                       "valid": "|".join(FG_LAYOUTS)},
    "row_bias":       {"type": "str", "default": "rng top|bottom|spread",
                       "valid": "top|bottom|spread"},
    "texture":        {"type": "str", "default": "alias for fg_layout",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 5, 7
    elif difficulty == "hard":
        h_lo, h_hi = 11, 14
    else:
        h_lo, h_hi = 5, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, ctx, rng)
    n_palette = int(overrides.get("fg_palette_size",
                                  ctx.draw_int("fg_palette_size", 2, 4)))
    n_palette = max(2, n_palette)
    palette = list(ctx.draw_distinct_colors("palette", n=n_palette, exclude={0}))
    density = float(overrides.get("fg_density",
                                  ctx.draw_rng("fg_density").uniform(0.15, 0.4)))
    layout = (overrides.get("texture") or overrides.get("fg_layout")
              or ctx.draw_choice("fg_layout", list(FG_LAYOUTS)))
    row_bias = overrides.get("row_bias",
                             ctx.draw_choice("row_bias", ["top", "bottom", "spread"]))
    g = full_grid(h, w, 0)
    candidates = _candidates_for_bias(row_bias, h, w)
    cells = _layout_cells(layout, candidates, density, rng)
    for r, c in cells:
        if 0 <= r < h and 0 <= c < w:
            g[r][c] = rng.choice(palette)
    _ensure_two_colors_and_visible_asymmetry(g, palette)
    return g


def _ensure_two_colors_and_visible_asymmetry(g, palette):
    h, w = len(g), len(g[0])

    def visible():
        return any(g[r][c] != 0 and g[h - 1 - r][c] == 0 and r != h - 1 - r
                   for r in range(h) for c in range(w))

    if not visible():
        g[0][0] = palette[0]
        g[h - 1][0] = 0
    colors = {v for row in g for v in row if v != 0}
    if len(colors) < 2:
        # Put a color not already present in a mirror-gap position so both the
        # palette and the symmetry-completion branch are visible in normal
        # examples.
        new_color = next((color for color in palette if color not in colors), palette[0])
        for r in range(h):
            mr = h - 1 - r
            if r == mr:
                continue
            for c in range(w):
                if g[r][c] == 0:
                    g[r][c] = new_color
                    g[mr][c] = 0
                    return
        # Extremely dense fallback: preserve at least one old color, then add the
        # missing color at a different column.
        g[0][0] = next(iter(colors))
        g[0][min(1, w - 1)] = new_color
        g[h - 1][min(1, w - 1)] = 0


def _candidates_for_bias(bias, h, w):
    if bias == "top":
        return [(r, c) for r in range(h // 2) for c in range(w)]
    if bias == "bottom":
        return [(r, c) for r in range(h // 2, h) for c in range(w)]
    return [(r, c) for r in range(h) for c in range(w)]


def _layout_cells(layout, candidates, density, rng):
    if not candidates:
        return []
    n = max(1, int(len(candidates) * density))
    if layout == "cluster":
        cr, cc = rng.choice(candidates)
        candidates = sorted(candidates, key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return candidates[:n]
    if layout == "row":
        rs = sorted({r for r, _ in candidates})
        if not rs: return []
        r = rng.choice(rs)
        cells = [(r, c) for (rr, c) in candidates if rr == r]
        rng.shuffle(cells)
        return cells[:n]
    if layout == "column":
        cs = sorted({c for _, c in candidates})
        if not cs: return []
        c = rng.choice(cs)
        cells = [(r, c) for (r, cc) in candidates if cc == c]
        rng.shuffle(cells)
        return cells[:n]
    if layout == "diagonal":
        cand_set = set(candidates)
        return [(k, k) for k in range(25) if (k, k) in cand_set][:n]
    if layout == "blob":
        cr, cc = rng.choice(candidates)
        candidates = sorted(candidates, key=lambda rc: max(abs(rc[0] - cr), abs(rc[1] - cc)))
        return candidates[:n]
    if layout == "scattered":
        scat = [(r, c) for (r, c) in candidates if (r + c) % 2 == 0]
        rng.shuffle(scat)
        return scat[:n]
    rng.shuffle(candidates)
    return candidates[:n]


def _draw_from_degenerate(name, h, w, ctx, rng):
    palette = list(ctx.draw_distinct_colors("palette", n=3, exclude={0}))
    g = full_grid(h, w, 0)
    if name == "ud_symmetric":
        for r in range(h // 2):
            for c in range(w):
                if rng.random() < 0.3:
                    color = rng.choice(palette)
                    g[r][c] = color
                    g[h - 1 - r][c] = color
        return g
    if name == "all_zero":
        return g
    if name == "monochrome":
        c0 = palette[0]
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.3:
                    g[r][c] = c0
        g[0][0] = c0
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or len({len(row) for row in grid}) != 1:
        return ["grid must be a nonempty rectangle"]
    h, w = len(grid), len(grid[0])
    colors = {v for row in grid for v in row if v != 0}
    if len(colors) < 2:
        msgs.append(f"normal symmetry example should use >=2 fg colors, found {sorted(colors)}")
    visible = any(grid[r][c] != 0 and grid[h - 1 - r][c] == 0 and r != h - 1 - r
                  for r in range(h) for c in range(w))
    if not visible:
        msgs.append("no cell has a nonzero value with a zero UD mirror; rule branch is hidden")
    return msgs
