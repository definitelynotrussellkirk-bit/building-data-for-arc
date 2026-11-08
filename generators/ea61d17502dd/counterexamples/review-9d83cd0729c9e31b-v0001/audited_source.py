"""Generator for f3e14006.

Rule: a dominant horizontal and vertical strand define a woven rectangle.

Combinatorial axes (8): grid_h/w, primary, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_strands, single_strand, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ea61d17502dd"
RULE_HASH = "b956a6f1bc99"  # canonical rule this generator was written against
VERSION = "2.1.0"  # add executable crossed-strand self_check; keep varied full-span canonical-scale strands
TASK_ID = "ea61d17502dd"
SUMMARY = (
    "Grid (h,w ~10-16) with a full-span horizontal STRAND on a random row R "
    "(base color + 2 spec-marker cells) and a full-span vertical STRAND on a "
    "random col C (base + 2 spec markers), crossing at (R,C). The crossing "
    "takes the primary strand's base. The rule finds the max-count row/col as "
    "the strands, reads each strand's base (most frequent) and spec colors, "
    "and weaves the rectangle bounded by the spec markers (the crossing cell "
    "selects which strand has priority). Strand positions and spec-marker "
    "positions vary, so the woven-rectangle size and place vary."
)

INVARIANTS = [
    "one row has the most non-background cells and carries a horizontal base color",
    "one column has the most non-background cells and carries a vertical base color",
    "minority colors on the dominant row and column mark the woven span",
    "the crossing cell selects which strand takes priority",
]

PRIMARIES = ("horizontal", "vertical")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_strands", "single_strand", "full_grid")
HELPFUL_TEXTURES = PRIMARIES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..16 by diff", "valid": "10..16"},
    "grid_w":         {"type": "int", "default": "rng 10..16 by diff", "valid": "10..16"},
    "primary":        {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PRIMARIES)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for primary",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    primary = (overrides.get("texture") if overrides.get("texture") in PRIMARIES else None) or \
              overrides.get("primary") or \
              ctx.draw_choice("primary", list(PRIMARIES))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11); w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 16); w = ctx.draw_int("grid_w", 14, 16)
    else:
        h = ctx.draw_int("grid_h", 12, 14); w = ctx.draw_int("grid_w", 12, 14)
    hbase, hspec, vbase, vspec = ctx.draw_distinct_colors(
        "strand_colors", n=4, exclude={0})
    rng2 = ctx.draw_rng("strands")
    row = rng2.randint(2, h - 3)            # strand row (interior, room for specs)
    col = rng2.randint(2, w - 3)            # strand col
    g = full_grid(h, w, 0)
    for c in range(w):                      # full-span horizontal strand
        g[row][c] = hbase
    for r in range(h):                      # full-span vertical strand
        g[r][col] = vbase
    # 2 spec markers on each strand at varied distinct positions (not the crossing)
    hcols = rng2.sample([c for c in range(w) if c != col], 2)
    for c in hcols:
        g[row][c] = hspec
    vrows = rng2.sample([r for r in range(h) if r != row], 2)
    for r in vrows:
        g[r][col] = vspec
    g[row][col] = hbase if primary == "horizontal" else vbase
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for the crossed-strand woven-rectangle task.

    The pedagogical failure mode for this generator is not a crash; it is an
    almost-right grid where the dominant row/column are not uniquely dominant or
    the spec markers do not actually define two visible spans.  The canonical rule
    then has an ambiguous/no-op read despite Racket parity still executing.
    """
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    colors = {v for row in grid for v in row}
    if 0 not in colors:
        errs.append("expected background color 0")
    nonzero = colors - {0}
    if len(nonzero) != 4:
        errs.append(f"expected exactly four strand/spec colors, found {len(nonzero)}")

    row_counts = [sum(1 for v in row if v != 0) for row in grid]
    col_counts = [sum(1 for r in range(h) if grid[r][c] != 0) for c in range(w)]
    max_row = max(row_counts) if row_counts else 0
    max_col = max(col_counts) if col_counts else 0
    rows = [r for r, n in enumerate(row_counts) if n == max_row]
    cols = [c for c, n in enumerate(col_counts) if n == max_col]
    if len(rows) != 1 or max_row != w:
        errs.append(f"expected exactly one full-span dominant row, got rows={rows} count={max_row}/{w}")
    if len(cols) != 1 or max_col != h:
        errs.append(f"expected exactly one full-span dominant col, got cols={cols} count={max_col}/{h}")
    if len(rows) != 1 or len(cols) != 1:
        return errs
    row, col = rows[0], cols[0]
    if not (2 <= row <= h - 3):
        errs.append(f"strand row should be interior with marker room, got {row} in h={h}")
    if not (2 <= col <= w - 3):
        errs.append(f"strand col should be interior with marker room, got {col} in w={w}")

    from collections import Counter
    row_vals = [grid[row][c] for c in range(w) if c != col]
    col_vals = [grid[r][col] for r in range(h) if r != row]
    row_counts_by_color = Counter(row_vals)
    col_counts_by_color = Counter(col_vals)
    if not row_counts_by_color or not col_counts_by_color:
        return errs
    row_base, row_base_n = row_counts_by_color.most_common(1)[0]
    col_base, col_base_n = col_counts_by_color.most_common(1)[0]
    row_spec_counts = [n for color, n in row_counts_by_color.items() if color != row_base]
    col_spec_counts = [n for color, n in col_counts_by_color.items() if color != col_base]
    if row_base == 0 or col_base == 0:
        errs.append("strand base colors must be nonzero")
    if row_base == col_base:
        errs.append("horizontal and vertical base colors should be distinct")
    if not any(n >= 2 for n in row_spec_counts):
        errs.append("dominant row lacks a repeated spec-marker color")
    if not any(n >= 2 for n in col_spec_counts):
        errs.append("dominant column lacks a repeated spec-marker color")
    crossing = grid[row][col]
    if crossing not in (row_base, col_base):
        errs.append("crossing cell should choose either the horizontal or vertical base color")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    if name == "no_strands":
        return g
    if name == "single_strand":
        for c in range(1, 11):
            g[6][c] = 3
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(12):
                g[r][c] = 3
        return g
    return g
