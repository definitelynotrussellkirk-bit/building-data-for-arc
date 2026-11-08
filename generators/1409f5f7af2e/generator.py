"""Generate identifiable lessons for ARC task 1409f5f7af2e.

The task recolors a black cell red exactly when the cells immediately above and
below it are both green.  The endpoints remain green and every other cell is
unchanged.

Ordinary samples use a three-slot ``anchor / all-controls / shared-chain``
schedule. Every three-example sliding window therefore contains a canonical
two-color scene, a scene that separates the true rule from color/orientation
shortcuts, and a lawful overlapping chain that refutes the historical
"targets must be isolated" shortcut.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "1409f5f7af2e"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "f34e705e21f3"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.45

SUMMARY = (
    "For every interior black cell, inspect the cells immediately above and "
    "below it in the same column. Recolor the black cell red iff both neighbors "
    "are green; preserve the green endpoints and every other cell."
)

INVARIANTS = [
    "background is black (0), input contains green (3), and red (2) is output-only",
    "every ordinary scene has three through six visible green-black-green vertical targets",
    "at least one green cell is harmless and must remain unchanged",
    "all-controls scenes also contain a horizontal green gap, a blocked green gap, and a non-green equal-color vertical gap",
    "shared-chain scenes contain at least two targets that reuse one green endpoint",
    "every three consecutive scheduled samples include an anchor, all controls, and a shared chain",
]

SCENE_PROFILES = ("canonical_anchor", "all_controls", "shared_chain")
_PROFILE_PATTERN = SCENE_PROFILES
_DIMENSION_PATTERN = ((10, 10), (11, 11), (11, 10))
_PAIR_PATTERN = {
    "easy": (3, 3, 4),
    "medium": (4, 4, 5),
    "hard": (5, 5, 6),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three-slot profile schedule",
        "valid": "9..11",
    },
    "grid_w": {
        "type": "int",
        "default": "three-slot profile schedule",
        "valid": "9..11",
    },
    "n_pairs": {
        "type": "int",
        "default": "difficulty-aware three-slot schedule",
        "valid": "3..6",
    },
    "scene_profile": {
        "type": "str",
        "default": "anchor|all-controls|shared-chain schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
}

SCHEDULE_PROFILES = SCENE_PROFILES
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Expose the deterministic three-profile lesson schedule."""
    del seed, difficulty
    return _PROFILE_PATTERN[int(sample_index) % len(_PROFILE_PATTERN)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(
            f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}"
        )
    for name, lo, hi in (
        ("grid_h", 9, 11),
        ("grid_w", 9, 11),
        ("n_pairs", 3, 6),
    ):
        value = overrides.get(name)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError(
            f"scene_profile must be one of {SCENE_PROFILES}, found {profile!r}"
        )
    return band


def _draw_axis_int(ctx: Any, name: str, default: int, lo: int, hi: int, overrides: dict[str, Any]) -> int:
    if name in overrides and overrides[name] is not None:
        return int(ctx.draw_int(name, lo, hi))
    return int(ctx.draw_int(name, default, default))


def _draw_profile(ctx: Any, default: str, overrides: dict[str, Any]) -> str:
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        return str(ctx.draw_choice("scene_profile", SCENE_PROFILES))
    return str(ctx.draw_choice("scene_profile", (default,)))


def _target_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    return [
        (row, col)
        for row in range(1, height - 1)
        for col in range(width)
        if (
            grid[row][col] == 0
            and grid[row - 1][col] == 3
            and grid[row + 1][col] == 3
        )
    ]


def _target_endpoints(grid: list[list[int]]) -> set[tuple[int, int]]:
    endpoints: set[tuple[int, int]] = set()
    for row, col in _target_cells(grid):
        endpoints.add((row - 1, col))
        endpoints.add((row + 1, col))
    return endpoints


