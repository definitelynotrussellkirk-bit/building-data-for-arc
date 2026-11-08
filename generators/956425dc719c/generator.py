"""Generator for the exactly-one-border orange-component recolor rule.

Orange (7) components touching exactly one grid border are recolored gray (5).
Orange components touching zero or two borders, and every non-orange object,
stay unchanged.  The teaching distribution is anchored to all five canonical
inputs and adds role/geometry counterexamples that refute common shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "956425dc719c"
TASK_ID = "956425dc719c"
VERSION = "2.0.0"
RULE_HASH = "69dae4a2243d"
SUMMARY = (
    "Recolor only orange components touching exactly one border to gray; "
    "preserve interior/corner orange components and all non-orange distractors."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.95

INVARIANTS = [
    "background is 0 and input contains no gray(5) answer leakage",
    "at least one orange component touches exactly one border",
    "at least one orange component touches zero or two borders and stays orange",
    "at least one non-orange distractor is present and remains unchanged",
    "same-color components are 4-connected and separated by background",
]

PUBLIC_PROFILES = (
    "canonical_train_0",
    "canonical_train_1",
    "canonical_train_2",
    "canonical_train_3",
    "canonical_test_0",
)
SYNTHETIC_PROFILES = ("balanced", "all_sides", "role_alias")
SCENE_PROFILES = PUBLIC_PROFILES + SYNTHETIC_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng across canonical and synthetic profiles",
        "valid": "|".join(SCENE_PROFILES),
    },
    "transform": {
        "type": "int",
        "default": "rng 0..7",
        "valid": "0..7",
    },
}

# Every canonical train/test input is represented exactly here.  Distractor
# colors may be bijectively remapped at draw time, but their object roles and
# the number of distinct distractor colors are preserved.
_PUBLIC_ROWS = {
    "canonical_train_0": (
        "000007770000",
        "000207770000",
        "002200000077",
        "000000077777",
        "000000077700",
        "002200000000",
        "002200000000",
        "000000000000",
        "770000000000",
        "770000000000",
    ),
    "canonical_train_1": (
        "000770000000",
        "000770000077",
        "000000000077",
        "000000000000",
        "007700000000",
        "007700000000",
        "000000000600",
        "000006606600",
        "770006600000",
        "770000000000",
    ),
    "canonical_train_2": (
        "0000000007700",
        "0000000007700",
        "0000000000077",
        "0000066660077",
        "0000000077077",
        "0000000077000",
        "7700000220000",
        "7700000200000",
    ),
    "canonical_train_3": (
        "000000007700",
        "000000007700",
        "000000000000",
        "066000002200",
        "066000002000",
        "000000000077",
        "000000000077",
        "000000077777",
        "770000077700",
        "770000000000",
    ),
    "canonical_test_0": (
        "000000007700",
        "000220007700",
        "000200000077",
        "000000000077",
        "000000000077",
        "000777000000",
        "770777006000",
        "770000066000",
    ),
}

_WEIGHTED_PROFILES = {
    "easy": (
        *PUBLIC_PROFILES,
        *PUBLIC_PROFILES,
        "balanced",
        "balanced",
        "role_alias",
        "all_sides",
    ),
    "medium": (
        *PUBLIC_PROFILES,
        "balanced",
        "balanced",
        "role_alias",
        "role_alias",
        "all_sides",
        "all_sides",
    ),
    "hard": (
        *PUBLIC_PROFILES,
        "balanced",
        "role_alias",
        "role_alias",
        "all_sides",
        "all_sides",
        "all_sides",
    ),
}

_BASE_SHAPES = (
    ((0, 0), (1, 0)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
)
_SIDES = ("top", "bottom", "left", "right")
_DISTRACTOR_COLORS = (1, 2, 3, 4, 6, 8, 9)


def _empty_grid(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _parse_rows(rows: Iterable[str]) -> list[list[int]]:
    return [[int(value) for value in row] for row in rows]


def _rotate90(grid: list[list[int]]) -> list[list[int]]:
    return [
        [grid[len(grid) - 1 - row][col] for row in range(len(grid))]
        for col in range(len(grid[0]))
    ]


def _reflect(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _d4(grid: list[list[int]]) -> tuple[list[list[int]], ...]:
    transformed = []
    current = [row[:] for row in grid]
    for _ in range(4):
        transformed.append([row[:] for row in current])
        transformed.append(_reflect(current))
        current = _rotate90(current)
    return tuple(transformed)


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def _canonical_orientation(grid):
    return min(_d4(grid), key=_grid_key)


def _normalize_shape(cells):
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _shape_orientations(shape):
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    grid = _empty_grid(height, width)
    for row, col in shape:
        grid[row][col] = 1
    return tuple(
        sorted(
            {
                _normalize_shape(
                    (row, col)
                    for row, values in enumerate(transformed)
                    for col, value in enumerate(values)
                    if value
                )
                for transformed in _d4(grid)
            }
        )
    )


_SHAPE_FAMILIES = tuple(_shape_orientations(shape) for shape in _BASE_SHAPES)


def _touch_sides(cells, height, width):
    sides = []
    if any(row == 0 for row, _ in cells):
        sides.append("top")
    if any(row == height - 1 for row, _ in cells):
        sides.append("bottom")
    if any(col == 0 for _, col in cells):
        sides.append("left")
    if any(col == width - 1 for _, col in cells):
        sides.append("right")
    return tuple(sides)


def _free(cells, occupied, height, width):
    for row, col in cells:
        if not (0 <= row < height and 0 <= col < width):
            return False
        if (row, col) in occupied:
            return False
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (row + dr, col + dc) in occupied:
                return False
    return True


def _place_component(
    grid,
    occupied,
    rng,
    color,
    *,
    exact_sides=None,
    touch_count=None,
    shape_family=None,
):
    height, width = len(grid), len(grid[0])
    families = [shape_family] if shape_family is not None else list(_SHAPE_FAMILIES)
    rng.shuffle(families)
    required_sides = tuple(exact_sides) if exact_sides is not None else None
    for family in families:
        orientations = list(family)
        rng.shuffle(orientations)
        for shape in orientations:
            shape_height = max(row for row, _ in shape) + 1
            shape_width = max(col for _, col in shape) + 1
            candidates = []
            for start_row in range(height - shape_height + 1):
                for start_col in range(width - shape_width + 1):
                    cells = tuple(
                        (start_row + row, start_col + col) for row, col in shape
                    )
                    sides = _touch_sides(cells, height, width)
                    if required_sides is not None and sides != required_sides:
                        continue
                    if touch_count is not None and len(sides) != touch_count:
                        continue
                    if _free(cells, occupied, height, width):
                        candidates.append(cells)
            if candidates:
                cells = rng.choice(candidates)
                for row, col in cells:
                    grid[row][col] = color
                    occupied.add((row, col))
                return cells
    return None


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row, next_col = current_row + dr, current_col + dc
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (
                        (next_row, next_col) in seen
                        or grid[next_row][next_col] != color
                    ):
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            found.append({"color": color, "cells": tuple(sorted(cells))})
    return found


def _normalize_distractors(grid):
    return [[value if value in (0, 7) else 1 for value in row] for row in grid]


_PUBLIC_PROFILE_LOOKUP = {}
for _profile, _rows in _PUBLIC_ROWS.items():
    for _grid in _d4(_normalize_distractors(_parse_rows(_rows))):
        _PUBLIC_PROFILE_LOOKUP[_grid_key(_grid)] = _profile


def _canonical_answer_profile(grid):
    return _PUBLIC_PROFILE_LOOKUP.get(_grid_key(_normalize_distractors(grid)))


def _analyze(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"strict": False, "reasons": ["empty_or_non_grid"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"strict": False, "reasons": ["ragged"]}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"strict": False, "reasons": ["invalid_arc_value"]}

    reasons = []
    height = len(grid)
    palette = tuple(sorted({value for row in grid for value in row}))
    if not (8 <= height <= 13 and 8 <= width <= 13):
        reasons.append("dimension_range")
    if 0 not in palette:
        reasons.append("missing_background_zero")
    if 5 in palette:
        reasons.append("gray_answer_leakage")
    if not 3 <= len(palette) <= 4:
        reasons.append("palette_size")

    found_components = _components(grid)
    orange = [obj for obj in found_components if obj["color"] == 7]
    distractors = [obj for obj in found_components if obj["color"] != 7]
    orange_sides = [_touch_sides(obj["cells"], height, width) for obj in orange]
    orange_touches = [len(sides) for sides in orange_sides]
    if not 3 <= len(orange) <= 7:
        reasons.append("orange_component_count")
    if orange and any(not 2 <= len(obj["cells"]) <= 14 for obj in orange):
        reasons.append("orange_component_size")
    if not any(touch == 1 for touch in orange_touches):
        reasons.append("missing_one_border_target")
    if not any(touch != 1 for touch in orange_touches):
        reasons.append("missing_retained_orange_contrast")
    if not 1 <= len(distractors) <= 4:
        reasons.append("distractor_component_count")
    if distractors and any(not 2 <= len(obj["cells"]) <= 6 for obj in distractors):
        reasons.append("distractor_component_size")

    target_count = sum(touch == 1 for touch in orange_touches)
    target_sides = {
        side for sides in orange_sides if len(sides) == 1 for side in sides
    }
    distractor_has_one_side = any(
        len(_touch_sides(obj["cells"], height, width)) == 1 for obj in distractors
    )
    answer_profile = _canonical_answer_profile(grid)
    if answer_profile is not None:
        scene_profile = answer_profile
    elif target_sides == set(_SIDES):
        scene_profile = "all_sides"
    elif distractor_has_one_side:
        scene_profile = "role_alias"
    else:
        scene_profile = "balanced"

    return {
        "strict": not reasons,
        "reasons": reasons,
        "height": height,
        "width": width,
        "palette": palette,
        "scene_profile": scene_profile,
        "canonical_answer_profile": answer_profile,
        "orange_component_count": len(orange),
        "orange_touches": tuple(sorted(orange_touches)),
        "target_component_count": target_count,
        "target_cell_count": sum(
            len(obj["cells"])
            for obj, touch in zip(orange, orange_touches)
            if touch == 1
        ),
        "retained_orange_count": sum(touch != 1 for touch in orange_touches),
        "has_interior_orange": any(touch == 0 for touch in orange_touches),
        "has_corner_orange": any(touch >= 2 for touch in orange_touches),
        "target_sides": tuple(sorted(target_sides)),
        "distractor_component_count": len(distractors),
        "distractor_has_one_side": distractor_has_one_side,
    }


def observe_overrides(grid):
    """Recover the exact returned-grid meaning of every declared axis."""
    analysis = _analyze(grid)
    canonical = _canonical_orientation(grid)
    transform = next(
        index for index, candidate in enumerate(_d4(canonical)) if candidate == grid
    )
    return {"scene_profile": analysis["scene_profile"], "transform": transform}


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the task-specific teaching grammar from the returned grid only."""
    return _analyze(grid)["reasons"]


