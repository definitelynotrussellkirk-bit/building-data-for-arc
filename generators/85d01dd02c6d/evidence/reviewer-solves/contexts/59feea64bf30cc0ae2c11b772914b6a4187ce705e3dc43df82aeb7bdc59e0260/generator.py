"""Canonical-style sampler for task 85d01dd02c6d (Ray-Overlap Map).

Every ordinary input has an outer color-9 frame and either a canonical full
divider or a three-cell wall segment.  Three distinct singleton seeds are placed
so that an aligned pair is genuinely blocked and another pair creates a positive
>=2-visibility overlap.  Full and partial walls alternate by sample index: this
keeps canonical morphology prominent while ensuring every three-example lesson
refutes the canonical-fitting shortcut that only complete divider lines block.

Gap profiles replace one divider cell with the third seed, matching canonical
examples where a seed is embedded in a wall.  Outputs are produced only by the
unchanged canonical Racket authority; ``rule_mirror`` is an independent Python
oracle used by focused tests and semantic rivals.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "85d01dd02c6d"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "071ab7615984"

FULL_DIVIDER_PROFILES = (
    "vertical_solid",
    "vertical_gap",
    "horizontal_solid",
    "horizontal_gap",
)
SEGMENT_PROFILES = (
    "vertical_segment",
    "horizontal_segment",
)
SCENE_PROFILES = FULL_DIVIDER_PROFILES + SEGMENT_PROFILES

SUMMARY = (
    "A color-9 outer frame contains three distinct seeds and either a canonical "
    "full divider or a short straight wall segment.  An aligned pair proves "
    "that individual 9 cells block line of sight, while another pair proves "
    "the >=2 overlap branch."
)

INVARIANTS = [
    "the outer border is entirely color 9",
    "the internal wall is one full divider (optionally with a seed gap) or one three-cell segment",
    "exactly three distinct singleton seeds use colors outside {0,8,9}",
    "an aligned seed pair is separated by a wall and refutes ignoring walls",
    "short-wall profiles refute the canonical-fitting full-divider-only shortcut",
    "at least one background cell has clear line of sight to at least two seeds",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "uniform 9..11",
        "valid": "9..11",
        "doc": "Exact grid height, including the outer frame.",
    },
    "grid_w": {
        "type": "int",
        "default": "uniform 11..13",
        "valid": "11..13",
        "doc": "Exact grid width, including the outer frame.",
    },
    "scene_profile": {
        "type": "enum",
        "default": "alternating full-divider/short-segment schedule with keyed orientation",
        "valid": "|".join(SCENE_PROFILES),
        "doc": "Wall orientation and morphology; exact overrides bypass the default parity schedule.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
MIN_STRICT_FRAC = 0.45
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("full_divider", "partial_segment")


def _basic_grid_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["every row must be a non-empty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["grid cells must be integer colors 0..9 (bool is not a color)"]
    return []


def _seeds(grid) -> list[tuple[int, int, int]]:
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 9)
    ]


def _visible(grid, seed: tuple[int, int, int], row: int, col: int, *, ignore_walls: bool) -> bool:
    seed_row, seed_col, _ = seed
    if seed_row == row:
        if ignore_walls:
            return True
        return all(
            grid[row][scan_col] != 9
            for scan_col in range(min(seed_col, col), max(seed_col, col) + 1)
        )
    if seed_col == col:
        if ignore_walls:
            return True
        return all(
            grid[scan_row][col] != 9
            for scan_row in range(min(seed_row, row), max(seed_row, row) + 1)
        )
    return False


def _solve(grid, *, threshold: int = 2, ignore_walls: bool = False) -> list[list[int]]:
    errors = _basic_grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    seeds = _seeds(grid)
    height, width = len(grid), len(grid[0])
    return [
        [
            9
            if grid[row][col] == 9
            else 8
            if sum(
                _visible(grid, seed, row, col, ignore_walls=ignore_walls)
                for seed in seeds
            )
            >= threshold
            else 0
            for col in range(width)
        ]
        for row in range(height)
    ]


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of the pinned canonical rule."""
    return _solve(grid, threshold=2, ignore_walls=False)


def _ignore_internal_walls(grid) -> list[list[int]]:
    """Plausible rival: aligned seeds see through every color-9 divider."""
    return _solve(grid, threshold=2, ignore_walls=True)


def _one_seed_suffices(grid) -> list[list[int]]:
    """Plausible threshold rival: paint cells seen by at least one seed."""
    return _solve(grid, threshold=1, ignore_walls=False)


