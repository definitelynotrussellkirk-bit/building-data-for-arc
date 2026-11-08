"""Semantic generator for ARC task ``c0aac14eef4d`` (RE-ARC bbc9ae5d).

The input is one even-width row containing one nonzero color.  Let ``n`` be
its number of nonzero cells.  The output has ``width / 2`` rows; output row
``r`` is a left-aligned prefix of ``n + r`` cells in the input color.

All six public input signatures are explicit scene profiles.  Generalized
profiles move the same number of markers to the right edge, alternating
columns, both edges, an interior block, or an irregular scatter.  Those
non-left layouts are decisive counterexamples to canonical-compatible shortcut
rules that copy marker positions, use the rightmost marker, or measure only the
leading run instead of counting all markers.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "c0aac14eef4d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "7e58a2e36b58"
MIN_STRICT_FRAC = 0.05
EXAMPLES_NEEDED = 5

SUMMARY = (
    "Count every nonzero cell in the one-row input. Build a width/2 by width "
    "output whose row r is a left-aligned prefix of count+r cells in the same "
    "nonzero color; all remaining cells are background 0."
)

INVARIANTS = [
    "the input is exactly one nonempty row with an even width from 4 through 30",
    "all cells are ARC colors 0..9 and exactly one nonzero color is present",
    "at least one cell carries that nonzero color",
    "marker positions are nuisance geometry: only their count affects the output",
    "the output height is input width/2 and each successive row grows by one cell",
]

COUNTER_HYPOTHESES = [
    "copy the input marker layout into row 0 and grow it rightward",
    "use the rightmost marker position rather than the marker count",
    "use only the leading nonzero run rather than all markers",
    "grow every input marker independently while preserving gaps",
    "start every staircase at half the input width",
    "always paint with color 1",
    "always emit three output rows",
]

PUBLIC_PROFILES = (
    "public_w6_n4",
    "public_w8_n1",
    "public_w10_n3",
    "public_w6_n1",
    "public_w6_n2",
    "public_w12_n3",
)
GENERAL_PROFILES = (
    "left_general",
    "right_block",
    "alternating",
    "edge_split",
    "interior_block",
    "scattered",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "canonical-anchored profile prior plus non-left shortcut witnesses",
        "valid": (
            "public_w6_n4|public_w8_n1|public_w10_n3|public_w6_n1|"
            "public_w6_n2|public_w12_n3|left_general|right_block|"
            "alternating|edge_split|interior_block|scattered"
        ),
    },
    "color": {
        "type": "color",
        "default": "rng nonzero ARC color",
        "valid": "1..9",
    },
}

# Every scene profile is compatible with every nonzero color.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)

_PUBLIC_SPECS = {
    "public_w6_n4": (6, 4),
    "public_w8_n1": (8, 1),
    "public_w10_n3": (10, 3),
    "public_w6_n1": (6, 1),
    "public_w6_n2": (6, 2),
    "public_w12_n3": (12, 3),
}
_PUBLIC_SIGNATURES = frozenset(
    (width, count, tuple(range(count)))
    for width, count in _PUBLIC_SPECS.values()
)
_PUBLIC_SIGNATURE_TO_PROFILE = {
    (width, count, tuple(range(count))): profile
    for profile, (width, count) in _PUBLIC_SPECS.items()
}

# Public profiles occupy 6/36 = 16.7% of the default prior in every band.
# Non-left profiles dominate the remaining mass so a five-demo lesson almost
# certainly contains a canonical-compatible shortcut counterexample.
_DEFAULT_PROFILE_POOL = (
    *PUBLIC_PROFILES,
    "left_general", "left_general", "left_general", "left_general", "left_general",
    "right_block", "right_block", "right_block", "right_block", "right_block",
    "alternating", "alternating", "alternating", "alternating", "alternating",
    "edge_split", "edge_split", "edge_split", "edge_split", "edge_split",
    "interior_block", "interior_block", "interior_block", "interior_block", "interior_block",
    "scattered", "scattered", "scattered", "scattered", "scattered",
)

_GENERAL_WIDTHS = {
    "easy": (4, 6, 8, 10, 12),
    "medium": (10, 12, 14, 16, 18, 20),
    "hard": (18, 20, 22, 24, 26, 28, 30),
}
_LEFT_GENERAL_PAIRS = {
    "easy": ((4, 1), (8, 3), (10, 5), (12, 7)),
    "medium": ((10, 1), (12, 5), (14, 2), (16, 7), (18, 4), (20, 9)),
    "hard": ((18, 2), (20, 5), (22, 3), (24, 11), (26, 7), (28, 13), (30, 4)),
}


def _validate_difficulty(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return str(difficulty)


def _positions(grid: Any) -> tuple[int, tuple[int, ...], int] | None:
    """Return (width, nonzero positions, color), or None for malformed grids."""
    if not isinstance(grid, (list, tuple)) or len(grid) != 1:
        return None
    row = grid[0]
    if not isinstance(row, (list, tuple)) or not row:
        return None
    values: list[int] = []
    for value in row:
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
            return None
        if value:
            values.append(value)
    colors = set(values)
    if len(colors) != 1:
        return None
    color = next(iter(colors))
    return len(row), tuple(i for i, value in enumerate(row) if value), color


def canonical_profile_signature(grid: Any):
    parsed = _positions(grid)
    if parsed is None:
        return None
    width, positions, _color = parsed
    return width, len(positions), positions


def _classify_positions(width: int, positions: tuple[int, ...]) -> str | None:
    count = len(positions)
    signature = (width, count, positions)
    public = _PUBLIC_SIGNATURE_TO_PROFILE.get(signature)
    if public is not None:
        return public
    if positions == tuple(range(count)):
        return "left_general"
    if positions == tuple(range(width - count, width)):
        return "right_block"
    if positions == tuple(range(0, 2 * count, 2)):
        return "alternating"
    if count >= 2:
        for left_count in range(1, count):
            right_count = count - left_count
            if positions == tuple(range(left_count)) + tuple(range(width - right_count, width)):
                return "edge_split"
    if positions and positions == tuple(range(positions[0], positions[0] + count)):
        if positions[0] > 0 and positions[-1] < width - 1:
            return "interior_block"
    if positions:
        return "scattered"
    return None


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every declared axis exactly from the returned grid."""
    parsed = _positions(grid)
    if parsed is None:
        return {}
    width, positions, color = parsed
    profile = _classify_positions(width, positions)
    if profile is None:
        return {}
    return {"scene_profile": profile, "color": color}


