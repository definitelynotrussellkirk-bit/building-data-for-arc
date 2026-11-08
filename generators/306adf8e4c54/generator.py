"""Semantic generator for ARC task 306adf8e4c54 (One-Gap Completion).

The authoritative rule is a *single simultaneous pass* over the original grid.
A zero cell becomes yellow(4) exactly when its immediate left/right neighbors
or its immediate up/down neighbors are both yellow.  Nonzero midpoints, wider
separations, and sandwiches made from any other color remain unchanged.

A four-example schedule makes the rule identifiable rather than merely
executable:

* ``canonical_7x7`` includes both axes and an active gap attached to an
  adjacent yellow cell, matching the public demonstrations.
* ``chain_8x8`` includes two active gaps on one line plus a wider-distance
  negative control.
* ``controls_9x9`` includes a blocked yellow sandwich and a same-color
  non-yellow sandwich, both of which must be preserved.
* ``noncascade_8x9`` includes a cell that would fire only on a second pass,
  distinguishing the canonical simultaneous rule from iterative closure.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "306adf8e4c54"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "aff0e8ed7bbb"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "In one simultaneous pass, fill a zero cell yellow(4) exactly when its "
    "immediate horizontal or vertical neighbors are both yellow. Preserve "
    "blocked midpoints, wider separations, other-color sandwiches, and cells "
    "that would become eligible only after an earlier fill."
)

INVARIANTS = [
    "the grid is rectangular and uses literal ARC colors 0..9",
    "at least one zero cell is immediately bracketed by yellow(4) horizontally or vertically",
    "the authoritative transform reads every condition from the original input",
    "nonzero midpoint cells and non-yellow endpoint colors are preserved",
    "every four consecutive samples cover all four semantic curriculum profiles",
]

SCENE_PROFILES = (
    "canonical_7x7",
    "chain_8x8",
    "controls_9x9",
    "noncascade_8x9",
)
SCHEDULE_PROFILES = SCENE_PROFILES
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-example semantic schedule keyed by sample_index",
        "valid": "|".join(SCENE_PROFILES),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_PROFILE_SHAPES = {
    "canonical_7x7": (7, 7),
    "chain_8x8": (8, 8),
    "controls_9x9": (9, 9),
    "noncascade_8x9": (8, 9),
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every four consecutive sample indices visit all semantic profiles."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if "scene_profile" in overrides and overrides["scene_profile"] not in SCENE_PROFILES:
        raise ValueError(
            f"scene_profile must be one of {SCENE_PROFILES}, "
            f"found {overrides['scene_profile']!r}"
        )


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    errors: list[str] = []
    if not 3 <= len(grid) <= 30 or not 3 <= width <= 30:
        errors.append(f"grid dimensions must be in 3..30, found {len(grid)}x{width}")
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} does not have width {width}")
            continue
        for col_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{col_index}) is not a literal ARC color 0..9: {value!r}"
                )
    return errors


def _bracketed_by_four(grid: list[list[int]], row: int, col: int, axis: str) -> bool:
    height, width = len(grid), len(grid[0])
    if axis == "h":
        return 0 < col < width - 1 and grid[row][col - 1] == grid[row][col + 1] == 4
    return 0 < row < height - 1 and grid[row - 1][col] == grid[row + 1][col] == 4


def _active_orientations(grid: list[list[int]]) -> dict[tuple[int, int], frozenset[str]]:
    active: dict[tuple[int, int], frozenset[str]] = {}
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] != 0:
                continue
            axes = {
                axis for axis in ("h", "v")
                if _bracketed_by_four(grid, row, col, axis)
            }
            if axes:
                active[(row, col)] = frozenset(axes)
    return active


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the selected single-pass Racket authority."""
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    for (row, col), _axes in _active_orientations(source).items():
        output[row][col] = 4
    return output


def _rival_horizontal_only(grid: list[list[int]]) -> list[list[int]]:
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    for (row, col), axes in _active_orientations(source).items():
        if "h" in axes:
            output[row][col] = 4
    return output


def _rival_vertical_only(grid: list[list[int]]) -> list[list[int]]:
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    for (row, col), axes in _active_orientations(source).items():
        if "v" in axes:
            output[row][col] = 4
    return output


