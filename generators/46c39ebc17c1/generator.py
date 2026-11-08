"""Generate dense color noise containing two to four solid rectangles.

Every input is a 30x30 field using colors 1, 2, 3, 6, and 8.  Embedded
same-color rectangles are at least 4x4; the transformation recolors every
cell of those rectangles yellow (4) while preserving the dense noise.
"""

from __future__ import annotations

from collections import Counter
import copy
from typing import NamedTuple

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "46c39ebc17c1"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "e55ddd0b7670"
SUMMARY = (
    "Find every solid same-color rectangle of at least 4x4 in a dense "
    "five-color field and recolor the rectangle cells yellow."
)
INVARIANTS = [
    "the input is exactly 30x30 and uses exactly colors 1, 2, 3, 6, and 8",
    "two to four interior solid rectangles have distinct source colors",
    "each rectangle is at least 4x4 and its color recurs in adjacent noise",
    "the output changes exactly the rectangle cells to yellow (4)",
]
EXPECTED_OUTPUT_CODOMAIN = 1_000_000

Grid = list[list[int]]
NOISE_PALETTE = (1, 2, 3, 6, 8)
NOISE_PALETTE_SET = frozenset(NOISE_PALETTE)
OUTPUT_COLOR = 4
GRID_SIZE = 30


class SceneSpec(NamedTuple):
    shapes: tuple[tuple[int, int], ...]


SCENE_SPECS = {
    # Exact linked train / visible-heldout rectangle-size signatures.
    "two_public_5x9_6x7": SceneSpec(((5, 9), (6, 7))),
    "four_public_5x5_6x6_6x7x2": SceneSpec(
        ((5, 5), (6, 6), (6, 7), (6, 7))
    ),
    "three_public_4x5_6x7_7x10": SceneSpec(
        ((4, 5), (6, 7), (7, 10))
    ),
    # Lawful recombinations of only demonstrated rectangle dimensions.
    "two_extreme_4x5_7x10": SceneSpec(((4, 5), (7, 10))),
    "three_mixed_5x5_5x9_6x7": SceneSpec(
        ((5, 5), (5, 9), (6, 7))
    ),
    "four_mixed_4x5_5x5_6x6_7x10": SceneSpec(
        ((4, 5), (5, 5), (6, 6), (7, 10))
    ),
}
SCENE_PROFILES = tuple(SCENE_SPECS)
PUBLIC_PROFILES = SCENE_PROFILES[:3]

_PROFILE_WEIGHTS = {
    "easy": (
        ("two_public_5x9_6x7",) * 3
        + ("two_extreme_4x5_7x10",) * 3
    ),
    "medium": (
        ("three_public_4x5_6x7_7x10",) * 3
        + ("three_mixed_5x5_5x9_6x7",) * 3
    ),
    "hard": (
        ("four_public_5x5_6x6_6x7x2",) * 3
        + ("four_mixed_4x5_5x5_6x6_7x10",) * 3
    ),
    "all": SCENE_PROFILES,
}

# Integer approximations of the three public non-rectangle color histograms.
# The rule does not depend on exact frequencies, but retaining their range
# prevents the planted rectangles from sitting in an unrealistically sparse
# or uniform field.
_BACKGROUND_WEIGHT_RECIPES = (
    (13, 21, 32, 21, 26),
    (18, 21, 30, 13, 18),
    (23, 13, 28, 12, 25),
)

