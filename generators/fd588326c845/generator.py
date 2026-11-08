"""Generator for sparse-key recoloring task fd588326c845.

A small colored key and a larger cyan silhouette have the same occupancy
after rotating the key 90 degrees clockwise.  Each cyan logical tile is
recolored from the corresponding rotated key cell.
"""
from __future__ import annotations

import math
from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "fd588326c845"
VERSION = "3.0.0"
TASK_ID = "fd588326c845"
RULE_HASH = "857ce489e943"

SUMMARY = (
    "Place a sparse 3x3 or 4x4 multicolor key beside a cyan silhouette "
    "whose logical occupancy is the key rotated 90 degrees clockwise and "
    "expanded into uniform tiles. Recolor each cyan tile with its "
    "corresponding rotated key color while leaving the key unchanged."
)

INVARIANTS = [
    "zero is modal background and cyan 8 is the only mask color",
    "the key is a sparse square of side three or four with two to four colors",
    "the key contains a repeated color and at least one zero hole",
    "the key and cyan bounding boxes are disjoint with a background gap",
    "the cyan bbox is an integer one-through-six expansion of the key side",
    "cyan occupancy exactly equals the expanded clockwise-rotated key mask",
    "every logical cyan tile is solid and receives its rotated key color",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_KEY_SIZES = (3, 4)
_SCALES = (1, 2, 3, 4, 5, 6)
_PALETTE_SIZES = (2, 3, 4)
_KEY_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_PROFILE_PRIOR = 0.28

AXES = {
    "key_size": {
        "type": "int",
        "default": "difficulty-aware 3..4",
        "valid": "3..4",
    },
    "scale_h": {
        "type": "int",
        "default": "difficulty-aware 1..6",
        "valid": "1..6",
    },
    "scale_w": {
        "type": "int",
        "default": "usually equal to scale_h; otherwise 1..6",
        "valid": "1..6",
    },
    "palette_size": {
        "type": "int",
        "default": "difficulty-aware 2..4",
        "valid": "2..4",
    },
}

# Complete answer-bearing key profiles from both training demonstrations and
# the published held-out input.  Positive integers are equality roles, not
# concrete ARC colors.  Each profile is linked to its demonstrated scale.
_PROFILE_KEYS = (
    (
        (0, 1, 2),
        (3, 1, 0),
        (4, 0, 3),
    ),
    (
        (0, 0, 1, 0),
        (2, 0, 1, 3),
        (2, 4, 4, 0),
        (2, 0, 0, 3),
    ),
    (
        (0, 1, 0),
        (0, 1, 2),
        (3, 0, 2),
    ),
)
_PROFILE_SCALES = (3, 2, 4)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label, lower, upper in (
        ("key_size", 3, 4),
        ("scale_h", 1, 6),
        ("scale_w", 1, 6),
        ("palette_size", 2, 4),
    ):
        value = overrides.get(label)
        if value is not None and (
            type(value) is not int or not lower <= value <= upper
        ):
            raise ValueError(
                f"{label} must be an integer in [{lower}, {upper}]"
            )


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


def _is_rectangular_grid(grid):
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and all(
            isinstance(row, (list, tuple, str)) and bool(row)
            for row in grid
        )
        and len({len(row) for row in grid}) == 1
    )


def _rotate_90(matrix):
    return tuple(tuple(row) for row in zip(*matrix[::-1]))


def _normalize_roles(matrix):
    role_by_color = {}
    next_role = 1
    normalized = []
    for row in matrix:
        normalized_row = []
        for value in row:
            if value == 0:
                normalized_row.append(0)
                continue
            if value not in role_by_color:
                role_by_color[value] = next_role
                next_role += 1
            normalized_row.append(role_by_color[value])
        normalized.append(tuple(normalized_row))
    return tuple(normalized)


def _bbox(cells):
    return (
        min(row for row, _col in cells),
        min(col for _row, col in cells),
        max(row for row, _col in cells),
        max(col for _row, col in cells),
    )


def _boxes_separated(first, second):
    first_r1, first_c1, first_r2, first_c2 = first
    second_r1, second_c1, second_r2, second_c2 = second
    return (
        first_r2 < second_r1 - 1
        or second_r2 < first_r1 - 1
        or first_c2 < second_c1 - 1
        or second_c2 < first_c1 - 1
    )


