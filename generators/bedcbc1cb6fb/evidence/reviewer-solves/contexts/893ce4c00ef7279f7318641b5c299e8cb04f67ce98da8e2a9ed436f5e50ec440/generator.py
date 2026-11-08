"""Generator for ARC rule family bedcbc1cb6fb (source task 99306f82).

Distinct marker colors occupy the first cells of the main diagonal.  A blue
rectangular frame begins just after those markers.  The rule keeps the input
and fills the frame interior with the marker colors as concentric rectangles,
in outside-to-inside marker order.

The calibrated grammar preserves every linked public canvas/marker/frame
profile.  Small one-cell frame translations provide observable layout
variation without changing the answer-bearing rule.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "bedcbc1cb6fb"
TASK_ID = "bedcbc1cb6fb"
VERSION = "3.0.0"
RULE_HASH = "7e5bd081e0cd"

SUMMARY = (
    "Read every nonzero, non-blue color on the main diagonal in top-to-bottom "
    "order. Keep the blue rectangular frame, then fill its interior with "
    "those marker colors as nested rectangles from outside to inside."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "zero is the background and color 1 forms exactly one rectangular frame",
    "two through five distinct non-{0,1} markers occupy the first diagonal cells",
    "marker order along the main diagonal defines outside-to-inside ring order",
    "the linked canvas, marker count, and frame size match a complete public profile",
    "the frame starts zero or one row and column after its canonical origin",
    "the frame interior is large enough to expose every requested marker ring",
]

SCENE_PROFILES = (
    "three_markers_15x15",
    "two_markers_10x10",
    "four_markers_15x15",
    "five_markers_20x20",
)

LAYOUT_VARIANTS = (
    "canonical",
    "down_one",
    "right_one",
    "down_right",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted complete public family",
        "valid": (
            "two_markers_10x10|three_markers_15x15|"
            "four_markers_15x15|five_markers_20x20"
        ),
    },
    "layout_variant": {
        "type": "str",
        "default": "40% canonical; 20% each one-cell frame translation",
        "valid": "canonical|down_one|right_one|down_right",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_PROFILE_DATA = {
    "two_markers_10x10": {
        "canvas": (10, 10),
        "marker_count": 2,
        "frame_size": (6, 6),
    },
    "three_markers_15x15": {
        "canvas": (15, 15),
        "marker_count": 3,
        "frame_size": (9, 9),
    },
    "four_markers_15x15": {
        "canvas": (15, 15),
        "marker_count": 4,
        "frame_size": (10, 10),
    },
    "five_markers_20x20": {
        "canvas": (20, 20),
        "marker_count": 5,
        "frame_size": (13, 14),
    },
}

_PROFILE_INDEX = {
    profile: index
    for index, profile in enumerate(SCENE_PROFILES)
}

_VARIANT_OFFSETS = {
    "canonical": (0, 0),
    "down_one": (1, 0),
    "right_one": (0, 1),
    "down_right": (1, 1),
}


def _coerce_arc_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]
    converted = []
    errors = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted_row = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted_row.append(0)
            else:
                converted_row.append(value)
        converted.append(converted_row)
    if errors:
        return None, errors
    return converted, []


def _frame_facts(grid):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    if not cells:
        return None
    row1 = min(row for row, _col in cells)
    row2 = max(row for row, _col in cells)
    col1 = min(col for _row, col in cells)
    col2 = max(col for _row, col in cells)
    expected = {
        (row, col)
        for row in range(row1, row2 + 1)
        for col in range(col1, col2 + 1)
        if row in (row1, row2) or col in (col1, col2)
    }
    if set(cells) != expected:
        return None
    return {
        "bbox": (row1, col1, row2, col2),
        "size": (row2 - row1 + 1, col2 - col1 + 1),
    }


def _analyze_scene(grid):
    """Recover the complete linked profile and every exact layout axis."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    height = len(coerced)
    width = len(coerced[0])
    marker_cells = [
        (row, col, value)
        for row, values in enumerate(coerced)
        for col, value in enumerate(values)
        if value not in (0, 1)
    ]
    marker_count = len(marker_cells)
    if not 2 <= marker_count <= 5:
        return None
    expected_positions = [
        (index, index)
        for index in range(marker_count)
    ]
    if [
        (row, col)
        for row, col, _value in marker_cells
    ] != expected_positions:
        return None
    marker_colors = tuple(
        value
        for _row, _col, value in marker_cells
    )
    if len(set(marker_colors)) != marker_count:
        return None

    frame = _frame_facts(coerced)
    if frame is None:
        return None
    profile = None
    for candidate in SCENE_PROFILES:
        data = _PROFILE_DATA[candidate]
        if (
            data["canvas"] == (height, width)
            and data["marker_count"] == marker_count
            and data["frame_size"] == frame["size"]
        ):
            profile = candidate
            break
    if profile is None:
        return None

    row1, col1, row2, col2 = frame["bbox"]
    offset = (row1 - marker_count, col1 - marker_count)
    variant = next(
        (
            name
            for name, candidate_offset in _VARIANT_OFFSETS.items()
            if candidate_offset == offset
        ),
        None,
    )
    if variant is None:
        return None
    if row2 >= height or col2 >= width:
        return None
    interior_height = row2 - row1 - 1
    interior_width = col2 - col1 - 1
    if (
        interior_height < 2 * marker_count - 1
        or interior_width < 2 * marker_count - 1
    ):
        return None
    zero_count = sum(
        value == 0
        for row in coerced
        for value in row
    )
    if zero_count <= len(marker_cells) or zero_count <= 2 * (
        frame["size"][0] + frame["size"][1]
    ) - 4:
        return None
    return {
        "scene_profile": profile,
        "layout_variant": variant,
        "marker_colors": marker_colors,
        "marker_count": marker_count,
        "frame_bbox": frame["bbox"],
        "frame_size": frame["size"],
    }