def _general_width(band: str, rng) -> int:
    return rng.choice(_GENERAL_WIDTHS[band])


def _general_count(width: int, rng, *, minimum: int = 1, maximum: int | None = None) -> int:
    upper = min(width - 1, maximum if maximum is not None else width - 1)
    if upper < minimum:
        raise ValueError(f"no legal marker count for width={width}, range={minimum}..{upper}")
    return rng.randint(minimum, upper)


def _profile_geometry(profile: str, band: str, rng) -> tuple[int, tuple[int, ...]]:
    if profile in _PUBLIC_SPECS:
        width, count = _PUBLIC_SPECS[profile]
        return width, tuple(range(count))

    if profile == "left_general":
        width, count = rng.choice(_LEFT_GENERAL_PAIRS[band])
        return width, tuple(range(count))

    width = _general_width(band, rng)
    if profile == "right_block":
        count = _general_count(width, rng, minimum=1)
        return width, tuple(range(width - count, width))

    if profile == "alternating":
        count = _general_count(width, rng, minimum=2, maximum=width // 2)
        return width, tuple(range(0, 2 * count, 2))

    if profile == "edge_split":
        count = _general_count(width, rng, minimum=2, maximum=width - 2)
        left_count = rng.randint(1, count - 1)
        right_count = count - left_count
        positions = tuple(range(left_count)) + tuple(range(width - right_count, width))
        return width, positions

    if profile == "interior_block":
        count = _general_count(width, rng, minimum=1, maximum=width - 2)
        start = rng.randint(1, width - count - 1)
        return width, tuple(range(start, start + count))

    if profile == "scattered":
        count = _general_count(width, rng, minimum=2, maximum=width - 2)
        columns = list(range(width))
        for _ in range(256):
            positions = tuple(sorted(rng.sample(columns, count)))
            if _classify_positions(width, positions) == "scattered":
                return width, positions
        raise ValueError("unable to construct an irregular scattered profile")

    raise ValueError(f"unknown scene profile: {profile!r}")


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    """Return one deterministic, valid, and fully observable one-row input."""
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")
    band = _validate_difficulty(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", _DEFAULT_PROFILE_POOL)
    color = ctx.draw_color("color", exclude={0})
    width, positions = _profile_geometry(profile, band, ctx.draw_rng("geometry"))
    grid = full_grid(1, width, 0)
    for column in positions:
        grid[0][column] = color

    errors = self_check(
        grid,
        difficulty=band,
        meta={"overrides": {"scene_profile": profile, "color": color}},
    )
    if errors:
        raise ValueError("internal generation error: " + "; ".join(errors))
    return grid


def schedule_profile(seed: int, sample_index: int, difficulty=None):
    """Reproduce the exact default scene-profile draw for schedule auditing."""
    band = _validate_difficulty(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides={},
    )
    return ctx.draw_choice("scene_profile", _DEFAULT_PROFILE_POOL)


SCHEDULE_PROFILES = SCENE_PROFILES


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-wide input grammar and exact requested axes."""
    del difficulty
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if len(grid) != 1:
        errors.append(f"expected exactly one row, found {len(grid)}")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return errors + ["grid row must be a nonempty sequence"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return errors
    if width < 4 or width > 30 or width % 2:
        errors.append(f"expected even width in 4..30, found {width}")

    foreground: list[int] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC color at ({r},{c}): {value!r}")
            elif value:
                foreground.append(value)
    colors = sorted(set(foreground))
    if not foreground:
        errors.append("expected at least one nonzero marker")
    elif len(colors) != 1:
        errors.append(f"expected exactly one nonzero color, found {colors}")

    if not errors and meta and isinstance(meta, dict):
        requested = meta.get("overrides", {})
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis in AXES:
                if axis in requested and observed.get(axis) != requested[axis]:
                    errors.append(
                        f"{axis} observed {observed.get(axis)!r}, requested {requested[axis]!r}"
                    )
    return errors


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent Python mirror of the selected canonical Racket rule."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid triangular-fill input: " + "; ".join(errors))
    width, positions, color = _positions(grid)  # type: ignore[misc]
    count = len(positions)
    return [
        [color if column < count + row else 0 for column in range(width)]
        for row in range(width // 2)
    ]


# ---------------------------------------------------------------------------
# Task-linked semantic contract and named rival rules
# ---------------------------------------------------------------------------

def strict_canonical_like(grid: Any) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    signature = canonical_profile_signature(grid)
    if signature not in _PUBLIC_SIGNATURES:
        return ["not one of the six linked public (width, count, left-prefix) signatures"]
    return []


def _clone(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _prefix_output(width: int, count: int, color: int, *, height: int | None = None):
    output_height = width // 2 if height is None else height
    return [
        [color if column < count + row else 0 for column in range(width)]
        for row in range(output_height)
    ]


def _rival_copy_input_then_grow(grid: Any):
    width, positions, color = _positions(grid)  # type: ignore[misc]
    count = len(positions)
    output = []
    for row_index in range(width // 2):
        row = list(grid[0])
        for column in range(min(width, count + row_index)):
            row[column] = color
        output.append(row)
    return output


def _rival_rightmost_extent(grid: Any):
    width, positions, color = _positions(grid)  # type: ignore[misc]
    return _prefix_output(width, positions[-1] + 1, color)


def _rival_leading_run(grid: Any):
    width, positions, color = _positions(grid)  # type: ignore[misc]
    position_set = set(positions)
    count = 0
    while count in position_set:
        count += 1
    return _prefix_output(width, count, color)


def _rival_grow_each_marker(grid: Any):
    width, positions, color = _positions(grid)  # type: ignore[misc]
    output = full_grid(width // 2, width, 0)
    for row in range(width // 2):
        for start in positions:
            for column in range(start, min(width, start + row + 1)):
                output[row][column] = color
    return output


def _rival_half_width_start(grid: Any):
    width, _positions_value, color = _positions(grid)  # type: ignore[misc]
    return _prefix_output(width, width // 2, color)


def _rival_color_one(grid: Any):
    width, positions, _color = _positions(grid)  # type: ignore[misc]
    return _prefix_output(width, len(positions), 1)


def _rival_three_rows(grid: Any):
    width, positions, color = _positions(grid)  # type: ignore[misc]
    return _prefix_output(width, len(positions), color, height=3)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "copy_input_then_grow": _rival_copy_input_then_grow,
    "rightmost_extent": _rival_rightmost_extent,
    "leading_run": _rival_leading_run,
    "grow_each_marker": _rival_grow_each_marker,
    "half_width_start": _rival_half_width_start,
    "color_one": _rival_color_one,
    "three_rows": _rival_three_rows,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "copy_input_then_grow",
        "rightmost_extent",
        "leading_run",
        "grow_each_marker",
    )
}


def _valid_parsed(grid: Any):
    return None if self_check(grid) else _positions(grid)


def _witness_non_left_layout(grid: Any) -> bool:
    parsed = _valid_parsed(grid)
    if parsed is None:
        return False
    _width, positions, _color = parsed
    return positions != tuple(range(len(positions)))


def _witness_count_not_half(grid: Any) -> bool:
    parsed = _valid_parsed(grid)
    return bool(parsed and len(parsed[1]) != parsed[0] // 2)


def _witness_color_not_one(grid: Any) -> bool:
    parsed = _valid_parsed(grid)
    return bool(parsed and parsed[2] != 1)


def _witness_height_not_three(grid: Any) -> bool:
    parsed = _valid_parsed(grid)
    return bool(parsed and parsed[0] // 2 != 3)


SEMANTIC_WITNESSES = {
    "non_left_layout": _witness_non_left_layout,
    "count_not_half": _witness_count_not_half,
    "color_not_one": _witness_color_not_one,
    "height_not_three": _witness_height_not_three,
}
WITNESS_RIVALS = {
    "non_left_layout": [
        "copy_input_then_grow",
        "rightmost_extent",
        "leading_run",
        "grow_each_marker",
    ],
    "count_not_half": ["half_width_start"],
    "color_not_one": ["color_one"],
    "height_not_three": ["three_rows"],
}


def _grids_equal(left: Any, right: Any) -> bool:
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def lesson_identifiable(demos, query) -> list[str]:
    """Name every wrong rule still consistent with all demonstrations."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(
                _grids_equal(rival(pair["input"]), pair["output"])
                for pair in demos
            ):
                relation = (
                    "and query"
                    if _grids_equal(rival(query["input"]), query["output"])
                    else "but disagrees on query"
                )
                reasons.append(f"competitor {name!r} fits every demo {relation}")
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