def strict_canonical_like(grid):
    """Task-linked canonical manifold predicate for the semantic gate."""
    return _analyze(grid)["reasons"]


def solve_python(grid):
    """Input-pure mirror used only for tests; Racket remains output authority."""
    output = [row[:] for row in grid]
    if not grid:
        return output
    height, width = len(grid), len(grid[0])
    for obj in _components(grid):
        if obj["color"] == 7 and len(_touch_sides(obj["cells"], height, width)) == 1:
            for row, col in obj["cells"]:
                output[row][col] = 5
    return output


def _profile_dimensions(profile, difficulty, rng):
    band = difficulty if difficulty in _WEIGHTED_PROFILES else "medium"
    ranges = {
        "easy": (8, 10),
        "medium": (9, 11),
        "hard": (10, 13),
    }
    low, high = ranges[band]
    return rng.randint(low, high), rng.randint(max(9, low), high)


def _synthetic_specs(profile, difficulty, rng):
    band = difficulty if difficulty in _WEIGHTED_PROFILES else "medium"
    sides = list(_SIDES)
    rng.shuffle(sides)
    corner = rng.choice(
        (
            ("top", "left"),
            ("top", "right"),
            ("bottom", "left"),
            ("bottom", "right"),
        )
    )
    first_color = rng.choice(_DISTRACTOR_COLORS)
    second_color = rng.choice([color for color in _DISTRACTOR_COLORS if color != first_color])

    if profile == "all_sides":
        specs = [(7, {"exact_sides": (side,)}) for side in _SIDES]
        specs.extend(((7, {"touch_count": 0}), (7, {"exact_sides": corner})))
        specs.append((first_color, {"touch_count": 0}))
        if band == "hard":
            specs.append((second_color, {"touch_count": 0}))
        return specs

    if profile == "role_alias":
        shared_family = rng.choice(_SHAPE_FAMILIES)
        target_side, distractor_side = sides[0], sides[1]
        specs = [
            (7, {"exact_sides": (target_side,), "shape_family": shared_family}),
            (7, {"touch_count": 0, "shape_family": shared_family}),
            (7, {"exact_sides": corner}),
            (first_color, {"exact_sides": (distractor_side,), "shape_family": shared_family}),
            (second_color, {"touch_count": 0}),
        ]
        if band == "hard":
            specs.append((7, {"exact_sides": (sides[2],)}))
        return specs

    target_count = 1 if band == "easy" else 2
    specs = [(7, {"exact_sides": (side,)}) for side in sides[:target_count]]
    specs.extend(((7, {"touch_count": 0}), (7, {"exact_sides": corner})))
    specs.append((first_color, {"touch_count": 0}))
    if band != "easy":
        specs.append((second_color, {"touch_count": 0}))
    return specs


