"""Generator for arc_puzzle_bank_21_set24_bundle:medium_p03 — per-row gravity-left within wall segments.

Rule: walls are color 5 (typically vertical lines). Within each row,
between consecutive walls (or wall and grid edge), pack non-zero
non-wall values to the LEFT of the segment, preserving order.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "11551c46850f"
VERSION = "2.1.0"  # guarantee >=1 non-left-packed segment (random placement could be already-packed -> identity demo)
TASK_ID = "11551c46850f"

SUMMARY = (
    "Grid with VERTICAL color-5 walls (one or more full or partial "
    "color-5 columns) dividing the grid into row-segments. Each "
    "row-segment between consecutive walls (or wall and grid edge) "
    "holds some scattered non-zero non-5 values. Rule: for each row, "
    "scan left to right. Preserve color-5 cells in place. Within each "
    "segment between walls, collect all non-zero non-5 values in "
    "left-to-right order and pack them at the LEFT of the segment, "
    "filling the remainder with 0. Equivalent to per-row "
    "gravity-left within wall segments."
)

# Rivals: 'output is input' refuted by demos with non-left-aligned
# values. 'gravity-right' refuted by demos showing left alignment.
# 'sort values within segment' refuted by demos preserving left-to-
# right order. 'gravity across walls' refuted by demos where walls
# stop the pack. 'gravity down (vertical)' refuted by demos showing
# horizontal packing within rows. 'remove walls' refuted by demos
# preserving 5s. 4 demos with mixed segments (≥2 walls + ≥3 values
# per segment) pin both the per-row scope and the walls-as-barriers
# behavior.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "≥1 full vertical color-5 wall column (or partial wall blocks at consistent column)",
    "scattered non-zero values in segments — colors NOT 0 and NOT 5",
    "≥2 segments between walls/edges so the per-row pack is observable in multiple regions",
    "≥1 row has a non-trivially-packable segment (≥1 zero between non-zero values)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_values", "single_segment")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "n_walls":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "value_density":  {"type": "float", "default": "rng 0.2..0.4", "valid": "0..0.6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 9, 11)
        n_walls = ctx.draw_int("n_walls", 1, 2)
        value_density = 0.25
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 14, 18)
        n_walls = ctx.draw_int("n_walls", 3, 4)
        value_density = 0.35
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 11, 14)
        n_walls = ctx.draw_int("n_walls", 2, 3)
        value_density = 0.3
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Place vertical color-5 walls at evenly-spaced columns
    # Choose n_walls distinct columns, leaving room for ≥2 columns per
    # segment.
    seg_width = max(2, (w - n_walls) // (n_walls + 1))
    wall_cols = []
    pos = seg_width
    for _ in range(n_walls):
        if pos < w - 1:
            wall_cols.append(pos)
            pos += seg_width + 1
    # Some walls may be partial (not full column) — but for simplicity
    # use full walls.
    for wc in wall_cols:
        for r in range(h):
            g[r][wc] = 5
    # Determine segment column ranges
    segment_bounds = []
    last = -1
    for wc in wall_cols + [w]:
        seg_lo = last + 1
        seg_hi = wc - 1
        if seg_lo <= seg_hi:
            segment_bounds.append((seg_lo, seg_hi))
        last = wc
    # Sample values per row per segment
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], min(6, len([1, 2, 3, 4, 6, 7, 8, 9])))
    for r in range(h):
        for seg_lo, seg_hi in segment_bounds:
            seg_len = seg_hi - seg_lo + 1
            n_values = min(seg_len - 1, max(0, int(seg_len * value_density)))
            if n_values == 0:
                continue
            # Pick random columns within segment
            cols_in_seg = list(range(seg_lo, seg_hi + 1))
            rng.shuffle(cols_in_seg)
            chosen = cols_in_seg[:rng.randint(1, n_values + 1)]
            for c in chosen:
                g[r][c] = rng.choice(palette)
    # Guarantee the left-pack actually CHANGES the grid: if the random placement is
    # already fully left-packed (output == input, an identity demo), force one segment
    # in one row to hold a value with a 0 BEFORE it.
    if not _pack_changes(g, segment_bounds):
        wide = [s for s in segment_bounds if s[1] - s[0] >= 1]
        if wide:
            seg_lo, seg_hi = rng.choice(wide)
            r = rng.randint(0, h - 1)
            for c in range(seg_lo, seg_hi + 1):
                g[r][c] = 0
            g[r][seg_lo + 1] = rng.choice(palette)  # gap at seg_lo -> packs left
    return g


def _pack_changes(g, segment_bounds):
    """True if the per-row left-pack within wall segments would change the grid."""
    for r, row in enumerate(g):
        for seg_lo, seg_hi in segment_bounds:
            vals = [row[c] for c in range(seg_lo, seg_hi + 1) if row[c] != 0]
            packed = vals + [0] * (seg_hi - seg_lo + 1 - len(vals))
            if packed != [row[c] for c in range(seg_lo, seg_hi + 1)]:
                return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 color-5 wall and >=1 row-segment that is NOT already left-packed, so the
    per-row gravity-left pack actually changes the grid (no identity demo)."""
    errs = []
    if not any(5 in row for row in grid):
        errs.append("no color-5 wall")
    changes = False
    for row in grid:
        seg = []
        for v in list(row) + [5]:  # sentinel closes the final segment
            if v == 5:
                vals = [x for x in seg if x != 0]
                if vals + [0] * (len(seg) - len(vals)) != seg:
                    changes = True
                seg = []
            else:
                seg.append(v)
    if not changes:
        errs.append("every segment is already left-packed -> output == input")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 12
    g = full_grid(h, w, 0)
    if name == "no_walls":
        # Values but no walls — gravity-left for the whole row
        g[1][3] = 4; g[1][7] = 7
        g[3][2] = 8; g[3][9] = 6
        return g
    if name == "no_values":
        # Walls but no values — output equals input
        for r in range(h):
            g[r][3] = 5
            g[r][7] = 5
        return g
    if name == "single_segment":
        # One wall, but values only on one side
        for r in range(h):
            g[r][5] = 5
        g[1][2] = 4; g[2][3] = 7
        return g
    return g
