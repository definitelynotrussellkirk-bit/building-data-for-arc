"""Generator for ARC task ``0c9aba6e``.

The input contains two equal panels separated by one full row of colour 7.
For each aligned cell, the output is 8 exactly when both panel cells are 0;
all other aligned relations map to 0.

Every generated scene contains all four aligned occupancy relations.  The
layout also guarantees that the both-zero cells are not a row-major prefix,
so a count-only placement rule cannot accidentally match a labelled pair.

Lessons use a six-slot cyclic schedule: two strict canonical anchors, two
same-foreground controls, and two distinct noncanonical controls.  Five
demonstrations plus one query cover a complete cycle.  Holding out any one
of the six pairs still leaves a same-foreground example (refuting "mark equal
cells") and a distinct noncanonical example (refuting a profile-gated
count-only shortcut).
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "76aff6297765"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "5b347fef0b78"  # normalized canonical program_solution
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.30

SCHEDULE_PROFILES = (
    "canonical_anchor_a",
    "same_foreground_a",
    "distinct_broad_a",
    "canonical_anchor_b",
    "same_foreground_b",
    "distinct_broad_b",
)

SUMMARY = (
    "Two equal zero-background panels are split by a full colour-7 row. "
    "Emit 8 exactly at aligned positions where both panels are zero; emit 0 "
    "for the other three joint cell relations."
)

INVARIANTS = [
    "the grid is rectangular, 7..17 rows by 3..8 columns, with ARC colours",
    "exactly one full colour-7 separator row lies at the vertical centre",
    "the top and bottom panels have equal dimensions and contain no 7 or 8",
    "each panel uses zero plus exactly one foreground colour",
    "each panel contains at least one zero and at least one foreground cell",
    "ordinary generated scenes exhibit all four aligned zero/foreground states",
]

AXES = {
    "panel_h": {
        "type": "int",
        "default": "difficulty-aware draw over 3..8; canonical schedule slots anchor at 6",
        "valid": "3..8",
    },
    "panel_w": {
        "type": "int",
        "default": "difficulty-aware draw over 3..8; canonical schedule slots anchor at 4",
        "valid": "3..8",
    },
    "top_color": {
        "type": "color",
        "default": "six-slot lesson schedule; canonical anchors use 2",
        "valid": "1..9 (≠7, ≠8)",
    },
    "bot_color": {
        "type": "color",
        "default": "six-slot lesson schedule; canonical anchors use 6",
        "valid": "1..9 (≠7, ≠8)",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

# Counts are ordered as: both zero, top zero only, bottom zero only, both fg.
_CANONICAL_JOINT_COUNTS = (
    (9, 5, 3, 7),
    (6, 4, 9, 5),
    (7, 7, 5, 5),
    (8, 4, 3, 9),
    (7, 6, 4, 7),
)
_STATE_BOTH_ZERO = 0
_STATE_TOP_ZERO = 1
_STATE_BOTTOM_ZERO = 2
_STATE_BOTH_FOREGROUND = 3


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic six-slot curriculum profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid is empty or not a list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["first row is empty or not a list"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid is ragged or contains a non-list row"]

    errors: list[str] = []
    for row in grid:
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("grid contains a non-integer or colour outside 0..9")
                return errors
    return errors


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _shape_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    separator_rows = [
        row
        for row in range(height)
        if all(grid[row][col] == 7 for col in range(width))
    ]
    if len(separator_rows) != 1:
        errors.append(
            f"expected exactly one full colour-7 separator row, found {len(separator_rows)}"
        )
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "separator_rows": separator_rows,
        }

    separator = separator_rows[0]
    panel_h = separator
    bottom_h = height - separator - 1
    if panel_h != bottom_h:
        errors.append(f"panels have unequal heights: top={panel_h}, bottom={bottom_h}")
    if separator != height // 2:
        errors.append("separator row is not vertically centred")

    top = [row[:] for row in grid[:separator]]
    bottom = [row[:] for row in grid[separator + 1 :]]
    if any(value in {7, 8} for panel in (top, bottom) for row in panel for value in row):
        errors.append("panel cells may not use separator colour 7 or output marker 8")

    top_colours = sorted({value for row in top for value in row if value != 0})
    bottom_colours = sorted({value for row in bottom for value in row if value != 0})
    if len(top_colours) != 1:
        errors.append(
            f"top panel must use exactly one non-zero foreground colour, found {top_colours}"
        )
    if len(bottom_colours) != 1:
        errors.append(
            "bottom panel must use exactly one non-zero foreground colour, "
            f"found {bottom_colours}"
        )

    top_zero = sum(value == 0 for row in top for value in row)
    bottom_zero = sum(value == 0 for row in bottom for value in row)
    area = panel_h * width if panel_h > 0 else 0
    if area and top_zero in {0, area}:
        errors.append("top panel must contain both zero and foreground cells")
    if area and bottom_zero in {0, area}:
        errors.append("bottom panel must contain both zero and foreground cells")

    joint_counts = {
        "both_zero": 0,
        "top_zero_only": 0,
        "bottom_zero_only": 0,
        "both_foreground": 0,
    }
    if panel_h == bottom_h and panel_h > 0:
        for row in range(panel_h):
            for col in range(width):
                top_is_zero = top[row][col] == 0
                bottom_is_zero = bottom[row][col] == 0
                if top_is_zero and bottom_is_zero:
                    joint_counts["both_zero"] += 1
                elif top_is_zero:
                    joint_counts["top_zero_only"] += 1
                elif bottom_is_zero:
                    joint_counts["bottom_zero_only"] += 1
                else:
                    joint_counts["both_foreground"] += 1

    return {
        "errors": errors,
        "grid": [row[:] for row in grid],
        "height": height,
        "width": width,
        "separator": separator,
        "panel_h": panel_h,
        "panel_w": width,
        "top": top,
        "bottom": bottom,
        "top_color": top_colours[0] if len(top_colours) == 1 else None,
        "bot_color": bottom_colours[0] if len(bottom_colours) == 1 else None,
        "joint_counts": joint_counts,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-aligned input grammar and exact override claims."""
    del difficulty
    info = _analysis(grid)
    errors = list(info.get("errors", []))
    if errors:
        return errors

    panel_h, panel_w = info["panel_h"], info["panel_w"]
    if not 3 <= panel_h <= 8:
        errors.append(f"panel height {panel_h} outside teaching range 3..8")
    if not 3 <= panel_w <= 8:
        errors.append(f"panel width {panel_w} outside teaching range 3..8")

    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = meta
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in AXES and observed.get(axis) != value:
                errors.append(
                    f"{axis} requested {value!r}, observed {observed.get(axis)!r}"
                )
    return errors


