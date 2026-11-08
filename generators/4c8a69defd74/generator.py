"""Generator for puzzle 27f8ce4f.

Rule: `(rule! (lambda (g) (self-tile g (lambda (v) (= v (mode g))))))`.
Self-tile gated on cells equal to the most-common color (often the bg).
Output is H² × W² with the input duplicated where the mode-color appears.

Combinatorial axes:
  * grid_h / grid_w        — outer canvas size (small; output is H² × W²)
  * mode_color             — which color is the mode (forced by construction)
  * minority_palette_size  — number of distinct minority colors
  * mode_density           — fraction of cells that take the mode color
                             (must be > 0.5 to keep mode unambiguous)
  * minority_layout        — where minority cells sit: random / cluster /
                             corner / row / column
  * caller-opt-in degenerates: tied_modes (ambiguous mode), monochrome
                               (single color), all_minority_unique
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4c8a69defd74"
VERSION = "2.0.1"
TASK_ID = "4c8a69defd74"
SUMMARY = (
    "Small 0-bg grid (h×w, h=3..5, w=3..5) with EXACTLY ONE MODE "
    "color (strictly most frequent, >50% of cells). Other cells "
    "use 1-3 minority colors. Rule: self-tile the input. Output "
    "is h*h × w*w. For each cell (r, c) in the input, if its "
    "value equals the mode, place the entire input grid at "
    "block (r*h..r*h+h-1, c*w..c*w+w-1) in the output; "
    "otherwise that block is all 0. Effect: input acts as both "
    "the unit tile AND the mask of where to place itself."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input dims in [3, 5] × [3, 5]",
    "exactly one color is the strict mode (>50% of cells)",
    "≥2 distinct colors (else self-tile is trivially uniform)",
]

MINORITY_LAYOUTS = ("random", "cluster", "corner", "row", "column")
DEGENERATE_TEXTURES = ("tied_modes", "monochrome", "all_minority_unique")
HELPFUL_TEXTURES = MINORITY_LAYOUTS

AXES = {
    "grid_h":              {"type": "int",   "default": "rng 3..5", "valid": "3..6"},
    "grid_w":              {"type": "int",   "default": "rng 3..5", "valid": "3..6"},
    "mode_color":          {"type": "color", "default": "rng",      "valid": "0..9"},
    "minority_palette_size": {"type": "int", "default": "rng 1..3", "valid": "1..6"},
    "mode_density":        {"type": "float", "default": "rng 0.55..0.85",
                            "valid": "0.51..0.95"},
    "minority_layout":     {"type": "str",   "default": "rng helpful",
                            "valid": "|".join(MINORITY_LAYOUTS)},
    "texture":             {"type": "str",   "default": "alias for minority_layout",
                            "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi, p_lo, p_hi = 3, 4, 1, 1
    elif difficulty == "hard":
        h_lo, h_hi, p_lo, p_hi = 5, 5, 2, 3
    else:
        h_lo, h_hi, p_lo, p_hi = 3, 5, 1, 3

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("cells")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, ctx, rng)

    n_palette = int(overrides.get("minority_palette_size",
                                  ctx.draw_int("minority_palette_size", p_lo, p_hi)))
    palette = ctx.draw_distinct_colors("palette", n=n_palette + 1)
    mode_color = palette[0]
    minority = palette[1:] if len(palette) > 1 else palette

    density = float(overrides.get(
        "mode_density",
        ctx.draw_rng("mode_density").uniform(0.55, 0.85)))
    layout = (overrides.get("texture")
              or overrides.get("minority_layout")
              or ctx.draw_choice("minority_layout", list(MINORITY_LAYOUTS)))

    g = full_grid(h, w, mode_color)
    n_cells = h * w
    n_mode = max(int(n_cells * density), n_cells // 2 + 1)
    n_minority = n_cells - n_mode

    minority_positions = _layout_positions(layout, h, w, n_minority, rng)
    for i, (r, c) in enumerate(minority_positions):
        g[r][c] = minority[i % len(minority)]

    # Sanity: ensure mode is strictly the majority (>50%) of cells.
    counts: dict = {}
    for r in range(h):
        for c in range(w):
            counts[g[r][c]] = counts.get(g[r][c], 0) + 1
    top = sorted(counts.values(), reverse=True)
    if len(top) >= 2 and top[0] <= top[1]:
        # Force one extra mode cell.
        for r in range(h):
            for c in range(w):
                if g[r][c] != mode_color:
                    g[r][c] = mode_color
                    return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify self-tile mode-gated input invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    problems = []
    if h < 3 or h > 6 or w < 3 or w > 6:
        problems.append(f"expected dims in [3,5]x[3,5], got {h}x{w}")
    counts: dict = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    if len(counts) < 2:
        problems.append(f"expected >=2 distinct colors, found {len(counts)}")
    else:
        total = h * w
        max_count = max(counts.values())
        if max_count <= total // 2:
            problems.append("no color has strict majority (>50%) — mode is ambiguous")
    return problems


def _layout_positions(layout, h, w, n, rng):
    if n <= 0:
        return []
    cells = [(r, c) for r in range(h) for c in range(w)]
    if layout == "cluster":
        # Concentrate minority in one corner.
        center_r = rng.randint(0, h - 1)
        center_c = rng.randint(0, w - 1)
        cells.sort(key=lambda rc: (abs(rc[0] - center_r) + abs(rc[1] - center_c),
                                   rng.random()))
        return cells[:n]
    if layout == "corner":
        cells.sort(key=lambda rc: min(rc[0], h - 1 - rc[0])
                                  + min(rc[1], w - 1 - rc[1]))
        return cells[:n]
    if layout == "row":
        r = rng.randint(0, h - 1)
        row_cells = [(r, c) for c in range(w)]
        rng.shuffle(row_cells)
        return row_cells[:n]
    if layout == "column":
        c = rng.randint(0, w - 1)
        col_cells = [(r, c) for r in range(h)]
        rng.shuffle(col_cells)
        return col_cells[:n]
    rng.shuffle(cells)
    return cells[:n]


def _draw_from_degenerate(name, h, w, ctx, rng):
    """Edge-case where the mode-gated self-tile signal collapses.

    tied_modes          — two colors tie for most-common; mode is
                          implementation-dependent.
    monochrome          — all cells the same color → output is a uniform
                          big block.
    all_minority_unique — every non-mode cell uses a different color;
                          self-tile pattern is dense, hard to read.
    """
    palette = ctx.draw_distinct_colors("palette", n=4)
    g = full_grid(h, w, palette[0])
    if name == "tied_modes":
        # Half the cells palette[0], half palette[1].
        cells = [(r, c) for r in range(h) for c in range(w)]
        rng.shuffle(cells)
        half = len(cells) // 2
        for r, c in cells[:half]:
            g[r][c] = palette[0]
        for r, c in cells[half:half * 2]:
            g[r][c] = palette[1]
        return g
    if name == "monochrome":
        color = rng.choice(palette)
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "all_minority_unique":
        # Mode dominates, but every non-mode cell is a different color.
        for r in range(h):
            for c in range(w):
                g[r][c] = palette[0]
        cells = [(r, c) for r in range(h) for c in range(w)]
        rng.shuffle(cells)
        unique_minority_count = min(h * w // 3, len(palette) - 1)
        for i in range(unique_minority_count):
            r, c = cells[i]
            g[r][c] = palette[1 + i % (len(palette) - 1)]
        return g
    return g