def _profile_options(difficulty: str | None, sample_index: int) -> tuple[str, ...]:
    """Return the default parity-scheduled morphology choices.

    Even indices use canonical full dividers.  Odd indices use short segments,
    so every three consecutive demonstrations and every three-of-four rotation
    includes a counterexample to the full-divider-only canonical shortcut.
    Exact ``scene_profile`` overrides bypass this schedule.
    """
    if sample_index % 2:
        return SEGMENT_PROFILES
    if difficulty == "easy":
        return FULL_DIVIDER_PROFILES + ("vertical_solid", "horizontal_solid")
    if difficulty == "hard":
        return FULL_DIVIDER_PROFILES + ("vertical_gap", "horizontal_gap")
    return FULL_DIVIDER_PROFILES


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return "partial_segment" if sample_index % 2 else "full_divider"


def _paint_outer_frame(grid: list[list[int]]) -> None:
    height, width = len(grid), len(grid[0])
    for col in range(width):
        grid[0][col] = 9
        grid[height - 1][col] = 9
    for row in range(height):
        grid[row][0] = 9
        grid[row][width - 1] = 9


def _build_vertical(
    grid: list[list[int]], profile: str, colors: tuple[int, int, int], rng
) -> None:
    height, width = len(grid), len(grid[0])
    wall_col = rng.choice(tuple(range(4, width - 4)))
    for row in range(height):
        grid[row][wall_col] = 9

    blocked_row = rng.choice(tuple(range(2, height - 2)))
    left_col = rng.choice(tuple(range(2, wall_col)))
    right_col = rng.choice(tuple(range(wall_col + 1, width - 2)))
    grid[blocked_row][left_col] = colors[0]
    grid[blocked_row][right_col] = colors[1]

    if profile == "vertical_gap":
        gap_row = rng.choice(tuple(row for row in range(1, height - 1) if row != blocked_row))
        grid[gap_row][wall_col] = colors[2]
    else:
        extra_row = rng.choice(tuple(row for row in range(1, height - 1) if row != blocked_row))
        extra_col = rng.choice(tuple(col for col in range(1, wall_col) if col != left_col))
        grid[extra_row][extra_col] = colors[2]


def _build_horizontal(
    grid: list[list[int]], profile: str, colors: tuple[int, int, int], rng
) -> None:
    height, width = len(grid), len(grid[0])
    wall_row = rng.choice(tuple(range(3, height - 3)))
    for col in range(width):
        grid[wall_row][col] = 9

    blocked_col = rng.choice(tuple(range(2, width - 2)))
    top_row = rng.choice(tuple(range(1, wall_row)))
    bottom_row = rng.choice(tuple(range(wall_row + 1, height - 1)))
    grid[top_row][blocked_col] = colors[0]
    grid[bottom_row][blocked_col] = colors[1]

    if profile == "horizontal_gap":
        gap_col = rng.choice(tuple(col for col in range(1, width - 1) if col != blocked_col))
        grid[wall_row][gap_col] = colors[2]
    else:
        extra_row = rng.choice(tuple(row for row in range(1, wall_row) if row != top_row))
        extra_col = rng.choice(tuple(col for col in range(1, width - 1) if col != blocked_col))
        grid[extra_row][extra_col] = colors[2]


def _build_vertical_segment(
    grid: list[list[int]], colors: tuple[int, int, int], rng
) -> None:
    height, width = len(grid), len(grid[0])
    wall_col = rng.choice(tuple(range(4, width - 4)))
    blocked_row = rng.choice(tuple(range(3, height - 3)))
    for row in range(blocked_row - 1, blocked_row + 2):
        grid[row][wall_col] = 9

    left_col = rng.choice(tuple(range(2, wall_col)))
    right_col = rng.choice(tuple(range(wall_col + 1, width - 2)))
    grid[blocked_row][left_col] = colors[0]
    grid[blocked_row][right_col] = colors[1]

    extra_rows = tuple(
        row
        for row in range(1, height - 1)
        if row not in (blocked_row - 1, blocked_row, blocked_row + 1)
    )
    extra_row = rng.choice(extra_rows)
    grid[extra_row][left_col] = colors[2]


