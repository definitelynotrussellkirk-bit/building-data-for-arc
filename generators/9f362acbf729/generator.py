"""Generator for ARC task ``9f362acbf729`` — corner-key transform mosaic.

The four input corners are transform keys for the tight crop of every other
non-zero cell.  Key 1 rotates the crop 90° clockwise, key 2 rotates 180°,
key 3 flips left/right, and key 4 transposes.  The four transformed copies are
packed in the corresponding corner order as two top-aligned galleries with a
one-cell horizontal gap and one all-zero row between the galleries.
"""
from __future__ import annotations

from itertools import permutations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9f362acbf729"
VERSION = "2.0.0"
TASK_ID = "9f362acbf729"
RULE_HASH = "75692873c100"

SUMMARY = (
    "Read transform keys 1..4 from the four corners, tightly crop the remaining "
    "colored body, transform one copy per key, and pack the copies into a 2×2 "
    "top-aligned mosaic with one-cell gaps."
)

INVARIANTS = [
    "the input canvas is the canonical 5×5 shape",
    "background is 0 and all cells are ARC colors 0..9",
    "the four corners are a permutation of keys 1, 2, 3, and 4",
    "clearing the corner keys leaves a non-empty tight body crop at least 2×2",
    "ordinary generated bodies distinguish all four keyed transforms, except the canonical 2×2 monochrome three-image profile",
    "the canonical Racket program is the output authority",
]

_KEY_ORDERS = tuple("-".join(map(str, order)) for order in permutations((1, 2, 3, 4)))
_BODY_COLORS = (5, 6, 7, 8, 9)

AXES = {
    "body_h": {
        "type": "int",
        "default": "2..3 easy, 2..4 medium, 3..4 hard",
        "valid": "2..4",
    },
    "body_w": {
        "type": "int",
        "default": "2..3 easy, 2..4 medium, 3..4 hard",
        "valid": "2..4",
    },
    "palette_size": {
        "type": "int",
        "default": "1..2 easy, 1..3 medium, 2..3 hard",
        "valid": "1..3",
    },
    "key_order": {
        "type": "str",
        "default": "uniform permutation of 1-2-3-4",
        "valid": "1-2-3-4|1-2-4-3|1-3-2-4|1-3-4-2|1-4-2-3|1-4-3-2|2-1-3-4|2-1-4-3|2-3-1-4|2-3-4-1|2-4-1-3|2-4-3-1|3-1-2-4|3-1-4-2|3-2-1-4|3-2-4-1|3-4-1-2|3-4-2-1|4-1-2-3|4-1-3-2|4-2-1-3|4-2-3-1|4-3-1-2|4-3-2-1",
        "probe": "diagnostic",
    },
}


def _strict_int(value, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer (not bool), got {value!r}")
    return value


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _rotate_ccw(grid):
    return _rotate_cw(_rotate_180(grid))


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _crop_nonzero(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def _transform_by_key(shape, key):
    transform = {
        1: _rotate_cw,
        2: _rotate_180,
        3: _flip_lr,
        4: _transpose,
    }.get(key)
    return transform(shape) if transform is not None else [row[:] for row in shape]


def _pack_gallery(shapes, gap=1):
    height = max((len(shape) for shape in shapes), default=1)
    width = sum(len(shape[0]) for shape in shapes) + gap * max(0, len(shapes) - 1)
    out = full_grid(height, width, 0)
    left = 0
    for shape in shapes:
        for r, row in enumerate(shape):
            for c, value in enumerate(row):
                if value != 0:
                    out[r][left + c] = value
        left += len(shape[0]) + gap
    return out


def _assemble_mosaic(transformed):
    top = _pack_gallery(transformed[:2])
    bottom = _pack_gallery(transformed[2:])
    out_width = max(len(top[0]), len(bottom[0]))
    top = [row + [0] * (out_width - len(row)) for row in top]
    bottom = [row + [0] * (out_width - len(row)) for row in bottom]
    return top + [[0] * out_width] + bottom


def _grid_shape_error(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return "grid must be a non-empty list of non-empty rows"
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return "grid must be rectangular"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "grid colors must be integers in 0..9"
    return None


def _rule_facts(grid):
    height, width = len(grid), len(grid[0])
    keys = (
        grid[0][0],
        grid[0][width - 1],
        grid[height - 1][0],
        grid[height - 1][width - 1],
    )
    cleared = [row[:] for row in grid]
    for r, c in ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)):
        cleared[r][c] = 0
    shape = _crop_nonzero(cleared)
    transformed = tuple(_transform_by_key(shape, key) for key in keys)
    output = _assemble_mosaic(transformed)
    return {
        "keys": keys,
        "cleared": cleared,
        "shape": shape,
        "transformed": transformed,
        "output": output,
    }


def rule_mirror(grid):
    """Independent Python mirror; the canonical Racket program remains authority."""
    error = _grid_shape_error(grid)
    if error:
        raise ValueError(error)
    facts = _rule_facts(grid)
    if sorted(facts["keys"]) != [1, 2, 3, 4]:
        raise ValueError(f"corner keys must be a permutation of 1,2,3,4; got {facts['keys']}")
    if not any(value != 0 for row in facts["cleared"] for value in row):
        raise ValueError("clearing the four corners leaves no body cells")
    return [row[:] for row in facts["output"]]


def numeric_rotation_rival(grid):
    """Plausible wrong rule: treat key k as k clockwise quarter-turns."""
    error = _grid_shape_error(grid)
    if error:
        raise ValueError(error)
    facts = _rule_facts(grid)
    if sorted(facts["keys"]) != [1, 2, 3, 4]:
        raise ValueError("corner keys must be a permutation of 1,2,3,4")
    transforms = {
        1: _rotate_cw,
        2: _rotate_180,
        3: _rotate_ccw,
        4: lambda shape: [row[:] for row in shape],
    }
    transformed = tuple(transforms[key](facts["shape"]) for key in facts["keys"])
    return _assemble_mosaic(transformed)


SEMANTIC_RIVALS = {
    "numeric_rotation": numeric_rotation_rival,
}
SEMANTIC_WITNESSES = {
    "key_mapping_not_numeric_rotation": (
        lambda grid: rule_mirror(grid) != numeric_rotation_rival(grid)
    ),
}
WITNESS_RIVALS = {
    "key_mapping_not_numeric_rotation": ["numeric_rotation"],
}


def _analyze(grid):
    result = {"errors": []}
    error = _grid_shape_error(grid)
    if error:
        result["errors"].append(error)
        return result

    height, width = len(grid), len(grid[0])
    result.update({"grid_h": height, "grid_w": width})
    if (height, width) != (5, 5):
        result["errors"].append(f"input canvas must be canonical 5x5; got {height}x{width}")

    facts = _rule_facts(grid)
    result.update(facts)
    if sorted(facts["keys"]) != [1, 2, 3, 4]:
        result["errors"].append(
            f"corner keys must be a permutation of 1,2,3,4; got {facts['keys']}"
        )

    cells = [
        (r, c, value)
        for r, row in enumerate(facts["cleared"])
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        result["errors"].append("clearing the four corner keys leaves no body")
        return result

    shape = facts["shape"]
    body_h, body_w = len(shape), len(shape[0])
    result.update(
        {
            "body_h": body_h,
            "body_w": body_w,
            "palette_size": len({value for _, _, value in cells}),
            "key_order": "-".join(map(str, facts["keys"])),
            "transform_orbit": len({_grid_key(part) for part in facts["transformed"]}),
            "body_cell_count": len(cells),
        }
    )
    if body_h < 2 or body_w < 2:
        result["errors"].append(f"tight body crop must be at least 2x2; got {body_h}x{body_w}")
    if len(cells) < 3:
        result["errors"].append("body must contain at least three non-zero cells")
    canonical_three_image_exception = (
        body_h == body_w == 2 and result["palette_size"] == 1
    )
    required_orbit = 3 if canonical_three_image_exception else 4
    if result["transform_orbit"] != required_orbit:
        if canonical_three_image_exception:
            result["errors"].append(
                "canonical 2x2 monochrome body must expose exactly three distinct keyed transforms"
            )
        else:
            result["errors"].append(
                "body must expose four distinct canonical keyed transforms"
            )
    return result


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed or shortcut-prone scenes while accepting canonical inputs."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "body_h": analysis["body_h"],
        "body_w": analysis["body_w"],
        "palette_size": analysis["palette_size"],
        "key_order": analysis["key_order"],
    }


def _draw_int(ctx, label, full_bounds, default_bounds):
    lo, hi = full_bounds if ctx.overrides.get(label) is not None else default_bounds
    return ctx.draw_int_strict(label, lo, hi)


def _sample_body(ctx, *, grid_h, grid_w, body_h, body_w, palette):
    canvas_corners = {(0, 0), (0, grid_w - 1), (grid_h - 1, 0), (grid_h - 1, grid_w - 1)}
    for attempt in range(256):
        rng = ctx.draw_rng(f"body:{attempt}")
        r0 = rng.randint(0, grid_h - body_h)
        c0 = rng.randint(0, grid_w - body_w)
        allowed = [
            (r, c)
            for r in range(body_h)
            for c in range(body_w)
            if (r0 + r, c0 + c) not in canvas_corners
        ]
        allowed_set = set(allowed)
        edge_sets = (
            [(0, c) for c in range(body_w) if (0, c) in allowed_set],
            [(body_h - 1, c) for c in range(body_w) if (body_h - 1, c) in allowed_set],
            [(r, 0) for r in range(body_h) if (r, 0) in allowed_set],
            [(r, body_w - 1) for r in range(body_h) if (r, body_w - 1) in allowed_set],
        )
        if any(not edge for edge in edge_sets):
            continue
        active = {rng.choice(edge) for edge in edge_sets}
        minimum = max(3, len(palette))
        maximum = len(allowed)
        if maximum < minimum:
            continue
        low_target = max(minimum, (maximum + 2) // 3)
        target = rng.randint(low_target, maximum)
        remaining = [cell for cell in allowed if cell not in active]
        rng.shuffle(remaining)
        active.update(remaining[: max(0, target - len(active))])

        cells = list(active)
        rng.shuffle(cells)
        values = list(palette)
        values.extend(rng.choice(palette) for _ in range(len(cells) - len(values)))
        rng.shuffle(values)
        body = full_grid(body_h, body_w, 0)
        for (r, c), value in zip(cells, values):
            body[r][c] = value
        transformed = [_transform_by_key(body, key) for key in (1, 2, 3, 4)]
        required_orbit = 3 if body_h == body_w == 2 and len(palette) == 1 else 4
        if len({_grid_key(part) for part in transformed}) != required_orbit:
            continue
        return r0, c0, body
    raise RuntimeError("could not sample a tight transform-distinguishing body")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    seed = _strict_int(seed, "seed")
    sample_index = _strict_int(sample_index, "sample_index")
    if sample_index < 0:
        raise ValueError(f"sample_index must be nonnegative, got {sample_index}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None/easy/medium/hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    defaults = {
        "easy": {
            "body_h": (2, 3), "body_w": (2, 3), "palette_size": (1, 2),
        },
        "medium": {
            "body_h": (2, 4), "body_w": (2, 4), "palette_size": (1, 3),
        },
        "hard": {
            "body_h": (3, 4), "body_w": (3, 4), "palette_size": (2, 3),
        },
    }[band]
    grid_h = grid_w = 5
    body_h = _draw_int(ctx, "body_h", (2, 4), defaults["body_h"])
    body_w = _draw_int(ctx, "body_w", (2, 4), defaults["body_w"])
    palette_size = _draw_int(ctx, "palette_size", (1, 3), defaults["palette_size"])
    key_order = ctx.draw_choice("key_order", _KEY_ORDERS)
    keys = tuple(int(value) for value in key_order.split("-"))

    palette = tuple(ctx.draw_rng("palette").sample(_BODY_COLORS, palette_size))
    r0, c0, body = _sample_body(
        ctx,
        grid_h=grid_h,
        grid_w=grid_w,
        body_h=body_h,
        body_w=body_w,
        palette=palette,
    )
    grid = full_grid(grid_h, grid_w, 0)
    for r in range(body_h):
        for c in range(body_w):
            if body[r][c] != 0:
                grid[r0 + r][c0 + c] = body[r][c]
    grid[0][0], grid[0][-1], grid[-1][0], grid[-1][-1] = keys

    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator invariant failure: " + "; ".join(errors))
    return grid
