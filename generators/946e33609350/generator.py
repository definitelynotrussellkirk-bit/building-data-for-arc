"""Generator for 946e33609350: nearest seed through color-1 corridors.

Color 1 is an impassable wall. Every other non-zero cell is a uniquely
colored seed. A zero cell receives the color of its unique nearest seed under
4-neighbor shortest-path distance through non-wall cells; finite ties remain
zero. Walls and seeds are preserved.

Three consecutive default examples form a complete lesson:

* ``horizontal_gate`` forces paths through one gap in a horizontal wall;
* ``open_tie`` exposes a finite equal-distance locus that must remain zero;
* ``vertical_gate`` provides a transposed wall-detour example and a third seed.

Every public override is exact, observable from returned pixels, and valid in
every difficulty band. Default draws use the three measured canonical
(height, width, palette-size) profiles so every lesson stays source-shaped.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "946e33609350"
TASK_ID = GENERATOR_ID
RULE_HASH = "1ec8459f97ec"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A color-1 rectangular frame contains two or three distinct singleton "
    "seeds. Zeros take the unique nearest seed color by wall-aware 4-neighbor "
    "BFS; equal-distance ties remain zero. A three-example schedule guarantees "
    "an open tie and horizontal/vertical one-gap wall detours."
)

INVARIANTS = [
    "grid is 6..10 by 9..12 with a complete color-1 boundary frame",
    "there are exactly two or three globally distinct singleton seed colors from 2..9",
    "interior walls are absent or form one horizontal/vertical one-gap barrier",
    "all non-wall cells are reachable from at least one seed",
    "finite nearest-seed ties stay zero and all walls/seeds are preserved",
]

SCHEDULE_PROFILES = (
    "horizontal_gate",
    "open_tie",
    "vertical_gate",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile: 6 or 8",
        "valid": "6..10",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile: 9 or 10",
        "valid": "9..12",
        "doc": "Exact returned grid width.",
    },
    "n_seeds": {
        "type": "int",
        "default": "scheduled canonical profile: 2 or 3",
        "valid": "2..3",
        "doc": "Exact count of distinct singleton colors other than 0 and 1.",
    },
    "profile": {
        "type": "enum",
        "default": "three-example semantic schedule",
        "valid": "horizontal_gate|open_tie|vertical_gate",
        "doc": "Exact recoverable corridor topology / teaching branch.",
    },
}

# Every product of the exact public domains is constructively supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SEED_COLORS = (2, 3, 4, 5, 6, 7, 8, 9)
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_SYMMETRIES = ("none", "lr", "ud", "lr_ud")
_DEFAULTS = {
    "horizontal_gate": (8, 9, 3),
    "open_tie": (6, 9, 2),
    "vertical_gate": (8, 10, 3),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Cycle all three teaching branches in every consecutive lesson window."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    int_domains = {
        "grid_h": range(6, 11),
        "grid_w": range(9, 13),
        "n_seeds": range(2, 4),
    }
    for name, domain in int_domains.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        if value not in domain:
            raise ValueError(
                f"{name}={value!r} is outside [{min(domain)}, {max(domain)}]"
            )
    if "profile" in overrides and overrides["profile"] is not None:
        value = overrides["profile"]
        if type(value) is not str or value not in SCHEDULE_PROFILES:
            raise ValueError(
                f"profile must be one of {SCHEDULE_PROFILES}, got {value!r}"
            )


def _draw_profile(ctx, seed, sample_index, difficulty):
    scheduled = schedule_profile(seed, sample_index, difficulty)
    if "profile" in ctx.overrides and ctx.overrides["profile"] is not None:
        return ctx.draw_choice("profile", SCHEDULE_PROFILES)
    return ctx.draw_choice("profile", (scheduled,))


def _draw_scheduled_int(ctx, name: str, low: int, high: int, default: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, low, high)
    return ctx.draw_int(name, default, default)


def _base_canvas(height: int, width: int) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    for col in range(width):
        grid[0][col] = 1
        grid[height - 1][col] = 1
    for row in range(height):
        grid[row][0] = 1
        grid[row][width - 1] = 1
    return grid


def _build_open_tie(height: int, width: int, n_seeds: int, gap_offset: int):
    del gap_offset
    grid = _base_canvas(height, width)
    left_col = 1
    right_col = width - 2
    # Force an even separation so the first two seeds have a finite midpoint
    # tie. A third seed on the opposite row cannot dominate that midpoint.
    if (right_col - left_col) % 2:
        right_col -= 1
    positions = [(1, left_col), (1, right_col)]
    if n_seeds == 3:
        positions.append((height - 2, left_col))
    return grid, positions


def _build_horizontal_gate(
    height: int,
    width: int,
    n_seeds: int,
    gap_offset: int,
):
    grid = _base_canvas(height, width)
    barrier_row = height // 2
    gap_col = (width - 1) // 2 + gap_offset
    gap_col = max(2, min(width - 3, gap_col))
    for col in range(width):
        grid[barrier_row][col] = 1
    grid[barrier_row][gap_col] = 0
    if n_seeds == 2:
        positions = [(1, 1), (height - 2, width - 2)]
    else:
        positions = [(1, 1), (1, width - 2), (height - 2, 1)]
    return grid, positions


def _build_vertical_gate(
    height: int,
    width: int,
    n_seeds: int,
    gap_offset: int,
):
    grid = _base_canvas(height, width)
    barrier_col = (width - 1) // 2
    gap_row = (height - 1) // 2 + gap_offset
    gap_row = max(2, min(height - 3, gap_row))
    for row in range(height):
        grid[row][barrier_col] = 1
    grid[gap_row][barrier_col] = 0
    if n_seeds == 2:
        positions = [(1, 1), (height - 2, width - 2)]
    else:
        positions = [(1, 1), (height - 2, 1), (1, width - 2)]
    return grid, positions


def _flip_lr(grid, positions):
    width = len(grid[0])
    return [list(reversed(row)) for row in grid], [
        (row, width - 1 - col) for row, col in positions
    ]


def _flip_ud(grid, positions):
    height = len(grid)
    return [list(row) for row in reversed(grid)], [
        (height - 1 - row, col) for row, col in positions
    ]


def _apply_symmetry(grid, positions, symmetry: str):
    if "lr" in symmetry:
        grid, positions = _flip_lr(grid, positions)
    if "ud" in symmetry:
        grid, positions = _flip_ud(grid, positions)
    return grid, positions


def _difficulty_symmetry(base: str, difficulty) -> str:
    """Keep overrides legal while making the public difficulty knob live."""
    offsets = {None: 0, "easy": 0, "medium": 1, "hard": 2}
    return _SYMMETRIES[
        (_SYMMETRIES.index(base) + offsets[difficulty]) % len(_SYMMETRIES)
    ]


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
    profile = _draw_profile(ctx, seed, sample_index, difficulty)
    default_h, default_w, default_n = _DEFAULTS[profile]
    height = _draw_scheduled_int(ctx, "grid_h", 6, 10, default_h)
    width = _draw_scheduled_int(ctx, "grid_w", 9, 12, default_w)
    n_seeds = _draw_scheduled_int(ctx, "n_seeds", 2, 3, default_n)

    gap_offset = ctx.draw_choice("gate_offset", (-1, 0, 1))
    builders = {
        "open_tie": _build_open_tie,
        "horizontal_gate": _build_horizontal_gate,
        "vertical_gate": _build_vertical_gate,
    }
    grid, positions = builders[profile](height, width, n_seeds, gap_offset)

    base_symmetry = ctx.draw_choice("layout_symmetry", _SYMMETRIES)
    symmetry = _difficulty_symmetry(base_symmetry, difficulty)
    grid, positions = _apply_symmetry(grid, positions, symmetry)

    colors = ctx.draw_rng("seed_colors").sample(list(_SEED_COLORS), n_seeds)
    for (row, col), color in zip(positions, colors):
        if grid[row][col] != 0:
            raise AssertionError(
                f"seed position {(row, col)} overlaps wall color {grid[row][col]}"
            )
        grid[row][col] = color

    findings = self_check(grid)
    if findings:
        raise AssertionError("constructed invalid grid: " + "; ".join(findings))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_seeds": n_seeds,
        "profile": profile,
    }
    if observed != expected:
        raise AssertionError(f"override observer drift: expected {expected}, got {observed}")
    return grid


# ---------------------------------------------------------------------------
# Grammar validation and exact override observation
# ---------------------------------------------------------------------------


def _shape_error(grid) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a nonempty row sequence"
    if not all(isinstance(row, (list, tuple)) for row in grid) or not grid[0]:
        return "grid rows must be nonempty sequences"
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return "ragged grid"
    return None


def _seed_cells(grid):
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 1)
    ]


def _interior_wall_profile(grid) -> tuple[str | None, str | None]:
    height, width = len(grid), len(grid[0])
    walls = {
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] == 1
    }
    if not walls:
        return "open_tie", None

    wall_rows = {row for row, _ in walls}
    wall_cols = {col for _, col in walls}
    if len(wall_rows) == 1:
        row = next(iter(wall_rows))
        gaps = [col for col in range(1, width - 1) if grid[row][col] != 1]
        expected = {(row, col) for col in range(1, width - 1) if col not in gaps}
        if len(gaps) == 1 and grid[row][gaps[0]] == 0 and walls == expected:
            return "horizontal_gate", None
        return None, "horizontal barrier must contain exactly one zero gap"
    if len(wall_cols) == 1:
        col = next(iter(wall_cols))
        gaps = [row for row in range(1, height - 1) if grid[row][col] != 1]
        expected = {(row, col) for row in range(1, height - 1) if row not in gaps}
        if len(gaps) == 1 and grid[gaps[0]][col] == 0 and walls == expected:
            return "vertical_gate", None
        return None, "vertical barrier must contain exactly one zero gap"
    return None, "interior color-1 walls must form one horizontal or vertical barrier"


def _reachable_nonwalls(grid, starts):
    height, width = len(grid), len(grid[0])
    seen = set(starts)
    queue = deque(starts)
    while queue:
        row, col = queue.popleft()
        for dr, dc in _DIR4:
            nr, nc = row + dr, col + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 1
                and (nr, nc) not in seen
            ):
                seen.add((nr, nc))
                queue.append((nr, nc))
    return seen


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the selected task grammar from pixels, including canonicals."""
    del difficulty, meta
    error = _shape_error(grid)
    if error:
        return [error]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if not (6 <= height <= 10):
        errors.append(f"grid height must be 6..10, found {height}")
    if not (9 <= width <= 12):
        errors.append(f"grid width must be 9..12, found {width}")
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell {(row, col)} must be an integer ARC color 0..9, found {value!r}"
                )
                if len(errors) >= 5:
                    return errors
    if errors:
        return errors

    boundary = (
        [(0, col) for col in range(width)]
        + [(height - 1, col) for col in range(width)]
        + [(row, 0) for row in range(1, height - 1)]
        + [(row, width - 1) for row in range(1, height - 1)]
    )
    broken = next(((row, col) for row, col in boundary if grid[row][col] != 1), None)
    if broken is not None:
        errors.append(f"color-1 boundary frame is incomplete at {broken}")

    profile, profile_error = _interior_wall_profile(grid)
    if profile_error:
        errors.append(profile_error)

    seeds = _seed_cells(grid)
    if len(seeds) not in (2, 3):
        errors.append(f"expected exactly two or three seeds, found {len(seeds)}")
    colors = [color for _, _, color in seeds]
    if len(colors) != len(set(colors)):
        errors.append("seed colors must be globally distinct singleton colors")
    for row, col, _ in seeds:
        if not (1 <= row < height - 1 and 1 <= col < width - 1):
            errors.append(f"seed {(row, col)} must lie strictly inside the frame")

    if not any(
        grid[row][col] == 0
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ):
        errors.append("frame interior must contain at least one zero cell")

    if seeds and not errors:
        reachable = _reachable_nonwalls(grid, [(row, col) for row, col, _ in seeds])
        unreachable = next(
            (
                (row, col)
                for row in range(1, height - 1)
                for col in range(1, width - 1)
                if grid[row][col] != 1 and (row, col) not in reachable
            ),
            None,
        )
        if unreachable is not None:
            errors.append(f"non-wall cell {unreachable} is unreachable from every seed")

    # Keep `profile` live in validation so malformed wall layouts cannot hide
    # behind otherwise plausible dimensions and seed counts.
    if profile is None and profile_error is None:
        errors.append("could not recover a declared semantic profile")
    return errors


