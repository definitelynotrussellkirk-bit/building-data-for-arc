"""Generator for 19b:hard_129 — overlay elbow paths count map.

Rule: each color with exactly 2 cells produces an elbow path between
them. Output is a per-cell overlay count: 1→2, 2→3, 3+→4, else 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, single_endpoint, no_overlap.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "570e20669e58"
VERSION = "2.1.0"  # add task-specific self_check coverage
TASK_ID = "570e20669e58"

SUMMARY = (
    "0-bg grid (h ∈ 8-13, w ∈ 9-13, by "
    "difficulty) with: N_COLORS ∈ 3-4 "
    "DISTINCT non-bg colors drawn from "
    "{1..9}, each appearing EXACTLY "
    "TWICE as ISOLATED single cells "
    "(no two non-bg cells within "
    "Chebyshev-distance 1, enforced "
    "via _too_close). Generation "
    "retries up to 40 outer attempts "
    "until all pairs placed cleanly. "
    "Rule (FOR EACH COLOR-PAIR, "
    "DRAW BOTH POSSIBLE 'ELBOW' "
    "PATHS BETWEEN ITS TWO ENDPOINTS "
    "(GO HORIZONTAL-THEN-VERTICAL "
    "OR VERTICAL-THEN-HORIZONTAL); "
    "PER CELL, COUNT HOW MANY ELBOW "
    "PATHS PASS THROUGH; OUTPUT A "
    "FRESH SAME-SIZE GRID WHERE "
    "EACH CELL'S VALUE ENCODES THE "
    "OVERLAY COUNT: 1→COLOR 2, "
    "2→COLOR 3, 3+→COLOR 4, ELSE "
    "0): For EACH color pair "
    "(p1, p2): GENERATE the 2 "
    "elbow paths between p1 and "
    "p2 (one with horizontal-then-"
    "vertical, one with vertical-"
    "then-horizontal). For EACH "
    "cell along these paths: "
    "INCREMENT its overlay count. "
    "PRODUCE output: count=0→0, "
    "count=1→2 (red), count=2→3 "
    "(green), count≥3→4 (yellow). "
    "Net: dense intersections "
    "appear in brighter colors; "
    "sparse paths in red."
)

INVARIANTS = [
    "background is 0",
    "3-4 distinct non-bg colors are present",
    "each color appears in exactly 2 isolated single cells",
    "all cells pairwise non-adjacent",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_endpoint", "no_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "isolated_color_pairs",
                       "valid": "isolated_color_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _too_close(g, r, c) -> bool:
    h, w = len(g), len(g[0])
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    rng = ctx.draw_rng("layout")
    n_colors = rng.randint(3, 4)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_colors)
    for _ in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for color in palette:
            placed = 0
            for _ in range(80):
                if placed == 2: break
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0 or _too_close(g, r, c): continue
                g[r][c] = color
                placed += 1
            if placed != 2:
                ok = False; break
        if ok:
            cnt = Counter(v for row in g for v in row if v != 0)
            if all(v == 2 for v in cnt.values()) and len(cnt) == n_colors:
                return g
    raise ValueError("could not place required color-pairs")


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Empty grid — rule has no pairs to compute elbow paths for.
        return g
    if name == "single_endpoint":
        # Color appears once — rule's "exactly 2 cells per color"
        # filter excludes; elbow path undefined.
        g[3][3] = 4
        return g
    if name == "no_overlap":
        # Multiple pairs whose elbow paths don't intersect — rule's
        # count map degenerates: no cells with count > 1.
        g[1][1] = 4; g[1][3] = 4
        g[7][6] = 6; g[7][8] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    from collections import Counter as _Counter
    counts = _Counter(v for row in grid for v in row if v != 0)
    if not (3 <= len(counts) <= 4):
        errors.append("expected 3-4 distinct non-bg colors")
    for color, n in counts.items():
        if n != 2:
            errors.append(f"color {color} should appear exactly twice")
    pts = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    for i, (r, c) in enumerate(pts):
        for rr, cc in pts[i + 1:]:
            if max(abs(r - rr), abs(c - cc)) <= 1:
                errors.append("all endpoint cells should be pairwise non-adjacent")
                return errors
    return errors
