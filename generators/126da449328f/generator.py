"""Generator for ``shoot_a_ray_to_the_nearest_border``.

Every nonzero cell is a colored singleton seed.  Paint a straight ray from the
seed through its nearest border, preserving the seed color.  The authoritative
Racket rule resolves equal distances in the fixed order top, bottom, left,
right.  The canonical third training input contains a top/right tie and proves
that the former "uniquely nearest" description was too narrow.

Ordinary six-example windows deliberately cover unique minima and every
meaningful priority comparison: top over a side, bottom over a side, top over
bottom, and left over right.  This makes one-step, leave-ties-unchanged,
horizontal-first, always-horizontal, and always-vertical rivals observable.
The named ``right_over_left_ties`` shortcut is deliberately canonical-compatible:
the official examples never isolate a left/right tie, while generated lessons do.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "126da449328f"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "f5d1690cbbbb"
EXAMPLES_NEEDED = 6
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Extend every colored singleton seed to a nearest border.  Equal-distance "
    "ties use the authoritative priority top, then bottom, then left, then right."
)

INVARIANTS = [
    "the grid is 7..9 by 7..9 with background color 0",
    "there are 3..4 pairwise-distinct nonzero singleton seeds",
    "no seed is already on a border",
    "the priority-selected border rays are pairwise disjoint",
    "each ordinary scene uses at least three of the four ray directions",
    "six consecutive ordinary scenes cover unique minima and all tie priorities",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 7..9 with scheduled 7x9/9x7 tie anchors",
        "valid": "7..9",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 7..9 with scheduled 7x9/9x7 tie anchors",
        "valid": "7..9",
    },
    "seed_count": {
        "type": "int",
        "default": "difficulty-aware 3..4",
        "valid": "3..4",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

SIDES = ("top", "bottom", "left", "right")
SCENE_PROFILES = (
    "unique_only",
    "top_over_side",
    "bottom_over_side",
    "top_over_bottom",
    "left_over_right",
    "mixed_priority",
)
SCHEDULE_PROFILES = SCENE_PROFILES
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_AXIS_BOUNDS = {
    "grid_h": (7, 9),
    "grid_w": (7, 9),
    "seed_count": (3, 4),
}


def _validate_sample_index(sample_index: Any) -> None:
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")


def _validate_controls(
    seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool or a coercible value)")
    _validate_sample_index(sample_index)
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(
                f"{name} must be an integer (not bool or a coercible value)"
            )
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Any six consecutive ordinary samples contain every teaching profile."""
    del seed
    _validate_sample_index(sample_index)
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _distance_tuple(h: int, w: int, row: int, col: int) -> tuple[int, int, int, int]:
    return row, h - 1 - row, col, w - 1 - col


def _nearest_sides(h: int, w: int, row: int, col: int) -> tuple[str, ...]:
    distances = _distance_tuple(h, w, row, col)
    minimum = min(distances)
    return tuple(side for side, distance in zip(SIDES, distances) if distance == minimum)


def _ray_cells(
    h: int, w: int, row: int, col: int, *, side: str | None = None
) -> tuple[tuple[int, int], ...]:
    chosen = side or _nearest_sides(h, w, row, col)[0]
    if chosen == "top":
        return tuple((rr, col) for rr in range(0, row + 1))
    if chosen == "bottom":
        return tuple((rr, col) for rr in range(row, h))
    if chosen == "left":
        return tuple((row, cc) for cc in range(0, col + 1))
    if chosen == "right":
        return tuple((row, cc) for cc in range(col, w))
    raise ValueError(f"unknown side {chosen!r}")


