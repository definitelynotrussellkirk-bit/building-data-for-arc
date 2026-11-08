"""Generator for arc_puzzle_bank_21_set16_s:S16_H1 — same-row/col/diag grouping matrix.

Rule: among single-cell markers, pairs sharing a row, column, or diagonal
are grouped. Output is N×N matrix marking groups.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_isolated, all_same_row, single_marker.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "151f4dc0c08f"
# 1.4.0: every ordinary draw now contains a diagonal-only relation; for n>=3
# it also contains an unrelated pair. This closes the retained row/column-only
# lesson shortcut while preserving the canonical relation rule.
VERSION = "1.4.0"
TASK_ID = "151f4dc0c08f"
SUMMARY = "3-5 single-cell markers in distinct colors at distinct positions."

INVARIANTS = [
    "background is 0",
    "2-6 single-cell markers in distinct non-zero colors at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_isolated", "all_same_row", "single_marker")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n":              {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has 2-6 single-cell markers in distinct non-zero colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not counts:
        return errors  # degenerate (single_marker) — allowed
    n_colors = len(counts)
    if n_colors < 2:
        return errors  # degenerate — allowed
    # Each color should appear exactly once (single-cell markers)
    multi = [v for v in counts.values() if v > 1]
    if multi:
        errors.append(f"some colors appear >1 times (not single-cell markers): {multi[:3]}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 7, 9)
        n = ctx.draw_int("n", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        n = ctx.draw_int("n", 5, 6)
    else:
        h = ctx.draw_int("grid_h", 6, 11)
        w = ctx.draw_int("grid_w", 7, 12)
        n = ctx.draw_int("n", 2, 6)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    positions = _sample_teaching_positions(rng, h, w, n)
    for color, (r, c) in zip(colors, positions):
        g[r][c] = color
    return g


def _related(a, b):
    r1, c1 = a; r2, c2 = b
    return r1 == r2 or c1 == c2 or abs(r1 - r2) == abs(c1 - c2)


def _relation_profile(pos):
    """Return row/column, diagonal-only, and unrelated unordered-pair counts."""
    row_col = diagonal_only = unrelated = 0
    for i in range(len(pos)):
        r1, c1 = pos[i]
        for j in range(i + 1, len(pos)):
            r2, c2 = pos[j]
            same_row_col = r1 == r2 or c1 == c2
            diagonal = abs(r1 - r2) == abs(c1 - c2)
            if same_row_col:
                row_col += 1
            elif diagonal:
                diagonal_only += 1
            else:
                unrelated += 1
    return row_col, diagonal_only, unrelated


def _teaches_relation(pos):
    # Every ordinary sample must expose the clause omitted by the retained
    # competitor: a pair related *only* by 45-degree diagonal alignment.
    # With three or more markers, retain a negative pair so the output is not
    # the all-cyan matrix. A two-marker draw can only express one pair.
    _row_col, diagonal_only, unrelated = _relation_profile(pos)
    return diagonal_only > 0 and (len(pos) == 2 or unrelated > 0)


def _fallback_positions(h, w, n):
    # The first two points form a diagonal-only pair. The third is unrelated to
    # the diagonal point (and row-aligned with the anchor), fixing both positive
    # and negative evidence before any extra markers are appended.
    pos = [(0, 0), (1, 1)]
    if n >= 3:
        pos.append((0, 3 if w > 3 else w - 1))
        if not _teaches_relation(pos):
            # All supported ordinary grids are at least 5x5, but retain a
            # deterministic bounded search rather than relying on that fact.
            pos = [(0, 0), (1, 1)]
            for r in range(h):
                for c in range(w):
                    p = (r, c)
                    if p not in pos and _teaches_relation(pos + [p]):
                        pos.append(p)
                        break
                if len(pos) == 3:
                    break
    for r in range(h):
        for c in range(w):
            if len(pos) >= n:
                return pos[:n]
            if (r, c) not in pos:
                pos.append((r, c))
    return pos[:n]


def _sample_teaching_positions(rng, h, w, n):
    cells = [(r, c) for r in range(h) for c in range(w)]
    for _ in range(1000):
        pos = rng.sample(cells, n)
        if _teaches_relation(pos):
            return pos
    return _fallback_positions(h, w, n)

def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "all_isolated":
        # markers placed so no two share row, col, or diagonal → no groups form
        g[0][1] = 3
        g[2][5] = 4
        g[5][2] = 6
        return g
    if name == "all_same_row":
        # all markers on row 3 → degenerate single row-group
        g[3][1] = 3; g[3][3] = 4; g[3][5] = 6
        return g
    if name == "single_marker":
        # only one marker → no pairs to group, output trivially identity
        g[3][4] = 5
        return g
    return g
