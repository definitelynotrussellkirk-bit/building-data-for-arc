"""Semantic generator for ARC task 9d52c9d09009 (source 37d3e8b2).

Find each 4-connected color-8 object.  Within its bounding box, count the
4-connected zero-cell regions.  Recolor the object by that count, except that
four regions map to color 7.  Other cells and colors are preserved.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "9d52c9d09009"
TASK_ID = "9d52c9d09009"
VERSION = "3.0.0"
RULE_HASH = "3d808db30609"
SUMMARY = "Recolor each color-8 object by its bounding-box zero-region count, mapping four regions to 7."
INVARIANTS = [
    "calibrated inputs contain four through seven separate 4-connected color-8 objects",
    "each object has a complete rectangular outer boundary and one through four zero regions in its bounding box",
    "one, two, and three zero regions map to colors 1, 2, and 3",
    "four zero regions map to color 7 rather than color 4",
    "background cells remain zero",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = ("all_counts", "one_focus", "two_focus", "high_focus")
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four complete official object families plus four controlled hole-count contrasts",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_1": (
        "00000000000000000", "00888888000888880", "00800808000808880",
        "00800888000888080", "00888888000808880", "00000000000888880",
        "00000888800000000", "00000800800888800", "00000888800800800",
        "00000880800888800", "00000888800888800", "00000000000000000",
        "08888800088888880", "08880800080888080", "08088800088808080",
        "08888800080888880", "00000000088888880",
    ),
    "public_2": (
        "00000000000000000", "08880000000000000", "08080000000000000",
        "08880888888800000", "08880888880800000", "00000808880800000",
        "00000888088800000", "00000888888800000", "00000000000000000",
        "00000000088888880", "00088880080080080", "00088880088888880",
        "00080880000000000", "00088880000888800", "00088880000800800",
        "00000000000888800", "00000000000808800", "00000000000888800",
        "00000000000000000",
    ),
    "public_3": (
        "0000000000000000", "0888888000000000", "0800808000000000",
        "0800888088888800", "0888808080080800", "0888888088888800",
        "0000000088008800", "0088888088888800", "0080888000000000",
        "0080808000000000", "0088808000000000", "0088888000000000",
        "0080888000888888", "0088888000808088", "0088008000888888",
        "0088888000808008", "0000000000888888",
    ),
    "public_4": (
        "008888800000000000", "008080808888888000", "008088808088008000",
        "008888808888008000", "000000008008888000", "000000008888888000",
        "008888000000000000", "008008000088888880", "008888000080088880",
        "000000000088880080", "000000000088880080", "088888880080888880",
        "080088880080888880", "080088880088800880", "088880880088800880",
        "088888880088888880", "000000000000000000",
    ),
}
_PUBLIC_INPUTS = {
    profile: [[int(value) for value in row] for row in rows]
    for profile, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_SIGNATURES = {
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


def _components4(grid, color):
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    components = []
    while cells:
        queue = [cells.pop()]
        component = []
        for row, col in queue:
            component.append((row, col))
            for other in ((row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1)):
                if other in cells:
                    cells.remove(other)
                    queue.append(other)
        components.append(component)
    return sorted(components, key=lambda component: min(component))


def _normalize(cells):
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _variants(norm):
    height = max(row for row, _ in norm) + 1
    width = max(col for _, col in norm) + 1
    transforms = (
        lambda row, col: (row, col),
        lambda row, col: (height - 1 - row, col),
        lambda row, col: (row, width - 1 - col),
        lambda row, col: (height - 1 - row, width - 1 - col),
        lambda row, col: (col, row),
        lambda row, col: (width - 1 - col, height - 1 - row),
        lambda row, col: (col, height - 1 - row),
        lambda row, col: (width - 1 - col, row),
    )
    return tuple(sorted({_normalize(transform(row, col) for row, col in norm) for transform in transforms}))


def _family_key(norm):
    return min(_variants(norm))


def _hole_count(grid, component):
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    row0, row1, col0, col1 = min(rows), max(rows), min(cols), max(cols)
    zeros = {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if grid[row][col] == 0
    }
    count = 0
    while zeros:
        queue = [zeros.pop()]
        for row, col in queue:
            for other in ((row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1)):
                if other in zeros:
                    zeros.remove(other)
                    queue.append(other)
        count += 1
    return count


def _shape_holes(norm):
    height = max(row for row, _ in norm) + 1
    width = max(col for _, col in norm) + 1
    grid = [[0] * width for _ in range(height)]
    for row, col in norm:
        grid[row][col] = 8
    return _hole_count(grid, list(norm))


def _complete_border(norm):
    cells = set(norm)
    height = max(row for row, _ in cells) + 1
    width = max(col for _, col in cells) + 1
    border = {
        (row, col)
        for row in range(height) for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    }
    return border <= cells


def rule_mirror(grid):
    """Broad, input-pure mirror of the canonical Racket program."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    result = [list(row) for row in grid]
    for component in _components4(grid, 8):
        holes = _hole_count(grid, component)
        color = 7 if holes == 4 else holes
        for row, col in component:
            result[row][col] = color
    return result


