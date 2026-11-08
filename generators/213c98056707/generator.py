"""Generator for 6b:m39 — fill tallest ring with key.

Rule: pick the tallest hollow rectangle ring; fill its interior with
the lone key-cell's color; output is the cropped, filled ring.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "213c98056707"
VERSION = "1.2.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one single-occurrence color (key); >=3 distinct colors (key + rings)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not counts:
        errs.append("no non-zero cells")
        return errs
    single_occ = [c for c, n in counts.items() if n == 1]
    if len(single_occ) != 1:
        errs.append(f"expected exactly 1 single-occurrence color (key), got {len(single_occ)}")
    if len(counts) < 3:
        errs.append(f"expected >=3 distinct colors (key + >=2 rings), got {len(counts)}")
    return errs
TASK_ID = "213c98056707"
SUMMARY = "1 lone key cell + 2-3 hollow rectangle rings, distinct colors and heights."

INVARIANTS = [
    "background is 0",
    "exactly one isolated single-cell marker (the key)",
    "2-3 hollow rectangle outlines (rings), distinct colors, distinct heights",
    "rings and key are mutually non-adjacent",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rings", "no_key", "tied_heights")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 12..16", "valid": "10..18"},
    "grid_w":            {"type": "int", "default": "rng 14..18", "valid": "12..20"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "position_bias":     {"type": "str", "default": "rings_with_distinct_heights_and_key",
                          "valid": "rings_with_distinct_heights_and_key"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_rings|no_key|tied_heights"},
}


def _try_layout(h, w, rng):
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    n_rings = rng.randint(2, 3)
    palette = rng.sample([2, 3, 4, 6, 7, 8, 9], n_rings + 1)
    key_color = palette[0]
    ring_colors = palette[1:]
    heights = rng.sample([3, 4, 5, 6], n_rings)      # distinct heights
    placed = 0
    for color, rh in zip(ring_colors, heights):
        for _ in range(60):
            rw = rng.randint(3, 6)
            r0 = rng.randint(0, h - rh)
            c0 = rng.randint(0, w - rw)
            cells = []
            for c in range(c0, c0 + rw):
                cells.append((r0, c)); cells.append((r0 + rh - 1, c))
            for r in range(r0 + 1, r0 + rh - 1):
                cells.append((r, c0)); cells.append((r, c0 + rw - 1))
            bad = any((r, c) in used
                      for r in range(max(0, r0 - 1), min(h, r0 + rh + 1))
                      for c in range(max(0, c0 - 1), min(w, c0 + rw + 1)))
            if bad:
                continue
            for r, c in cells:
                g[r][c] = color
            for r in range(max(0, r0 - 1), min(h, r0 + rh + 1)):
                for c in range(max(0, c0 - 1), min(w, c0 + rw + 1)):
                    used.add((r, c))
            placed += 1; break
    if placed < n_rings:
        return None
    for _ in range(80):
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        bad = any((rr, cc) in used
                  for rr in range(max(0, r - 1), min(h, r + 2))
                  for cc in range(max(0, c - 1), min(w, c + 2)))
        if bad:
            continue
        g[r][c] = key_color
        return g
    return None


def _fallback(h, w, rng):
    """Guaranteed layout: two distinct-height rings + a far key cell."""
    g = full_grid(h, w, 0)
    key_color, ca, cb = rng.sample([2, 3, 4, 6, 7, 8, 9], 3)
    # ring A: 3x3 at (1,1)
    for c in range(1, 4):
        g[1][c] = ca; g[3][c] = ca
    g[2][1] = ca; g[2][3] = ca
    # ring B: 5x4 at rows 1..5, cols 6..9 (distinct height 5)
    for c in range(6, 10):
        g[1][c] = cb; g[5][c] = cb
    for r in range(2, 5):
        g[r][6] = cb; g[r][9] = cb
    # key: bottom-left corner, far from both rings
    g[h - 1][0] = key_color
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 13); w = ctx.draw_int("grid_w", 14, 15)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 16); w = ctx.draw_int("grid_w", 16, 18)
    else:
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 14, 18)
    rng = ctx.draw_rng("layout")
    for _outer in range(40):
        g = _try_layout(h, w, rng)
        if g is not None:
            return g
    return _fallback(h, w, rng)


def _draw_from_degenerate(name, rng):
    h, w = 13, 15
    g = full_grid(h, w, 0)
    if name == "no_rings":
        # No rings — rule has no chambers.
        g[3][4] = 4
        return g
    if name == "no_key":
        # Rings but no key cell — no fill color.
        for c in range(2, 6): g[1][c] = 2; g[5][c] = 2
        for r in range(1, 6): g[r][2] = 2; g[r][5] = 2
        for c in range(8, 12): g[7][c] = 3; g[10][c] = 3
        for r in range(7, 11): g[r][8] = 3; g[r][11] = 3
        return g
    if name == "tied_heights":
        # Two rings same 5-row height — selector ambiguous.
        for c in range(2, 6): g[1][c] = 2; g[5][c] = 2
        for r in range(1, 6): g[r][2] = 2; g[r][5] = 2
        for c in range(8, 12): g[1][c] = 3; g[5][c] = 3
        for r in range(1, 6): g[r][8] = 3; g[r][11] = 3
        g[10][7] = 4
        return g
    return g
