"""Canonical input sampler for ARC task 87ab05b8 / 637229802e6f.

Exactly one red (2) marker selects one of the four 2x2 quadrants of a
4x4 grid.  The authoritative output fills that quadrant with red and every
other cell with magenta (6).  Non-{2,6} input cells are answer-irrelevant
clutter; the sampler preserves the four decoration profiles present in the
canonical corpus while varying positions and colors.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "637229802e6f"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "315e7341b297"
EXPECTED_OUTPUT_CODOMAIN = 4  # one 4x4 mask for each marker quadrant

SUMMARY = (
    "A 4x4 grid contains exactly one red (2) marker, magenta (6) background, "
    "and 3-7 non-{2,6} decorations.  Locate the red marker, identify its 2x2 "
    "quadrant, fill that quadrant red, and replace every other output cell "
    "with magenta.  Decoration positions, colors, and multiplicities are "
    "irrelevant to the answer."
)

INVARIANTS = [
    "the input is exactly 4x4",
    "there is exactly one color-2 marker",
    "all remaining cells are color 6 or non-{2,6} decorations",
    "the decoration (cell count, distinct-color count) is one of the four canonical profiles",
]

QUADRANTS = ("top_left", "top_right", "bottom_left", "bottom_right")
DECORATION_PROFILES = ("sparse3", "sparse4", "dense4", "dense6")
PROFILE_SPECS = {
    "sparse3": (3, 3),
    "sparse4": (4, 4),
    "dense4": (7, 4),
    "dense6": (7, 6),
}
_PROFILE_FROM_COUNTS = {value: name for name, value in PROFILE_SPECS.items()}
_DECORATION_COLORS = (0, 1, 3, 4, 5, 7, 8, 9)
_DIFFICULTY_OFFSETS = {None: 3, "easy": 0, "medium": 1, "hard": 2}

AXES = {
    "marker_quadrant": {
        "type": "str",
        "default": "four-step lesson schedule; seed-rotated",
        "valid": "|".join(QUADRANTS),
    },
    "marker_slot": {
        "type": "int",
        "default": "block-stable 0..3 local cell within the selected quadrant",
        "valid": "0..3",
    },
    "decoration_profile": {
        "type": "str",
        "default": "block-stable canonical profile, difficulty-offset",
        "valid": "|".join(DECORATION_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = QUADRANTS


def _has_override(overrides: dict[str, Any], name: str) -> bool:
    return name in overrides and overrides[name] is not None


def _validate_request(
    seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]
) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer (not bool)")
    if difficulty not in _DIFFICULTY_OFFSETS:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")

    if _has_override(overrides, "marker_quadrant"):
        value = overrides["marker_quadrant"]
        if type(value) is not str or value not in QUADRANTS:
            raise ValueError(f"marker_quadrant must be one of {QUADRANTS}, got {value!r}")
    if _has_override(overrides, "marker_slot"):
        value = overrides["marker_slot"]
        if type(value) is not int or not 0 <= value <= 3:
            raise ValueError("marker_slot must be an integer in 0..3 (not bool)")
    if _has_override(overrides, "decoration_profile"):
        value = overrides["decoration_profile"]
        if type(value) is not str or value not in DECORATION_PROFILES:
            raise ValueError(
                f"decoration_profile must be one of {DECORATION_PROFILES}, got {value!r}"
            )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the scheduled answer branch for the default lesson stream."""
    del difficulty
    return QUADRANTS[(int(seed) + int(sample_index)) % len(QUADRANTS)]


def _scheduled_decoration_profile(seed: int, sample_index: int, difficulty) -> str:
    # Keep the nuisance profile constant across each four-answer block.  This
    # makes the same clutter complexity accompany every quadrant, preventing a
    # palette/count shortcut from identifying the answer within a lesson.
    block = sample_index // LESSON_SCHEDULE_PERIOD
    offset = _DIFFICULTY_OFFSETS[difficulty]
    return DECORATION_PROFILES[(seed + block + offset) % len(DECORATION_PROFILES)]


