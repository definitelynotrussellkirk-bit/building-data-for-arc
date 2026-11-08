"""Constructive generator for ``Crossing rays with blockers``.

The top edge contains green (3) column shooters and the left edge contains red
(2) row shooters.  Maroon (9) interior cells stop rays.  A cell reached by a
single ray receives that ray's color; a cell reached by both becomes cyan (8).

Version 4 uses a three-example semantic curriculum.  Every ordinary draw has an
observable horizontal stop, vertical stop, horizontal-only cell, vertical-only
cell, and cyan crossing.  The schedule rotates through one combined adjacent /
first-step fixture, separated stops, and late stops so every three consecutive
examples refute common no-blocker, off-by-one, and fixed-position shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b0e266482663"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "d12310adc715"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Green (3) markers on the top edge shoot downward and red (2) markers on "
    "the left edge shoot rightward. Maroon (9) cells stop rays. Horizontal-only "
    "and vertical-only cells become 2 and 3; crossings become cyan (8)."
)

INVARIANTS = [
    "background is 0 and the unused top-left corner is 0",
    "top-edge shooters are 3 and left-edge shooters are 2",
    "every ordinary input has at least one observable stop in each direction",
    "every ordinary input exercises horizontal-only, vertical-only, and crossing branches",
    "all blockers are interior to the two marker edges",
]

_GRID_H_VALUES = tuple(range(6, 14))
_GRID_W_VALUES = tuple(range(6, 15))
_SHOOTER_VALUES = (1, 2, 3, 4)
_BLOCKER_VALUES = tuple(range(2, 11))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "paired canonical/generalization profile in 6..13",
        "valid": "6..13",
    },
    "grid_w": {
        "type": "int",
        "default": "paired canonical/generalization profile in 6..14",
        "valid": "6..14",
    },
    "n_row_shoot": {
        "type": "int",
        "default": "difficulty-weighted choice in 1..4",
        "valid": "1..4",
    },
    "n_col_shoot": {
        "type": "int",
        "default": "difficulty-weighted choice in 1..4",
        "valid": "1..4",
    },
    "n_blockers": {
        "type": "int",
        "default": "difficulty/profile-weighted choice in 2..10",
        "valid": "2..10",
    },
}
_ALLOWED_OVERRIDES = frozenset(AXES)
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "adjacent_first_step",
    "separated_stops",
    "late_stops",
)

# Pick height and width as a *pair*.  Independent marginal weighting produced
# all nine combinations of 7/8/9 by 8/9/10, so only about one third of draws
# matched a real source profile.  Paired planning preserves those profiles
# while retaining deliberate out-of-profile generalization examples.
_CANONICAL_SHAPES = ((7, 8), (8, 9), (9, 10))
_EXPANDED_SHAPES = {
    "easy": ((6, 7), (6, 8), (7, 9), (8, 10)),
    "medium": ((6, 11), (10, 7), (11, 12), (12, 14)),
    "hard": ((10, 11), (11, 13), (12, 14), (13, 14)),
}


def _difficulty_band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the deterministic four-slot semantic curriculum profile."""
    del seed
    _difficulty_band(difficulty)
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")


def _planned_shape(ctx, band: str) -> tuple[int, int]:
    """Choose one coherent shape profile before exposing its two public axes."""
    choices = _CANONICAL_SHAPES * 4 + _EXPANDED_SHAPES[band]
    return tuple(ctx.draw_rng("shape_plan").choice(choices))


