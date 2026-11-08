"""Generator for 04ec2218e2d8: repaint cyan objects by bbox regions.

Every calibrated input is a 23x23 black canvas containing two or three
separated cyan components.  Each component is either a solid rectangle, a
rectangle with one interior hole, or a rectangle with one non-corner edge
notch.  For each component, the canonical rule paints an inset yellow center
and colors the remaining object cells by bbox quadrant: magenta top-left, blue
top-right, red bottom-left, and green bottom-right.  Background cutouts remain
background.

The three published rectangle-size tuples are explicit scene profiles.  Two
additional profiles vary sizes within the same grammar.  Positions, packing
orientation, and whole-scene D4 transform vary without retry or object loss;
a bounded solid-only branch reconstructs each published input literally.  A
three-slot sample-index schedule cycles all component styles so demonstrations
refute the plausible but wrong rule that paints whole bounding boxes.
"""
from __future__ import annotations

from itertools import combinations_with_replacement

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "04ec2218e2d8"
TASK_ID = "04ec2218e2d8"
VERSION = "4.0.0"
RULE_HASH = "6d0c8228b329"

SUMMARY = (
    "Build a 23x23 black scene with two or three separated cyan components "
    "whose bounding boxes follow the demonstrated size grammar. Components "
    "cycle among solid rectangles, one-hole rectangles, and one-notch "
    "rectangles. Repaint only cyan cells: inset center yellow; outer top-left "
    "magenta, top-right blue, bottom-left red, and bottom-right green."
)

EXAMPLES_NEEDED = 3
EXPECTED_OUTPUT_CODOMAIN = 1_000_000
OUTPUT_CODOMAIN_BY_DIFFICULTY = {
    "easy": 200_000,
    "medium": 500_000,
    "hard": 500_000,
    None: 1_000_000,
}

INVARIANTS = [
    "input and output are 23x23 with black background",
    "the input contains exactly two or three 4-connected cyan components",
    "each component is a solid rectangle or has one lawful hole or edge notch",
    "every component bbox is 6..14 cells per side and has a one-cell border",
    "components have at least one blank row or column between their bboxes",
    "bbox sizes determine scene_profile; cutout topology determines component_style",
    "positions and whole-scene D4 transforms are nuisance variables",
]