def _build_horizontal_segment(
    grid: list[list[int]], colors: tuple[int, int, int], rng
) -> None:
    height, width = len(grid), len(grid[0])
    wall_row = rng.choice(tuple(range(3, height - 3)))
    blocked_col = rng.choice(tuple(range(3, width - 3)))
    for col in range(blocked_col - 1, blocked_col + 2):
        grid[wall_row][col] = 9

    top_row = rng.choice(tuple(range(1, wall_row)))
    bottom_row = rng.choice(tuple(range(wall_row + 1, height - 1)))
    grid[top_row][blocked_col] = colors[0]
    grid[bottom_row][blocked_col] = colors[1]

    extra_cols = tuple(
        col
        for col in range(1, width - 1)
        if col not in (blocked_col - 1, blocked_col, blocked_col + 1)
    )
    extra_col = rng.choice(extra_cols)
    grid[top_row][extra_col] = colors[2]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
    profile_override = overrides.get("scene_profile")
    if profile_override is not None and type(profile_override) is not str:
        raise TypeError("scene_profile override must be a string")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_strict("grid_h", 9, 11)
    width = ctx.draw_int_strict("grid_w", 11, 13)
    profile_options = (
        SCENE_PROFILES
        if profile_override is not None
        else _profile_options(difficulty, sample_index)
    )
    profile = ctx.draw_choice("scene_profile", profile_options)
    colors = ctx.draw_distinct_colors("seed_colors", n=3, exclude={0, 8, 9})

    grid = full_grid(height, width, 0)
    _paint_outer_frame(grid)
    rng = ctx.draw_rng("layout")
    if profile == "vertical_segment":
        _build_vertical_segment(grid, colors, rng)
    elif profile == "horizontal_segment":
        _build_horizontal_segment(grid, colors, rng)
    elif profile.startswith("vertical_"):
        _build_vertical(grid, profile, colors, rng)
    else:
        _build_horizontal(grid, profile, colors, rng)
    return grid


def _divider_candidates(grid) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    candidates: list[dict[str, Any]] = []
    for col in range(1, width - 1):
        gaps = [(row, grid[row][col]) for row in range(1, height - 1) if grid[row][col] != 9]
        if len(gaps) <= 1 and (not gaps or gaps[0][1] not in (0, 8, 9)):
            candidates.append(
                {
                    "orientation": "vertical",
                    "index": col,
                    "gap": (gaps[0][0], col, gaps[0][1]) if gaps else None,
                    "cells": {(row, col) for row in range(height)},
                }
            )
    for row in range(1, height - 1):
        gaps = [(col, grid[row][col]) for col in range(1, width - 1) if grid[row][col] != 9]
        if len(gaps) <= 1 and (not gaps or gaps[0][1] not in (0, 8, 9)):
            candidates.append(
                {
                    "orientation": "horizontal",
                    "index": row,
                    "gap": (row, gaps[0][0], gaps[0][1]) if gaps else None,
                    "cells": {(row, col) for col in range(width)},
                }
            )
    return candidates


def _full_divider_blockers(grid) -> set[tuple[int, int]]:
    """Wall cells recognized by the canonical-fitting full-divider shortcut."""
    blockers: set[tuple[int, int]] = set()
    for candidate in _divider_candidates(grid):
        blockers.update(
            point for point in candidate["cells"] if grid[point[0]][point[1]] == 9
        )
    return blockers


def _solve_with_blockers(
    grid, blocking_walls: set[tuple[int, int]], *, threshold: int = 2
) -> list[list[int]]:
    errors = _basic_grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    seeds = _seeds(grid)
    height, width = len(grid), len(grid[0])

    def visible(seed: tuple[int, int, int], row: int, col: int) -> bool:
        seed_row, seed_col, _ = seed
        if seed_row == row:
            return not any(
                (row, scan_col) in blocking_walls
                for scan_col in range(min(seed_col, col), max(seed_col, col) + 1)
            )
        if seed_col == col:
            return not any(
                (scan_row, col) in blocking_walls
                for scan_row in range(min(seed_row, row), max(seed_row, row) + 1)
            )
        return False

    return [
        [
            9
            if grid[row][col] == 9
            else 8
            if sum(visible(seed, row, col) for seed in seeds) >= threshold
            else 0
            for col in range(width)
        ]
        for row in range(height)
    ]


def _full_divider_walls_only(grid) -> list[list[int]]:
    """Canonical-fitting shortcut: only complete divider lines block rays."""
    return _solve_with_blockers(grid, _full_divider_blockers(grid))