def _construct_synthetic(profile, difficulty, rng):
    for _ in range(100):
        height, width = _profile_dimensions(profile, difficulty, rng)
        grid = _empty_grid(height, width)
        occupied = set()
        complete = True
        for color, kwargs in _synthetic_specs(profile, difficulty, rng):
            if not _place_component(grid, occupied, rng, color, **kwargs):
                complete = False
                break
        if complete and not self_check(grid, difficulty=difficulty):
            return grid
    raise RuntimeError(f"unable to construct complete {profile!r} scene")


def _remap_public_distractors(grid, rng):
    source_colors = sorted({value for row in grid for value in row if value not in (0, 7)})
    choices = list(_DISTRACTOR_COLORS)
    rng.shuffle(choices)
    mapping = dict(zip(source_colors, choices))
    return [[mapping.get(value, value) for value in row] for row in grid]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if "transform" in overrides and overrides["transform"] is not None:
        value = overrides["transform"]
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 7:
            raise ValueError("transform override must be an integer in 0..7")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in _WEIGHTED_PROFILES else "medium"
    # Every four-pair lesson gets a role-alias demonstration, which is the
    # decisive counterexample to "recolor any one-border component". Exact
    # overrides still range over the complete declared codomain.
    if overrides.get("scene_profile") is not None:
        profile_choices = SCENE_PROFILES
    elif sample_index % EXAMPLES_NEEDED == 0:
        profile_choices = ("role_alias",)
    else:
        profile_choices = _WEIGHTED_PROFILES[band]
    profile = ctx.draw_choice("scene_profile", profile_choices)
    scene_rng = ctx.draw_rng("scene")

    if profile in PUBLIC_PROFILES:
        grid = _remap_public_distractors(_parse_rows(_PUBLIC_ROWS[profile]), scene_rng)
    else:
        grid = _construct_synthetic(profile, difficulty, scene_rng)

    canonical_grid = _canonical_orientation(grid)
    transform = ctx.draw_choice("transform", tuple(range(8)))
    grid = _d4(canonical_grid)[transform]
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid {profile!r} scene: {errors}")
    return [row[:] for row in grid]


