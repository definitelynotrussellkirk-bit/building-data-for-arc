"""Generator for ARC task ``25bcc06211d8``: bbox-center crosses.

For every 4-connected nonzero object, clear the input and paint the full center
row and center column of that object's tight bounding box in its own colour.
When a bounding-box dimension is even, the canonical Racket rule uses the
upper/left of the two middle coordinates (integer floor).
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "25bcc06211d8"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"  # exact observable axes, canonical-safe checker, tie-break curriculum
RULE_HASH = "a677c65272a2"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

CENTER_PROFILES = ("odd", "row_tie", "column_tie", "both_ties")
SCHEDULE_PROFILES = CENTER_PROFILES

SUMMARY = (
    "Replace every distinct-colour connected object by the '+' cross spanning "
    "the center row and center column of its tight bounding box, on an otherwise "
    "zero grid. Ordinary lessons contain two or three separated irregular "
    "objects whose source cells are both removed and added by the rule. A "
    "four-slot schedule covers odd boxes plus upper/left tie-breaking for even "
    "heights and widths."
)

INVARIANTS = [
    "background is colour 0",
    "ordinary scenes contain two or three separated distinct-colour objects",
    "object bounding boxes and their output crosses do not overlap",
    "every ordinary object has source cells outside its cross and missing cross cells",
    "even bbox dimensions choose the upper/left middle coordinate by floor division",
    "the canonical Racket program is the sole output authority",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 9..12", "valid": "9..12"},
    "grid_w": {"type": "int", "default": "scheduled 9..12", "valid": "9..12"},
    "object_count": {"type": "int", "default": "scheduled 2..3", "valid": "2..3"},
    "center_profile": {
        "type": "str",
        "default": "four-slot schedule",
        "valid": "|".join(CENTER_PROFILES),
    },
}

# Every Cartesian combination of the declared domains is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

Grid = list[list[int]]
Cell = tuple[int, int]
BBox = tuple[int, int, int, int]


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({r},{c}) is not a literal ARC colour 0..9: {value!r}"
                ]
    return len(grid), width, []


def _components(grid: Grid) -> list[set[Cell]]:
    """Return 4-connected monochrome nonzero objects in reading order."""
    height = len(grid)
    width = len(grid[0]) if grid else 0
    seen: set[Cell] = set()
    result: list[set[Cell]] = []
    for sr in range(height):
        for sc in range(width):
            colour = grid[sr][sc]
            if colour == 0 or (sr, sc) in seen:
                continue
            seen.add((sr, sc))
            queue = deque([(sr, sc)])
            component = {(sr, sc)}
            while queue:
                r, c = queue.popleft()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    nxt = (nr, nc)
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and nxt not in seen
                        and grid[nr][nc] == colour
                    ):
                        seen.add(nxt)
                        component.add(nxt)
                        queue.append(nxt)
            result.append(component)
    return result


def _bbox(cells: set[Cell]) -> BBox:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_cross(cells: set[Cell], *, round_up: bool = False) -> set[Cell]:
    r1, c1, r2, c2 = _bbox(cells)
    bias = 1 if round_up else 0
    center_r = (r1 + r2 + bias) // 2
    center_c = (c1 + c2 + bias) // 2
    return (
        {(center_r, c) for c in range(c1, c2 + 1)}
        | {(r, center_c) for r in range(r1, r2 + 1)}
    )


def _paint(grid: Grid, cells: set[Cell], colour: int) -> None:
    for r, c in cells:
        grid[r][c] = colour


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror used only by tests and semantic hooks."""
    height, width, errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    output = full_grid(height, width, 0)
    for component in _components(grid):
        colour = grid[min(component)[0]][min(component)[1]]
        _paint(output, _bbox_cross(component), colour)
    return output


def _rectangles_overlap(a: BBox, b: BBox) -> bool:
    ar1, ac1, ar2, ac2 = a
    br1, bc1, br2, bc2 = b
    return not (ar2 < br1 or br2 < ar1 or ac2 < bc1 or bc2 < ac1)


def _objects_touch(grid: Grid) -> bool:
    height, width = len(grid), len(grid[0])
    for r in range(height):
        for c in range(width):
            colour = grid[r][c]
            if colour == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width:
                    other = grid[nr][nc]
                    if other != 0 and other != colour:
                        return True
    return False


def _center_profile(components: list[set[Cell]]) -> str:
    even_height = False
    even_width = False
    for component in components:
        r1, c1, r2, c2 = _bbox(component)
        even_height |= (r2 - r1 + 1) % 2 == 0
        even_width |= (c2 - c1 + 1) % 2 == 0
    if even_height and even_width:
        return "both_ties"
    if even_height:
        return "row_tie"
    if even_width:
        return "column_tie"
    return "odd"