def _object_facts(grid):
    facts = []
    for component in _components4(grid, 8):
        norm = _normalize(component)
        height = max(row for row, _ in norm) + 1
        width = max(col for _, col in norm) + 1
        facts.append({
            "cells": component,
            "norm": norm,
            "family_key": _family_key(norm),
            "holes": _hole_count(grid, component),
            "size": len(component),
            "height": height,
            "width": width,
            "complete_border": _complete_border(norm),
        })
    return facts


_PUBLIC_OBJECTS = {
    profile: [obj["norm"] for obj in _object_facts(grid)]
    for profile, grid in _PUBLIC_INPUTS.items()
}
_PUBLIC_FAMILY_SIGNATURES = {
    tuple(sorted(_family_key(shape) for shape in shapes)): profile
    for profile, shapes in _PUBLIC_OBJECTS.items()
}
_GENERAL_HOLES = {
    "all_counts": (1, 2, 3, 4),
    "one_focus": (1, 1, 1, 2, 3, 4),
    "two_focus": (1, 2, 2, 2, 3, 3, 4),
    "high_focus": (1, 2, 3, 3, 4, 4),
}
_GENERAL_SIGNATURES = {tuple(sorted(value)): profile for profile, value in _GENERAL_HOLES.items()}


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_SIGNATURES.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    height, width = len(grid), len(grid[0])
    components = _object_facts(grid)
    if not 12 <= height <= 30 or not 12 <= width <= 30:
        errors.append("calibrated canvas dimensions must be twelve through thirty")
    if any(value not in (0, 8) for row in grid for value in row):
        errors.append("calibrated input palette must be exactly zero and eight")
    if not 4 <= len(components) <= 7:
        errors.append(f"expected four through seven separate color-8 objects, got {len(components)}")
    for index, obj in enumerate(components):
        if not obj["complete_border"]:
            errors.append(f"object {index} must contain its complete bounding-box border")
        if not 10 <= obj["size"] <= 55:
            errors.append(f"object {index} size must be ten through fifty-five")
        if not 3 <= obj["height"] <= 9 or not 3 <= obj["width"] <= 9:
            errors.append(f"object {index} bounding box must have sides three through nine")
        if obj["holes"] not in (1, 2, 3, 4):
            errors.append(f"object {index} must have one through four bounding-box zero regions")
    family_signature = tuple(sorted(obj["family_key"] for obj in components))
    hole_signature = tuple(sorted(obj["holes"] for obj in components))
    profile = _PUBLIC_FAMILY_SIGNATURES.get(family_signature)
    if profile is None:
        profile = _GENERAL_SIGNATURES.get(hole_signature)
    if profile is None:
        errors.append(f"unsupported calibrated hole/morphology signature {hole_signature!r}")
    output = rule_mirror(grid)
    if not errors and any(output[row][col] == 8 for obj in components for row, col in obj["cells"]):
        errors.append("every calibrated color-8 object must visibly change")
    return {
        "errors": errors,
        "scene_profile": profile if not errors else None,
        "facts": {
            "objects": components,
            "object_count": len(components),
            "hole_signature": hole_signature,
            "family_signature": family_signature,
        },
        "output": output,
    }


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    return analysis["scene_profile"] if not analysis["errors"] else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def _partition_shape(holes, difficulty, rng):
    maximum = 6 if difficulty == "easy" else 9 if difficulty == "hard" else 8
    for _ in range(200):
        if holes == 1:
            height, width = rng.randint(3, maximum), rng.randint(3, maximum)
            if 2 * height + 2 * width - 4 < 10:
                continue
        elif holes == 2:
            if rng.random() < 0.5:
                height, width = rng.randint(3, maximum), rng.randint(5, maximum)
            else:
                height, width = rng.randint(5, maximum), rng.randint(3, maximum)
        else:
            height, width = rng.randint(5, maximum), rng.randint(5, maximum)
        cells = {
            (row, col)
            for row in range(height) for col in range(width)
            if row in (0, height - 1) or col in (0, width - 1)
        }
        if holes == 2:
            if width >= 5 and (height < 5 or rng.random() < 0.5):
                split = rng.randint(2, width - 3)
                cells.update((row, split) for row in range(height))
            else:
                split = rng.randint(2, height - 3)
                cells.update((split, col) for col in range(width))
        elif holes == 3:
            split_col = rng.randint(2, width - 3)
            split_row = rng.randint(2, height - 3)
            cells.update((row, split_col) for row in range(height))
            if rng.random() < 0.5:
                cells.update((split_row, col) for col in range(split_col + 1))
            else:
                cells.update((split_row, col) for col in range(split_col, width))
        elif holes == 4:
            split_col = rng.randint(2, width - 3)
            split_row = rng.randint(2, height - 3)
            cells.update((row, split_col) for row in range(height))
            cells.update((split_row, col) for col in range(width))
        for _ in range(rng.randint(2, 16)):
            candidates = [
                (row, col)
                for row in range(1, height - 1)
                for col in range(1, width - 1)
                if (row, col) not in cells
                and any(other in cells for other in ((row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1)))
            ]
            if not candidates:
                break
            row, col = rng.choice(candidates)
            trial = _normalize(cells | {(row, col)})
            if len(trial) <= 55 and _shape_holes(trial) == holes:
                cells.add((row, col))
        norm = _normalize(cells)
        if 10 <= len(norm) <= 55 and _shape_holes(norm) == holes and _complete_border(norm):
            return rng.choice(_variants(norm))
    raise AssertionError(f"could not synthesize {holes}-region object")


