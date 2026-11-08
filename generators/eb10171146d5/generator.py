"""Generator for bank task M69 / eb10171146d5.

The input contains one connected blue-1 shape and one connected red-2 shape.
Normalize both to their own top-left corners, take their symmetric difference,
crop that difference to its bounding box, and render it in cyan 8.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "eb10171146d5"
VERSION = "4.1.0"
TASK_ID = "eb10171146d5"
RULE_HASH = "915cc17c87cf"

SUMMARY = (
    "Construct one separated connected blue shape and one connected red "
    "shape. Their top-left-normalized forms overlap but differ, so the "
    "rule emits a nonempty cyan symmetric difference cropped to its own "
    "bounding box. A controlled default prior covers all five complete "
    "public shape-pair profiles while most draws vary larger polyominoes."
)

INVARIANTS = [
    "the canvas is a 7..20 by 9..20 zero-background grid",
    "there is exactly one 4-connected color-1 object and one color-2 object",
    "the two absolute objects do not share an orthogonal edge",
    "each normalized object has 2..18 cells and fits within an 8x8 box",
    "the normalized shapes overlap and have a symmetric difference of at least two cells",
    "the cropped XOR has one to three 4-connected components",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 7..20",
        "valid": "7..20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 9..20",
        "valid": "9..20",
    },
}

_VALID_H = (7, 20)
_VALID_W = (9, 20)
_PROFILE_PRIOR = 0.07
_BAND_BOUNDS = {
    "easy": ((11, 14), (12, 16)),
    "medium": ((11, 16), (12, 18)),
    "hard": ((15, 20), (15, 20)),
}
_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _shape(*cells):
    return tuple(sorted(cells))


_PROFILE_SPECS = (
    {
        "height": 11,
        "width": 14,
        "blue": _shape((0, 0), (0, 1), (1, 1), (2, 1)),
        "red": _shape((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    },
    {
        "height": 10,
        "width": 12,
        "blue": _shape((0, 0), (0, 1), (1, 0), (1, 1)),
        "red": _shape((0, 0), (1, 0)),
    },
    {
        "height": 11,
        "width": 12,
        "blue": _shape((0, 1), (1, 0), (1, 1), (1, 2)),
        "red": _shape((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    },
    {
        "height": 9,
        "width": 13,
        "blue": _shape((0, 0), (1, 0)),
        "red": _shape((0, 0), (0, 1)),
    },
    {
        "height": 9,
        "width": 12,
        "blue": _shape((0, 0), (1, 0), (1, 1)),
        "red": _shape((0, 1), (1, 0), (1, 1), (1, 2)),
    },
)
for _spec in _PROFILE_SPECS:
    _spec["signature"] = (
        _spec["height"],
        _spec["width"],
        _spec["blue"],
        _spec["red"],
    )
_CANONICAL_PROFILE_SIGNATURES = frozenset(
    spec["signature"] for spec in _PROFILE_SPECS
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _components(grid, color):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            todo = deque([(row, col)])
            seen.add((row, col))
            cells = set()
            while todo:
                rr, cc = todo.popleft()
                cells.add((rr, cc))
                for dr, dc in _DELTAS:
                    nr = rr + dr
                    nc = cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append(cells)
    return result


def _normalize(cells):
    min_row = min(row for row, _col in cells)
    min_col = min(col for _row, col in cells)
    return tuple(sorted(
        (row - min_row, col - min_col) for row, col in cells
    ))


def _bbox_shape(cells):
    return (
        max(row for row, _col in cells) + 1,
        max(col for _row, col in cells) + 1,
    )


def _component_count(cells):
    cells = set(cells)
    count = 0
    seen = set()
    for start in sorted(cells):
        if start in seen:
            continue
        count += 1
        todo = [start]
        seen.add(start)
        while todo:
            row, col = todo.pop()
            for dr, dc in _DELTAS:
                neighbor = row + dr, col + dc
                if neighbor in cells and neighbor not in seen:
                    seen.add(neighbor)
                    todo.append(neighbor)
    return count


def _xor_features(blue, red):
    blue_set = set(blue)
    red_set = set(red)
    xor_raw = blue_set ^ red_set
    if not xor_raw:
        return {
            "overlap": len(blue_set & red_set),
            "raw": frozenset(),
            "normalized": (),
            "shape": (0, 0),
            "components": 0,
            "crop_offset": (0, 0),
        }
    min_row = min(row for row, _col in xor_raw)
    min_col = min(col for _row, col in xor_raw)
    normalized = _normalize(xor_raw)
    return {
        "overlap": len(blue_set & red_set),
        "raw": frozenset(xor_raw),
        "normalized": normalized,
        "shape": _bbox_shape(normalized),
        "components": _component_count(normalized),
        "crop_offset": (min_row, min_col),
    }


def _scene_shapes(grid):
    blue_components = _components(grid, 1)
    red_components = _components(grid, 2)
    if len(blue_components) != 1 or len(red_components) != 1:
        return None
    return (
        _normalize(blue_components[0]),
        _normalize(red_components[0]),
        blue_components[0],
        red_components[0],
    )


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]

    errors = []
    height = len(coerced)
    if not _VALID_H[0] <= height <= _VALID_H[1]:
        errors.append("grid height must be in 7..20")
    if not _VALID_W[0] <= width <= _VALID_W[1]:
        errors.append("grid width must be in 9..20")
    if any(
        type(value) is not int or value not in (0, 1, 2)
        for row in coerced
        for value in row
    ):
        errors.append("input colors must be integer 0, 1, or 2")
        return errors

    shapes = _scene_shapes(coerced)
    if shapes is None:
        errors.append(
            "exactly one 4-connected blue object and one red object are required"
        )
        return errors
    blue, red, blue_absolute, red_absolute = shapes
    for label, shape in (("blue", blue), ("red", red)):
        if not 2 <= len(shape) <= 18:
            errors.append(f"{label} shape must contain 2..18 cells")
        box_h, box_w = _bbox_shape(shape)
        if box_h > 8 or box_w > 8:
            errors.append(f"{label} shape must fit within an 8x8 box")

    if any(
        abs(ar - br) + abs(ac - bc) <= 1
        for ar, ac in blue_absolute
        for br, bc in red_absolute
    ):
        errors.append("the two absolute objects may not touch orthogonally")

    xor = _xor_features(blue, red)
    if xor["overlap"] == 0:
        errors.append("normalized shapes must overlap")
    if len(xor["raw"]) < 2:
        errors.append(
            "normalized symmetric difference must contain at least two cells"
        )
    if xor["components"] not in (1, 2, 3):
        errors.append("cropped XOR must have one to three components")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    coerced = _coerce_grid(grid)
    blue, red, _blue_absolute, _red_absolute = _scene_shapes(coerced)
    xor = _xor_features(blue, red)
    cells = set(xor["normalized"])
    height, width = xor["shape"]
    return [
        [8 if (row, col) in cells else 0 for col in range(width)]
        for row in range(height)
    ]


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    coerced = _coerce_grid(grid)
    blue, red, _blue_absolute, _red_absolute = _scene_shapes(coerced)
    signature = (len(coerced), len(coerced[0]), blue, red)
    return signature if signature in _CANONICAL_PROFILE_SIGNATURES else None


def is_canonical_profile(grid):
    return (
        canonical_profile_signature(grid)
        in _CANONICAL_PROFILE_SIGNATURES
    )


def _random_polyomino(rng, size, max_span=6):
    cells = {(0, 0)}
    while len(cells) < size:
        frontier = set()
        for row, col in cells:
            for dr, dc in _DELTAS:
                candidate = row + dr, col + dc
                if candidate in cells:
                    continue
                trial = _normalize(cells | {candidate})
                box_h, box_w = _bbox_shape(trial)
                if box_h <= max_span and box_w <= max_span:
                    frontier.add(candidate)
        if not frontier:
            return None
        cells.add(rng.choice(sorted(frontier)))
    return _normalize(cells)


def _translated(cells, top, left):
    return {(top + row, left + col) for row, col in cells}


def _separated(blue, red):
    return all(
        abs(ar - br) + abs(ac - bc) > 1
        for ar, ac in blue
        for br, bc in red
    )


def _placements(cells, height, width):
    box_h, box_w = _bbox_shape(cells)
    return [
        (top, left)
        for top in range(height - box_h + 1)
        for left in range(width - box_w + 1)
    ]


def _place_shapes(height, width, blue, red, rng):
    blue_positions = _placements(blue, height, width)
    red_positions = _placements(red, height, width)
    rng.shuffle(blue_positions)
    rng.shuffle(red_positions)
    prefer_boundary = rng.random() < 0.55
    if prefer_boundary:
        blue_positions.sort(
            key=lambda item: (
                item[0] not in (0, height - _bbox_shape(blue)[0])
                and item[1] not in (0, width - _bbox_shape(blue)[1])
            )
        )
    for blue_top, blue_left in blue_positions:
        blue_absolute = _translated(blue, blue_top, blue_left)
        for red_top, red_left in red_positions:
            red_absolute = _translated(red, red_top, red_left)
            if _separated(blue_absolute, red_absolute):
                grid = full_grid(height, width, 0)
                for row, col in blue_absolute:
                    grid[row][col] = 1
                for row, col in red_absolute:
                    grid[row][col] = 2
                return grid
    return None


def _draw_profile(spec, rng):
    grid = _place_shapes(
        spec["height"],
        spec["width"],
        spec["blue"],
        spec["red"],
        rng,
    )
    if grid is None:
        raise AssertionError("could not place exact public profile")
    if canonical_profile_signature(grid) != spec["signature"]:
        raise AssertionError("constructed profile signature drifted")
    return grid


def _draw_general(height, width, band, rng):
    size_ranges = {
        "easy": (7, 14),
        "medium": (7, 14),
        "hard": (9, 18),
    }
    size_lo, size_hi = size_ranges[band]
    max_span = max(2, min(8, (min(height, width) - 1) // 2))
    size_hi = min(size_hi, max_span * max_span)
    # A forced narrow canvas can reduce the normalized box to 3x3. Keep
    # several unoccupied cells available so the two shapes need not collapse
    # to the same full box and can still have a varied XOR.
    size_lo = min(size_lo, max(2, size_hi - 3))
    for _ in range(3_000):
        blue = _random_polyomino(
            rng,
            rng.randint(size_lo, size_hi),
            max_span=max_span,
        )
        red = _random_polyomino(
            rng,
            rng.randint(size_lo, size_hi),
            max_span=max_span,
        )
        if blue is None or red is None:
            continue
        xor = _xor_features(blue, red)
        if xor["overlap"] == 0 or len(xor["raw"]) < 2:
            continue
        if xor["components"] not in (1, 2, 3):
            continue
        grid = _place_shapes(height, width, blue, red, rng)
        if grid is not None:
            return grid
    raise AssertionError(
        f"could not construct lawful normalized-XOR scene in {height}x{width}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    has_override = any(
        overrides.get(label) is not None for label in AXES
    )
    profile_index = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_SPECS))),
            )

    if profile_index is not None:
        spec = _PROFILE_SPECS[profile_index]
        height = ctx.draw_int(
            "grid_h", spec["height"], spec["height"]
        )
        width = ctx.draw_int(
            "grid_w", spec["width"], spec["width"]
        )
        grid = _draw_profile(spec, ctx.draw_rng("layout"))
    else:
        height_bounds, width_bounds = _BAND_BOUNDS[band]
        if overrides.get("grid_h") is not None:
            height = ctx.draw_int("grid_h", *_VALID_H)
        else:
            height = ctx.draw_int("grid_h", *height_bounds)
        if overrides.get("grid_w") is not None:
            width = ctx.draw_int("grid_w", *_VALID_W)
        else:
            width = ctx.draw_int("grid_w", *width_bounds)
        grid = _draw_general(
            height,
            width,
            band,
            ctx.draw_rng("layout"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
