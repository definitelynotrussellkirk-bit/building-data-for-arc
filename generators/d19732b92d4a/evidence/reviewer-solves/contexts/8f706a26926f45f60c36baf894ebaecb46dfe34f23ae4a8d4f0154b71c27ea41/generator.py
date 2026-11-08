"""Generator for ``d19732b92d4a`` (fill length-3 diagonal midpoints).

The selected rule is local and simultaneous: whenever a zero cell has equal,
non-zero cells one step away on opposite corners of either diagonal, paint the
zero cell with that shared color.  Ordinary lessons follow a four-sample
schedule.  Two exact-canonical-profile anchors alternate with two scenes that
also contain axis-aligned, length-5 diagonal, and blocked-midpoint controls.
Every sliding three-demo lesson therefore contains a scene that refutes the
main plausible over-generalizations of the canonical examples.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d19732b92d4a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4a1befe9ed91"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.45

SUMMARY = (
    "A color-0 grid contains two or three same-color endpoint pairs on "
    "opposite corners of length-3 diagonals.  The output fills each blank "
    "midpoint with the endpoint color.  Scheduled control scenes additionally "
    "contain one axis-aligned distance-2 pair, one length-5 diagonal pair, and "
    "one length-3 diagonal whose midpoint is already occupied; those controls "
    "remain unchanged and distinguish the exact local rule from broader rivals."
)

INVARIANTS = [
    "background is color 0",
    "every ordinary draw contains two or three fillable length-3 diagonal pairs",
    "positive-pair colors are distinct and each positive midpoint is blank",
    "controls occur either as a complete axis/long-diagonal/blocked trio or not at all",
    "every declared axis is exactly recoverable from the returned input grid",
    "the canonical Racket program, not the Python mirror, is output authority",
]

_ORIENTATIONS = ("main", "anti", "both")
_CONTROL_PROFILES = ("none", "all")
_POSITION_PROFILES = ("interior", "border")
_CANONICAL_DIMS = {(6, 9), (7, 7), (8, 8)}

AXES = {
    "grid_h": {"type": "int", "default": "scheduled/band draw", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "scheduled/band draw", "valid": "7..14"},
    "pair_count": {"type": "int", "default": "scheduled 2..3", "valid": "2..3"},
    "orientation_profile": {
        "type": "enum",
        "default": "both",
        "valid": "main|anti|both",
    },
    "control_profile": {
        "type": "enum",
        "default": "scheduled none/all",
        "valid": "none|all",
    },
    "position_profile": {
        "type": "enum",
        "default": "scheduled interior/border",
        "valid": "interior|border",
    },
}

SCHEDULE_PROFILES = (
    "anchor_a",
    "controls_border",
    "anchor_b",
    "controls_interior",
)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "pair_count"):
        value = overrides.get(name)
        if value is not None and (type(value) is not int):
            raise ValueError(f"{name} must be an integer")
    for name in ("orientation_profile", "control_profile", "position_profile"):
        value = overrides.get(name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{name} must be a string")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % 4]


def _scheduled_defaults(ctx, difficulty: Any) -> dict[str, Any]:
    slot = int(ctx.sample_index) % 4
    rng = ctx.draw_rng("schedule")
    if slot in (0, 2):
        canonical = ((6, 9, 2), (7, 7, 2), (8, 8, 3))
        h, w, pair_count = canonical[rng.randrange(len(canonical))]
        return {
            "grid_h": h,
            "grid_w": w,
            "pair_count": pair_count,
            "orientation_profile": "both",
            "control_profile": "none",
            "position_profile": "interior",
        }

    if difficulty == "easy":
        h, w, pair_count = rng.randint(7, 9), rng.randint(7, 9), 2
    elif difficulty == "hard":
        h, w, pair_count = rng.randint(11, 14), rng.randint(11, 14), 3
    else:
        h, w, pair_count = rng.randint(8, 11), rng.randint(8, 11), rng.randint(2, 3)
    return {
        "grid_h": h,
        "grid_w": w,
        "pair_count": pair_count,
        "orientation_profile": "both",
        "control_profile": "all",
        "position_profile": "border" if slot == 1 else "interior",
    }


def _draw_int(ctx, overrides: dict[str, Any], name: str, default: int,
              valid: tuple[int, int]) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, valid[0], valid[1])
    return ctx.draw_int(name, default, default)


def _draw_choice(ctx, overrides: dict[str, Any], name: str, default: str,
                 options: tuple[str, ...]) -> str:
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _positive_candidates(h: int, w: int, orientation: str, position: str):
    dr, dc = (1, 1) if orientation == "main" else (1, -1)
    out = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            a = (r - dr, c - dc)
            b = (r + dr, c + dc)
            touches = any(rr in (0, h - 1) or cc in (0, w - 1) for rr, cc in (a, b))
            if position == "border" and not touches:
                continue
            if position == "interior" and touches:
                continue
            out.append((a, (r, c), b))
    return out


def _axis_candidates(h: int, w: int):
    out = []
    for r in range(h):
        for c in range(w - 2):
            out.append(((r, c), (r, c + 1), (r, c + 2)))
    for r in range(h - 2):
        for c in range(w):
            out.append(((r, c), (r + 1, c), (r + 2, c)))
    return out


def _long_diagonal_candidates(h: int, w: int):
    out = []
    for r in range(2, h - 2):
        for c in range(2, w - 2):
            out.append(((r - 2, c - 2), (r, c), (r + 2, c + 2)))
            out.append(((r - 2, c + 2), (r, c), (r + 2, c - 2)))
    return out


def _blocked_candidates(h: int, w: int):
    out = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            out.append(((r - 1, c - 1), (r, c), (r + 1, c + 1)))
            out.append(((r - 1, c + 1), (r, c), (r + 1, c - 1)))
    return out


def _orientation_sequence(pair_count: int, profile: str, rng) -> list[str]:
    if profile == "main":
        return ["main"] * pair_count
    if profile == "anti":
        return ["anti"] * pair_count
    rest = [rng.choice(("main", "anti")) for _ in range(pair_count - 2)]
    return ["main", "anti", *rest]


def _place_scene(
    h: int,
    w: int,
    pair_count: int,
    orientation_profile: str,
    control_profile: str,
    position_profile: str,
    colors: list[int],
    rng,
) -> list[list[int]]:
    orientations = _orientation_sequence(pair_count, orientation_profile, rng)
    specs: list[dict[str, Any]] = []
    color_index = 0

    if control_profile == "all":
        axis_color = colors[color_index]
        long_color = colors[color_index + 1]
        blocked_color = colors[color_index + 2]
        blocker_color = colors[color_index + 3]
        color_index += 4
        specs.extend([
            {
                "kind": "long",
                "candidates": _long_diagonal_candidates(h, w),
                "values": lambda cells, color=long_color: {
                    cells[0]: color, cells[2]: color
                },
            },
            {
                "kind": "axis",
                "candidates": _axis_candidates(h, w),
                "values": lambda cells, color=axis_color: {
                    cells[0]: color, cells[2]: color
                },
            },
            {
                "kind": "blocked",
                "candidates": _blocked_candidates(h, w),
                "values": lambda cells, color=blocked_color, blocker=blocker_color: {
                    cells[0]: color, cells[1]: blocker, cells[2]: color
                },
            },
        ])

    for index, orientation in enumerate(orientations):
        color = colors[color_index]
        color_index += 1
        required_position = position_profile if index == 0 else (
            "interior" if position_profile == "interior" else "any"
        )
        if required_position == "any":
            candidates = (
                _positive_candidates(h, w, orientation, "interior")
                + _positive_candidates(h, w, orientation, "border")
            )
        else:
            candidates = _positive_candidates(h, w, orientation, required_position)
        specs.append({
            "kind": f"positive_{index}",
            "candidates": candidates,
            "values": lambda cells, color=color: {cells[0]: color, cells[2]: color},
        })

    for spec in specs:
        rng.shuffle(spec["candidates"])
        if not spec["candidates"]:
            raise ValueError(f"no placements exist for {spec['kind']} in {h}x{w}")
    specs.sort(key=lambda item: len(item["candidates"]))

    chosen: list[tuple[dict[str, Any], tuple[tuple[int, int], ...]]] = []
    occupied: set[tuple[int, int]] = set()

    def search(index: int) -> bool:
        if index == len(specs):
            return True
        spec = specs[index]
        for cells in spec["candidates"]:
            reserved = set(cells)
            if occupied & reserved:
                continue
            occupied.update(reserved)
            chosen.append((spec, cells))
            if search(index + 1):
                return True
            chosen.pop()
            occupied.difference_update(reserved)
        return False

    if not search(0):
        raise ValueError(
            "could not place the requested exact combination: "
            f"grid={h}x{w}, pair_count={pair_count}, "
            f"orientation_profile={orientation_profile}, "
            f"control_profile={control_profile}, position_profile={position_profile}"
        )

    grid = full_grid(h, w, 0)
    for spec, cells in chosen:
        for (r, c), value in spec["values"](cells).items():
            grid[r][c] = value
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
    defaults = _scheduled_defaults(ctx, difficulty)
    h = _draw_int(ctx, overrides, "grid_h", defaults["grid_h"], (6, 14))
    w = _draw_int(ctx, overrides, "grid_w", defaults["grid_w"], (7, 14))
    pair_count = _draw_int(ctx, overrides, "pair_count", defaults["pair_count"], (2, 3))
    orientation_profile = _draw_choice(
        ctx, overrides, "orientation_profile", defaults["orientation_profile"], _ORIENTATIONS
    )
    control_profile = _draw_choice(
        ctx, overrides, "control_profile", defaults["control_profile"], _CONTROL_PROFILES
    )
    position_profile = _draw_choice(
        ctx, overrides, "position_profile", defaults["position_profile"], _POSITION_PROFILES
    )

    rng = ctx.draw_rng("layout")
    color_count = pair_count + (4 if control_profile == "all" else 0)
    colors = rng.sample(range(1, 10), color_count)
    grid = _place_scene(
        h,
        w,
        pair_count,
        orientation_profile,
        control_profile,
        position_profile,
        colors,
        rng,
    )
    errors = self_check(grid)
    if errors:
        raise AssertionError("internal generator error: " + "; ".join(errors))
    return grid


def _opposite_color(grid: list[list[int]], r: int, c: int,
                    dr: int, dc: int) -> int | None:
    h, w = len(grid), len(grid[0])
    r1, c1, r2, c2 = r - dr, c - dc, r + dr, c + dc
    if not (0 <= r1 < h and 0 <= c1 < w and 0 <= r2 < h and 0 <= c2 < w):
        return None
    first, second = grid[r1][c1], grid[r2][c2]
    return first if first != 0 and first == second else None


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used only for tests and semantic rival scoring."""
    out = deepcopy(grid)
    if not grid or not grid[0]:
        return out
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            color = _opposite_color(grid, r, c, 1, 1)
            if color is None:
                color = _opposite_color(grid, r, c, 1, -1)
            if color is not None:
                out[r][c] = color
    return out