def _analysis(grid: Any) -> dict[str, Any]:
    height, width, errors = _validate_grid(grid)
    if errors:
        return {"errors": errors, "components": [], "output": None}
    if not (5 <= height <= 30 and 5 <= width <= 30):
        errors.append(f"grid dimensions {height}x{width} outside supported 5..30")
    if not any(value == 0 for row in grid for value in row):
        errors.append("background colour 0 must be present")

    components = _components(grid)
    if not (1 <= len(components) <= 4):
        errors.append(f"expected 1..4 nonzero objects, found {len(components)}")
    if _objects_touch(grid):
        errors.append("different-colour objects must not 4-touch")

    boxes = [_bbox(component) for component in components]
    crosses = [_bbox_cross(component) for component in components]
    for index, (component, box, cross) in enumerate(zip(components, boxes, crosses)):
        r1, c1, r2, c2 = box
        one_dimensional = r1 == r2 or c1 == c2
        if component == cross:
            if not one_dimensional:
                errors.append(f"object {index} already equals a non-line target cross")
        else:
            if not component - cross:
                errors.append(f"object {index} has no source cells outside its target cross")
            if not cross - component:
                errors.append(f"object {index} already contains its full target cross")
    for left in range(len(components)):
        for right in range(left + 1, len(components)):
            if _rectangles_overlap(boxes[left], boxes[right]):
                errors.append(f"object bounding boxes {left} and {right} overlap")
            if crosses[left] & crosses[right]:
                errors.append(f"object crosses {left} and {right} overlap")

    output = None
    if not errors:
        output = rule_mirror(grid)
        if output == [list(row) for row in grid]:
            errors.append("whole scene is an identity transformation")
    return {
        "errors": sorted(set(errors)),
        "height": height,
        "width": width,
        "components": components,
        "boxes": boxes,
        "crosses": crosses,
        "output": output,
        "center_profile": _center_profile(components) if components else None,
        "palette_size": len({value for row in grid for value in row}),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical mixed scenes; reject malformed or identity lessons."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


_CANONICAL_PROFILES = {
    (9, 9, 3),
    (10, 10, 3),
    (11, 11, 3),
    (10, 11, 3),
}


def strict_canonical_like(grid) -> list[str]:
    """Empirical canonical manifold: dimensions/palette plus two objects."""
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    profile = (analysis["height"], analysis["width"], analysis["palette_size"])
    if profile not in _CANONICAL_PROFILES:
        reasons.append(f"profile {profile} is outside canonical h/w/palette profiles")
    if len(analysis["components"]) != 2:
        reasons.append("canonical inputs contain exactly two objects")
    return reasons


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe axes: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "object_count": len(analysis["components"]),
        "center_profile": analysis["center_profile"],
    }