_PROFILE_BY_SHAPES = {
    tuple(sorted(spec.shapes)): profile
    for profile, spec in SCENE_SPECS.items()
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted dense-rectangle profile",
        "valid": (
            "two_public_5x9_6x7|four_public_5x5_6x6_6x7x2|"
            "three_public_4x5_6x7_7x10|two_extreme_4x5_7x10|"
            "three_mixed_5x5_5x9_6x7|"
            "four_mixed_4x5_5x5_6x6_7x10"
        ),
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic dense-noise rectangle scene."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    if (
        isinstance(difficulty, str)
        and difficulty not in {"easy", "medium", "hard"}
    ):
        raise ValueError(f"invalid difficulty: {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = (
        difficulty
        if difficulty in {"easy", "medium", "hard"}
        else "all"
    )
    profile_options = (
        SCENE_PROFILES
        if overrides.get("scene_profile") is not None
        else _PROFILE_WEIGHTS[band]
    )
    profile = ctx.draw_choice("scene_profile", profile_options)
    layout_rng = ctx.draw_rng(f"dense_rectangle_layout_{band}")
    noise_rng = ctx.draw_rng(f"dense_rectangle_noise_{band}")

    for _ in range(256):
        rectangles = _construct_rectangles(
            SCENE_SPECS[profile].shapes,
            layout_rng,
        )
        grid = _paint_dense_scene(rectangles, noise_rng)
        try:
            analysis = _analyze(grid)
        except (TypeError, ValueError):
            continue
        if analysis["profile"] != profile:
            continue
        if min(analysis["halo_matches"]) < 2:
            continue
        if solve_python(grid) != _solve_from_rectangles(
            grid, analysis["rectangles"]
        ):
            continue
        return grid
    raise RuntimeError(
        f"unable to construct {profile!r} after 256 deterministic attempts"
    )


def solve_python(grid: Grid) -> Grid:
    """Mirror the canonical row-major maximal-prefix rectangle scan."""
    height, width = _validate_rectangular_grid(grid)
    output = copy.deepcopy(grid)
    marked: set[tuple[int, int]] = set()
    for r1 in range(height - 3):
        for c1 in range(width - 3):
            if (r1, c1) in marked:
                continue
            color = grid[r1][c1]
            max_c = c1
            while max_c < width and grid[r1][max_c] == color:
                max_c += 1
            min_width = max_c - c1
            best_r2 = r1
            best_c2 = max_c - 1
            best_area = 0
            row = r1 + 1
            current_width = min_width
            while row < height:
                row_width = 0
                while (
                    row_width < current_width
                    and grid[row][c1 + row_width] == color
                ):
                    row_width += 1
                new_width = min(current_width, row_width)
                if new_width < 4:
                    break
                rectangle_height = row - r1 + 1
                area = rectangle_height * new_width
                if area > best_area and rectangle_height >= 4:
                    best_area = area
                    best_r2 = row
                    best_c2 = c1 + new_width - 1
                row += 1
                current_width = new_width
            if best_r2 - r1 + 1 < 4 or best_c2 - c1 + 1 < 4:
                continue
            cells = {
                (row, col)
                for row in range(r1, best_r2 + 1)
                for col in range(c1, best_c2 + 1)
            }
            if any(grid[row][col] != color for row, col in cells):
                continue
            for row, col in cells:
                output[row][col] = OUTPUT_COLOR
                marked.add((row, col))
    return output


def self_check(grid, *, difficulty=None, meta=None):
    """Recognize the complete returned-grid training grammar."""
    try:
        analysis = _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    if solve_python(grid) != _solve_from_rectangles(
        grid, analysis["rectangles"]
    ):
        return [
            "canonical scan and independent solid-window detector disagree"
        ]
    return []


def observe_overrides(grid):
    """Recover the declared linked scene profile from a returned grid."""
    try:
        analysis = _analyze(grid)
    except (TypeError, ValueError):
        return {}
    return {"scene_profile": analysis["profile"]}


def canonical_profile_index(grid):
    """Return the linked public-profile index, or ``None``."""
    try:
        profile = _analyze(grid)["profile"]
    except (TypeError, ValueError):
        return None
    return (
        PUBLIC_PROFILES.index(profile)
        if profile in PUBLIC_PROFILES
        else None
    )


