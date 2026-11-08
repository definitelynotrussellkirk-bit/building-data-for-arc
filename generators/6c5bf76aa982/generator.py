"""Generate small component scenes for the exactly-one-border recolor rule.

Orange (7) components touching exactly one grid border are recolored
green (3). Orange components touching zero or two borders, plus every
non-orange distractor, stay unchanged.
"""

from __future__ import annotations

from collections.abc import Iterable

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "6c5bf76aa982"
TASK_ID = "6c5bf76aa982"
VERSION = "2.0.0"
RULE_HASH = "7bcfd291ec7c"
SUMMARY = (
    "Recolor only orange components touching exactly one border; preserve "
    "interior/corner orange components and non-orange distractors."
)

INVARIANTS = [
    "background is 0",
    "3..6 separated orange components, each with 2..4 cells",
    "at least one orange component touches exactly one border",
    "at least one orange component is strictly interior",
    "non-orange distractors are optional and never recolored",
]

PUBLIC_PROFILES = (
    "public_9x10",
    "public_10x10",
    "public_8x11",
    "public_9x9",
    "public_10x12",
)
EXTRAPOLATION_PROFILES = (
    "balanced_small",
    "all_sides",
    "role_alias",
)
SCENE_PROFILES = PUBLIC_PROFILES + EXTRAPOLATION_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng across all complete profiles",
        "valid": "|".join(SCENE_PROFILES),
    },
    "transform": {
        "type": "int",
        "default": "rng 1..7 for public profiles, 0..7 otherwise",
        "valid": "0..7",
    },
}

_PUBLIC_ROWS = {
    "public_9x10": (
        "0700000004",
        "0700000004",
        "0700000000",
        "0000000000",
        "0000077000",
        "0000070000",
        "7000000000",
        "7000000000",
        "7700000000",
    ),
    "public_10x10": (
        "0000770000",
        "0000700000",
        "0000000007",
        "0000000007",
        "0000000007",
        "0070000000",
        "0070000000",
        "0000000000",
        "0000000070",
        "3000000077",
    ),
    "public_8x11": (
        "00000000700",
        "00000000770",
        "00007700000",
        "70007000000",
        "70000000070",
        "00000000070",
        "00000700070",
        "00000700000",
    ),
    "public_9x9": (
        "770007000",
        "700007000",
        "000000000",
        "700000000",
        "700700000",
        "000770000",
        "000000000",
        "000000007",
        "000000007",
    ),
    "public_10x12": (
        "007000000077",
        "007000000007",
        "007000000007",
        "000000000000",
        "000007000000",
        "700007700000",
        "770000000000",
        "000000000000",
        "000000000070",
        "000000000770",
    ),
}

_WEIGHTED_PROFILES = {
    "easy": (
        *PUBLIC_PROFILES,
        *(("balanced_small",) * 7),
        *(("all_sides",) * 3),
        *(("role_alias",) * 5),
    ),
    "medium": (
        *PUBLIC_PROFILES,
        *(("balanced_small",) * 5),
        *(("all_sides",) * 5),
        *(("role_alias",) * 5),
    ),
    "hard": (
        *PUBLIC_PROFILES,
        *(("balanced_small",) * 3),
        *(("all_sides",) * 7),
        *(("role_alias",) * 5),
    ),
}

_BASE_SHAPES = (
    ((0, 0), (1, 0)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
)
_SIDES = ("top", "bottom", "left", "right")


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


def _normalize_shape(cells):
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(
        sorted((row - min_row, col - min_col) for row, col in cells)
    )


def _shape_orientations(shape):
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    grid = _empty_grid(height, width)
    for row, col in shape:
        grid[row][col] = 1
    orientations = {
        _normalize_shape(
            (row, col)
            for row, values in enumerate(transformed)
            for col, value in enumerate(values)
            if value
        )
        for transformed in _d4(grid)
    }
    return tuple(sorted(orientations))


_SHAPE_FAMILIES = tuple(
    _shape_orientations(shape) for shape in _BASE_SHAPES
)


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
    families = (
        [shape_family]
        if shape_family is not None
        else list(_SHAPE_FAMILIES)
    )
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
                        (start_row + row, start_col + col)
                        for row, col in shape
                    )
                    sides = _touch_sides(cells, height, width)
                    if required_sides is not None and sides != required_sides:
                        continue
                    if touch_count is not None and len(sides) != touch_count:
                        continue
                    if _free(cells, occupied, height, width):
                        candidates.append(cells)
            if not candidates:
                continue
            cells = rng.choice(candidates)
            for row, col in cells:
                grid[row][col] = color
                occupied.add((row, col))
            return cells
    return None


