"""Normalized difference of the two size-ranked objects.

The selected Racket authority sorts nonzero objects by descending cell count,
normalizes the first two to a shared top-left origin, and paints cells occupied
by the larger but not the smaller.  This generator deliberately stays in the
canonical two-object domain while teaching exact-mask subtraction,
normalization, output color, and the max-bounding-box output canvas.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9de65c6eed00"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "5c7d71fc1b03"

SUMMARY = (
    "Two separated connected objects have distinct colors and unequal sizes. "
    "Normalize both masks to the same top-left origin, remove the smaller "
    "mask's exact cells from the larger mask, and paint the remainder in the "
    "larger object's color on the maximum of their normalized bounding boxes."
)
INVARIANTS = [
    "background is 0 and every cell is an integer color 0..9",
    "exactly two separated four-connected nonzero objects in distinct colors",
    "object sizes are unequal, so the first two size-ranked objects are unambiguous",
    "the normalized larger-minus-smaller difference is nonempty",
    "all advertised controls are exact and recoverable from returned pixels",
]

AXES = {
    "grid_h": {"type": "int", "default": "schedule/difficulty mixture", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "schedule/difficulty mixture", "valid": "9..18"},
    "profile_id": {"type": "int", "default": "sample_index mod 4", "valid": "0..3"},
    "palette_id": {"type": "int", "default": "rng 0..5", "valid": "0..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (0, 1, 2, 3)
MIN_STRICT_FRAC = 1.0

# Ordered as (larger-object color, smaller-object color).  The first three
# reproduce the canonical color roles while the remaining entries broaden them.
PALETTES = ((2, 3), (5, 7), (3, 5), (8, 4), (6, 1), (9, 2))

# Each pair is (larger mask, smaller mask), already normalized.  Profile 0 is
# the canonical subset case.  Profiles 1..3 have genuine normalized overlap but
# are not subsets; profiles 2 and 3 also make the smaller bbox taller/wider than
# the larger bbox, exposing the authority's max-canvas rule.
PROFILES = {
    0: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 1)),
        ((0, 0), (0, 1)),
    ),
    1: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2), (3, 2)),
        ((0, 0), (0, 1), (1, 0), (2, 0)),
    ),
    2: (
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)),
    ),
    3: (
        ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1), (2, 2), (3, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3)),
    ),
}
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def schedule_profile(seed, sample_index, difficulty=None):
    """The semantic shape schedule is exactly periodic in sample_index."""
    return sample_index % LESSON_SCHEDULE_PERIOD


def _normalize(cells):
    cells = tuple(cells)
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _orient(cells, orientation):
    """Apply one of the eight D4 transforms and renormalize."""
    current = set(cells)
    if orientation >= 4:
        current = {(row, -col) for row, col in current}
    for _ in range(orientation % 4):
        current = {(col, -row) for row, col in current}
    return _normalize(current)


def _bbox_size(cells):
    return max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1


def _draw_int(ctx, name, low, high, preferred):
    # Difficulty affects default frequency only.  Explicit values retain the
    # full advertised domain in every band.
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, low, high)
    return ctx.draw_choice(name, tuple(preferred))


def _default_shape(profile_id, difficulty):
    if profile_id == 0:
        return (6,), (9,)
    if profile_id == 1:
        return (6,), (10,)
    if profile_id == 2:
        return (6,), (11,)
    if difficulty == "easy":
        return range(6, 9), range(9, 13)
    if difficulty == "hard":
        return range(11, 15), range(15, 19)
    return range(8, 12), range(11, 16)


def _place_pair(grid, rng, large, small, colors):
    """Constructively place both masks with at least one blank column between."""
    height, width = len(grid), len(grid[0])
    order = [(large, colors[0]), (small, colors[1])]
    if rng.randrange(2):
        order.reverse()
    (left_cells, left_color), (right_cells, right_color) = order
    left_h, left_w = _bbox_size(left_cells)
    right_h, right_w = _bbox_size(right_cells)
    slack = width - left_w - right_w - 1
    if slack < 0 or left_h > height or right_h > height:
        raise ValueError("requested grid is too small for the selected profile")
    extra_gap = rng.randint(0, slack)
    outer_slack = slack - extra_gap
    left_margin = rng.randint(0, outer_slack)
    left_origin = rng.randint(0, height - left_h), left_margin
    right_origin = (rng.randint(0, height - right_h),
                    left_margin + left_w + 1 + extra_gap)
    for cells, color, (top, col0) in (
            (left_cells, left_color, left_origin),
            (right_cells, right_color, right_origin)):
        for row, col in cells:
            grid[top + row][col0 + col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("profile_id") is not None:
        profile_id = ctx.draw_int_strict("profile_id", 0, 3)
    else:
        profile_id = ctx.draw_choice(
            "profile_id", (sample_index % LESSON_SCHEDULE_PERIOD,))
    palette_id = ctx.draw_int_strict("palette_id", 0, len(PALETTES) - 1)
    heights, widths = _default_shape(profile_id, difficulty)
    height = _draw_int(ctx, "grid_h", 6, 14, heights)
    width = _draw_int(ctx, "grid_w", 9, 18, widths)
    rng = ctx.draw_rng("geometry")
    orientation = rng.randrange(8)
    large = _orient(PROFILES[profile_id][0], orientation)
    small = _orient(PROFILES[profile_id][1], orientation)
    grid = full_grid(height, width, 0)
    _place_pair(grid, rng, large, small, PALETTES[palette_id])
    return grid


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            color = grid[start_row][start_col]
            cells = [(start_row, start_col)]
            seen.add((start_row, start_col))
            for row, col in cells:
                for dr, dc in _DIRS:
                    point = row + dr, col + dc
                    rr, cc = point
                    if (0 <= rr < height and 0 <= cc < width and point not in seen
                            and grid[rr][cc] == color):
                        seen.add(point)
                        cells.append(point)
            result.append((color, tuple(cells)))
    return result


def _ranked_objects(grid):
    return sorted(_components(grid), key=lambda item: (
        -len(item[1]), min(row for row, _ in item[1]), min(col for _, col in item[1])))


def _profile_id(large, small):
    large, small = _normalize(large), _normalize(small)
    for profile_id, (base_large, base_small) in PROFILES.items():
        for orientation in range(8):
            if (large == _orient(base_large, orientation)
                    and small == _orient(base_small, orientation)):
                return profile_id
    raise ValueError("object masks do not match an advertised profile")


def observe_overrides(grid):
    """Recover all exact controls from pixels, independently of draw metadata."""
    ranked = _ranked_objects(grid)
    if len(ranked) != 2:
        raise ValueError("expected exactly two objects")
    (large_color, large), (small_color, small) = ranked
    try:
        palette_id = PALETTES.index((large_color, small_color))
    except ValueError as exc:
        raise ValueError("object colors do not match an advertised palette") from exc
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "profile_id": _profile_id(large, small), "palette_id": palette_id}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding booleans"]
    errors = []
    if not 6 <= len(grid) <= 14 or not 9 <= width <= 18:
        errors.append("selected domain is 6..14 rows and 9..18 columns")
    parts = _components(grid)
    if len(parts) != 2:
        errors.append(f"expected exactly two connected objects, found {len(parts)}")
        return errors
    colors = [color for color, _ in parts]
    if len(set(colors)) != 2:
        errors.append("objects must have distinct colors")
    sizes = [len(cells) for _, cells in parts]
    if sizes[0] == sizes[1]:
        errors.append("object sizes must be unequal")
    first, second = (set(parts[0][1]), set(parts[1][1]))
    if any(max(abs(r1 - r2), abs(c1 - c2)) <= 1
           for r1, c1 in first for r2, c2 in second):
        errors.append("objects must be separated by at least one background cell")
    ranked = _ranked_objects(grid)
    if len(ranked) == 2:
        large = set(_normalize(ranked[0][1]))
        small = set(_normalize(ranked[1][1]))
        if not large - small:
            errors.append("normalized larger-minus-smaller difference must be nonempty")
    return errors


def strict_canonical_like(grid):
    """The selected lawful two-object manifold, including every canonical pair."""
    return self_check(grid)


def _geometry(grid):
    (large_color, large_raw), (small_color, small_raw) = _ranked_objects(grid)[:2]
    large, small = set(_normalize(large_raw)), set(_normalize(small_raw))
    large_h, large_w = _bbox_size(large)
    small_h, small_w = _bbox_size(small)
    return {"large_color": large_color, "small_color": small_color,
            "large": large, "small": small,
            "large_h": large_h, "large_w": large_w,
            "small_h": small_h, "small_w": small_w}


def _paint(cells, color, height, width):
    output = full_grid(height, width, 0)
    for row, col in cells:
        if 0 <= row < height and 0 <= col < width:
            output[row][col] = color
    return output


def _correct_output(grid):
    info = _geometry(grid)
    return _paint(info["large"] - info["small"], info["large_color"],
                  max(info["large_h"], info["small_h"]),
                  max(info["large_w"], info["small_w"]))


def _rival_no_normalization(grid):
    info = _geometry(grid)
    return _paint(info["large"], info["large_color"],
                  max(info["large_h"], info["small_h"]),
                  max(info["large_w"], info["small_w"]))


def _rival_bbox_subtraction(grid):
    info = _geometry(grid)
    remainder = {point for point in info["large"]
                 if not (point[0] < info["small_h"] and point[1] < info["small_w"])}
    return _paint(remainder, info["large_color"],
                  max(info["large_h"], info["small_h"]),
                  max(info["large_w"], info["small_w"]))


def _rival_smaller_color(grid):
    info = _geometry(grid)
    return _paint(info["large"] - info["small"], info["small_color"],
                  max(info["large_h"], info["small_h"]),
                  max(info["large_w"], info["small_w"]))


def _rival_subset_only(grid):
    info = _geometry(grid)
    remainder = info["large"] - info["small"] if info["small"] <= info["large"] else info["large"]
    return _paint(remainder, info["large_color"],
                  max(info["large_h"], info["small_h"]),
                  max(info["large_w"], info["small_w"]))


def _rival_crop_to_large(grid):
    info = _geometry(grid)
    return _paint(info["large"] - info["small"], info["large_color"],
                  info["large_h"], info["large_w"])


def _witness_overlap(grid):
    info = _geometry(grid)
    return bool(info["large"] & info["small"])


def _witness_bbox_hole(grid):
    info = _geometry(grid)
    return any(point in info["large"] and point not in info["small"]
               for point in ((row, col)
                             for row in range(info["small_h"])
                             for col in range(info["small_w"])))


def _witness_color(grid):
    info = _geometry(grid)
    return info["large_color"] != info["small_color"] and bool(info["large"] - info["small"])


def _witness_non_subset(grid):
    info = _geometry(grid)
    return bool(info["large"] & info["small"]) and not info["small"] <= info["large"]


def _witness_expanded_canvas(grid):
    info = _geometry(grid)
    return info["small_h"] > info["large_h"] or info["small_w"] > info["large_w"]


SEMANTIC_RIVALS = {
    "no_normalization": _rival_no_normalization,
    "bbox_subtraction": _rival_bbox_subtraction,
    "smaller_color": _rival_smaller_color,
    "subset_only": _rival_subset_only,
    "crop_to_large": _rival_crop_to_large,
}
SEMANTIC_WITNESSES = {
    "normalized_overlap": _witness_overlap,
    "exact_mask_not_bbox": _witness_bbox_hole,
    "larger_output_color": _witness_color,
    "non_subset_overlap": _witness_non_subset,
    "max_canvas": _witness_expanded_canvas,
}
WITNESS_RIVALS = {
    "normalized_overlap": ["no_normalization"],
    "exact_mask_not_bbox": ["bbox_subtraction"],
    "larger_output_color": ["smaller_color"],
    "non_subset_overlap": ["subset_only"],
    "max_canvas": ["crop_to_large"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# This wrong rule fits all three labeled canonical pairs because every canonical
# smaller bounding box fits within the larger one.  Profiles 2/3 refute it.
CANONICAL_SHORTCUTS = {"crop_to_large": _rival_crop_to_large}


def lesson_identifiable(demos, query):
    """Report any declared rival that fits all demonstrations but changes query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if (all(rival(pair["input"]) == pair["output"] for pair in demos)
                and rival(query["input"]) != query["output"]):
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
