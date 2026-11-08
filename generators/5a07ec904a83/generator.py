"""Generate uniform fields whose unique black marker expands into an X.

The calibrated prior retains each complete published centered-square profile.
Explicit extrapolation profiles move the marker or use an odd rectangle so a
learner cannot succeed by painting a fixed centered X.
"""

from __future__ import annotations

from itertools import product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "5a07ec904a83"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2d673baf6c22"

SUMMARY = (
    "Read the nonzero color at the top-left cell and the first black marker; "
    "return the same-size uniform field with both diagonals through that "
    "marker painted black."
)
INVARIANTS = [
    "the input is an odd 3..15 by 3..15 square or rectangle",
    "cell (0,0) is a nonzero background color",
    "exactly one cell is black and every other cell equals the background",
    "the complete dimension/marker relation is one declared scene profile",
    "the rule changes at least one non-marker cell",
]
EXPECTED_OUTPUT_CODOMAIN = 23_544

PUBLIC_PROFILES = (
    "center_5",
    "center_3",
    "center_7",
    "center_11",
)
EXTRAPOLATION_PROFILES = (
    "center_9",
    "offset_square",
    "edge_square",
    "rect_center",
    "rect_offset",
)
SCENE_PROFILES = PUBLIC_PROFILES + EXTRAPOLATION_PROFILES

ODD_SIDES = tuple(range(3, 16, 2))
_PUBLIC_SIDE_BY_PROFILE = {
    "center_5": 5,
    "center_3": 3,
    "center_7": 7,
    "center_11": 11,
}
_PUBLIC_BG_BY_PROFILE = {
    "center_5": 2,
    "center_3": 1,
    "center_7": 3,
    "center_11": 6,
}
_PUBLIC_PROFILE_INDEX = {
    profile: index for index, profile in enumerate(PUBLIC_PROFILES)
}