def _profile_dimensions(profile, difficulty, rng):
    band = difficulty if difficulty in _WEIGHTED_PROFILES else "medium"
    if profile == "balanced_small":
        ranges = {
            "easy": (8, 10),
            "medium": (9, 11),
            "hard": (10, 12),
        }
    elif profile == "all_sides":
        ranges = {
            "easy": (10, 10),
            "medium": (10, 11),
            "hard": (11, 12),
        }
    else:
        ranges = {
            "easy": (9, 10),
            "medium": (10, 11),
            "hard": (11, 12),
        }
    low, high = ranges[band]
    return rng.randint(low, high), rng.randint(low, high)


def _balanced_specs(difficulty, rng):
    band = difficulty if difficulty in _WEIGHTED_PROFILES else "medium"
    if band == "easy":
        target_count, interior_count, corner_count = 1, 1, 1
    elif band == "hard":
        target_count = rng.randint(2, 3)
        interior_count = rng.randint(1, 2)
        corner_count = rng.randint(0, 1)
    else:
        target_count = rng.randint(1, 2)
        interior_count = 2 if target_count == 1 else 1
        corner_count = rng.randint(0, 1)
    while target_count + interior_count + corner_count < 3:
        interior_count += 1
    while target_count + interior_count + corner_count > 6:
        interior_count -= 1

    sides = list(_SIDES)
    rng.shuffle(sides)
    specs = [
        (7, {"exact_sides": (side,)})
        for side in sides[:target_count]
    ]
    specs.extend(
        (7, {"touch_count": 0}) for _ in range(interior_count)
    )
    corners = (
        ("top", "left"),
        ("top", "right"),
        ("bottom", "left"),
        ("bottom", "right"),
    )
    if corner_count:
        specs.append(
            (7, {"exact_sides": rng.choice(corners)})
        )
    return specs


def _all_sides_specs(rng):
    specs = [
        (7, {"exact_sides": (side,)}) for side in _SIDES
    ]
    specs.append((7, {"touch_count": 0}))
    if rng.random() < 0.55:
        specs.append(
            (
                7,
                {
                    "exact_sides": rng.choice(
                        (
                            ("top", "left"),
                            ("top", "right"),
                            ("bottom", "left"),
                            ("bottom", "right"),
                        )
                    )
                },
            )
        )
    return specs


def _role_alias_specs(difficulty, rng):
    band = difficulty if difficulty in _WEIGHTED_PROFILES else "medium"
    target_count = 1 if band == "easy" else rng.randint(1, 2)
    sides = list(_SIDES)
    rng.shuffle(sides)
    shared_family = rng.choice(
        [
            family
            for family in _SHAPE_FAMILIES
            if len(family[0]) in (2, 3)
        ]
    )
    specs = [
        (
            7,
            {
                "exact_sides": (side,),
                "shape_family": shared_family,
            },
        )
        for side in sides[:target_count]
    ]
    specs.extend(
        (
            (
                7,
                {
                    "touch_count": 0,
                    "shape_family": shared_family,
                },
            ),
            (
                7,
                {
                    "exact_sides": rng.choice(
                        (
                            ("top", "left"),
                            ("top", "right"),
                            ("bottom", "left"),
                            ("bottom", "right"),
                        )
                    )
                },
            ),
        )
    )
    distractor_color = rng.choice((3, 3, 3, 1, 2, 4, 5, 6, 8, 9))
    distractor_side = next(
        side for side in sides if side not in sides[:target_count]
    )
    specs.append(
        (
            distractor_color,
            {
                "exact_sides": (distractor_side,),
                "shape_family": shared_family,
            },
        )
    )
    if band == "hard" and rng.random() < 0.5:
        second_color = rng.choice(
            [
                color
                for color in (1, 2, 3, 4, 5, 6, 8, 9)
                if color != distractor_color
            ]
        )
        specs.append((second_color, {"touch_count": 0}))
    return specs