SCENE_PROFILES = (
    "two_8x12_10x12",
    "two_8x8_10x12",
    "three_6x6_10x6_14x10",
    "two_generalized",
    "three_generalized",
)
COMPONENT_STYLES = (
    "solid",
    "interior_hole",
    "edge_notch",
)
SCHEDULE_PROFILES = COMPONENT_STYLES
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
MIN_STRICT_FRAC = 1.0

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted rectangle-size grammar",
        "valid": "|".join(SCENE_PROFILES),
        "doc": (
            "Exact normalized component-bbox size tuple recovered from the "
            "returned grid."
        ),
    },
    "component_style": {
        "type": "str",
        "default": "sample_index mod 3 teaching schedule",
        "valid": "|".join(COMPONENT_STYLES),
        "doc": (
            "All components are solid, have one strict-interior hole, or "
            "have one non-corner edge notch."
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_PUBLIC_SPECS = {
    "two_8x12_10x12": (
        (1, 5, 10, 12),
        (14, 1, 8, 12),
    ),
    "two_8x8_10x12": (
        (1, 2, 8, 8),
        (10, 7, 10, 12),
    ),
    "three_6x6_10x6_14x10": (
        (1, 3, 10, 6),
        (4, 12, 14, 10),
        (15, 3, 6, 6),
    ),
}

_PROFILE_SIZES = {
    "two_8x12_10x12": (
        (8, 12),
        (10, 12),
    ),
    "two_8x8_10x12": (
        (8, 8),
        (10, 12),
    ),
    "three_6x6_10x6_14x10": (
        (10, 6),
        (6, 6),
        (14, 10),
    ),
}

_EXACT_SIGNATURES = {
    (
        (8, 12),
        (10, 12),
    ): "two_8x12_10x12",
    (
        (8, 8),
        (10, 12),
    ): "two_8x8_10x12",
    (
        (6, 6),
        (6, 10),
        (10, 14),
    ): "three_6x6_10x6_14x10",
}


def _build_generalized_two_sizes():
    shapes = tuple(
        (short_side, long_side)
        for short_side in range(6, 15)
        for long_side in range(short_side, 15)
    )
    return tuple(
        (first, second)
        for first, second in combinations_with_replacement(shapes, 2)
        if first[0] + second[0] + 1 <= 21
        and first[0] * first[1] + second[0] * second[1] <= 250
        and tuple(sorted((first, second))) not in _EXACT_SIGNATURES
    )


def _build_generalized_three_sizes():
    small_shapes = tuple(
        (height, width)
        for height in range(6, 10)
        for width in range(6, 11)
    )
    large_shapes = tuple(
        (height, width)
        for height in range(8, 15)
        for width in range(8, 15)
    )
    candidates = []
    for first, second in combinations_with_replacement(
        small_shapes,
        2,
    ):
        for large_height, large_width in large_shapes:
            large = (large_height, large_width)
            signature = tuple(sorted(
                (
                    (min(first), max(first)),
                    (min(second), max(second)),
                    (min(large), max(large)),
                )
            ))
            if (
                first[0] + second[0] + 1 <= 21
                and max(first[1], second[1]) + large[1] + 1 <= 21
                and (
                    first[0] * first[1]
                    + second[0] * second[1]
                    + large[0] * large[1]
                    <= 250
                )
                and signature not in _EXACT_SIGNATURES
            ):
                candidates.append((first, second, large))
    return tuple(candidates)


_GENERALIZED_TWO_SIZES = _build_generalized_two_sizes()
_GENERALIZED_THREE_SIZES = _build_generalized_three_sizes()


def _blank(height=23, width=23, color=0):
    return [
        [color for _col in range(width)]
        for _row in range(height)
    ]


def _draw_rect(grid, top, left, height, width, color=8):
    for row in range(top, top + height):
        for col in range(left, left + width):
            grid[row][col] = color


def _render_specs(specs):
    grid = _blank()
    for top, left, height, width in specs:
        _draw_rect(grid, top, left, height, width)
    return grid


_PUBLIC_GRIDS = {
    profile: tuple(
        tuple(row)
        for row in _render_specs(specs)
    )
    for profile, specs in _PUBLIC_SPECS.items()
}
_PUBLIC_GRID_TO_PROFILE = {
    grid: profile
    for profile, grid in _PUBLIC_GRIDS.items()
}


def _coerce_arc_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]
    converted = []
    errors = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted_row = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted_row.append(0)
            else:
                converted_row.append(value)
        converted.append(converted_row)
    if errors:
        return None, errors
    return converted, []


def _components4_of_color(grid, color):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for delta_row, delta_col in (
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1),
                ):
                    candidate = (
                        current_row + delta_row,
                        current_col + delta_col,
                    )
                    if (
                        0 <= candidate[0] < height
                        and 0 <= candidate[1] < width
                        and candidate not in seen
                        and grid[candidate[0]][candidate[1]] == color
                    ):
                        seen.add(candidate)
                        queue.append(candidate)
            components.append(cells)
    return components


def _bbox(cells):
    return (
        min(row for row, _col in cells),
        min(col for _row, col in cells),
        max(row for row, _col in cells),
        max(col for _row, col in cells),
    )


def _normalized_signature(rectangles):
    return tuple(sorted(
        (
            min(rectangle["height"], rectangle["width"]),
            max(rectangle["height"], rectangle["width"]),
        )
        for rectangle in rectangles
    ))


def _separated(first, second):
    return (
        first["bottom"] + 1 < second["top"]
        or second["bottom"] + 1 < first["top"]
        or first["right"] + 1 < second["left"]
        or second["right"] + 1 < first["left"]
    )


def _analyze_scene(grid):
    original, errors = _coerce_arc_grid(grid)
    if errors or len(original) != 23 or len(original[0]) != 23:
        return None
    palette = {value for row in original for value in row}
    if palette != {0, 8}:
        return None

    rectangles = []
    component_styles = []
    for cells in _components4_of_color(original, 8):
        top, left, bottom, right = _bbox(cells)
        height = bottom - top + 1
        width = right - left + 1
        if (
            not (6 <= height <= 14)
            or not (6 <= width <= 14)
            or top == 0
            or left == 0
            or bottom == 22
            or right == 22
        ):
            return None

        cell_set = set(cells)
        missing = sorted(
            (row, col)
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
            if (row, col) not in cell_set
        )
        if not missing:
            component_style = "solid"
        elif len(missing) == 1:
            row, col = missing[0]
            on_horizontal_edge = row in (top, bottom)
            on_vertical_edge = col in (left, right)
            if not on_horizontal_edge and not on_vertical_edge:
                component_style = "interior_hole"
            elif on_horizontal_edge != on_vertical_edge:
                component_style = "edge_notch"
            else:
                return None
        else:
            return None

        component_styles.append(component_style)
        rectangles.append({
            "cells": cells,
            "missing": missing,
            "component_style": component_style,
            "top": top,
            "left": left,
            "bottom": bottom,
            "right": right,
            "height": height,
            "width": width,
        })

    if len(rectangles) not in (2, 3):
        return None
    if len(set(component_styles)) != 1:
        return None
    if any(
        not _separated(first, second)
        for index, first in enumerate(rectangles)
        for second in rectangles[index + 1:]
    ):
        return None

    signature = _normalized_signature(rectangles)
    profile = _EXACT_SIGNATURES.get(signature)
    if profile is None:
        profile = (
            "two_generalized"
            if len(rectangles) == 2
            else "three_generalized"
        )
    frozen = tuple(tuple(row) for row in original)
    return {
        "scene_profile": profile,
        "component_style": component_styles[0],
        "rectangles": rectangles,
        "signature": signature,
        "exact_public": frozen in _PUBLIC_GRID_TO_PROFILE,
    }


