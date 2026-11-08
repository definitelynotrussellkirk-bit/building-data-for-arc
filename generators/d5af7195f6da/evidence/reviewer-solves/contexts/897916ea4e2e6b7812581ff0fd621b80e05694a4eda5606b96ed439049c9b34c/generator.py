"""Generator for d5af7195f6da: roomwise nearest-seed fill.

Color 5 is an impassable wall.  Every other non-zero cell is a seed.  A zero
cell receives the color of its uniquely nearest *seed color* under four-neighbor
shortest-path distance through non-wall cells.  A finite tie between different
colors, or a cell unreachable from every seed, remains zero.  Walls and seeds
are preserved.

Seven default demonstrations plus one query form a rotation-safe lesson. The
period-four schedule repeats every profile twice across those eight pairs:

* ``distinct_tie`` proves that a finite tie between different colors stays 0;
* ``wall_detour`` makes geodesic distance disagree with component Manhattan;
* ``seedless_chamber`` leaves an unreachable chamber unchanged;
* ``same_color_tie`` proves that ties are deduplicated by color, not seed cell.

Every public override is exact, recoverable from the returned pixels, and valid
in every difficulty band.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d5af7195f6da"
TASK_ID = GENERATOR_ID
RULE_HASH = "ca2bc3cf692f"
VERSION = "4.2.0"
EXAMPLES_NEEDED = 7
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 7-row color-5 arena contains two to four singleton seed cells. Zeros "
    "take the unique nearest seed COLOR by wall-aware four-neighbor BFS; "
    "different-color ties and seedless chambers stay zero. Four scheduled "
    "profiles guarantee evidence for ties, wall detours, unreachable cells, "
    "and equal-distance same-color seeds. Seven demonstrations provide one spare "
    "copy of every profile so any of the eight pairs can be held out as query."
)

INVARIANTS = [
    "grids are 7 rows by 9..11 columns and use only integer ARC colors 0..9",
    "color 5 is an impassable wall and every other non-zero cell is a seed",
    "there are exactly 2..4 singleton seed cells and at least one zero cell",
    "each eight-pair lesson contains every semantic profile twice for rotated holdouts",
]

SCHEDULE_PROFILES = (
    "distinct_tie",
    "wall_detour",
    "seedless_chamber",
    "same_color_tie",
)

AXES = {
    "grid_w": {
        "type": "int",
        "default": "9 on easy, 9|11 on medium/None, 11 on hard",
        "valid": "9..11",
        "doc": "Exact returned grid width; height is fixed at canonical 7.",
    },
    "n_seed_cells": {
        "type": "int",
        "default": "profile/difficulty schedule over 2..4",
        "valid": "2..4",
        "doc": "Exact number of non-{0,5} seed cells.",
    },
    "profile": {
        "type": "enum",
        "default": "period-four schedule; seven demos plus one query",
        "valid": "|".join(SCHEDULE_PROFILES),
        "doc": "Exact recoverable wall topology / semantic lesson profile.",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SEED_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_SYMMETRIES = ("none", "lr", "ud", "lr_ud")
_HEIGHT = 7


def schedule_profile(seed, sample_index, difficulty=None):
    """Cycle four profiles; an eight-pair lesson contains each profile twice."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    for name, domain in {
        "grid_w": range(9, 12),
        "n_seed_cells": range(2, 5),
    }.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
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


def _draw_width(ctx, difficulty):
    if "grid_w" in ctx.overrides and ctx.overrides["grid_w"] is not None:
        return ctx.draw_choice("grid_w", (9, 10, 11))
    options = {
        "easy": (9,),
        "medium": (9, 11),
        "hard": (11,),
        None: (9, 11),
    }[difficulty]
    return ctx.draw_choice("grid_w", options)


def _draw_seed_count(ctx, profile, difficulty):
    if (
        "n_seed_cells" in ctx.overrides
        and ctx.overrides["n_seed_cells"] is not None
    ):
        return ctx.draw_choice("n_seed_cells", (2, 3, 4))
    if profile == "distinct_tie":
        # Every lesson carries a canonical-palette anchor in this slot.
        options = (2,)
    else:
        options = {
            "easy": (2,),
            "medium": (3,),
            "hard": (4,),
            None: (2, 3, 4),
        }[difficulty]
    return ctx.draw_choice("n_seed_cells", options)


def _base_canvas(width: int) -> list[list[int]]:
    grid = full_grid(_HEIGHT, width, 0)
    for col in range(width):
        grid[0][col] = 5
        grid[_HEIGHT - 1][col] = 5
    for row in range(_HEIGHT):
        grid[row][0] = 5
        grid[row][width - 1] = 5
    return grid