def _rival_any_equal_nonzero(grid: list[list[int]]) -> list[list[int]]:
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])
    for row in range(height):
        for col in range(width):
            if source[row][col] != 0:
                continue
            replacement = None
            if 0 < col < width - 1:
                left, right = source[row][col - 1], source[row][col + 1]
                if left == right != 0:
                    replacement = left
            if replacement is None and 0 < row < height - 1:
                above, below = source[row - 1][col], source[row + 1][col]
                if above == below != 0:
                    replacement = above
            if replacement is not None:
                output[row][col] = replacement
    return output


def _rival_overwrite_blocked_midpoints(grid: list[list[int]]) -> list[list[int]]:
    source = [list(row) for row in grid]
    output = rule_mirror(source)
    for row in range(len(source)):
        for col in range(len(source[0])):
            if _bracketed_by_four(source, row, col, "h") or _bracketed_by_four(
                source, row, col, "v"
            ):
                output[row][col] = 4
    return output


def _rival_connect_all_aligned_fours(grid: list[list[int]]) -> list[list[int]]:
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])
    for row in range(height):
        columns = [col for col in range(width) if source[row][col] == 4]
        for left_index, left in enumerate(columns):
            for right in columns[left_index + 1 :]:
                for col in range(left + 1, right):
                    if source[row][col] == 0:
                        output[row][col] = 4
    for col in range(width):
        rows = [row for row in range(height) if source[row][col] == 4]
        for top_index, top in enumerate(rows):
            for bottom in rows[top_index + 1 :]:
                for row in range(top + 1, bottom):
                    if source[row][col] == 0:
                        output[row][col] = 4
    return output


def _rival_isolated_pairs_only(grid: list[list[int]]) -> list[list[int]]:
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])
    for (row, col), axes in _active_orientations(source).items():
        qualifies = False
        if "h" in axes:
            outer_left = source[row][col - 2] if col >= 2 else 0
            outer_right = source[row][col + 2] if col + 2 < width else 0
            qualifies |= outer_left != 4 and outer_right != 4
        if "v" in axes:
            outer_top = source[row - 2][col] if row >= 2 else 0
            outer_bottom = source[row + 2][col] if row + 2 < height else 0
            qualifies |= outer_top != 4 and outer_bottom != 4
        if qualifies:
            output[row][col] = 4
    return output


def _rival_first_per_line(grid: list[list[int]]) -> list[list[int]]:
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    active = _active_orientations(source)
    for row in range(len(source)):
        candidates = sorted(col for (rr, col), axes in active.items() if rr == row and "h" in axes)
        if candidates:
            output[row][candidates[0]] = 4
    for col in range(len(source[0])):
        candidates = sorted(row for (row, cc), axes in active.items() if cc == col and "v" in axes)
        if candidates:
            output[candidates[0]][col] = 4
    return output


def _rival_iterative_closure(grid: list[list[int]]) -> list[list[int]]:
    current = [list(row) for row in grid]
    for _ in range(len(current) * len(current[0])):
        updated = rule_mirror(current)
        if updated == current:
            return updated
        current = updated
    return current


def _different_cells(first: list[list[int]], second: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row in range(len(first))
        for col in range(len(first[0]))
        if first[row][col] != second[row][col]
    ]


