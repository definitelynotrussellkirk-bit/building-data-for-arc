"""Generator for 878187ab: encode two point-set counts as a diamond.

The input is a sparse 15x15 or 16x16 field with one modal background and
exactly two foreground colors.  Let H be the smaller foreground count and W
the larger.  The output is a 16x16 canvas in the input background whose
bottom H rows contain a W-wide color-2 block, with color-4 markers tracing
the two clipped diamond edges.

All three demonstrated linked profiles are generated directly:
15x15/H5/W7, 16x16/H5/W10, and 16x16/H12/W14.  A calibrated generalized
branch supplies other lawful H/W pairs and modal backgrounds on the same
15x15/16x16 canvases, so the output cannot be memorized as one of only three
labels or one fixed background.  Foreground colors and point locations vary
independently because the rule depends only on their counts.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "e9b415370025"
TASK_ID = "e9b415370025"
VERSION = "3.0.0"
RULE_HASH = "d973d40ee762"

SUMMARY = (
    "Count two sparse foreground point sets on their modal background.  Use the "
    "smaller count as output height and the larger count as output width, "
    "then mark the two clipped-diamond edges in color 4 inside a color-2 "
    "block on a fixed 16x16 canvas.  Public linked profiles have a calibrated "
    "30% prior; lawful generalized counts and backgrounds provide diversity."
)

EXAMPLES_NEEDED = 3
EXPECTED_OUTPUT_CODOMAIN = 780
OUTPUT_CODOMAIN_BY_DIFFICULTY = {
    "easy": 200,
    "medium": 340,
    "hard": 230,
    None: 780,
}

INVARIANTS = [
    "background is always the strict mode; linked public profiles use color 7",
    "exactly two distinct non-background colors are present",
    "the two foreground counts satisfy 2 <= H < W <= 14",
    "public profiles are 15x15/H5/W7, 16x16/H5/W10, and 16x16/H12/W14",
    "other lawful count/background tuples form one observable generalized branch",
    "foreground positions and identities do not affect the count-coded answer",
]

PUBLIC_SCENE_PROFILES = (
    "h5_w10_16",
    "h5_w7_15",
    "h12_w14_16",
)

SCENE_PROFILES = PUBLIC_SCENE_PROFILES + ("generalized",)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "30% linked-public profile, 70% generalized",
        "valid": "h5_w10_16|h5_w7_15|h12_w14_16|generalized",
        "doc": (
            "Linked input canvas, smaller foreground count H, and larger "
            "foreground count W.  The three public tuples are named; all "
            "other calibrated tuples are observed as generalized."
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_PROFILE_DATA = {
    "h5_w10_16": {
        "canvas": (16, 16),
        "min_count": 5,
        "max_count": 10,
        "public_layers": (
            (
                6,
                (
                    (3, 1),
                    (3, 12),
                    (4, 3),
                    (11, 6),
                    (12, 9),
                ),
            ),
            (
                8,
                (
                    (0, 1),
                    (1, 12),
                    (2, 6),
                    (4, 9),
                    (8, 6),
                    (10, 14),
                    (11, 3),
                    (12, 14),
                    (13, 8),
                    (15, 14),
                ),
            ),
        ),
    },
    "h5_w7_15": {
        "canvas": (15, 15),
        "min_count": 5,
        "max_count": 7,
        "public_layers": (
            (
                5,
                (
                    (3, 9),
                    (7, 5),
                    (8, 8),
                    (10, 11),
                    (11, 8),
                ),
            ),
            (
                4,
                (
                    (1, 1),
                    (2, 14),
                    (3, 8),
                    (7, 3),
                    (7, 14),
                    (12, 1),
                    (12, 6),
                ),
            ),
        ),
    },
    "h12_w14_16": {
        "canvas": (16, 16),
        "min_count": 12,
        "max_count": 14,
        "public_layers": (
            (
                5,
                (
                    (0, 11),
                    (2, 3),
                    (3, 5),
                    (5, 7),
                    (7, 1),
                    (7, 13),
                    (8, 10),
                    (10, 1),
                    (10, 12),
                    (11, 2),
                    (11, 11),
                    (13, 15),
                ),
            ),
            (
                0,
                (
                    (1, 10),
                    (1, 14),
                    (2, 10),
                    (2, 15),
                    (4, 9),
                    (4, 11),
                    (7, 8),
                    (7, 10),
                    (7, 12),
                    (8, 5),
                    (8, 15),
                    (10, 10),
                    (12, 2),
                    (13, 3),
                ),
            ),
        ),
    },
}

_PROFILE_INDEX = {
    profile: index
    for index, profile in enumerate(PUBLIC_SCENE_PROFILES)
}


def _blank(height, width, color):
    return [
        [color for _col in range(width)]
        for _row in range(height)
    ]


def _render_public(profile):
    data = _PROFILE_DATA[profile]
    height, width = data["canvas"]
    grid = _blank(height, width, 7)
    for color, cells in data["public_layers"]:
        for row, col in cells:
            grid[row][col] = color
    return grid


_PUBLIC_GRIDS = {
    profile: tuple(
        tuple(row)
        for row in _render_public(profile)
    )
    for profile in PUBLIC_SCENE_PROFILES
}

_PUBLIC_GRID_TO_PROFILE = {
    grid: profile
    for profile, grid in _PUBLIC_GRIDS.items()
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


def _mode_first_seen(values):
    counts = Counter(values)
    if not counts:
        return None
    best_count = max(counts.values())
    return next(value for value in values if counts[value] == best_count)


def _analyze_scene(grid):
    original, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    height = len(original)
    width = len(original[0])
    flat = [value for row in original for value in row]
    counts = Counter(flat)
    background = _mode_first_seen(flat)
    if any(
        counts[background] <= count
        for color, count in counts.items()
        if color != background
    ):
        return None
    foreground = sorted(
        (count, color)
        for color, count in counts.items()
        if color != background
    )
    if len(foreground) != 2:
        return None
    if foreground[0][0] == foreground[1][0]:
        return None
    profile = None
    if background == 7:
        profile = next(
            (
                name
                for name, data in _PROFILE_DATA.items()
                if data["canvas"] == (height, width)
                and data["min_count"] == foreground[0][0]
                and data["max_count"] == foreground[1][0]
            ),
            None,
        )
    if (
        profile is None
        and (height, width) in ((15, 15), (16, 16))
        and 2 <= foreground[0][0] < foreground[1][0] <= 14
    ):
        profile = "generalized"
    if profile is None:
        return None
    frozen = tuple(tuple(row) for row in original)
    return {
        "scene_profile": profile,
        "height": height,
        "width": width,
        "background": background,
        "min_count": foreground[0][0],
        "max_count": foreground[1][0],
        "min_color": foreground[0][1],
        "max_color": foreground[1][1],
        "exact_public": frozen in _PUBLIC_GRID_TO_PROFILE,
    }


def observe_overrides(grid):
    """Recover every declared semantic axis from the returned grid."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def canonical_profile_index(grid):
    """Return the linked public profile index, or ``None``."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return None
    return _PROFILE_INDEX.get(analysis["scene_profile"])


def exact_public_profile_index(grid):
    """Return the public input index only for a literal demonstrated grid."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    profile = _PUBLIC_GRID_TO_PROFILE.get(
        tuple(tuple(row) for row in original)
    )
    return _PROFILE_INDEX[profile] if profile is not None else None


