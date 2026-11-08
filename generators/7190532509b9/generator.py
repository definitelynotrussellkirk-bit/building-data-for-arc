"""Generator for puzzle c7d4e6ad.

Rule: `(rule! (lambda (g) (cellmap g (r c v) (if (= v 5) (at g r 0) v))))`.
Column 0 of each row contains a marker color; gray(5) cells anywhere
in that row get recolored to the marker (the row's col-0 value).

Combinatorial axes:
  * grid_h / grid_w        — outer canvas size
  * n_grays                — how many gray(5) cells to plant
  * gray_layout            — random / cluster / one_per_row / column /
                             diagonal / scattered
  * marker_diversity       — same / mixed / all_distinct (controls how
                             the col-0 markers vary across rows)
  * decor_palette_size     — extra cells of other colors that don't
                             change (must not be 5 or 0)
  * caller-opt-in degenerates: no_grays (rule no-op), all_grays_one_row
                               (visually trivial), col0_all_same
                               (output ambiguous with "fill with X")
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7190532509b9"
VERSION = "2.1.0"
TASK_ID = "7190532509b9"
SUMMARY = (
    "0-bg grid (h, w~5-14) "
    "where each ACTIVE ROW has at "
    "COL 0 a NON-GRAY, "
    "NON-ZERO MARKER COLOR "
    "(per-active-row marker; "
    "diversity may be same / "
    "mixed / all-distinct "
    "across rows). The "
    "remaining cells of active rows (cols "
    "1..w-1) contain 3-12 "
    "GRAY(5) CELLS placed "
    "in a chosen layout "
    "(random, cluster, "
    "one-per-row, column, "
    "diagonal, scattered) "
    "plus optional decor "
    "cells in other non-"
    "gray colors. Rule (PER-"
    "ROW RECOLOR GRAY → "
    "COL-0 MARKER): For EACH "
    "ROW r: let M = g[r][0] "
    "(the marker color). For "
    "EACH cell (r, c) with "
    "c ≥ 1: if cell value == "
    "5 (gray), RECOLOR to M. "
    "Else, keep. Col 0 "
    "stays. Inactive rows normally stay all-bg. Net: gray cells "
    "inherit each row's left-"
    "edge marker color."
)

INVARIANTS = [
    "every row containing gray(5) has a non-bg, non-gray color at column 0",
    "≥1 gray(5) cell in columns 1..w-1",
    "active rows form a few canonical-style marker bands",
]

GRAY_LAYOUTS = (
    "random", "cluster", "one_per_row", "column", "diagonal", "scattered",
)
MARKER_DIVERSITIES = ("same", "mixed", "all_distinct")
DEGENERATE_TEXTURES = ("no_grays", "all_grays_one_row", "col0_all_same")
HELPFUL_TEXTURES = GRAY_LAYOUTS

AXES = {
    "grid_h":              {"type": "int", "default": "rng 5..14",  "valid": "4..18"},
    "grid_w":              {"type": "int", "default": "rng 5..14",  "valid": "4..18"},
    "n_grays":              {"type": "int", "default": "rng 3..12", "valid": "1..30"},
    "gray_layout":         {"type": "str", "default": "rng helpful",
                            "valid": "|".join(GRAY_LAYOUTS)},
    "marker_diversity":    {"type": "str", "default": "rng same|mixed|all_distinct",
                            "valid": "|".join(MARKER_DIVERSITIES)},
    "decor_palette_size":  {"type": "int", "default": "0",          "valid": "0..6"},
    "texture":             {"type": "str", "default": "alias for gray_layout",
                            "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi, n_lo, n_hi = 5, 7, 2, 5
    elif difficulty == "hard":
        h_lo, h_hi, n_lo, n_hi = 12, 14, 8, 12
    else:
        h_lo, h_hi, n_lo, n_hi = 5, 14, 3, 10

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)

    n_grays = int(overrides.get("n_grays",
                                ctx.draw_int("n_grays", n_lo, n_hi)))
    layout = (overrides.get("texture")
              or overrides.get("gray_layout")
              or ctx.draw_choice("gray_layout", list(GRAY_LAYOUTS)))
    diversity = overrides.get(
        "marker_diversity",
        ctx.draw_choice("marker_diversity", list(MARKER_DIVERSITIES)))
    n_decor = int(overrides.get("decor_palette_size", 0))

    g = full_grid(h, w, 0)
    palette = [c for c in range(1, 10) if c != 5]
    rng.shuffle(palette)

    groups = _active_row_groups(h, rng, n_grays)
    active_rows = [r for group in groups for r in group]
    if diversity == "same":
        group_markers = [palette[0]] * len(groups)
    elif diversity == "all_distinct":
        group_markers = (palette[:len(groups)] if len(palette) >= len(groups)
                         else palette + [palette[0]] * (len(groups) - len(palette)))
    else:  # mixed
        group_markers = [rng.choice(palette) for _ in groups]
    for marker, rows in zip(group_markers, groups):
        for r in rows:
            g[r][0] = marker

    gray_positions = _gray_layout(layout, h, w, n_grays, rng, active_rows)
    # Ensure every marker row actually demonstrates the row-wise recolor.
    counts = {r: 0 for r in active_rows}
    for r, _ in gray_positions:
        if r in counts:
            counts[r] += 1
    for missing in [r for r in active_rows if counts.get(r, 0) == 0]:
        repl_idx = None
        for i, (rr, _cc) in enumerate(gray_positions):
            if counts.get(rr, 0) > 1:
                repl_idx = i
                break
        if repl_idx is None:
            gray_positions.append((missing, rng.randint(1, w - 1)))
        else:
            old_r, _old_c = gray_positions[repl_idx]
            counts[old_r] -= 1
            gray_positions[repl_idx] = (missing, rng.randint(1, w - 1))
        counts[missing] = counts.get(missing, 0) + 1
    for r, c in gray_positions:
        if c >= 1 and 0 <= r < h:  # never overwrite col 0
            g[r][c] = 5

    decor_palette = [c for c in palette if c not in set(group_markers)][:n_decor]
    if decor_palette:
        for r in active_rows:
            for c in range(1, w):
                if g[r][c] == 0 and rng.random() < 0.08:
                    g[r][c] = rng.choice(decor_palette)

    if not any(g[r][c] == 5 for r in range(h) for c in range(1, w)):
        r = active_rows[0]
        g[r][1] = 5
    return g


def _active_row_groups(h, rng, n_grays):
    """Canonical examples use a few active marker bands, not markers on every row."""
    max_active = max(2, min(h, n_grays, 8))
    max_groups = min(4, max_active, max(2, h // 3))
    n_groups = rng.randint(2, max_groups)
    total_rows = rng.randint(n_groups, max_active)
    # Start with one row per group, then distribute the remainder.
    lengths = [1] * n_groups
    for _ in range(total_rows - n_groups):
        lengths[rng.randrange(n_groups)] += 1
    needed = sum(lengths) + (n_groups - 1)
    if needed > h:
        overflow = needed - h
        for i in range(n_groups - 1, -1, -1):
            take = min(overflow, max(0, lengths[i] - 1))
            lengths[i] -= take
            overflow -= take
            if overflow == 0:
                break
    needed = sum(lengths) + (n_groups - 1)
    extra = max(0, h - needed)
    before = rng.randint(0, extra)
    after_and_between = extra - before
    gaps = [1] * (n_groups - 1) + [0]
    for _ in range(after_and_between):
        gaps[rng.randrange(len(gaps))] += 1
    groups = []
    row = before
    for i, length in enumerate(lengths):
        groups.append(list(range(row, row + length)))
        row += length + gaps[i]
    return groups


def _gray_layout(layout, h, w, n, rng, rows=None):
    rows = list(rows if rows is not None else range(h))
    if not rows:
        rows = [0]
    cells = [(r, c) for r in rows for c in range(1, w)]
    if layout == "cluster":
        cr = rng.choice(rows); cc = rng.randint(1, w - 1)
        cells.sort(key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return cells[:n]
    if layout == "one_per_row":
        out = []
        for r in rows:
            out.append((r, rng.randint(1, w - 1)))
        rest = [cell for cell in cells if cell not in out]
        rng.shuffle(rest)
        return (out + rest)[:n]
    if layout == "column":
        c = rng.randint(1, w - 1)
        col = [(r, c) for r in rows]
        rng.shuffle(col)
        rest = [cell for cell in cells if cell not in col]
        rng.shuffle(rest)
        return (col + rest)[:n]
    if layout == "diagonal":
        diag = [(r, 1 + (i % (w - 1))) for i, r in enumerate(rows)]
        rest = [cell for cell in cells if cell not in diag]
        rng.shuffle(rest)
        return (diag + rest)[:n]
    if layout == "scattered":
        sparse = [(r, c) for r in rows for c in range(1, w, 2)]
        rng.shuffle(sparse)
        rest = [cell for cell in cells if cell not in sparse]
        rng.shuffle(rest)
        return (sparse + rest)[:n]
    rng.shuffle(cells)
    return cells[:n]


def _draw_from_degenerate(name, h, w, rng):
    """Edge-case where the col-0-marker signal collapses.

    no_grays           — input has no 5s; rule is no-op (output == input).
    all_grays_one_row  — only one row has 5s; output looks like that
                          single row repeating its marker.
    col0_all_same      — every row's col-0 is the same color; output is
                          ambiguous with "fill 5 → X" (no per-row signal).
    """
    g = full_grid(h, w, 0)
    palette = [c for c in range(1, 10) if c != 5]
    rng.shuffle(palette)
    if name == "no_grays":
        for r in range(h):
            g[r][0] = rng.choice(palette)
        for r in range(h):
            for c in range(1, w):
                if rng.random() < 0.3:
                    g[r][c] = rng.choice(palette[:3])
        return g
    if name == "all_grays_one_row":
        for r in range(h):
            g[r][0] = rng.choice(palette)
        target_row = rng.randint(0, h - 1)
        for c in range(1, w):
            g[target_row][c] = 5
        return g
    if name == "col0_all_same":
        marker = palette[0]
        for r in range(h):
            g[r][0] = marker
        for r in range(h):
            for c in range(1, w):
                if rng.random() < 0.3:
                    g[r][c] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Rows containing gray(5) must have a valid col-0 marker; no gray in inactive rows."""
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    gray_rows = [r for r in range(h) if any(grid[r][c] == 5 for c in range(1, w))]
    if not gray_rows:
        errs.append("no gray(5) cell in columns 1+ found")
    for r in gray_rows:
        if grid[r][0] in (0, 5):
            errs.append(f"row {r} has gray cells but col 0 marker is {grid[r][0]}")
            break
    marker_rows = [r for r in range(h) if grid[r][0] not in (0, 5)]
    stray = sorted(set(marker_rows) - set(gray_rows))
    if stray:
        errs.append(f"marker rows without gray cells: {stray[:5]}")
    if len(set(gray_rows)) < 2:
        errs.append("fewer than two active gray rows; row-wise recolor signal is weak")
    return errs
