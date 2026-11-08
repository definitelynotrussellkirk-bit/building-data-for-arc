"""Generator for puzzle 9b30e358.

Rule: bottom band of non-bg rows + all-bg rows above. Rule tiles the
bottom band upward to fill empty space.

Combinatorial axes (8): grid_h/w, band_h, band_color, band_pattern,
palette_size, bg_color, decoy_density, band_density.
Degenerates: no_band, full_band, alternating_rows.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e28d95a116e4"
VERSION = "3.2.0"  # WIDEN-DIST: default backgrounds are now nonzero and default dimensions are larger, matching eval nonzero-bg/area spread; WRONG-BG: canonical bg is a NON-ZERO field color (t0 bg=5, t1 bg=3) with the band pattern in OTHER colors; gen always used bg=0. Rule uses bg=mode (works either way) but the distribution diverged. Now draw a varied bg color, fill the field with it, and paint the band pattern in distinct non-bg colors."
TASK_ID = "e28d95a116e4"
SUMMARY = (
    "Nonzero modal-bg grid (default h~12-22, w~12-22) with a SOLID "
    "BOTTOM BAND of band_h~3-7 rows containing a "
    "PATTERN (even_cols / odd_cols / halves / "
    "thirds / diagonal / checker / frame / "
    "scattered) painted in one or more colors "
    "distinct from the field/background color. "
    "Above the band, all rows are entirely the "
    "modal background. Rule: extract the "
    "band's pattern. TILE the band UPWARD by "
    "REPEATING the band's row sequence (or "
    "row-by-row period) through the empty rows "
    "above, filling them with the same band "
    "pattern until the entire grid is covered. "
    "Net: input has modal-bg top + a patterned band "
    "at bottom; output is the band's pattern "
    "REPLICATED upward to fill the whole grid."
)

INVARIANTS = [
    "bg is most common color (rule uses (mode g -1))",
    "the bottom band of non-bg rows starts at the bottom",
    "above the band is entirely bg",
    "band height >=2 and < grid_h",
]

BAND_PATTERNS = ("even_cols", "odd_cols", "halves", "thirds",
                 "diagonal", "checker", "frame", "scattered")
DEGENERATE_TEXTURES = ("no_band", "full_band", "alternating_rows")
HELPFUL_TEXTURES = BAND_PATTERNS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..22", "valid": "6..30"},
    "grid_w":         {"type": "int", "default": "rng 12..22", "valid": "5..30"},
    "band_h":         {"type": "int", "default": "rng 3..7",  "valid": "2..10"},
    "band_color":     {"type": "color", "default": "rng (≠ bg_color)",
                       "valid": "0..9"},
    "band_pattern":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(BAND_PATTERNS)},
    "band_density":   {"type": "float", "default": "rng 0.5..0.8",
                       "valid": "0.2..1"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..3"},
    "bg_color":       {"type": "color", "default": "rng nonzero modal field color", "valid": "0..9"},
    "texture":        {"type": "str", "default": "alias for band_pattern",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, b_lo, b_hi = 8, 12, 8, 12, 2, 4
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, b_lo, b_hi = 20, 30, 18, 30, 5, 9
    else:
        h_lo, h_hi, w_lo, w_hi, b_lo, b_hi = 12, 22, 12, 22, 3, 7
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("band")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    band_h = int(overrides.get("band_h", ctx.draw_int("band_h", b_lo, b_hi)))
    band_h = max(2, min(h - 1, band_h))
    # bg is a varied FIELD color (canonical uses non-zero bg, e.g. 5/3); it stays
    # the mode because the top (h-band_h rows) is all-bg.
    bg = int(overrides.get("bg_color", ctx.draw_color("bg_color", exclude={0})))
    band_color = int(overrides.get("band_color",
                                   ctx.draw_color("band_color", exclude={bg})))
    n_palette = int(overrides.get("palette_size", 1))
    pool = [c for c in range(0, 10) if c not in (bg, band_color)]
    rng.shuffle(pool)
    palette = [band_color] + pool[:max(0, n_palette - 1)]
    pattern = (overrides.get("texture") or overrides.get("band_pattern")
               or ctx.draw_choice("band_pattern", list(BAND_PATTERNS)))
    density = float(overrides.get("band_density",
                                  ctx.draw_rng("band_density")
                                  .uniform(0.5, 0.8)))
    g = full_grid(h, w, bg)
    _fill_band(g, pattern, h, w, band_h, palette, density, rng)
    band_count = sum(1 for r in range(h - band_h, h) for c in range(w)
                     if g[r][c] != bg)
    if band_count < (band_h * w) // 4:
        for r in range(h - band_h, h):
            g[r][0] = band_color
            g[r][w - 1] = band_color
    return g


def _fill_band(g, pattern, h, w, band_h, palette, density, rng):
    for r in range(h - band_h, h):
        for c in range(w):
            if _band_should_fill(pattern, r - (h - band_h), c, band_h, w, rng, density):
                g[r][c] = rng.choice(palette)


def _band_should_fill(pattern, br, c, band_h, w, rng, density):
    if pattern == "even_cols":
        return c % 2 == 0 and rng.random() < density + 0.2
    if pattern == "odd_cols":
        return c % 2 == 1 and rng.random() < density + 0.2
    if pattern == "halves":
        return c < w // 2
    if pattern == "thirds":
        return c % 3 != 0
    if pattern == "diagonal":
        return c == br or c == band_h - 1 - br
    if pattern == "checker":
        return (br + c) % 2 == 0
    if pattern == "frame":
        return br in (0, band_h - 1) or c in (0, w - 1)
    return rng.random() < density


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    if name == "no_band":
        return g
    if name == "full_band":
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "alternating_rows":
        for r in range(h):
            if r % 2 == 0:
                for c in range(w):
                    g[r][c] = color
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    counts: dict[int, int] = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=lambda v: (counts[v], -v))
    non_bg_rows = [r for r, row in enumerate(grid) if any(v != bg for v in row)]
    if bg == 0:
        errs.append("default modal background should be nonzero to match eval-like fields")
    if not non_bg_rows:
        return errs + ["missing patterned bottom band"]
    start = min(non_bg_rows)
    band_h = h - start
    if not (2 <= band_h < h):
        errs.append(f"band height should be in 2..h-1, got {band_h} for h={h}")
    if non_bg_rows != list(range(start, h)):
        errs.append(f"non-bg rows must form one contiguous bottom band, got {non_bg_rows}")
    for r in range(start):
        if any(v != bg for v in grid[r]):
            errs.append(f"row {r} above band is not entirely modal bg {bg}")
            break
    if not any(v != bg for r in range(start, h) for v in grid[r]):
        errs.append("bottom band contains no non-bg pattern cells")
    return errs

