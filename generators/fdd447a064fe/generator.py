"""Generator for puzzle 5521c0d9.

Rule: bar chart at bottom; each bar jumps up by its own height.

Combinatorial axes (8): grid_h/w, n_bars, bar_height_distribution,
bar_width_distribution, bar_position_bias, palette_size,
inter_bar_spacing, anchor_bottom.
Degenerates: single_bar, no_bars, equal_height_bars.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fdd447a064fe"
VERSION = "2.2.0"  # fix grid_w sampling, add shared-baseline bar self_check, and sync floating-baseline docs
TASK_ID = "fdd447a064fe"
SUMMARY = (
    "0-bg grid (h~10-18, w~10-16) "
    "with 3-5 RECTANGULAR BARS "
    "anchored at a SHARED BASELINE "
    "(a varied row, not always the "
    "bottom). Each bar has: (a) WIDTH "
    "(1-4 cells, from width_dist "
    "uniform_1/uniform_2/all_2/"
    "mixed/wide); (b) HEIGHT from "
    "height_dist (ascending/"
    "tight_spread/wide_spread/"
    "shuffled), with 2*h_b ≤ "
    "grid_h. Bars don't overlap "
    "horizontally; spacing 0-2 "
    "cells between them. Each "
    "bar uses a DISTINCT color "
    "from 1..9. Rule (JUMP EACH "
    "BAR UP BY OWN HEIGHT): for "
    "EACH BAR with height h_b "
    "at columns c0..c0+w_b-1 "
    "TRANSLATE the bar UPWARD by "
    "h_b cells — paint the bar's "
    "cells at the new top "
    "position one bar-height above "
    "its current baseline. Net: each bar "
    "doubles its vertical extent "
    "by jumping up its own "
    "height."
)

INVARIANTS = [
    "background is 0",
    ">=2 rectangular same-color bar components share a baseline row",
    "each bar height h_b has room to jump upward by h_b without clipping",
    "bars don't overlap horizontally",
    "bars use distinct colors",
]

HEIGHT_DISTS = ("ascending", "wide_spread", "tight_spread", "shuffled")
WIDTH_DISTS = ("uniform_1", "uniform_2", "mixed", "all_2", "wide")
DEGENERATE_TEXTURES = ("single_bar", "no_bars", "equal_height_bars")
HELPFUL_TEXTURES = HEIGHT_DISTS

AXES = {
    "grid_h":             {"type": "int", "default": "rng 10..18", "valid": "8..22"},
    "grid_w":             {"type": "int", "default": "rng 10..16", "valid": "8..20"},
    "n_bars":             {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "bar_height_distribution": {"type": "str", "default": "rng helpful",
                                "valid": "ascending|wide_spread|tight_spread|shuffled"},
    "bar_width_distribution": {"type": "str", "default": "rng helpful",
                               "valid": "uniform_1|uniform_2|mixed|all_2|wide"},
    "bar_position_bias":  {"type": "str", "default": "rng spread|left|center",
                           "valid": "spread|left|center"},
    "inter_bar_spacing":  {"type": "int", "default": "rng 0..2",
                           "valid": "0..3"},
    "anchor_bottom":      {"type": "bool", "default": "false (floating baseline unless overridden)",
                           "valid": "true|false"},
    "texture":            {"type": "str", "default": "alias for bar_height_distribution",
                           "valid": "ascending|wide_spread|tight_spread|shuffled|single_bar|no_bars|equal_height_bars"},
}


def _bar_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Normal samples: distinct rectangular bars on one baseline, each able to jump up by its own height."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    comps = _bar_components(grid)
    if len(comps) < 2:
        errors.append(f"expected at least 2 bar components, found {len(comps)}")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errors.append("bar colors should be distinct")
    baselines = set()
    col_spans = []
    for color, cells in comps:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        bh, bw = r2 - r1 + 1, c2 - c1 + 1
        baselines.add(r2)
        col_spans.append((c1, c2, color))
        if len(cells) != bh * bw:
            errors.append(f"color {color} is not a solid rectangle")
        if r1 - bh < 0:
            errors.append(f"color {color} would clip when jumped upward by height {bh}")
    if len(baselines) > 1:
        errors.append(f"bars do not share one baseline row: {sorted(baselines)}")
    for i, (a1, a2, ca) in enumerate(col_spans):
        for b1, b2, cb in col_spans[i + 1:]:
            if max(a1, b1) <= min(a2, b2):
                errors.append(f"bars {ca} and {cb} overlap in columns")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 8, 12, 10, 14, 2, 3
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 16, 22, 16, 20, 5, 7
    else:
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 10, 18, 10, 16, 3, 5
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_bars = int(overrides.get("n_bars",
                               ctx.draw_int("n_bars", n_lo, n_hi)))
    n_bars = max(2, min(7, n_bars))
    palette = list(ctx.draw_distinct_colors("palette",
                                            n=n_bars, exclude={0}))
    while len(palette) < n_bars:
        palette.append(palette[0])
    height_dist = (overrides.get("texture") or
                   overrides.get("bar_height_distribution")
                   or ctx.draw_choice("bar_height_distribution",
                                      list(HEIGHT_DISTS)))
    width_dist = overrides.get("bar_width_distribution",
                               ctx.draw_choice("bar_width_distribution",
                                               list(WIDTH_DISTS)))
    bias = overrides.get("bar_position_bias",
                         ctx.draw_choice("bar_position_bias",
                                         ["spread", "left", "center"]))
    spacing = int(overrides.get("inter_bar_spacing",
                                ctx.draw_int("inter_bar_spacing", 0, 2)))
    g = full_grid(h, w, 0)
    heights = _draw_heights(height_dist, n_bars, h, rng)
    widths = _draw_widths(width_dist, n_bars, rng)
    positions = _draw_positions(bias, w, n_bars, widths, spacing, rng)
    # Shared baseline for the chart, but NOT always the bottom row: the rule shifts
    # each bar up by its own height regardless of where it sits, so a floating baseline
    # is rule-valid and adds vertical-position diversity. Pick it high enough that every
    # bar's upward jump (by its height) still lands fully in-bounds.
    fit_heights = [bh for bh in heights if 2 * bh < h]
    max_bh = max(fit_heights) if fit_heights else 1
    lo = 2 * max_bh - 1
    anchor_bottom = overrides.get("anchor_bottom", False)
    if isinstance(anchor_bottom, str):
        anchor_bottom = anchor_bottom.lower() in {"1", "true", "yes"}
    base_bottom = h - 1 if anchor_bottom else (rng.randint(lo, h - 1) if lo <= h - 1 else h - 1)
    placed = 0
    for i, (start_c, bw, bh) in enumerate(zip(positions, widths, heights)):
        if start_c is None:
            continue
        if 2 * bh >= h or start_c + bw > w:
            continue
        for dr in range(bh):
            for dc in range(bw):
                rr = base_bottom - dr
                if 0 <= rr < h and 0 <= start_c + dc < w:
                    g[rr][start_c + dc] = palette[i]
        placed += 1
    if placed < 2:
        # Fallback: simple 2-bar placement
        g = full_grid(h, w, 0)
        g[h - 1][1] = palette[0]
        g[h - 1][3] = palette[1] if len(palette) > 1 else palette[0]
        g[h - 2][3] = palette[1] if len(palette) > 1 else palette[0]
    return g


def _draw_heights(dist, n, h, rng):
    max_h = h // 2 - 1
    if max_h < 1:
        return [1] * n
    if dist == "ascending":
        return [min(max_h, 1 + i) for i in range(n)]
    if dist == "tight_spread":
        base = rng.randint(1, max(1, max_h - n + 1))
        return [min(max_h, base + i) for i in range(n)]
    if dist == "wide_spread":
        return sorted([rng.randint(1, max_h) for _ in range(n)])
    return [rng.randint(1, max_h) for _ in range(n)]


def _draw_widths(dist, n, rng):
    if dist == "uniform_1":
        return [1] * n
    if dist == "uniform_2":
        return [2] * n
    if dist == "all_2":
        return [2] * n
    if dist == "wide":
        return [rng.randint(2, 4) for _ in range(n)]
    return [rng.choice([1, 2, 3]) for _ in range(n)]   # mixed


def _draw_positions(bias, w, n, widths, spacing, rng):
    total_width = sum(widths) + (n - 1) * spacing
    if total_width > w:
        return [None] * n
    if bias == "left":
        positions = []
        c = 0
        for bw in widths:
            positions.append(c)
            c += bw + spacing
        return positions
    if bias == "center":
        positions = []
        c = max(0, (w - total_width) // 2)
        for bw in widths:
            positions.append(c)
            c += bw + spacing
        return positions
    free = w - total_width
    gap = max(spacing, free // (n + 1))
    positions = []
    c = gap
    for bw in widths:
        positions.append(c)
        c += bw + max(spacing, gap)
    return positions


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    if name == "single_bar":
        for dr in range(min(3, h - 1)):
            g[h - 1 - dr][w // 2] = color
        return g
    if name == "no_bars":
        return g
    if name == "equal_height_bars":
        bh = 2
        for i, c0 in enumerate([1, 4, 7]):
            if c0 + 1 < w and i < 3:
                color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
                for dr in range(bh):
                    g[h - 1 - dr][c0] = color
        return g
    return g