def _construct_extrapolation(profile, difficulty, rng):
    for _ in range(80):
        height, width = _profile_dimensions(profile, difficulty, rng)
        grid = _empty_grid(height, width)
        occupied = set()
        if profile == "balanced_small":
            specs = _balanced_specs(difficulty, rng)
        elif profile == "all_sides":
            specs = _all_sides_specs(rng)
        elif profile == "role_alias":
            specs = _role_alias_specs(difficulty, rng)
        else:
            raise ValueError(f"unknown scene profile {profile!r}")

        complete = True
        for color, kwargs in specs:
            if not _place_component(
                grid,
                occupied,
                rng,
                color,
                **kwargs,
            ):
                complete = False
                break
        if complete and not self_check(grid):
            return grid
    raise RuntimeError(
        f"unable to construct complete {profile!r} scene after 80 attempts"
    )


def _normalize_distractors(grid):
    return [
        [value if value in (0, 7) else 1 for value in row]
        for row in grid
    ]


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def _canonical_orientation(grid):
    return min(_d4(grid), key=_grid_key)


_PUBLIC_PROFILE_LOOKUP = {}
for _profile, _rows in _PUBLIC_ROWS.items():
    for _grid in _d4(_normalize_distractors(_parse_rows(_rows))):
        _PUBLIC_PROFILE_LOOKUP[_grid_key(_grid)] = _profile


def _canonical_answer_profile(grid):
    return _PUBLIC_PROFILE_LOOKUP.get(
        _grid_key(_normalize_distractors(grid))
    )


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
                    next_row = current_row + dr
                    next_col = current_col + dc
                    if not (
                        0 <= next_row < height
                        and 0 <= next_col < width
                    ):
                        continue
                    if (
                        (next_row, next_col) in seen
                        or grid[next_row][next_col] != color
                    ):
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            found.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                }
            )
    return found


def _analyze(grid):
    reasons = []
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        return {"strict": False, "reasons": ["empty_or_non_grid"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"strict": False, "reasons": ["ragged"]}
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"strict": False, "reasons": ["invalid_arc_value"]}

    height = len(grid)
    if not (8 <= height <= 12 and 8 <= width <= 12):
        reasons.append("dimension_range")
    if not any(value == 0 for row in grid for value in row):
        reasons.append("background_zero")

    found_objects = _components(grid)
    orange = [obj for obj in found_objects if obj["color"] == 7]
    distractors = [
        obj for obj in found_objects if obj["color"] != 7
    ]
    orange_sizes = [len(obj["cells"]) for obj in orange]
    orange_sides = [
        _touch_sides(obj["cells"], height, width) for obj in orange
    ]
    orange_touches = [len(sides) for sides in orange_sides]
    distractor_sizes = [len(obj["cells"]) for obj in distractors]

    if not 3 <= len(orange) <= 6:
        reasons.append("orange_component_count")
    if orange and any(not 2 <= size <= 4 for size in orange_sizes):
        reasons.append("orange_component_size")
    if orange and any(touch not in (0, 1, 2) for touch in orange_touches):
        reasons.append("orange_touch_domain")
    if not any(touch == 1 for touch in orange_touches):
        reasons.append("missing_one_border_target")
    if not any(touch == 0 for touch in orange_touches):
        reasons.append("missing_interior_contrast")
    target_count = sum(touch == 1 for touch in orange_touches)
    if not 1 <= target_count <= 4:
        reasons.append("target_component_count")
    if len(distractors) > 2:
        reasons.append("distractor_component_count")
    if distractors and any(not 1 <= size <= 3 for size in distractor_sizes):
        reasons.append("distractor_component_size")
    nonzero_cells = sum(value != 0 for row in grid for value in row)
    if not 8 <= nonzero_cells <= 26:
        reasons.append("nonzero_density")

    answer_profile = _canonical_answer_profile(grid)
    target_sides = {
        side
        for sides in orange_sides
        if len(sides) == 1
        for side in sides
    }
    distractor_has_one_side = any(
        len(_touch_sides(obj["cells"], height, width)) == 1
        for obj in distractors
    )
    if answer_profile is not None:
        scene_profile = answer_profile
    elif target_sides == set(_SIDES):
        scene_profile = "all_sides"
    elif distractor_has_one_side:
        scene_profile = "role_alias"
    else:
        scene_profile = "balanced_small"

    return {
        "strict": not reasons,
        "reasons": reasons,
        "height": height,
        "width": width,
        "scene_profile": scene_profile,
        "canonical_answer_profile": answer_profile,
        "orange_component_count": len(orange),
        "orange_sizes": tuple(sorted(orange_sizes)),
        "orange_touches": tuple(sorted(orange_touches)),
        "target_component_count": target_count,
        "target_cell_count": sum(
            len(obj["cells"])
            for obj, touch in zip(orange, orange_touches)
            if touch == 1
        ),
        "distractor_component_count": len(distractors),
        "distractor_sizes": tuple(sorted(distractor_sizes)),
        "palette": tuple(
            sorted({value for row in grid for value in row})
        ),
        "nonzero_cells": nonzero_cells,
    }


