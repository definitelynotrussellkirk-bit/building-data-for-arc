"""Semantic curriculum generator for task ``928c39acebe3``.

A red(2) emitter launches one ray to the right.  A yellow(4) cell is a
slash mirror, a gray(5) cell is a backslash mirror, and a magenta(6) cell
stops the ray without being painted.  The output is otherwise empty and
marks every traversed cell—including mirror cells—in cyan(8).

The public examples cover only three of the four incoming directions for each
mirror type.  Two scheduled probe profiles therefore exercise the missing
``slash from west`` and ``backslash from north`` branches on the same ray.
This prevents a partial lookup-table shortcut from fitting a lesson.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "928c39acebe3"
TASK_ID = GENERATOR_ID
VERSION = "2.0.1"
RULE_HASH = "5e6d34fb1a87"

SUMMARY = (
    "Trace the right-launched red(2) ray, paint every traversed cell cyan(8), "
    "reflect on slash(4) and backslash(5) mirrors, and stop before magenta(6)."
)

INVARIANTS = [
    "the background is black(0)",
    "exactly one red(2) emitter launches to the right",
    "every yellow(4) and gray(5) mirror lies on the traced route",
    "exactly one magenta(6) blocker terminates the route",
    "the output is an empty same-size grid with every traversed cell painted cyan(8)",
]


@dataclass(frozen=True)
class _Profile:
    height: int
    width: int
    hit_colors: tuple[int, ...]
    recipe: str


_PROFILE_ROWS: tuple[tuple[str, _Profile], ...] = (
    (
        "canonical_8x12_545",
        _Profile(8, 12, (5, 4, 5), "box_stop_up"),
    ),
    (
        "canonical_9x13_554",
        _Profile(9, 13, (5, 5, 4), "stair_stop_up"),
    ),
    (
        "canonical_8x14_5454",
        _Profile(8, 14, (5, 4, 5, 4), "box_exit_right"),
    ),
    (
        "canonical_9x14_5544",
        _Profile(9, 14, (5, 5, 4, 4), "stair_exit_right"),
    ),
    (
        "full_direction_probe_compact",
        _Profile(10, 14, (5, 4, 4, 5, 4, 5), "full_direction_probe"),
    ),
    (
        "full_direction_probe_wide",
        _Profile(11, 16, (5, 4, 4, 5, 4, 5), "full_direction_probe"),
    ),
)

SCENE_PROFILES = tuple(name for name, _profile in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = dict(_PROFILE_ROWS)

# Alternating canonical-shaped examples and full-direction probes means every
# four-pair window contains two probes.  With three demonstrations and one
# query, every query rotation therefore leaves at least one probe visible.
DEFAULT_SCHEDULE = (
    "canonical_8x12_545",
    "full_direction_probe_compact",
    "canonical_9x13_554",
    "full_direction_probe_wide",
    "canonical_8x14_5454",
    "full_direction_probe_compact",
    "canonical_9x14_5544",
    "full_direction_probe_wide",
)
SCHEDULE_PERIOD = len(DEFAULT_SCHEDULE)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "eight-slot canonical/probe semantic schedule",
        "valid": (
            "canonical_8x12_545|canonical_9x13_554|"
            "canonical_8x14_5454|canonical_9x14_5544|"
            "full_direction_probe_compact|full_direction_probe_wide"
        ),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.40

_CANONICAL_LINKED_SIGNATURES = {
    (8, 12, (5, 4, 5)),
    (9, 13, (5, 5, 4)),
    (8, 14, (5, 4, 5, 4)),
    (9, 14, (5, 5, 4, 4)),
}


def _literal_int(name: str, value: Any, *, nonnegative: bool = False) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a literal integer (not bool)")
    if nonnegative and value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the source-bound eight-slot teaching profile."""
    _literal_int("seed", seed)
    index = _literal_int("sample_index", sample_index, nonnegative=True)
    _band(difficulty)
    return DEFAULT_SCHEDULE[index % SCHEDULE_PERIOD]


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["grid must be rectangular"]
    if not 3 <= len(grid) <= 30 or not 3 <= width <= 30:
        return [f"grid dimensions must be in 3..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _reflect(color: int, dr: int, dc: int) -> tuple[int, int]:
    if color == 4:  # slash: /
        return -dc, -dr
    if color == 5:  # backslash: \
        return dc, dr
    raise ValueError(f"not a mirror color: {color!r}")


def _simulate(
    grid: Sequence[Sequence[int]],
    *,
    mirror_mode: str = "official",
    slash_west_mode: str = "official",
    backslash_north_mode: str = "official",
    ignore_blocker: bool = False,
    stop_after_mirrors: int | None = None,
    paint_mode: str = "all",
) -> list[list[int]]:
    """Trace all emitters without mutating the input.

    The default branch is a direct Python mirror of the synchronized Racket
    authority.  Optional modes define explicit finite rivals used only by the
    semantic checks below.
    """
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    emitters = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    ]
    for source_row, source_col in emitters:
        row, col = source_row, source_col
        dr, dc = 0, 1
        seen: set[tuple[int, int, int, int]] = set()
        mirror_count = 0
        for _fuel in range(max(500, height * width * 8)):
            next_row, next_col = row + dr, col + dc
            if not (0 <= next_row < height and 0 <= next_col < width):
                break
            state = (next_row, next_col, dr, dc)
            if state in seen:
                break
            seen.add(state)
            value = grid[next_row][next_col]
            if value == 2:
                break
            if value == 6 and not ignore_blocker:
                break

            if paint_mode == "all" or value == 0:
                output[next_row][next_col] = 8

            if value in (4, 5):
                mirror_count += 1
                incoming = (dr, dc)
                if mirror_mode == "stop":
                    break
                effective = value
                if mirror_mode == "swapped":
                    effective = 5 if value == 4 else 4
                elif mirror_mode == "straight":
                    effective = 0
                if effective in (4, 5):
                    if (
                        effective == 4
                        and incoming == (0, -1)
                        and slash_west_mode == "straight"
                    ):
                        pass
                    elif (
                        effective == 5
                        and incoming == (-1, 0)
                        and backslash_north_mode == "straight"
                    ):
                        pass
                    else:
                        dr, dc = _reflect(effective, dr, dc)
                if stop_after_mirrors is not None and mirror_count >= stop_after_mirrors:
                    break
            row, col = next_row, next_col
    return output


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror; synchronized Racket remains authority."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _simulate(grid)


