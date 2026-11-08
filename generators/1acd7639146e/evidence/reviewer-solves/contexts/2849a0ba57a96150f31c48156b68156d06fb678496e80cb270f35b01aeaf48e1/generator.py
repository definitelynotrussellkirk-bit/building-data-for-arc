"""Source-bound inputs for completing a rectangle from three typed corners.

The unchanged Racket authority uses color 1 as the shared corner, color 2 to
set the horizontal reach, and color 3 to set the vertical reach, then paints a
fresh color-8 rectangle outline.  This sampler keeps exactly one marker of each
type while varying all four shared-corner orientations, rectangle dimensions,
canvas dimensions, aspect ratios, and border contact.

Default lessons repeat one canonical-density profile and three joint witnesses.
Each witness simultaneously refutes four shortcuts that fit every canonical
pair: supporting only the three orientations seen canonically, refusing border-touch
cases, refusing compact rectangles, or assuming canonical near-square aspect.
Only the pinned Racket rule supplies labels; Python renderers below are finite
rivals and test diagnostics, never export authorities.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1acd7639146e"
TASK_ID = GENERATOR_ID
RULE_HASH = "695d22e3417f"
VERSION = "3.0.0"
SUMMARY = (
    "Exactly one marker each of colors 1, 2 and 3 defines an axis-aligned "
    "rectangle: 1 is the shared corner, 2 fixes its horizontal reach and 3 "
    "its vertical reach. Paint the complete outline on a fresh grid in color 8."
)

INVARIANTS = [
    "rectangular integer grid, 6..18 rows and 6..18 columns, with zero background",
    "exactly one marker of each color 1, 2 and 3 and no other nonzero input colors",
    "colors 1 and 2 share a row; colors 1 and 3 share a column",
    "rectangle height and width are independently 3..6 cells",
    "all four shared-corner orientations and both interior/border-contact placements occur",
]

AXES = {
    "grid_h": {"type": "int", "default": "profile/band draw", "valid": "6..18"},
    "grid_w": {"type": "int", "default": "profile/band draw", "valid": "6..18"},
    "rect_h": {"type": "int", "default": "profile draw", "valid": "3..6"},
    "rect_w": {"type": "int", "default": "profile draw", "valid": "3..6"},
    "orientation": {
        "type": "int",
        "default": "profile draw",
        "valid": "0..3 (TL,TR,BL,BR shared corner)",
    },
}
# Min canvas 6x6 fits every declared 3..6 by 3..6 rectangle, so all exact
# combinations are constructive in every difficulty band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("canonical", "joint_tr", "joint_bl", "joint_mixed")

# orientation -> (shared row side, shared column side), where 0 means top/left
# and 1 means bottom/right.
_ORIENTATION_SIDES = {
    0: (0, 0),  # top-left
    1: (0, 1),  # top-right
    2: (1, 0),  # bottom-left
    3: (1, 1),  # bottom-right
}
_CANONICAL_CANVASES = ((9, 10), (10, 11), (10, 12))
_CANONICAL_RECTS = ((5, 6), (6, 6))
_RICH_RECTS = {
    1: ((3, 6), (3, 5), (4, 6)),
    2: ((6, 3), (5, 3), (6, 4)),
    3: ((3, 6), (6, 3), (3, 5), (5, 3), (4, 6), (6, 4)),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic semantic schedule slot (seed-independent)."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _axis(ctx, name, lo, hi, defaults):
    """Honor exact overrides over the full declared range in every band."""
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, tuple(defaults))


def _band_canvases(difficulty):
    if difficulty == "easy":
        values = tuple(range(6, 11))
    elif difficulty == "hard":
        values = tuple(range(13, 19))
    else:
        values = tuple(range(9, 15))
    return values, values


def _placement(ctx, h, w, rect_h, rect_w, slot):
    max_top, max_left = h - rect_h, w - rect_w
    rng = ctx.draw_rng("placement")
    if slot == 0:
        # Preserve canonical interior placement whenever exact controls permit.
        top = rng.randint(1, max_top - 1) if max_top >= 2 else rng.randint(0, max_top)
        left = rng.randint(1, max_left - 1) if max_left >= 2 else rng.randint(0, max_left)
        return top, left
    if slot == 1:
        mode = ctx.draw_choice("border_mode", ("top", "left", "top_left"))
        top = 0 if mode in ("top", "top_left") else rng.randint(0, max_top)
        left = 0 if mode in ("left", "top_left") else rng.randint(0, max_left)
        return top, left
    if slot == 2:
        mode = ctx.draw_choice("border_mode", ("bottom", "right", "bottom_right"))
        top = max_top if mode in ("bottom", "bottom_right") else rng.randint(0, max_top)
        left = max_left if mode in ("right", "bottom_right") else rng.randint(0, max_left)
        return top, left
    # Every mixed slot touches a randomly chosen corner.
    return ctx.draw_choice("corner_top", (0, max_top)), ctx.draw_choice("corner_left", (0, max_left))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium or hard")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    slot = sample_index % LESSON_SCHEDULE_PERIOD
    if slot == 0:
        default_h, default_w = ctx.draw_choice("canonical_canvas", _CANONICAL_CANVASES)
        default_rect_h, default_rect_w = ctx.draw_choice("canonical_rect", _CANONICAL_RECTS)
        orientation_defaults = (0, 1, 3)
    else:
        heights, widths = _band_canvases(difficulty)
        default_h = ctx.draw_choice("profile_grid_h", heights)
        default_w = ctx.draw_choice("profile_grid_w", widths)
        default_rect_h, default_rect_w = ctx.draw_choice("profile_rect", _RICH_RECTS[slot])
        orientation_defaults = (2,)

    h = _axis(ctx, "grid_h", 6, 18, (default_h,))
    w = _axis(ctx, "grid_w", 6, 18, (default_w,))
    rect_h = _axis(ctx, "rect_h", 3, 6, (default_rect_h,))
    rect_w = _axis(ctx, "rect_w", 3, 6, (default_rect_w,))
    orientation = _axis(ctx, "orientation", 0, 3, orientation_defaults)

    top, left = _placement(ctx, h, w, rect_h, rect_w, slot)
    bottom, right = top + rect_h - 1, left + rect_w - 1
    shared_row_side, shared_col_side = _ORIENTATION_SIDES[orientation]
    shared = (bottom if shared_row_side else top, right if shared_col_side else left)
    other_h = (shared[0], left if shared_col_side else right)
    other_v = (top if shared_row_side else bottom, shared[1])

    grid = full_grid(h, w, 0)
    for (row, col), color in ((shared, 1), (other_h, 2), (other_v, 3)):
        grid[row][col] = color
    return grid


def _positions(grid):
    result = {}
    for color in (1, 2, 3):
        hits = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(hits) != 1:
            raise ValueError(f"expected exactly one color-{color} marker, found {len(hits)}")
        result[color] = hits[0]
    return result


def _geometry(grid):
    points = _positions(grid)
    r1, c1 = points[1]
    r2, c2 = points[2]
    r3, c3 = points[3]
    if r1 != r2 or c1 != c3 or r1 == r3 or c1 == c2:
        raise ValueError("markers do not form the typed L geometry")
    orientation = {
        (1, 1): 0,
        (1, -1): 1,
        (-1, 1): 2,
        (-1, -1): 3,
    }[((r3 > r1) - (r3 < r1), (c2 > c1) - (c2 < c1))]
    top, bottom = sorted((r1, r3))
    left, right = sorted((c1, c2))
    return points, top, left, bottom, right, orientation


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    _, top, left, bottom, right, orientation = _geometry(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "rect_h": bottom - top + 1,
        "rect_w": right - left + 1,
        "orientation": orientation,
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9; booleans are not colors"]
    if not 6 <= len(grid) <= 18 or not 6 <= width <= 18:
        return ["canvas must be 6..18 rows by 6..18 columns"]
    errors = []
    nonzero = {value for row in grid for value in row if value}
    if nonzero - {1, 2, 3}:
        errors.append(f"unexpected nonzero colors: {sorted(nonzero - {1, 2, 3})}")
    positions = {}
    for color in (1, 2, 3):
        hits = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(hits) != 1:
            errors.append(f"expected exactly one color-{color} marker, found {len(hits)}")
        else:
            positions[color] = hits[0]
    if len(positions) == 3:
        r1, c1 = positions[1]
        r2, c2 = positions[2]
        r3, c3 = positions[3]
        if r1 != r2:
            errors.append("colors 1 and 2 must share a row")
        if c1 != c3:
            errors.append("colors 1 and 3 must share a column")
        rect_h, rect_w = abs(r3 - r1) + 1, abs(c2 - c1) + 1
        if not 3 <= rect_h <= 6:
            errors.append(f"rectangle height {rect_h} outside 3..6")
        if not 3 <= rect_w <= 6:
            errors.append(f"rectangle width {rect_w} outside 3..6")
    return errors


def strict_canonical_like(grid):
    """The declared typed-L rule domain; canonical pairs are a subset."""
    return self_check(grid)


# ---- Deliberately incorrect finite rivals; never used as label authority. ----

def _outline(grid):
    _, top, left, bottom, right, _ = _geometry(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    for col in range(left, right + 1):
        out[top][col] = out[bottom][col] = 8
    for row in range(top, bottom + 1):
        out[row][left] = out[row][right] = 8
    return out


def _known_sides_only(grid):
    points, _, _, _, _, _ = _geometry(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    r1, c1 = points[1]
    _, c2 = points[2]
    r3, _ = points[3]
    for col in range(min(c1, c2), max(c1, c2) + 1):
        out[r1][col] = 8
    for row in range(min(r1, r3), max(r1, r3) + 1):
        out[row][c1] = 8
    return out


def _canonical_orientations_only(grid):
    """RIVAL: completes only the three shared-corner orientations seen canonically."""
    return _outline(grid) if observe_overrides(grid)["orientation"] in (0, 1, 3) else _known_sides_only(grid)


def _interior_only(grid):
    """RIVAL: assumes the rectangle never touches the canvas boundary."""
    _, top, left, bottom, right, _ = _geometry(grid)
    interior = top > 0 and left > 0 and bottom < len(grid) - 1 and right < len(grid[0]) - 1
    return _outline(grid) if interior else _known_sides_only(grid)


def _canonical_scale_only(grid):
    """RIVAL: assumes canonical rectangles are at least 5 rows by 6 columns."""
    stats = observe_overrides(grid)
    return _outline(grid) if stats["rect_h"] >= 5 and stats["rect_w"] >= 6 else _known_sides_only(grid)


def _near_square_only(grid):
    """RIVAL: assumes the canonical equal/near-equal side lengths always persist."""
    stats = observe_overrides(grid)
    return _outline(grid) if abs(stats["rect_h"] - stats["rect_w"]) <= 1 else _known_sides_only(grid)


def _unseen_orientation(grid):
    return observe_overrides(grid)["orientation"] == 2


def _border_contact(grid):
    _, top, left, bottom, right, _ = _geometry(grid)
    return top == 0 or left == 0 or bottom == len(grid) - 1 or right == len(grid[0]) - 1


def _compact(grid):
    stats = observe_overrides(grid)
    return stats["rect_h"] < 5 or stats["rect_w"] < 6


def _extreme_aspect(grid):
    stats = observe_overrides(grid)
    return abs(stats["rect_h"] - stats["rect_w"]) > 1


SEMANTIC_RIVALS = {
    "canonical_orientations_only": _canonical_orientations_only,
    "interior_only": _interior_only,
    "canonical_scale_only": _canonical_scale_only,
    "near_square_only": _near_square_only,
}
SEMANTIC_WITNESSES = {
    "unseen_bottom_left_orientation": _unseen_orientation,
    "border_contact": _border_contact,
    "compact_rectangle": _compact,
    "extreme_aspect": _extreme_aspect,
}
WITNESS_RIVALS = {
    "unseen_bottom_left_orientation": ["canonical_orientations_only"],
    "border_contact": ["interior_only"],
    "compact_rectangle": ["canonical_scale_only"],
    "extreme_aspect": ["near_square_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite declared-rival check on supplied Racket-labelled pairs."""
    return [
        f"{name} fits every demonstration but changes the query answer"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]