def _tie_columns(width: int) -> tuple[int, int]:
    left = 1
    right = width - 2
    if (right - left) % 2:
        right -= 1
    return left, right


def _build_distinct_tie(width: int, n_seed_cells: int):
    grid = _base_canvas(width)
    left, right = _tie_columns(width)
    positions = [(1, left), (1, right)]
    extras = [(5, left), (5, right)]
    positions.extend(extras[: n_seed_cells - 2])
    return grid, positions


def _build_same_color_tie(width: int, n_seed_cells: int):
    # Geometry matches distinct_tie; only the first two seed colors coincide.
    return _build_distinct_tie(width, n_seed_cells)


def _build_wall_detour(width: int, n_seed_cells: int):
    grid = _base_canvas(width)
    barrier_col = width // 2
    for row in range(1, 5):
        grid[row][barrier_col] = 5
    positions = [(1, barrier_col - 1), (5, barrier_col + 1)]
    extras = [(5, 1), (3, 1)]
    positions.extend(extras[: n_seed_cells - 2])
    return grid, positions


def _build_seedless_chamber(width: int, n_seed_cells: int):
    grid = _base_canvas(width)
    barrier_col = width // 2
    for row in range(1, 6):
        grid[row][barrier_col] = 5
    positions = [(1, 1), (5, 1)]
    extras = [(3, barrier_col - 1), (1, barrier_col - 1)]
    positions.extend(extras[: n_seed_cells - 2])
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


def _apply_symmetry(grid, positions, symmetry):
    if "lr" in symmetry:
        grid, positions = _flip_lr(grid, positions)
    if "ud" in symmetry:
        grid, positions = _flip_ud(grid, positions)
    return grid, positions


def _difficulty_symmetry(base, difficulty):
    offsets = {None: 0, "easy": 0, "medium": 1, "hard": 2}
    return _SYMMETRIES[
        (_SYMMETRIES.index(base) + offsets[difficulty]) % len(_SYMMETRIES)
    ]