def _trace_one(grid: Sequence[Sequence[int]], source: tuple[int, int]) -> dict[str, Any]:
    height, width = len(grid), len(grid[0])
    row, col = source
    dr, dc = 0, 1
    seen: set[tuple[int, int, int, int]] = set()
    path: list[tuple[int, int, int, int, int]] = []
    hits: list[tuple[int, int, int, int, int]] = []
    stop_kind = "none"
    stop_cell: tuple[int, int] | None = None
    stop_direction: tuple[int, int] | None = None
    for _fuel in range(max(500, height * width * 8)):
        next_row, next_col = row + dr, col + dc
        if not (0 <= next_row < height and 0 <= next_col < width):
            stop_kind = "edge"
            stop_cell = (next_row, next_col)
            stop_direction = (dr, dc)
            break
        state = (next_row, next_col, dr, dc)
        if state in seen:
            stop_kind = "loop"
            stop_cell = (next_row, next_col)
            stop_direction = (dr, dc)
            break
        seen.add(state)
        value = grid[next_row][next_col]
        if value == 6:
            stop_kind = "blocker"
            stop_cell = (next_row, next_col)
            stop_direction = (dr, dc)
            break
        if value == 2:
            stop_kind = "emitter"
            stop_cell = (next_row, next_col)
            stop_direction = (dr, dc)
            break
        path.append((next_row, next_col, value, dr, dc))
        if value in (4, 5):
            hits.append((next_row, next_col, value, dr, dc))
            dr, dc = _reflect(value, dr, dc)
        row, col = next_row, next_col
    else:
        stop_kind = "fuel"
    return {
        "path": path,
        "hits": hits,
        "stop_kind": stop_kind,
        "stop_cell": stop_cell,
        "stop_direction": stop_direction,
        "looped": stop_kind == "loop",
    }


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    palette = {value for row in grid for value in row}
    extras = sorted(palette - {0, 2, 4, 5, 6})
    if extras:
        errors.append(f"unexpected input colors: {extras}")
    emitters = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    ]
    blockers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 6
    ]
    mirrors = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] in (4, 5)
    ]
    result: dict[str, Any] = {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "palette_size": len(palette),
        "emitters": emitters,
        "blockers": blockers,
        "all_mirrors": mirrors,
    }
    if len(emitters) != 1:
        errors.append(f"expected exactly one red(2) emitter, found {len(emitters)}")
        return result
    details = _trace_one(grid, emitters[0])
    hit_positions = {(row, col) for row, col, _value, _dr, _dc in details["hits"]}
    result.update(
        {
            "source": emitters[0],
            "path": details["path"],
            "hit_mirrors": details["hits"],
            "hit_colors": tuple(hit[2] for hit in details["hits"]),
            "incoming_pairs": tuple((hit[2], hit[3], hit[4]) for hit in details["hits"]),
            "off_path_mirrors": [
                mirror for mirror in mirrors if mirror[:2] not in hit_positions
            ],
            "stop_kind": details["stop_kind"],
            "stop_cell": details["stop_cell"],
            "stop_direction": details["stop_direction"],
            "looped": details["looped"],
            "painted_zeros": [
                (row, col)
                for row, col, value, _dr, _dc in details["path"]
                if value == 0
            ],
        }
    )
    return result


