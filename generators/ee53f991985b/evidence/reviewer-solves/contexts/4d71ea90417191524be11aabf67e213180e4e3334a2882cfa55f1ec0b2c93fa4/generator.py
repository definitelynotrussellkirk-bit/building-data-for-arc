"""Generator for ee53f991985b — fill complete rectangular outlines.

The canonical rule fills the bounding box of each same-color component only
when that component is exactly the border of its bounding box.  Production
examples always include a connected incomplete frame so that the plausible
shortcut "fill every component bounding box" is visibly refuted.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ee53f991985b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "638445812e80"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A 0-background grid contains one or more closed rectangular outlines and "
    "at least one connected incomplete rectangular frame. Fill the full bounding "
    "box of each complete outline with its color; leave incomplete frames and "
    "other non-outline components unchanged."
)

INVARIANTS = [
    "background is 0",
    "at least one closed same-color rectangular outline has a non-empty interior",
    "generated production inputs include an incomplete-frame shortcut witness",
    "component bounding boxes do not overlap",
]

# Keep the public override surface limited to controls recoverable from pixels.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted", "valid": "7..24"},
    "grid_w": {"type": "int", "default": "difficulty-weighted", "valid": "10..28"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_BANDS = {None, "easy", "medium", "hard"}
_COLORS = tuple(range(1, 10))


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    if difficulty not in _BANDS:
        raise ValueError(f"difficulty must be one of easy/medium/hard/None, got {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"unknown override axis: {names}")
    for name, lo, hi in (("grid_h", 7, 24), ("grid_w", 10, 28)):
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _dimension_options(difficulty, sample_index):
    # The profile-floor census uses source-bound pseudo-random sample indices.
    # A residue-based canonical anchor gives every band deterministic exact
    # support while leaving most draws on broader, difficulty-scaled canvases.
    if sample_index % 4 == 0:
        return (10,), (12,), True
    if difficulty == "easy":
        return tuple(range(7, 15)), tuple(range(10, 18)), False
    if difficulty == "hard":
        return tuple(range(14, 25)), tuple(range(18, 29)), False
    return tuple(range(10, 20)), tuple(range(12, 23)), False


def _draw_outline(grid, box, color):
    row1, col1, row2, col2 = box
    for col in range(col1, col2 + 1):
        grid[row1][col] = color
        grid[row2][col] = color
    for row in range(row1, row2 + 1):
        grid[row][col1] = color
        grid[row][col2] = color


def _draw_broken_frame(grid, box, color, missing):
    row1, col1, row2, col2 = box
    if missing != "top":
        for col in range(col1, col2 + 1):
            grid[row1][col] = color
    if missing != "bottom":
        for col in range(col1, col2 + 1):
            grid[row2][col] = color
    if missing != "left":
        for row in range(row1, row2 + 1):
            grid[row][col1] = color
    if missing != "right":
        for row in range(row1, row2 + 1):
            grid[row][col2] = color


def _box_cells(box):
    row1, col1, row2, col2 = box
    return {(row, col) for row in range(row1, row2 + 1) for col in range(col1, col2 + 1)}


def _base_boxes(height, width, rng):
    """Return guaranteed disjoint boxes on the minimum 7x10 canvas."""
    split = width // 2
    left_width = split
    right_width = width - split
    positive_h = rng.randint(4, min(6, height))
    broken_h = rng.randint(4, min(6, height))
    positive_w = rng.randint(4, min(5, left_width))
    broken_w = rng.randint(4, min(5, right_width))
    positive_row = rng.randint(0, height - positive_h)
    broken_row = rng.randint(0, height - broken_h)
    positive_col = rng.randint(0, left_width - positive_w)
    broken_col = split + rng.randint(0, right_width - broken_w)
    positive = (
        positive_row,
        positive_col,
        positive_row + positive_h - 1,
        positive_col + positive_w - 1,
    )
    broken = (
        broken_row,
        broken_col,
        broken_row + broken_h - 1,
        broken_col + broken_w - 1,
    )
    if rng.randrange(2):
        positive, broken = broken, positive
    return positive, broken


def _find_available_box(height, width, reserved, rng):
    """Find one free rectangle without enumerating/shuffling the full canvas."""
    max_h = min(8, height)
    max_w = min(8, width)
    for _ in range(80):
        box_h = rng.randint(4, max_h)
        box_w = rng.randint(4, max_w)
        row1 = rng.randint(0, height - box_h)
        col1 = rng.randint(0, width - box_w)
        box = (row1, col1, row1 + box_h - 1, col1 + box_w - 1)
        if _box_cells(box).isdisjoint(reserved):
            return box
    # Deterministic fallback keeps placement complete on cramped canvases while
    # avoiding the large temporary list used by the previous implementation.
    for box_h in range(4, max_h + 1):
        for box_w in range(4, max_w + 1):
            for row1 in range(height - box_h + 1):
                for col1 in range(width - box_w + 1):
                    box = (row1, col1, row1 + box_h - 1, col1 + box_w - 1)
                    if _box_cells(box).isdisjoint(reserved):
                        return box
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height_options, width_options, canonical_anchor = _dimension_options(
        difficulty, sample_index
    )
    if "grid_h" in overrides:
        height = ctx.draw_int_strict("grid_h", 7, 24)
    else:
        height = ctx.draw_choice("grid_h", height_options)
    if "grid_w" in overrides:
        width = ctx.draw_int_strict("grid_w", 10, 28)
    else:
        width = ctx.draw_choice("grid_w", width_options)
    # Explicit dimensions are exact controls; only an unoverridden 10x12 anchor
    # is constrained to the two-color canonical profile.
    canonical_anchor = canonical_anchor and not overrides

    layout_rng = ctx.draw_rng("layout")
    colors = list(_COLORS)
    layout_rng.shuffle(colors)
    grid = full_grid(height, width, 0)
    positive_box, broken_box = _base_boxes(height, width, layout_rng)
    _draw_outline(grid, positive_box, colors.pop())
    _draw_broken_frame(
        grid,
        broken_box,
        colors.pop(),
        layout_rng.choice(("top", "bottom", "left", "right")),
    )
    reserved = _box_cells(positive_box) | _box_cells(broken_box)

    if canonical_anchor:
        return grid

    # Broader draws vary object count by difficulty, but these counts are not
    # advertised as exact controls. Failed extra placements simply stop; the
    # guaranteed positive and broken witness above remain intact.
    if difficulty == "easy":
        extra_positive = layout_rng.randint(0, 1)
        extra_negative = 0
    elif difficulty == "hard":
        extra_positive = layout_rng.randint(2, 3)
        extra_negative = layout_rng.randint(1, 2)
    else:
        extra_positive = layout_rng.randint(1, 2)
        extra_negative = layout_rng.randint(0, 1)

    plan = ["outline"] * extra_positive + ["negative"] * extra_negative
    layout_rng.shuffle(plan)
    for kind in plan:
        if not colors:
            break
        box = _find_available_box(height, width, reserved, layout_rng)
        if box is None:
            break
        color = colors.pop()
        if kind == "outline":
            _draw_outline(grid, box, color)
        elif layout_rng.randrange(3) == 0:
            row1, col1, row2, col2 = box
            for row in range(row1, row2 + 1):
                for col in range(col1, col2 + 1):
                    grid[row][col] = color
        else:
            _draw_broken_frame(
                grid,
                box,
                color,
                layout_rng.choice(("top", "bottom", "left", "right")),
            )
        reserved.update(_box_cells(box))
    return grid


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    point = (next_row, next_col)
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and point not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add(point)
                        queue.append(point)
            result.append((color, cells))
    return result


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _is_rect_outline(cells):
    row1, col1, row2, col2 = _bbox(cells)
    border = {
        (row, col)
        for row in range(row1, row2 + 1)
        for col in range(col1, col2 + 1)
        if row in (row1, row2) or col in (col1, col2)
    }
    return set(cells) == border


def _fill_selected_bboxes(grid, *, every_component):
    output = [list(row) for row in grid]
    for color, cells in _components(grid):
        if every_component or _is_rect_outline(cells):
            row1, col1, row2, col2 = _bbox(cells)
            for row in range(row1, row2 + 1):
                for col in range(col1, col2 + 1):
                    output[row][col] = color
    return output


def rule_mirror(grid):
    """Independent Python mirror of the pinned canonical Racket rule."""
    return _fill_selected_bboxes(grid, every_component=False)


def _fill_every_component_bbox(grid):
    """Plausible shortcut: omit the complete-outline predicate."""
    return _fill_selected_bboxes(grid, every_component=True)


def _has_broken_frame_witness(grid):
    try:
        return _fill_every_component_bbox(grid) != rule_mirror(grid)
    except Exception:
        return False


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def self_check(grid, *, difficulty=None, meta=None):
    issues = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid rows must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        issues.append("grid values must be integer colors 0..9")
        return issues
    height = len(grid)
    if not 7 <= height <= 24:
        issues.append(f"grid height {height} outside [7, 24]")
    if not 10 <= width <= 28:
        issues.append(f"grid width {width} outside [10, 28]")

    fillable = 0
    boxes = []
    for color, cells in _components(grid):
        box = _bbox(cells)
        boxes.append((color, box))
        if not _is_rect_outline(cells):
            continue
        row1, col1, row2, col2 = box
        if row2 - row1 < 2 or col2 - col1 < 2:
            continue
        interior = [
            (row, col)
            for row in range(row1 + 1, row2)
            for col in range(col1 + 1, col2)
        ]
        if interior and all(grid[row][col] == 0 for row, col in interior):
            fillable += 1
    if fillable == 0:
        issues.append("expected at least one closed rectangular outline with fillable interior")

    for index, (_, first) in enumerate(boxes):
        first_cells = _box_cells(first)
        for _, second in boxes[index + 1 :]:
            if not first_cells.isdisjoint(_box_cells(second)):
                issues.append("component bounding boxes must not overlap")
                return issues
    return issues


def strict_canonical_like(grid):
    return self_check(grid)


SEMANTIC_WITNESSES = {"broken_frame": _has_broken_frame_witness}
SEMANTIC_RIVALS = {"fill_every_component_bbox": _fill_every_component_bbox}
WITNESS_RIVALS = {"broken_frame": ("fill_every_component_bbox",)}
CANONICAL_SHORTCUTS = {"fill_every_component_bbox": _fill_every_component_bbox}
LESSON_COMPETITORS = {"fill_every_component_bbox": _fill_every_component_bbox}


def lesson_identifiable(demos, query):
    reasons = []
    for name, solve in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(solve(pair["input"]) == pair["output"] for pair in demos)
            changes_query = solve(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits every demonstration but changes the query")
    return reasons