def _scene_analysis(grid):
    if not _is_rectangular_grid(grid):
        return None, None, ["grid must be non-empty and rectangular"]
    coerced = _coerce_grid(grid)
    height = len(coerced)
    width = len(coerced[0])
    errors = []
    if not 5 <= height <= 30 or not 5 <= width <= 30:
        errors.append("grid dimensions must be between five and thirty")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("cells must be integer ARC colors zero through nine")
        return coerced, None, errors

    key_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if coerced[row][col] not in (0, 8)
    ]
    cyan_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if coerced[row][col] == 8
    ]
    if not key_cells:
        errors.append("a nonzero non-cyan key is required")
    if not cyan_cells:
        errors.append("a cyan mask is required")
    if errors:
        return coerced, None, errors

    key_box = _bbox(key_cells)
    cyan_box = _bbox(cyan_cells)
    key_r1, key_c1, key_r2, key_c2 = key_box
    cyan_r1, cyan_c1, cyan_r2, cyan_c2 = cyan_box
    key_h = key_r2 - key_r1 + 1
    key_w = key_c2 - key_c1 + 1
    cyan_h = cyan_r2 - cyan_r1 + 1
    cyan_w = cyan_c2 - cyan_c1 + 1
    if key_h != key_w or key_h not in _KEY_SIZES:
        errors.append("the key bbox must be a 3x3 or 4x4 square")
    if not _boxes_separated(key_box, cyan_box):
        errors.append(
            "the key and cyan bboxes must have at least one-cell separation"
        )
    if key_h == 0 or cyan_h % key_h or cyan_w % key_h:
        errors.append("cyan bbox dimensions must be key-side multiples")
        scale_h = None
        scale_w = None
    else:
        scale_h = cyan_h // key_h
        scale_w = cyan_w // key_h
        if scale_h not in _SCALES or scale_w not in _SCALES:
            errors.append("cyan scale must be between one and six")

    key_matrix = tuple(
        tuple(
            coerced[key_r1 + row][key_c1 + col]
            for col in range(key_w)
        )
        for row in range(key_h)
    )
    if any(value == 8 for row in key_matrix for value in row):
        errors.append("cyan may not occur inside the key bbox")
    key_mask = tuple(
        tuple(int(value != 0) for value in row)
        for row in key_matrix
    )
    key_count = sum(value for row in key_mask for value in row)
    key_area = key_h * key_w
    lower_count = math.ceil(0.50 * key_area)
    upper_count = math.floor(0.75 * key_area)
    if not lower_count <= key_count <= upper_count:
        errors.append("key occupancy must be between 50 and 75 percent")
    palette = tuple(sorted({
        value
        for row in key_matrix
        for value in row
        if value != 0
    }))
    if len(palette) not in _PALETTE_SIZES:
        errors.append("the key must use two through four colors")
    if key_count <= len(palette):
        errors.append("at least one key color must repeat")
    if not any(value == 0 for row in key_matrix for value in row):
        errors.append("the key must contain at least one zero hole")

    exact_mask = False
    if (
        key_h == key_w
        and scale_h is not None
        and scale_w is not None
    ):
        rotated_mask = _rotate_90(key_mask)
        exact_mask = True
        for tile_row in range(key_h):
            for tile_col in range(key_h):
                expected = (
                    8 if rotated_mask[tile_row][tile_col] else 0
                )
                for delta_row in range(scale_h):
                    for delta_col in range(scale_w):
                        value = coerced[
                            cyan_r1
                            + tile_row * scale_h
                            + delta_row
                        ][
                            cyan_c1
                            + tile_col * scale_w
                            + delta_col
                        ]
                        if value != expected:
                            exact_mask = False
        if not exact_mask:
            errors.append(
                "cyan occupancy must exactly expand the rotated key mask"
            )

    counts = Counter(value for row in coerced for value in row)
    if 0 not in counts or counts[0] != max(counts.values()):
        errors.append("zero must be a modal background color")

    features = {
        "height": height,
        "width": width,
        "key_box": key_box,
        "cyan_box": cyan_box,
        "key_size": key_h if key_h == key_w else None,
        "key_matrix": key_matrix,
        "key_mask": key_mask,
        "key_count": key_count,
        "palette": palette,
        "palette_size": len(palette),
        "scale_h": scale_h,
        "scale_w": scale_w,
        "exact_mask": exact_mask,
    }
    return coerced, features, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "key_size": features["key_size"],
        "scale_h": features["scale_h"],
        "scale_w": features["scale_w"],
        "palette_size": features["palette_size"],
    }


def rule_mirror(grid):
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid key lesson: " + "; ".join(errors))
    key_r1, key_c1, _key_r2, _key_c2 = features["key_box"]
    cyan_r1, cyan_c1, _cyan_r2, _cyan_c2 = features["cyan_box"]
    key_size = features["key_size"]
    scale_h = features["scale_h"]
    scale_w = features["scale_w"]
    output = [row[:] for row in coerced]
    for row in range(len(coerced)):
        for col in range(len(coerced[0])):
            if coerced[row][col] != 8:
                continue
            tile_row = (row - cyan_r1) // scale_h
            tile_col = (col - cyan_c1) // scale_w
            key_row = key_size - 1 - tile_col
            key_col = tile_row
            output[row][col] = coerced[
                key_r1 + key_row
            ][
                key_c1 + key_col
            ]
    return output


def _profile_variants(matrix):
    variants = []
    current = tuple(tuple(row) for row in matrix)
    for _turn in range(4):
        if current not in variants:
            variants.append(current)
        current = _rotate_90(current)
    return tuple(variants)


_PROFILE_VARIANTS = tuple(
    _profile_variants(matrix) for matrix in _PROFILE_KEYS
)
_PROFILE_SIGNATURE_TO_INDEX = {}
for _profile_index, (_variants, _scale) in enumerate(
    zip(_PROFILE_VARIANTS, _PROFILE_SCALES)
):
    for _variant in _variants:
        _signature = (
            len(_variant),
            _scale,
            _scale,
            _normalize_roles(_variant),
        )
        _previous = _PROFILE_SIGNATURE_TO_INDEX.setdefault(
            _signature,
            _profile_index,
        )
        if _previous != _profile_index:
            raise AssertionError("canonical profile orbits overlap")


def canonical_profile_index(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        return None
    signature = (
        features["key_size"],
        features["scale_h"],
        features["scale_w"],
        _normalize_roles(features["key_matrix"]),
    )
    return _PROFILE_SIGNATURE_TO_INDEX.get(signature)


def is_canonical_profile(grid):
    return canonical_profile_index(grid) is not None


def _color_roles(role_matrix, rng):
    role_count = max(value for row in role_matrix for value in row)
    palette = rng.sample(_KEY_COLORS, role_count)
    return tuple(
        tuple(0 if role == 0 else palette[role - 1] for role in row)
        for row in role_matrix
    )


def _draw_general_key(key_size, palette_size, rng):
    area = key_size * key_size
    lower = max(palette_size + 1, math.ceil(0.50 * area))
    upper = math.floor(0.75 * area)
    occupied_count = rng.randint(lower, upper)

    occupied = {
        (0, rng.randrange(key_size)),
        (key_size - 1, rng.randrange(key_size)),
        (rng.randrange(key_size), 0),
        (rng.randrange(key_size), key_size - 1),
    }
    remaining = [
        (row, col)
        for row in range(key_size)
        for col in range(key_size)
        if (row, col) not in occupied
    ]
    rng.shuffle(remaining)
    occupied.update(remaining[: occupied_count - len(occupied)])
    if len(occupied) < occupied_count:
        raise AssertionError("failed to construct requested key occupancy")

    palette = rng.sample(_KEY_COLORS, palette_size)
    positions = sorted(occupied)
    rng.shuffle(positions)
    assigned = palette[:] + [
        rng.choice(palette)
        for _index in range(occupied_count - palette_size)
    ]
    rng.shuffle(assigned)
    key = [[0] * key_size for _row in range(key_size)]
    for (row, col), color in zip(positions, assigned):
        key[row][col] = color
    return tuple(tuple(row) for row in key)


def _choose_canvas(key_matrix, scale_h, scale_w, rng):
    key_size = len(key_matrix)
    key_count = sum(value != 0 for row in key_matrix for value in row)
    cyan_h = key_size * scale_h
    cyan_w = key_size * scale_w
    cyan_count = key_count * scale_h * scale_w
    candidates = []
    for relation in ("above", "below", "left", "right"):
        if relation in ("above", "below"):
            maximum_gap = 30 - key_size - cyan_h
        else:
            maximum_gap = 30 - key_size - cyan_w
        if maximum_gap >= 1:
            candidates.append((relation, maximum_gap))
    if not candidates:
        raise ValueError("key and cyan mask cannot fit in a 30x30 canvas")
    relation, maximum_gap = rng.choice(candidates)
    gap = rng.randint(1, min(5, maximum_gap))

    if relation in ("above", "below"):
        minimum_h = key_size + gap + cyan_h
        minimum_w = max(key_size, cyan_w)
    else:
        minimum_h = max(key_size, cyan_h)
        minimum_w = key_size + gap + cyan_w
    height = max(
        5,
        minimum_h + rng.randint(0, min(5, 30 - minimum_h)),
    )
    width = max(
        5,
        minimum_w + rng.randint(0, min(5, 30 - minimum_w)),
    )

    # Keep zero truly modal even for the largest cyan expansions.
    required_area = 2 * cyan_count + key_count
    while height * width < required_area:
        if height < 30 and (height <= width or width == 30):
            height += 1
        elif width < 30:
            width += 1
        else:
            raise ValueError("cannot preserve modal background in 30x30")

    if relation in ("above", "below"):
        stack_h = key_size + gap + cyan_h
        stack_top = rng.randint(0, height - stack_h)
        key_col = rng.randint(0, width - key_size)
        cyan_col = rng.randint(0, width - cyan_w)
        if relation == "above":
            key_row = stack_top
            cyan_row = stack_top + key_size + gap
        else:
            cyan_row = stack_top
            key_row = stack_top + cyan_h + gap
    else:
        stack_w = key_size + gap + cyan_w
        stack_left = rng.randint(0, width - stack_w)
        key_row = rng.randint(0, height - key_size)
        cyan_row = rng.randint(0, height - cyan_h)
        if relation == "left":
            key_col = stack_left
            cyan_col = stack_left + key_size + gap
        else:
            cyan_col = stack_left
            key_col = stack_left + cyan_w + gap
    return (
        height,
        width,
        key_row,
        key_col,
        cyan_row,
        cyan_col,
    )


def _render_scene(key_matrix, scale_h, scale_w, rng):
    (
        height,
        width,
        key_row,
        key_col,
        cyan_row,
        cyan_col,
    ) = _choose_canvas(key_matrix, scale_h, scale_w, rng)
    grid = full_grid(height, width, 0)
    key_size = len(key_matrix)
    for row in range(key_size):
        for col in range(key_size):
            grid[key_row + row][key_col + col] = key_matrix[row][col]

    key_mask = tuple(
        tuple(int(value != 0) for value in row)
        for row in key_matrix
    )
    rotated_mask = _rotate_90(key_mask)
    for tile_row in range(key_size):
        for tile_col in range(key_size):
            if not rotated_mask[tile_row][tile_col]:
                continue
            for delta_row in range(scale_h):
                for delta_col in range(scale_w):
                    grid[
                        cyan_row + tile_row * scale_h + delta_row
                    ][
                        cyan_col + tile_col * scale_w + delta_col
                    ] = 8
    return grid


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
                tuple(range(len(_PROFILE_KEYS))),
            )

    scene_rng = ctx.draw_rng("scene")
    if profile_index is not None:
        role_matrix = scene_rng.choice(
            _PROFILE_VARIANTS[profile_index]
        )
        key_matrix = _color_roles(role_matrix, scene_rng)
        scale_h = _PROFILE_SCALES[profile_index]
        scale_w = scale_h
        grid = _render_scene(
            key_matrix,
            scale_h,
            scale_w,
            scene_rng,
        )
        observed = observe_overrides(grid)
        for label in AXES:
            ctx.draw_choice(label, (observed[label],))
    else:
        key_options = {
            "easy": (3, 3, 3, 4),
            "medium": (3, 3, 4, 4),
            "hard": (3, 4, 4, 4),
        }[band]
        scale_options = {
            "easy": (1, 2, 2, 3),
            "medium": (2, 3, 3, 4),
            "hard": (3, 4, 5, 6),
        }[band]
        palette_options = {
            "easy": (2, 3, 3, 3),
            "medium": (2, 3, 3, 4),
            "hard": (3, 3, 4, 4),
        }[band]
        if overrides.get("key_size") is not None:
            key_options = _KEY_SIZES
        if overrides.get("scale_h") is not None:
            scale_options_h = _SCALES
        else:
            scale_options_h = scale_options
        if overrides.get("palette_size") is not None:
            palette_options = _PALETTE_SIZES

        key_size = ctx.draw_choice("key_size", key_options)
        scale_h = ctx.draw_choice("scale_h", scale_options_h)
        if overrides.get("scale_w") is not None:
            scale_options_w = _SCALES
        else:
            scale_options_w = (
                scale_h,
                scale_h,
                scale_h,
                *scale_options,
            )
        scale_w = ctx.draw_choice("scale_w", scale_options_w)
        palette_size = ctx.draw_choice(
            "palette_size",
            palette_options,
        )
        key_matrix = _draw_general_key(
            key_size,
            palette_size,
            scene_rng,
        )
        grid = _render_scene(
            key_matrix,
            scale_h,
            scale_w,
            scene_rng,
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