def _profile_signature(grid: Any) -> tuple[Any, ...] | None:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    return (
        analysis["height"],
        analysis["width"],
        analysis["source"][1],
        analysis["hit_colors"],
    )


def _declared_signature(profile: _Profile) -> tuple[Any, ...]:
    return profile.height, profile.width, 1, profile.hit_colors


_PROFILE_BY_SIGNATURE = {
    _declared_signature(profile): name for name, profile in _PROFILE_ROWS
}


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact composite profile from a returned grid."""
    name = _PROFILE_BY_SIGNATURE.get(_profile_signature(grid))
    return {"scene_profile": name} if name is not None else {}


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the selected curriculum manifold and semantic visibility."""
    if difficulty is not None:
        try:
            _band(difficulty)
        except ValueError as exc:
            return [str(exc)]
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if analysis["palette"] != {0, 2, 4, 5, 6}:
        errors.append(
            f"expected exact input palette {{0,2,4,5,6}}, found {sorted(analysis['palette'])}"
        )
    if len(analysis["blockers"]) != 1:
        errors.append(f"expected exactly one magenta(6) blocker, found {len(analysis['blockers'])}")
    if not 3 <= len(analysis["all_mirrors"]) <= 6:
        errors.append(
            f"expected 3..6 mirrors, found {len(analysis['all_mirrors'])}"
        )
    if set(analysis["hit_colors"]) != {4, 5}:
        errors.append("the traced route must expose both mirror colors 4 and 5")
    if analysis["off_path_mirrors"]:
        errors.append("every mirror in this curriculum must lie on the traced route")
    if len(analysis["hit_mirrors"]) != len(analysis["all_mirrors"]):
        errors.append("every mirror must be encountered exactly once")
    if analysis["stop_kind"] != "blocker":
        errors.append(f"the traced route must stop at color 6, found {analysis['stop_kind']}")
    if analysis["blockers"] and analysis["stop_cell"] != analysis["blockers"][0]:
        errors.append("the unique blocker is not the beam terminus")
    if not analysis["painted_zeros"]:
        errors.append("the route must traverse at least one background cell")
    if analysis["looped"]:
        errors.append("the route must not repeat a position/direction state")
    if not errors and _simulate(grid, ignore_blocker=True) == rule_mirror(grid):
        errors.append("the blocker needs a visible downstream counterfactual")
    realized = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and requested is not None and realized.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {realized.get(name)!r}"
            )
    return errors


def _candidate_box_stop_up(profile: _Profile) -> list[tuple[Any, ...]]:
    h, w = profile.height, profile.width
    candidates = []
    for source_row in range(1, h - 4):
        for bottom_row in range(source_row + 3, h - 1):
            for right_col in range(5, w - 2):
                for left_col in range(2, right_col - 1):
                    for stop_row in range(source_row + 1, bottom_row - 1):
                        candidates.append(
                            (
                                (source_row, 1),
                                (
                                    (source_row, right_col),
                                    (bottom_row, right_col),
                                    (bottom_row, left_col),
                                ),
                                (stop_row, left_col),
                            )
                        )
    return candidates


def _candidate_stair_stop_up(profile: _Profile) -> list[tuple[Any, ...]]:
    h, w = profile.height, profile.width
    candidates = []
    for source_row in range(1, h - 4):
        for bottom_row in range(source_row + 3, h - 1):
            for first_col in range(4, w - 5):
                for second_col in range(first_col + 3, w - 1):
                    for stop_row in range(source_row + 1, bottom_row - 1):
                        candidates.append(
                            (
                                (source_row, 1),
                                (
                                    (source_row, first_col),
                                    (bottom_row, first_col),
                                    (bottom_row, second_col),
                                ),
                                (stop_row, second_col),
                            )
                        )
    return candidates