_PROFILE_OPTIONS = {
    "easy": (
        ("center_5",) * 3
        + ("center_3",) * 3
        + ("center_7",) * 2
        + ("center_11",) * 2
        + ("center_9",)
        + ("offset_square",) * 11
        + ("edge_square",) * 7
        + ("rect_center",) * 2
        + ("rect_offset",) * 9
    ),
    "medium": (
        ("center_5",) * 3
        + ("center_3",) * 2
        + ("center_7",) * 3
        + ("center_11",) * 2
        + ("center_9",)
        + ("offset_square",) * 10
        + ("edge_square",) * 7
        + ("rect_center",) * 2
        + ("rect_offset",) * 10
    ),
    "hard": (
        ("center_5",) * 2
        + ("center_3",)
        + ("center_7",) * 3
        + ("center_11",) * 4
        + ("center_9",)
        + ("offset_square",) * 10
        + ("edge_square",) * 7
        + ("rect_center",) * 2
        + ("rect_offset",) * 10
    ),
    "all": SCENE_PROFILES,
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted complete geometry profile",
        "valid": "|".join(SCENE_PROFILES),
    },
    "background_color": {
        "type": "color",
        "default": "rng nonzero; exact public literal color excluded by default",
        "valid": "1..9",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

Grid = list[list[int]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic member of the calibrated X-ray grammar."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty is not None else "all"
    profile = ctx.draw_choice(
        "scene_profile",
        _PROFILE_OPTIONS[band],
    )

    background_options = tuple(range(1, 10))
    if (
        "background_color" not in overrides
        and profile in PUBLIC_PROFILES
    ):
        published_color = _PUBLIC_BG_BY_PROFILE[profile]
        background_options = tuple(
            color
            for color in background_options
            if color != published_color
        )
    background = ctx.draw_choice(
        "background_color",
        background_options,
    )

    height, width, marker_row, marker_col = _profile_geometry(
        ctx,
        profile,
        difficulty,
    )
    grid = full_grid(height, width, background)
    grid[marker_row][marker_col] = 0
    analysis = _analyze(grid)
    if (
        analysis["scene_profile"] != profile
        or analysis["background_color"] != background
    ):
        raise AssertionError("constructed grid lost an exact axis")
    return grid


def solve_python(grid: Grid) -> Grid:
    """Independent Python mirror of the canonical first-zero X rule."""
    height, width = _validate_rectangular_grid(grid)
    marker = next(
        (
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == 0
        ),
        None,
    )
    if marker is None:
        raise ValueError("grid has no black marker")
    marker_row, marker_col = marker
    background = grid[0][0]
    return [
        [
            0
            if abs(row - marker_row) == abs(col - marker_col)
            else background
            for col in range(width)
        ]
        for row in range(height)
    ]


def self_check(grid, *, difficulty=None, meta=None):
    """Recognize the complete returned-grid training grammar."""
    try:
        analysis = _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    errors = []
    if analysis["scene_profile"] is None:
        errors.append(
            "dimension and marker position do not match a declared profile"
        )
    try:
        output = solve_python(grid)
    except (TypeError, ValueError) as exc:
        errors.append(str(exc))
    else:
        if output == grid:
            errors.append("the X rule leaves this grid unchanged")
    return errors


def observe_overrides(grid):
    """Recover both exact declared axes from the returned cells."""
    if self_check(grid):
        return {}
    analysis = _analyze(grid)
    return {
        "scene_profile": analysis["scene_profile"],
        "background_color": analysis["background_color"],
    }


def canonical_profile_index(grid):
    """Return the complete linked public geometry index, or ``None``."""
    if self_check(grid):
        return None
    profile = _analyze(grid)["scene_profile"]
    return _PUBLIC_PROFILE_INDEX.get(profile)


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
    if "background_color" in overrides:
        color = overrides["background_color"]
        if (
            not isinstance(color, int)
            or isinstance(color, bool)
            or not 1 <= color <= 9
        ):
            raise ValueError("background_color must be an integer 1..9")


def _size_options(difficulty):
    return {
        "easy": (3, 5, 7, 9, 11),
        "medium": (5, 7, 9, 11, 13),
        "hard": (7, 9, 11, 13, 15),
    }.get(difficulty, ODD_SIDES)


def _profile_geometry(ctx, profile, difficulty):
    if profile in PUBLIC_PROFILES:
        side = _PUBLIC_SIDE_BY_PROFILE[profile]
        return side, side, side // 2, side // 2
    if profile == "center_9":
        return 9, 9, 4, 4

    sizes = _size_options(difficulty)
    if profile == "offset_square":
        square_sizes = tuple(side for side in sizes if side >= 5)
        side = ctx.draw_choice("square_size", square_sizes)
        center = (side // 2, side // 2)
        positions = tuple(
            (row, col)
            for row in range(1, side - 1)
            for col in range(1, side - 1)
            if (row, col) != center
        )
        marker_row, marker_col = ctx.draw_choice(
            "marker_position",
            positions,
        )
        return side, side, marker_row, marker_col

    if profile == "edge_square":
        side = ctx.draw_choice("square_size", sizes)
        positions = tuple(
            (row, col)
            for row in range(side)
            for col in range(side)
            if (
                row in (0, side - 1)
                or col in (0, side - 1)
            )
            and (row, col) != (0, 0)
        )
        marker_row, marker_col = ctx.draw_choice(
            "marker_position",
            positions,
        )
        return side, side, marker_row, marker_col

    dimensions = tuple(
        (height, width)
        for height, width in product(sizes, repeat=2)
        if height != width
    )
    height, width = ctx.draw_choice(
        "rectangle_dimensions",
        dimensions,
    )
    center = (height // 2, width // 2)
    if profile == "rect_center":
        marker_row, marker_col = center
    elif profile == "rect_offset":
        positions = tuple(
            (row, col)
            for row in range(1, height - 1)
            for col in range(1, width - 1)
            if (row, col) != center
        )
        marker_row, marker_col = ctx.draw_choice(
            "marker_position",
            positions,
        )
    else:
        raise ValueError(f"unknown scene profile: {profile!r}")
    return height, width, marker_row, marker_col


def _validate_rectangular_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty rectangular sequence")
    first = grid[0]
    if not isinstance(first, (list, tuple)) or not first:
        raise ValueError("grid rows must be nonempty sequences")
    width = len(first)
    if len(grid) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30x30")
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise ValueError(f"row {row_index} must have width {width}")
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                raise ValueError("all cells must be integer ARC colors 0..9")
    return len(grid), width


def _classify_profile(height, width, marker_row, marker_col):
    centered = (
        marker_row == height // 2
        and marker_col == width // 2
    )
    on_edge = (
        marker_row in (0, height - 1)
        or marker_col in (0, width - 1)
    )
    interior = (
        0 < marker_row < height - 1
        and 0 < marker_col < width - 1
    )
    if height == width and centered:
        for profile, side in _PUBLIC_SIDE_BY_PROFILE.items():
            if height == side:
                return profile
        if height == 9:
            return "center_9"
    if (
        height == width
        and height in ODD_SIDES
        and on_edge
        and (marker_row, marker_col) != (0, 0)
    ):
        return "edge_square"
    if (
        height == width
        and height in ODD_SIDES
        and height >= 5
        and interior
        and not centered
    ):
        return "offset_square"
    if (
        height != width
        and height in ODD_SIDES
        and width in ODD_SIDES
        and centered
    ):
        return "rect_center"
    if (
        height != width
        and height in ODD_SIDES
        and width in ODD_SIDES
        and interior
        and not centered
    ):
        return "rect_offset"
    return None


def _analyze(grid):
    height, width = _validate_rectangular_grid(grid)
    background = grid[0][0]
    if background == 0:
        raise ValueError("cell (0,0) must be a nonzero background")
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
    ]
    if len(markers) != 1:
        raise ValueError(
            f"expected exactly one black marker, found {len(markers)}"
        )
    if any(
        value not in (0, background)
        for row in grid
        for value in row
    ):
        raise ValueError(
            "every non-marker cell must equal the top-left background"
        )
    marker_row, marker_col = markers[0]
    return {
        "height": height,
        "width": width,
        "background_color": background,
        "marker_row": marker_row,
        "marker_col": marker_col,
        "scene_profile": _classify_profile(
            height,
            width,
            marker_row,
            marker_col,
        ),
    }