def observe_overrides(grid):
    """Recover every declared exact semantic axis from the returned grid."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return {}
    return {
        "scene_profile": analysis["scene_profile"],
        "layout_variant": analysis["layout_variant"],
    }


def canonical_profile_index(grid):
    """Return the linked public-profile index for any calibrated layout."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return None
    return _PROFILE_INDEX[analysis["scene_profile"]]


def exact_public_profile_index(grid):
    """Return the profile index only at the exact published frame origin."""
    analysis = _analyze_scene(grid)
    if analysis is None or analysis["layout_variant"] != "canonical":
        return None
    return _PROFILE_INDEX[analysis["scene_profile"]]


def self_check(grid, *, difficulty=None, meta=None):
    """Strictly recognize the calibrated public-profile/layout grammar."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    analysis = _analyze_scene(coerced)
    if analysis is None:
        return [
            "grid must match one complete public canvas/marker/frame profile "
            "and one supported frame offset"
        ]
    if difficulty not in (None, "easy", "medium", "hard"):
        return ["difficulty must be easy, medium, hard, or None"]
    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = meta
        for axis in AXES:
            if (
                axis in requested
                and requested[axis] is not None
                and analysis[axis] != requested[axis]
            ):
                errors.append(
                    f"{axis} requested {requested[axis]!r}, "
                    f"observed {analysis[axis]!r}"
                )
    return errors


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
    if (
        "layout_variant" in overrides
        and overrides["layout_variant"] not in LAYOUT_VARIANTS
    ):
        raise ValueError("unknown layout_variant")


def _profile_options(difficulty):
    if difficulty == "easy":
        return (
            "two_markers_10x10",
            "two_markers_10x10",
            "two_markers_10x10",
            "two_markers_10x10",
            "three_markers_15x15",
            "three_markers_15x15",
            "three_markers_15x15",
            "four_markers_15x15",
            "four_markers_15x15",
            "five_markers_20x20",
        )
    if difficulty == "hard":
        return (
            "two_markers_10x10",
            "three_markers_15x15",
            "three_markers_15x15",
            "four_markers_15x15",
            "four_markers_15x15",
            "four_markers_15x15",
            "five_markers_20x20",
            "five_markers_20x20",
            "five_markers_20x20",
            "five_markers_20x20",
        )
    return SCENE_PROFILES


def _render_profile(profile, variant, marker_colors):
    data = _PROFILE_DATA[profile]
    height, width = data["canvas"]
    frame_height, frame_width = data["frame_size"]
    marker_count = data["marker_count"]
    delta_row, delta_col = _VARIANT_OFFSETS[variant]
    row1 = marker_count + delta_row
    col1 = marker_count + delta_col
    row2 = row1 + frame_height - 1
    col2 = col1 + frame_width - 1
    grid = [
        [0 for _col in range(width)]
        for _row in range(height)
    ]
    for index, color in enumerate(marker_colors):
        grid[index][index] = color
    for col in range(col1, col2 + 1):
        grid[row1][col] = 1
        grid[row2][col] = 1
    for row in range(row1, row2 + 1):
        grid[row][col1] = 1
        grid[row][col2] = 1
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
    profile = ctx.draw_choice(
        "scene_profile",
        _profile_options(difficulty),
    )
    variant = ctx.draw_choice(
        "layout_variant",
        (
            "canonical",
            "canonical",
            "down_one",
            "right_one",
            "down_right",
        ),
    )
    marker_colors = ctx.draw_distinct_colors(
        "marker_palette",
        n=_PROFILE_DATA[profile]["marker_count"],
        exclude={0, 1},
    )
    grid = _render_profile(profile, variant, marker_colors)
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise RuntimeError(
            "constructed an invalid calibrated scene: "
            + "; ".join(errors)
        )
    return grid


def rule_mirror(grid):
    """Broad Python mirror of the canonical Racket frame-filling rule."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height = len(original)
    width = len(original[0])
    markers = [
        original[index][index]
        for index in range(min(height, width))
        if original[index][index] not in (0, 1)
    ]
    blue_cells = [
        (row, col)
        for row, values in enumerate(original)
        for col, value in enumerate(values)
        if value == 1
    ]
    if not blue_cells:
        raise ValueError("the rule requires at least one blue frame cell")
    inner_row1 = min(row for row, _col in blue_cells) + 1
    inner_col1 = min(col for _row, col in blue_cells) + 1
    inner_row2 = max(row for row, _col in blue_cells) - 1
    inner_col2 = max(col for _row, col in blue_cells) - 1
    output = [row[:] for row in original]
    for color in markers:
        if inner_row1 > inner_row2 or inner_col1 > inner_col2:
            break
        for row in range(inner_row1, inner_row2 + 1):
            for col in range(inner_col1, inner_col2 + 1):
                output[row][col] = color
        inner_row1 += 1
        inner_col1 += 1
        inner_row2 -= 1
        inner_col2 -= 1
    return output
