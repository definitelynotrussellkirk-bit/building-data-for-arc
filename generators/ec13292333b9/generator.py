"""Generator for arc_puzzle_bank_21_set19_s:S19_M1 — symmetric difference of two panels.

Rule: two panels of equal size separated by a vertical 9-col. Output:
8 at every cell where exactly ONE panel has a non-zero cell at that
position.

Combinatorial axes (8): grid_h, grid_w, palette_kind, panel_w,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, identical_panels, one_panel_empty.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ec13292333b9"
VERSION = "2.1.0"  # guarantee partial overlap (>=1 shared cancels + >=1 unique each side) so the XOR discriminator is always visible (was 2/60 disjoint -> XOR==OR); widen panels
TASK_ID = "ec13292333b9"
SUMMARY = (
    "Two equal-size panels (h x pw) separated by one full vertical 9-col. "
    "Each panel holds sparse non-zero cells (one color per panel; color is "
    "irrelevant to the rule). The patterns are built with GUARANTEED PARTIAL "
    "overlap: >=1 position occupied in BOTH panels (cancels) and >=1 position "
    "unique to each side (survives). Rule: split on the 9-col; output (panel "
    "size) is 8 at every position where EXACTLY ONE panel is occupied (XOR of "
    "occupancy). Partial overlap makes XOR distinguishable from OR/AND."
)

INVARIANTS = [
    "background is 0",
    "exactly one full vertical 9-col separator; two equal-size panels",
    "panels partially overlap: >=1 shared cell (cancels) and >=1 unique cell each side",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "identical_panels", "one_panel_empty")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..10 by diff", "valid": "3..10"},
    "panel_w":        {"type": "int", "default": "rng 4..8 by diff", "valid": "3..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "two_panels_with_9div",
                       "valid": "two_panels_with_9div"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_divider|identical_panels|one_panel_empty"},
}


def _grow_from(seed_cells, blocked, h, pw, rng, n_extra):
    """Grow a compact connected extension from seed_cells inside one panel."""
    grown = set()
    support = set(seed_cells)
    for _ in range(max(1, n_extra)):
        cand = {
            (r + dr, c + dc)
            for (r, c) in support | grown
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if 0 <= r + dr < h and 0 <= c + dc < pw
        }
        cand -= support
        cand -= grown
        cand -= blocked
        if not cand:
            break
        cell = rng.choice(sorted(cand))
        grown.add(cell)
    return grown


def _compact_partial_overlap(h, pw, rng):
    """Return (shared, left_only, right_only) as compact connected masks.

    Earlier versions sampled each class as independent random cells. That made
    the task look like singleton dust (many object components) while the
    canonical examples are compact panel shapes.  The shared core plus two
    small connected extensions keeps XOR/AND/OR distinguishable without
    changing the task into a scattered-cell counting problem.
    """
    rh = rng.randint(2, min(3, h))
    rw = rng.randint(1, min(3, pw))
    top = rng.randint(0, h - rh)
    left = rng.randint(0, pw - rw)
    shared = {(r, c) for r in range(top, top + rh) for c in range(left, left + rw)}
    max_extra = max(1, min(4, (h * pw - len(shared)) // 2))
    lonly = _grow_from(shared, set(), h, pw, rng, rng.randint(1, max_extra))
    ronly = _grow_from(shared, lonly, h, pw, rng, rng.randint(1, max_extra))
    if not ronly:
        # Extremely tight fallback: steal one left-only cell's neighbor if possible.
        ronly = _grow_from(shared, set(), h, pw, rng, 1) - lonly
    if not lonly or not ronly:
        # The configured panel sizes are >=4x4, so this should be unreachable;
        # keep a deterministic fallback to preserve generator totality.
        cells = [(r, c) for r in range(h) for c in range(pw) if (r, c) not in shared]
        lonly = {cells[0]}
        ronly = {cells[-1]} if cells[-1] != cells[0] else {cells[1]}
    return shared, lonly, ronly


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 5)
        pw = ctx.draw_int("panel_w", 4, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 10)
        pw = ctx.draw_int("panel_w", 6, 8)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        pw = ctx.draw_int("panel_w", 4, 6)
    w = pw * 2 + 1
    sep = pw
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][sep] = 9
    color_l, color_r = rng.sample([1, 2, 3, 4, 5, 6, 7], 2)
    # Build compact occupancy with GUARANTEED partial overlap: a shared core
    # (both panels -> cancels) and one connected extension on each side
    # (survives as 8). This matches the canonical compact-panel distribution
    # instead of teaching singleton dust.
    shared, lonly, ronly = _compact_partial_overlap(h, pw, rng)
    for (r, c) in shared:
        g[r][c] = color_l
        g[r][sep + 1 + c] = color_r
    for (r, c) in lonly:
        g[r][c] = color_l
    for (r, c) in ronly:
        g[r][sep + 1 + c] = color_r
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the normal XOR-panel instances.

    The teaching signal requires a unique full-height 9 separator, two equal
    panels, at least one overlapping occupied cell that cancels under XOR, and
    at least one left-only and right-only occupied cell that survives.
    """
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    sep_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(sep_cols) != 1:
        errs.append(f"expected exactly one full-height color-9 separator; found {len(sep_cols)}")
        return errs
    sep = sep_cols[0]
    if sep == 0 or sep == w - 1 or sep * 2 + 1 != w:
        errs.append(f"separator does not split grid into two equal non-empty panels: sep={sep}, w={w}")
        return errs
    if any(grid[r][c] == 9 for r in range(h) for c in range(w) if c != sep):
        errs.append("color 9 appears outside the separator column")
    left = {(r, c) for r in range(h) for c in range(sep) if grid[r][c] != 0}
    right = {(r, c - sep - 1) for r in range(h) for c in range(sep + 1, w) if grid[r][c] != 0}
    shared = left & right
    lonly = left - right
    ronly = right - left
    if not shared:
        errs.append("no occupied position appears in both panels, so XOR cancellation is invisible")
    if not lonly:
        errs.append("no left-only occupied position, so one surviving XOR branch is hidden")
    if not ronly:
        errs.append("no right-only occupied position, so one surviving XOR branch is hidden")
    return errs


def _draw_from_degenerate(name, rng):
    h, pw = 5, 4
    w = pw * 2 + 1
    g = full_grid(h, w, 0)
    sep = pw
    if name == "no_divider":
        # no 9-col → no panel split
        for r in range(h):
            for c in range(pw): g[r][c] = 4 if (r + c) % 3 == 0 else 0
            for c in range(sep + 1, w): g[r][c] = 6 if (r + c) % 2 == 0 else 0
        return g
    for r in range(h): g[r][sep] = 9
    if name == "identical_panels":
        # left == right → symmetric difference is empty
        for (dr, dc) in [(0, 1), (1, 2), (2, 0)]:
            g[dr][dc] = 4
            g[dr][sep + 1 + dc] = 6
        return g
    if name == "one_panel_empty":
        # one panel empty → sym-diff equals the other panel
        for (dr, dc) in [(0, 1), (1, 2), (2, 0)]:
            g[dr][dc] = 4
        return g
    return g
