"""Generator for the rotated-template matching task ``1d26c382ab68``.

A full maroon (9) row separates one blue (1) template above from three
same-color candidate objects below.  Exactly one candidate is a rotation of
the template and must be recolored red (2); the two distractors have the same
cell count, including a reflected copy that is deliberately *not* accepted.
"""
from __future__ import annotations

from itertools import combinations
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1d26c382ab68"
TASK_ID = "1d26c382ab68"
VERSION = "3.0.0"
RULE_HASH = "e4dd26fbc01b"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.35

SUMMARY = (
    "A 0-background grid has one full color-9 separator row. Above it is one "
    "connected color-1 template. Below it are exactly three separated, "
    "single-color candidate objects with the same cell count as the template. "
    "Exactly one candidate is the template rotated by 0/90/180/270 degrees; "
    "the other two include a reflected same-size counterexample and another "
    "near miss. Recolor only the rotational match to color 2."
)

INVARIANTS = [
    "one full color-9 row separates the template above from candidates below",
    "the template is one connected color-1 polyomino with 4 or 5 cells",
    "exactly three lower candidates share one color in 3..8 and the template's cell count",
    "exactly one lower candidate is rotation-equivalent to the template",
    "a reflected same-size distractor is preserved, so reflection is not accepted",
]

AXES = {
    "grid_h": {"type": "int", "default": "9..11", "valid": "9..11"},
    "grid_w": {"type": "int", "default": "grid_h+2", "valid": "11..13"},
    "candidate_color": {
        "type": "color",
        "default": "weighted toward canonical color 8",
        "valid": "3..8",
    },
    "template_cells": {"type": "int", "default": "4..5", "valid": "4..5"},
    "match_slot": {"type": "int", "default": "sample_index mod 3", "valid": "0..2"},
    "match_rotation": {
        "type": "enum",
        "default": "sample_index mod 4",
        "valid": ["0", "90", "180", "270"],
    },
}

_CANDIDATE_COLOR_OPTIONS = (8, 8, 8, 8, 8, 8, 3, 4, 5, 6, 7)
_ROTATION_LABELS = ("0", "90", "180", "270")

Shape = tuple[tuple[int, int], ...]


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(cells)
    minimum_row = min(row for row, _col in cells)
    minimum_col = min(col for _row, col in cells)
    return tuple(sorted(
        (row - minimum_row, col - minimum_col)
        for row, col in cells
    ))


def _rotate_cw(shape: Shape) -> Shape:
    return _normalize((col, -row) for row, col in shape)


def _rotate(shape: Shape, turns: int) -> Shape:
    result = _normalize(shape)
    for _ in range(turns % 4):
        result = _rotate_cw(result)
    return result


def _rotations(shape: Shape) -> tuple[Shape, ...]:
    return tuple(_rotate(shape, turns) for turns in range(4))


def _reflect_lr(shape: Shape) -> Shape:
    width = max(col for _row, col in shape) + 1
    return _normalize((row, width - 1 - col) for row, col in shape)


def _bbox(shape: Shape) -> tuple[int, int]:
    return (
        max(row for row, _col in shape) + 1,
        max(col for _row, col in shape) + 1,
    )


def _is_connected(shape: Shape) -> bool:
    cells = set(shape)
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = (row + delta_row, col + delta_col)
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == cells


def _enumerate_shapes(size: int) -> tuple[Shape, ...]:
    shapes = {
        _normalize(cells)
        for cells in combinations(
            ((row, col) for row in range(3) for col in range(3)),
            size,
        )
        if _is_connected(_normalize(cells))
    }
    return tuple(sorted(shapes))


_ALL_SHAPES = {size: _enumerate_shapes(size) for size in (4, 5)}


def _template_families(size: int) -> tuple[Shape, ...]:
    families: dict[Shape, Shape] = {}
    for shape in _ALL_SHAPES[size]:
        orbit = set(_rotations(shape))
        if len(orbit) != 4 or _reflect_lr(shape) in orbit:
            continue
        representative = min(orbit)
        families.setdefault(representative, representative)
    return tuple(sorted(families))