def _scheduled_marker_slot(seed: int, sample_index: int, difficulty) -> int:
    # Likewise hold local marker position constant within a four-answer block.
    block = sample_index // LESSON_SCHEDULE_PERIOD
    offset = _DIFFICULTY_OFFSETS[difficulty]
    return (seed // 7 + block + offset) % 4


def _draw_choice_or_schedule(ctx, overrides, name, options, scheduled):
    if _has_override(overrides, name):
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (scheduled,))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic 4x4 input on the canonical grammar."""
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    quadrant = _draw_choice_or_schedule(
        ctx,
        overrides,
        "marker_quadrant",
        QUADRANTS,
        schedule_profile(seed, sample_index, difficulty),
    )
    if _has_override(overrides, "marker_slot"):
        marker_slot = ctx.draw_int_strict("marker_slot", 0, 3)
    else:
        scheduled_slot = _scheduled_marker_slot(seed, sample_index, difficulty)
        marker_slot = ctx.draw_int_strict("marker_slot", scheduled_slot, scheduled_slot)
    decoration_profile = _draw_choice_or_schedule(
        ctx,
        overrides,
        "decoration_profile",
        DECORATION_PROFILES,
        _scheduled_decoration_profile(seed, sample_index, difficulty),
    )

    marker_r, marker_c = _marker_from_axes(quadrant, marker_slot)
    n_decorations, n_colors = PROFILE_SPECS[decoration_profile]

    grid = full_grid(4, 4, 6)
    grid[marker_r][marker_c] = 2

    candidates = [
        (r, c)
        for r in range(4)
        for c in range(4)
        if (r, c) != (marker_r, marker_c)
    ]
    positions = ctx.draw_rng("decoration_positions").sample(candidates, n_decorations)
    palette = ctx.draw_rng("decoration_palette").sample(
        list(_DECORATION_COLORS), n_colors
    )
    values = list(palette)
    value_rng = ctx.draw_rng("decoration_values")
    values.extend(value_rng.choice(palette) for _ in range(n_decorations - n_colors))
    value_rng.shuffle(values)
    for (r, c), color in zip(positions, values):
        grid[r][c] = color
    return grid


def _marker_from_axes(quadrant: str, slot: int) -> tuple[int, int]:
    r0 = 0 if quadrant.startswith("top") else 2
    c0 = 0 if quadrant.endswith("left") else 2
    dr, dc = divmod(slot, 2)
    return r0 + dr, c0 + dc


def _grid_errors(grid: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or len(grid) != 4:
        return ["grid must contain exactly four rows"]
    if any(not isinstance(row, (list, tuple)) or len(row) != 4 for row in grid):
        return ["every row must contain exactly four cells"]

    flat = [value for row in grid for value in row]
    if any(type(value) is not int or not 0 <= value <= 9 for value in flat):
        errors.append("cells must be integer ARC colors 0..9 (not bool)")
    if errors:
        return errors

    marker_count = flat.count(2)
    if marker_count != 1:
        errors.append(f"expected exactly one color-2 marker, found {marker_count}")
    decorations = [value for value in flat if value not in (2, 6)]
    profile = (len(decorations), len(set(decorations)))
    if profile not in _PROFILE_FROM_COUNTS:
        errors.append(
            "decoration profile must be one of "
            f"{sorted(_PROFILE_FROM_COUNTS)}, got {profile}"
        )
    return errors


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the exact source-bound input grammar."""
    del difficulty, meta
    return _grid_errors(grid)


def strict_canonical_like(grid) -> list[str]:
    """All generated inputs and all four canonical inputs share this grammar."""
    return self_check(grid)