def _lawful_domain_analysis(grid) -> dict[str, Any]:
    """Validate the shared canonical/generated task domain.

    The canonical evidence uses no internal wall or one full divider.  The task
    rule is cell-local, so the repaired sampler also admits one straight partial
    wall segment.  Curriculum-only requirements remain in ``_analyze``.
    """
    errors = _basic_grid_errors(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    if not 9 <= height <= 11:
        errors.append(f"grid height must be 9..11, found {height}")
    if not 11 <= width <= 13:
        errors.append(f"grid width must be 11..13, found {width}")
    if any(grid[0][col] != 9 or grid[height - 1][col] != 9 for col in range(width)):
        errors.append("top and bottom borders must be color 9")
    if any(grid[row][0] != 9 or grid[row][width - 1] != 9 for row in range(height)):
        errors.append("left and right borders must be color 9")

    seeds = _seeds(grid)
    if not 2 <= len(seeds) <= 3:
        errors.append(f"lawful scene must contain two or three seeds, found {len(seeds)}")
    seed_values = [value for _, _, value in seeds]
    if any(value == 8 for value in seed_values):
        errors.append("seed colors must exclude output marker 8")
    if len(seed_values) != len(set(seed_values)):
        errors.append("seed colors must be distinct")

    internal_walls = {
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] == 9
    }
    if internal_walls:
        wall_rows = {row for row, _ in internal_walls}
        wall_cols = {col for _, col in internal_walls}
        if len(wall_rows) != 1 and len(wall_cols) != 1:
            errors.append("interior walls must lie on one straight row or column")

    result.update(
        {
            "grid_h": height,
            "grid_w": width,
            "seeds": seeds,
            "internal_walls": internal_walls,
        }
    )
    return result


def _segment_candidate(grid, internal_walls: set[tuple[int, int]]) -> dict[str, Any] | None:
    if len(internal_walls) != 3:
        return None
    rows = sorted({row for row, _ in internal_walls})
    cols = sorted({col for _, col in internal_walls})
    if len(cols) == 1 and len(rows) == 3 and rows == list(range(rows[0], rows[0] + 3)):
        return {
            "orientation": "vertical",
            "index": cols[0],
            "cells": set(internal_walls),
        }
    if len(rows) == 1 and len(cols) == 3 and cols == list(range(cols[0], cols[0] + 3)):
        return {
            "orientation": "horizontal",
            "index": rows[0],
            "cells": set(internal_walls),
        }
    return None