def observe_overrides(grid):
    """Recover every declared semantic axis from the returned grid."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return {}
    return {
        "scene_profile": analysis["scene_profile"],
        "component_style": analysis["component_style"],
    }

def canonical_profile_index(grid):
    """Return the demonstrated profile index, or ``None``."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return None
    profile = analysis["scene_profile"]
    if profile not in _PUBLIC_SPECS:
        return None
    return SCENE_PROFILES.index(profile)


def exact_public_profile_index(grid):
    """Return the literal published-input profile index, or ``None``."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    profile = _PUBLIC_GRID_TO_PROFILE.get(
        tuple(tuple(row) for row in original)
    )
    return (
        SCENE_PROFILES.index(profile)
        if profile is not None
        else None
    )


def self_check(grid, *, difficulty=None, meta=None):
    """Strictly recognize the calibrated component/bbox grammar."""
    _original, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if difficulty not in (None, "easy", "medium", "hard"):
        return [
            "difficulty must be easy, medium, hard, or None"
        ]
    analysis = _analyze_scene(grid)
    if analysis is None:
        return [
            "expected a 23x23 black/cyan scene with exactly two or three "
            "separated 4-connected components, each a 6..14 bbox containing "
            "either no cutout, one interior hole, or one non-corner edge notch"
        ]
    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = meta
        for axis in ("scene_profile", "component_style"):
            requested_value = requested.get(axis)
            if (
                requested_value is not None
                and requested_value != analysis[axis]
            ):
                errors.append(
                    f"{axis} requested {requested_value!r}, "
                    f"observed {analysis[axis]!r}"
                )
    return errors

def schedule_profile(seed, sample_index, difficulty=None):
    """Return the fixed topology profile for an ordinary sample index."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative exact integer")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _profile_options(difficulty):
    if difficulty == "easy":
        weights = (1, 1, 1, 5, 2)
    elif difficulty == "hard":
        weights = (1, 1, 2, 1, 5)
    else:
        weights = (1, 1, 1, 4, 4)
    return tuple(
        profile
        for profile, weight in zip(SCENE_PROFILES, weights)
        for _repeat in range(weight)
    )


def _orientations(size):
    height, width = size
    if height == width:
        return (size,)
    return (size, (width, height))


def _pack_two(sizes, rng):
    plans = []
    for first_index, second_index in ((0, 1), (1, 0)):
        for first in _orientations(sizes[first_index]):
            for second in _orientations(sizes[second_index]):
                if first[0] + second[0] + 1 <= 21:
                    plans.append(("vertical", first, second))
                if first[1] + second[1] + 1 <= 21:
                    plans.append(("horizontal", first, second))
    if not plans:
        raise RuntimeError("two-rectangle size tuple has no strip packing")
    direction, first, second = plans[rng.randrange(len(plans))]
    grid = _blank()
    if direction == "vertical":
        slack = 21 - first[0] - second[0] - 1
        extra_gap = rng.randint(0, slack)
        outer_slack = slack - extra_gap
        first_top = 1 + rng.randint(0, outer_slack)
        second_top = first_top + first[0] + 1 + extra_gap
        first_left = rng.randint(1, 22 - first[1])
        second_left = rng.randint(1, 22 - second[1])
    else:
        slack = 21 - first[1] - second[1] - 1
        extra_gap = rng.randint(0, slack)
        outer_slack = slack - extra_gap
        first_left = 1 + rng.randint(0, outer_slack)
        second_left = first_left + first[1] + 1 + extra_gap
        first_top = rng.randint(1, 22 - first[0])
        second_top = rng.randint(1, 22 - second[0])
    _draw_rect(
        grid,
        first_top,
        first_left,
        first[0],
        first[1],
    )
    _draw_rect(
        grid,
        second_top,
        second_left,
        second[0],
        second[1],
    )
    return grid