def _construct_rectangles(shapes, rng):
    """Place a profile constructively in separated 13x13 slots."""
    slots = list(_slots_for_count(len(shapes)))
    shuffled_shapes = list(shapes)
    rng.shuffle(shuffled_shapes)
    rng.shuffle(slots)
    colors = rng.sample(list(NOISE_PALETTE), len(shapes))
    rectangles = []
    for (short_side, long_side), slot, color in zip(
        shuffled_shapes, slots, colors
    ):
        if short_side != long_side and rng.choice((False, True)):
            rect_height, rect_width = long_side, short_side
        else:
            rect_height, rect_width = short_side, long_side
        r_lo, c_lo, r_hi, c_hi = slot
        row = rng.randint(r_lo, r_hi - rect_height + 1)
        col = rng.randint(c_lo, c_hi - rect_width + 1)
        rectangles.append(
            {
                "bbox": (
                    row,
                    col,
                    row + rect_height - 1,
                    col + rect_width - 1,
                ),
                "color": color,
            }
        )
    transform = rng.randrange(8)
    transformed = []
    for rectangle in rectangles:
        transformed.append(
            {
                "bbox": _transform_bbox(
                    rectangle["bbox"], transform
                ),
                "color": rectangle["color"],
            }
        )
    return sorted(transformed, key=lambda item: item["bbox"])


def _slots_for_count(count):
    if count == 2:
        return (
            (1, 1, 13, 13),
            (16, 16, 28, 28),
        )
    if count == 3:
        return (
            (1, 1, 13, 13),
            (1, 16, 13, 28),
            (16, 8, 28, 20),
        )
    if count == 4:
        return (
            (1, 1, 13, 13),
            (1, 16, 13, 28),
            (16, 1, 28, 13),
            (16, 16, 28, 28),
        )
    raise ValueError(f"unsupported rectangle count: {count}")


def _transform_bbox(bbox, transform):
    r1, c1, r2, c2 = bbox
    corners = (
        (r1, c1),
        (r1, c2),
        (r2, c1),
        (r2, c2),
    )
    mapped = [
        _transform_cell(row, col, transform)
        for row, col in corners
    ]
    rows = [row for row, _ in mapped]
    cols = [col for _, col in mapped]
    return min(rows), min(cols), max(rows), max(cols)


def _transform_cell(row, col, transform):
    last = GRID_SIZE - 1
    transforms = (
        (row, col),
        (col, last - row),
        (last - row, last - col),
        (last - col, row),
        (row, last - col),
        (col, row),
        (last - row, col),
        (last - col, last - row),
    )
    return transforms[transform]


def _paint_dense_scene(rectangles, rng):
    weights = rng.choice(_BACKGROUND_WEIGHT_RECIPES)
    rectangle_by_cell = {}
    for rectangle in rectangles:
        r1, c1, r2, c2 = rectangle["bbox"]
        color = rectangle["color"]
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                rectangle_by_cell[(row, col)] = color
    grid = []
    for row in range(GRID_SIZE):
        current = []
        for col in range(GRID_SIZE):
            if (row, col) in rectangle_by_cell:
                current.append(rectangle_by_cell[(row, col)])
            else:
                current.append(_weighted_noise_color(rng, weights))
        grid.append(current)
    return grid


def _weighted_noise_color(rng, weights):
    candidates = [
        (color, weight)
        for color, weight in zip(NOISE_PALETTE, weights)
    ]
    total = sum(weight for _, weight in candidates)
    ticket = rng.randrange(total)
    for color, weight in candidates:
        if ticket < weight:
            return color
        ticket -= weight
    raise AssertionError("weighted color selection exhausted")


def _analyze(grid):
    height, width = _validate_rectangular_grid(grid)
    if (height, width) != (GRID_SIZE, GRID_SIZE):
        raise ValueError(
            f"expected 30x30 input, got {height}x{width}"
        )
    colors = {value for row in grid for value in row}
    if colors != NOISE_PALETTE_SET:
        raise ValueError(
            f"expected palette {sorted(NOISE_PALETTE_SET)}, "
            f"got {sorted(colors)}"
        )
    rectangles = _solid_rectangle_components(grid)
    if not 2 <= len(rectangles) <= 4:
        raise ValueError(
            f"expected two to four solid rectangles, got {len(rectangles)}"
        )
    if any(not rectangle["solid_bbox"] for rectangle in rectangles):
        raise ValueError("qualifying same-color region is not a solid rectangle")
    rectangle_colors = [rectangle["color"] for rectangle in rectangles]
    if len(set(rectangle_colors)) != len(rectangle_colors):
        raise ValueError("rectangle source colors must be distinct")
    if any(
        r1 == 0
        or c1 == 0
        or r2 == height - 1
        or c2 == width - 1
        for r1, c1, r2, c2 in (
            rectangle["bbox"] for rectangle in rectangles
        )
    ):
        raise ValueError("rectangles must be interior")
    normalized_shapes = tuple(
        sorted(
            (
                min(rectangle["height"], rectangle["width"]),
                max(rectangle["height"], rectangle["width"]),
            )
            for rectangle in rectangles
        )
    )
    profile = _PROFILE_BY_SHAPES.get(normalized_shapes)
    if profile is None:
        raise ValueError(
            f"rectangle signature is outside profiles: {normalized_shapes}"
        )
    rectangle_cells = set().union(
        *(rectangle["cells"] for rectangle in rectangles)
    )
    background_counts = Counter(
        grid[row][col]
        for row in range(height)
        for col in range(width)
        if (row, col) not in rectangle_cells
    )
    if set(background_counts) != NOISE_PALETTE_SET:
        raise ValueError("noise outside rectangles does not use all five colors")
    if min(background_counts.values()) < 40:
        raise ValueError(
            f"noise color is too rare: {dict(background_counts)}"
        )
    halo_matches = [
        _halo_match_count(grid, rectangle)
        for rectangle in rectangles
    ]
    return {
        "height": height,
        "width": width,
        "profile": profile,
        "rectangles": rectangles,
        "normalized_shapes": normalized_shapes,
        "background_counts": dict(sorted(background_counts.items())),
        "halo_matches": halo_matches,
    }


def _solid_rectangle_components(grid):
    height, width = _validate_rectangular_grid(grid)
    qualifying = set()
    for row in range(height - 3):
        for col in range(width - 3):
            color = grid[row][col]
            if all(
                grid[current_row][current_col] == color
                for current_row in range(row, row + 4)
                for current_col in range(col, col + 4)
            ):
                qualifying.update(
                    (current_row, current_col)
                    for current_row in range(row, row + 4)
                    for current_col in range(col, col + 4)
                )
    components = []
    remaining = set(qualifying)
    while remaining:
        start = remaining.pop()
        color = grid[start[0]][start[1]]
        component = {start}
        frontier = [start]
        while frontier:
            row, col = frontier.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                candidate = (row + dr, col + dc)
                if (
                    candidate in remaining
                    and grid[candidate[0]][candidate[1]] == color
                ):
                    remaining.remove(candidate)
                    component.add(candidate)
                    frontier.append(candidate)
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        r1, r2 = min(rows), max(rows)
        c1, c2 = min(cols), max(cols)
        bbox_cells = {
            (row, col)
            for row in range(r1, r2 + 1)
            for col in range(c1, c2 + 1)
        }
        components.append(
            {
                "bbox": (r1, c1, r2, c2),
                "height": r2 - r1 + 1,
                "width": c2 - c1 + 1,
                "area": len(component),
                "color": color,
                "solid_bbox": (
                    component == bbox_cells
                    and all(
                        grid[row][col] == color
                        for row, col in bbox_cells
                    )
                ),
                "cells": component,
            }
        )
    return sorted(components, key=lambda item: item["bbox"])


def _solve_from_rectangles(grid, rectangles):
    output = copy.deepcopy(grid)
    for rectangle in rectangles:
        for row, col in rectangle["cells"]:
            output[row][col] = OUTPUT_COLOR
    return output


def _halo_match_count(grid, rectangle):
    r1, c1, r2, c2 = rectangle["bbox"]
    color = rectangle["color"]
    return sum(
        grid[row][col] == color
        for row in range(max(0, r1 - 1), min(len(grid), r2 + 2))
        for col in range(max(0, c1 - 1), min(len(grid[0]), c2 + 2))
        if not (r1 <= row <= r2 and c1 <= col <= c2)
    )


def _validate_rectangular_grid(grid):
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list")
    if not all(isinstance(row, list) and row for row in grid):
        raise ValueError("grid rows must be non-empty lists")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    for row in grid:
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                raise ValueError("grid values must be ARC integers 0..9")
    return len(grid), width