def _weighted_state(rng, weights: tuple[float, float, float, float]) -> int:
    threshold = rng.random() * sum(weights)
    running = 0.0
    for state, weight in enumerate(weights):
        running += weight
        if threshold < running:
            return state
    return _STATE_BOTH_FOREGROUND


def _broad_joint_counts(area: int, sample_index: int, rng) -> tuple[int, int, int, int]:
    """Return variable overlap counts while guaranteeing all four relations."""
    profiles = (
        (0.12, 0.30, 0.30, 0.28),
        (0.30, 0.25, 0.25, 0.20),
        (0.52, 0.16, 0.16, 0.16),
    )
    weights = profiles[sample_index % len(profiles)]
    states = [
        _STATE_BOTH_ZERO,
        _STATE_TOP_ZERO,
        _STATE_BOTTOM_ZERO,
        _STATE_BOTH_FOREGROUND,
    ]
    states.extend(_weighted_state(rng, weights) for _ in range(area - 4))
    counts = tuple(states.count(state) for state in range(4))
    return counts  # type: ignore[return-value]


def _render_joint_states(
    panel_h: int,
    panel_w: int,
    top_color: int,
    bot_color: int,
    counts: tuple[int, int, int, int],
    rng,
) -> list[list[int]]:
    states: list[int] = []
    for state, count in enumerate(counts):
        states.extend([state] * count)
    if len(states) != panel_h * panel_w:
        raise AssertionError("joint-state count does not match panel area")
    rng.shuffle(states)

    # A row-major count-only rival emits 8 in the first ``both_zero`` cells.
    # Preserve all relation counts while making that placement observably wrong.
    both_zero_count = counts[_STATE_BOTH_ZERO]
    both_zero_positions = [
        index for index, state in enumerate(states) if state == _STATE_BOTH_ZERO
    ]
    if both_zero_positions == list(range(both_zero_count)):
        if not 0 < both_zero_count < len(states):
            raise AssertionError("all-four-state contract leaves no swap position")
        states[both_zero_count - 1], states[both_zero_count] = (
            states[both_zero_count],
            states[both_zero_count - 1],
        )

    grid = full_grid(panel_h * 2 + 1, panel_w, 0)
    for col in range(panel_w):
        grid[panel_h][col] = 7
    for index, state in enumerate(states):
        row, col = divmod(index, panel_w)
        if state == _STATE_BOTH_ZERO:
            top_value, bottom_value = 0, 0
        elif state == _STATE_TOP_ZERO:
            top_value, bottom_value = 0, bot_color
        elif state == _STATE_BOTTOM_ZERO:
            top_value, bottom_value = top_color, 0
        else:
            top_value, bottom_value = top_color, bot_color
        grid[row][col] = top_value
        grid[panel_h + 1 + row][col] = bottom_value
    return grid