def _draw_choice_axis(ctx, label: str, defaults: Sequence[int], domain: Sequence[int]):
    """Draw an axis while keeping the full public domain overrideable."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, domain)
    return ctx.draw_choice(label, defaults)


def _count_options(band: str, profile: str) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if band == "easy":
        shooters = (1,) * 10 + (2,) * 8 + (3, 4)
        blockers = (2,) * 10 + (3,) * 8 + (4,) * 4 + (5, 6, 7, 8, 9, 10)
    elif band == "hard":
        shooters = (1, 2, 2) + (3,) * 8 + (4,) * 12
        blockers = (2, 3, 4, 5) + (6,) * 4 + (7,) * 6 + (8,) * 8 + (9,) * 6 + (10,) * 5
    else:
        shooters = (1, 2, 2) + (3,) * 7 + (4,) * 4
        blockers = (2, 3, 3) + (4,) * 7 + (5,) * 6 + (6,) * 4 + (7, 8, 9, 10)

    # A first-step stop in both directions needs a second shooter and two extra
    # blockers.  Explicit caller overrides still take precedence through the
    # full-domain branch in ``_draw_choice_axis``.
    if profile == "adjacent_first_step":
        shooters = (2,) * 10 + (3,) * 8 + (4,) * 5
        blockers = (4,) * 10 + (5,) * 8 + (6,) * 6 + (7, 8, 9, 10)
    return tuple(shooters), tuple(blockers)


def _ordered_triplet(size: int, profile: str, rng) -> tuple[int, int, int]:
    """Choose crossing, single-ray witness, and later blocker coordinates."""
    # Positions 1..size-2 leave a visible cell after the blocker.
    candidates = list(range(1, size - 1))
    if profile == "adjacent_first_step":
        # The crossing at coordinate 1 guarantees adjacent edge shooters.  A
        # second required shooter is stopped at its first interior cell below.
        tail = sorted(rng.sample(candidates[1:], 2))
        return 1, tail[0], tail[1]
    if profile == "late_stops":
        blocker = candidates[-1]
        earlier = sorted(rng.sample(candidates[:-1], 2))
        return earlier[0], earlier[1], blocker
    chosen = sorted(rng.sample(candidates, 3))
    return chosen[0], chosen[1], chosen[2]


def _select_markers(
    candidates: Sequence[int],
    count: int,
    required: set[int],
    excluded: set[int],
    rng,
) -> list[int]:
    if required & excluded:
        raise ValueError("a marker coordinate cannot be both required and excluded")
    available = [value for value in candidates if value not in required and value not in excluded]
    needed = count - len(required)
    if needed < 0 or needed > len(available):
        raise ValueError(
            f"cannot place {count} markers with required={sorted(required)} "
            f"and excluded={sorted(excluded)}"
        )
    selected = sorted(required | set(rng.sample(available, needed)))
    if len(selected) != count:
        raise RuntimeError("marker construction did not preserve the requested count")
    return selected


def _construct_grid(
    height: int,
    width: int,
    n_row_shoot: int,
    n_col_shoot: int,
    n_blockers: int,
    profile: str,
    rng,
) -> list[list[int]]:
    cross_r, vertical_only_r, vertical_block_r = _ordered_triplet(height, profile, rng)
    cross_c, horizontal_only_c, horizontal_block_c = _ordered_triplet(width, profile, rng)

    first_step_enabled = (
        profile == "adjacent_first_step"
        and n_row_shoot >= 2
        and n_col_shoot >= 2
        and n_blockers >= 4
    )

    required_rows = {cross_r}
    required_cols = {cross_c}
    if first_step_enabled:
        required_rows.add(vertical_block_r)
        required_cols.add(horizontal_block_c)

    row_shooters = _select_markers(
        range(1, height),
        n_row_shoot,
        required_rows,
        {vertical_only_r},
        rng,
    )
    col_shooters = _select_markers(
        range(1, width),
        n_col_shoot,
        required_cols,
        {horizontal_only_c},
        rng,
    )

    # These two blockers are semantic anchors.  Their prefixes are protected,
    # so each visibly truncates a live ray and leaves at least one cell beyond.
    blockers = {
        (cross_r, horizontal_block_c),
        (vertical_block_r, cross_c),
    }
    if first_step_enabled:
        blockers.update(
            {
                (vertical_block_r, 1),
                (1, horizontal_block_c),
            }
        )

    protected = {
        (cross_r, col) for col in range(1, horizontal_block_c)
    } | {
        (row, cross_c) for row in range(1, vertical_block_r)
    }

    candidates = [
        (row, col)
        for row in range(1, height)
        for col in range(1, width)
        if (row, col) not in blockers and (row, col) not in protected
    ]
    rng.shuffle(candidates)
    need = n_blockers - len(blockers)
    if need < 0:
        # This is reachable only through an explicit low blocker override on the
        # first-step slot.  Keep the two universal anchors and omit the optional
        # immediate-stop pair, preserving exactness and the core rule branches.
        blockers = {
            (cross_r, horizontal_block_c),
            (vertical_block_r, cross_c),
        }
        first_step_enabled = False
        candidates = [
            (row, col)
            for row in range(1, height)
            for col in range(1, width)
            if (row, col) not in blockers and (row, col) not in protected
        ]
        rng.shuffle(candidates)
        need = n_blockers - len(blockers)
    if need > len(candidates):
        raise ValueError("requested blocker count exceeds the constructive layout capacity")
    blockers.update(candidates[:need])

    grid = full_grid(height, width, 0)
    for row in row_shooters:
        grid[row][0] = 2
    for col in col_shooters:
        grid[0][col] = 3
    for row, col in blockers:
        grid[row][col] = 9
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    band = _difficulty_band(difficulty)
    profile = schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    shooter_options, blocker_options = _count_options(band, profile)
    planned_height, planned_width = _planned_shape(ctx, band)
    height = _draw_choice_axis(ctx, "grid_h", (planned_height,), _GRID_H_VALUES)
    width = _draw_choice_axis(ctx, "grid_w", (planned_width,), _GRID_W_VALUES)
    n_row_shoot = _draw_choice_axis(
        ctx, "n_row_shoot", shooter_options, _SHOOTER_VALUES
    )
    n_col_shoot = _draw_choice_axis(
        ctx, "n_col_shoot", shooter_options, _SHOOTER_VALUES
    )
    n_blockers = _draw_choice_axis(
        ctx, "n_blockers", blocker_options, _BLOCKER_VALUES
    )
    grid = _construct_grid(
        height,
        width,
        n_row_shoot,
        n_col_shoot,
        n_blockers,
        profile,
        ctx.draw_rng("layout"),
    )
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_row_shoot": n_row_shoot,
        "n_col_shoot": n_col_shoot,
        "n_blockers": n_blockers,
    }
    if observed != expected:
        raise RuntimeError(f"keyed-axis mismatch: expected {expected}, observed {observed}")
    errors = self_check(grid, difficulty=band)
    if errors:
        raise RuntimeError("constructed invalid ray lesson: " + "; ".join(errors))
    return grid


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _ray_analysis(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    height, width = len(grid), len(grid[0])
    row_shooters = {row for row in range(1, height) if grid[row][0] == 2}
    col_shooters = {col for col in range(1, width) if grid[0][col] == 3}
    blockers = {
        (row, col)
        for row in range(1, height)
        for col in range(1, width)
        if grid[row][col] == 9
    }
    active_h = {
        (row, col)
        for row, col in blockers
        if row in row_shooters
        and col < width - 1
        and all(grid[row][cc] != 9 for cc in range(1, col))
    }
    active_v = {
        (row, col)
        for row, col in blockers
        if col in col_shooters
        and row < height - 1
        and all(grid[rr][col] != 9 for rr in range(1, row))
    }
    branch_counts = {"h_only": 0, "v_only": 0, "both": 0}
    for row in range(1, height):
        for col in range(1, width):
            if grid[row][col] == 9:
                continue
            h_ray = row in row_shooters and all(
                grid[row][cc] != 9 for cc in range(1, col + 1)
            )
            v_ray = col in col_shooters and all(
                grid[rr][col] != 9 for rr in range(1, row + 1)
            )
            if h_ray and v_ray:
                branch_counts["both"] += 1
            elif h_ray:
                branch_counts["h_only"] += 1
            elif v_ray:
                branch_counts["v_only"] += 1
    return {
        "row_shooters": row_shooters,
        "col_shooters": col_shooters,
        "blockers": blockers,
        "active_h": active_h,
        "active_v": active_v,
        "first_step_h": {(r, c) for r, c in active_h if c == 1},
        "first_step_v": {(r, c) for r, c in active_v if r == 1},
        **branch_counts,
    }


def observe_overrides(grid: Any) -> dict[str, int]:
    errors = _shape_errors(grid)
    if errors:
        raise ValueError("cannot observe axes: " + "; ".join(errors))
    analysis = _ray_analysis(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_row_shoot": len(analysis["row_shooters"]),
        "n_col_shoot": len(analysis["col_shooters"]),
        "n_blockers": len(analysis["blockers"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors = _shape_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not (5 <= height <= 30 and 5 <= width <= 30):
        errors.append("grid dimensions must stay within the ARC 5..30 envelope")
    if grid[0][0] != 0:
        errors.append("top-left corner must be unused background")
    if any(value not in (0, 3) for value in grid[0][1:]):
        errors.append("top edge may contain only background and green (3) shooters")
    if any(grid[row][0] not in (0, 2) for row in range(1, height)):
        errors.append("left edge may contain only background and red (2) shooters")
    if any(
        grid[row][col] not in (0, 9)
        for row in range(1, height)
        for col in range(1, width)
    ):
        errors.append("interior input cells may contain only background and blockers")
    if errors:
        return errors

    analysis = _ray_analysis(grid)
    if not analysis["row_shooters"]:
        errors.append("need at least one left-edge red row shooter")
    if not analysis["col_shooters"]:
        errors.append("need at least one top-edge green column shooter")
    if not analysis["active_h"]:
        errors.append("need an observable horizontal ray stopped before the final column")
    if not analysis["active_v"]:
        errors.append("need an observable vertical ray stopped before the final row")
    if analysis["h_only"] == 0:
        errors.append("horizontal-only branch is hidden")
    if analysis["v_only"] == 0:
        errors.append("vertical-only branch is hidden")
    if analysis["both"] == 0:
        errors.append("cyan crossing branch is hidden")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked grammar shared by canonical and generated inputs."""
    return self_check(grid)


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Input-pure Python mirror of the selected canonical Racket authority."""
    errors = _shape_errors(grid)
    if errors:
        raise ValueError("rule_mirror expects a rectangular ARC grid")
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 9:
                continue
            horizontal = (
                col >= 1
                and grid[row][0] == 2
                and all(grid[row][cc] != 9 for cc in range(1, col + 1))
            )
            vertical = (
                row >= 1
                and grid[0][col] == 3
                and all(grid[rr][col] != 9 for rr in range(1, row + 1))
            )
            if horizontal and vertical:
                output[row][col] = 8
            elif horizontal:
                output[row][col] = 2
            elif vertical:
                output[row][col] = 3
    return output


def _rival_ignore_blockers(grid):
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 9:
                continue
            horizontal = col >= 1 and grid[row][0] == 2
            vertical = row >= 1 and grid[0][col] == 3
            if horizontal and vertical:
                output[row][col] = 8
            elif horizontal:
                output[row][col] = 2
            elif vertical:
                output[row][col] = 3
    return output


def _rival_crossing_color(grid, winner: int):
    output = rule_mirror(grid)
    analysis = _ray_analysis(grid)
    for row in range(1, len(grid)):
        for col in range(1, len(grid[0])):
            if grid[row][col] == 9:
                continue
            horizontal = row in analysis["row_shooters"] and all(
                grid[row][cc] != 9 for cc in range(1, col + 1)
            )
            vertical = col in analysis["col_shooters"] and all(
                grid[rr][col] != 9 for rr in range(1, row + 1)
            )
            if horizontal and vertical:
                output[row][col] = winner
    return output


def _rival_horizontal_wins(grid):
    return _rival_crossing_color(grid, 2)


def _rival_vertical_wins(grid):
    return _rival_crossing_color(grid, 3)


def _rival_horizontal_only(grid):
    output = [list(row) for row in grid]
    for row in range(1, len(grid)):
        if grid[row][0] != 2:
            continue
        for col in range(1, len(grid[0])):
            if grid[row][col] == 9:
                break
            output[row][col] = 2
    return output


def _rival_vertical_only(grid):
    output = [list(row) for row in grid]
    for col in range(1, len(grid[0])):
        if grid[0][col] != 3:
            continue
        for row in range(1, len(grid)):
            if grid[row][col] == 9:
                break
            output[row][col] = 3
    return output


def _rival_stop_before_blocker(grid):
    output = rule_mirror(grid)
    analysis = _ray_analysis(grid)
    for row, col in analysis["active_h"]:
        if col > 1 and grid[row][col - 1] != 9:
            output[row][col - 1] = 0
    for row, col in analysis["active_v"]:
        if row > 1 and grid[row - 1][col] != 9:
            output[row - 1][col] = 0
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "ignore_blockers": _rival_ignore_blockers,
    "horizontal_color_wins_crossings": _rival_horizontal_wins,
    "vertical_color_wins_crossings": _rival_vertical_wins,
    "emit_horizontal_rays_only": _rival_horizontal_only,
    "emit_vertical_rays_only": _rival_vertical_only,
    "stop_one_cell_before_blocker": _rival_stop_before_blocker,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "ignore_blockers": _rival_ignore_blockers,
    "horizontal_color_wins_crossings": _rival_horizontal_wins,
    "vertical_color_wins_crossings": _rival_vertical_wins,
}

SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "horizontal_stop": lambda grid: bool(_ray_analysis(grid)["active_h"]),
    "vertical_stop": lambda grid: bool(_ray_analysis(grid)["active_v"]),
    "horizontal_only_fill": lambda grid: _ray_analysis(grid)["h_only"] > 0,
    "vertical_only_fill": lambda grid: _ray_analysis(grid)["v_only"] > 0,
    "cyan_crossing": lambda grid: _ray_analysis(grid)["both"] > 0,
    "adjacent_shooters": lambda grid: (
        1 in _ray_analysis(grid)["row_shooters"]
        and 1 in _ray_analysis(grid)["col_shooters"]
    ),
    "first_step_stops_both_axes": lambda grid: (
        bool(_ray_analysis(grid)["first_step_h"])
        and bool(_ray_analysis(grid)["first_step_v"])
    ),
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)
WITNESS_RIVALS = {
    "horizontal_stop": ["ignore_blockers"],
    "vertical_stop": ["ignore_blockers"],
    "horizontal_only_fill": ["emit_vertical_rays_only"],
    "vertical_only_fill": ["emit_horizontal_rays_only"],
    "cyan_crossing": [
        "horizontal_color_wins_crossings",
        "vertical_color_wins_crossings",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a lawful lesson that falsifies every declared rival rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"pair {index} is outside the ray grammar: {errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} disagrees with the selected ray rule")
    if reasons:
        return reasons

    for name, witness in SEMANTIC_WITNESSES.items():
        if not any(witness(pair["input"]) for pair in demos):
            reasons.append(f"demonstrations are missing witness: {name}")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
