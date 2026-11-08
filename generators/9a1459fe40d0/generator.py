"""Semantic generator for ARC task 9a1459fe40d0 (Folded XOR Mask).

A full-height cyan bar separates equal-width halves.  Compare occupancy at
mirror-related cells across that bar.  The authoritative output is a fresh
zero grid with orange only at the RIGHT-HALF position of every occupancy XOR.
Input colors are payload only: matched cells of different colors still produce
zero, which rules out the raw-value-inequality shortcut left open by the three
canonical examples.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "9a1459fe40d0"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
# sha256[:12] of the whitespace-normalized selected canonical Racket rule.
RULE_HASH = "1ed249363e20"

SUMMARY = (
    "A full-height cyan(8) bar separates equal-width halves. For every left "
    "cell, compare whether it and its reflected right-half partner are "
    "occupied (nonzero). Return a fresh all-zero grid and paint orange(7) "
    "only at the reflected RIGHT-HALF position when exactly one side is "
    "occupied. The input bar and source colors are not copied to the output."
)

INVARIANTS = [
    "background is literal color 0",
    "the odd-width grid has one full-height cyan(8) center bar and equal halves",
    "colors 7 and 8 never appear as payload cells outside the center bar",
    "both left-only and right-only occupancy mismatches are present",
    "at least one mirrored pair is occupied on both sides and must output black",
    "generated scenes include a different-colored matched pair, so raw value inequality is not the rule",
    "the output is a same-size right-half-only orange mismatch mask on a zero canvas",
]

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

# Every profile has unique (height, width), making the one declared exact axis
# fully observable.  The first three profiles exactly anchor the three public
# canonical (height, width, palette-size) signatures.  All profiles still
# contain both XOR directions and matched controls, so every individual lesson
# is semantically useful rather than relying on aggregate schedule coverage.
PROFILE_SPECS: dict[str, tuple[int, int, int, int]] = {
    # name: (height, width, payload_color_count, mismatch_pairs_per_direction)
    "canonical_6x11": (6, 11, 2, 2),
    "canonical_7x11": (7, 11, 2, 3),
    "canonical_7x13": (7, 13, 2, 3),
    "compact_5x9": (5, 9, 3, 2),
    "wide_6x15": (6, 15, 3, 3),
    "tall_8x11": (8, 11, 3, 3),
    "balanced_8x13": (8, 13, 4, 4),
    "wide_9x15": (9, 15, 4, 4),
    "tall_10x9": (10, 9, 3, 3),
    "large_10x13": (10, 13, 4, 5),
    "large_11x15": (11, 15, 4, 5),
    "maximal_12x15": (12, 15, 4, 6),
}
SCENE_PROFILES = tuple(PROFILE_SPECS)
SCHEDULE_PROFILES = SCENE_PROFILES
_DIMS_TO_PROFILE = {
    (height, width): name
    for name, (height, width, _colors, _mismatches) in PROFILE_SPECS.items()
}
if len(_DIMS_TO_PROFILE) != len(PROFILE_SPECS):
    raise AssertionError("scene profiles must have unique dimensions")

AXES = {
    "scene_profile": {
        "type": "enum",
        "default": "deterministic twelve-profile sample-index cycle with a difficulty offset",
        "valid": "canonical_6x11|canonical_7x11|canonical_7x13|compact_5x9|wide_6x15|tall_8x11|balanced_8x13|wide_9x15|tall_10x9|large_10x13|large_11x15|maximal_12x15",
    }
}

_SOURCE_COLORS = (1, 2, 3, 4, 5, 6, 9)
_DIFFICULTY_OFFSETS = {"easy": 0, "medium": 4, "hard": 8}


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _DIFFICULTY_OFFSETS:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    return str(difficulty)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        profile = overrides["scene_profile"]
        if profile not in PROFILE_SPECS:
            raise ValueError(
                f"override scene_profile must be one of {SCENE_PROFILES}, got {profile!r}"
            )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the exact profile selected by the deterministic curriculum."""
    del seed
    band = _band(difficulty)
    offset = _DIFFICULTY_OFFSETS[band]
    return SCENE_PROFILES[(int(sample_index) + offset) % len(SCENE_PROFILES)]


