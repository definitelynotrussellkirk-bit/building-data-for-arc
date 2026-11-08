"""Generator for arc_additional_puzzle_bank_volume20:M137.

Canonical rule: row-0 markers of color 1 select columns; col-0 markers of
color 2 select rows; paint the Cartesian product with color 3, preserving
all other input cells. Independently reproducible seed/sample_index draws.

Version 1.2.0 repairs exact-override controls and teaches preservation of
unrelated input content instead of only presenting blank interiors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1dd0439f7260"
TASK_ID = GENERATOR_ID
VERSION = "1.2.0"
SUMMARY = (
    "Border markers of colors 1 and 2 select Cartesian intersections to "
    "paint green (3); unrelated colored cells are preserved. Exact dimension, "
    "marker-count and input-color controls are honored, including degenerates."
)
INVARIANTS = [
    "ordinary: 1..6 color-1 markers on row 0 right of corner",
    "ordinary: 1..6 color-2 markers on col 0 below corner",
    "ordinary: (0,0)=0; every non-marker colored pixel is unrelated content",
]
PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_row_marks", "no_col_marks", "marks_in_corner")
HELPFUL_TEXTURES = PALETTE_KINDS
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-dependent", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "difficulty-dependent", "valid": "5..14"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "n_row_marks": {"type": "int", "default": "difficulty-dependent", "valid": "1..6; <=width-1"},
    "n_col_marks": {"type": "int", "default": "difficulty-dependent", "valid": "1..6; <=height-1"},
    "palette_size": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias": {"type": "str", "default": "row0_col0_axes", "valid": "row0_col0_axes"},
    "n_distinct_colors": {"type": "int", "default": "same as palette_size", "valid": "2..3"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {"type": "str", "default": "default", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _validated(overrides):
    extra = sorted(set(overrides) - set(AXES))
    if extra:
        raise ValueError(f"unknown override names: {extra}")
    number_ranges = {"grid_h": (5, 14), "grid_w": (5, 14),
                     "n_row_marks": (1, 6), "n_col_marks": (1, 6),
                     "palette_size": (2, 3), "n_distinct_colors": (2, 3)}
    for key, (low, high) in number_ranges.items():
        if key in overrides:
            value = overrides[key]
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{key} must be an exact integer in {low}..{high}")
    text_controls = {"palette_kind": PALETTE_KINDS,
                     "position_bias": ("row0_col0_axes",),
                     "density": ("sparse",),
                     "texture": HELPFUL_TEXTURES + DEGENERATE_TEXTURES}
    for key, options in text_controls.items():
        if key in overrides and (type(overrides[key]) is not str or overrides[key] not in options):
            raise ValueError(f"invalid {key}: {overrides[key]!r}")
    left, right = overrides.get("palette_size"), overrides.get("n_distinct_colors")
    if left is not None and right is not None and left != right:
        raise ValueError("palette_size and n_distinct_colors must agree when both supplied")
    texture = overrides.get("texture")
    if texture == "no_row_marks" and "n_row_marks" in overrides:
        raise ValueError("no_row_marks intentionally has no row-0 markers; do not request a positive exact count")
    if texture == "no_col_marks" and "n_col_marks" in overrides:
        raise ValueError("no_col_marks intentionally has no col-0 markers; do not request a positive exact count")


def _size(ctx, name, overrides, difficulty, normal, hard, easy):
    if name in overrides:
        return ctx.draw_int(name, 5, 14)
    low, high = easy if difficulty == "easy" else hard if difficulty == "hard" else normal
    return ctx.draw_int(name, low, high)


def _marks(ctx, name, overrides, n_allowed, difficulty, *, ordinary_low=1):
    if name in overrides:
        if overrides[name] > n_allowed:
            raise ValueError(f"{name} exceeds available border positions ({n_allowed})")
        return ctx.draw_int(name, 1, n_allowed)
    if difficulty == "easy":low,high = ordinary_low, min(2,n_allowed)
    elif difficulty == "hard":low,high = min(3,n_allowed),min(4,n_allowed)
    else:low,high = ordinary_low,min(4,n_allowed)
    return ctx.draw_int(name, low, high)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validated(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("invalid difficulty")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h = _size(ctx, "grid_h", overrides, difficulty, (6,10), (8,10), (6,7))
    w = _size(ctx, "grid_w", overrides, difficulty, (6,10), (8,10), (6,7))
    row_count = _marks(ctx, "n_row_marks", overrides, w-1, difficulty)
    col_count = _marks(ctx, "n_col_marks", overrides, h-1, difficulty)
    grid = full_grid(h,w,0)
    rng = ctx.draw_rng("placement")
    cols = list(range(1,w)); rng.shuffle(cols)
    rows = list(range(1,h)); rng.shuffle(rows)
    for c in cols[:row_count]:grid[0][c]=1
    for r in rows[:col_count]:grid[r][0]=2

    texture = overrides.get("texture", "default")
    if texture == "no_row_marks":
        for c in range(1,w):grid[0][c]=0
    elif texture == "no_col_marks":
        for r in range(1,h):grid[r][0]=0
    elif texture == "marks_in_corner":
        grid[0][0]=1
    # Degenerate families still honor the literal two/three input-color
    # controls. A non-border pixel supplies a missing marker color without
    # introducing a forbidden border marker in a missing-marker lesson.
    reserved_content = set()
    if texture == "no_row_marks":
        grid[1][1] = 1
        reserved_content.add((1, 1))
    elif texture == "no_col_marks":
        grid[1][1] = 2
        reserved_content.add((1, 1))

    # Border markers have fixed colors for the canonical reference. A third
    # color, when selected, is a non-marker distractor that must be preserved.
    # Both exact public color controls are aliases of the same physical count.
    requested = overrides.get("palette_size",overrides.get("n_distinct_colors"))
    if requested is None:
        count = 3 if ctx.draw_rng("content-preservation").random() < .70 else 2
    else:
        count = requested
    if count == 3:
        kind=overrides.get("palette_kind", texture if texture in PALETTE_KINDS else "default")
        content_rng=ctx.draw_rng("unrelated-content")
        if kind=="warm":color=7
        elif kind=="cool":color=8
        elif kind=="varied":color=content_rng.choice((5,6,7,8,9))
        else:color=content_rng.choice((5,6,7,8,9))
        interior=[(r,c) for r in range(1,h) for c in range(1,w) if (r,c) not in reserved_content]
        content_rng.shuffle(interior)
        n=content_rng.randint(1,min(5,max(1,(h-1)*(w-1)//7)))
        for r,c in interior[:n]:grid[r][c]=color
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or any(len(row)!=len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h,w=len(grid),len(grid[0]);errs=[]
    if not (5<=h<=14 and 5<=w<=14):errs.append("shape must be 5..14 by 5..14")
    texture=(meta or {}).get("texture","")
    if texture not in DEGENERATE_TEXTURES:
        if not any(grid[0][c]==1 for c in range(1,w)):
            errs.append("missing row-0 color-1 markers")
        if not any(grid[r][0]==2 for r in range(1,h)):
            errs.append("missing col-0 color-2 markers")
        if grid[0][0]!=0:errs.append("(0,0) must be 0")
    if any(type(cell) is not int or not 0<=cell<=9 for row in grid for cell in row):
        errs.append("colors must be exact integers 0..9")
    return errs
