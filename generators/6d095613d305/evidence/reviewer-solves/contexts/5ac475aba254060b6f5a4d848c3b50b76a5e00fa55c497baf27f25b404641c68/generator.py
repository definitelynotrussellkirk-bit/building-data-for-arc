"""Semantic curriculum generator for H49 polyline intersections.

Each of two nonzero colors supplies row-major ordered waypoints.  Consecutive
waypoints are joined horizontally first and vertically second.  A cell used by
both color traces is painted 9.  Ordinary draws deliberately distinguish that
rule from vertical-first bends, column-major waypoint order, first-to-last-only
traces, and overwriting an intersection with the later color.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6d095613d305"
TASK_ID = "6d095613d305"
RULE_HASH = "bd682e817aa3"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "Trace each color's row-major waypoints with horizontal-then-vertical "
    "segments; paint cells shared by both traces with color 9."
)

INVARIANTS = [
    "the input has exactly two nonzero, non-9 waypoint colors",
    "each color has the same 3..5 waypoint count",
    "each color's row-major chain contains horizontal and vertical movement",
    "ordinary three-example windows cover zero, one, and multiple overlaps",
]

SCHEDULE_PROFILES = ("single", "multiple", "separated")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-scale slot or difficulty-aware 8..18",
        "valid": "8..18",
        "doc": "Grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-scale slot or difficulty-aware 9..20",
        "valid": "9..20",
        "doc": "Grid width.",
    },
    "points_per_color": {
        "type": "int",
        "default": "3 in canonical-scale slot, otherwise difficulty-aware 3..5",
        "valid": "3..5",
        "doc": "Equal number of row-major waypoints for both colors.",
    },
    "crossing_profile": {
        "type": "str",
        "default": "sample_index schedule",
        "valid": "separated|single|multiple",
        "doc": "Number of output overlap cells: 0, exactly 1, or at least 2.",
    },
}


def _normalize_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    normalized: list[list[int]] = []
    for row in grid:
        out_row: list[int] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return None, [f"cell value {value!r} is not an ARC color 0..9"]
            out_row.append(value)
        normalized.append(out_row)
    return normalized, []


def _color_points(grid: list[list[int]]) -> list[tuple[int, list[tuple[int, int]]]]:
    order: list[int] = []
    points: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            if value not in points:
                order.append(value)
                points[value] = []
            points[value].append((r, c))
    return [(color, points[color]) for color in order]


def _ordered_points(points: list[tuple[int, int]], order: str) -> list[tuple[int, int]]:
    if order == "row_major":
        return sorted(points)
    if order == "column_major":
        return sorted(points, key=lambda point: (point[1], point[0]))
    raise ValueError(f"unknown point order {order!r}")


def _axis_cells(start: int, end: int) -> range:
    if start == end:
        return range(0)
    step = 1 if end > start else -1
    return range(start + step, end + step, step)


def _trace_cells(
    points: list[tuple[int, int]],
    *,
    order: str = "row_major",
    bend: str = "horizontal_first",
    use_all_points: bool = True,
) -> list[tuple[int, int]]:
    ordered = _ordered_points(points, order)
    if not use_all_points and len(ordered) > 1:
        ordered = [ordered[0], ordered[-1]]
    if not ordered:
        return []

    cells = [ordered[0]]
    for (r1, c1), (r2, c2) in zip(ordered, ordered[1:]):
        if bend == "horizontal_first":
            cells.extend((r1, c) for c in _axis_cells(c1, c2))
            cells.extend((r, c2) for r in _axis_cells(r1, r2))
        elif bend == "vertical_first":
            cells.extend((r, c1) for r in _axis_cells(r1, r2))
            cells.extend((r2, c) for c in _axis_cells(c1, c2))
        else:
            raise ValueError(f"unknown bend mode {bend!r}")

    # The Racket authority removes repeated cells before painting.  Painting a
    # set in either first- or last-occurrence order is answer-equivalent here.
    return list(dict.fromkeys(cells))


def _apply_rule(
    grid: Any,
    *,
    order: str = "row_major",
    bend: str = "horizontal_first",
    use_all_points: bool = True,
    overlap: str = "nine",
) -> list[list[int]]:
    normalized, errors = _normalize_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    assert normalized is not None
    height, width = len(normalized), len(normalized[0])
    out = full_grid(height, width, 0)
    for color, points in _color_points(normalized):
        for r, c in _trace_cells(
            points,
            order=order,
            bend=bend,
            use_all_points=use_all_points,
        ):
            if out[r][c] == 0:
                out[r][c] = color
            elif overlap == "nine":
                out[r][c] = 9
            elif overlap == "later_color":
                out[r][c] = color
            else:
                raise ValueError(f"unknown overlap mode {overlap!r}")
    return out


def rule_mirror(grid: Any) -> list[list[int]]:
    """Input-pure Python mirror of the selected Racket authority."""
    return _apply_rule(grid)


def _vertical_first(grid: Any) -> list[list[int]]:
    return _apply_rule(grid, bend="vertical_first")


def _column_major_order(grid: Any) -> list[list[int]]:
    return _apply_rule(grid, order="column_major")


def _first_to_last_only(grid: Any) -> list[list[int]]:
    return _apply_rule(grid, use_all_points=False)


def _overlap_as_later_color(grid: Any) -> list[list[int]]:
    return _apply_rule(grid, overlap="later_color")


def semantic_observables(grid: Any) -> dict[str, Any]:
    normalized, errors = _normalize_grid(grid)
    facts: dict[str, Any] = {
        "grid_h": 0,
        "grid_w": 0,
        "points_per_color": None,
        "colors": [],
        "overlap_cells": 0,
        "crossing_profile": None,
        "rule_output": None,
    }
    if errors:
        return {"errors": errors, **facts}
    assert normalized is not None
    height, width = len(normalized), len(normalized[0])
    facts["grid_h"] = height
    facts["grid_w"] = width

    color_points = _color_points(normalized)
    colors = [color for color, _ in color_points]
    facts["colors"] = colors
    if 9 in colors:
        errors.append("input color 9 is reserved for output overlaps")
    if len(colors) != 2:
        errors.append(f"expected exactly two waypoint colors; found {colors}")

    counts = [len(points) for _, points in color_points]
    if len(counts) == 2:
        if counts[0] != counts[1]:
            errors.append(f"waypoint counts must match; found {counts}")
        if not all(3 <= count <= 5 for count in counts):
            errors.append(f"each color needs 3..5 waypoints; found {counts}")
        if counts[0] == counts[1]:
            facts["points_per_color"] = counts[0]

    for color, points in color_points:
        ordered = sorted(points)
        horizontal = any(c1 != c2 for (_, c1), (_, c2) in zip(ordered, ordered[1:]))
        vertical = any(r1 != r2 for (r1, _), (r2, _) in zip(ordered, ordered[1:]))
        if not horizontal or not vertical:
            errors.append(
                f"color {color} row-major chain must contain horizontal and vertical movement"
            )

    if errors:
        return {"errors": errors, **facts}

    truth = rule_mirror(normalized)
    if truth == normalized:
        errors.append("rule would be an identity transformation")
    if _first_to_last_only(normalized) == truth:
        errors.append("middle waypoints do not affect the output")

    overlap_cells = sum(value == 9 for row in truth for value in row)
    profile = "separated" if overlap_cells == 0 else "single" if overlap_cells == 1 else "multiple"
    facts.update(
        {
            "overlap_cells": overlap_cells,
            "crossing_profile": profile,
            "rule_output": truth,
        }
    )
    return {"errors": errors, **facts}


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, weak, reserved-color, or non-chain inputs."""
    del difficulty, meta
    observed = semantic_observables(grid)
    errors = list(observed["errors"])
    if errors:
        return errors
    if not 8 <= observed["grid_h"] <= 18:
        errors.append(f"grid height {observed['grid_h']} outside 8..18")
    if not 9 <= observed["grid_w"] <= 20:
        errors.append(f"grid width {observed['grid_w']} outside 9..20")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Accept the public H49 manifold: canonical scale, three points, 1..2 overlaps."""
    reasons = self_check(grid)
    observed = semantic_observables(grid)
    if reasons:
        return reasons
    if not 9 <= observed["grid_h"] <= 10 or not 11 <= observed["grid_w"] <= 13:
        reasons.append(
            f"canonical dimensions are 9..10 by 11..13; found "
            f"{observed['grid_h']}x{observed['grid_w']}"
        )
    if observed["points_per_color"] != 3:
        reasons.append(
            f"canonical inputs have three points per color; found "
            f"{observed['points_per_color']}"
        )
    if not 1 <= observed["overlap_cells"] <= 2:
        reasons.append(
            f"canonical inputs expose one or two overlaps; found "
            f"{observed['overlap_cells']}"
        )
    return reasons


def observe_overrides(grid: Any) -> dict[str, int | str]:
    """Recover every declared exact axis from a valid returned grid."""
    observed = semantic_observables(grid)
    if observed["errors"]:
        raise ValueError("; ".join(observed["errors"]))
    return {
        "grid_h": observed["grid_h"],
        "grid_w": observed["grid_w"],
        "points_per_color": observed["points_per_color"],
        "crossing_profile": observed["crossing_profile"],
        "overlap_cells": observed["overlap_cells"],
    }


def _witness_horizontal_first(grid: Any) -> bool:
    return rule_mirror(grid) != _vertical_first(grid)


def _witness_row_major_order(grid: Any) -> bool:
    return rule_mirror(grid) != _column_major_order(grid)


def _witness_all_waypoints(grid: Any) -> bool:
    return rule_mirror(grid) != _first_to_last_only(grid)


def _witness_overlap_marker(grid: Any) -> bool:
    return rule_mirror(grid) != _overlap_as_later_color(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "vertical_first": _vertical_first,
    "column_major_order": _column_major_order,
    "first_to_last_only": _first_to_last_only,
    "overlap_as_later_color": _overlap_as_later_color,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "horizontal_first": _witness_horizontal_first,
    "row_major_order": _witness_row_major_order,
    "all_waypoints": _witness_all_waypoints,
    "overlap_marker": _witness_overlap_marker,
}

WITNESS_RIVALS = {
    "horizontal_first": ["vertical_first"],
    "row_major_order": ["column_major_order"],
    "all_waypoints": ["first_to_last_only"],
    "overlap_marker": ["overlap_as_later_color"],
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic three-slot lesson schedule to the semantic gate."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def lesson_identifiable(demos, query) -> list[str]:
    """Verify that a three-demo lesson refutes every named plausible rival."""
    errors: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    profiles: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} is missing input/output")
            continue
        try:
            truth = rule_mirror(pair["input"])
            profiles.add(observe_overrides(pair["input"])["crossing_profile"])
        except (TypeError, ValueError) as exc:
            errors.append(f"demo {index} is invalid: {exc}")
            continue
        if truth != pair["output"]:
            errors.append(f"demo {index} output disagrees with the selected rule")

    if profiles != set(SCHEDULE_PROFILES):
        errors.append(
            f"demos must cover {sorted(SCHEDULE_PROFILES)}; found {sorted(profiles)}"
        )

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"competitor {name!r} could not be scored: {exc}")
            continue
        if survives:
            errors.append(f"competitor {name!r} fits every demonstration")

    if isinstance(query, dict) and "input" in query and "output" in query:
        try:
            if rule_mirror(query["input"]) != query["output"]:
                errors.append("query output disagrees with the selected rule")
        except (TypeError, ValueError) as exc:
            errors.append(f"query is invalid: {exc}")
    return errors


def _draw_int_axis(
    ctx,
    overrides: dict[str, Any],
    name: str,
    *,
    canonical: tuple[int, int] | None,
    global_bounds: tuple[int, int],
) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, *global_bounds)
    if canonical is not None:
        return ctx.draw_int(name, *canonical)
    return ctx.draw_int_diff(name, *global_bounds)


def _profile_matches(overlap_cells: int, profile: str) -> bool:
    if profile == "separated":
        return overlap_cells == 0
    if profile == "single":
        return overlap_cells == 1
    if profile == "multiple":
        return overlap_cells >= 2
    return False


def _candidate_is_teaching(grid: list[list[int]], profile: str) -> bool:
    observed = semantic_observables(grid)
    if observed["errors"] or not _profile_matches(observed["overlap_cells"], profile):
        return False
    truth = observed["rule_output"]
    if _vertical_first(grid) == truth:
        return False
    if _column_major_order(grid) == truth:
        return False
    if _first_to_last_only(grid) == truth:
        return False
    if profile != "separated" and _overlap_as_later_color(grid) == truth:
        return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    scheduled = schedule_profile(seed, sample_index, difficulty)
    explicit_profile = overrides.get("crossing_profile")
    effective = dict(overrides)
    if explicit_profile is None:
        effective["crossing_profile"] = scheduled

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    profile = ctx.draw_choice("crossing_profile", SCHEDULE_PROFILES)
    canonical_slot = explicit_profile is None and scheduled == "single"
    height = _draw_int_axis(
        ctx,
        overrides,
        "grid_h",
        canonical=(9, 10) if canonical_slot else None,
        global_bounds=(8, 18),
    )
    width = _draw_int_axis(
        ctx,
        overrides,
        "grid_w",
        canonical=(11, 13) if canonical_slot else None,
        global_bounds=(9, 20),
    )
    points_per_color = _draw_int_axis(
        ctx,
        overrides,
        "points_per_color",
        canonical=(3, 3) if canonical_slot else None,
        global_bounds=(3, 5),
    )
    colors = ctx.draw_distinct_colors("colors", n=2, exclude=(0, 9))
    rng = ctx.draw_rng("layout")
    population = [(r, c) for r in range(height) for c in range(width)]

    for _ in range(1024):
        chosen = rng.sample(population, 2 * points_per_color)
        grid = full_grid(height, width, 0)
        for r, c in chosen[:points_per_color]:
            grid[r][c] = colors[0]
        for r, c in chosen[points_per_color:]:
            grid[r][c] = colors[1]
        if not _candidate_is_teaching(grid, profile):
            continue
        observed = observe_overrides(grid)
        expected = {
            "grid_h": height,
            "grid_w": width,
            "points_per_color": points_per_color,
            "crossing_profile": profile,
        }
        if any(observed[name] != value for name, value in expected.items()):
            raise AssertionError(f"axis observation mismatch: expected {expected}, got {observed}")
        return grid

    raise RuntimeError(
        f"could not realize profile={profile!r}, grid={height}x{width}, "
        f"points_per_color={points_per_color} after 1024 deterministic attempts"
    )