def _infer_profile(
    height: int, width: int, palette: set[int]
) -> str | None:
    if (height, width) == (7, 7) and palette.issubset({0, 4}):
        return "canonical_7x7"
    if (height, width) == (8, 8) and palette.issubset({0, 4}):
        return "chain_8x8"
    if (height, width) == (9, 9) and bool(palette - {0, 4}):
        return "controls_9x9"
    if (height, width) == (8, 9) and palette.issubset({0, 4}):
        return "noncascade_8x9"
    return None


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    source = [list(row) for row in grid]
    height, width = len(source), len(source[0])
    palette = {value for row in source for value in row}
    active = _active_orientations(source)
    official = rule_mirror(source)

    blocked: set[tuple[int, int]] = set()
    nonfour: set[tuple[int, int]] = set()
    for row in range(height):
        for col in range(width):
            value = source[row][col]
            if value not in (0, 4) and (
                _bracketed_by_four(source, row, col, "h")
                or _bracketed_by_four(source, row, col, "v")
            ):
                blocked.add((row, col))
            # A color-specific negative control must be causal, not merely
            # present geometrically.  If this midpoint is also an active 4-0-4
            # gap on the orthogonal axis, both the canonical rule and the
            # any-equal-nonzero rival write 4, so the decoy teaches nothing.
            if value == 0 and (row, col) not in active:
                if 0 < col < width - 1:
                    left, right = source[row][col - 1], source[row][col + 1]
                    if left == right and left not in (0, 4):
                        nonfour.add((row, col))
                if 0 < row < height - 1:
                    above, below = source[row - 1][col], source[row + 1][col]
                    if above == below and above not in (0, 4):
                        nonfour.add((row, col))

    connect_all = _rival_connect_all_aligned_fours(source)
    long_controls = set(_different_cells(official, connect_all))
    iterative = _rival_iterative_closure(source)
    cascade_only = set(_different_cells(official, iterative))

    horizontal_single = sorted(
        position for position, axes in active.items() if axes == frozenset({"h"})
    )
    vertical_single = sorted(
        position for position, axes in active.items() if axes == frozenset({"v"})
    )
    both_axes = sorted(
        position for position, axes in active.items() if axes == frozenset({"h", "v"})
    )

    return {
        "errors": [],
        "height": height,
        "width": width,
        "palette": palette,
        "scene_profile": _infer_profile(height, width, palette),
        "active": active,
        "horizontal_single_axis": horizontal_single,
        "vertical_single_axis": vertical_single,
        "both_axes": both_axes,
        "blocked_midpoints": sorted(blocked),
        "nonfour_sandwiches": sorted(nonfour),
        "long_distance_controls": sorted(long_controls),
        "cascade_only_cells": sorted(cascade_only),
        "adjacent_anchor_difference": bool(
            _different_cells(official, _rival_isolated_pairs_only(source))
        ),
        "multiple_same_line_difference": bool(
            _different_cells(official, _rival_first_per_line(source))
        ),
    }