def _facts(grid):
    return _analyze(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "one_border_target": lambda grid: _facts(grid)["target_component_count"] >= 1,
    "retained_orange": lambda grid: _facts(grid)["retained_orange_count"] >= 1,
    "interior_orange": lambda grid: _facts(grid)["has_interior_orange"],
    "corner_orange": lambda grid: _facts(grid)["has_corner_orange"],
    "nonorange_distractor": lambda grid: _facts(grid)["distractor_component_count"] >= 1,
    "nonorange_one_border_alias": lambda grid: _facts(grid)["distractor_has_one_side"],
    "target_top": lambda grid: "top" in _facts(grid)["target_sides"],
    "target_bottom": lambda grid: "bottom" in _facts(grid)["target_sides"],
    "target_left": lambda grid: "left" in _facts(grid)["target_sides"],
    "target_right": lambda grid: "right" in _facts(grid)["target_sides"],
}


def _candidate_output(grid, mode):
    output = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    found_components = _components(grid)
    orange = [obj for obj in found_components if obj["color"] == 7]
    orange_sizes = [len(obj["cells"]) for obj in orange]
    for obj in found_components:
        touches = len(_touch_sides(obj["cells"], height, width))
        should_paint = False
        if mode == "intended":
            should_paint = obj["color"] == 7 and touches == 1
        elif mode == "identity":
            should_paint = False
        elif mode == "all_orange":
            should_paint = obj["color"] == 7
        elif mode == "any_border_orange":
            should_paint = obj["color"] == 7 and touches >= 1
        elif mode == "corner_orange":
            should_paint = obj["color"] == 7 and touches >= 2
        elif mode == "any_color_one_border":
            should_paint = touches == 1
        elif mode == "largest_orange":
            should_paint = obj["color"] == 7 and len(obj["cells"]) == max(orange_sizes)
        elif mode == "smallest_orange":
            should_paint = obj["color"] == 7 and len(obj["cells"]) == min(orange_sizes)
        elif mode.startswith("fixed_"):
            side = mode.removeprefix("fixed_")
            should_paint = obj["color"] == 7 and _touch_sides(obj["cells"], height, width) == (side,)
        if should_paint:
            for row, col in obj["cells"]:
                output[row][col] = 5
    return output


def lesson_identifiable(demos, query):
    """Refute named shortcut rules against the complete materialized lesson."""
    rivals = (
        "identity",
        "all_orange",
        "any_border_orange",
        "corner_orange",
        "any_color_one_border",
        "largest_orange",
        "smallest_orange",
        "fixed_top",
        "fixed_bottom",
        "fixed_left",
        "fixed_right",
    )
    reasons = []
    for rival in rivals:
        if all(_candidate_output(pair["input"], rival) == pair["output"] for pair in demos):
            if _candidate_output(query["input"], rival) != query["output"]:
                reasons.append(f"rival {rival} fits demonstrations but changes query answer")
    return reasons
