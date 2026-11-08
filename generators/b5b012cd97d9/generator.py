"""Generator for ARC rule family b5b012cd97d9 (source task 8abad3cf).

The Racket rule treats the most frequent *nonzero* color as background,
counts every remaining color, and packs the largest repeated mass, the next
repeated mass, and an optional singleton into a canonical square layout.

The calibrated distribution is built from the three complete public scene
families.  It includes the demonstrated no-singleton branch and the held-out
case where zero is an answer-bearing 4x4 mass rather than background.
Position is a lawful nuisance, so non-canonical examples use exact horizontal,
vertical, or 180-degree reflections of the public role geometry.
"""
from __future__ import annotations

import math
from collections import Counter

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "b5b012cd97d9"
TASK_ID = "b5b012cd97d9"
VERSION = "3.0.0"
RULE_HASH = "8dee168c2b2a"

SUMMARY = (
    "Choose the most frequent nonzero color as background. Count every "
    "other color; turn the largest repeated count and the next repeated "
    "count into solid squares whose side lengths are their integer square "
    "roots, and preserve an optional singleton. Place the big square at "
    "the upper right, the smaller square at the lower left, and—when "
    "present—the singleton at the bottom-left corner."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "the input is one of the three complete public canvas/count families",
    "the modal nonzero background is unique and more frequent than any role",
    "big and small role counts are distinct positive perfect squares",
    "the no-singleton 7x4 family and the zero-big 5x10 family are both live",
    "layout variation changes positions only and preserves every role count",
    "the output is recomputed by the broad count-and-pack semantic rule",
]

SCENE_PROFILES = (
    "with_single_7x7_4_3",
    "no_single_7x4_3_2",
    "zero_big_5x10_4_2",
)