def _draw_scheduled_colors(ctx, overrides: dict[str, Any], profile: str) -> tuple[int, int]:
    legal = tuple(colour for colour in range(1, 10) if colour not in {7, 8})
    top_overridden = overrides.get("top_color") is not None
    bot_overridden = overrides.get("bot_color") is not None

    if profile.startswith("canonical_anchor"):
        top_color = (
            ctx.draw_color("top_color", exclude={0, 7, 8})
            if top_overridden
            else ctx.draw_choice("top_color", (2,))
        )
        bot_color = (
            ctx.draw_color("bot_color", exclude={0, 7, 8})
            if bot_overridden
            else ctx.draw_choice("bot_color", (6,))
        )
        return int(top_color), int(bot_color)

    if profile.startswith("same_foreground"):
        if top_overridden and bot_overridden:
            return (
                int(ctx.draw_color("top_color", exclude={0, 7, 8})),
                int(ctx.draw_color("bot_color", exclude={0, 7, 8})),
            )
        if bot_overridden:
            bot_color = int(ctx.draw_color("bot_color", exclude={0, 7, 8}))
            top_color = int(ctx.draw_choice("top_color", (bot_color,)))
            return top_color, bot_color
        top_color = int(ctx.draw_color("top_color", exclude={0, 7, 8}))
        bot_color = (
            int(ctx.draw_color("bot_color", exclude={0, 7, 8}))
            if bot_overridden
            else int(ctx.draw_choice("bot_color", (top_color,)))
        )
        return top_color, bot_color

    if not profile.startswith("distinct_broad"):
        raise ValueError(f"unknown schedule profile {profile!r}")

    if top_overridden and bot_overridden:
        return (
            int(ctx.draw_color("top_color", exclude={0, 7, 8})),
            int(ctx.draw_color("bot_color", exclude={0, 7, 8})),
        )
    if bot_overridden:
        bot_color = int(ctx.draw_color("bot_color", exclude={0, 7, 8}))
        choices = [colour for colour in legal if colour != bot_color]
        if bot_color == 6:
            choices = [colour for colour in choices if colour != 2]
        top_color = int(ctx.draw_choice("top_color", choices))
        return top_color, bot_color

    top_color = int(ctx.draw_color("top_color", exclude={0, 7, 8}))
    choices = [colour for colour in legal if colour != top_color]
    if top_color == 2:
        choices = [colour for colour in choices if colour != 6]
    bot_color = (
        int(ctx.draw_color("bot_color", exclude={0, 7, 8}))
        if bot_overridden
        else int(ctx.draw_choice("bot_color", choices))
    )
    return top_color, bot_color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {unknown[0]}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    canonical_anchor = profile.startswith("canonical_anchor")

    if "panel_h" in overrides:
        panel_h = ctx.draw_int("panel_h", 3, 8)
    elif canonical_anchor:
        panel_h = ctx.draw_choice("panel_h", (6,))
    else:
        panel_h = ctx.draw_int_diff("panel_h", 3, 8)

    if "panel_w" in overrides:
        panel_w = ctx.draw_int("panel_w", 3, 8)
    elif canonical_anchor:
        panel_w = ctx.draw_choice("panel_w", (4,))
    else:
        panel_w = ctx.draw_int_diff("panel_w", 3, 8)

    top_color, bot_color = _draw_scheduled_colors(ctx, overrides, profile)

    layout_rng = ctx.draw_rng("joint_layout")
    if (
        canonical_anchor
        and panel_h == 6
        and panel_w == 4
        and top_color == 2
        and bot_color == 6
    ):
        anchor_offset = 0 if profile.endswith("_a") else 1
        cycle = int(sample_index) // len(SCHEDULE_PROFILES)
        counts = _CANONICAL_JOINT_COUNTS[
            (2 * cycle + anchor_offset) % len(_CANONICAL_JOINT_COUNTS)
        ]
    else:
        counts = _broad_joint_counts(panel_h * panel_w, sample_index, layout_rng)

    grid = _render_joint_states(
        panel_h,
        panel_w,
        top_color,
        bot_color,
        counts,
        layout_rng,
    )
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": ctx.overrides_used()},
    )
    if errors:
        raise AssertionError("generator constructed invalid grid: " + "; ".join(errors))

    info = _analysis(grid)
    missing_states = [
        name for name, count in info["joint_counts"].items() if count == 0
    ]
    if missing_states:
        raise AssertionError(
            "generator omitted decisive aligned relation(s): " + ", ".join(missing_states)
        )
    if _rival_count_only_row_major(grid) == rule_mirror(grid):
        raise AssertionError("row-major count-only shortcut survived generated layout")

    if not overrides:
        if canonical_anchor and strict_canonical_like(grid):
            raise AssertionError("canonical schedule slot missed the strict profile")
        if profile.startswith("same_foreground") and top_color != bot_color:
            raise AssertionError("same-foreground schedule slot used distinct colours")
        if profile.startswith("distinct_broad"):
            if top_color == bot_color:
                raise AssertionError("distinct schedule slot used equal colours")
            if strict_canonical_like(grid) == []:
                raise AssertionError("distinct broad schedule slot collapsed to canonical")
    return grid

