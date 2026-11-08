"""Generator for ARC rule family 4e9dfb260106 (source task M111).

A connected red marker encodes a cell count.  Exactly three separated blue
objects have distinct sizes, and the uniquely size-matching blue object is
returned as a binary crop.  Four profiles preserve every demonstrated small
scene; five larger profiles extend the same count-selection law with diverse
connected shapes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "4e9dfb260106"
TASK_ID = "4e9dfb260106"
VERSION = "3.0.0"
RULE_HASH = "98ab4126a48a"

SUMMARY = (
    "Count the connected red marker cells. Select the unique blue component "
    "with that many cells and output its binary mask cropped to its bounding "
    "box."
)

INVARIANTS = [
    "exactly three separated blue components have distinct sizes",
    "one connected red marker has the size of exactly one blue component",
    "one isolated border cell uses a non-role color from 3 through 9",
    "the selected component is returned as a color-1 bbox crop",
    "small profiles preserve the demonstrated L, square, zigzag, and marker shapes",
]

SCENE_PROFILES = (
    "canonical_l3",
    "canonical_square4",
    "canonical_l5",
    "canonical_zigzag4",
    "extended_10",
    "extended_11",
    "extended_12",
    "extended_13",
    "extended_14",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": (
            "20% demonstrated profiles and 80% larger count-matching profiles"
        ),
        "valid": (
            "canonical_l3|canonical_square4|canonical_l5|"
            "canonical_zigzag4|extended_10|extended_11|extended_12|"
            "extended_13|extended_14"
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

_L3 = ((0, 0), (1, 0), (1, 1))
_SQUARE4 = ((0, 0), (0, 1), (1, 0), (1, 1))
_ZIGZAG4 = ((0, 0), (0, 1), (1, 1), (1, 2))
_L5 = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2))
_LINE3 = ((0, 0), (0, 1), (0, 2))
_LINE4 = ((0, 0), (0, 1), (0, 2), (0, 3))
_P5 = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1))


def _coerce_arc_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]
    errors = []
    coerced = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted.append(0)
            else:
                converted.append(value)
        coerced.append(converted)
    if errors:
        return None, errors
    return coerced, []


def _normalize(cells):
    top = min(row for row, _col in cells)
    left = min(col for _row, col in cells)
    return tuple(sorted(
        (row - top, col - left) for row, col in cells
    ))


def _oriented_variants(cells):
    points = list(_normalize(cells))
    variants = set()
    for reflected in (False, True):
        transformed = [
            (row, -col if reflected else col)
            for row, col in points
        ]
        for _turn in range(4):
            variants.add(_normalize(transformed))
            transformed = [
                (col, -row) for row, col in transformed
            ]
    return tuple(sorted(variants))


def _shape_key(cells):
    return min(_oriented_variants(cells))


_L3_KEY = _shape_key(_L3)
_SQUARE4_KEY = _shape_key(_SQUARE4)
_ZIGZAG4_KEY = _shape_key(_ZIGZAG4)
_L5_KEY = _shape_key(_L5)
_LINE3_KEY = _shape_key(_LINE3)
_LINE4_KEY = _shape_key(_LINE4)
_P5_KEY = _shape_key(_P5)


def _bbox_size(cells):
    rows = [row for row, _col in cells]
    cols = [col for _row, col in cells]
    return max(rows) - min(rows) + 1, max(cols) - min(cols) + 1


def _components(grid, color):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            start = (start_row, start_col)
            if start in seen or grid[start_row][start_col] != color:
                continue
            stack = [start]
            seen.add(start)
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for delta_row, delta_col in _CARDINAL:
                    neighbor = (row + delta_row, col + delta_col)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(tuple(sorted(cells)))
    return tuple(result)


def _groups_have_margin(groups):
    for index, first in enumerate(groups):
        for second in groups[index + 1:]:
            if any(
                max(abs(row_a - row_b), abs(col_a - col_b)) <= 1
                for row_a, col_a in first
                for row_b, col_b in second
            ):
                return False
    return True


def _semantic_signature(grid):
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    height = len(coerced)
    width = len(coerced[0])
    extras = tuple(
        (row, col, value)
        for row, values in enumerate(coerced)
        for col, value in enumerate(values)
        if value not in (0, 1, 2)
    )
    if len(extras) != 1:
        return None
    extra_row, extra_col, extra_color = extras[0]
    if not (
        extra_row in (0, height - 1)
        or extra_col in (0, width - 1)
    ):
        return None
    values = {value for row in coerced for value in row}
    if values != {0, 1, 2, extra_color}:
        return None

    blue = _components(coerced, 1)
    red = _components(coerced, 2)
    if len(blue) != 3 or len(red) != 1:
        return None
    groups = blue + red + (((extra_row, extra_col),),)
    if not _groups_have_margin(groups):
        return None

    sizes = tuple(len(component) for component in blue)
    if len(set(sizes)) != 3:
        return None
    red_count = len(red[0])
    if sizes.count(red_count) != 1:
        return None
    by_size = {
        len(component): component for component in blue
    }

    profile = None
    if set(sizes) == {3, 4, 5}:
        if (
            _shape_key(by_size[3]) != _L3_KEY
            or _shape_key(by_size[5]) != _L5_KEY
        ):
            return None
        shape4 = _shape_key(by_size[4])
        marker_shape = _shape_key(red[0])
        if (
            red_count == 3
            and marker_shape == _LINE3_KEY
            and shape4 == _SQUARE4_KEY
        ):
            profile = "canonical_l3"
        elif (
            red_count == 4
            and marker_shape == _LINE4_KEY
            and shape4 == _SQUARE4_KEY
        ):
            profile = "canonical_square4"
        elif (
            red_count == 5
            and marker_shape == _P5_KEY
            and shape4 == _SQUARE4_KEY
        ):
            profile = "canonical_l5"
        elif (
            red_count == 4
            and marker_shape == _LINE4_KEY
            and shape4 == _ZIGZAG4_KEY
        ):
            profile = "canonical_zigzag4"
    else:
        candidate = f"extended_{red_count}"
        if (
            candidate in SCENE_PROFILES
            and set(sizes) == {
                red_count - 2,
                red_count,
                red_count + 1,
            }
            and all(
                min(_bbox_size(component)) >= 2
                for component in blue + red
            )
        ):
            profile = candidate
    if profile is None:
        return None
    return {"scene_profile": profile}


def canonical_profile_index(grid):
    """Return the linked scene-profile index for a calibrated input."""
    signature = _semantic_signature(grid)
    if signature is None:
        return None
    return SCENE_PROFILES.index(signature["scene_profile"])


def observe_overrides(grid):
    """Recover every declared exact axis from a valid returned grid."""
    signature = _semantic_signature(grid)
    return {} if signature is None else dict(signature)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if (
        "scene_profile" in overrides
        and overrides["scene_profile"] not in SCENE_PROFILES
    ):
        raise ValueError("unknown scene_profile")


def _profile_options():
    options = []
    for profile in SCENE_PROFILES[:4]:
        options.extend([profile] * 5)
    for profile in SCENE_PROFILES[4:]:
        options.extend([profile] * 16)
    return tuple(options)


def _canvas_ranges(profile, difficulty):
    band = difficulty or "medium"
    if profile.startswith("canonical_"):
        return {
            "easy": ((8, 11), (9, 13)),
            "medium": ((9, 13), (10, 15)),
            "hard": ((11, 16), (12, 18)),
        }[band]
    return {
        "easy": ((14, 16), (14, 17)),
        "medium": ((16, 19), (16, 20)),
        "hard": ((18, 22), (18, 23)),
    }[band]


def _random_polyomino(rng, size, *, max_dimension=6):
    for _attempt in range(256):
        cells = {(0, 0)}
        while len(cells) < size:
            frontier = sorted({
                (row + delta_row, col + delta_col)
                for row, col in cells
                for delta_row, delta_col in _CARDINAL
                if (row + delta_row, col + delta_col) not in cells
            })
            cells.add(rng.choice(frontier))
        normalized = _normalize(cells)
        box_height, box_width = _bbox_size(normalized)
        if (
            2 <= box_height <= max_dimension
            and 2 <= box_width <= max_dimension
        ):
            return normalized
    return _compact_polyomino(size)


def _compact_polyomino(size):
    width = 3 if size <= 9 else 4
    return tuple(
        (index // width, index % width)
        for index in range(size)
    )


def _oriented(cells, rng):
    return rng.choice(_oriented_variants(cells))


def _profile_shapes(profile, rng):
    if profile.startswith("canonical_"):
        shape4 = (
            _ZIGZAG4
            if profile == "canonical_zigzag4"
            else _SQUARE4
        )
        marker = {
            "canonical_l3": _LINE3,
            "canonical_square4": _LINE4,
            "canonical_l5": _P5,
            "canonical_zigzag4": _LINE4,
        }[profile]
        return [
            (1, _oriented(_L3, rng)),
            (1, _oriented(shape4, rng)),
            (1, _oriented(_L5, rng)),
            (2, _oriented(marker, rng)),
        ]

    red_count = int(profile.removeprefix("extended_"))
    sizes = (red_count - 2, red_count, red_count + 1)
    shapes = [
        (1, _oriented(_random_polyomino(rng, size), rng))
        for size in sizes
    ]
    marker = _oriented(
        _random_polyomino(rng, red_count),
        rng,
    )
    return shapes + [(2, marker)]


def _free(grid, top, left, cells):
    height = len(grid)
    width = len(grid[0])
    for delta_row, delta_col in cells:
        row = top + delta_row
        col = left + delta_col
        if not (0 <= row < height and 0 <= col < width):
            return False
        for neighbor_row in range(row - 1, row + 2):
            for neighbor_col in range(col - 1, col + 2):
                if (
                    0 <= neighbor_row < height
                    and 0 <= neighbor_col < width
                    and grid[neighbor_row][neighbor_col] != 0
                ):
                    return False
    return True


def _paint(grid, top, left, cells, color):
    for delta_row, delta_col in cells:
        grid[top + delta_row][left + delta_col] = color


def _border_positions(height, width):
    return tuple(dict.fromkeys(
        [(0, col) for col in range(width)]
        + [(height - 1, col) for col in range(width)]
        + [(row, 0) for row in range(height)]
        + [(row, width - 1) for row in range(height)]
    ))


def _try_random_scene(profile, height, width, shapes, decoy_color, rng):
    for _attempt in range(96):
        grid = [[0 for _col in range(width)] for _row in range(height)]
        decoy_row, decoy_col = rng.choice(
            _border_positions(height, width)
        )
        grid[decoy_row][decoy_col] = decoy_color
        ordered_shapes = list(shapes)
        rng.shuffle(ordered_shapes)
        for color, cells in ordered_shapes:
            box_height, box_width = _bbox_size(cells)
            candidates = [
                (top, left)
                for top in range(height - box_height + 1)
                for left in range(width - box_width + 1)
            ]
            rng.shuffle(candidates)
            placement = next(
                (
                    (top, left)
                    for top, left in candidates
                    if _free(grid, top, left, cells)
                ),
                None,
            )
            if placement is None:
                break
            _paint(grid, *placement, cells, color)
        else:
            if _semantic_signature(grid) == {
                "scene_profile": profile
            }:
                return grid
    return None


def _fallback_shapes(profile):
    if profile.startswith("canonical_"):
        shape4 = (
            _ZIGZAG4
            if profile == "canonical_zigzag4"
            else _SQUARE4
        )
        marker = {
            "canonical_l3": _LINE3,
            "canonical_square4": _LINE4,
            "canonical_l5": _P5,
            "canonical_zigzag4": _LINE4,
        }[profile]
        return [(1, _L3), (1, shape4), (1, _L5), (2, marker)]
    red_count = int(profile.removeprefix("extended_"))
    return [
        (1, _compact_polyomino(red_count - 2)),
        (1, _compact_polyomino(red_count)),
        (1, _compact_polyomino(red_count + 1)),
        (2, _compact_polyomino(red_count)),
    ]


def _fallback_scene(profile, height, width, decoy_color):
    shapes = _fallback_shapes(profile)
    dimensions = [_bbox_size(cells) for _color, cells in shapes]
    anchors = (
        (0, 0),
        (0, width - dimensions[1][1]),
        (height - dimensions[2][0], 0),
        (
            height - dimensions[3][0],
            width - dimensions[3][1],
        ),
    )
    grid = [[0 for _col in range(width)] for _row in range(height)]
    for (color, cells), (top, left) in zip(shapes, anchors):
        if not _free(grid, top, left, cells):
            raise AssertionError("fallback component layout does not fit")
        _paint(grid, top, left, cells, color)
    decoy = next(
        (
            position
            for position in _border_positions(height, width)
            if _free(grid, *position, ((0, 0),))
        ),
        None,
    )
    if decoy is None:
        raise AssertionError("fallback has no isolated border decoy")
    grid[decoy[0]][decoy[1]] = decoy_color
    if _semantic_signature(grid) != {"scene_profile": profile}:
        raise AssertionError("fallback lost the requested scene profile")
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
    profile = ctx.draw_choice("scene_profile", _profile_options())
    height_range, width_range = _canvas_ranges(profile, difficulty)
    height = ctx.draw_int("canvas_height", *height_range)
    width = ctx.draw_int("canvas_width", *width_range)
    rng = ctx.draw_rng("scene")
    decoy_color = rng.choice(tuple(range(3, 10)))
    shapes = _profile_shapes(profile, rng)
    grid = _try_random_scene(
        profile,
        height,
        width,
        shapes,
        decoy_color,
        rng,
    )
    if grid is None:
        grid = _fallback_scene(
            profile,
            height,
            width,
            decoy_color,
        )
    if observe_overrides(grid) != {"scene_profile": profile}:
        raise AssertionError("constructed scene lost an exact axis")
    return grid


def rule_mirror(grid):
    """Broad Python mirror of the canonical count-select-crop rule."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    red_count = sum(
        value == 2 for row in coerced for value in row
    )
    target = next(
        (
            component
            for component in _components(coerced, 1)
            if len(component) == red_count
        ),
        None,
    )
    if target is None:
        return [[0]]
    top = min(row for row, _col in target)
    bottom = max(row for row, _col in target)
    left = min(col for _row, col in target)
    right = max(col for _row, col in target)
    target_cells = set(target)
    return [
        [
            1 if (row, col) in target_cells else 0
            for col in range(left, right + 1)
        ]
        for row in range(top, bottom + 1)
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept only complete demonstrated or calibrated extended scenes."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if _semantic_signature(coerced) is None:
        return [
            "grid must contain one complete calibrated scene: three "
            "separated blue components, one connected count-matching red "
            "marker, and one isolated non-role border cell"
        ]
    if rule_mirror(coerced) == [[0]]:
        return ["red count must select one blue component"]
    return []