def _target_endpoint_usage(grid: list[list[int]]) -> dict[tuple[int, int], int]:
    usage: dict[tuple[int, int], int] = {}
    for row, col in _target_cells(grid):
        for endpoint in ((row - 1, col), (row + 1, col)):
            usage[endpoint] = usage.get(endpoint, 0) + 1
    return usage


def _shared_target_endpoints(grid: list[list[int]]) -> set[tuple[int, int]]:
    return {
        endpoint
        for endpoint, count in _target_endpoint_usage(grid).items()
        if count > 1
    }


def _has_shared_target_endpoint(grid: list[list[int]]) -> bool:
    return bool(_shared_target_endpoints(grid))


def _harmless_green_count(grid: list[list[int]]) -> int:
    endpoints = _target_endpoints(grid)
    return sum(
        value == 3 and (row, col) not in endpoints
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
    )


def _horizontal_only_green_gap(grid: list[list[int]]) -> bool:
    targets = set(_target_cells(grid))
    height, width = len(grid), len(grid[0])
    return any(
        grid[row][col] == 0
        and grid[row][col - 1] == 3
        and grid[row][col + 1] == 3
        and (row, col) not in targets
        for row in range(height)
        for col in range(1, width - 1)
    )


def _blocked_vertical_green_gap(grid: list[list[int]]) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        grid[row - 1][col] == 3
        and grid[row + 1][col] == 3
        and grid[row][col] not in (0, 3)
        for row in range(1, height - 1)
        for col in range(width)
    )


def _other_color_vertical_gap(grid: list[list[int]]) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        grid[row][col] == 0
        and grid[row - 1][col] == grid[row + 1][col]
        and grid[row - 1][col] not in (0, 2, 3)
        for row in range(1, height - 1)
        for col in range(width)
    )


def _profile_of(grid: list[list[int]]) -> str | None:
    colors = {value for row in grid for value in row}
    has_horizontal = _horizontal_only_green_gap(grid)
    has_blocked = _blocked_vertical_green_gap(grid)
    has_other = _other_color_vertical_gap(grid)
    if colors == {0, 3} and not (has_horizontal or has_blocked or has_other):
        return "shared_chain" if _has_shared_target_endpoint(grid) else "canonical_anchor"
    if has_horizontal and has_blocked and has_other:
        return "all_controls"
    return None


def _place_pattern(
    grid: list[list[int]],
    cells: list[tuple[int, int, int]],
) -> bool:
    if any(grid[row][col] != 0 for row, col, _ in cells):
        return False
    for row, col, value in cells:
        grid[row][col] = value
    return True


