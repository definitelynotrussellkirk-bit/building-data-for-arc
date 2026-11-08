"""Generator for 71e2e99645f4 — classify 3 sections by hole pattern.

Rule: 3 sections of width 4 separated by full-height color-0 columns.
Each section is filled with one non-zero color. Each section has one
of 4 hole patterns:
  - center hole (rows 1-2, cols 1-2 = 0) → output class 8
  - bottom hole (rows 2-3, cols 1-2 = 0) → output class 4
  - left-right edge holes (cols 0, 3 = 0) → output class 3
  - no holes → output class 2
Output is 3×3 grid: row i = class of section i (repeated 3 times).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "71e2e99645f4"
VERSION = "2.0.1"
TASK_ID = "71e2e99645f4"
SUMMARY = (
    "4×14 grid (h=4, w=14) with THREE 4-column sections at cols "
    "0-3, 5-8, 10-13 separated by full-height color-0 dividers at "
    "cols 4 and 9. Each section is filled with the SAME non-zero "
    "color (chosen once) and has one of 4 HOLE PATTERNS: "
    "(a) center hole (2×2 hole at center) → class 8; (b) bottom "
    "hole (2×2 hole at bottom) → class 4; (c) edge holes (left + "
    "right cols all 0) → class 3; (d) no holes → class 2. "
    "Different sections may have different patterns. Rule: "
    "classify each section's hole pattern. Output is 3×3: row i = "
    "section i's class color, repeated across the 3 columns."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "4×14 grid",
    "3 sections at cols 0-3, 5-8, 10-13 separated by color-0 dividers",
    "all sections filled with the same non-zero color",
    "each section has one of 4 hole patterns",
]

PALETTE_KINDS = ("default",)
HOLE_PATTERNS = ("center_hole", "bottom_hole", "edge_hole", "no_hole")
DEGENERATE_TEXTURES = ("no_holes", "all_holes", "full_grid")
HELPFUL_TEXTURES = HOLE_PATTERNS

AXES = {
    "section_height": {"type": "int", "default": "4", "valid": "4"},
    "fill_color":     {"type": "color", "default": "rng !0", "valid": "1..9"},
    "hole_patterns":  {"type": "list", "default": "rng per section",
                       "valid": "|".join(HOLE_PATTERNS)},
    "palette_kind":   {"type": "str", "default": "default", "valid": "default"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "n_sections":     {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: 4×14 grid; color-0 at cols 4 and 9; non-zero fill cells; skip degenerate."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    if h != 4 or w != 14:
        errs.append(f"expected 4×14 grid, got {h}×{w}")
        return errs
    for r in range(h):
        if grid[r][4] != 0:
            errs.append(f"expected divider col 4 = 0 at row {r}, got {grid[r][4]}")
            break
    for r in range(h):
        if grid[r][9] != 0:
            errs.append(f"expected divider col 9 = 0 at row {r}, got {grid[r][9]}")
            break
    nonzero = sum(1 for r in range(h) for c in range(w) if grid[r][c] != 0)
    if nonzero == 0:
        errs.append("no non-zero fill cells found")
    return errs


def _apply_pattern(g, sec_start, pattern, color):
    """Apply hole pattern to a 4-col section starting at sec_start."""
    if pattern == "center_hole":
        for dr, dc in [(1, 1), (1, 2), (2, 1), (2, 2)]:
            g[dr][sec_start + dc] = 0
    elif pattern == "bottom_hole":
        for dr, dc in [(2, 1), (2, 2), (3, 1), (3, 2)]:
            g[dr][sec_start + dc] = 0
    elif pattern == "edge_hole":
        for r in range(4):
            g[r][sec_start + 0] = 0
            g[r][sec_start + 3] = 0
    # no_hole: leave filled


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    color = int(overrides.get("fill_color",
                              ctx.draw_color("fill_color", exclude={0})))
    # Fill grid with color; then re-zero the divider columns and apply hole
    # patterns per section.
    g = full_grid(4, 14, color)
    for r in range(4):
        g[r][4] = 0
        g[r][9] = 0

    # Pick patterns per section — ensure ≥1 variety (not all identical) so
    # the output has multiple distinct rows.
    for _try in range(20):
        patterns = [rng.choice(HOLE_PATTERNS) for _ in range(3)]
        if len(set(patterns)) >= 2:
            break
    else:
        patterns = ["center_hole", "no_hole", "bottom_hole"]

    for i, pat in enumerate(patterns):
        # Reset section to fill color first
        sec_start = i * 5
        for r in range(4):
            for c in range(sec_start, sec_start + 4):
                g[r][c] = color
        _apply_pattern(g, sec_start, pat, color)
    return g


def _draw_from_degenerate(name, rng):
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    g = full_grid(4, 14, color)
    for r in range(4):
        g[r][4] = 0
        g[r][9] = 0
    if name == "no_holes":
        return g
    if name == "all_holes":
        for r in range(4):
            for c in range(14):
                g[r][c] = 0
        return g
    if name == "full_grid":
        return g
    return g
