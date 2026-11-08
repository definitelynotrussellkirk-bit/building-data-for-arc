"""Generator for arc_puzzle_bank_21_set22_bundle:easy_p04.

Create a sparse colored pattern strictly in the upper half of the grid.  The
Racket rule preserves that pattern and copies every nonzero cell to its
vertical mirror below the horizontal midline.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c8d8b907048d"
VERSION = "3.0.0"  # canonical-scale distribution + exact override provenance
TASK_ID = "c8d8b907048d"
RULE_HASH = "30f91a42c7e5"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A 6-9 by 8-10 zero-background grid contains 4-8 colored source cells "
    "strictly above the horizontal midline.  The source uses two or three "
    "nonzero colors, reaches both the top row and the row immediately above "
    "the midline, and leaves the entire lower half empty.  Copy each nonzero "
    "cell (r,c) to (h-1-r,c) with the same color while preserving the source."
)

INVARIANTS = [
    "background is 0",
    "there are 4-8 source cells using 2-3 nonzero colors",
    "all source cells are strictly above h//2 and the lower half is empty",
    "the pattern reaches row 0 and row h//2-1 and spans at least two columns",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw in 6..9",
        "valid": "6..9",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw in 8..10",
        "valid": "8..10",
    },
    "cell_count": {
        "type": "int",
        "default": "difficulty-aware draw in 4..8",
        "valid": "4..8",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "difficulty-aware draw in 2..3",
        "valid": "2..3",
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic upper-half source pattern.

    Every declared exact axis is drawn before layout and is realized without
    clamping or fallback.  The minimum dimensions leave at least 24 legal
    source cells, so every valid count/color combination is feasible.
    """
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 6, 9)
    w = ctx.draw_int_diff("grid_w", 8, 10)
    cell_count = ctx.draw_int_diff("cell_count", 4, 8)
    n_colors = ctx.draw_int_diff("n_distinct_colors", 2, 3)
    colors = ctx.draw_distinct_colors(
        "source_colors", n=n_colors, exclude=(0,)
    )
    rng = ctx.draw_rng("layout")

    upper_h = h // 2
    grid = full_grid(h, w, 0)

    # Two depth anchors make the reflection distance identifiable: one source
    # reaches the outer border and another reaches the row adjacent to the
    # centerline.  Distinct columns rule out a fixed-column echo shortcut.
    top_col = rng.randrange(w)
    near_mid_col = rng.randrange(w - 1)
    if near_mid_col >= top_col:
        near_mid_col += 1
    positions = [(0, top_col), (upper_h - 1, near_mid_col)]

    candidates = [
        (r, c)
        for r in range(upper_h)
        for c in range(w)
        if (r, c) not in positions
    ]
    rng.shuffle(candidates)
    positions.extend(candidates[: cell_count - len(positions)])
    rng.shuffle(positions)

    # Seed each requested color once, then distribute the remaining cells.
    assignments = list(colors)
    assignments.extend(rng.choice(colors) for _ in range(cell_count - n_colors))
    rng.shuffle(assignments)
    for (r, c), color in zip(positions, assignments):
        grid[r][c] = color
    return grid


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from a returned grid."""
    nonzero = [value for row in grid for value in row if value != 0]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "cell_count": len(nonzero),
        "n_distinct_colors": len(set(nonzero)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding teaching examples."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular and non-empty"]

    errors: list[str] = []
    h = len(grid)
    if not (6 <= h <= 9 and 8 <= w <= 10):
        errors.append(f"expected canonical-scale grid, got {h}x{w}")

    invalid = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
    ]
    if invalid:
        errors.append(f"invalid ARC colors at {invalid[:3]}")
        return errors

    upper_h = h // 2
    sources = [
        (r, c, grid[r][c])
        for r in range(upper_h)
        for c in range(w)
        if grid[r][c] != 0
    ]
    lower = [
        (r, c)
        for r in range(upper_h, h)
        for c in range(w)
        if grid[r][c] != 0
    ]
    if lower:
        errors.append(f"lower half must start empty; found {lower[:3]}")

    count = len(sources)
    if not 4 <= count <= 8:
        errors.append(f"expected 4-8 upper-half source cells, found {count}")
    colors = {value for _, _, value in sources}
    if not 2 <= len(colors) <= 3:
        errors.append(f"expected 2-3 nonzero source colors, found {len(colors)}")

    rows = {r for r, _, _ in sources}
    cols = {c for _, c, _ in sources}
    if 0 not in rows:
        errors.append("source pattern must reach the top row")
    if upper_h - 1 not in rows:
        errors.append("source pattern must reach the row above the midline")
    if len(cols) < 2:
        errors.append("source pattern must span at least two columns")

    if sources:
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        if count == (r1 - r0 + 1) * (c1 - c0 + 1):
            errors.append("source cells must not fill a solid bounding rectangle")
    return errors