def _draw_seed_colors(seed, sample_index, profile, n_seed_cells):
    """Choose collision-resistant colors for repeated curriculum profiles.

    The production materializer rejects byte-identical inputs.  A profile occurs
    again four sample indices later, so rotate its palette by the occurrence
    number.  Consecutive copies therefore cannot collapse to one accepted pair,
    even when a symmetry happens to permute the seed positions.
    """
    profile_index = SCHEDULE_PROFILES.index(profile)
    occurrence = int(sample_index) // len(SCHEDULE_PROFILES)
    offset = (int(seed) * 5 + profile_index * 3 + occurrence) % len(_SEED_COLORS)
    ordered = list(_SEED_COLORS[offset:] + _SEED_COLORS[:offset])
    if profile == "same_color_tie":
        return [ordered[0], ordered[0], *ordered[1 : n_seed_cells - 1]]
    return ordered[:n_seed_cells]


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
    width = _draw_width(ctx, difficulty)
    n_seed_cells = _draw_seed_count(ctx, profile, difficulty)

    builders = {
        "distinct_tie": _build_distinct_tie,
        "wall_detour": _build_wall_detour,
        "seedless_chamber": _build_seedless_chamber,
        "same_color_tie": _build_same_color_tie,
    }
    grid, positions = builders[profile](width, n_seed_cells)
    base_symmetry = ctx.draw_choice("layout_symmetry", _SYMMETRIES)
    symmetry = _difficulty_symmetry(base_symmetry, difficulty)
    grid, positions = _apply_symmetry(grid, positions, symmetry)

    colors = _draw_seed_colors(seed, sample_index, profile, n_seed_cells)
    for (row, col), color in zip(positions, colors):
        if grid[row][col] != 0:
            raise AssertionError(
                f"seed position {(row, col)} overlaps wall color {grid[row][col]}"
            )
        grid[row][col] = color

    findings = self_check(grid)
    if findings:
        raise AssertionError("constructed invalid grid: " + "; ".join(findings))
    expected = {
        "grid_w": width,
        "n_seed_cells": n_seed_cells,
        "profile": profile,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(
            f"override observer drift: expected {expected}, got {observed}"
        )
    return grid


# ---------------------------------------------------------------------------
# Grammar validation and override observation
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
        if value not in (0, 5)
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the selected task grammar from pixels, including canonicals."""
    del difficulty
    error = _shape_error(grid)
    if error:
        return [error]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if height != _HEIGHT:
        errors.append(f"grid height must be {_HEIGHT}, found {height}")
    if not (9 <= width <= 11):
        errors.append(f"grid width must be 9..11, found {width}")

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

    seeds = _seed_cells(grid)
    if not (2 <= len(seeds) <= 4):
        errors.append(f"expected 2..4 seed cells, found {len(seeds)}")
    if not any(value == 5 for values in grid for value in values):
        errors.append("expected at least one color-5 wall cell")
    if not any(value == 0 for values in grid for value in values):
        errors.append("expected at least one zero cell for the rule to transform")

    for row, col, color in seeds:
        for dr, dc in _DIR4:
            nr, nc = row + dr, col + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] == color
            ):
                errors.append(
                    f"same-color adjacent seed cells at {(row, col)} and {(nr, nc)} "
                    "form a motif rather than singleton seeds"
                )
                break
        if errors and len(errors) >= 5:
            return errors

    if meta and meta.get("overrides") and not errors:
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(f"override observer failed: {exc}")
        else:
            for name, expected in meta["overrides"].items():
                if expected is not None and observed.get(name) != expected:
                    errors.append(
                        f"override {name}={expected!r} was not realized; "
                        f"observed {observed.get(name)!r}"
                    )
    return errors


def strict_canonical_like(grid):
    """Default samples stay on the measured canonical dimensions and grammar."""
    errors = self_check(grid)
    if errors:
        return errors
    if len(grid[0]) not in (9, 11):
        return [f"strict canonical width must be 9 or 11, found {len(grid[0])}"]
    return []


def _has_complete_outer_frame(grid) -> bool:
    height, width = len(grid), len(grid[0])
    return (
        all(grid[0][col] == 5 and grid[height - 1][col] == 5 for col in range(width))
        and all(grid[row][0] == 5 and grid[row][width - 1] == 5 for row in range(height))
    )


def _observe_profile(grid) -> str:
    if not _has_complete_outer_frame(grid):
        raise ValueError("generated-profile observer requires a complete outer wall frame")
    interior_walls = {
        (row, col)
        for row in range(1, len(grid) - 1)
        for col in range(1, len(grid[0]) - 1)
        if grid[row][col] == 5
    }
    if not interior_walls:
        colors = [color for _, _, color in _seed_cells(grid)]
        return "same_color_tie" if len(colors) != len(set(colors)) else "distinct_tie"

    rows = {row for row, _ in interior_walls}
    cols = {col for _, col in interior_walls}
    spans_column = len(cols) == 1 and rows <= set(range(1, 6))
    spans_row = len(rows) == 1 and cols <= set(range(1, len(grid[0]) - 1))
    if not (spans_column or spans_row):
        raise ValueError("interior walls do not match a scheduled divider topology")
    span = rows if spans_column else cols
    full_span = set(range(1, 6)) if spans_column else set(range(1, len(grid[0]) - 1))
    if span == full_span:
        return "seedless_chamber"
    if len(span) == len(full_span) - 1 and (
        min(full_span) not in span or max(full_span) not in span
    ):
        return "wall_detour"
    raise ValueError("interior divider is neither complete nor one-end-open")


def observe_overrides(grid) -> dict[str, int | str]:
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    return {
        "grid_w": len(grid[0]),
        "n_seed_cells": len(_seed_cells(grid)),
        "profile": _observe_profile(grid),
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
            if grid[nxt[0]][nxt[1]] != 5 and nxt not in distance:
                distance[nxt] = distance[point] + 1
                queue.append(nxt)
    return distance


def _seed_distance_maps(grid):
    return [
        (color, _distance_map(grid, (row, col)))
        for row, col, color in _seed_cells(grid)
    ]


def _geodesic_output(grid, *, break_distinct_ties=False, require_unique_seed=False):
    output = deepcopy(grid)
    maps = _seed_distance_maps(grid)
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
            nearest = [color for distance, color in options if distance == best]
            winning_colors = sorted(set(nearest))
            if require_unique_seed:
                if len(nearest) == 1:
                    output[row][col] = nearest[0]
            elif len(winning_colors) == 1:
                output[row][col] = winning_colors[0]
            elif break_distinct_ties:
                output[row][col] = winning_colors[0]
    return output


def rule_mirror(grid):
    """Pure-Python mirror of the pinned canonical Racket authority."""
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    return _geodesic_output(grid)


def _component_ids(grid):
    height, width = len(grid), len(grid[0])
    ids: dict[tuple[int, int], int] = {}
    component_id = 0
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5 or (row, col) in ids:
                continue
            ids[(row, col)] = component_id
            queue = deque([(row, col)])
            while queue:
                point = queue.popleft()
                for nxt in _neighbors(point, height, width):
                    if grid[nxt[0]][nxt[1]] != 5 and nxt not in ids:
                        ids[nxt] = component_id
                        queue.append(nxt)
            component_id += 1
    return ids


def _rival_break_distinct_ties_low_color(grid):
    """Wrong rule: deterministically fill finite different-color ties."""
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    return _geodesic_output(grid, break_distinct_ties=True)


def _rival_component_manhattan(grid):
    """Wrong rule: walls split chambers but never lengthen paths within one."""
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    components = _component_ids(grid)
    seeds = _seed_cells(grid)
    output = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                continue
            options = [
                (abs(row - sr) + abs(col - sc), color)
                for sr, sc, color in seeds
                if components.get((sr, sc)) == components.get((row, col))
            ]
            if not options:
                continue
            best = min(distance for distance, _ in options)
            winners = {color for distance, color in options if distance == best}
            if len(winners) == 1:
                output[row][col] = next(iter(winners))
    return output


def _rival_fill_seedless_chambers(grid):
    """Wrong rule: globally Manhattan-fill cells unreachable from every seed."""
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    output = _geodesic_output(grid)
    maps = _seed_distance_maps(grid)
    seeds = _seed_cells(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                continue
            if any((row, col) in distance for _, distance in maps):
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


def _rival_unique_seed_ties_blank(grid):
    """Wrong rule: tie by seed-cell identity rather than distinct seed color."""
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    return _geodesic_output(grid, require_unique_seed=True)


def _has_distinct_color_tie_stays_zero(grid) -> bool:
    true_output = rule_mirror(grid)
    rival = _rival_break_distinct_ties_low_color(grid)
    return any(
        grid[row][col] == 0
        and true_output[row][col] == 0
        and rival[row][col] != 0
        for row in range(len(grid))
        for col in range(len(grid[0]))
    )


def _has_wall_aware_distance(grid) -> bool:
    return rule_mirror(grid) != _rival_component_manhattan(grid)


def _has_unreachable_stays_zero(grid) -> bool:
    maps = _seed_distance_maps(grid)
    return any(
        grid[row][col] == 0
        and not any((row, col) in distance for _, distance in maps)
        for row in range(len(grid))
        for col in range(len(grid[0]))
    )


def _has_same_color_tie_fills(grid) -> bool:
    true_output = rule_mirror(grid)
    rival = _rival_unique_seed_ties_blank(grid)
    return any(
        grid[row][col] == 0
        and true_output[row][col] != 0
        and rival[row][col] == 0
        for row in range(len(grid))
        for col in range(len(grid[0]))
    )


SEMANTIC_WITNESSES = {
    "distinct_color_tie_stays_zero": _has_distinct_color_tie_stays_zero,
    "wall_aware_distance": _has_wall_aware_distance,
    "unreachable_stays_zero": _has_unreachable_stays_zero,
    "same_color_tie_fills": _has_same_color_tie_fills,
}

SEMANTIC_RIVALS = {
    "break_distinct_ties_low_color": _rival_break_distinct_ties_low_color,
    "component_manhattan": _rival_component_manhattan,
    "fill_seedless_chambers": _rival_fill_seedless_chambers,
    "unique_seed_ties_blank": _rival_unique_seed_ties_blank,
}

WITNESS_RIVALS = {
    "distinct_color_tie_stays_zero": ["break_distinct_ties_low_color"],
    "wall_aware_distance": ["component_manhattan"],
    "unreachable_stays_zero": ["fill_seedless_chambers"],
    "same_color_tie_fills": ["unique_seed_ties_blank"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# These three wrong rules fit every canonical pair. The scheduled generated
# lesson provides the missing disambiguating evidence without changing the
# pinned authority.
CANONICAL_SHORTCUTS = {
    "component_manhattan": _rival_component_manhattan,
    "fill_seedless_chambers": _rival_fill_seedless_chambers,
    "unique_seed_ties_blank": _rival_unique_seed_ties_blank,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a declared plausible wrong rule can change its query."""
    reasons: list[str] = []
    normalized_demos = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with wall-aware BFS")
        normalized_demos.append((demo["input"], expected))

    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with wall-aware BFS")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(grid) == expected for grid, expected in normalized_demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons
