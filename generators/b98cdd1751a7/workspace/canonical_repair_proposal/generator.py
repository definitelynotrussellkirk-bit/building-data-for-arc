"""Semantic generator for ARC task b98cdd1751a7 (source 1990f7a8).

The canonical rule finds same-color 8-connected nonzero objects, separates
them into upper and lower groups using the first/last object's top rows,
orders each group left-to-right, and copies the first four normalized crops
into the four 3x3 quadrants of a zero-filled 7x7 output.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "b98cdd1751a7"
TASK_ID = "b98cdd1751a7"
VERSION = "3.1.0"
RULE_HASH = "781a5f8cfaee"
SUMMARY = "Order four scattered 8-connected objects by upper/lower row group and left/right column, then assemble their normalized crops into a 7x7 quadrant grid."
INVARIANTS = [
    "calibrated inputs contain exactly four separated same-color 8-connected objects",
    "the canonical first/last-top-row midpoint places exactly two objects in each row group",
    "objects in each row group have distinct left-to-right bounding-box positions",
    "every calibrated crop is at most 3x3 and is copied without rotation or recoloring",
    "the output is a zero-filled 7x7 grid with crop origins at (0,0), (0,4), (4,0), and (4,4)",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = ("novel_uniform", "recolored_uniform", "distinct_palette", "varied_extent")
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four complete official shape families plus four labeled palette/extent contrasts",
        "valid": "|".join(SCENE_PROFILES),
    }
}


def _shape(*rows):
    return tuple(
        (row, col)
        for row, values in enumerate(rows)
        for col, value in enumerate(values)
        if value != "0"
    )


_PUBLIC_SPECS = {
    "public_1": {
        "canvas": (17, 19),
        "objects": (
            (2, 3, _shape("101", "011", "001")),
            (2, 11, _shape("110", "101", "110")),
            (9, 6, _shape("111", "101", "111")),
            (8, 13, _shape("110", "010", "101")),
        ),
    },
    "public_2": {
        "canvas": (23, 23),
        "objects": (
            (2, 3, _shape("111", "101", "111")),
            (5, 11, _shape("111", "111", "111")),
            (12, 5, _shape("101", "010", "111")),
            (13, 16, _shape("100", "011", "100")),
        ),
    },
    "public_3": {
        "canvas": (17, 16),
        "objects": (
            (1, 1, _shape("010", "101", "010")),
            (2, 8, _shape("101", "010", "110")),
            (12, 3, _shape("101", "110", "001")),
            (8, 10, _shape("010", "111", "010")),
        ),
    },
    "public_4": {
        "canvas": (17, 17),
        "objects": (
            (2, 6, _shape("101", "010", "111")),
            (4, 12, _shape("001", "011", "101")),
            (11, 1, _shape("101", "111", "100")),
            (11, 10, _shape("111", "101", "101")),
        ),
    },
}


def _normalize(cells):
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _shape_key(shapes):
    return tuple(sorted(tuple(sorted(shape)) for shape in shapes))


def _d4_variants(shape):
    variants = set()
    for mirrored in (False, True):
        transformed = tuple((row, -col) if mirrored else (row, col) for row, col in shape)
        for _ in range(4):
            variants.add(_normalize(transformed))
            transformed = tuple((col, -row) for row, col in transformed)
    return tuple(sorted(variants))


def _orbit_key(shape):
    return min(_d4_variants(shape))


def _family_key(shapes):
    return tuple(sorted(_orbit_key(shape) for shape in shapes))


_PUBLIC_FAMILY_KEYS = {
    _family_key(tuple(obj[2] for obj in spec["objects"])): profile
    for profile, spec in _PUBLIC_SPECS.items()
}


def _render_exact(spec):
    height, width = spec["canvas"]
    grid = [[0] * width for _ in range(height)]
    for row0, col0, shape in spec["objects"]:
        for row, col in shape:
            grid[row0 + row][col0 + col] = 2
    return grid


_PUBLIC_INPUTS = {
    profile: _render_exact(spec) for profile, spec in _PUBLIC_SPECS.items()
}
_PUBLIC_EXACT = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["input must contain one through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        return ["input must contain one through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _objects8(grid):
    """Same-color row-major 8-connected components, matching objects-8."""
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                here_row, here_col = stack.pop()
                cells.append((here_row, here_col))
                for row_delta in (-1, 0, 1):
                    for col_delta in (-1, 0, 1):
                        if row_delta == 0 and col_delta == 0:
                            continue
                        next_row = here_row + row_delta
                        next_col = here_col + col_delta
                        if (
                            0 <= next_row < height
                            and 0 <= next_col < width
                            and (next_row, next_col) not in seen
                            and grid[next_row][next_col] == color
                        ):
                            seen.add((next_row, next_col))
                            stack.append((next_row, next_col))
            row0 = min(r for r, _ in cells)
            row1 = max(r for r, _ in cells)
            col0 = min(c for _, c in cells)
            col1 = max(c for _, c in cells)
            components.append({
                "color": color,
                "cells": tuple(sorted(cells)),
                "bbox": (row0, col0, row1, col1),
                "shape": _normalize(cells),
            })
    return components


def _ordered_objects(grid):
    components = sorted(
        _objects8(grid),
        key=lambda obj: (obj["bbox"][0], obj["bbox"][1]),
    )
    if not components:
        raise ValueError("rule requires at least one nonzero object")
    midpoint = (components[0]["bbox"][0] + components[-1]["bbox"][0]) / 2.0
    upper = sorted(
        (obj for obj in components if obj["bbox"][0] < midpoint),
        key=lambda obj: obj["bbox"][1],
    )
    lower = sorted(
        (obj for obj in components if obj["bbox"][0] >= midpoint),
        key=lambda obj: obj["bbox"][1],
    )
    return upper + lower, upper, lower, midpoint


def rule_mirror(grid):
    """Broad, input-pure mirror of the canonical Racket program."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    ordered, _, _, _ = _ordered_objects(grid)
    output = [[0] * 7 for _ in range(7)]
    positions = ((0, 0), (0, 4), (4, 0), (4, 4))
    for obj, (target_row, target_col) in zip(ordered[:4], positions):
        source_row, source_col = obj["bbox"][:2]
        for row, col in obj["cells"]:
            new_row = target_row + row - source_row
            new_col = target_col + col - source_col
            if 0 <= new_row < 7 and 0 <= new_col < 7:
                output[new_row][new_col] = grid[row][col]
    return output


def _profile_for(components, exact_profile=None):
    shapes = tuple(obj["shape"] for obj in components)
    family_key = _family_key(shapes)
    colors = [obj["color"] for obj in components]
    bboxes = [
        (obj["bbox"][2] - obj["bbox"][0] + 1, obj["bbox"][3] - obj["bbox"][1] + 1)
        for obj in components
    ]
    public_profile = _PUBLIC_FAMILY_KEYS.get(family_key)
    if len(set(colors)) == 1 and public_profile is not None:
        return exact_profile or public_profile
    if all(box == (3, 3) for box in bboxes):
        if all(color == 2 for color in colors):
            return "novel_uniform"
        if len(set(colors)) == 1:
            return "recolored_uniform"
        if len(set(colors)) == 4:
            return "distinct_palette"
    if all(color == 2 for color in colors) and any(box != (3, 3) for box in bboxes):
        return "varied_extent"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    height, width = len(grid), len(grid[0])
    if not 10 <= height <= 30 or not 10 <= width <= 30:
        errors.append("calibrated canvas dimensions must be ten through thirty")
    components = _objects8(grid)
    if len(components) != 4:
        errors.append(f"expected exactly four same-color 8-connected objects, got {len(components)}")
    if components:
        ordered, upper, lower, midpoint = _ordered_objects(grid)
    else:
        ordered, upper, lower, midpoint = [], [], [], None
    if len(upper) != 2 or len(lower) != 2:
        errors.append(f"canonical midpoint must split two upper and two lower objects, got {len(upper)} and {len(lower)}")
    if len({obj["bbox"][1] for obj in upper}) != len(upper):
        errors.append("upper objects must have distinct left-to-right bounding-box columns")
    if len({obj["bbox"][1] for obj in lower}) != len(lower):
        errors.append("lower objects must have distinct left-to-right bounding-box columns")
    for index, obj in enumerate(components):
        row0, col0, row1, col1 = obj["bbox"]
        box_height, box_width = row1 - row0 + 1, col1 - col0 + 1
        if not 1 <= box_height <= 3 or not 1 <= box_width <= 3:
            errors.append(f"object {index} bounding box must fit within 3x3")
        if not 2 <= len(obj["cells"]) <= 9:
            errors.append(f"object {index} must contain two through nine cells")
    for left_index, left in enumerate(components):
        for right in components[left_index + 1:]:
            if min(
                max(abs(a_row - b_row), abs(a_col - b_col))
                for a_row, a_col in left["cells"]
                for b_row, b_col in right["cells"]
            ) <= 1:
                errors.append("calibrated objects must remain spatially separated even when colors differ")
                break
    exact = None
    try:
        exact = _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        pass
    profile = _profile_for(components, exact) if len(components) == 4 else None
    if profile is None and len(components) == 4:
        errors.append("unsupported calibrated shape/palette profile")
    output = rule_mirror(grid) if components else None
    return {
        "errors": errors,
        "scene_profile": profile if not errors else None,
        "facts": {
            "objects": components,
            "ordered": ordered,
            "upper_count": len(upper),
            "lower_count": len(lower),
            "midpoint": midpoint,
            "colors": tuple(obj["color"] for obj in components),
            "shape_key": _shape_key(tuple(obj["shape"] for obj in components)) if components else (),
            "bbox_dimensions": tuple(
                (obj["bbox"][2] - obj["bbox"][0] + 1, obj["bbox"][3] - obj["bbox"][1] + 1)
                for obj in components
            ),
        },
        "output": output,
    }


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    profile = analysis["scene_profile"]
    return profile if profile in PUBLIC_PROFILES and not analysis["errors"] else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def _polyomino(rng, box_height, box_width, min_cells, max_cells):
    for _ in range(300):
        target = rng.randint(min_cells, min(max_cells, box_height * box_width))
        cells = {(rng.randrange(box_height), rng.randrange(box_width))}
        while len(cells) < target:
            row, col = rng.choice(sorted(cells))
            neighbors = [
                (row + row_delta, col + col_delta)
                for row_delta in (-1, 0, 1)
                for col_delta in (-1, 0, 1)
                if (row_delta or col_delta)
                and 0 <= row + row_delta < box_height
                and 0 <= col + col_delta < box_width
                and (row + row_delta, col + col_delta) not in cells
            ]
            if not neighbors:
                break
            cells.add(rng.choice(neighbors))
        normalized = _normalize(cells)
        actual_height = max(row for row, _ in normalized) + 1
        actual_width = max(col for _, col in normalized) + 1
        if len(normalized) == target and (actual_height, actual_width) == (box_height, box_width):
            return normalized
    raise AssertionError(f"could not construct {box_height}x{box_width} connected shape")


def _exact_three_shapes(rng, difficulty):
    if difficulty == "easy":
        low, high = 4, 6
    elif difficulty == "hard":
        low, high = 5, 9
    else:
        low, high = 4, 8
    for _ in range(300):
        shapes = tuple(_polyomino(rng, 3, 3, low, high) for _ in range(4))
        if len(set(shapes)) == 4:
            return shapes
    raise AssertionError("could not construct four distinct 3x3 shapes")


def _varied_shapes(rng, difficulty):
    dimensions = [(2, 2), (2, 3), (3, 2), (1, 3), (3, 1), (3, 3)]
    for _ in range(300):
        chosen = [rng.choice(dimensions) for _ in range(4)]
        if all(value == (3, 3) for value in chosen):
            continue
        shapes = []
        for box_height, box_width in chosen:
            area = box_height * box_width
            low = 2 if area > 1 else 1
            low = max(low, box_height, box_width)
            high = max(low, area if difficulty == "hard" else area - 1)
            shapes.append(_polyomino(rng, box_height, box_width, low, high))
        return tuple(shapes)
    raise AssertionError("could not construct varied crop extents")


def _limits(difficulty):
    if difficulty == "easy":
        return 12, 17
    if difficulty == "hard":
        return 18, 28
    return 15, 23


def _place_shapes(shapes, colors, difficulty, rng):
    low, high = _limits(difficulty)
    for _ in range(500):
        height, width = rng.randint(low, high), rng.randint(low, high)
        layout = rng.choice(("balanced", "upper_shifted", "lower_shifted"))
        if layout == "balanced":
            top_limit = max(1, height // 2 - 4)
            bottom_low = min(height - 4, height // 2 + 1)
            top_rows = [rng.randint(1, top_limit) for _ in range(2)]
            bottom_rows = [rng.randint(bottom_low, height - 4) for _ in range(2)]
        elif layout == "upper_shifted":
            upper_row = 1
            lower_row = (height - 1) // 2
            if lower_row - upper_row < 4:
                continue
            top_rows = [upper_row, upper_row]
            bottom_rows = [lower_row, lower_row]
        else:
            upper_row = (height + 1) // 2
            lower_row = height - 3
            if lower_row - upper_row < 4:
                continue
            top_rows = [upper_row, upper_row]
            bottom_rows = [lower_row, lower_row]
        left_limit = max(1, width // 2 - 4)
        right_low = min(width - 4, width // 2 + 1)
        left_cols = [rng.randint(1, left_limit) for _ in range(2)]
        right_cols = [rng.randint(right_low, width - 4) for _ in range(2)]
        anchors = (
            (top_rows[0], left_cols[0]),
            (top_rows[1], right_cols[0]),
            (bottom_rows[0], left_cols[1]),
            (bottom_rows[1], right_cols[1]),
        )
        order = list(range(4))
        rng.shuffle(order)
        grid = [[0] * width for _ in range(height)]
        for anchor, source_index in zip(anchors, order):
            row0, col0 = anchor
            for row, col in shapes[source_index]:
                grid[row0 + row][col0 + col] = colors[source_index]
        analysis = _analysis(grid)
        if not analysis["errors"]:
            return grid
    raise AssertionError("could not place four separated ordered objects")


def _random_scene(profile, difficulty, rng):
    for _ in range(300):
        if profile in PUBLIC_PROFILES:
            shapes = tuple(
                rng.choice(_d4_variants(obj[2]))
                for obj in _PUBLIC_SPECS[profile]["objects"]
            )
            color = rng.randint(1, 9)
            colors = (color,) * 4
        elif profile == "novel_uniform":
            shapes = _exact_three_shapes(rng, difficulty)
            if _family_key(shapes) in _PUBLIC_FAMILY_KEYS:
                continue
            colors = (2, 2, 2, 2)
        elif profile == "recolored_uniform":
            shapes = _exact_three_shapes(rng, difficulty)
            color = rng.choice((1, 3, 4, 5, 6, 7, 8, 9))
            colors = (color,) * 4
        elif profile == "distinct_palette":
            shapes = _exact_three_shapes(rng, difficulty)
            palette = list(range(1, 10))
            rng.shuffle(palette)
            colors = tuple(palette[:4])
        elif profile == "varied_extent":
            shapes = _varied_shapes(rng, difficulty)
            colors = (2, 2, 2, 2)
        else:
            raise ValueError(f"unknown scene profile: {profile!r}")
        try:
            grid = _place_shapes(shapes, colors, difficulty, rng)
        except AssertionError:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct object-assembly lesson {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice(
        "scene_profile",
        list(PUBLIC_PROFILES) * 4 + list(GENERAL_PROFILES) * 2,
    )
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES and overrides.get("scene_profile") is not None:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _random_scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid object-assembly lesson: " + "; ".join(errors))
    return grid