_TEMPLATE_FAMILIES = {size: _template_families(size) for size in (4, 5)}


def _components(
    grid: list[list[int]],
    *,
    row_lo: int,
    row_hi: int,
    predicate,
) -> list[Shape]:
    height, width = len(grid), len(grid[0])
    row_lo = max(0, row_lo)
    row_hi = min(height - 1, row_hi)
    seen: set[tuple[int, int]] = set()
    components: list[Shape] = []
    for row in range(row_lo, row_hi + 1):
        for col in range(width):
            if (row, col) in seen or not predicate(grid[row][col]):
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (
                        row_lo <= next_row <= row_hi
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and predicate(grid[next_row][next_col])
                    ):
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            components.append(tuple(sorted(cells)))
    return components


def _relative_rotations(template: Shape, candidate: Shape) -> tuple[str, ...]:
    candidate = _normalize(candidate)
    return tuple(
        label
        for label, rotated in zip(_ROTATION_LABELS, _rotations(template))
        if rotated == candidate
    )


def _structure(grid: list[list[int]]) -> dict:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("every cell must be an ARC color 0..9")

    height = len(grid)
    if not 9 <= height <= 11 or not 11 <= width <= 13:
        raise ValueError(f"grid dimensions must be 9..11 by 11..13, got {height}x{width}")

    separator_rows = [
        row for row in range(height)
        if all(grid[row][col] == 9 for col in range(width))
    ]
    if len(separator_rows) != 1:
        raise ValueError(f"expected exactly one full color-9 separator row, found {len(separator_rows)}")
    separator_row = separator_rows[0]
    if separator_row != height - 6:
        raise ValueError(
            f"separator must leave the canonical five-row candidate region; got row {separator_row}"
        )
    if any(
        grid[row][col] == 9 and row != separator_row
        for row in range(height)
        for col in range(width)
    ):
        raise ValueError("color 9 may appear only in the separator row")

    upper_colors = {
        grid[row][col]
        for row in range(separator_row)
        for col in range(width)
        if grid[row][col] != 0
    }
    if upper_colors != {1}:
        raise ValueError(f"upper region must contain only one color-1 template, got {sorted(upper_colors)}")
    template_components = _components(
        grid,
        row_lo=0,
        row_hi=separator_row - 1,
        predicate=lambda value: value == 1,
    )
    if len(template_components) != 1:
        raise ValueError(f"expected one connected template, found {len(template_components)}")
    template_cells_abs = template_components[0]
    template = _normalize(template_cells_abs)
    template_cells = len(template)
    if template_cells not in (4, 5):
        raise ValueError(f"template must have 4 or 5 cells, got {template_cells}")

    lower_colors = {
        grid[row][col]
        for row in range(separator_row + 1, height)
        for col in range(width)
        if grid[row][col] != 0
    }
    if len(lower_colors) != 1:
        raise ValueError(f"lower candidates must share one color, got {sorted(lower_colors)}")
    candidate_color = next(iter(lower_colors))
    if candidate_color not in range(3, 9):
        raise ValueError(f"candidate color must be in 3..8, got {candidate_color}")

    candidate_components_abs = _components(
        grid,
        row_lo=separator_row + 1,
        row_hi=height - 1,
        predicate=lambda value: value == candidate_color,
    )
    if len(candidate_components_abs) != 3:
        raise ValueError(f"expected exactly three lower candidates, found {len(candidate_components_abs)}")
    if any(len(component) != template_cells for component in candidate_components_abs):
        sizes = sorted(len(component) for component in candidate_components_abs)
        raise ValueError(
            f"all candidates must match template cell count {template_cells}; got {sizes}"
        )

    ordered_abs = sorted(
        candidate_components_abs,
        key=lambda component: (
            min(col for _row, col in component),
            min(row for row, _col in component),
        ),
    )
    ordered = [_normalize(component) for component in ordered_abs]
    matches = [index for index, shape in enumerate(ordered) if shape in set(_rotations(template))]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one rotational match, found {len(matches)}")
    match_slot = matches[0]
    relative = _relative_rotations(template, ordered[match_slot])
    match_rotation = relative[0]

    reflected_orbit = set(_rotations(_reflect_lr(template)))
    reflection_slots = [
        index for index, shape in enumerate(ordered)
        if index != match_slot and shape in reflected_orbit
    ]

    return {
        "grid_h": height,
        "grid_w": width,
        "separator_row": separator_row,
        "candidate_color": candidate_color,
        "template_cells": template_cells,
        "template": template,
        "template_cells_abs": template_cells_abs,
        "candidate_components_abs": ordered_abs,
        "candidate_shapes": ordered,
        "match_slot": match_slot,
        "match_rotation": match_rotation,
        "reflection_distractor": bool(reflection_slots),
        "reflection_slots": reflection_slots,
    }


