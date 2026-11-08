"""Generator for puzzle 9af7a82c.

Rule: count cells per color (including 0). Sort by count desc. Output
each color as a column in a max-height grid; bars rise from top.

Combinatorial axes (8): grid_h/w, n_colors, palette_kind,
count_distribution, position_bias, anchor_corner, asymmetry_force,
include_zero.
Degenerates: monochrome, all_distinct, equal_counts.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "370e7fced412"
VERSION = "2.1.1"  # distinct-count/zero-tie guard + stronger self_check
TASK_ID = "370e7fced412"
SUMMARY = (
    "Small grid (h, w~3-6) with "
    "n_colors (3-4) DISTINCT "
    "NONZERO COLORS at random "
    "positions, each with a "
    "DISTINCT COUNT determined by "
    "a distribution (uniform_gap/"
    "increasing/decreasing/"
    "polarized/powers). All "
    "counts are < total cells; "
    "max count ≤ grid_h (so bars "
    "fit). Palette kind: warm/"
    "cool/broad/primary. Rule "
    "(COLOR-COUNT BAR CHART): "
    "COUNT cells per COLOR "
    "(including 0). SORT colors "
    "by COUNT DESCENDING. EMIT "
    "OUTPUT GRID: each SORTED "
    "COLOR becomes a VERTICAL "
    "COLUMN in the output, with "
    "a BAR rising from the TOP "
    "(top cells = the color, "
    "lower cells = 0). The BAR "
    "HEIGHT = the color's count. "
    "Output dims: max(counts) × "
    "n_colors. Net: color-count "
    "histogram emitted as a "
    "top-to-bottom bar chart."
)

INVARIANTS = [
    ">=3 distinct colors with distinct counts",
    "all counts < total cells (so no color fills entire grid)",
    "max count <= grid_h (so output bars fit)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
COUNT_DISTRIBUTIONS = ("uniform_gap", "increasing", "decreasing",
                        "polarized", "powers")
DEGENERATE_TEXTURES = ("monochrome", "all_distinct", "equal_counts")
HELPFUL_TEXTURES = COUNT_DISTRIBUTIONS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 3..6", "valid": "2..10"},
    "grid_w":            {"type": "int", "default": "rng 3..6", "valid": "2..10"},
    "n_colors":          {"type": "int", "default": "rng 3..4", "valid": "2..7"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "warm|cool|broad|primary"},
    "count_distribution":{"type": "str", "default": "rng helpful",
                          "valid": "uniform_gap|increasing|decreasing|polarized|powers"},
    "anchor_corner":     {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "asymmetry_force":   {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "include_zero":      {"type": "bool", "default": "true",
                          "valid": "true|false"},
    "texture":           {"type": "str", "default": "alias for count_distribution",
                          "valid": "uniform_gap|increasing|decreasing|polarized|powers|monochrome|all_distinct|equal_counts"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the color-count bar-chart inputs."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors: list[str] = []
    bad = sorted({v for row in grid for v in row if not (0 <= v <= 9)})
    if bad:
        errors.append(f"out-of-range colors: {bad}")
    from collections import Counter
    counts = Counter(v for row in grid for v in row)
    nonzero_colors = sorted(c for c in counts if c != 0)
    if len(nonzero_colors) < 3:
        errors.append(f"expected at least three nonzero colors, got {nonzero_colors}")
    nonzero_counts = [counts[c] for c in nonzero_colors]
    if len(nonzero_counts) != len(set(nonzero_counts)):
        errors.append(f"nonzero color counts must be distinct, got {dict((c, counts[c]) for c in nonzero_colors)}")
    if any(cnt > h for cnt in nonzero_counts):
        errors.append(f"a color count exceeds grid height {h}: {nonzero_counts}")
    if counts[0] in nonzero_counts:
        errors.append(f"background count ties a color count ({counts[0]}); sort branch is ambiguous")
    if max(counts.values()) > 30:
        errors.append(f"output bar height would exceed 30: max count {max(counts.values())}")
    if any(cnt >= h * w for cnt in nonzero_counts):
        errors.append("a nonzero color fills the whole grid")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 3, 4, 4, 6
    elif difficulty == "hard":
        # Total cells must stay small enough that the background-count bar also
        # fits within ARC's 30-row output bound.
        h_lo, h_hi, w_lo, w_hi = 5, 6, 6, 6
    else:
        h_lo, h_hi, w_lo, w_hi = 3, 6, 5, 6
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_colors = int(overrides.get("n_colors",
                                 ctx.draw_int("n_colors", 3, 4)))
    # We need strictly distinct positive counts, each <= grid height.  Cap the
    # color count by h instead of silently emitting duplicates on short grids.
    n_colors = max(3, min(min(7, h, h * w - 1), n_colors))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    distribution = (overrides.get("texture") or
                    overrides.get("count_distribution")
                    or ctx.draw_choice("count_distribution",
                                       list(COUNT_DISTRIBUTIONS)))
    palette = _build_palette(palette_kind, n_colors, rng)
    counts = _build_counts(distribution, n_colors, h, h * w, rng)
    if len(counts) != n_colors or len(set(counts)) != len(counts):
        raise ValueError(f"could not realize distinct counts: {counts}")
    if h * w - sum(counts) in set(counts):
        raise ValueError(f"background count ties a color count: bg={h*w-sum(counts)} counts={counts}")
    g = full_grid(h, w, 0)
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    idx = 0
    for color, cnt in zip(palette, counts):
        for _ in range(cnt):
            if idx >= len(cells):
                break
            r, c = cells[idx]
            idx += 1
            g[r][c] = color
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    while len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
    return pool[:n]


def _build_counts(distribution, n, max_count, total_cells, rng):
    """Return n strictly distinct positive counts, all <= max_count.

    The previous duplicate-repair loop could still emit duplicate counts for
    polarized/easy cases (for example [3, 1, 2, 1]), hiding the sort/tie branch
    that this task is supposed to teach.
    """
    max_count = max(3, max_count)
    n = max(3, min(n, max_count))
    high_desc = list(range(max_count, 0, -1))
    low_asc = list(range(1, max_count + 1))
    if distribution in ("uniform_gap", "decreasing"):
        counts = high_desc[:n]
    elif distribution == "increasing":
        counts = low_asc[:n]
    elif distribution == "polarized":
        counts = [max_count] + low_asc[:n - 1]
    elif distribution == "powers":
        counts = []
        for i in range(n):
            c = min(max_count, 2 ** i)
            while c in counts and c < max_count:
                c += 1
            while c in counts and c > 1:
                c -= 1
            counts.append(c)
        if len(set(counts)) < n:
            counts = high_desc[:n]
    else:
        counts = high_desc[:n]
    # Preserve the requested flavor but make the no-tie invariant explicit.
    seen = set()
    final = []
    for c in counts:
        if c in seen:
            for cand in high_desc:
                if cand not in seen:
                    c = cand
                    break
        seen.add(c)
        final.append(c)
    if sum(final) >= total_cells:
        # Should not happen for default grids; fail closed instead of scaling
        # into duplicate counts.
        raise ValueError("distinct counts exceed available cells")
    return final[:n]


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    if name == "monochrome":
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "all_distinct":
        cells = [(r, c) for r in range(h) for c in range(w)]
        rng.shuffle(cells)
        palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(9, len(cells)))
        for i, (r, c) in enumerate(cells):
            g[r][c] = palette[i % len(palette)]
        return g
    if name == "equal_counts":
        # Two colors with equal counts → tie in sort order
        for r in range(h):
            for c in range(w):
                g[r][c] = color if (r + c) % 2 == 0 else (color % 9) + 1
        return g
    return g