def _place_shared_chain(
    grid: list[list[int]],
    target_count: int,
    rng: Any,
) -> bool:
    """Place the longest lawful alternating vertical chain for this scene."""
    height, width = len(grid), len(grid[0])
    chain_targets = min(target_count, (height - 1) // 2)
    if chain_targets < 2:
        return False
    span = 2 * chain_targets + 1
    for _ in range(100):
        row0 = rng.randrange(height - span + 1)
        col = rng.randrange(width)
        cells = [(row0 + 2 * offset, col, 3) for offset in range(chain_targets + 1)]
        if not _place_pattern(grid, cells):
            continue
        if len(_target_cells(grid)) == chain_targets and _has_shared_target_endpoint(grid):
            return True
        for row, column, _ in cells:
            grid[row][column] = 0
    return False


def _place_all_controls(grid: list[list[int]], rng: Any) -> bool:
    """Place three disjoint controls without creating a true target."""
    height, width = len(grid), len(grid[0])
    for _ in range(200):
        candidate = full_grid(height, width, 0)

        row = rng.randrange(height)
        col = rng.randrange(width - 2)
        if not _place_pattern(candidate, [(row, col, 3), (row, col + 2, 3)]):
            continue

        row = rng.randrange(height - 2)
        col = rng.randrange(width)
        if not _place_pattern(
            candidate,
            [(row, col, 3), (row + 1, col, 5), (row + 2, col, 3)],
        ):
            continue

        row = rng.randrange(height - 2)
        col = rng.randrange(width)
        if not _place_pattern(candidate, [(row, col, 4), (row + 2, col, 4)]):
            continue

        if _target_cells(candidate):
            continue
        if not (
            _horizontal_only_green_gap(candidate)
            and _blocked_vertical_green_gap(candidate)
            and _other_color_vertical_gap(candidate)
        ):
            continue
        for r in range(height):
            grid[r][:] = candidate[r]
        return True
    return False


def _add_exact_targets(grid: list[list[int]], count: int, rng: Any) -> bool:
    height, width = len(grid), len(grid[0])
    centers = [(row, col) for row in range(1, height - 1) for col in range(width)]
    rng.shuffle(centers)
    placed = len(_target_cells(grid))
    for row, col in centers:
        if placed >= count:
            break
        if any(grid[r][col] != 0 for r in (row - 1, row, row + 1)):
            continue
        grid[row - 1][col] = 3
        grid[row + 1][col] = 3
        new_count = len(_target_cells(grid))
        if new_count == placed + 1:
            placed = new_count
        else:
            grid[row - 1][col] = 0
            grid[row + 1][col] = 0
    return placed == count


def _add_harmless_greens(
    grid: list[list[int]],
    wanted: int,
    profile: str,
    target_count: int,
    rng: Any,
) -> bool:
    height, width = len(grid), len(grid[0])
    added = 0
    cells = [(row, col) for row in range(height) for col in range(width)]
    rng.shuffle(cells)
    for row, col in cells:
        if added >= wanted:
            break
        if grid[row][col] != 0:
            continue
        before = _profile_of(grid)
        grid[row][col] = 3
        if len(_target_cells(grid)) != target_count:
            grid[row][col] = 0
            continue
        after = _profile_of(grid)
        if profile == "canonical_anchor" and after != "canonical_anchor":
            grid[row][col] = 0
            continue
        if profile == "all_controls" and after != "all_controls":
            grid[row][col] = 0
            continue
        # The new green must itself be harmless, not merely preserve the count.
        if (row, col) in _target_endpoints(grid):
            grid[row][col] = 0
            continue
        if before == after or after == profile:
            added += 1
    return added == wanted


def _build_scene(
    height: int,
    width: int,
    n_pairs: int,
    profile: str,
    rng: Any,
) -> list[list[int]]:
    for _ in range(400):
        grid = full_grid(height, width, 0)
        if profile == "all_controls" and not _place_all_controls(grid, rng):
            continue
        if profile == "shared_chain" and not _place_shared_chain(grid, n_pairs, rng):
            continue
        if not _add_exact_targets(grid, n_pairs, rng):
            continue
        decoys = 2 + rng.randrange(3)
        if not _add_harmless_greens(grid, decoys, profile, n_pairs, rng):
            continue
        if _profile_of(grid) != profile:
            continue
        if len(_target_cells(grid)) != n_pairs:
            continue
        if _harmless_green_count(grid) < 1:
            continue
        errors = self_check(grid)
        if errors:
            continue
        return grid
    raise ValueError(
        f"could not construct {profile} scene {height}x{width} with {n_pairs} targets"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    slot = int(sample_index) % len(_PROFILE_PATTERN)
    default_h, default_w = _DIMENSION_PATTERN[slot]
    default_pairs = _PAIR_PATTERN[band][slot]
    default_profile = _PROFILE_PATTERN[slot]

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height = _draw_axis_int(ctx, "grid_h", default_h, 9, 11, overrides)
    width = _draw_axis_int(ctx, "grid_w", default_w, 9, 11, overrides)
    n_pairs = _draw_axis_int(ctx, "n_pairs", default_pairs, 3, 6, overrides)
    profile = _draw_profile(ctx, default_profile, overrides)

    grid = _build_scene(
        height,
        width,
        n_pairs,
        profile,
        ctx.draw_rng("layout"),
    )
    observed = observe_overrides(grid)
    requested = {
        "grid_h": height,
        "grid_w": width,
        "n_pairs": n_pairs,
        "scene_profile": profile,
    }
    if observed != requested:
        raise RuntimeError(
            f"internal override-observation mismatch: requested={requested}, observed={observed}"
        )
    return grid


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    height = len(grid)
    errors: list[str] = []
    if not (3 <= height <= 30 and 3 <= width <= 30):
        errors.append(f"grid dimensions must be within 3..30, found {height}x{width}")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
    return errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical-compatible input grammar, not curriculum extras."""
    del difficulty, meta
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    flat = [value for row in grid for value in row]
    colors = set(flat)
    zero_count = flat.count(0)
    targets = _target_cells(grid)

    if 0 not in colors or 3 not in colors:
        errors.append("input must contain black background and green cue cells")
    if 2 in colors:
        errors.append("red 2 is output-only and must not appear in the input")
    if zero_count <= len(flat) // 2:
        errors.append("black 0 must be the modal sparse background")
    if not 3 <= len(targets) <= 6:
        errors.append(
            f"expected three through six vertical green-black-green targets, found {len(targets)}"
        )
    if _harmless_green_count(grid) < 1:
        errors.append("need at least one harmless green cue that is not a target endpoint")
    if zero_count - len(targets) < max(1, (height * width) // 4):
        errors.append("too few unchanged black cells to make target selection visible")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the exact public scale/palette manifold plus its lawful geometry."""
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]))
    if profile not in {(9, 9), (10, 10)}:
        errors.append(f"dimensions {profile} are outside canonical 9x9/10x10 profiles")
    colors = {value for row in grid for value in row}
    if colors != {0, 3}:
        errors.append(f"canonical inputs use exactly colors {{0,3}}, found {sorted(colors)}")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    profile = _profile_of(grid)
    if profile is None:
        raise ValueError("grid does not encode a declared scene_profile")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(_target_cells(grid)),
        "scene_profile": profile,
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror used only for tests and rival analysis."""
    errors = _basic_grid_errors(grid)
    if errors:
        raise ValueError("invalid input: " + "; ".join(errors))
    output = deepcopy(grid)
    for row, col in _target_cells(grid):
        output[row][col] = 2
    return output


def _rival_identity(grid: list[list[int]]) -> list[list[int]]:
    return deepcopy(grid)


def _rival_any_equal_vertical(grid: list[list[int]]) -> list[list[int]]:
    output = deepcopy(grid)
    for row in range(1, len(grid) - 1):
        for col in range(len(grid[0])):
            if (
                grid[row][col] == 0
                and grid[row - 1][col] == grid[row + 1][col]
                and grid[row - 1][col] != 0
            ):
                output[row][col] = 2
    return output


def _rival_horizontal_or_vertical(grid: list[list[int]]) -> list[list[int]]:
    output = rule_mirror(grid)
    for row in range(len(grid)):
        for col in range(1, len(grid[0]) - 1):
            if grid[row][col] == 0 and grid[row][col - 1] == 3 and grid[row][col + 1] == 3:
                output[row][col] = 2
    return output


def _rival_fill_blocked_gap(grid: list[list[int]]) -> list[list[int]]:
    output = deepcopy(grid)
    for row in range(1, len(grid) - 1):
        for col in range(len(grid[0])):
            if grid[row - 1][col] == 3 and grid[row + 1][col] == 3:
                output[row][col] = 2
    return output


def _rival_recolor_all_green(grid: list[list[int]]) -> list[list[int]]:
    return [[2 if value == 3 else value for value in row] for row in grid]


def _rival_same_count_first_zeros(grid: list[list[int]]) -> list[list[int]]:
    output = deepcopy(grid)
    remaining = len(_target_cells(grid))
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if remaining and grid[row][col] == 0:
                output[row][col] = 2
                remaining -= 1
    return output


def _rival_isolated_targets_only(grid: list[list[int]]) -> list[list[int]]:
    """Historical shortcut: refuse targets that reuse a green endpoint."""
    output = deepcopy(grid)
    usage = _target_endpoint_usage(grid)
    for row, col in _target_cells(grid):
        if usage[(row - 1, col)] == 1 and usage[(row + 1, col)] == 1:
            output[row][col] = 2
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity_no_fill": _rival_identity,
    "any_equal_color_vertical_gap": _rival_any_equal_vertical,
    "horizontal_or_vertical_green_gap": _rival_horizontal_or_vertical,
    "fill_even_when_middle_is_nonblack": _rival_fill_blocked_gap,
    "recolor_green_markers": _rival_recolor_all_green,
    "same_count_first_black_cells": _rival_same_count_first_zeros,
    "isolated_targets_only": _rival_isolated_targets_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "any_equal_color_vertical_gap": _rival_any_equal_vertical,
    "horizontal_or_vertical_green_gap": _rival_horizontal_or_vertical,
    "same_count_first_black_cells": _rival_same_count_first_zeros,
    "isolated_targets_only": _rival_isolated_targets_only,
}


def _witness_targets(grid: list[list[int]]) -> bool:
    return not self_check(grid) and bool(_target_cells(grid))


def _witness_harmless_green(grid: list[list[int]]) -> bool:
    return not self_check(grid) and _harmless_green_count(grid) > 0


def _witness_horizontal_only(grid: list[list[int]]) -> bool:
    return not self_check(grid) and _horizontal_only_green_gap(grid)


def _witness_blocked_gap(grid: list[list[int]]) -> bool:
    return not self_check(grid) and _blocked_vertical_green_gap(grid)


def _witness_other_color_gap(grid: list[list[int]]) -> bool:
    return not self_check(grid) and _other_color_vertical_gap(grid)


def _witness_shared_endpoint_chain(grid: list[list[int]]) -> bool:
    return not self_check(grid) and _has_shared_target_endpoint(grid)


SEMANTIC_WITNESSES = {
    "active_vertical_green_black_green_targets": _witness_targets,
    "harmless_green_cue_stays_green": _witness_harmless_green,
    "horizontal_green_gap_stays_black": _witness_horizontal_only,
    "blocked_vertical_green_gap_preserves_middle": _witness_blocked_gap,
    "non_green_equal_vertical_gap_stays_black": _witness_other_color_gap,
    "shared_endpoint_chain_targets_still_fill": _witness_shared_endpoint_chain,
}
WITNESS_RIVALS = {
    "active_vertical_green_black_green_targets": ["identity_no_fill"],
    "harmless_green_cue_stays_green": ["recolor_green_markers"],
    "horizontal_green_gap_stays_black": ["horizontal_or_vertical_green_gap"],
    "blocked_vertical_green_gap_preserves_middle": ["fill_even_when_middle_is_nonblack"],
    "non_green_equal_vertical_gap_stays_black": ["any_equal_color_vertical_gap"],
    "shared_endpoint_chain_targets_still_fill": ["isolated_targets_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named rival fits every demo but changes the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    refuted = {name: False for name in LESSON_COMPETITORS}
    profiles: set[str] = set()

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match the task rule")
            continue
        observed_profile = _profile_of(pair["input"])
        if observed_profile is not None:
            profiles.add(observed_profile)
        for name, competitor in LESSON_COMPETITORS.items():
            if competitor(pair["input"]) != expected:
                refuted[name] = True

    if "canonical_anchor" not in profiles:
        reasons.append("demonstrations need a canonical two-color anchor")
    if "all_controls" not in profiles:
        reasons.append("demonstrations need an all-controls counterexample scene")
    if "shared_chain" not in profiles:
        reasons.append("demonstrations need a shared-endpoint target chain")
    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input invalid: {query_errors[0]}")
        return reasons
    truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != truth:
        reasons.append("query output does not match the task rule")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(
            isinstance(pair, dict)
            and {"input", "output"} <= set(pair)
            and competitor(pair["input"]) == pair["output"]
            for pair in demos
        ) and competitor(query["input"]) != truth:
            reasons.append(
                f"competing rule {name!r} fits every demo but predicts a different query"
            )
    return reasons