def _identity(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _add_cross_keep_source(grid: Grid) -> Grid:
    output = [list(row) for row in grid]
    for component in _components(grid):
        colour = grid[min(component)[0]][min(component)[1]]
        _paint(output, _bbox_cross(component), colour)
    return output


def _solid_bbox_fill(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for component in _components(grid):
        colour = grid[min(component)[0]][min(component)[1]]
        r1, c1, r2, c2 = _bbox(component)
        _paint(
            output,
            {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)},
            colour,
        )
    return output


def _center_dot_only(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for component in _components(grid):
        colour = grid[min(component)[0]][min(component)[1]]
        r1, c1, r2, c2 = _bbox(component)
        output[(r1 + r2) // 2][(c1 + c2) // 2] = colour
    return output


def _round_up_cross(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for component in _components(grid):
        colour = grid[min(component)[0]][min(component)[1]]
        _paint(output, _bbox_cross(component, round_up=True), colour)
    return output


def _monochrome_cross(grid: Grid) -> Grid:
    output = rule_mirror(grid)
    colours = [value for row in output for value in row if value]
    colour = min(colours) if colours else 0
    return [[colour if value else 0 for value in row] for row in output]


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "identity": _identity,
    "add_cross_keep_source": _add_cross_keep_source,
    "solid_bbox_fill": _solid_bbox_fill,
    "center_dot_only": _center_dot_only,
    "round_up_even_center": _round_up_cross,
    "monochrome_cross": _monochrome_cross,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_and(predicate: Callable[[Grid], bool], grid: Grid) -> bool:
    return not self_check(grid) and predicate(grid)


def _replacement_visible(grid: Grid) -> bool:
    return _valid_and(lambda g: _add_cross_keep_source(g) != rule_mirror(g), grid)


def _cross_not_solid(grid: Grid) -> bool:
    return _valid_and(lambda g: _solid_bbox_fill(g) != rule_mirror(g), grid)


def _full_cross_extent(grid: Grid) -> bool:
    return _valid_and(lambda g: _center_dot_only(g) != rule_mirror(g), grid)


def _floor_tie_break_visible(grid: Grid) -> bool:
    return _valid_and(lambda g: _round_up_cross(g) != rule_mirror(g), grid)


def _object_colours_preserved(grid: Grid) -> bool:
    return _valid_and(lambda g: _monochrome_cross(g) != rule_mirror(g), grid)


SEMANTIC_WITNESSES = {
    "source_is_replaced_not_preserved": _replacement_visible,
    "bbox_cross_is_not_solid_fill": _cross_not_solid,
    "full_bbox_arms_not_center_dot": _full_cross_extent,
    "upper_left_even_tie_break": _floor_tie_break_visible,
    "each_object_keeps_its_colour": _object_colours_preserved,
}
WITNESS_RIVALS = {
    "source_is_replaced_not_preserved": ["identity", "add_cross_keep_source"],
    "bbox_cross_is_not_solid_fill": ["solid_bbox_fill"],
    "full_bbox_arms_not_center_dot": ["center_dot_only"],
    "upper_left_even_tie_break": ["round_up_even_center"],
    "each_object_keeps_its_colour": ["monochrome_cross"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named rival survives demos but changes the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos[:EXAMPLES_NEEDED]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match bbox-center crosses")
            continue
        valid_demos.append(pair)

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query must contain input and output grids")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output does not match bbox-center crosses")

    profiles = {
        observe_overrides(pair["input"])["center_profile"] for pair in valid_demos
    }
    row_tie_seen = bool(profiles & {"row_tie", "both_ties"})
    column_tie_seen = bool(profiles & {"column_tie", "both_ties"})
    if not row_tie_seen:
        reasons.append("demonstrations do not establish the upper middle row for even heights")
    if not column_tie_seen:
        reasons.append("demonstrations do not establish the left middle column for even widths")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = bool(valid_demos) and all(
            competitor(pair["input"]) == pair["output"] for pair in valid_demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four consecutive draws cover odd, row, column, and both ties."""
    del seed, difficulty
    return CENTER_PROFILES[int(sample_index) % len(CENTER_PROFILES)]


def _default_dimensions(sample_index: int, difficulty) -> tuple[int, int]:
    slot = int(sample_index) % 4
    profiles = {
        "easy": ((9, 9), (10, 10), (10, 11), (9, 9)),
        "medium": ((9, 9), (10, 10), (11, 11), (10, 11)),
        "hard": ((11, 11), (12, 12), (10, 11), (11, 11)),
    }
    return profiles.get(difficulty, profiles["medium"])[slot]


def _default_object_count(sample_index: int, difficulty) -> int:
    slot = int(sample_index) % 4
    profiles = {
        "easy": (2, 2, 2, 2),
        "medium": (2, 3, 2, 3),
        "hard": (3, 2, 3, 2),
    }
    return profiles.get(difficulty, profiles["medium"])[slot]


def _scheduled_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _scheduled_choice(ctx, overrides, label: str, default: str, options: tuple[str, ...]) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _dims_for_profile(profile: str, count: int) -> list[tuple[int, int]]:
    if profile == "odd":
        return [(3, 3)] * count
    if profile == "row_tie":
        return [(2, 3)] + [(3, 3)] * (count - 1)
    if profile == "column_tie":
        return [(3, 2)] + [(3, 3)] * (count - 1)
    if profile == "both_ties":
        return [(2, 2)] + [(3, 3)] * (count - 1)
    raise ValueError(f"unknown center profile {profile!r}")


def _transform_shape(shape: set[Cell], height: int, width: int, code: int) -> set[Cell]:
    transformed = set(shape)
    if code & 1:
        transformed = {(r, width - 1 - c) for r, c in transformed}
    if code & 2:
        transformed = {(height - 1 - r, c) for r, c in transformed}
    return transformed


def _local_shape(height: int, width: int, variant: int) -> set[Cell]:
    bases: dict[tuple[int, int], set[Cell]] = {
        (3, 3): {(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)},
        (2, 3): {(0, 0), (1, 0), (1, 1), (1, 2)},
        (3, 2): {(0, 1), (1, 1), (2, 1), (2, 0)},
        (2, 2): {(0, 0), (1, 0), (1, 1)},
    }
    transform_codes = (0, 1, 3) if (height, width) == (2, 2) else (0, 1, 2, 3)
    code = transform_codes[variant % len(transform_codes)]
    shape = _transform_shape(bases[(height, width)], height, width, code)
    cross = _bbox_cross(set(shape))
    if not (shape - cross) or not (cross - shape):
        raise RuntimeError(f"shape {height}x{width} failed two-sided edit invariant")
    return shape


def _separated(a: BBox, b: BBox) -> bool:
    ar1, ac1, ar2, ac2 = a
    br1, bc1, br2, bc2 = b
    return (
        ar2 + 1 < br1
        or br2 + 1 < ar1
        or ac2 + 1 < bc1
        or bc2 + 1 < ac1
    )


def _place_boxes(rng, height: int, width: int, dims: list[tuple[int, int]]) -> list[BBox]:
    for _ in range(2000):
        boxes: list[BBox] = []
        for box_h, box_w in dims:
            r1 = rng.randint(1, height - box_h - 1)
            c1 = rng.randint(1, width - box_w - 1)
            candidate = (r1, c1, r1 + box_h - 1, c1 + box_w - 1)
            if all(_separated(candidate, prior) for prior in boxes):
                boxes.append(candidate)
            else:
                break
        if len(boxes) == len(dims):
            return boxes

    # Deterministic fallback for the smallest 9x9 / three-object case.
    if len(dims) == 2:
        (h0, w0), (h1, w1) = dims
        boxes = [
            (1, 1, h0, w0),
            (height - h1 - 1, width - w1 - 1, height - 2, width - 2),
        ]
    else:
        (h0, w0), (h1, w1), (h2, w2) = dims
        boxes = [
            (1, 1, h0, w0),
            (1, width - w1 - 1, h1, width - 2),
            (height - h2 - 1, (width - w2) // 2, height - 2, (width - w2) // 2 + w2 - 1),
        ]
    if not all(_separated(boxes[i], boxes[j]) for i in range(len(boxes)) for j in range(i + 1, len(boxes))):
        raise RuntimeError(f"could not place separated boxes in {height}x{width}: {dims}")
    return boxes


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w = _default_dimensions(sample_index, difficulty)
    height = _scheduled_int(ctx, overrides, "grid_h", default_h, 9, 12)
    width = _scheduled_int(ctx, overrides, "grid_w", default_w, 9, 12)
    object_count = _scheduled_int(
        ctx,
        overrides,
        "object_count",
        _default_object_count(sample_index, difficulty),
        2,
        3,
    )
    center_profile = _scheduled_choice(
        ctx,
        overrides,
        "center_profile",
        schedule_profile(seed, sample_index, difficulty),
        CENTER_PROFILES,
    )

    dimensions = _dims_for_profile(center_profile, object_count)
    layout_rng = ctx.draw_rng("layout")
    boxes = _place_boxes(layout_rng, height, width, dimensions)
    colours = ctx.draw_distinct_colors("object_colours", n=object_count, exclude={0})

    grid = full_grid(height, width, 0)
    for index, ((r1, c1, _r2, _c2), (box_h, box_w), colour) in enumerate(
        zip(boxes, dimensions, colours)
    ):
        shape_rng = ctx.draw_rng(f"shape_{index}")
        local = _local_shape(box_h, box_w, shape_rng.randrange(4))
        for r, c in local:
            grid[r1 + r][c1 + c] = colour

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal construction violated self_check: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "object_count": object_count,
        "center_profile": center_profile,
    }
    if observed != expected:
        raise RuntimeError(f"observable axis mismatch: expected {expected}, observed {observed}")
    return grid


def mutation_fixtures():
    """Named malformed/rule-hiding inputs that self_check must reject."""
    blank = full_grid(9, 9, 0)

    ragged = full_grid(9, 9, 0)
    ragged[3] = ragged[3][:-1]

    bad_colour = full_grid(9, 9, 0)
    bad_colour[3][3] = 10

    identity_line = full_grid(9, 9, 0)
    identity_line[2][3] = identity_line[3][3] = identity_line[4][3] = 4

    touching = full_grid(9, 9, 0)
    touching[2][2] = touching[2][3] = touching[3][2] = 2
    touching[3][3] = touching[3][4] = touching[4][3] = 6

    full_one_colour = full_grid(9, 9, 7)

    return [
        ("blank_identity_scene", blank),
        ("ragged_grid", ragged),
        ("out_of_palette_colour", bad_colour),
        ("one_dimensional_identity_scene", identity_line),
        ("touching_overlapping_objects", touching),
        ("missing_background", full_one_colour),
    ]
