"""Generator for 984d8a3e.

Rule: rows rebuilt from left, middle, and right color counts so middle
run shares a common right edge.

Combinatorial axes (8): row_count, palette_kind, grid_w, anchor_corner,
asymmetry_force, palette_size, left_count_pattern, mid_count_pattern.
Degenerates: single_color, no_pattern, full_grid.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "18a074d140e9"
# 1.3.0: enforce the declared/modal-color invariant.  The canonical rule reads
#        mid-color as (mode g -1); the previous randomized left counts often made
#        the left color modal, so the generated boards taught a different rule.
VERSION = "1.3.0"
TASK_ID = "18a074d140e9"
SUMMARY = (
    "Rows contain three contiguous color runs: left, modal middle, right. "
    "The middle run is the global mode and its right edge varies by row; "
    "the rule preserves per-row color counts while aligning those middle "
    "runs to a common right edge."
)

INVARIANTS = [
    "the left color is the value at the top-left cell",
    "the middle color is the modal color",
    "the third non-background color is the right color",
    "each row contains contiguous left/middle/right runs with all three colors",
    "the middle run's right edge varies across rows so the rule is visibly active",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("single_color", "no_pattern", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "row_count":      {"type": "int", "default": "rng 4..6", "valid": "1..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "left_count_pattern":{"type": "str", "default": "small_random",
                       "valid": "small_random|fixed"},
    "mid_count_pattern":{"type": "str", "default": "modal_remainder",
                       "valid": "modal_remainder"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|single_color|no_pattern|full_grid"},
}


def _run_lengths(row):
    runs = []
    i = 0
    while i < len(row):
        v = row[i]
        j = i + 1
        while j < len(row) and row[j] == v:
            j += 1
        runs.append((v, j - i, i, j - 1))
        i = j
    return runs


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs

    counts = Counter(v for row in grid for v in row)
    colors = set(counts)
    if len(colors) != 3:
        errs.append(f"normal sample must use exactly 3 colors, got {sorted(colors)}")
        return errs
    left = grid[0][0]
    mid = counts.most_common(1)[0][0]
    if mid == left:
        errs.append("modal/middle color must differ from top-left/left color")
        return errs
    rights = sorted(colors - {left, mid})
    if len(rights) != 1:
        errs.append("could not identify a unique right color")
        return errs
    right = rights[0]
    if counts[mid] <= max(counts[left], counts[right]):
        errs.append("middle color is not strictly the global mode")

    mid_right_edges = []
    for r, row in enumerate(grid):
        runs = _run_lengths(row)
        if len(runs) != 3:
            errs.append(f"row {r} should have exactly three contiguous runs, got {runs}")
            continue
        values = [v for v, _, _, _ in runs]
        if values != [left, mid, right]:
            errs.append(f"row {r} runs should be left/middle/right colors, got {values}")
            continue
        if any(length <= 0 for _, length, _, _ in runs):
            errs.append(f"row {r} has an empty run")
        mid_right_edges.append(runs[1][3])
    if len(set(mid_right_edges)) < 2:
        errs.append("middle run right edge should vary across rows; otherwise alignment is hidden")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        rc_lo, rc_hi = 3, 4
    elif difficulty == "hard":
        rc_lo, rc_hi = 7, 12
    else:
        rc_lo, rc_hi = 4, 6
    rows = ctx.draw_int("row_count", rc_lo, rc_hi)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    pal = _build_palette(palette_kind, 3, rng)
    left, mid, right = pal[0], pal[1], pal[2]
    w = int(overrides.get("grid_w", 8 + rng.randint(0, 6)))

    # Keep the left/right runs small so `mid` is the strict global mode; retry
    # until at least two rows have different middle-run right edges, which makes
    # the alignment transform non-identity in the demos.
    side_hi = max(1, min(3, w // 4))
    for _attempt in range(80):
        g = full_grid(rows, w, right)
        mid_right_edges = []
        for r in range(rows):
            left_count = rng.randint(1, side_hi)
            right_count = rng.randint(1, side_hi)
            mid_count = w - left_count - right_count
            if mid_count < 2:
                # Defensive for narrow override widths.
                mid_count = 2
                right_count = max(1, w - left_count - mid_count)
            for c in range(left_count):
                g[r][c] = left
            for c in range(left_count, left_count + mid_count):
                g[r][c] = mid
            for c in range(left_count + mid_count, w):
                g[r][c] = right
            mid_right_edges.append(left_count + mid_count - 1)
        counts = Counter(v for row in g for v in row)
        if counts[mid] > max(counts[left], counts[right]) and len(set(mid_right_edges)) >= 2:
            return g

    # Deterministic fallback with visible alignment and strict modal middle.
    g = full_grid(rows, w, right)
    for r in range(rows):
        left_count = 1 + (r % side_hi)
        right_count = 1 + ((r + 1) % side_hi)
        mid_count = w - left_count - right_count
        for c in range(left_count):
            g[r][c] = left
        for c in range(left_count, left_count + mid_count):
            g[r][c] = mid
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
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    h, w = 5, 10
    if name == "single_color":
        return full_grid(h, w, 2)
    if name == "no_pattern":
        return full_grid(h, w, 0)
    if name == "full_grid":
        return full_grid(h, w, 2)
    return full_grid(h, w, 0)