def _analyze(grid: Any) -> dict[str, Any]:
    info: dict[str, Any] = {
        "errors": [],
        "grid_h": 0,
        "grid_w": 0,
        "positive_pairs": [],
        "axis_controls": [],
        "long_controls": [],
        "blocked_pairs": [],
        "singletons": [],
        "unknown_colors": [],
    }
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        info["errors"].append("grid must be a non-empty list of rows")
        return info
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        info["errors"].append("grid must be rectangular and non-empty")
        return info
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        info["errors"].append("grid colors must be integers in 0..9")
        return info

    height = len(grid)
    info["grid_h"], info["grid_w"] = height, width
    by_color = {
        color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                if value == color]
        for color in sorted({value for row in grid for value in row if value != 0})
    }

    for color, cells in by_color.items():
        if len(cells) == 1:
            info["singletons"].append({"color": color, "cell": cells[0]})
            continue
        if len(cells) != 2:
            info["unknown_colors"].append({"color": color, "cells": cells})
            continue
        a, b = sorted(cells)
        dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
        midpoint = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
        if dr == 2 and dc == 2:
            orientation = "main" if (b[0] - a[0]) * (b[1] - a[1]) > 0 else "anti"
            item = {
                "color": color,
                "cells": (a, b),
                "midpoint": midpoint,
                "orientation": orientation,
            }
            if grid[midpoint[0]][midpoint[1]] == 0:
                info["positive_pairs"].append(item)
            else:
                item["blocker_color"] = grid[midpoint[0]][midpoint[1]]
                info["blocked_pairs"].append(item)
        elif (dr, dc) in ((0, 2), (2, 0)) and grid[midpoint[0]][midpoint[1]] == 0:
            info["axis_controls"].append({
                "color": color, "cells": (a, b), "midpoint": midpoint
            })
        elif dr == 4 and dc == 4 and grid[midpoint[0]][midpoint[1]] == 0:
            info["long_controls"].append({
                "color": color, "cells": (a, b), "midpoint": midpoint
            })
        else:
            info["unknown_colors"].append({"color": color, "cells": cells})

    orientations = {pair["orientation"] for pair in info["positive_pairs"]}
    if orientations == {"main"}:
        info["orientation_profile"] = "main"
    elif orientations == {"anti"}:
        info["orientation_profile"] = "anti"
    elif orientations == {"main", "anti"}:
        info["orientation_profile"] = "both"
    else:
        info["orientation_profile"] = "invalid"

    info["pair_count"] = len(info["positive_pairs"])
    info["position_profile"] = "border" if any(
        r in (0, height - 1) or c in (0, width - 1)
        for pair in info["positive_pairs"] for r, c in pair["cells"]
    ) else "interior"

    blocked_midpoints = {
        (pair["midpoint"], pair["blocker_color"]) for pair in info["blocked_pairs"]
    }
    singleton_roles = {(item["cell"], item["color"]) for item in info["singletons"]}
    blockers_match = blocked_midpoints == singleton_roles
    no_controls = not any((
        info["axis_controls"], info["long_controls"],
        info["blocked_pairs"], info["singletons"],
    ))
    all_controls = (
        len(info["axis_controls"]) == 1
        and len(info["long_controls"]) == 1
        and len(info["blocked_pairs"]) == 1
        and len(info["singletons"]) == 1
        and blockers_match
    )
    info["control_profile"] = "none" if no_controls else "all" if all_controls else "invalid"

    true_matches: dict[tuple[int, int], list[int]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            colors = []
            for dr, dc in ((1, 1), (1, -1)):
                color = _opposite_color(grid, r, c, dr, dc)
                if color is not None:
                    colors.append(color)
            if colors:
                true_matches[(r, c)] = colors
    info["true_matches"] = true_matches
    expected = {
        pair["midpoint"]: [pair["color"]] for pair in info["positive_pairs"]
    }
    info["true_matches_exact"] = true_matches == expected
    return info


def observe_overrides(grid: Any) -> dict[str, Any]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "pair_count": info["pair_count"],
        "orientation_profile": info["orientation_profile"],
        "control_profile": info["control_profile"],
        "position_profile": info["position_profile"],
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty
    info = _analyze(grid)
    messages = list(info["errors"])
    if messages:
        return messages
    h, w = info["grid_h"], info["grid_w"]
    if not 6 <= h <= 14:
        messages.append("grid height must be in 6..14")
    if not 7 <= w <= 14:
        messages.append("grid width must be in 7..14")
    if not 2 <= info["pair_count"] <= 3:
        messages.append("expected two or three fillable diagonal pairs")
    if info["orientation_profile"] not in _ORIENTATIONS:
        messages.append("positive pairs do not form a valid orientation profile")
    if info["control_profile"] not in _CONTROL_PROFILES:
        messages.append("controls must be absent or one complete axis/long/blocked trio")
    if info["unknown_colors"]:
        messages.append("every non-zero color must have one recognized structural role")
    if not info["true_matches_exact"]:
        messages.append("blank diagonal matches must equal the declared positive-pair midpoints")

    output = rule_mirror(grid)
    changed = {
        (r, c) for r in range(h) for c in range(w) if output[r][c] != grid[r][c]
    }
    expected_changed = {pair["midpoint"] for pair in info["positive_pairs"]}
    if changed != expected_changed:
        messages.append("the selected rule must change exactly the positive-pair midpoints")

    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for name, value in requested.items():
                if name in AXES and value is not None and observed.get(name) != value:
                    messages.append(
                        f"override {name} requested {value!r}, observed {observed.get(name)!r}"
                    )
    return messages


def strict_canonical_like(grid: Any) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    observed = observe_overrides(grid)
    if (observed["grid_h"], observed["grid_w"]) not in _CANONICAL_DIMS:
        reasons.append("dimensions are outside the three canonical joint profiles")
    if observed["control_profile"] != "none":
        reasons.append("canonical inputs contain no negative-control objects")
    if observed["orientation_profile"] != "both":
        reasons.append("canonical inputs exercise both diagonal orientations")
    return reasons


def _rival_axis_or_diagonal(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            for dr, dc in ((1, 1), (1, -1), (1, 0), (0, 1)):
                color = _opposite_color(grid, r, c, dr, dc)
                if color is not None:
                    out[r][c] = color
                    break
    return out


def _rival_any_diagonal_span(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            chosen = None
            for distance in (1, 2):
                for dc_sign in (1, -1):
                    r1, c1 = r - distance, c - distance * dc_sign
                    r2, c2 = r + distance, c + distance * dc_sign
                    if not (0 <= r1 < h and 0 <= c1 < w and 0 <= r2 < h and 0 <= c2 < w):
                        continue
                    first, second = grid[r1][c1], grid[r2][c2]
                    if first != 0 and first == second:
                        chosen = first
                        break
                if chosen is not None:
                    break
            if chosen is not None:
                out[r][c] = chosen
    return out


def _rival_overwrite_blocked(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, _value in enumerate(row):
            color = _opposite_color(grid, r, c, 1, 1)
            if color is None:
                color = _opposite_color(grid, r, c, 1, -1)
            if color is not None:
                out[r][c] = color
    return out


def _rival_main_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                color = _opposite_color(grid, r, c, 1, 1)
                if color is not None:
                    out[r][c] = color
    return out


def _rival_anti_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                color = _opposite_color(grid, r, c, 1, -1)
                if color is not None:
                    out[r][c] = color
    return out


def _witness_orientation(name: str) -> Callable[[Any], bool]:
    return lambda grid: any(
        pair["orientation"] == name for pair in _analyze(grid)["positive_pairs"]
    )


def _witness_control(name: str) -> Callable[[Any], bool]:
    return lambda grid: bool(_analyze(grid)[name])


SEMANTIC_WITNESSES = {
    "main_diagonal_pair": _witness_orientation("main"),
    "anti_diagonal_pair": _witness_orientation("anti"),
    "axis_aligned_control": _witness_control("axis_controls"),
    "length5_diagonal_control": _witness_control("long_controls"),
    "blocked_midpoint_control": _witness_control("blocked_pairs"),
}

SEMANTIC_RIVALS = {
    "fill_axis_or_diagonal_distance2": _rival_axis_or_diagonal,
    "fill_any_diagonal_span": _rival_any_diagonal_span,
    "overwrite_blocked_midpoints": _rival_overwrite_blocked,
    "fill_main_only": _rival_main_only,
    "fill_anti_only": _rival_anti_only,
}

WITNESS_RIVALS = {
    "main_diagonal_pair": ["fill_anti_only"],
    "anti_diagonal_pair": ["fill_main_only"],
    "axis_aligned_control": ["fill_axis_or_diagonal_distance2"],
    "length5_diagonal_control": ["fill_any_diagonal_span"],
    "blocked_midpoint_control": ["overwrite_blocked_midpoints"],
}

CANONICAL_SHORTCUTS = {
    "fill_axis_or_diagonal_distance2": _rival_axis_or_diagonal,
    "fill_any_diagonal_span": _rival_any_diagonal_span,
    "overwrite_blocked_midpoints": _rival_overwrite_blocked,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if not 2 <= len(demos) <= 5:
        reasons.append("lesson must contain between two and five demonstrations")
        return reasons
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is missing input/output")
            continue
        if rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} disagrees with the selected rule")
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is missing input/output")
        return reasons
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the selected rule")

    for name, competitor in LESSON_COMPETITORS.items():
        fits_demos = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if fits_demos and competitor(query["input"]) != query["output"]:
            reasons.append(f"competitor {name} fits every demo but changes the query answer")
    return reasons
