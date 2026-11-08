"""Generator for E118 — crop the largest non-background object.

The canonical rule ranks 4-connected non-background objects by area, then by
uppermost bbox row, then by leftmost bbox column, and returns the selected
object's tight bounding-box crop.  Generated five-pair lessons deliberately
teach the unique-largest branch and both tie-break branches.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "2c7b1545edf9"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "6526de2b0dea"

SUMMARY = (
    "Place three through five isolated monochromatic objects. Select the "
    "largest by area; equal-largest objects are resolved by uppermost bbox "
    "row and then leftmost bbox column. Return the selected object's tight "
    "crop. Five-pair lessons demonstrate all three selection branches."
)

INVARIANTS = [
    "background is 0 and every nonzero object is 4-connected and monochromatic",
    "objects are orthogonally separated and the scene contains 3..5 objects",
    "the selected largest object is non-rectangular, so its crop contains background",
    "equal-largest scenes have exactly two maxima and expose either the topmost or leftmost tie-break",
    "repeated-distractor scenes repeat only a non-target color whose total frequency exceeds the target area",
]

SELECTION_MODES = ("unique_largest", "tied_topmost", "tied_leftmost")
COLOR_LAYOUTS = ("distinct", "repeated_distractor")
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 9..14", "valid": "9..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware 10..14", "valid": "10..14"},
    "n_blobs": {"type": "int", "default": "difficulty-aware 3..5", "valid": "3..5"},
    "selection_mode": {
        "type": "str",
        "default": "five-pair lesson schedule",
        "valid": "unique_largest|tied_topmost|tied_leftmost",
    },
    "color_layout": {
        "type": "str",
        "default": "five-pair lesson schedule",
        "valid": "distinct|repeated_distractor",
    },
}

_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _coerce_grid(grid):
    return [
        [int(value) if isinstance(value, str) and value.isdigit() else value for value in row]
        for row in grid
    ]


def _components(grid):
    """Color-specific 4-connected nonzero objects in reading order."""
    height = len(grid)
    width = len(grid[0]) if grid else 0
    unseen = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        start_color = grid[start[0]][start[1]]
        pending = [start]
        cells = []
        while pending:
            row, col = pending.pop()
            cells.append((row, col))
            for drow, dcol in _CARDINALS:
                neighbor = (row + drow, col + dcol)
                if neighbor in unseen and grid[neighbor[0]][neighbor[1]] == start_color:
                    unseen.remove(neighbor)
                    pending.append(neighbor)
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        components.append(
            {
                "cells": tuple(sorted(cells)),
                "size": len(cells),
                "r1": min(rows),
                "c1": min(cols),
                "r2": max(rows),
                "c2": max(cols),
                "colors": frozenset(grid[row][col] for row, col in cells),
            }
        )
    return components


def _selected_object(components):
    return min(components, key=lambda obj: (-obj["size"], obj["r1"], obj["c1"]))


def _selection_mode(components):
    maximum = max(obj["size"] for obj in components)
    tied = [obj for obj in components if obj["size"] == maximum]
    if len(tied) == 1:
        return "unique_largest"
    top = min(obj["r1"] for obj in tied)
    top_tied = [obj for obj in tied if obj["r1"] == top]
    if len(top_tied) == 1:
        return "tied_topmost"
    return "tied_leftmost"


def _analysis(grid) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list"], "grid": None, "components": ()}
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return {"errors": ["grid rows must be non-empty lists or digit strings"], "grid": None, "components": ()}

    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return {"errors": ["grid must be rectangular"], "grid": coerced, "components": ()}

    errors = []
    height = len(coerced)
    if not 9 <= height <= 14:
        errors.append(f"grid height must be in 9..14, got {height}")
    if not 10 <= width <= 14:
        errors.append(f"grid width must be in 10..14, got {width}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in coerced for value in row):
        errors.append("every cell must be an integer color in 0..9")
        return {"errors": errors, "grid": coerced, "components": ()}
    if not any(value == 0 for row in coerced for value in row):
        errors.append("background color 0 must be present")

    components = _components(coerced)
    if not 3 <= len(components) <= 5:
        errors.append(f"scene must contain 3..5 objects, got {len(components)}")
        return {"errors": errors, "grid": coerced, "components": tuple(components)}
    if any(len(obj["colors"]) != 1 for obj in components):
        errors.append("every connected object must be monochromatic")

    selected = _selected_object(components)
    bbox_area = (selected["r2"] - selected["r1"] + 1) * (
        selected["c2"] - selected["c1"] + 1
    )
    if bbox_area == selected["size"]:
        errors.append("selected object must be non-rectangular so the crop contains background")

    mode = _selection_mode(components)
    maximum = selected["size"]
    maxima = [obj for obj in components if obj["size"] == maximum]
    if mode != "unique_largest" and len(maxima) != 2:
        errors.append("tie scenes must contain exactly two equal-largest objects")
    if mode == "tied_leftmost":
        top = min(obj["r1"] for obj in maxima)
        top_tied = [obj for obj in maxima if obj["r1"] == top]
        if len(top_tied) != 2 or len({obj["c1"] for obj in top_tied}) != 2:
            errors.append("leftmost tie branch must have two maxima sharing the same top row")

    color_to_objects: dict[int, list[dict[str, Any]]] = {}
    for obj in components:
        if len(obj["colors"]) == 1:
            color = next(iter(obj["colors"]))
            color_to_objects.setdefault(color, []).append(obj)
    repeated = [members for members in color_to_objects.values() if len(members) > 1]
    if repeated:
        if len(repeated) != 1 or len(repeated[0]) != 2:
            errors.append("repeated-color scenes must repeat exactly one color on exactly two objects")
        else:
            members = repeated[0]
            if selected in members:
                errors.append("the selected target color must never repeat elsewhere")
            if any(member["size"] >= maximum for member in members):
                errors.append("repeated-color objects must both be smaller distractors")
            if sum(member["size"] for member in members) <= maximum:
                errors.append("repeated distractor color must outnumber the selected target in total")

    return {
        "errors": errors,
        "grid": coerced,
        "components": tuple(components),
        "selected": selected,
        "selection_mode": mode,
        "color_layout": "repeated_distractor" if repeated else "distinct",
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe overrides: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": len(analysis["grid"]),
        "grid_w": len(analysis["grid"][0]),
        "n_blobs": len(analysis["components"]),
        "selection_mode": analysis["selection_mode"],
        "color_layout": analysis["color_layout"],
    }


def rule_mirror(grid):
    """Python test mirror; the canonical Racket program remains authoritative."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    obj = analysis["selected"]
    return [
        row[obj["c1"] : obj["c2"] + 1]
        for row in analysis["grid"][obj["r1"] : obj["r2"] + 1]
    ]


