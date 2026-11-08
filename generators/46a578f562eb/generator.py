"""Generator for ARC rule family 46a578f562eb (source task d037b0a7).

Each nonzero seed keeps its color.  Every zero below the first nonzero seed in
its column takes that top seed's color.  The calibrated family preserves one
of the four published 3x3 seed-row profiles while applying exact color,
column-permutation, and bounded zero-margin metamorphisms.
"""
from __future__ import annotations

from itertools import permutations, product

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "46a578f562eb"
TASK_ID = "46a578f562eb"
VERSION = "3.1.0"
RULE_HASH = "38f0f6fa9469"

SUMMARY = (
    "Preserve every nonzero seed. In each column, fill every zero below the "
    "topmost seed with that seed's color; cells above the first seed remain "
    "zero."
)

INVARIANTS = [
    "the canvas is 3x3",
    "there are exactly two or three pairwise-distinct nonzero seeds",
    "no two seeds share a column",
    "the complete seed-row multiset matches one published profile",
    "any larger canvas is only a bounded all-zero margin around that profile",
    "the rule changes at least one zero below a seed",
]

SCENE_PROFILES = (
    "three_seed_middle_pair",
    "three_seed_diagonal",
    "two_seed_stair",
    "three_seed_split",
)
LAYOUT_MODES = ("canonical", "permuted")
CANVAS_MODES = ("canonical", "padded")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted complete published seed profile",
        "valid": (
            "three_seed_middle_pair|three_seed_diagonal|"
            "two_seed_stair|three_seed_split"
        ),
    },
    "layout_mode": {
        "type": "str",
        "default": "20% canonical and 80% noncanonical column permutation",
        "valid": "canonical|permuted",
    },
    "canvas_mode": {
        "type": "str",
        "default": "20% exact 3x3 and 80% bounded zero-margin extension",
        "valid": "canonical|padded",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

# The four unique public inputs.  Concrete seed colors are nuisance variables:
# the rule is equivariant under any permutation of nonzero colors.
_CANONICAL_POSITIONS = {
    "three_seed_middle_pair": ((0, 1), (1, 0), (1, 2)),
    "three_seed_diagonal": ((0, 2), (1, 1), (2, 0)),
    "two_seed_stair": ((0, 0), (1, 1)),
    "three_seed_split": ((0, 0), (0, 2), (2, 1)),
}

_PROFILE_BY_ROWS = {
    (0, 1, 1): "three_seed_middle_pair",
    (0, 1, 2): "three_seed_diagonal",
    (0, 1): "two_seed_stair",
    (0, 0, 2): "three_seed_split",
}

_PROFILE_INDEX = {
    profile: index for index, profile in enumerate(SCENE_PROFILES)
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


def _markers(grid):
    return tuple(
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    )


def _column_permuted_positions(profile):
    canonical = _CANONICAL_POSITIONS[profile]
    variants = {
        tuple(sorted((row, column_order[col]) for row, col in canonical))
        for column_order in permutations(range(3))
    }
    return tuple(sorted(variants))


_POSITION_VARIANTS = {
    profile: _column_permuted_positions(profile)
    for profile in SCENE_PROFILES
}


def _semantic_signature(grid):
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    found = _markers(coerced)
    if len(found) not in (2, 3):
        return None
    if len({value for _row, _col, value in found}) != len(found):
        return None
    if len({col for _row, col, _value in found}) != len(found):
        return None
    top = min(row for row, _col, _value in found)
    profile = _PROFILE_BY_ROWS.get(tuple(sorted(
        row - top for row, _col, _value in found
    )))
    if profile is None:
        return None
    height = len(coerced)
    width = len(coerced[0])
    if len(found) == 3:
        left = min(col for _row, col, _value in found)
        bottom = height - (top + 3)
        right = width - (left + 3)
        if (
            not 0 <= top <= 3
            or not 0 <= bottom <= 3
            or not 0 <= left <= 3
            or not 0 <= right <= 3
        ):
            return None
    else:
        left = 0
        bottom = height - (top + 3)
        right = 0
        if (
            width != 3
            or not 0 <= top <= 3
            or not 0 <= bottom <= 3
        ):
            return None
    positions = tuple(sorted(
        (row - top, col - left)
        for row, col, _value in found
    ))
    if positions not in _POSITION_VARIANTS[profile]:
        return None
    layout_mode = (
        "canonical"
        if positions == tuple(sorted(_CANONICAL_POSITIONS[profile]))
        else "permuted"
    )
    canvas_mode = (
        "canonical"
        if (top, bottom, left, right) == (0, 0, 0, 0)
        else "padded"
    )
    return {
        "scene_profile": profile,
        "layout_mode": layout_mode,
        "canvas_mode": canvas_mode,
    }


def canonical_profile_index(grid):
    """Return the linked public seed-row profile index, if calibrated."""
    signature = _semantic_signature(grid)
    if signature is None:
        return None
    return _PROFILE_INDEX[signature["scene_profile"]]


def observe_overrides(grid):
    """Recover every declared exact axis from a valid returned grid."""
    signature = _semantic_signature(grid)
    if signature is None:
        return {}
    return dict(signature)


def _profile_options(difficulty):
    return sum(
        ((profile,) * 25 for profile in SCENE_PROFILES),
        (),
    )


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
        "layout_mode" in overrides
        and overrides["layout_mode"] not in LAYOUT_MODES
    ):
        raise ValueError("unknown layout_mode")
    if (
        "canvas_mode" in overrides
        and overrides["canvas_mode"] not in CANVAS_MODES
    ):
        raise ValueError("unknown canvas_mode")


def _padding_options(profile, difficulty):
    max_padding = {
        "easy": 1,
        "hard": 3,
    }.get(difficulty, 2)
    if profile == "two_seed_stair":
        return tuple(
            (top, bottom, 0, 0)
            for top, bottom in product(
                range(max_padding + 1),
                repeat=2,
            )
            if top or bottom
        )
    return tuple(
        padding
        for padding in product(
            range(max_padding + 1),
            repeat=4,
        )
        if any(padding)
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
    profile = ctx.draw_choice(
        "scene_profile",
        _profile_options(difficulty),
    )
    layout_mode = ctx.draw_choice(
        "layout_mode",
        ("canonical",) * 20 + ("permuted",) * 80,
    )
    canvas_mode = ctx.draw_choice(
        "canvas_mode",
        ("canonical",) * 20 + ("padded",) * 80,
    )
    canonical = tuple(sorted(_CANONICAL_POSITIONS[profile]))
    if layout_mode == "canonical":
        positions = canonical
    else:
        positions = ctx.draw_choice(
            "column_permutation",
            tuple(
                variant
                for variant in _POSITION_VARIANTS[profile]
                if variant != canonical
            ),
        )
    if canvas_mode == "canonical":
        top, bottom, left, right = 0, 0, 0, 0
    else:
        top, bottom, left, right = ctx.draw_choice(
            "zero_margins",
            _padding_options(profile, difficulty),
        )
    colors = ctx.draw_distinct_colors(
        "seed_colors",
        n=len(positions),
        exclude={0},
    )
    color_rng = ctx.draw_rng("color_assignment")
    colors = list(colors)
    color_rng.shuffle(colors)
    grid = [
        [0 for _col in range(left + 3 + right)]
        for _row in range(top + 3 + bottom)
    ]
    for (row, col), color in zip(positions, colors):
        grid[top + row][left + col] = color
    observed = _semantic_signature(grid)
    if observed != {
        "scene_profile": profile,
        "layout_mode": layout_mode,
        "canvas_mode": canvas_mode,
    }:
        raise AssertionError("constructed scene lost an exact axis")
    return grid


def rule_mirror(grid):
    """Independent Python mirror of the canonical topmost-column rule."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [row[:] for row in coerced]
    height = len(coerced)
    width = len(coerced[0])
    for col in range(width):
        topmost = None
        for row in range(height):
            value = coerced[row][col]
            if value != 0:
                if topmost is None:
                    topmost = value
            elif topmost is not None:
                output[row][col] = topmost
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept only complete published seed profiles and metamorphisms."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if _semantic_signature(coerced) is None:
        return [
            "grid must preserve one complete published seed profile: two "
            "or three distinct seeds, one per active column, an exact "
            "linked seed-row multiset, and only bounded all-zero margins"
        ]
    if rule_mirror(coerced) == coerced:
        return ["topmost-column fill must change at least one cell"]
    return []
