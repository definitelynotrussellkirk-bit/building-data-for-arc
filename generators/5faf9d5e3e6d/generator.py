"""Generator for transform-the-object-by-the-key-cell.

The cell at (0, 0) is a key: 1=identity, 2=rotate 90 degrees clockwise,
3=rotate 180 degrees, and 4=flip left/right. Remove that key, crop the
remaining nonzero pattern, and apply the selected transform.

The first four sample indices of each five-pair lesson are a seed-dependent
permutation of all four keys. The fifth (query) key varies by seed. Bodies use
one or two colors, vary in size and placement, and are rejected unless the
four canonical transforms produce four different crops.
"""
from __future__ import annotations

from typing import Iterable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5faf9d5e3e6d"
VERSION = "2.0.0"
TASK_ID = "5faf9d5e3e6d"
RULE_HASH = "abd7c563a610"

SUMMARY = (
    "A unique transform key at (0,0) selects identity, clockwise rotation, "
    "180-degree rotation, or horizontal reflection of the cropped nonzero "
    "body. Every lesson demonstrates all four key meanings before a "
    "seed-varying query; generated bodies make the four answers distinct."
)

INVARIANTS = [
    "background is 0 and the only key-colored cell is at (0,0)",
    "the key is one of 1,2,3,4 with the canonical transform meaning",
    "the body is one 8-connected pattern using one or two non-key colors",
    "the body lies inside a 2..5 by 2..5 bbox",
    "identity, rotate-cw, rotate-180, and flip-lr yield four distinct crops",
]

POSITION_ZONES = ("upper_left", "upper_right", "lower_left", "lower_right")
_ALLOWED_OVERRIDES = {
    "grid_h",
    "grid_w",
    "key_code",
    "body_h",
    "body_w",
    "body_color_count",
    "position_zone",
}

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 7..14", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware 8..14", "valid": "8..14"},
    "key_code": {"type": "int", "default": "lesson schedule", "valid": "1..4"},
    "body_h": {"type": "int", "default": "difficulty-aware 2..5", "valid": "2..5"},
    "body_w": {"type": "int", "default": "difficulty-aware 2..5", "valid": "2..5"},
    "body_color_count": {"type": "int", "default": "lesson schedule", "valid": "1..2"},
    "position_zone": {
        "type": "str",
        "default": "lesson schedule",
        "valid": "upper_left|upper_right|lower_left|lower_right",
    },
}


def _stable_random(seed: int, cycle: int, label: str):
    return stable_rng(seed, f"{TASK_ID}|{cycle}|{label}", VERSION)


def _scheduled_value(
    seed: int,
    sample_index: int,
    label: str,
    training_values: Iterable[int | str],
    query_values: Iterable[int | str],
):
    """Return a seed-varying five-pair lesson schedule.

    The four training positions use a shuffled fixed multiset. The query
    position is sampled independently, so no transform or nuisance value is
    tied to the test slot.
    """
    cycle, position = divmod(int(sample_index), 5)
    rng = _stable_random(int(seed), cycle, label)
    training = list(training_values)
    rng.shuffle(training)
    if position < 4:
        return training[position]
    return rng.choice(list(query_values))


def _draw_int_axis(ctx, overrides, label, default_lo, default_hi, valid_lo, valid_hi):
    if label in overrides:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _transform_outputs(body):
    return (body, _rotate_cw(body), _rotate_180(body), _flip_lr(body))


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def _four_answers_are_distinct(body) -> bool:
    return len({_grid_key(output) for output in _transform_outputs(body)}) == 4


def _is_eight_connected(body) -> bool:
    points = {
        (row, col)
        for row, values in enumerate(body)
        for col, value in enumerate(values)
        if value != 0
    }
    if not points:
        return False
    pending = [next(iter(points))]
    reached = set(pending)
    while pending:
        row, col = pending.pop()
        for drow in (-1, 0, 1):
            for dcol in (-1, 0, 1):
                if drow == dcol == 0:
                    continue
                neighbor = (row + drow, col + dcol)
                if neighbor in points and neighbor not in reached:
                    reached.add(neighbor)
                    pending.append(neighbor)
    return reached == points


def _body_bbox(grid):
    points = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and (row, col) != (0, 0)
    ]
    if not points:
        return None
    return (
        min(row for row, _ in points),
        min(col for _, col in points),
        max(row for row, _ in points),
        max(col for _, col in points),
    )


def _crop_body(grid):
    bbox = _body_bbox(grid)
    if bbox is None:
        return None
    top, left, bottom, right = bbox
    return [row[left : right + 1] for row in grid[top : bottom + 1]]


def _candidate_body(rng, height: int, width: int, colors: tuple[int, ...]):
    area = height * width
    min_cells = max(3, len(colors), (area + 3) // 4)
    max_cells = max(min_cells, min(area - 1, (3 * area + 3) // 4))
    cell_count = rng.randint(min_cells, max_cells)
    coordinates = [(row, col) for row in range(height) for col in range(width)]
    chosen = rng.sample(coordinates, cell_count)
    chosen_set = set(chosen)
    if not (
        any(row == 0 for row, _ in chosen_set)
        and any(row == height - 1 for row, _ in chosen_set)
        and any(col == 0 for _, col in chosen_set)
        and any(col == width - 1 for _, col in chosen_set)
    ):
        return None

    body = full_grid(height, width, 0)
    shuffled = list(chosen)
    rng.shuffle(shuffled)
    for index, (row, col) in enumerate(shuffled):
        color = colors[index] if index < len(colors) else rng.choice(colors)
        body[row][col] = color
    if {value for row in body for value in row if value} != set(colors):
        return None
    return body


def _build_body(rng, height: int, width: int, colors: tuple[int, ...]):
    if height == width == 2 and len(colors) == 1:
        raise ValueError(
            "body_h=2, body_w=2, body_color_count=1 cannot expose four distinct transforms"
        )
    for _ in range(400):
        body = _candidate_body(rng, height, width, colors)
        if (
            body is not None
            and _is_eight_connected(body)
            and _four_answers_are_distinct(body)
        ):
            return body
    raise RuntimeError(
        f"could not construct an unambiguous {height}x{width} body with {len(colors)} colors"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    scheduled = dict(overrides)
    scheduled.setdefault(
        "key_code",
        _scheduled_value(seed, sample_index, "key", (1, 2, 3, 4), (1, 2, 3, 4)),
    )
    scheduled.setdefault(
        "body_color_count",
        _scheduled_value(seed, sample_index, "body-colors", (1, 1, 2, 2), (1, 2)),
    )
    scheduled.setdefault(
        "position_zone",
        _scheduled_value(
            seed,
            sample_index,
            "position",
            POSITION_ZONES,
            POSITION_ZONES,
        ),
    )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=scheduled,
    )

    if difficulty == "easy":
        grid_h_bounds, grid_w_bounds = (7, 9), (8, 10)
        body_h_bounds, body_w_bounds = (2, 3), (2, 3)
    elif difficulty == "hard":
        grid_h_bounds, grid_w_bounds = (10, 14), (11, 14)
        body_h_bounds, body_w_bounds = (3, 5), (3, 5)
    else:
        grid_h_bounds, grid_w_bounds = (8, 11), (9, 12)
        body_h_bounds, body_w_bounds = (2, 4), (2, 4)

    height = _draw_int_axis(ctx, overrides, "grid_h", *grid_h_bounds, 7, 14)
    width = _draw_int_axis(ctx, overrides, "grid_w", *grid_w_bounds, 8, 14)
    key = ctx.draw_int("key_code", 1, 4)
    body_color_count = ctx.draw_int("body_color_count", 1, 2)
    position_zone = ctx.draw_choice("position_zone", POSITION_ZONES)

    body_h_lo, body_h_hi = body_h_bounds
    body_w_lo, body_w_hi = body_w_bounds
    if body_color_count == 1 and overrides.get("body_w") == 2 and "body_h" not in overrides:
        body_h_lo = max(body_h_lo, 3)
    body_h = _draw_int_axis(ctx, overrides, "body_h", body_h_lo, body_h_hi, 2, 5)
    if body_color_count == 1 and body_h == 2 and "body_w" not in overrides:
        body_w_lo = max(body_w_lo, 3)
    body_w = _draw_int_axis(ctx, overrides, "body_w", body_w_lo, body_w_hi, 2, 5)
    if body_color_count == 1 and body_h == body_w == 2:
        raise ValueError(
            "body_h=2, body_w=2, body_color_count=1 cannot expose four distinct transforms"
        )

    rng = ctx.draw_rng("layout")
    legal_colors = [color for color in range(1, 10) if color != key]
    colors = tuple(rng.sample(legal_colors, body_color_count))
    body = _build_body(rng, body_h, body_w, colors)

    vertical, horizontal = position_zone.split("_")
    top = 1 if vertical == "upper" else height - body_h
    left = 1 if horizontal == "left" else width - body_w
    if top < 1 or left < 1:
        raise ValueError(
            f"body {body_h}x{body_w} does not fit position_zone={position_zone} "
            f"inside grid {height}x{width}"
        )

    grid = full_grid(height, width, 0)
    grid[0][0] = key
    for row in range(body_h):
        for col in range(body_w):
            grid[top + row][left + col] = body[row][col]
    return grid


def observe_overrides(grid):
    if not grid or not grid[0]:
        return {}
    bbox = _body_bbox(grid)
    observed = {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "key_code": grid[0][0],
    }
    if bbox is None:
        return observed
    top, left, bottom, right = bbox
    body_h = bottom - top + 1
    body_w = right - left + 1
    body_colors = {
        grid[row][col]
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if grid[row][col] != 0
    }
    vertical = "upper" if top == 1 else "lower" if top == len(grid) - body_h else None
    horizontal = (
        "left" if left == 1 else "right" if left == len(grid[0]) - body_w else None
    )
    observed.update(
        {
            "body_h": body_h,
            "body_w": body_w,
            "body_color_count": len(body_colors),
        }
    )
    if vertical is not None and horizontal is not None:
        observed["position_zone"] = f"{vertical}_{horizontal}"
    return observed


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["grid is empty"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid colors must be integers in 0..9"]

    height, width = len(grid), len(grid[0])
    errors = []
    if not (7 <= height <= 14 and 8 <= width <= 14):
        errors.append(f"grid dimensions must be within 7..14 by 8..14, got {height}x{width}")

    key = grid[0][0]
    if key not in (1, 2, 3, 4):
        errors.append(f"cell (0,0) must be a transform key in 1..4, got {key}")
    if key in (1, 2, 3, 4):
        duplicate_keys = sum(
            value == key
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if (row, col) != (0, 0)
        )
        if duplicate_keys:
            errors.append("the key color must occur only at (0,0)")

    if any(grid[0][col] != 0 for col in range(1, width)) or any(
        grid[row][0] != 0 for row in range(1, height)
    ):
        errors.append("the body must be separated from the key by an empty top row and left column")

    body = _crop_body(grid)
    if body is None:
        errors.append("no body cells found outside (0,0)")
        return errors

    body_h, body_w = len(body), len(body[0])
    if not (2 <= body_h <= 5 and 2 <= body_w <= 5):
        errors.append(f"body bbox must be 2..5 by 2..5, got {body_h}x{body_w}")
    body_cells = [value for row in body for value in row if value != 0]
    if len(body_cells) < 3:
        errors.append("body must contain at least three nonzero cells")
    body_colors = set(body_cells)
    if not (1 <= len(body_colors) <= 2):
        errors.append(f"body must use one or two colors, got {len(body_colors)}")
    if key in body_colors:
        errors.append("body colors must exclude the transform-key color")
    if not _is_eight_connected(body):
        errors.append("body must form one 8-connected object")
    if not _four_answers_are_distinct(body):
        errors.append("body admits fewer than four distinct canonical transform answers")
    return errors