def _tie_kind(nearest: tuple[str, ...]) -> str:
    if len(nearest) == 1:
        return "unique"
    side_set = set(nearest)
    if side_set == {"top", "bottom"}:
        return "top_bottom"
    if side_set == {"left", "right"}:
        return "left_right"
    if nearest[0] == "top" and "bottom" not in side_set and side_set & {"left", "right"}:
        return "top_side"
    if nearest[0] == "bottom" and "top" not in side_set and side_set & {"left", "right"}:
        return "bottom_side"
    return "multiway"


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "seeds": []}

    normalized = [list(row) for row in grid]
    h, w = len(normalized), len(normalized[0])
    if not 7 <= h <= 9:
        errors.append(f"height must be 7..9, found {h}")
    if not 7 <= w <= 9:
        errors.append(f"width must be 7..9, found {w}")

    raw_seeds = [
        (row, col, value)
        for row, values in enumerate(normalized)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not 3 <= len(raw_seeds) <= 4:
        errors.append(f"expected 3..4 colored seeds, found {len(raw_seeds)}")
    colors = [value for _, _, value in raw_seeds]
    if len(set(colors)) != len(colors):
        errors.append("seed colors must be pairwise distinct")

    seeds: list[dict[str, Any]] = []
    for row, col, color in raw_seeds:
        nearest = _nearest_sides(h, w, row, col)
        chosen = nearest[0]
        ray = _ray_cells(h, w, row, col, side=chosen)
        distance = min(_distance_tuple(h, w, row, col))
        if distance == 0:
            errors.append(f"seed at {(row, col)} lies on a border")
        seeds.append(
            {
                "position": (row, col),
                "row": row,
                "col": col,
                "color": color,
                "nearest_sides": nearest,
                "chosen_side": chosen,
                "tie_kind": _tie_kind(nearest),
                "distance": distance,
                "ray": ray,
            }
        )

    for index, first in enumerate(seeds):
        first_ray = set(first["ray"])
        for second in seeds[index + 1 :]:
            overlap = first_ray & set(second["ray"])
            if overlap:
                errors.append(
                    "priority-selected rays overlap at "
                    f"{sorted(overlap)[:3]} for seeds {first['position']} and {second['position']}"
                )

    directions = {seed["chosen_side"] for seed in seeds}
    if len(directions) < min(3, len(seeds)):
        errors.append("scene must exercise at least three distinct chosen border directions")

    tie_kinds = {seed["tie_kind"] for seed in seeds if seed["tie_kind"] != "unique"}
    profile: str | None
    if not tie_kinds:
        profile = "unique_only"
    elif tie_kinds <= {"top_side"}:
        profile = "top_over_side"
    elif tie_kinds <= {"bottom_side"}:
        profile = "bottom_over_side"
    elif tie_kinds <= {"top_bottom"}:
        profile = "top_over_bottom"
    elif tie_kinds <= {"left_right"}:
        profile = "left_over_right"
    elif tie_kinds <= {"top_side", "bottom_side"} and {
        "top_side",
        "bottom_side",
    } <= tie_kinds:
        profile = "mixed_priority"
    else:
        profile = None

    return {
        "errors": errors,
        "grid": normalized,
        "grid_h": h,
        "grid_w": w,
        "seed_count": len(raw_seeds),
        "seeds": seeds,
        "directions": directions,
        "tie_kinds": tie_kinds,
        "scene_profile": profile,
        "max_distance": max((seed["distance"] for seed in seeds), default=0),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate canonical inputs and the stronger generated teaching grammar."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if analysis["scene_profile"] is None:
        errors.append("tie combination is outside the scheduled teaching profiles")
    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis in AXES:
                if axis in requested and requested[axis] != observed[axis]:
                    errors.append(
                        f"override {axis}={requested[axis]!r} realized as {observed[axis]!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generated grammar is deliberately the canonical size/palette envelope."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned input grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid scene: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "seed_count": analysis["seed_count"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["scene_profile"] is None:
        raise ValueError("cannot observe invalid scene")
    return {
        **observe_overrides(grid),
        "scene_profile": analysis["scene_profile"],
        "directions": sorted(analysis["directions"]),
        "tie_kinds": sorted(analysis["tie_kinds"]),
        "max_distance": analysis["max_distance"],
    }


def _draw_axis_int(ctx, label: str, lo: int, hi: int, scheduled: int | None = None) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    if scheduled is not None:
        return ctx.draw_int_strict(label, scheduled, scheduled)
    return ctx.draw_int_diff(label, lo, hi)


def _candidate(
    h: int, w: int, row: int, col: int
) -> dict[str, Any]:
    nearest = _nearest_sides(h, w, row, col)
    chosen = nearest[0]
    return {
        "position": (row, col),
        "direction": chosen,
        "tie_kind": _tie_kind(nearest),
        "distance": min(_distance_tuple(h, w, row, col)),
        "ray": frozenset(_ray_cells(h, w, row, col, side=chosen)),
    }


def _required_tie_kinds(profile: str) -> set[str]:
    return {
        "unique_only": set(),
        "top_over_side": {"top_side"},
        "bottom_over_side": {"bottom_side"},
        "top_over_bottom": {"top_bottom"},
        "left_over_right": {"left_right"},
        "mixed_priority": {"top_side", "bottom_side"},
    }[profile]


def _allowed_tie_kinds(profile: str) -> set[str]:
    return {
        "unique_only": {"unique"},
        "top_over_side": {"unique", "top_side"},
        "bottom_over_side": {"unique", "bottom_side"},
        "top_over_bottom": {"unique", "top_bottom"},
        "left_over_right": {"unique", "left_right"},
        "mixed_priority": {"unique", "top_side", "bottom_side"},
    }[profile]


def _target_directions(profile: str, seed_count: int, sample_index: int) -> set[str]:
    if seed_count == 4:
        return set(SIDES)
    alternating_side = "left" if int(sample_index) % 2 == 0 else "right"
    alternating_vertical = "top" if int(sample_index) % 2 == 0 else "bottom"
    return {
        "unique_only": {"top", "bottom", alternating_side},
        "top_over_side": {"top", "left", "right"},
        "bottom_over_side": {"bottom", "left", "right"},
        "top_over_bottom": {"top", "bottom", alternating_side},
        "left_over_right": {"left", "right", alternating_vertical},
        "mixed_priority": {"top", "bottom", alternating_side},
    }[profile]


def _profile_possible(h: int, w: int, profile: str) -> bool:
    required = _required_tie_kinds(profile)
    present = {
        _candidate(h, w, row, col)["tie_kind"]
        for row in range(1, h - 1)
        for col in range(1, w - 1)
    }
    return required <= present


def _fallback_profile(profile: str, h: int, w: int) -> str:
    if _profile_possible(h, w, profile):
        return profile
    if profile == "top_over_bottom":
        return "top_over_side"
    if profile == "left_over_right":
        return "bottom_over_side"
    return "unique_only"


def _choose_positions(
    h: int,
    w: int,
    seed_count: int,
    profile: str,
    sample_index: int,
    rng,
) -> list[dict[str, Any]]:
    allowed = _allowed_tie_kinds(profile)
    candidates = [
        _candidate(h, w, row, col)
        for row in range(1, h - 1)
        for col in range(1, w - 1)
        if _candidate(h, w, row, col)["tie_kind"] in allowed
    ]
    rng.shuffle(candidates)
    required_ties = _required_tie_kinds(profile)
    target_directions = _target_directions(profile, seed_count, sample_index)

    def search(selected: list[dict[str, Any]], start: int):
        if len(selected) == seed_count:
            chosen_ties = {item["tie_kind"] for item in selected}
            chosen_directions = {item["direction"] for item in selected}
            if not required_ties <= chosen_ties:
                return None
            if not target_directions <= chosen_directions:
                return None
            if max(item["distance"] for item in selected) < 2:
                return None
            return selected

        missing_ties = required_ties - {item["tie_kind"] for item in selected}
        missing_directions = target_directions - {item["direction"] for item in selected}
        options = []
        for index in range(start, len(candidates)):
            item = candidates[index]
            if any(item["ray"] & previous["ray"] for previous in selected):
                continue
            score = (
                item["tie_kind"] in missing_ties,
                item["direction"] in missing_directions,
                item["distance"],
                rng.random(),
            )
            options.append((score, index, item))
        options.sort(reverse=True)
        for _score, index, item in options:
            found = search(selected + [item], index + 1)
            if found is not None:
                return found
        return None

    selected = search([], 0)
    if selected is None:
        raise ValueError(
            f"could not place {seed_count} disjoint seeds for {profile} on {h}x{w}"
        )
    return selected


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_controls(seed, sample_index, difficulty, overrides)

    band = "medium" if difficulty is None else difficulty
    profile = schedule_profile(seed, sample_index, band)
    scheduled_h = 7 if profile == "top_over_bottom" else 9 if profile == "left_over_right" else None
    scheduled_w = 9 if profile == "top_over_bottom" else 7 if profile == "left_over_right" else None

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h = _draw_axis_int(ctx, "grid_h", 7, 9, scheduled_h)
    w = _draw_axis_int(ctx, "grid_w", 7, 9, scheduled_w)
    seed_count = ctx.draw_int_diff("seed_count", 3, 4)
    profile = _fallback_profile(profile, h, w)

    rng = ctx.draw_rng(f"layout:{profile}")
    selected = _choose_positions(h, w, seed_count, profile, sample_index, rng)
    colors = ctx.draw_distinct_colors("colors", n=seed_count, exclude={0})
    grid = full_grid(h, w, 0)
    for item, color in zip(selected, colors):
        row, col = item["position"]
        grid[row][col] = color

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    expected_axes = {
        "grid_h": h,
        "grid_w": w,
        "seed_count": seed_count,
    }
    observed_axes = observe_overrides(grid)
    if observed_axes != expected_axes:
        raise AssertionError(
            f"constructed axes drifted: expected {expected_axes}, observed {observed_axes}"
        )
    return grid


def _apply_rule(
    grid: Any,
    *,
    priority: tuple[str, ...] = SIDES,
    leave_ties_unchanged: bool = False,
    one_step: bool = False,
    restrict: str | None = None,
) -> list[list[int]]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    source = [list(row) for row in grid]
    out = [row[:] for row in source]
    h, w = len(source), len(source[0])
    for row, values in enumerate(source):
        for col, color in enumerate(values):
            if color == 0:
                continue
            distances = dict(zip(SIDES, _distance_tuple(h, w, row, col)))
            minimum = min(distances.values())
            nearest = tuple(side for side in SIDES if distances[side] == minimum)
            if leave_ties_unchanged and len(nearest) > 1:
                continue
            if restrict == "vertical":
                side = min(("top", "bottom"), key=lambda name: (distances[name], SIDES.index(name)))
            elif restrict == "horizontal":
                side = min(("left", "right"), key=lambda name: (distances[name], SIDES.index(name)))
            else:
                side = min(priority, key=lambda name: (distances[name], priority.index(name)))
            ray = list(_ray_cells(h, w, row, col, side=side))
            if one_step and len(ray) > 1:
                if side in ("top", "left"):
                    ray = ray[-2:]
                else:
                    ray = ray[:2]
            for rr, cc in ray:
                out[rr][cc] = color
    return out


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python semantic mirror; the canonical Racket program remains authority."""
    return _apply_rule(grid)


def _horizontal_first(grid: Any) -> list[list[int]]:
    return _apply_rule(grid, priority=("left", "right", "top", "bottom"))


def _right_over_left_ties(grid: Any) -> list[list[int]]:
    """Canonical-compatible shortcut that reverses only the left/right tie."""
    return _apply_rule(grid, priority=("top", "bottom", "right", "left"))


def _leave_ties_unchanged(grid: Any) -> list[list[int]]:
    return _apply_rule(grid, leave_ties_unchanged=True)


def _one_step(grid: Any) -> list[list[int]]:
    return _apply_rule(grid, one_step=True)


def _always_vertical(grid: Any) -> list[list[int]]:
    return _apply_rule(grid, restrict="vertical")


def _always_horizontal(grid: Any) -> list[list[int]]:
    return _apply_rule(grid, restrict="horizontal")


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "horizontal_first_ties": _horizontal_first,
    "right_over_left_ties": _right_over_left_ties,
    "leave_ties_unchanged": _leave_ties_unchanged,
    "extend_one_step": _one_step,
    "always_vertical": _always_vertical,
    "always_horizontal": _always_horizontal,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _profile_witness(profile: str):
    def predicate(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and analysis["scene_profile"] == profile

    return predicate


SEMANTIC_WITNESSES = {
    profile: _profile_witness(profile) for profile in SCENE_PROFILES
}
SEMANTIC_WITNESSES.update(
    {
        "multi_direction_scene": lambda grid: (
            not _analyze(grid)["errors"]
            and len(_analyze(grid)["directions"]) >= 3
        ),
        "long_ray": lambda grid: (
            not _analyze(grid)["errors"] and _analyze(grid)["max_distance"] >= 2
        ),
    }
)

WITNESS_RIVALS = {
    "top_over_side": ["horizontal_first_ties", "leave_ties_unchanged"],
    "bottom_over_side": ["horizontal_first_ties", "leave_ties_unchanged"],
    "top_over_bottom": ["leave_ties_unchanged"],
    "left_over_right": ["leave_ties_unchanged", "right_over_left_ties"],
    "mixed_priority": ["horizontal_first_ties", "leave_ties_unchanged"],
    "unique_only": ["extend_one_step", "always_vertical", "always_horizontal"],
    "multi_direction_scene": ["always_vertical", "always_horizontal"],
    "long_ray": ["extend_one_step"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every sliding lesson to identify distance, direction, and ties."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    profiles: set[str] = set()
    directions: set[str] = set()
    has_long_ray = False
    for index, pair in enumerate(demos):
        grid = pair.get("input")
        analysis = _analyze(grid)
        if analysis["errors"] or analysis["scene_profile"] is None:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = rule_mirror(grid)
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the authoritative rule")
        profiles.add(analysis["scene_profile"])
        directions.update(analysis["directions"])
        has_long_ray = has_long_ray or analysis["max_distance"] >= 2

    missing_profiles = sorted(set(SCENE_PROFILES) - profiles)
    if missing_profiles:
        reasons.append(f"demonstrations omit scene profiles {missing_profiles}")
    missing_directions = sorted(set(SIDES) - directions)
    if missing_directions:
        reasons.append(f"demonstrations omit ray directions {missing_directions}")
    if not has_long_ray:
        reasons.append("demonstrations do not refute the one-step extension rival")

    for name, competitor in LESSON_COMPETITORS.items():
        if demos and all(
            competitor(pair["input"]) == pair.get("output")
            for pair in demos
            if "input" in pair
        ):
            reasons.append(f"named competitor {name!r} survives every demonstration")

    query_grid = query.get("input") if isinstance(query, dict) else None
    query_analysis = _analyze(query_grid)
    if query_analysis["errors"]:
        reasons.append("query input is outside the teaching grammar")
    elif isinstance(query, dict) and "output" in query:
        if query["output"] != rule_mirror(query_grid):
            reasons.append("query output disagrees with the authoritative rule")
    return reasons
