"""Generator for arc_additional_puzzle_bank_volume18:E121.

Rule: three red rectangle corners imply a cyan fourth corner; the fourth
corner is filled in cyan (color 8).

Combinatorial axes (8): grid_h/w, palette_kind, missing_corner,
palette_size, position_bias, n_distinct_colors, rect_size, texture.
Degenerates: only_2_corners, all_4_corners, no_corners.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6f2e2e5221f2"
VERSION = "2.0.1"  # add executable self_check for red-corner rectangle invariants
TASK_ID = "6f2e2e5221f2"
SUMMARY = (
    "0-bg grid with: (a) exactly THREE color-2 (red) cells positioned "
    "as three corners of a rectangle (so exactly 2 distinct row values "
    "and 2 distinct col values); (b) 0-3 DECORATION cells in OTHER "
    "non-{0, 2, 8} colors that the rule preserves but ignores. Rule: "
    "find all color-2 cells. Compute rs = unique rows, cs = unique "
    "cols. corners = product rs × cs (4 candidate corner cells). "
    "The rectangle has both dimensions at least 3 cells, and may include "
    "0-4 non-{0,2,8} decoration cells away from the red corners. "
    "missing = first corner not already in pts. Set missing to 8. "
    "Output = input with the missing corner painted 8."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 3 color-2 (red) cells",
    "the 3 red cells share exactly 2 distinct rows and 2 distinct cols (so 4th corner is well-defined)",
    "rectangle height and width both ≥3 (so corners are clearly separated)",
    "0-4 decoration cells in colors NOT in {0, 2, 8}",
]

PALETTE_KINDS = ("default", "tight_rect", "wide_rect", "tall_rect")
DEGENERATE_TEXTURES = ("only_2_corners", "all_4_corners", "no_corners")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..13", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 7..13", "valid": "4..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "missing_corner": {"type": "str", "default": "rng", "valid": "rng"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "rect_size":      {"type": "str", "default": "mixed", "valid": "mixed"},
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
        w = ctx.draw_int("grid_w", 6, 8)
        n_decor = ctx.draw_int("n_decor", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 18)
        w = ctx.draw_int("grid_w", 12, 18)
        n_decor = ctx.draw_int("n_decor", 2, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        n_decor = ctx.draw_int("n_decor", 1, 2)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    r0 = rng.randint(0, h - 4)
    r1 = rng.randint(r0 + 2, h - 1)
    c0 = rng.randint(0, w - 4)
    c1 = rng.randint(c0 + 2, w - 1)
    corners = [(r0, c0), (r0, c1), (r1, c0), (r1, c1)]
    missing = rng.choice(corners)
    occupied = set()
    for r, c in corners:
        if (r, c) != missing:
            g[r][c] = 2
            occupied.add((r, c))
    # Place decorations in non-{0, 2, 8} colors at non-corner positions
    decor_colors = [1, 3, 4, 5, 6, 7, 9]
    placed = 0
    for _ in range(n_decor * 8):
        if placed >= n_decor:
            break
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if g[r][c] != 0:
            continue
        # Don't place at any of the 4 corners (would mess up corner detection logic)
        if (r, c) in [(r0, c0), (r0, c1), (r1, c0), (r1, c1)]:
            continue
        # Don't place on row r0/r1 or col c0/c1 (would add to rs/cs and break product)
        if r in (r0, r1) or c in (c0, c1):
            continue
        g[r][c] = rng.choice(decor_colors)
        placed += 1
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Default instances must contain exactly three red rectangle corners plus
    only harmless non-{0,2,8} decoration.  This catches regressions where the
    missing corner is ambiguous, already present, too close to read as a
    rectangle, or poisoned by color 8 in the input."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    reds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    if len(reds) != 3:
        errs.append(f"expected exactly 3 red corners, found {len(reds)}")
        return errs
    rs = sorted({r for r, _ in reds})
    cs = sorted({c for _, c in reds})
    if len(rs) != 2 or len(cs) != 2:
        errs.append(f"red cells do not determine a rectangle (rows={rs}, cols={cs})")
        return errs
    if rs[1] - rs[0] < 2 or cs[1] - cs[0] < 2:
        errs.append(f"rectangle is too small/ambiguous (height={rs[1]-rs[0]+1}, width={cs[1]-cs[0]+1})")
    corners = {(r, c) for r in rs for c in cs}
    redset = set(reds)
    if not redset < corners or len(corners - redset) != 1:
        errs.append(f"red cells are not exactly three of the four rectangle corners: {sorted(reds)}")
    decor = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 0 or v == 2:
                continue
            if v == 8:
                errs.append(f"input already contains color 8 at {(r, c)}; rule should write the missing corner")
            else:
                decor.append((r, c, v))
    if len(decor) > 4:
        errs.append(f"too many decoration cells ({len(decor)} > 4)")
    return errs

def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "only_2_corners":
        # only 2 red corners → 4th corner can't be inferred uniquely
        g[1][1] = 2
        g[1][6] = 2
        return g
    if name == "all_4_corners":
        # all 4 corners already red — no missing corner to fill
        g[1][1] = 2; g[1][6] = 2
        g[6][1] = 2; g[6][6] = 2
        return g
    if name == "no_corners":
        # empty grid — rule has no rectangle to complete
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    red = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    if len(red) != 3:
        return [f"expected exactly three red corner cells, got {len(red)}"]
    rows = sorted({r for r, _ in red})
    cols = sorted({c for _, c in red})
    if len(rows) != 2 or len(cols) != 2:
        return ["red cells must occupy exactly two rows and two columns"]
    if rows[1] - rows[0] < 2 or cols[1] - cols[0] < 2:
        msgs.append("rectangle corners must be separated by at least one interior row and column")
    corners = {(r, c) for r in rows for c in cols}
    missing = corners - set(red)
    if len(missing) != 1:
        msgs.append("exactly one rectangle corner must be missing")
    elif grid[next(iter(missing))[0]][next(iter(missing))[1]] != 0:
        msgs.append("the missing corner must be background before the rule paints it cyan")
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 8:
                msgs.append("input must not already contain output color 8")
            if v not in (0, 2):
                if r in rows or c in cols:
                    msgs.append("decoration cells must not lie on the inferred rectangle rows/cols")
    return msgs