def _requested_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    requested: dict[str, Any] = {}
    if isinstance(meta.get("overrides"), dict):
        requested.update(meta["overrides"])
    for name in AXES:
        if name in meta:
            requested[name] = meta[name]
    return requested


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the authority domain while rejecting identity/rule-hiding scenes."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if not analysis["active"]:
        errors.append("at least one active yellow 4-0-4 gap is required")
    requested = _requested_overrides(meta)
    if requested:
        observed = observe_overrides(grid)
        for name, expected in requested.items():
            if name in AXES and observed.get(name) != expected:
                errors.append(
                    f"override {name}={expected!r} realized as {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Characterise the shared profile of all three public inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis = _analyze(grid)
    if (analysis["height"], analysis["width"]) not in {(7, 7), (8, 8), (9, 9)}:
        reasons.append(
            f"shape {analysis['height']}x{analysis['width']} is not a canonical shape"
        )
    if analysis["palette"] != {0, 4}:
        reasons.append(f"canonical palette is exactly {{0, 4}}, found {sorted(analysis['palette'])}")
    if not any("h" in axes for axes in analysis["active"].values()):
        reasons.append("canonical inputs contain a horizontal active gap")
    if not any("v" in axes for axes in analysis["active"].values()):
        reasons.append("canonical inputs contain a vertical active gap")
    return reasons


def observe_overrides(grid) -> dict[str, str | None]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def _line_coords(
    row: int, col: int, axis: str, length: int
) -> list[tuple[int, int]]:
    if axis == "h":
        return [(row, col + offset) for offset in range(length)]
    return [(row + offset, col) for offset in range(length)]


def _place_random_line(
    grid: list[list[int]],
    occupied: set[tuple[int, int]],
    values: Iterable[int],
    axis: str,
    rng,
    *,
    attempts: int = 160,
) -> bool:
    values = tuple(values)
    height, width = len(grid), len(grid[0])
    for _ in range(attempts):
        if axis == "h":
            row = rng.randrange(height)
            col = rng.randrange(width - len(values) + 1)
        else:
            row = rng.randrange(height - len(values) + 1)
            col = rng.randrange(width)
        coords = _line_coords(row, col, axis, len(values))
        if any(position in occupied for position in coords):
            continue
        for (rr, cc), value in zip(coords, values):
            grid[rr][cc] = value
        occupied.update(coords)
        return True
    return False


def _place_cascade(
    grid: list[list[int]], occupied: set[tuple[int, int]], rng
) -> str | None:
    """Place A<-trigger and A,zero,4 so only a second pass fills the latter."""
    height, width = len(grid), len(grid[0])
    for _ in range(200):
        mode = rng.choice(("vertical_trigger", "horizontal_trigger"))
        if mode == "vertical_trigger":
            row = rng.randrange(1, height - 1)
            col = rng.randrange(0, width - 2)
            coords = {
                (row - 1, col),
                (row, col),
                (row + 1, col),
                (row, col + 1),
                (row, col + 2),
            }
            if coords & occupied:
                continue
            grid[row - 1][col] = 4
            grid[row + 1][col] = 4
            grid[row][col + 2] = 4
            occupied.update(coords)
            return "v"
        row = rng.randrange(0, height - 2)
        col = rng.randrange(1, width - 1)
        coords = {
            (row, col - 1),
            (row, col),
            (row, col + 1),
            (row + 1, col),
            (row + 2, col),
        }
        if coords & occupied:
            continue
        grid[row][col - 1] = 4
        grid[row][col + 1] = 4
        grid[row + 2][col] = 4
        occupied.update(coords)
        return "h"
    return None


def _profile_reasons(profile: str, grid: list[list[int]]) -> list[str]:
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if analysis["scene_profile"] != profile:
        reasons.append(
            f"profile signature is {analysis['scene_profile']!r}, expected {profile!r}"
        )
    if not analysis["horizontal_single_axis"]:
        reasons.append("profile lacks a horizontal-only active gap")
    if not analysis["vertical_single_axis"]:
        reasons.append("profile lacks a vertical-only active gap")
    if profile == "canonical_7x7":
        if not analysis["adjacent_anchor_difference"]:
            reasons.append("canonical profile lacks an active adjacent-anchor control")
    elif profile == "chain_8x8":
        if not analysis["multiple_same_line_difference"]:
            reasons.append("chain profile lacks multiple active gaps on one line")
        if not analysis["long_distance_controls"]:
            reasons.append("chain profile lacks a wider-distance negative control")
    elif profile == "controls_9x9":
        if not analysis["blocked_midpoints"]:
            reasons.append("controls profile lacks a blocked yellow midpoint")
        if not analysis["nonfour_sandwiches"]:
            reasons.append("controls profile lacks a non-yellow sandwich")
        if not analysis["long_distance_controls"]:
            reasons.append("controls profile lacks a wider-distance negative control")
    elif profile == "noncascade_8x9":
        if not analysis["cascade_only_cells"]:
            reasons.append("noncascade profile lacks a second-pass-only cell")
    return reasons


def _construct_profile(profile: str, rng) -> list[list[int]] | None:
    height, width = _PROFILE_SHAPES[profile]
    grid = full_grid(height, width, 0)
    occupied: set[tuple[int, int]] = set()

    if profile == "canonical_7x7":
        first_axis = rng.choice(("h", "v"))
        second_axis = "v" if first_axis == "h" else "h"
        if not _place_random_line(grid, occupied, (4, 4, 0, 4), first_axis, rng):
            return None
        if not _place_random_line(grid, occupied, (4, 0, 4), second_axis, rng):
            return None

    elif profile == "chain_8x8":
        chain_axis = rng.choice(("h", "v"))
        other_axis = "v" if chain_axis == "h" else "h"
        if not _place_random_line(grid, occupied, (4, 0, 4, 0, 4), chain_axis, rng):
            return None
        if not _place_random_line(grid, occupied, (4, 0, 4), other_axis, rng):
            return None
        if not _place_random_line(
            grid, occupied, (4, 0, 0, 4), rng.choice(("h", "v")), rng
        ):
            return None

    elif profile == "controls_9x9":
        colors = list(range(1, 10))
        colors.remove(4)
        blocker, decoy = rng.sample(colors, 2)
        patterns = [
            ((4, 0, 4), "h"),
            ((4, 0, 4), "v"),
            ((4, blocker, 4), rng.choice(("h", "v"))),
            ((decoy, 0, decoy), rng.choice(("h", "v"))),
            ((4, 0, 0, 4), rng.choice(("h", "v"))),
        ]
        for values, axis in patterns:
            if not _place_random_line(grid, occupied, values, axis, rng):
                return None

    else:
        trigger_axis = _place_cascade(grid, occupied, rng)
        if trigger_axis is None:
            return None
        other_axis = "h" if trigger_axis == "v" else "v"
        if not _place_random_line(grid, occupied, (4, 0, 4), other_axis, rng):
            return None

    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    effective_overrides = dict(overrides)
    effective_overrides.setdefault("scene_profile", scheduled)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    layout_code = ctx.draw_int_diff("layout_code", 0, 1_000_000)
    rng = ctx.draw_rng(f"layout:{profile}:{layout_code}")

    for _ in range(600):
        grid = _construct_profile(profile, rng)
        if grid is None:
            continue
        if not _profile_reasons(profile, grid):
            return grid
    raise RuntimeError(f"could not construct semantic profile {profile!r}")


def _witness_horizontal_single_axis(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and bool(analysis["horizontal_single_axis"])


def _witness_vertical_single_axis(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and bool(analysis["vertical_single_axis"])


def _rival_differs(rival: Callable, grid: Any) -> bool:
    if _grid_errors(grid):
        return False
    source = [list(row) for row in grid]
    return rival(source) != rule_mirror(source)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "any_equal_nonzero_color": _rival_any_equal_nonzero,
    "overwrite_blocked_midpoints": _rival_overwrite_blocked_midpoints,
    "connect_all_aligned_fours": _rival_connect_all_aligned_fours,
    "isolated_pairs_only": _rival_isolated_pairs_only,
    "first_gap_per_line_only": _rival_first_per_line,
    "iterative_closure": _rival_iterative_closure,
}

SEMANTIC_WITNESSES: dict[str, Callable] = {
    "horizontal_single_axis_gap": _witness_horizontal_single_axis,
    "vertical_single_axis_gap": _witness_vertical_single_axis,
    "yellow_is_color_specific": lambda grid: _rival_differs(
        _rival_any_equal_nonzero, grid
    ),
    "blocked_midpoint_is_preserved": lambda grid: _rival_differs(
        _rival_overwrite_blocked_midpoints, grid
    ),
    "only_one_cell_distance_fires": lambda grid: _rival_differs(
        _rival_connect_all_aligned_fours, grid
    ),
    "adjacent_anchor_still_fires": lambda grid: _rival_differs(
        _rival_isolated_pairs_only, grid
    ),
    "all_gaps_on_a_line_fire": lambda grid: _rival_differs(
        _rival_first_per_line, grid
    ),
    "single_pass_not_iterative": lambda grid: _rival_differs(
        _rival_iterative_closure, grid
    ),
}

WITNESS_RIVALS = {
    "horizontal_single_axis_gap": ["vertical_only"],
    "vertical_single_axis_gap": ["horizontal_only"],
    "yellow_is_color_specific": ["any_equal_nonzero_color"],
    "blocked_midpoint_is_preserved": ["overwrite_blocked_midpoints"],
    "only_one_cell_distance_fires": ["connect_all_aligned_fours"],
    "adjacent_anchor_still_fires": ["isolated_pairs_only"],
    "all_gaps_on_a_line_fire": ["first_gap_per_line_only"],
    "single_pass_not_iterative": ["iterative_closure"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Report every named rival that the demonstrations fail to eliminate."""
    reasons: list[str] = []
    valid_demos = [
        pair
        for pair in demos
        if isinstance(pair, dict) and "input" in pair and "output" in pair
    ]
    if not valid_demos:
        return ["no valid demonstrations were supplied"]
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(pair["input"]) == pair["output"] for pair in valid_demos
            )
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            suffix = ""
            if isinstance(query, dict) and "input" in query and "output" in query:
                try:
                    suffix = (
                        " and changes the query"
                        if competitor(query["input"]) != query["output"]
                        else " and also survives the query"
                    )
                except Exception:
                    suffix = ""
            reasons.append(f"declared competitor survives demonstrations: {name}{suffix}")
    return reasons


def mutation_fixtures() -> list[tuple[str, Any]]:
    blank = full_grid(7, 7, 0)

    adjacent_only = full_grid(7, 7, 0)
    adjacent_only[3][2] = adjacent_only[3][3] = 4

    nonfour_only = full_grid(7, 7, 0)
    nonfour_only[2][1] = nonfour_only[2][3] = 6

    invalid_color = full_grid(7, 7, 0)
    invalid_color[2][1] = invalid_color[2][3] = 4
    invalid_color[0][0] = 10

    ragged = [[0, 4, 0, 4], [0, 0, 0]]

    return [
        ("blank_identity_scene", blank),
        ("adjacent_without_gap", adjacent_only),
        ("nonfour_sandwich_without_yellow_trigger", nonfour_only),
        ("invalid_arc_color", invalid_color),
        ("ragged_grid", ragged),
    ]