def canonical_like(grid) -> bool:
    """Strict returned-grid predicate used by the pinned uniform census."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    selected = analysis["selected"]
    output = rule_mirror(grid)
    return (
        output
        and len(output) == selected["r2"] - selected["r1"] + 1
        and len(output[0]) == selected["c2"] - selected["c1"] + 1
        and len(output) < len(analysis["grid"])
        and len(output[0]) < len(analysis["grid"][0])
        and any(value == 0 for row in output for value in row)
    )


def _scheduled_value(seed, sample_index, label, training_values, query_values):
    cycle, position = divmod(int(sample_index), 5)
    rng = stable_rng(seed, f"{TASK_ID}|{cycle}|{label}", VERSION)
    training = list(training_values)
    rng.shuffle(training)
    if position < 4:
        return training[position]
    return rng.choice(tuple(query_values))


def _draw_int_axis(ctx, explicit, label, default_lo, default_hi, valid_lo, valid_hi):
    if label in explicit:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _random_polyomino(rng, size, *, max_h=4, max_w=4, require_nonrect=False):
    if size > max_h * max_w:
        raise ValueError(f"size {size} cannot fit in {max_h}x{max_w}")
    for _ in range(500):
        cells = {(rng.randrange(max_h), rng.randrange(max_w))}
        while len(cells) < size:
            frontier = {
                (row + drow, col + dcol)
                for row, col in cells
                for drow, dcol in _CARDINALS
                if 0 <= row + drow < max_h and 0 <= col + dcol < max_w
            } - cells
            if not frontier:
                break
            cells.add(rng.choice(sorted(frontier)))
        if len(cells) != size:
            continue
        min_row = min(row for row, _ in cells)
        min_col = min(col for _, col in cells)
        normalized = tuple(sorted((row - min_row, col - min_col) for row, col in cells))
        height = max(row for row, _ in normalized) + 1
        width = max(col for _, col in normalized) + 1
        if require_nonrect and (height < 2 or width < 2):
            continue
        if require_nonrect and height * width == size:
            continue
        return normalized
    raise ValueError(f"could not construct a size-{size} polyomino")


def _shape_dims(shape):
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _free(grid, shape, top, left, *, pad=1):
    height, width = len(grid), len(grid[0])
    shape_h, shape_w = _shape_dims(shape)
    if top < 0 or left < 0 or top + shape_h > height or left + shape_w > width:
        return False
    for row, col in shape:
        rr, cc = top + row, left + col
        for drow in range(-pad, pad + 1):
            for dcol in range(-pad, pad + 1):
                nr, nc = rr + drow, cc + dcol
                if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] != 0:
                    return False
    return True


def _place_random(grid, shape, color, rng):
    shape_h, shape_w = _shape_dims(shape)
    for _ in range(300):
        top = rng.randint(0, len(grid) - shape_h)
        left = rng.randint(0, len(grid[0]) - shape_w)
        if _free(grid, shape, top, left):
            paint_at(grid, top, left, shape, color)
            return (top, left)
    return None


def _place_tied_pair(grid, left_shape, right_shape, colors, mode, rng):
    left_h, left_w = _shape_dims(left_shape)
    right_h, right_w = _shape_dims(right_shape)
    height, width = len(grid), len(grid[0])
    if mode == "tied_leftmost":
        required_w = left_w + 1 + right_w
        if required_w > width:
            return False
        top = rng.randint(0, height - max(left_h, right_h))
        left = rng.randint(0, width - required_w)
        right = left + left_w + 1
        paint_at(grid, top, left, left_shape, colors[0])
        if not _free(grid, right_shape, top, right):
            return False
        paint_at(grid, top, right, right_shape, colors[1])
        return True

    required_h = left_h + 1 + right_h
    if required_h > height:
        return False
    top = rng.randint(0, height - required_h)
    bottom = top + left_h + 1
    first_left = rng.randint(0, width - left_w)
    second_left = rng.randint(0, width - right_w)
    paint_at(grid, top, first_left, left_shape, colors[0])
    if not _free(grid, right_shape, bottom, second_left):
        return False
    paint_at(grid, bottom, second_left, right_shape, colors[1])
    return True


def _component_sizes(rng, n_blobs, selection_mode):
    target = rng.randint(6, 8)
    if selection_mode == "unique_largest":
        return [target] + [target - offset for offset in range(1, n_blobs)]
    return [target, target] + [target - offset for offset in range(1, n_blobs - 1)]


def _component_colors(ctx, n_blobs, selection_mode, color_layout):
    tied_count = 1 if selection_mode == "unique_largest" else 2
    if color_layout == "distinct":
        return list(ctx.draw_distinct_colors("colors", n=n_blobs, exclude=(0,)))
    unique_count = n_blobs - 1
    palette = list(ctx.draw_distinct_colors("colors", n=unique_count, exclude=(0,)))
    colors = palette[:tied_count]
    repeated = palette[tied_count]
    colors.extend([repeated, repeated])
    colors.extend(palette[tied_count + 1 :])
    return colors


def _validate_call(difficulty, overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    band = "medium" if difficulty is None else difficulty
    scheduled = dict(overrides)
    scheduled.setdefault(
        "selection_mode",
        _scheduled_value(
            seed,
            sample_index,
            "selection-mode",
            ("unique_largest", "unique_largest", "tied_topmost", "tied_leftmost"),
            SELECTION_MODES,
        ),
    )
    scheduled.setdefault(
        "color_layout",
        _scheduled_value(
            seed,
            sample_index,
            "color-layout",
            ("distinct", "distinct", "repeated_distractor", "repeated_distractor"),
            COLOR_LAYOUTS,
        ),
    )
    if overrides.get("n_blobs") == 3:
        tied = scheduled["selection_mode"] != "unique_largest"
        repeated = scheduled["color_layout"] == "repeated_distractor"
        if tied and repeated:
            if "color_layout" not in overrides:
                scheduled["color_layout"] = "distinct"
            elif "selection_mode" not in overrides:
                scheduled["selection_mode"] = "unique_largest"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=scheduled,
    )
    selection_mode = ctx.draw_choice("selection_mode", SELECTION_MODES)
    color_layout = ctx.draw_choice("color_layout", COLOR_LAYOUTS)

    if band == "easy":
        h_bounds, w_bounds, n_bounds = (9, 10), (10, 11), (3, 4)
    elif band == "hard":
        h_bounds, w_bounds, n_bounds = (12, 14), (12, 14), (4, 5)
    else:
        h_bounds, w_bounds, n_bounds = (10, 12), (11, 13), (3, 5)

    if selection_mode != "unique_largest" and color_layout == "repeated_distractor":
        n_bounds = (max(4, n_bounds[0]), max(4, n_bounds[1]))
    height = _draw_int_axis(ctx, overrides, "grid_h", *h_bounds, 9, 14)
    width = _draw_int_axis(ctx, overrides, "grid_w", *w_bounds, 10, 14)
    n_blobs = _draw_int_axis(ctx, overrides, "n_blobs", *n_bounds, 3, 5)
    if selection_mode != "unique_largest" and color_layout == "repeated_distractor" and n_blobs < 4:
        raise ValueError(
            "tied selection with repeated_distractor requires n_blobs>=4 so the repeated color remains off both maxima"
        )

    colors = _component_colors(ctx, n_blobs, selection_mode, color_layout)
    rng = ctx.draw_rng("layout")
    sizes = _component_sizes(rng, n_blobs, selection_mode)

    for _ in range(600):
        grid = full_grid(height, width, 0)
        shapes = [
            _random_polyomino(
                rng,
                size,
                max_h=4,
                max_w=4,
                require_nonrect=(index == 0),
            )
            for index, size in enumerate(sizes)
        ]
        next_index = 0
        if selection_mode == "unique_largest":
            if _place_random(grid, shapes[0], colors[0], rng) is None:
                continue
            next_index = 1
        else:
            if not _place_tied_pair(
                grid,
                shapes[0],
                shapes[1],
                colors[:2],
                selection_mode,
                rng,
            ):
                continue
            next_index = 2

        placed = True
        for index in range(next_index, n_blobs):
            if _place_random(grid, shapes[index], colors[index], rng) is None:
                placed = False
                break
        if not placed:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and observe_overrides(grid) == {
            "grid_h": height,
            "grid_w": width,
            "n_blobs": n_blobs,
            "selection_mode": selection_mode,
            "color_layout": color_layout,
        }:
            return grid

    raise ValueError(
        f"could not place a lawful {selection_mode}/{color_layout} scene with "
        f"{n_blobs} objects in {height}x{width}; the override combination is incompatible"
    )