def _pack_three(sizes, rng):
    first_small, second_small, large = sizes
    if rng.randrange(2):
        first_small, second_small = second_small, first_small
    small_width = max(first_small[1], second_small[1])
    vertical_total = first_small[0] + second_small[0] + 1
    horizontal_total = small_width + large[1] + 1
    if vertical_total > 21 or horizontal_total > 21:
        raise RuntimeError("three-rectangle tuple has no column packing")
    grid = _blank()
    horizontal_slack = 21 - horizontal_total
    extra_horizontal_gap = rng.randint(0, horizontal_slack)
    horizontal_outer = horizontal_slack - extra_horizontal_gap
    small_left = 1 + rng.randint(0, horizontal_outer)
    large_left = (
        small_left
        + small_width
        + 1
        + extra_horizontal_gap
    )
    vertical_slack = 21 - vertical_total
    extra_vertical_gap = rng.randint(0, vertical_slack)
    vertical_outer = vertical_slack - extra_vertical_gap
    first_top = 1 + rng.randint(0, vertical_outer)
    second_top = (
        first_top
        + first_small[0]
        + 1
        + extra_vertical_gap
    )
    first_left = small_left + rng.randint(
        0,
        small_width - first_small[1],
    )
    second_left = small_left + rng.randint(
        0,
        small_width - second_small[1],
    )
    large_top = rng.randint(1, 22 - large[0])
    _draw_rect(
        grid,
        first_top,
        first_left,
        first_small[0],
        first_small[1],
    )
    _draw_rect(
        grid,
        second_top,
        second_left,
        second_small[0],
        second_small[1],
    )
    _draw_rect(
        grid,
        large_top,
        large_left,
        large[0],
        large[1],
    )
    return grid


def _transform_square(grid, transform):
    current = [row[:] for row in grid]
    if transform >= 4:
        current = [list(reversed(row)) for row in current]
        transform -= 4
    for _rotation in range(transform):
        current = [
            [
                current[len(current) - 1 - row][col]
                for row in range(len(current))
            ]
            for col in range(len(current[0]))
        ]
    return current


def _apply_component_style(grid, component_style, rng):
    """Remove one lawful cell from every solid component, if requested."""
    if component_style == "solid":
        return [row[:] for row in grid]
    styled = [row[:] for row in grid]
    for cells in _components4_of_color(styled, 8):
        top, left, bottom, right = _bbox(cells)
        if component_style == "interior_hole":
            candidates = [
                (row, col)
                for row in range(top + 1, bottom)
                for col in range(left + 1, right)
            ]
        elif component_style == "edge_notch":
            candidates = [
                (row, col)
                for row in range(top, bottom + 1)
                for col in range(left, right + 1)
                if (
                    (row in (top, bottom))
                    != (col in (left, right))
                )
            ]
        else:
            raise ValueError("unknown component_style")
        if not candidates:
            raise RuntimeError(
                f"no lawful {component_style} cutout in {top,left,bottom,right}"
            )
        row, col = candidates[rng.randrange(len(candidates))]
        styled[row][col] = 0
    return styled


def _generalized_grid(profile, component_style, context):
    layout_rng = context.draw_rng("layout")
    if profile == "two_generalized":
        sizes = context.draw_choice(
            "size_tuple",
            _GENERALIZED_TWO_SIZES,
        )
        grid = _pack_two(sizes, layout_rng)
    elif profile == "three_generalized":
        sizes = context.draw_choice(
            "size_tuple",
            _GENERALIZED_THREE_SIZES,
        )
        grid = _pack_three(sizes, layout_rng)
    elif profile.startswith("two_"):
        grid = _pack_two(_PROFILE_SIZES[profile], layout_rng)
    else:
        grid = _pack_three(_PROFILE_SIZES[profile], layout_rng)
    grid = _apply_component_style(
        grid,
        component_style,
        context.draw_rng("component_cutouts"),
    )
    transform = context.draw_choice(
        "scene_transform",
        tuple(range(8)),
    )
    return _transform_square(grid, transform)


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an exact integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            "unknown override(s): " + ", ".join(unknown)
        )
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError("unknown scene_profile")
    component_style = overrides.get("component_style")
    if (
        component_style is not None
        and component_style not in COMPONENT_STYLES
    ):
        raise ValueError("unknown component_style")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    effective_overrides = dict(overrides)
    effective_overrides.setdefault(
        "component_style",
        schedule_profile(seed, sample_index, difficulty),
    )
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    profile = context.draw_choice(
        "scene_profile",
        _profile_options(difficulty),
    )
    component_style = context.draw_choice(
        "component_style",
        COMPONENT_STYLES,
    )
    literal_rng = context.draw_rng("literal_public")
    if (
        component_style == "solid"
        and profile in _PUBLIC_GRIDS
        and literal_rng.randrange(10) == 0
    ):
        grid = [
            list(row)
            for row in _PUBLIC_GRIDS[profile]
        ]
    else:
        grid = _generalized_grid(
            profile,
            component_style,
            context,
        )
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": effective_overrides},
    )
    if errors:
        raise RuntimeError(
            "constructed an invalid calibrated scene: "
            + "; ".join(errors)
        )
    return grid