def _place_shapes(height, width, shapes, rng):
    indexed = sorted(enumerate(shapes), key=lambda item: len(item[1]), reverse=True)
    placements, boxes = {}, []
    for index, shape in indexed:
        shape_height = max(row for row, _ in shape) + 1
        shape_width = max(col for _, col in shape) + 1
        candidates = [
            (row0, col0)
            for row0 in range(height - shape_height + 1)
            for col0 in range(width - shape_width + 1)
        ]
        rng.shuffle(candidates)
        for row0, col0 in candidates:
            row1, col1 = row0 + shape_height - 1, col0 + shape_width - 1
            if any(not (row1 + 1 < other[0] or other[1] + 1 < row0 or col1 + 1 < other[2] or other[3] + 1 < col0) for other in boxes):
                continue
            placements[index] = {(row0 + row, col0 + col) for row, col in shape}
            boxes.append((row0, row1, col0, col1))
            break
        else:
            raise AssertionError("could not pack separated hole-count objects")
    grid = [[0] * width for _ in range(height)]
    for cells in placements.values():
        for row, col in cells:
            grid[row][col] = 8
    return grid


def _limits(difficulty):
    if difficulty == "easy":
        return 17, 20
    if difficulty == "medium":
        return 21, 24
    if difficulty == "hard":
        return 25, 28
    return 18, 25


def _public_scene(profile, difficulty, rng):
    low, high = _limits(difficulty)
    for _ in range(240):
        shapes = [rng.choice(_variants(shape)) for shape in _PUBLIC_OBJECTS[profile]]
        try:
            grid = _place_shapes(rng.randint(low, high), rng.randint(low, high), shapes, rng)
        except AssertionError:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct public morphology family {profile!r}")


def _general_scene(profile, difficulty, rng):
    low, high = _limits(difficulty)
    for _ in range(240):
        shapes = [_partition_shape(holes, difficulty, rng) for holes in _GENERAL_HOLES[profile]]
        try:
            grid = _place_shapes(rng.randint(low, high), rng.randint(low, high), shapes, rng)
        except AssertionError:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct generalized hole-count family {profile!r}")


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
    profile = ctx.draw_choice("scene_profile", list(PUBLIC_PROFILES) * 3 + list(GENERAL_PROFILES) * 2)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES and overrides.get("scene_profile") is not None:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    rng = ctx.draw_rng("objects")
    grid = _public_scene(profile, difficulty, rng) if profile in PUBLIC_PROFILES else _general_scene(profile, difficulty, rng)
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid hole-count lesson: " + "; ".join(errors))
    return grid