def _candidate_box_exit_right(profile: _Profile) -> list[tuple[Any, ...]]:
    h, w = profile.height, profile.width
    candidates = []
    for source_row in range(3, h - 2):
        for top_row in range(1, source_row - 1):
            for bottom_row in range(source_row + 2, h - 1):
                for right_col in range(5, w - 3):
                    for left_col in range(2, right_col - 1):
                        for stop_col in range(left_col + 2, w - 1):
                            candidates.append(
                                (
                                    (source_row, 1),
                                    (
                                        (source_row, right_col),
                                        (bottom_row, right_col),
                                        (bottom_row, left_col),
                                        (top_row, left_col),
                                    ),
                                    (top_row, stop_col),
                                )
                            )
    return candidates


def _candidate_stair_exit_right(profile: _Profile) -> list[tuple[Any, ...]]:
    h, w = profile.height, profile.width
    candidates = []
    for source_row in range(3, h - 2):
        for top_row in range(1, source_row - 1):
            for bottom_row in range(source_row + 2, h - 1):
                for first_col in range(4, w - 6):
                    for second_col in range(first_col + 3, w - 3):
                        for stop_col in range(second_col + 2, w - 1):
                            candidates.append(
                                (
                                    (source_row, 1),
                                    (
                                        (source_row, first_col),
                                        (bottom_row, first_col),
                                        (bottom_row, second_col),
                                        (top_row, second_col),
                                    ),
                                    (top_row, stop_col),
                                )
                            )
    return candidates


def _candidate_full_direction_probe(profile: _Profile) -> list[tuple[Any, ...]]:
    h, w = profile.height, profile.width
    candidates = []
    for top_row in range(1, h - 7):
        for source_row in range(top_row + 2, h - 5):
            for middle_row in range(source_row + 2, h - 3):
                for lower_row in range(middle_row + 2, h - 1):
                    for left_col in range(2, w - 8):
                        for first_col in range(left_col + 2, w - 6):
                            for stop_col in range(first_col + 2, w - 3):
                                for right_col in range(stop_col + 2, w - 1):
                                    candidates.append(
                                        (
                                            (source_row, 1),
                                            (
                                                (source_row, first_col),
                                                (middle_row, first_col),
                                                (middle_row, left_col),
                                                (lower_row, left_col),
                                                (lower_row, right_col),
                                                (top_row, right_col),
                                            ),
                                            (top_row, stop_col),
                                        )
                                    )
    return candidates


_CANDIDATE_BUILDERS = {
    "box_stop_up": _candidate_box_stop_up,
    "stair_stop_up": _candidate_stair_stop_up,
    "box_exit_right": _candidate_box_exit_right,
    "stair_exit_right": _candidate_stair_exit_right,
    "full_direction_probe": _candidate_full_direction_probe,
}


def _construct_profile(profile: _Profile, rng) -> list[list[int]]:
    candidates = _CANDIDATE_BUILDERS[profile.recipe](profile)
    if not candidates:
        raise ValueError(f"profile recipe has no legal geometry: {profile!r}")
    source, mirror_positions, blocker = rng.choice(candidates)
    if len(mirror_positions) != len(profile.hit_colors):
        raise AssertionError("profile recipe and mirror-color sequence disagree")
    grid = full_grid(profile.height, profile.width, 0)
    grid[source[0]][source[1]] = 2
    for (row, col), color in zip(mirror_positions, profile.hit_colors):
        if grid[row][col] != 0:
            raise AssertionError("profile recipe overlaps semantic objects")
        grid[row][col] = color
    if grid[blocker[0]][blocker[1]] != 0:
        raise AssertionError("profile recipe overlaps blocker")
    grid[blocker[0]][blocker[1]] = 6
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    seed = _literal_int("seed", seed)
    sample_index = _literal_int("sample_index", sample_index, nonnegative=True)
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile_name = ctx.draw_choice("scene_profile", [scheduled])
    profile = _PROFILE_BY_NAME[profile_name]
    grid = _construct_profile(profile, ctx.draw_rng(f"layout_{band}"))
    errors = self_check(
        grid,
        difficulty=band,
        meta={"overrides": {"scene_profile": profile_name}},
    )
    if errors:
        raise ValueError(
            f"internal profile construction failed for {profile_name!r}: {errors}"
        )
    return grid