def _region_color(relative_row, relative_col, height, width):
    inset = max(2, min(height, width) // 4)
    if (
        inset <= relative_row < height - inset
        and inset <= relative_col < width - inset
    ):
        return 4
    if 2 * relative_row < height and 2 * relative_col < width:
        return 6
    if 2 * relative_row < height:
        return 1
    if 2 * relative_col < width:
        return 2
    return 3


def rule_mirror(grid):
    """Broad, input-pure Python mirror of the canonical Racket rule."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [row[:] for row in original]
    for cells in _components4_of_color(original, 8):
        top, left, bottom, right = _bbox(cells)
        height = bottom - top + 1
        width = right - left + 1
        for row, col in cells:
            output[row][col] = _region_color(
                row - top,
                col - left,
                height,
                width,
            )
    return output


def _bbox_fill_rival(grid):
    """Plausible wrong rule: paint every cell in each cyan component bbox."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [row[:] for row in original]
    for cells in _components4_of_color(original, 8):
        top, left, bottom, right = _bbox(cells)
        height = bottom - top + 1
        width = right - left + 1
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                output[row][col] = _region_color(
                    row - top,
                    col - left,
                    height,
                    width,
                )
    return output


SEMANTIC_RIVALS = {
    "paint_whole_bounding_boxes": _bbox_fill_rival,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def strict_canonical_like(grid):
    """Return short reasons outside the calibrated teaching manifold."""
    return self_check(grid)


def _witness_style(grid, expected_style):
    analysis = _analyze_scene(grid)
    return (
        analysis is not None
        and analysis["component_style"] == expected_style
    )


def _witness_solid_components(grid):
    return _witness_style(grid, "solid")


def _witness_interior_hole(grid):
    return _witness_style(grid, "interior_hole")


def _witness_edge_notch(grid):
    return _witness_style(grid, "edge_notch")


SEMANTIC_WITNESSES = {
    "solid_components": _witness_solid_components,
    "interior_hole_preserves_background": _witness_interior_hole,
    "edge_notch_preserves_background": _witness_edge_notch,
}
BRANCH_WITNESSES = set(SEMANTIC_WITNESSES)
WITNESS_RIVALS = {
    "interior_hole_preserves_background": [
        "paint_whole_bounding_boxes"
    ],
    "edge_notch_preserves_background": [
        "paint_whole_bounding_boxes"
    ],
}


def lesson_identifiable(demos, query):
    """Report when labeled demonstrations leave the bbox-fill rival viable."""
    if not isinstance(demos, (list, tuple)):
        return ["demos must be a sequence of labeled pairs"]
    reasons = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(
            f"at least {EXAMPLES_NEEDED} demonstrations are required"
        )

    episodes = [*demos, query]
    for index, episode in enumerate(episodes):
        role = f"demo {index}" if index < len(demos) else "query"
        if (
            not isinstance(episode, dict)
            or "input" not in episode
            or "output" not in episode
        ):
            reasons.append(f"{role} must contain input and output grids")
            continue
        findings = self_check(episode["input"])
        if findings:
            reasons.append(
                f"{role} input is outside the teaching grammar: "
                + "; ".join(findings[:2])
            )
            continue
        expected = rule_mirror(episode["input"])
        if expected != episode["output"]:
            reasons.append(
                f"{role} output disagrees with the selected object-cell rule"
            )
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                rival(demo["input"]) == demo["output"]
                for demo in demos
            )
            changes_query = (
                rival(query["input"]) != query["output"]
            )
        except Exception as exc:
            reasons.append(
                f"shortcut {name!r} raised {type(exc).__name__}: {exc}"
            )
            continue
        if fits_demos and changes_query:
            reasons.append(
                f"demonstrations leave shortcut {name!r} able to change "
                "the query answer"
            )
    return reasons