def _scheduled_profile(ctx, sample_index: int) -> str:
    if ctx.overrides.get("scene_profile") is not None:
        return ctx.draw_choice("scene_profile", SCENE_PROFILES)
    selected = schedule_profile(ctx.seed, sample_index, ctx.difficulty)
    return ctx.draw_choice("scene_profile", (selected,))


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return [f"grid dimensions must lie in 1..30, got {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["grid cells must be literal ARC integers 0..9"]
    return []


def _analyze(grid: Sequence[Sequence[int]]) -> tuple[dict[str, Any], list[str]]:
    errors = _grid_errors(grid)
    if errors:
        return {}, errors

    height, width = len(grid), len(grid[0])
    if width % 2 == 0 or width < 7:
        return {}, [f"width {width} must be odd and at least 7"]
    bar_col = width // 2

    if not all(grid[row][bar_col] == 8 for row in range(height)):
        errors.append(f"column {bar_col} must be a full-height cyan(8) bar")
    stray_eights = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if col != bar_col and grid[row][col] == 8
    ]
    if stray_eights:
        errors.append(f"cyan(8) payload appears outside the center bar at {stray_eights[:3]}")

    stray_orange = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 7
    ]
    if stray_orange:
        errors.append(f"orange(7) is reserved for the output marker, found at {stray_orange[:3]}")

    left_only: list[tuple[int, int, int]] = []
    right_only: list[tuple[int, int, int]] = []
    both_same: list[tuple[int, int, int]] = []
    both_different: list[tuple[int, int, int, int]] = []
    both_empty = 0
    for row in range(height):
        for col in range(bar_col):
            mirror_col = 2 * bar_col - col
            left = grid[row][col]
            right = grid[row][mirror_col]
            if left and right:
                if left == right:
                    both_same.append((row, col, left))
                else:
                    both_different.append((row, col, left, right))
            elif left:
                left_only.append((row, col, left))
            elif right:
                right_only.append((row, col, right))
            else:
                both_empty += 1

    if not left_only:
        errors.append("at least one left-only occupied mirror pair is required")
    if not right_only:
        errors.append("at least one right-only occupied mirror pair is required")
    if not (both_same or both_different):
        errors.append("at least one doubly occupied matched pair is required")

    facts = {
        "height": height,
        "width": width,
        "bar_col": bar_col,
        "profile": _DIMS_TO_PROFILE.get((height, width)),
        "left_only": tuple(left_only),
        "right_only": tuple(right_only),
        "both_same": tuple(both_same),
        "both_different": tuple(both_different),
        "both_empty": both_empty,
        "payload_colors": frozenset(
            value
            for row in grid
            for value in row
            if value not in (0, 8)
        ),
    }
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, no-op, or branch-hiding folded-XOR scenes."""
    del difficulty
    facts, errors = _analyze(grid)
    if errors:
        return errors
    requested = ((meta or {}).get("overrides") or {}).get("scene_profile")
    if requested is not None and facts["profile"] != requested:
        errors.append(
            f"scene profile drifted from {requested!r} to {facts['profile']!r}"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the complete lawful occupancy-XOR input grammar."""
    return list(self_check(grid))


def observe_overrides(grid) -> dict[str, str | None]:
    facts, errors = _analyze(grid)
    if errors:
        return {"scene_profile": None}
    return {"scene_profile": facts["profile"]}


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains output authority."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = full_grid(facts["height"], facts["width"], 0)
    bar_col = facts["bar_col"]
    for row in range(facts["height"]):
        for col in range(bar_col):
            mirror_col = 2 * bar_col - col
            left = grid[row][col] != 0
            right = grid[row][mirror_col] != 0
            if left != right:
                output[row][mirror_col] = 7
    return output


def _payload_palette(rng, count: int) -> tuple[int, ...]:
    return tuple(rng.sample(list(_SOURCE_COLORS), count))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = _scheduled_profile(ctx, sample_index)
    height, width, color_count, mismatch_each = PROFILE_SPECS[profile]
    bar_col = width // 2

    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][bar_col] = 8

    positions = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(bar_col)
    ]
    # Every profile has enough interior support for both mismatch directions,
    # one same-color match, and one different-color match.
    needed = 2 * mismatch_each + 2
    if len(positions) < needed:
        raise RuntimeError(f"profile {profile} has only {len(positions)} slots for {needed} controls")
    layout_rng = ctx.draw_rng("layout")
    layout_rng.shuffle(positions)
    selected = positions[:needed]

    palette = _payload_palette(ctx.draw_rng("palette"), color_count)
    color_rng = ctx.draw_rng("colors")

    cursor = 0
    for _ in range(mismatch_each):
        row, col = selected[cursor]
        cursor += 1
        grid[row][col] = color_rng.choice(palette)
    for _ in range(mismatch_each):
        row, col = selected[cursor]
        cursor += 1
        mirror_col = 2 * bar_col - col
        grid[row][mirror_col] = color_rng.choice(palette)

    row, col = selected[cursor]
    cursor += 1
    mirror_col = 2 * bar_col - col
    same_color = color_rng.choice(palette)
    grid[row][col] = same_color
    grid[row][mirror_col] = same_color

    row, col = selected[cursor]
    mirror_col = 2 * bar_col - col
    left_color, right_color = color_rng.sample(list(palette), 2)
    grid[row][col] = left_color
    grid[row][mirror_col] = right_color

    errors = self_check(grid, meta={"overrides": ctx.overrides_used()})
    if errors:
        raise RuntimeError("generated invalid folded-XOR scene: " + "; ".join(errors))
    return grid