LAYOUT_VARIANTS = (
    "canonical",
    "horizontal",
    "vertical",
    "rotated_180",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted complete public family",
        "valid": (
            "with_single_7x7_4_3|no_single_7x4_3_2|"
            "zero_big_5x10_4_2"
        ),
    },
    "layout_variant": {
        "type": "str",
        "default": "40% canonical; 20% each nonidentity reflection",
        "valid": "canonical|horizontal|vertical|rotated_180",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()


_PROFILE_DATA = {
    "with_single_7x7_4_3": {
        "canvas": (7, 7),
        "big_side": 4,
        "small_side": 3,
        "has_single": True,
        "zero_role": "none",
        "template": (
            "BBBBB..",
            "B...B.S",
            "B.I.B.S",
            "B...B..",
            "BBBBB.S",
            "......S",
            "SSSSS..",
        ),
    },
    "no_single_7x4_3_2": {
        "canvas": (7, 4),
        "big_side": 3,
        "small_side": 2,
        "has_single": False,
        "zero_role": "none",
        "template": (
            "BBBB",
            "..B.",
            "BBBB",
            "....",
            ".S.S",
            ".S.S",
            "....",
        ),
    },
    "zero_big_5x10_4_2": {
        "canvas": (5, 10),
        "big_side": 4,
        "small_side": 2,
        "has_single": True,
        "zero_role": "big",
        "template": (
            "...BBB...S",
            "BB.B.B.I.S",
            "BB.BBB...S",
            ".......B.S",
            ".....BBB..",
        ),
    },
}

_PROFILE_BY_CANVAS = {
    data["canvas"]: profile
    for profile, data in _PROFILE_DATA.items()
}

_PROFILE_INDEX = {
    profile: index
    for index, profile in enumerate(SCENE_PROFILES)
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
    errors = []
    converted = []
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


def _unique_racket_background(grid):
    """Return `(mode g)` when its nonzero maximum is unambiguous."""
    counts = Counter(
        value
        for row in grid
        for value in row
        if value != 0
    )
    if not counts:
        return None
    maximum = max(counts.values())
    candidates = [
        color
        for color, count in counts.items()
        if count == maximum
    ]
    return candidates[0] if len(candidates) == 1 else None


def _variant_template(template, variant):
    if variant == "canonical":
        return tuple(template)
    if variant == "horizontal":
        return tuple(row[::-1] for row in template)
    if variant == "vertical":
        return tuple(reversed(template))
    if variant == "rotated_180":
        return tuple(row[::-1] for row in reversed(template))
    raise ValueError(f"unknown layout variant {variant!r}")


def _role_template(grid, colors):
    inverse = {
        colors["background"]: ".",
        colors["big"]: "B",
        colors["small"]: "S",
    }
    if colors.get("single") is not None:
        inverse[colors["single"]] = "I"
    try:
        return tuple(
            "".join(inverse[value] for value in row)
            for row in grid
        )
    except KeyError:
        return None


def _analyze_scene(grid):
    """Recover the complete linked public profile and exact layout variant."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    canvas = (len(coerced), len(coerced[0]))
    profile = _PROFILE_BY_CANVAS.get(canvas)
    if profile is None:
        return None
    data = _PROFILE_DATA[profile]
    counts = Counter(value for row in coerced for value in row)
    background = _unique_racket_background(coerced)
    if background is None or background == 0:
        return None

    expected_roles = 2 + int(data["has_single"])
    if len(counts) != expected_roles + 1:
        return None
    big_count = data["big_side"] ** 2
    small_count = data["small_side"] ** 2
    single_count = 1 if data["has_single"] else 0
    expected_background = (
        canvas[0] * canvas[1]
        - big_count
        - small_count
        - single_count
    )
    if counts.get(background) != expected_background:
        return None

    role_colors = {
        "background": background,
        "big": None,
        "small": None,
        "single": None,
    }
    for color, count in counts.items():
        if color == background:
            continue
        if count == big_count:
            role = "big"
        elif count == small_count:
            role = "small"
        elif data["has_single"] and count == 1:
            role = "single"
        else:
            return None
        if role_colors[role] is not None:
            return None
        role_colors[role] = color
    if role_colors["big"] is None or role_colors["small"] is None:
        return None
    if data["has_single"] != (role_colors["single"] is not None):
        return None
    if data["zero_role"] == "big":
        if role_colors["big"] != 0:
            return None
    elif 0 in counts:
        return None

    observed_template = _role_template(coerced, role_colors)
    layout_variant = None
    for candidate in LAYOUT_VARIANTS:
        if observed_template == _variant_template(
            data["template"],
            candidate,
        ):
            layout_variant = candidate
            break
    if layout_variant is None:
        return None
    return {
        "scene_profile": profile,
        "layout_variant": layout_variant,
        "colors": role_colors,
        "counts": {
            "background": expected_background,
            "big": big_count,
            "small": small_count,
            "single": single_count,
        },
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
    """Return the complete public count/canvas-family index, if calibrated."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return None
    return _PROFILE_INDEX[analysis["scene_profile"]]


def exact_public_profile_index(grid):
    """Return the public-family index only for the unreflected role layout."""
    analysis = _analyze_scene(grid)
    if analysis is None or analysis["layout_variant"] != "canonical":
        return None
    return _PROFILE_INDEX[analysis["scene_profile"]]


def self_check(grid, *, difficulty=None, meta=None):
    """Strictly recognize the calibrated public-profile/symmetry grammar."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    analysis = _analyze_scene(coerced)
    if analysis is None:
        return [
            "grid must match one complete public canvas/count/zero-role "
            "profile and one supported role-layout symmetry"
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
            "no_single_7x4_3_2",
            "no_single_7x4_3_2",
            "with_single_7x7_4_3",
            "zero_big_5x10_4_2",
        )
    if difficulty == "hard":
        return (
            "zero_big_5x10_4_2",
            "zero_big_5x10_4_2",
            "with_single_7x7_4_3",
            "no_single_7x4_3_2",
        )
    return SCENE_PROFILES


def _draw_role_colors(ctx, profile):
    data = _PROFILE_DATA[profile]
    if data["zero_role"] == "big":
        background, small, single = ctx.draw_distinct_colors(
            "palette",
            n=3,
            exclude={0},
        )
        return {
            "background": background,
            "big": 0,
            "small": small,
            "single": single,
        }
    role_count = 3 + int(data["has_single"])
    palette = ctx.draw_distinct_colors(
        "palette",
        n=role_count,
        exclude={0},
    )
    return {
        "background": palette[0],
        "big": palette[1],
        "small": palette[2],
        "single": palette[3] if data["has_single"] else None,
    }


def _render_profile(profile, variant, colors):
    template = _variant_template(
        _PROFILE_DATA[profile]["template"],
        variant,
    )
    role_colors = {
        ".": colors["background"],
        "B": colors["big"],
        "S": colors["small"],
    }
    if colors["single"] is not None:
        role_colors["I"] = colors["single"]
    return [
        [role_colors[role] for role in row]
        for row in template
    ]


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
            "horizontal",
            "vertical",
            "rotated_180",
        ),
    )
    colors = _draw_role_colors(ctx, profile)
    grid = _render_profile(profile, variant, colors)
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
    """Broad Python mirror of the canonical Racket count-and-pack rule."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    background = _unique_racket_background(original)
    if background is None:
        raise ValueError(
            "the Racket mode background must have a unique nonzero maximum"
        )
    counts = Counter(value for row in original for value in row)
    colors = sorted(color for color in counts if color != background)
    entries = [(counts[color], color) for color in colors]
    if not entries:
        raise ValueError("the rule requires at least one non-background color")
    sorted_entries = sorted(
        entries,
        key=lambda entry: entry[0],
        reverse=True,
    )
    big_count, big_color = sorted_entries[0]
    repeated = [
        entry
        for entry in sorted_entries[1:]
        if entry[0] > 1
    ]
    small = repeated[0] if repeated else None
    single = next(
        (entry for entry in entries if entry[0] == 1),
        None,
    )

    def square_side(count):
        side = math.isqrt(count)
        if side < 1 or side * side != count:
            raise ValueError(
                f"color count {count} is not a positive perfect square"
            )
        return side

    big_side = square_side(big_count)
    small_side = square_side(small[0]) if small else 0
    output_height = max(
        big_side,
        small_side + int(single is not None),
    )
    small_col = 2 if single else 0
    big_col = small_col + small_side + 1
    output_width = big_col + big_side
    small_row = output_height - small_side
    output = [
        [background for _col in range(output_width)]
        for _row in range(output_height)
    ]
    for row in range(big_side):
        for col in range(big_col, big_col + big_side):
            output[row][col] = big_color
    if small:
        for row in range(small_row, output_height):
            for col in range(small_col, small_col + small_side):
                output[row][col] = small[1]
    if single:
        output[-1][0] = single[1]
    return output
