"""Generator for arc_puzzle_bank_21_set20_bundle:easy_p02.

Rule: sparse cells in a square grid are echoed across the
anti-diagonal.

Combinatorial axes (8): size, cell_count, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_cells, on_anti_diagonal_only, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bd8f152c0224"
# 2.1.0: widen size range (4..12 -> more output shapes) and allow source
# cells ON the anti-diagonal (r+c == n-1) which echo to themselves,
# exercising that branch of the rule. Cells still kept on/above the
# anti-diagonal to avoid same-cell colour conflicts.
VERSION = "2.2.0"  # keep on-anti branch but prevent all-on-anti degenerate; strengthen self_check
TASK_ID = "bd8f152c0224"
SUMMARY = (
    "SQUARE grid (n × n with "
    "n ∈ [6, 9]) with 3-6 "
    "NON-BG CELLS placed "
    "EXCLUSIVELY on or "
    "ABOVE the ANTI-"
    "DIAGONAL (positions "
    "(r, c) with r + c < "
    "n - 1). Cells use "
    "various non-0 colors. "
    "Rule (ECHO EACH NON-"
    "BG CELL ACROSS THE "
    "ANTI-DIAGONAL): For "
    "EACH CELL at (r, c) "
    "with value V (non-0)"
    ": PAINT its ANTI-"
    "TRANSPOSE position "
    "(n - 1 - c, n - 1 - "
    "r) with the SAME "
    "VALUE V. Cells on "
    "the anti-diagonal "
    "(where r + c == n - 1)"
    " echo to themselves. "
    "Existing cells stay. "
    "Net: the upper-anti-"
    "triangle pattern "
    "is mirrored across "
    "the anti-diagonal "
    "into an anti-"
    "transpose-symmetric "
    "grid."
)

INVARIANTS = [
    "background is 0",
    "grid is square",
    "source cells are placed on one side of the anti-diagonal to avoid conflicts",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_cells", "on_anti_diagonal_only", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "size":           {"type": "int", "default": "rng 6..9", "valid": "4..12"},
    "cell_count":     {"type": "int", "default": "rng 3..6", "valid": "1..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "true",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "anti_triangle", "valid": "anti_triangle"},
    "n_distinct_colors":{"type": "int", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the anti-diagonal echo scene.

    Normal generation may include cells *on* the anti-diagonal to exercise the
    self-echo branch, but it must also include at least one strict source cell on
    the upper/left side.  Otherwise the whole example is an identity transform
    and leaks the declared ``on_anti_diagonal_only`` degenerate.
    """
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    if h != w:
        errs.append(f"expected square grid, got {h}x{w}")
        return errs
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not cells:
        errs.append("no non-bg cells for anti-diagonal echo")
        return errs
    off_side = [(r, c) for r, c in cells if r + c > h - 1]
    if off_side:
        errs.append(f"source cells cross below anti-diagonal: {off_side[:3]}")
    if not any(r + c < h - 1 for r, c in cells):
        errs.append("all source cells lie on anti-diagonal; echo rule is identity")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        size = ctx.draw_int("size", 5, 7)
        cell_count = ctx.draw_int("cell_count", 3, 4)
    elif difficulty == "hard":
        size = ctx.draw_int("size", 10, 12)
        cell_count = ctx.draw_int("cell_count", 6, 10)
    else:
        size = ctx.draw_int("size", 6, 11)
        cell_count = ctx.draw_int("cell_count", 3, 8)
    rng = ctx.draw_rng("layout")
    grid = full_grid(size, size, 0)
    # Keep cells on or above the anti-diagonal (r + c <= n - 1) so an echo
    # never lands on a different source cell. On-anti-diagonal cells echo to
    # themselves (exercises that branch).
    candidates = [(r, c) for r in range(size) for c in range(size)
                  if r + c <= size - 1]
    rng.shuffle(candidates)
    chosen = candidates[: min(cell_count, len(candidates))]
    # Keep the useful on-anti-diagonal self-echo branch, but never let the whole
    # default sample collapse to that identity-only degenerate.
    if chosen and not any(r + c < size - 1 for r, c in chosen):
        strict = [(r, c) for r, c in candidates if r + c < size - 1]
        chosen[0] = rng.choice(strict)
    for r, c in chosen:
        grid[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return grid


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_cells":
        return g
    if name == "on_anti_diagonal_only":
        for i in range(7):
            g[i][6 - i] = 3
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(7):
                g[r][c] = 3
        return g
    return g