def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned grid."""
    info = _analysis(grid)
    if info.get("errors"):
        raise ValueError("cannot observe malformed grid: " + "; ".join(info["errors"]))
    return {
        "panel_h": info["panel_h"],
        "panel_w": info["panel_w"],
        "top_color": info["top_color"],
        "bot_color": info["bot_color"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked geometry, palette, and joint-state envelope."""
    info = _analysis(grid)
    errors = list(info.get("errors", []))
    if errors:
        return errors

    reasons: list[str] = []
    if (info["panel_h"], info["panel_w"]) != (6, 4):
        reasons.append("canonical panels are 6x4")
    if info["top_color"] != 2 or info["bot_color"] != 6:
        reasons.append("canonical top and bottom foreground colours are 2 and 6")

    counts = info["joint_counts"]
    ranges = {
        "both_zero": (6, 9),
        "top_zero_only": (3, 7),
        "bottom_zero_only": (3, 9),
        "both_foreground": (5, 9),
    }
    for name, (low, high) in ranges.items():
        if not low <= counts[name] <= high:
            reasons.append(
                f"canonical {name} count is {low}..{high}, got {counts[name]}"
            )
    return reasons


def rule_mirror(grid) -> list[list[int]]:
    """Diagnostic mirror; canonical Racket remains the output authority."""
    info = _analysis(grid)
    if info.get("errors"):
        raise ValueError("invalid task grid: " + "; ".join(info["errors"]))
    return [
        [
            8 if info["top"][row][col] == 0 and info["bottom"][row][col] == 0 else 0
            for col in range(info["panel_w"])
        ]
        for row in range(info["panel_h"])
    ]


def _rival_top_zero_only(grid):
    info = _analysis(grid)
    return [
        [8 if info["top"][row][col] == 0 else 0 for col in range(info["panel_w"])]
        for row in range(info["panel_h"])
    ]


def _rival_bottom_zero_only(grid):
    info = _analysis(grid)
    return [
        [8 if info["bottom"][row][col] == 0 else 0 for col in range(info["panel_w"])]
        for row in range(info["panel_h"])
    ]


def _rival_either_zero(grid):
    info = _analysis(grid)
    return [
        [
            8 if info["top"][row][col] == 0 or info["bottom"][row][col] == 0 else 0
            for col in range(info["panel_w"])
        ]
        for row in range(info["panel_h"])
    ]


def _rival_both_foreground(grid):
    info = _analysis(grid)
    return [
        [
            8 if info["top"][row][col] != 0 and info["bottom"][row][col] != 0 else 0
            for col in range(info["panel_w"])
        ]
        for row in range(info["panel_h"])
    ]


