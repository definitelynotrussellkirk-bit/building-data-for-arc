"""Generator for 382eb0e592eb: copy horizontal equal-color pairs down.

The pinned rule fires on every adjacent equal nonzero horizontal window, not
only isolated 1x2 components.  The four-slot curriculum alternates compact
canonical anchors with exact-profile semantic witnesses that separate the rule
from four plausible shortcuts while retaining the public 4x5/3x6, three-color
profile on every ordinary draw.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "382eb0e592eb"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "03fbcf596117"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 4

SCHEDULE_PROFILES = (
    "canonical_4x5",
    "semantic_3x6",
    "canonical_3x6",
    "semantic_4x5",
)
_PROFILE_DIMS = {
    "canonical_4x5": (4, 5),
    "semantic_3x6": (3, 6),
    "canonical_3x6": (3, 6),
    "semantic_4x5": (4, 5),
}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_COLOR_POOLS = {
    None: tuple(range(1, 10)),
    "easy": (1, 2, 3),
    "medium": (4, 5, 6),
    "hard": (7, 8, 9),
}

SUMMARY = (
    "Three-color 4x5/3x6 scenes. Every equal nonzero horizontal pair copies "
    "its color into the two cells directly below, using the original input for "
    "pair detection. A four-slot schedule mixes isolated-pair anchors with "
    "overlap, overwrite, vertical-decoy, and bottom-boundary witnesses."
)
INVARIANTS = [
    "background is 0 and ordinary draws use exactly two nonzero colors",
    "at least one horizontal equal-color pair above the bottom row changes the output",
    "pair detection reads the original input; writes do not create recursive triggers",
    "bottom-row pairs are inert because no target row exists",
    "every ordinary draw has an exact public height/width/palette profile",
]

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-slot cyclic curriculum",
        "valid": "|".join(SCHEDULE_PROFILES),
        "doc": "Exact observable scene family: dimensions plus canonical or semantic layout.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

Grid = list[list[int]]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-slot teaching profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))
    value = overrides.get("scene_profile")
    if value is not None and (type(value) is not str or value not in SCHEDULE_PROFILES):
        raise ValueError("scene_profile must be one of: " + ", ".join(SCHEDULE_PROFILES))


def _shape_error(grid: Any) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a nonempty list of rows"
    if not all(isinstance(row, list) for row in grid):
        return "every row must be a list"
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return "grid must be rectangular and nonempty"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "grid values must be integer ARC colors 0..9 (not bool)"
    return None


def _mirror_horizontal(grid: Grid) -> Grid:
    return [list(reversed(row)) for row in grid]


def _paint_pair(grid: Grid, row: int, col: int, color: int) -> None:
    grid[row][col] = color
    grid[row][col + 1] = color


def _build_canonical_4x5(first: int, second: int, rng) -> Grid:
    grid = full_grid(4, 5, 0)
    layouts = (
        ((0, 1), (2, 2)),
        ((0, 0), (2, 3)),
        ((1, 0), (1, 3)),
        ((0, 2), (2, 0)),
    )
    (r1, c1), (r2, c2) = rng.choice(layouts)
    _paint_pair(grid, r1, c1, first)
    _paint_pair(grid, r2, c2, second)
    if rng.randrange(2):
        grid = _mirror_horizontal(grid)
    return grid


def _build_canonical_3x6(first: int, second: int, rng) -> Grid:
    grid = full_grid(3, 6, 0)
    layouts = (
        ((0, 0), (1, 3)),
        ((0, 1), (1, 4)),
        ((0, 3), (1, 0)),
        ((0, 4), (1, 1)),
    )
    (r1, c1), (r2, c2) = rng.choice(layouts)
    _paint_pair(grid, r1, c1, first)
    _paint_pair(grid, r2, c2, second)
    if rng.randrange(2):
        grid = _mirror_horizontal(grid)
    return grid


def _build_semantic_3x6(first: int, second: int, rng) -> Grid:
    """Fit all four shortcut witnesses inside an exact public 3x6 profile."""
    grid = full_grid(3, 6, 0)
    run_start = rng.choice((0, 1))
    vertical_col = 5 if run_start == 0 else 0
    bottom_start = 0 if vertical_col == 5 else 4
    for col in range(run_start, run_start + 3):
        grid[0][col] = first
    grid[1][run_start + 1] = second  # nonzero target overwritten by the rule
    grid[0][vertical_col] = second
    grid[1][vertical_col] = second  # same-color vertical decoy, blank below
    _paint_pair(grid, 2, bottom_start, second)  # inert bottom-boundary pair
    return grid


def _build_semantic_4x5(first: int, second: int, rng) -> Grid:
    """Fit all four shortcut witnesses inside an exact public 4x5 profile."""
    grid = full_grid(4, 5, 0)
    run_start = rng.choice((0, 1))
    run_row = rng.choice((0, 1))
    vertical_col = 4 if run_start == 0 else 0
    bottom_start = 0 if vertical_col == 4 else 3
    for col in range(run_start, run_start + 3):
        grid[run_row][col] = first
    grid[run_row + 1][run_start + 1] = second
    grid[0][vertical_col] = second
    grid[1][vertical_col] = second
    _paint_pair(grid, 3, bottom_start, second)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    effective_overrides = dict(overrides)
    if effective_overrides.get("scene_profile") is None:
        effective_overrides["scene_profile"] = scheduled
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCHEDULE_PROFILES)
    color_pool = _COLOR_POOLS[difficulty]
    first = ctx.draw_choice("first_color", color_pool)
    second = ctx.draw_choice("second_color", tuple(color for color in color_pool if color != first))
    band_label = difficulty or "unbanded"
    rng = ctx.draw_rng(f"layout:{band_label}")
    builders = {
        "canonical_4x5": _build_canonical_4x5,
        "semantic_3x6": _build_semantic_3x6,
        "canonical_3x6": _build_canonical_3x6,
        "semantic_4x5": _build_semantic_4x5,
    }
    grid = builders[profile](first, second, rng)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise AssertionError(
            f"axis realization mismatch: expected {profile!r}, observed {observed!r}"
        )
    return grid


def rule_mirror(grid: Grid) -> Grid:
    """Pure mirror of the pinned rule; all pair tests read the original input."""
    error = _shape_error(grid)
    if error:
        raise ValueError(error)
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height - 1):
        for col in range(width - 1):
            value = grid[row][col]
            if value != 0 and grid[row][col + 1] == value:
                output[row + 1][col] = value
                output[row + 1][col + 1] = value
    return output


def _has_horizontal_neighbor(grid: Grid, row: int, col: int) -> bool:
    value = grid[row][col]
    width = len(grid[0])
    return bool(
        value != 0
        and (
            (col > 0 and grid[row][col - 1] == value)
            or (col + 1 < width and grid[row][col + 1] == value)
        )
    )


def _witness_overlapping_pair_run(grid: Grid) -> bool:
    width = len(grid[0])
    for row in range(len(grid) - 1):
        col = 0
        while col < width:
            value = grid[row][col]
            end = col + 1
            while value != 0 and end < width and grid[row][end] == value:
                end += 1
            if value != 0 and end - col >= 3:
                return True
            col = max(end, col + 1)
    return False


def _witness_nontrigger_vertical(grid: Grid) -> bool:
    height, width = len(grid), len(grid[0])
    for row in range(height - 1):
        for col in range(width):
            value = grid[row][col]
            if (
                value != 0
                and grid[row + 1][col] == value
                and not _has_horizontal_neighbor(grid, row, col)
                and not _has_horizontal_neighbor(grid, row + 1, col)
            ):
                return True
    return False


def _witness_overwrite_nonzero_below(grid: Grid) -> bool:
    height, width = len(grid), len(grid[0])
    for row in range(height - 1):
        for col in range(width - 1):
            value = grid[row][col]
            if value != 0 and grid[row][col + 1] == value:
                targets = (grid[row + 1][col], grid[row + 1][col + 1])
                if any(target != 0 and target != value for target in targets):
                    return True
    return False


def _witness_bottom_row_pair(grid: Grid) -> bool:
    row = grid[-1]
    return any(value != 0 and row[col + 1] == value for col, value in enumerate(row[:-1]))


def _is_semantic_scene(grid: Grid) -> bool:
    return all(
        witness(grid)
        for witness in (
            _witness_overlapping_pair_run,
            _witness_nontrigger_vertical,
            _witness_overwrite_nonzero_below,
            _witness_bottom_row_pair,
        )
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    error = _shape_error(grid)
    if error:
        return [error]
    errors: list[str] = []
    dims = (len(grid), len(grid[0]))
    if dims not in {(4, 5), (3, 6)}:
        errors.append(f"dimensions {dims} are outside the supported 4x5/3x6 profiles")
    palette = {value for row in grid for value in row}
    if 0 not in palette:
        errors.append("background color 0 is absent")
    if len(palette) != 3:
        errors.append(f"expected background plus exactly two nonzero colors, found palette {sorted(palette)}")
    active = any(
        grid[row][col] != 0 and grid[row][col + 1] == grid[row][col]
        for row in range(len(grid) - 1)
        for col in range(len(grid[0]) - 1)
    )
    if not active:
        errors.append("no horizontal equal-color pair above the bottom row")
    elif rule_mirror(grid) == grid:
        errors.append("all rule writes are already satisfied; transformation is invisible")
    return sorted(set(errors))


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    if profile not in {(4, 5, 3), (3, 6, 3)}:
        return [f"profile {profile} is outside the exact canonical profiles"]
    return []


def observe_overrides(grid) -> dict[str, str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    dims = (len(grid), len(grid[0]))
    if dims == (4, 5):
        profile = "semantic_4x5" if _is_semantic_scene(grid) else "canonical_4x5"
    elif dims == (3, 6):
        profile = "semantic_3x6" if _is_semantic_scene(grid) else "canonical_3x6"
    else:
        raise ValueError(f"unsupported dimensions for scene_profile: {dims}")
    return {"scene_profile": profile}


def _rival_exact_domino_only(grid: Grid) -> Grid:
    """Rival: expand only maximal horizontal runs of exactly two cells."""
    error = _shape_error(grid)
    if error:
        raise ValueError(error)
    output = [list(row) for row in grid]
    width = len(grid[0])
    for row in range(len(grid) - 1):
        col = 0
        while col < width:
            value = grid[row][col]
            end = col + 1
            while value != 0 and end < width and grid[row][end] == value:
                end += 1
            if value != 0 and end - col == 2:
                output[row + 1][col] = value
                output[row + 1][col + 1] = value
            col = max(end, col + 1)
    return output


def _rival_copy_all_nonzero_down(grid: Grid) -> Grid:
    """Rival: copy every nonzero cell down, regardless of horizontal pairing."""
    error = _shape_error(grid)
    if error:
        raise ValueError(error)
    output = [list(row) for row in grid]
    for row in range(len(grid) - 1):
        for col, value in enumerate(grid[row]):
            if value != 0:
                output[row + 1][col] = value
    return output


def _rival_blank_below_only(grid: Grid) -> Grid:
    """Rival: expand a pair only when both original target cells are zero."""
    error = _shape_error(grid)
    if error:
        raise ValueError(error)
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height - 1):
        for col in range(width - 1):
            value = grid[row][col]
            if (
                value != 0
                and grid[row][col + 1] == value
                and grid[row + 1][col] == 0
                and grid[row + 1][col + 1] == 0
            ):
                output[row + 1][col] = value
                output[row + 1][col + 1] = value
    return output


def _rival_bottom_pair_upwards(grid: Grid) -> Grid:
    """Rival: apply the rule, then incorrectly extend bottom-row pairs upward."""
    output = rule_mirror(grid)
    if len(grid) < 2:
        return output
    row = len(grid) - 1
    for col in range(len(grid[0]) - 1):
        value = grid[row][col]
        if value != 0 and grid[row][col + 1] == value:
            output[row - 1][col] = value
            output[row - 1][col + 1] = value
    return output


SEMANTIC_WITNESSES = {
    "overlapping_pair_run": _witness_overlapping_pair_run,
    "nontrigger_vertical": _witness_nontrigger_vertical,
    "overwrite_nonzero_below": _witness_overwrite_nonzero_below,
    "bottom_row_pair": _witness_bottom_row_pair,
}
SEMANTIC_RIVALS = {
    "exact_domino_only": _rival_exact_domino_only,
    "copy_all_nonzero_down": _rival_copy_all_nonzero_down,
    "blank_below_only": _rival_blank_below_only,
    "bottom_pair_upwards": _rival_bottom_pair_upwards,
}
WITNESS_RIVALS = {
    "overlapping_pair_run": ["exact_domino_only"],
    "nontrigger_vertical": ["copy_all_nonzero_down"],
    "overwrite_nonzero_below": ["blank_below_only"],
    "bottom_row_pair": ["bottom_pair_upwards"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Report named rivals that fit every demo but change the query answer."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict):
        return ["query must be an input/output pair"]

    errors: list[str] = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"pair {index} must contain input and output")
            continue
        structural = self_check(pair["input"])
        if structural:
            errors.append(f"pair {index} input: {'; '.join(structural)}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"pair {index} output disagrees with the pinned rule mirror")
    if errors:
        return sorted(set(errors))

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                errors.append(f"named rival {name} fits all demos but changes the query")
    return sorted(set(errors))