# ---------------------------------------------------------------------------
# Task-linked semantic contract and shortcut rivals
# ---------------------------------------------------------------------------

def _blank_like(grid):
    return full_grid(len(grid), len(grid[0]), 0)


def _identity(grid):
    return [list(row) for row in grid]


def _mark_both_sides(grid):
    facts, errors = _analyze(grid)
    if errors:
        return _identity(grid)
    output = _blank_like(grid)
    b = facts["bar_col"]
    for row in range(facts["height"]):
        for col in range(b):
            mc = 2 * b - col
            if (grid[row][col] != 0) != (grid[row][mc] != 0):
                output[row][col] = 7
                output[row][mc] = 7
    return output


def _mark_left_only(grid):
    facts, errors = _analyze(grid)
    if errors:
        return _identity(grid)
    output = _blank_like(grid)
    b = facts["bar_col"]
    for row in range(facts["height"]):
        for col in range(b):
            mc = 2 * b - col
            if grid[row][col] != 0 and grid[row][mc] == 0:
                output[row][mc] = 7
    return output


def _mark_right_only(grid):
    facts, errors = _analyze(grid)
    if errors:
        return _identity(grid)
    output = _blank_like(grid)
    b = facts["bar_col"]
    for row in range(facts["height"]):
        for col in range(b):
            mc = 2 * b - col
            if grid[row][col] == 0 and grid[row][mc] != 0:
                output[row][mc] = 7
    return output


def _mark_union(grid):
    facts, errors = _analyze(grid)
    if errors:
        return _identity(grid)
    output = _blank_like(grid)
    b = facts["bar_col"]
    for row in range(facts["height"]):
        for col in range(b):
            mc = 2 * b - col
            if grid[row][col] != 0 or grid[row][mc] != 0:
                output[row][mc] = 7
    return output


def _mark_intersection(grid):
    facts, errors = _analyze(grid)
    if errors:
        return _identity(grid)
    output = _blank_like(grid)
    b = facts["bar_col"]
    for row in range(facts["height"]):
        for col in range(b):
            mc = 2 * b - col
            if grid[row][col] != 0 and grid[row][mc] != 0:
                output[row][mc] = 7
    return output


def _raw_value_inequality(grid):
    """Canonical-fitting shortcut: compare literal colors, not occupancy."""
    facts, errors = _analyze(grid)
    if errors:
        return _identity(grid)
    output = _blank_like(grid)
    b = facts["bar_col"]
    for row in range(facts["height"]):
        for col in range(b):
            mc = 2 * b - col
            if grid[row][col] != grid[row][mc]:
                output[row][mc] = 7
    return output


def _preserve_scene_and_mark(grid):
    output = _identity(grid)
    mask = rule_mirror(grid)
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if mask[row][col] == 7:
                output[row][col] = 7
    return output


def _echo_input_orange(grid):
    output = _blank_like(grid)
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 7:
                output[row][col] = 7
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], list[list[int]]]] = {
    "identity": _identity,
    "mark_both_sides": _mark_both_sides,
    "left_only_reflected": _mark_left_only,
    "right_only_existing": _mark_right_only,
    "right_union": _mark_union,
    "right_intersection": _mark_intersection,
    "raw_value_inequality": _raw_value_inequality,
    "preserve_scene_and_mark": _preserve_scene_and_mark,
    "echo_input_orange": _echo_input_orange,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {"raw_value_inequality": _raw_value_inequality}


def _has_left_only(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and bool(facts["left_only"])


def _has_right_only(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and bool(facts["right_only"])


def _has_matched_pair(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and bool(facts["both_same"] or facts["both_different"])


def _has_same_color_match(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and bool(facts["both_same"])


def _has_different_color_match(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and bool(facts["both_different"])


def _has_nonempty_xor_and_no_input_orange(grid) -> bool:
    facts, errors = _analyze(grid)
    return (
        not errors
        and bool(facts["left_only"] or facts["right_only"])
        and 7 not in facts["payload_colors"]
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Sequence[Sequence[int]]], bool]] = {
    "left_only_mismatch": _has_left_only,
    "right_only_mismatch": _has_right_only,
    "matched_occupied_control": _has_matched_pair,
    "same_color_matched_control": _has_same_color_match,
    "different_color_matched_control": _has_different_color_match,
    "right_half_mask_not_input_echo": _has_nonempty_xor_and_no_input_orange,
}
WITNESS_RIVALS = {
    "left_only_mismatch": ["right_only_existing"],
    "right_only_mismatch": ["left_only_reflected"],
    "matched_occupied_control": ["right_union"],
    "same_color_matched_control": ["right_intersection"],
    "different_color_matched_control": ["raw_value_inequality"],
    "right_half_mask_not_input_echo": [
        "identity",
        "mark_both_sides",
        "preserve_scene_and_mark",
        "echo_input_orange",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible shortcut survives its demos."""
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(
                    f"competitor {name!r} fits every demonstration but changes the query"
                )
    return reasons