def strict_canonical_like(grid):
    """Generated inputs stay on the measured framed-corridor manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    profile, error = _interior_wall_profile(grid)
    if error or profile is None:
        raise ValueError(error or "could not recover profile")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_seeds": len(_seed_cells(grid)),
        "profile": profile,
    }


# ---------------------------------------------------------------------------
# Selected-rule mirror and task-linked rivals
# ---------------------------------------------------------------------------


def _neighbors(point, height, width):
    row, col = point
    for dr, dc in _DIR4:
        nr, nc = row + dr, col + dc
        if 0 <= nr < height and 0 <= nc < width:
            yield nr, nc


def _distance_map(grid, start):
    height, width = len(grid), len(grid[0])
    distance = {start: 0}
    queue = deque([start])
    while queue:
        point = queue.popleft()
        for nxt in _neighbors(point, height, width):
            if grid[nxt[0]][nxt[1]] != 1 and nxt not in distance:
                distance[nxt] = distance[point] + 1
                queue.append(nxt)
    return distance


def _seed_distance_maps(grid, seeds=None):
    selected = _seed_cells(grid) if seeds is None else seeds
    return [
        (color, _distance_map(grid, (row, col)))
        for row, col, color in selected
    ]


def _geodesic_output(grid, *, seeds=None, break_ties=False):
    output = deepcopy(grid)
    maps = _seed_distance_maps(grid, seeds=seeds)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                continue
            options = [
                (distance[(row, col)], color)
                for color, distance in maps
                if (row, col) in distance
            ]
            if not options:
                continue
            best = min(distance for distance, _ in options)
            winners = sorted(color for distance, color in options if distance == best)
            if len(winners) == 1 or break_ties:
                output[row][col] = winners[0]
    return output


def rule_mirror(grid):
    """Pure-Python mirror of the selected canonical Racket authority."""
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    return _geodesic_output(grid)


def _rival_wall_blind_manhattan(grid):
    """Wrong rule: use direct Manhattan distance and ignore wall detours."""
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    seeds = _seed_cells(grid)
    output = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                continue
            options = [
                (abs(row - sr) + abs(col - sc), color)
                for sr, sc, color in seeds
            ]
            best = min(distance for distance, _ in options)
            winners = {color for distance, color in options if distance == best}
            if len(winners) == 1:
                output[row][col] = next(iter(winners))
    return output


def _rival_break_ties_low_color(grid):
    """Wrong rule: assign a deterministic color instead of preserving ties."""
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    return _geodesic_output(grid, break_ties=True)


def _rival_drop_highest_seed(grid):
    """Wrong rule: ignore the numerically highest seed during propagation."""
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    seeds = _seed_cells(grid)
    highest = max(color for _, _, color in seeds)
    retained = [seed for seed in seeds if seed[2] != highest]
    return _geodesic_output(grid, seeds=retained)


def _has_finite_tie(grid) -> bool:
    maps = _seed_distance_maps(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                continue
            options = [
                distance[(row, col)]
                for _, distance in maps
                if (row, col) in distance
            ]
            if options:
                best = min(options)
                if sum(distance == best for distance in options) >= 2:
                    return True
    return False


def _has_wall_aware_distance(grid) -> bool:
    return rule_mirror(grid) != _rival_wall_blind_manhattan(grid)


def _all_seed_colors_compete(grid) -> bool:
    seeds = _seed_cells(grid)
    if len(seeds) != 3:
        return False
    output = rule_mirror(grid)
    return all(
        sum(value == color for values in output for value in values) > 1
        for _, _, color in seeds
    )


SEMANTIC_WITNESSES = {
    "finite_tie_stays_zero": _has_finite_tie,
    "wall_aware_distance": _has_wall_aware_distance,
    "all_seed_colors_compete": _all_seed_colors_compete,
}

SEMANTIC_RIVALS = {
    "break_ties_low_color": _rival_break_ties_low_color,
    "wall_blind_manhattan": _rival_wall_blind_manhattan,
    "drop_highest_seed": _rival_drop_highest_seed,
}

WITNESS_RIVALS = {
    "finite_tie_stays_zero": ["break_ties_low_color"],
    "wall_aware_distance": ["wall_blind_manhattan"],
    "all_seed_colors_compete": ["drop_highest_seed"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Every named rival is already falsified by at least one labeled canonical pair.
CANONICAL_SHORTCUTS = {}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a named plausible wrong rule survives all demos."""
    reasons: list[str] = []
    normalized_demos = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with blocked nearest-seed BFS")
        normalized_demos.append((demo["input"], expected))
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with blocked nearest-seed BFS")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(grid) == expected for grid, expected in normalized_demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons
