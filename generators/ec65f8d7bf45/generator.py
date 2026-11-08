"""Generator for bank task E132 / ec65f8d7bf45.

A singleton corner cell supplies the paint color.  The other nonzero color
forms one strictly interior rectangular frame.  The rule preserves both and
fills the frame interior with a paint-colored checkerboard whose top-left
interior cell is painted.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid


GENERATOR_ID = "ec65f8d7bf45"
VERSION = "3.0.0"
TASK_ID = "ec65f8d7bf45"
RULE_HASH = "7cc365f60685"

SUMMARY = (
    "Place one singleton paint-color key at a canvas corner and one closed "
    "rectangular frame of the more frequent nonzero color, with at least one "
    "blank cell between the frame and every canvas edge. The output preserves "
    "the scene and fills the frame interior with a paint-color checkerboard "
    "starting at the interior top-left cell."
)

INVARIANTS = [
    "the input is a 7..18 by 7..18 rectangular ARC grid",
    "zero is the background and exactly two nonzero colors are present",
    "the paint color occurs once at one of the four canvas corners",
    "the frame color occurs only on one closed rectangle outline",
    "the frame is at least 4x4 and has a blank margin on all four sides",
    "the frame interior is empty before the checkerboard is painted",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

MARKER_CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 7..18",
        "valid": "7..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 7..18",
        "valid": "7..18",
    },
    "frame_h": {
        "type": "int",
        "default": "rng 4..h-2",
        "valid": "4..h-2",
    },
    "frame_w": {
        "type": "int",
        "default": "rng 4..w-2",
        "valid": "4..w-2",
    },
    "marker_corner": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(MARKER_CORNERS),
    },
}

_GRID_BOUNDS = (7, 18)
_PROFILE_PRIOR = 0.28
_BAND_BOUNDS = {
    "easy": ((7, 10), (7, 11)),
    "medium": ((9, 14), (9, 14)),
    "hard": ((13, 18), (13, 18)),
}
_CORNER_COORDS = {
    "top_left": lambda h, w: (0, 0),
    "top_right": lambda h, w: (0, w - 1),
    "bottom_left": lambda h, w: (h - 1, 0),
    "bottom_right": lambda h, w: (h - 1, w - 1),
}

# The five published input profiles.  Compact rows keep the calibrated prior
# inspectable without loading the canonical dataset at generation time.
_PROFILE_ROWS = (
    (
        "300000000",
        "000000000",
        "005555550",
        "005000050",
        "005000050",
        "005000050",
        "005555550",
        "000000000",
    ),
    (
        "0000000000",
        "0000777770",
        "0000700070",
        "0000700070",
        "0000700070",
        "0000777770",
        "2000000000",
    ),
    (
        "000000008",
        "000000000",
        "000000000",
        "044444000",
        "040004000",
        "040004000",
        "040004000",
        "044444000",
        "000000000",
    ),
    (
        "00000000000",
        "00000000000",
        "00066666660",
        "00060000060",
        "00060000060",
        "00060000060",
        "00066666660",
        "20000000000",
    ),
    (
        "000000004",
        "088888800",
        "080000800",
        "080000800",
        "080000800",
        "088888800",
        "000000000",
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for label, bounds in (
        ("grid_h", _GRID_BOUNDS),
        ("grid_w", _GRID_BOUNDS),
        ("frame_h", (4, _GRID_BOUNDS[1] - 2)),
        ("frame_w", (4, _GRID_BOUNDS[1] - 2)),
    ):
        value = overrides.get(label)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{label} must be an integer")
        if not bounds[0] <= value <= bounds[1]:
            raise ValueError(
                f"{label} must be in {bounds[0]}..{bounds[1]}"
            )

    marker_corner = overrides.get("marker_corner")
    if marker_corner is not None and marker_corner not in MARKER_CORNERS:
        raise ValueError(
            "marker_corner must be one of " + ", ".join(MARKER_CORNERS)
        )
    if (
        overrides.get("grid_h") is not None
        and overrides.get("frame_h") is not None
        and overrides["frame_h"] > overrides["grid_h"] - 2
    ):
        raise ValueError("frame_h requires grid_h >= frame_h + 2")
    if (
        overrides.get("grid_w") is not None
        and overrides.get("frame_w") is not None
        and overrides["frame_w"] > overrides["grid_w"] - 2
    ):
        raise ValueError("frame_w requires grid_w >= frame_w + 2")


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


def _marker_corner(row, col, height, width):
    for name, coordinate in _CORNER_COORDS.items():
        if (row, col) == coordinate(height, width):
            return name
    return None


def _scene_analysis(grid):
    if not isinstance(grid, list) or not grid:
        return None, None, ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return None, None, [
            "grid rows must be non-empty lists or digit strings"
        ]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return coerced, None, ["grid must be rectangular"]

    height = len(coerced)
    errors = []
    if not _GRID_BOUNDS[0] <= height <= _GRID_BOUNDS[1]:
        errors.append("grid height must be in 7..18")
    if not _GRID_BOUNDS[0] <= width <= _GRID_BOUNDS[1]:
        errors.append("grid width must be in 7..18")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return coerced, None, errors

    counts = Counter(
        value for row in coerced for value in row if value != 0
    )
    if len(counts) != 2:
        errors.append("exactly two nonzero colors are required")
        return coerced, None, errors
    singleton_colors = [color for color, count in counts.items() if count == 1]
    if len(singleton_colors) != 1:
        errors.append("exactly one nonzero color must be a singleton")
        return coerced, None, errors
    paint_color = singleton_colors[0]
    frame_color = next(color for color in counts if color != paint_color)

    marker = next(
        (row, col)
        for row, values in enumerate(coerced)
        for col, value in enumerate(values)
        if value == paint_color
    )
    corner = _marker_corner(*marker, height, width)
    if corner is None:
        errors.append("the paint marker must occupy a canvas corner")

    frame_cells = {
        (row, col)
        for row, values in enumerate(coerced)
        for col, value in enumerate(values)
        if value == frame_color
    }
    top = min(row for row, _col in frame_cells)
    bottom = max(row for row, _col in frame_cells)
    left = min(col for _row, col in frame_cells)
    right = max(col for _row, col in frame_cells)
    frame_h = bottom - top + 1
    frame_w = right - left + 1
    if frame_h < 4 or frame_w < 4:
        errors.append("the frame must be at least 4x4")
    if top < 1 or left < 1 or bottom > height - 2 or right > width - 2:
        errors.append("the frame must have a blank margin on every side")

    outline = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }
    if frame_cells != outline:
        errors.append("frame-color cells must form exactly one closed outline")
    if any(
        coerced[row][col] != 0
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
    ):
        errors.append("the frame interior must be empty")
    if errors:
        return coerced, None, errors

    return coerced, {
        "grid_h": height,
        "grid_w": width,
        "frame_h": frame_h,
        "frame_w": frame_w,
        "marker_corner": corner,
        "frame_color": frame_color,
        "paint_color": paint_color,
        "bbox": (top, left, bottom, right),
    }, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "grid_h": features["grid_h"],
        "grid_w": features["grid_w"],
        "frame_h": features["frame_h"],
        "frame_w": features["frame_w"],
        "marker_corner": features["marker_corner"],
    }


def rule_mirror(grid):
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    output = [row[:] for row in coerced]
    top, left, bottom, right = features["bbox"]
    for row in range(top + 1, bottom):
        for col in range(left + 1, right):
            output[row][col] = (
                features["paint_color"]
                if (row - top - 1 + col - left - 1) % 2 == 0
                else 0
            )
    return output


def _rotate(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _transform_grid(grid, transform):
    result = [row[:] for row in grid]
    if transform >= 4:
        result = [row[::-1] for row in result]
    for _ in range(transform % 4):
        result = _rotate(result)
    return result


def _profile_feature(grid):
    variants = []
    for transform in range(8):
        candidate = _transform_grid(grid, transform)
        _coerced, features, errors = _scene_analysis(candidate)
        if errors:
            return None
        top, left, bottom, right = features["bbox"]
        marker = _CORNER_COORDS[features["marker_corner"]](
            features["grid_h"], features["grid_w"]
        )
        variants.append(
            (
                features["grid_h"],
                features["grid_w"],
                (top, left, bottom, right),
                marker,
            )
        )
    return min(variants)


def _decode_rows(rows):
    return [[int(value) for value in row] for row in rows]


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    _profile_feature(_decode_rows(rows)) for rows in _PROFILE_ROWS
)


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    signature = _profile_feature(_coerce_grid(grid))
    return (
        signature
        if signature in _CANONICAL_PROFILE_SIGNATURES
        else None
    )


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) is not None


def _draw_profile(rows, transform, frame_color, paint_color):
    grid = _decode_rows(rows)
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise AssertionError("invalid embedded profile: " + "; ".join(errors))
    mapping = {
        features["frame_color"]: frame_color,
        features["paint_color"]: paint_color,
    }
    recolored = [
        [mapping.get(value, value) for value in row]
        for row in grid
    ]
    result = _transform_grid(recolored, transform)
    if canonical_profile_signature(result) is None:
        raise AssertionError("constructed public profile drifted")
    return result


def _draw_dimension(ctx, label, band_bounds, required_min, explicit):
    if explicit is not None:
        return ctx.draw_int(label, *_GRID_BOUNDS)
    low = max(band_bounds[0], required_min)
    high = band_bounds[1] if low <= band_bounds[1] else _GRID_BOUNDS[1]
    return ctx.draw_int(label, low, high)


def _draw_general(ctx, band, overrides):
    height_bounds, width_bounds = _BAND_BOUNDS[band]
    requested_frame_h = overrides.get("frame_h")
    requested_frame_w = overrides.get("frame_w")
    height = _draw_dimension(
        ctx,
        "grid_h",
        height_bounds,
        (requested_frame_h + 2) if requested_frame_h is not None else 7,
        overrides.get("grid_h"),
    )
    width = _draw_dimension(
        ctx,
        "grid_w",
        width_bounds,
        (requested_frame_w + 2) if requested_frame_w is not None else 7,
        overrides.get("grid_w"),
    )
    frame_h = ctx.draw_int("frame_h", 4, height - 2)
    frame_w = ctx.draw_int("frame_w", 4, width - 2)
    corner = ctx.draw_choice("marker_corner", MARKER_CORNERS)

    rng = ctx.draw_rng("layout")
    frame_color, paint_color = rng.sample(list(range(1, 10)), 2)
    top = rng.randint(1, height - frame_h - 1)
    left = rng.randint(1, width - frame_w - 1)
    grid = full_grid(height, width, 0)
    draw_rect_outline(
        grid, top, left, frame_h, frame_w, frame_color
    )
    marker_row, marker_col = _CORNER_COORDS[corner](height, width)
    grid[marker_row][marker_col] = paint_color
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
                tuple(range(len(_PROFILE_ROWS))),
            )

    if profile_index is not None:
        profile_rng = ctx.draw_rng("profile_layout")
        transform = profile_rng.randrange(8)
        frame_color, paint_color = profile_rng.sample(
            list(range(1, 10)), 2
        )
        grid = _draw_profile(
            _PROFILE_ROWS[profile_index],
            transform,
            frame_color,
            paint_color,
        )
        _coerced, features, errors = _scene_analysis(grid)
        if errors:
            raise AssertionError(
                "generated invalid profile: " + "; ".join(errors)
            )
        ctx.draw_int("grid_h", features["grid_h"], features["grid_h"])
        ctx.draw_int("grid_w", features["grid_w"], features["grid_w"])
        ctx.draw_int("frame_h", features["frame_h"], features["frame_h"])
        ctx.draw_int("frame_w", features["frame_w"], features["frame_w"])
        ctx.draw_choice(
            "marker_corner", (features["marker_corner"],)
        )
    else:
        grid = _draw_general(ctx, band, overrides)

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