def canonical_profile_signature(grid):
    """Return the complete linked canvas/count signature."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return None
    return (
        analysis["height"],
        analysis["width"],
        analysis["background"],
        2,
        analysis["min_count"],
        analysis["max_count"],
    )


def self_check(grid, *, difficulty=None, meta=None):
    """Strictly recognize the calibrated public-plus-generalized grammar."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if difficulty not in (None, "easy", "medium", "hard"):
        return ["difficulty must be easy, medium, hard, or None"]
    analysis = _analyze_scene(original)
    if analysis is None:
        return [
            "grid must have one strict modal background, exactly two "
            "foreground colors, a 15x15/16x16 canvas, and counts "
            "2 <= H < W <= 14"
        ]
    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = meta
        requested_profile = requested.get("scene_profile")
        if (
            requested_profile is not None
            and analysis["scene_profile"] != requested_profile
        ):
            errors.append(
                f"scene_profile requested {requested_profile!r}, "
                f"observed {analysis['scene_profile']!r}"
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


def _profile_options(difficulty):
    if difficulty == "easy":
        return (
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "h5_w7_15",
            "h5_w7_15",
            "h5_w7_15",
            "h5_w10_16",
            "h5_w10_16",
            "h12_w14_16",
        )
    if difficulty == "hard":
        return (
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "h5_w7_15",
            "h5_w10_16",
            "h12_w14_16",
            "h12_w14_16",
            "h12_w14_16",
            "h12_w14_16",
        )
    return (
        "generalized",
        "generalized",
        "generalized",
        "generalized",
        "generalized",
        "generalized",
        "generalized",
        "generalized",
        "generalized",
        "generalized",
        "generalized",
        "generalized",
        "generalized",
        "generalized",
        "h5_w7_15",
        "h5_w7_15",
        "h5_w10_16",
        "h5_w10_16",
        "h12_w14_16",
        "h12_w14_16",
    )


def _generalized_signatures(difficulty):
    if difficulty == "easy":
        min_values = range(2, 6)
        max_limit = 8
    elif difficulty == "hard":
        min_values = range(8, 14)
        max_limit = 14
    elif difficulty == "medium":
        min_values = range(4, 10)
        max_limit = 12
    else:
        min_values = range(2, 14)
        max_limit = 14
    public = {
        (data["canvas"], data["min_count"], data["max_count"])
        for data in _PROFILE_DATA.values()
    }
    return tuple(
        (height, width, min_count, max_count)
        for height, width in ((15, 15), (16, 16))
        for min_count in min_values
        for max_count in range(min_count + 1, max_limit + 1)
        if ((height, width), min_count, max_count) not in public
    )


def _render_generalized(profile, context):
    if profile == "generalized":
        height, width, min_count, max_count = context.draw_choice(
            "generalized_signature",
            _generalized_signatures(context.difficulty),
        )
        background = context.draw_color("generalized_background")
    else:
        data = _PROFILE_DATA[profile]
        height, width = data["canvas"]
        min_count = data["min_count"]
        max_count = data["max_count"]
        background = 7
    grid = _blank(height, width, background)
    colors = context.draw_distinct_colors(
        "foreground_colors",
        n=2,
        exclude={background},
    )
    positions = [
        (row, col)
        for row in range(height)
        for col in range(width)
    ]
    placement_rng = context.draw_rng("placement")
    placement_rng.shuffle(positions)
    total = min_count + max_count
    for row, col in positions[:min_count]:
        grid[row][col] = colors[0]
    for row, col in positions[min_count:total]:
        grid[row][col] = colors[1]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = context.draw_choice(
        "scene_profile",
        _profile_options(difficulty),
    )
    literal_rng = context.draw_rng("literal_public")
    if profile != "generalized" and literal_rng.randrange(6) == 0:
        grid = [
            list(row)
            for row in _PUBLIC_GRIDS[profile]
        ]
    else:
        grid = _render_generalized(profile, context)
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
    """Broad, input-pure Python mirror of the canonical Racket rule."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    flat = [value for row in original for value in row]
    background = _mode_first_seen(flat)
    colors = []
    for value in flat:
        if value != background and value not in colors:
            colors.append(value)
    if not colors:
        raise ValueError("the rule requires at least one non-background color")
    counts = [
        sum(value == color for value in flat)
        for color in colors
    ]
    height_count = min(counts)
    width_count = max(counts)
    if height_count > 16 or width_count > 16:
        raise ValueError("foreground counts must fit the fixed 16x16 output")
    output = _blank(16, 16, background)
    top = 16 - height_count
    for index in range(height_count):
        row = top + index
        for col in range(width_count):
            output[row][col] = 2
        offset = width_count - height_count + index
        left = min(offset, width_count - 1 - offset)
        right = width_count - 1 - left
        output[row][left] = 4
        output[row][right] = 4
    return output