def _analyze(grid) -> dict[str, Any]:
    lawful = _lawful_domain_analysis(grid)
    errors = list(lawful["errors"])
    result: dict[str, Any] = dict(lawful)
    result["errors"] = errors
    if errors:
        return result

    height = lawful["grid_h"]
    width = lawful["grid_w"]
    seeds = lawful["seeds"]
    internal_walls = lawful["internal_walls"]
    if len(seeds) != 3:
        errors.append(f"ordinary generated scene must contain exactly three seeds, found {len(seeds)}")

    candidates = _divider_candidates(grid)
    divider = None
    wall_structure = None
    profile = None
    structure_cells: set[tuple[int, int]] = set()

    if len(candidates) == 1:
        candidate = candidates[0]
        allowed_internal = {
            point
            for point in candidate["cells"]
            if 0 < point[0] < height - 1 and 0 < point[1] < width - 1
        }
        if internal_walls <= allowed_internal:
            divider = candidate
            wall_structure = candidate
            suffix = "gap" if candidate["gap"] is not None else "solid"
            profile = f"{candidate['orientation']}_{suffix}"
            structure_cells = set(candidate["cells"])
            if candidate["gap"] is not None and candidate["gap"] not in seeds:
                errors.append("the sole divider gap must be occupied by one of the three seeds")

    if wall_structure is None:
        segment = _segment_candidate(grid, internal_walls)
        if segment is None:
            errors.append("generated wall must be one full divider or one contiguous three-cell segment")
        else:
            wall_structure = segment
            profile = f"{segment['orientation']}_segment"
            structure_cells = set(segment["cells"])

    if profile not in SCENE_PROFILES:
        errors.append(f"unrecognized generated scene profile {profile!r}")

    intended = rule_mirror(grid)
    ignore_walls_output = _ignore_internal_walls(grid)
    full_divider_only_output = _full_divider_walls_only(grid)
    if intended == ignore_walls_output:
        errors.append("wall does not change visibility relative to the ignore-walls rival")
    if profile in SEGMENT_PROFILES and intended == full_divider_only_output:
        errors.append("short wall does not refute the full-divider-only canonical shortcut")
    if not any(
        grid[row][col] == 0 and intended[row][col] == 8
        for row in range(height)
        for col in range(width)
    ):
        errors.append("scene lacks a positive background >=2-visibility overlap")
    if intended == _one_seed_suffices(grid):
        errors.append("scene does not distinguish the >=2 threshold from >=1")

    result.update(
        {
            "divider": divider,
            "wall_structure": wall_structure,
            "divider_cells": structure_cells,
            "scene_profile": profile,
            "output": intended,
            "ignore_walls_output": ignore_walls_output,
            "full_divider_only_output": full_divider_only_output,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate lawful canonical and short-wall inputs, not sampler policy."""
    del difficulty, meta
    return list(_lawful_domain_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "scene_profile": analysis["scene_profile"],
    }


def strict_canonical_like(grid) -> list[str]:
    lawful = _lawful_domain_analysis(grid)
    reasons = list(lawful["errors"])
    if reasons:
        return reasons
    internal_walls = lawful["internal_walls"]
    if not internal_walls:
        return reasons
    height, width = lawful["grid_h"], lawful["grid_w"]
    candidates = _divider_candidates(grid)
    if len(candidates) != 1:
        reasons.append("canonical internal walls form one full row/column, with at most a seed gap")
        return reasons
    allowed = {
        point
        for point in candidates[0]["cells"]
        if 0 < point[0] < height - 1 and 0 < point[1] < width - 1
    }
    if not internal_walls <= allowed:
        reasons.append("interior walls stray outside the canonical divider")
    return reasons


def _wall_blocks_visibility(grid) -> bool:
    try:
        return rule_mirror(grid) != _ignore_internal_walls(grid)
    except (TypeError, ValueError):
        return False


def _partial_wall_blocks_visibility(grid) -> bool:
    try:
        return rule_mirror(grid) != _full_divider_walls_only(grid)
    except (TypeError, ValueError):
        return False


def _single_visibility_stays_zero(grid) -> bool:
    try:
        return rule_mirror(grid) != _one_seed_suffices(grid)
    except (TypeError, ValueError):
        return False


def _positive_overlap(grid) -> bool:
    try:
        output = rule_mirror(grid)
    except (TypeError, ValueError):
        return False
    return any(
        grid[row][col] == 0 and output[row][col] == 8
        for row in range(len(grid))
        for col in range(len(grid[0]))
    )


SEMANTIC_RIVALS = {
    "ignore_internal_walls": _ignore_internal_walls,
    "one_seed_suffices": _one_seed_suffices,
    "full_divider_walls_only": _full_divider_walls_only,
}
LESSON_COMPETITORS = {
    "ignore_internal_walls": _ignore_internal_walls,
    "one_seed_suffices": _one_seed_suffices,
    "full_divider_walls_only": _full_divider_walls_only,
}
CANONICAL_SHORTCUTS = {
    "full_divider_walls_only": _full_divider_walls_only,
}
SEMANTIC_WITNESSES = {
    "wall_blocks_visibility": _wall_blocks_visibility,
    "partial_wall_blocks_visibility": _partial_wall_blocks_visibility,
    "single_visibility_stays_zero": _single_visibility_stays_zero,
    "positive_overlap": _positive_overlap,
}
WITNESS_RIVALS = {
    "wall_blocks_visibility": ["ignore_internal_walls"],
    "partial_wall_blocks_visibility": ["full_divider_walls_only"],
    "single_visibility_stays_zero": ["one_seed_suffices"],
}
BRANCH_WITNESSES = ("positive_overlap",)


def lesson_identifiable(demos, query) -> list[str]:
    del query
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["lesson has no demonstrations"]
    valid = [pair for pair in demos if isinstance(pair, dict) and "input" in pair and "output" in pair]
    if len(valid) != len(demos):
        reasons.append("every demonstration must contain input and output grids")
        return reasons
    if not any(_ignore_internal_walls(pair["input"]) != pair["output"] for pair in valid):
        reasons.append("demonstrations do not refute the ignore-internal-walls shortcut")
    if not any(_one_seed_suffices(pair["input"]) != pair["output"] for pair in valid):
        reasons.append("demonstrations do not establish the >=2 visibility threshold")
    if not any(_full_divider_walls_only(pair["input"]) != pair["output"] for pair in valid):
        reasons.append("demonstrations do not show that a partial wall segment blocks rays")
    if not any(
        pair["input"][row][col] == 0 and pair["output"][row][col] == 8
        for pair in valid
        for row in range(len(pair["input"]))
        for col in range(len(pair["input"][0]))
    ):
        reasons.append("demonstrations contain no positive background overlap")
    return reasons
