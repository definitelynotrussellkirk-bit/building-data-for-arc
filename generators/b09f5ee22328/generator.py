"""Generator for ARC task c3e719e8.

Rule: `(rule! (lambda (g) (self-tile g (lambda (v) (= v (mode g))))))`.
Same rule as 27f8ce4f but the canonical examples use a 3 × 3 input
exclusively. Kept independent so each task contributes its own slice.

Combinatorial axes:
  * grid_size              — n varies from 3 to 5 in the default path
  * mode_color             — which color is the mode
  * minority_palette_size  — distinct minority colors (1..3)
  * minority_count         — how many cells are minority (1..4)
                             (mode count is 9 - minority_count)
  * minority_layout        — where minorities sit
  * caller-opt-in degenerates: tied_modes, monochrome, all_minority_unique
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b09f5ee22328"
VERSION = "1.2.0"  # shape-locked in+out: hardcoded 3x3 -> always 9x9. self-tile fractals any n x n to n^2 x n^2; now vary n 3..5 (->9x9/16x16/25x25) + random minority placement."
TASK_ID = "b09f5ee22328"
SUMMARY = "An n × n grid (n in 3..5) with a unique most-frequent color; mode cells receive tile copies."

INVARIANTS = [
    "input is square with side length 3..5",
    "the modal color is unique (strictly more frequent than any other)",
    "≥1 non-modal cell so the rule has visible effect",
]

MINORITY_LAYOUTS = ("random", "corner", "row", "column", "cross", "diagonal")
DEGENERATE_TEXTURES = ("tied_modes", "monochrome", "all_minority_unique")
HELPFUL_TEXTURES = MINORITY_LAYOUTS

AXES = {
    "grid_size":             {"type": "int",   "default": "3..5 by difficulty/sample_index", "valid": "3..5"},
    "mode_color":            {"type": "color", "default": "rng", "valid": "0..9"},
    "minority_palette_size": {"type": "int",   "default": "rng 1..3", "valid": "1..6"},
    "minority_count":        {"type": "int",   "default": "rng 1..4", "valid": "1..8"},
    "minority_layout":       {"type": "str",   "default": "rng helpful",
                              "valid": "|".join(MINORITY_LAYOUTS)},
    "texture":               {"type": "str",   "default": "alias for minority_layout",
                              "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    # rule is self-tile: an n x n input fractals to (n*n) x (n*n). v1.x hardcoded
    # n=3 -> always 9x9 (shape-locked in+out). The rule handles any n, so vary it
    # (cap n=5 -> 25x25 <= 30). Minority count kept < n^2/2 so mode stays majority.
    if difficulty == "easy":
        n, p_lo, p_hi = 3, 1, 1
    elif difficulty == "hard":
        n, p_lo, p_hi = (4 if (sample_index % 2 == 0) else 5), 2, 3
    else:
        n = 3 + (sample_index % 3)            # 3,4,5
        p_lo, p_hi = 1, 3

    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], ctx, rng)

    n_palette = int(overrides.get("minority_palette_size",
                                  ctx.draw_int("minority_palette_size", p_lo, p_hi)))
    palette = ctx.draw_distinct_colors("palette", n=n_palette + 1)
    mode_color = palette[0]
    minority = palette[1:] if len(palette) > 1 else palette

    # minority cells: < n^2/2 so mode_color stays the majority (the self-tile key)
    cap = max(1, n * n // 2 - 1)
    n_minority = int(overrides.get("minority_count",
                                   ctx.draw_int("minority_count", 1, cap)))
    n_minority = max(1, min(cap, n_minority))
    g = full_grid(n, n, mode_color)
    cells = [(r, c) for r in range(n) for c in range(n)]
    for i, (r, c) in enumerate(rng.sample(cells, n_minority)):
        g[r][c] = minority[i % len(minority)]
    return g


def _layout_positions(layout, n, rng):
    if layout == "corner":
        candidates = [(0, 0), (0, 2), (2, 0), (2, 2)]
    elif layout == "row":
        r = rng.randint(0, 2)
        candidates = [(r, 0), (r, 1), (r, 2)]
    elif layout == "column":
        c = rng.randint(0, 2)
        candidates = [(0, c), (1, c), (2, c)]
    elif layout == "cross":
        candidates = [(0, 1), (1, 0), (1, 2), (2, 1)]
    elif layout == "diagonal":
        candidates = [(0, 0), (1, 1), (2, 2)] if rng.random() < 0.5 \
            else [(0, 2), (1, 1), (2, 0)]
    else:
        candidates = [(r, c) for r in range(3) for c in range(3)]
    rng.shuffle(candidates)
    return candidates[:max(0, min(n, len(candidates)))]


def _draw_from_degenerate(name, ctx, rng):
    """Edge-case where the mode-gated self-tile signal collapses.

    tied_modes          — two colors tie for most common; mode is ambiguous.
    monochrome          — uniform input; output is uniform 9 × 9.
    all_minority_unique — every non-mode cell is a unique color.
    """
    palette = ctx.draw_distinct_colors("palette", n=4)
    g = full_grid(3, 3, palette[0])
    if name == "tied_modes":
        # 4 of one color, 4 of another, 1 wild.
        cells = [(r, c) for r in range(3) for c in range(3)]
        rng.shuffle(cells)
        for i, (r, c) in enumerate(cells):
            if i < 4:
                g[r][c] = palette[0]
            elif i < 8:
                g[r][c] = palette[1]
            else:
                g[r][c] = palette[2] if len(palette) > 2 else palette[0]
        return g
    if name == "monochrome":
        color = rng.choice(palette)
        for r in range(3):
            for c in range(3):
                g[r][c] = color
        return g
    if name == "all_minority_unique":
        # Mode at center + 4 mode neighbors; minorities each unique.
        for r in range(3):
            for c in range(3):
                g[r][c] = palette[0]
        unique_cells = [(0, 0), (0, 2), (2, 0), (2, 2)]
        rng.shuffle(unique_cells)
        for i, (r, c) in enumerate(unique_cells[:min(3, len(palette) - 1)]):
            g[r][c] = palette[1 + i]
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not all(isinstance(row, list) and row for row in grid):
        return ["empty or malformed grid"]
    n = len(grid)
    if any(len(row) != n for row in grid):
        errs.append("input is not square")
        return errs
    if n not in (3, 4, 5):
        errs.append(f"unexpected self-tile side length {n}; expected 3..5")
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    if len(counts) < 2:
        errs.append("monochrome default instance hides the mode-gated copy rule")
        return errs
    ordered = sorted(counts.values(), reverse=True)
    if len(ordered) < 2 or ordered[0] <= ordered[1]:
        errs.append(f"modal color is not unique: counts={counts}")
    mode_count = ordered[0]
    if mode_count <= n * n // 2:
        errs.append("modal color is not a strict majority")
    return errs