def observe_overrides(grid):
    """Report the exact returned-grid meaning of both declared controls."""
    analysis = _analyze(grid)
    canonical = _canonical_orientation(grid)
    transform = next(
        index
        for index, candidate in enumerate(_d4(canonical))
        if candidate == grid
    )
    return {
        "scene_profile": analysis["scene_profile"],
        "transform": transform,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the calibrated returned-grid lesson, independently of locals."""
    return _analyze(grid)["reasons"]


def solve_python(grid):
    """Input-pure Python mirror of the canonical Racket component rule."""
    if not grid:
        return []
    if not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    output = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    for obj in _components(grid):
        if (
            obj["color"] == 7
            and len(_touch_sides(obj["cells"], height, width)) == 1
        ):
            for row, col in obj["cells"]:
                output[row][col] = 3
    return output


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if (
        "transform" in overrides
        and overrides["transform"] is not None
        and (
            isinstance(overrides["transform"], bool)
            or not isinstance(overrides["transform"], int)
        )
    ):
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
    profile = ctx.draw_choice(
        "scene_profile",
        _WEIGHTED_PROFILES[band],
    )
    scene_rng = ctx.draw_rng("scene")

    if profile in PUBLIC_PROFILES:
        grid = _parse_rows(_PUBLIC_ROWS[profile])
        distractor_colors = [
            value
            for row in grid
            for value in row
            if value not in (0, 7)
        ]
        if distractor_colors:
            replacement = scene_rng.choice(
                (3, 3, 3, 1, 2, 4, 5, 6, 8, 9)
            )
            grid = [
                [
                    replacement if value not in (0, 7) else value
                    for value in row
                ]
                for row in grid
            ]
    else:
        grid = _construct_extrapolation(profile, difficulty, scene_rng)

    canonical_grid = _canonical_orientation(grid)
    if "transform" in overrides and overrides["transform"] is not None:
        transform = ctx.draw_choice("transform", tuple(range(8)))
    elif profile in PUBLIC_PROFILES:
        original = _parse_rows(_PUBLIC_ROWS[profile])
        literal_transform = next(
            index
            for index, candidate in enumerate(_d4(canonical_grid))
            if _normalize_distractors(candidate)
            == _normalize_distractors(original)
        )
        transform = ctx.draw_choice(
            "transform",
            tuple(
                index
                for index in range(8)
                if index != literal_transform
            ),
        )
    else:
        transform = ctx.draw_choice("transform", tuple(range(8)))
    grid = _d4(canonical_grid)[transform]

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(
            f"constructed invalid {profile!r} scene: {errors}"
        )
    return [row[:] for row in grid]