def _rival_equal_cells(grid):
    info = _analysis(grid)
    return [
        [
            8 if info["top"][row][col] == info["bottom"][row][col] else 0
            for col in range(info["panel_w"])
        ]
        for row in range(info["panel_h"])
    ]


def _rival_count_only_row_major(grid):
    info = _analysis(grid)
    count = info["joint_counts"]["both_zero"]
    return [
        [8 if row * info["panel_w"] + col < count else 0 for col in range(info["panel_w"])]
        for row in range(info["panel_h"])
    ]


def _rival_profile_gated_count_only(grid):
    """A curriculum-aware shortcut that exposed the prior four-slot schedule."""
    info = _analysis(grid)
    if strict_canonical_like(grid) == [] or info["top_color"] == info["bot_color"]:
        return rule_mirror(grid)
    return _rival_count_only_row_major(grid)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "top_zero_only": _rival_top_zero_only,
    "bottom_zero_only": _rival_bottom_zero_only,
    "either_zero": _rival_either_zero,
    "both_foreground": _rival_both_foreground,
    "equal_cells": _rival_equal_cells,
    "count_only_row_major": _rival_count_only_row_major,
    "profile_gated_count_only": _rival_profile_gated_count_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "equal_cells": _rival_equal_cells,
    "profile_gated_count_only": _rival_profile_gated_count_only,
}


def _valid_info(grid):
    info = _analysis(grid)
    return None if info.get("errors") else info


def _has_joint_state(grid, name: str) -> bool:
    info = _valid_info(grid)
    return info is not None and info["joint_counts"][name] > 0


def _same_foreground(grid) -> bool:
    info = _valid_info(grid)
    return (
        info is not None
        and info["top_color"] == info["bot_color"]
        and info["joint_counts"]["both_foreground"] > 0
    )


def _refutes_count_only(grid) -> bool:
    info = _valid_info(grid)
    return info is not None and _rival_count_only_row_major(grid) != rule_mirror(grid)


def _distinct_noncanonical_refutes_profile_gate(grid) -> bool:
    info = _valid_info(grid)
    return (
        info is not None
        and info["top_color"] != info["bot_color"]
        and strict_canonical_like(grid) != []
        and _rival_profile_gated_count_only(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES = {
    "both_zero_maps_to_8": lambda grid: _has_joint_state(grid, "both_zero"),
    "top_zero_bottom_foreground_stays_0": lambda grid: _has_joint_state(
        grid, "top_zero_only"
    ),
    "top_foreground_bottom_zero_stays_0": lambda grid: _has_joint_state(
        grid, "bottom_zero_only"
    ),
    "both_foreground_stays_0": lambda grid: _has_joint_state(
        grid, "both_foreground"
    ),
    "same_foreground_refutes_equality": _same_foreground,
    "row_major_layout_refutes_count_only": _refutes_count_only,
    "distinct_noncanonical_refutes_profile_gate": _distinct_noncanonical_refutes_profile_gate,
}

WITNESS_RIVALS = {
    "both_zero_maps_to_8": ["both_foreground"],
    "top_zero_bottom_foreground_stays_0": ["top_zero_only", "either_zero"],
    "top_foreground_bottom_zero_stays_0": ["bottom_zero_only", "either_zero"],
    "both_foreground_stays_0": ["both_foreground"],
    "same_foreground_refutes_equality": ["equal_cells", "both_foreground"],
    "row_major_layout_refutes_count_only": ["count_only_row_major"],
    "distinct_noncanonical_refutes_profile_gate": ["profile_gated_count_only"],
}


def _coerce_grid(value: Any) -> list[list[int]]:
    if not isinstance(value, list):
        raise ValueError("grid value is not a list")
    return [[int(cell) for cell in row] for row in value]


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible rival survives the demos."""
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} is not an input/output pair")
            continue
        structural = self_check(pair["input"])
        if structural:
            reasons.append(f"{label} input violates task grammar: {structural[0]}")
            continue
        if rule_mirror(pair["input"]) != _coerce_grid(pair["output"]):
            reasons.append(f"{label} output disagrees with the double-zero rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == _coerce_grid(demo["output"])
            for demo in demos
        )
        if survives and competitor(query["input"]) != _coerce_grid(query["output"]):
            reasons.append(
                f"competing rule {name!r} fits every demo but answers the query differently"
            )
    return reasons