def _marker_position(grid) -> tuple[int, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2:
                return r, c
    raise ValueError("missing color-2 marker")


def _quadrant_of_grid(grid) -> str:
    r, c = _marker_position(grid)
    return ("top" if r < 2 else "bottom") + "_" + ("left" if c < 2 else "right")


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every advertised exact axis from returned pixels."""
    r, c = _marker_position(grid)
    quadrant = _quadrant_of_grid(grid)
    slot = (r % 2) * 2 + (c % 2)
    decorations = [value for row in grid for value in row if value not in (2, 6)]
    profile = _PROFILE_FROM_COUNTS[(len(decorations), len(set(decorations)))]
    return {
        "marker_quadrant": quadrant,
        "marker_slot": slot,
        "decoration_profile": profile,
    }


def _quadrant_output(quadrant: str) -> list[list[int]]:
    output = full_grid(4, 4, 6)
    r0 = 0 if quadrant.startswith("top") else 2
    c0 = 0 if quadrant.endswith("left") else 2
    for r in range(r0, r0 + 2):
        for c in range(c0, c0 + 2):
            output[r][c] = 2
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror used only for tests and semantic contracts."""
    return _quadrant_output(_quadrant_of_grid(grid))


def _always_top_left(_grid):
    return _quadrant_output("top_left")


def _always_top_right(_grid):
    return _quadrant_output("top_right")


def _always_bottom_left(_grid):
    return _quadrant_output("bottom_left")


def _always_bottom_right(_grid):
    return _quadrant_output("bottom_right")


def _row_half_only(grid):
    marker_r, _ = _marker_position(grid)
    output = full_grid(4, 4, 6)
    r0 = 0 if marker_r < 2 else 2
    for r in range(r0, r0 + 2):
        for c in range(4):
            output[r][c] = 2
    return output


def _column_half_only(grid):
    _, marker_c = _marker_position(grid)
    output = full_grid(4, 4, 6)
    c0 = 0 if marker_c < 2 else 2
    for r in range(4):
        for c in range(c0, c0 + 2):
            output[r][c] = 2
    return output


def _witness(quadrant: str) -> Callable[[Any], bool]:
    def predicate(grid) -> bool:
        try:
            return _quadrant_of_grid(grid) == quadrant
        except (TypeError, ValueError, IndexError):
            return False

    predicate.__name__ = f"witness_{quadrant}"
    return predicate


SEMANTIC_RIVALS = {
    "always_top_left": _always_top_left,
    "always_top_right": _always_top_right,
    "always_bottom_left": _always_bottom_left,
    "always_bottom_right": _always_bottom_right,
    "row_half_only": _row_half_only,
    "column_half_only": _column_half_only,
}
SEMANTIC_WITNESSES = {quadrant: _witness(quadrant) for quadrant in QUADRANTS}
WITNESS_RIVALS = {
    "top_left": ["always_top_right", "always_bottom_left", "always_bottom_right"],
    "top_right": ["always_top_left", "always_bottom_left", "always_bottom_right"],
    "bottom_left": ["always_top_left", "always_top_right", "always_bottom_right"],
    "bottom_right": ["always_top_left", "always_top_right", "always_bottom_left"],
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {}


def _check_pair(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    try:
        expected = rule_mirror(pair["input"])
    except (TypeError, ValueError, IndexError) as exc:
        return [f"{label} input is invalid: {type(exc).__name__}: {exc}"]
    if expected != pair["output"]:
        return [f"{label} output disagrees with the selected rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to expose both independent quadrant bits."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        reasons.extend(_check_pair(pair, f"demonstration {index}"))
    reasons.extend(_check_pair(query, "query"))
    if reasons:
        return reasons

    quadrants = {_quadrant_of_grid(pair["input"]) for pair in demos}
    rows = {quadrant.split("_")[0] for quadrant in quadrants}
    cols = {quadrant.split("_")[1] for quadrant in quadrants}
    if rows != {"top", "bottom"}:
        reasons.append("demonstrations do not distinguish top from bottom quadrants")
    if cols != {"left", "right"}:
        reasons.append("demonstrations do not distinguish left from right quadrants")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(pair["input"]) == pair["output"] for pair in demos):
                reasons.append(f"declared competitor {name} fits every demonstration")
        except Exception as exc:
            reasons.append(f"declared competitor {name} raised {type(exc).__name__}: {exc}")
    return reasons
