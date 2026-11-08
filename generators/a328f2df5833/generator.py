"""Generator for ARC task e872b94a.

Rule: `(rule! (lambda (g) (let ((n (length (find-0-regions g)))) (build-grid n 1 (r c) 0))))`.
Count the number of disjoint 0-regions (cells of color 0 separated
by full bars) and emit an n × 1 grid of 0s.

Combinatorial axes:
  * grid_h / grid_w        — outer canvas size
  * split_count            — how many vertical bars (cols of 5)
  * split_orientation      — vertical / horizontal / both
  * bar_color              — color of the dividing bars (canonical: 5)
  * region_decor           — what fills the 0-regions: pure_zero /
                             sparse_decoy / mixed_decoy
                             (decoy is non-bar, non-0 — should not
                             create new regions)
  * caller-opt-in degenerates: no_splits (n=1), single_cell_regions,
                               max_splits (squeeze regions to 1-cell wide)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a328f2df5833"
VERSION = "1.4.0"  # distinct 16: output is an n x 1 column of ALL ZEROS (n = bar-separated region count) -> only n varies (rule-intrinsic). Widen split counts + grid + favor 'both' (multiplicative region counts) to maximize the range of distinct n."
TASK_ID = "a328f2df5833"
SUMMARY = "Grid split by full color-5 bars (vertical and/or horizontal). Output is an n × 1 column of 0s where n = count of bar-separated 0-regions. Decoy non-bar cells inside regions do not change the count."

# Rivals: 'output is the grid' refuted by any demo (output is 1-col).
# 'output uses bar color' refuted by any demo (output is all 0).
# 'count bars instead of regions' refuted by ≥1 demo with both
# orientations (regions = (h_splits+1) × (v_splits+1) ≠ sum).
# 'count any nonzero blob' refuted by demos with decoy cells.
# 4 demos with mixed orientations + decoy textures cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "foreground bar color is 5",
    "0-regions are separated by complete bars (vertical and/or horizontal)",
    "region count fits within ARC output limits (≤ 30)",
]

SPLIT_ORIENTATIONS = ("vertical", "horizontal", "both")
REGION_DECORS = ("pure_zero", "sparse_decoy", "mixed_decoy")
DEGENERATE_TEXTURES = ("no_splits", "single_cell_regions", "max_splits")
HELPFUL_TEXTURES = SPLIT_ORIENTATIONS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 5..15", "valid": "3..22"},
    "grid_w":            {"type": "int", "default": "rng 5..15", "valid": "3..22"},
    "split_count":       {"type": "int", "default": "rng 1..5",  "valid": "1..8"},
    "split_orientation": {"type": "str", "default": "rng helpful",
                          "valid": "|".join(SPLIT_ORIENTATIONS)},
    "bar_color":         {"type": "color", "default": "5", "valid": "1..9"},
    "region_decor":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(REGION_DECORS)},
    "texture":           {"type": "str", "default": "alias for split_orientation",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    # Output is an n x 1 all-zero column (n = region count), so distinct outputs
    # are bounded by the range of achievable region counts. Widen splits + grid;
    # 'both' orientation multiplies (v+1)*(h+1) to reach high, varied counts.
    if difficulty == "easy":
        h_lo, h_hi, n_lo, n_hi = 4, 9, 1, 3
    elif difficulty == "hard":
        h_lo, h_hi, n_lo, n_hi = 16, 22, 5, 8
    else:
        h_lo, h_hi, n_lo, n_hi = 9, 18, 2, 6

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("bars")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)

    bar_color = int(overrides.get("bar_color", 5))
    n_splits = int(overrides.get("split_count",
                                 ctx.draw_int("split_count", n_lo, n_hi)))
    orientation = (overrides.get("texture")
                   or overrides.get("split_orientation")
                   or ctx.draw_choice("split_orientation", list(SPLIT_ORIENTATIONS)))
    decor = overrides.get(
        "region_decor",
        ctx.draw_choice("region_decor", list(REGION_DECORS)))

    g = full_grid(h, w, 0)

    if orientation == "vertical":
        cols = list(range(1, w - 1))
        rng.shuffle(cols)
        for c in sorted(cols[:min(n_splits, len(cols))]):
            for r in range(h):
                g[r][c] = bar_color
    elif orientation == "horizontal":
        rows = list(range(1, h - 1))
        rng.shuffle(rows)
        for r in sorted(rows[:min(n_splits, len(rows))]):
            for c in range(w):
                g[r][c] = bar_color
    else:  # both
        v = max(1, n_splits // 2)
        h_splits = max(1, n_splits - v)
        cols = list(range(1, w - 1))
        rng.shuffle(cols)
        for c in sorted(cols[:min(v, len(cols))]):
            for rr in range(h):
                g[rr][c] = bar_color
        rows = list(range(1, h - 1))
        rng.shuffle(rows)
        for rr in sorted(rows[:min(h_splits, len(rows))]):
            for c in range(w):
                g[rr][c] = bar_color

    if decor != "pure_zero":
        # Sprinkle decoy non-bar non-0 cells inside regions without changing
        # the number of 0-regions.  A previous version allowed decoys inside
        # 1-cell corridors, fragmenting the zero regions and occasionally
        # producing >30-row outputs.  Accept a decoy only when the canonical
        # region count is unchanged.
        decoy_palette = [c for c in range(1, 10) if c != bar_color]
        rate = 0.10 if decor == "sparse_decoy" else 0.25
        base_regions = _zero_region_count(g)
        for r in range(h):
            for c in range(w):
                if g[r][c] == 0 and rng.random() < rate:
                    old = g[r][c]
                    g[r][c] = rng.choice(decoy_palette)
                    if _zero_region_count(g) != base_regions:
                        g[r][c] = old
    return g


def _zero_region_count(g):
    h, w = len(g), len(g[0]) if g else 0
    seen = set()
    count = 0
    for r in range(h):
        for c in range(w):
            if g[r][c] != 0 or (r, c) in seen:
                continue
            count += 1
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and g[nr][nc] == 0 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return count


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    n = _zero_region_count(grid)
    if not (1 <= n <= 30):
        msgs.append(f"zero-region count must fit ARC output height 1..30, got {n}")
    if not any(v == 0 for row in grid for v in row):
        msgs.append("no zero cells to count")
    return msgs


def _draw_from_degenerate(name, h, w, rng):
    """Edge-case where the count-regions signal is hidden.

    no_splits           — no bars; only 1 region; output is 1 × 1 grid.
    single_cell_regions — many bars so each region is just 1 cell;
                           output is many × 1 (potentially overflows).
    max_splits          — bars at every other column; squeezes regions
                           to width 1 each.
    """
    g = full_grid(h, w, 0)
    if name == "no_splits":
        return g
    if name == "single_cell_regions":
        # Bars at cols 1, 3, 5, ... so each region is width 1.
        for c in range(1, w, 2):
            for r in range(h):
                g[r][c] = 5
        return g
    if name == "max_splits":
        # Vertical bars at cols 2 and w-3 (3 wide regions); horizontal
        # bar at row h//2 (doubles regions).
        for c in [max(1, 2), max(1, w - 3)]:
            if 0 < c < w - 1:
                for r in range(h):
                    g[r][c] = 5
        if h > 4:
            for c in range(w):
                g[h // 2][c] = 5
        return g
    return g