def strict_canonical_like(grid) -> list[str]:
    """Check the linked shape-plus-ray signature of the four canonical inputs."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if analysis["source"][1] != 1:
        errors.append("canonical emitters occupy column 1")
    linked = (analysis["height"], analysis["width"], analysis["hit_colors"])
    if linked not in _CANONICAL_LINKED_SIGNATURES:
        errors.append(f"linked beam signature is outside the canonical set: {linked!r}")
    return errors


def _rival_straight_through_mirrors(grid):
    return _simulate(grid, mirror_mode="straight")


def _rival_swap_mirror_types(grid):
    return _simulate(grid, mirror_mode="swapped")


def _rival_stop_after_first_mirror(grid):
    return _simulate(grid, stop_after_mirrors=1)


def _rival_ignore_blocker(grid):
    return _simulate(grid, ignore_blocker=True)


def _rival_paint_only_zero_cells(grid):
    return _simulate(grid, paint_mode="zeros_only")


def _rival_slash_from_west_continues(grid):
    return _simulate(grid, slash_west_mode="straight")


def _rival_backslash_from_north_continues(grid):
    return _simulate(grid, backslash_north_mode="straight")


def _rival_unseen_directions_continue(grid):
    return _simulate(
        grid,
        slash_west_mode="straight",
        backslash_north_mode="straight",
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "straight_through_mirrors": _rival_straight_through_mirrors,
    "swap_mirror_types": _rival_swap_mirror_types,
    "stop_after_first_mirror": _rival_stop_after_first_mirror,
    "ignore_blocker": _rival_ignore_blocker,
    "paint_only_zero_cells": _rival_paint_only_zero_cells,
    "slash_from_west_continues_straight": _rival_slash_from_west_continues,
    "backslash_from_north_continues_straight": (
        _rival_backslash_from_north_continues
    ),
    "unseen_directions_continue_straight": _rival_unseen_directions_continue,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# Every canonical ray omits slash-from-west and backslash-from-north.  These
# partial direction tables therefore match every public label exactly.
CANONICAL_SHORTCUTS = {
    "slash_from_west_continues_straight": _rival_slash_from_west_continues,
    "backslash_from_north_continues_straight": (
        _rival_backslash_from_north_continues
    ),
    "unseen_directions_continue_straight": _rival_unseen_directions_continue,
}


def _analysis_witness(predicate: Callable[[dict[str, Any]], bool]):
    def witness(grid) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and bool(predicate(analysis))

    return witness


SEMANTIC_WITNESSES = {
    "slash_reflection_on_path": _analysis_witness(
        lambda analysis: 4 in analysis["hit_colors"]
    ),
    "backslash_reflection_on_path": _analysis_witness(
        lambda analysis: 5 in analysis["hit_colors"]
    ),
    "multiple_reflections_are_followed": _analysis_witness(
        lambda analysis: len(analysis["hit_mirrors"]) >= 3
    ),
    "blocker_stops_without_painting": _analysis_witness(
        lambda analysis: analysis["stop_kind"] == "blocker"
    ),
    "mirror_cells_are_painted": _analysis_witness(
        lambda analysis: bool(analysis["hit_mirrors"])
    ),
    "slash_approached_from_west": _analysis_witness(
        lambda analysis: (4, 0, -1) in analysis["incoming_pairs"]
    ),
    "backslash_approached_from_north": _analysis_witness(
        lambda analysis: (5, -1, 0) in analysis["incoming_pairs"]
    ),
}
WITNESS_RIVALS = {
    "slash_reflection_on_path": ["straight_through_mirrors"],
    "backslash_reflection_on_path": ["straight_through_mirrors"],
    "multiple_reflections_are_followed": ["stop_after_first_mirror"],
    "blocker_stops_without_painting": ["ignore_blocker"],
    "mirror_cells_are_painted": ["paint_only_zero_cells"],
    "slash_approached_from_west": [
        "slash_from_west_continues_straight",
        "unseen_directions_continue_straight",
    ],
    "backslash_approached_from_north": [
        "backslash_from_north_continues_straight",
        "unseen_directions_continue_straight",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require visible demonstrations to falsify every declared rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    analyses: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        structural = self_check(pair["input"])
        if structural:
            reasons.append(f"demo {index} is outside the curriculum: {structural}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the ray-tracing rule")
            continue
        analyses.append(_analysis(pair["input"]))

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the curriculum: {query_errors}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the ray-tracing rule")

    incoming = {
        pair
        for analysis in analyses
        for pair in analysis.get("incoming_pairs", ())
    }
    if (4, 0, -1) not in incoming:
        reasons.append("demonstrations need a slash approached from west")
    if (5, -1, 0) not in incoming:
        reasons.append("demonstrations need a backslash approached from north")
    shapes = {(analysis["height"], analysis["width"]) for analysis in analyses}
    if len(shapes) < 2:
        reasons.append("demonstrations need at least two grid shapes")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
        except Exception as exc:  # pragma: no cover - gate-visible defensive path
            reasons.append(f"rival {name} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