def _validate_call(difficulty, overrides: dict) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))


def _choose_near_miss(template: Shape, rng) -> Shape:
    blocked = set(_rotations(template)) | set(_rotations(_reflect_lr(template)))
    target_bbox = sorted(_bbox(template))
    preferred = [
        shape for shape in _ALL_SHAPES[len(template)]
        if shape not in blocked and sorted(_bbox(shape)) == target_bbox
    ]
    candidates = preferred or [
        shape for shape in _ALL_SHAPES[len(template)]
        if shape not in blocked
    ]
    if not candidates:
        raise ValueError("no same-size non-equivalent distractor shape exists")
    return _rotate(rng.choice(candidates), rng.randrange(4))


def _place_shape(
    grid: list[list[int]],
    shape: Shape,
    *,
    top: int,
    left: int,
    color: int,
) -> None:
    for row, col in shape:
        grid[top + row][left + col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, exact-or-loud teaching instance."""
    _validate_call(difficulty, overrides)
    supplied = dict(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=dict(overrides),
    )

    height = ctx.draw_int("grid_h", 9, 11)
    if "grid_w" not in supplied:
        ctx.overrides["grid_w"] = height + 2
    width = ctx.draw_int("grid_w", 11, 13)
    candidate_color = ctx.draw_choice("candidate_color", _CANDIDATE_COLOR_OPTIONS)
    template_cells = ctx.draw_int("template_cells", 4, 5)
    if "match_slot" not in supplied:
        ctx.overrides["match_slot"] = sample_index % 3
    match_slot = ctx.draw_int("match_slot", 0, 2)
    if "match_rotation" not in supplied:
        ctx.overrides["match_rotation"] = _ROTATION_LABELS[sample_index % 4]
    match_rotation = ctx.draw_choice("match_rotation", _ROTATION_LABELS)

    layout_rng = ctx.draw_rng(f"layout:{difficulty or 'medium'}")
    family = layout_rng.choice(_TEMPLATE_FAMILIES[template_cells])
    template = _rotate(family, layout_rng.randrange(4))
    match = _rotate(template, _ROTATION_LABELS.index(match_rotation))
    reflection = _rotate(_reflect_lr(template), layout_rng.randrange(4))
    near_miss = _choose_near_miss(template, layout_rng)
    distractors = [reflection, near_miss]
    if layout_rng.random() < 0.5:
        distractors.reverse()

    candidates: list[Shape] = []
    distractor_index = 0
    for slot in range(3):
        if slot == match_slot:
            candidates.append(match)
        else:
            candidates.append(distractors[distractor_index])
            distractor_index += 1

    separator_row = height - 6
    grid = full_grid(height, width, 0)
    for col in range(width):
        grid[separator_row][col] = 9

    template_height, template_width = _bbox(template)
    template_top = layout_rng.randint(0, separator_row - template_height)
    template_left = layout_rng.randint(0, width - template_width)
    _place_shape(
        grid,
        template,
        top=template_top,
        left=template_left,
        color=1,
    )

    widths = [_bbox(shape)[1] for shape in candidates]
    minimum_width = sum(widths) + 2
    if minimum_width > width:
        raise ValueError("candidate shapes do not fit the requested grid width")
    slack = width - minimum_width
    buckets = [0, 0, 0, 0]
    for _ in range(slack):
        buckets[layout_rng.randrange(4)] += 1
    left = buckets[0]
    for index, shape in enumerate(candidates):
        shape_height, shape_width = _bbox(shape)
        top = separator_row + 1 + layout_rng.randint(0, 5 - shape_height)
        _place_shape(
            grid,
            shape,
            top=top,
            left=left,
            color=candidate_color,
        )
        left += shape_width
        if index < 2:
            left += 1 + buckets[index + 1]

    # Construction and observer must agree; never return a degraded fallback.
    observed = observe_overrides(grid)
    requested = {
        "grid_h": height,
        "grid_w": width,
        "candidate_color": candidate_color,
        "template_cells": template_cells,
        "match_slot": match_slot,
        "match_rotation": match_rotation,
    }
    if observed != requested:
        raise ValueError(f"constructed scene lost exact axis values: requested={requested}, observed={observed}")
    return [row[:] for row in grid]


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned grid."""
    info = _structure(grid)
    return {axis: info[axis] for axis in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full teaching grammar, not merely palette and dimensions."""
    try:
        _structure(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked canonical manifold, not independent marginals."""
    try:
        info = _structure(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if (info["grid_h"], info["grid_w"]) not in {(9, 11), (10, 12), (11, 13)}:
        errors.append("dimensions are not one of the three canonical linked profiles")
    if info["candidate_color"] != 8:
        errors.append("canonical candidates use color 8")
    return errors


def _witness(grid, predicate) -> bool:
    try:
        return bool(predicate(_structure(grid)))
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {
    "match_left": lambda grid: _witness(grid, lambda info: info["match_slot"] == 0),
    "match_middle": lambda grid: _witness(grid, lambda info: info["match_slot"] == 1),
    "match_right": lambda grid: _witness(grid, lambda info: info["match_slot"] == 2),
    "identity_match": lambda grid: _witness(grid, lambda info: info["match_rotation"] == "0"),
    "quarter_turn_cw_match": lambda grid: _witness(grid, lambda info: info["match_rotation"] == "90"),
    "half_turn_match": lambda grid: _witness(grid, lambda info: info["match_rotation"] == "180"),
    "quarter_turn_ccw_match": lambda grid: _witness(grid, lambda info: info["match_rotation"] == "270"),
    "reflection_is_distractor": lambda grid: _witness(grid, lambda info: info["reflection_distractor"]),
    "same_size_distractors": lambda grid: _witness(
        grid,
        lambda info: all(
            len(shape) == info["template_cells"]
            for shape in info["candidate_shapes"]
        ),
    ),
}


def expected_output(grid: list[list[int]]) -> list[list[int]]:
    """Small Python mirror used only for structural tests and lesson audits."""
    info = _structure(grid)
    output = [row[:] for row in grid]
    for row, col in info["candidate_components_abs"][info["match_slot"]]:
        output[row][col] = 2
    return output


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that leave fixed-position/count/reflection shortcuts viable."""
    errors: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        errors.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
        return errors

    demo_infos = []
    for index, pair in enumerate(demos):
        try:
            info = _structure(pair["input"])
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"demo {index} is malformed: {exc}")
            continue
        demo_infos.append(info)
        if pair.get("output") != expected_output(pair["input"]):
            errors.append(f"demo {index} output does not recolor exactly the rotational match")
        if not info["reflection_distractor"]:
            errors.append(f"demo {index} lacks a preserved reflected counterexample")

    try:
        query_info = _structure(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"query is malformed: {exc}")
        return errors
    if query.get("output") != expected_output(query["input"]):
        errors.append("query output does not recolor exactly the rotational match")
    if not query_info["reflection_distractor"]:
        errors.append("query lacks a reflected counterexample")

    if len({info["match_slot"] for info in demo_infos}) < 2:
        errors.append("demonstrations do not refute a fixed candidate-position shortcut")
    if len({info["match_rotation"] for info in demo_infos}) < 2:
        errors.append("demonstrations do not establish rotation invariance")
    return errors
