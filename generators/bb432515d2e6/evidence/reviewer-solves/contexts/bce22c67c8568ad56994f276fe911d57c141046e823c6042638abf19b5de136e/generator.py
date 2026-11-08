"""Generator for bb432515d2e6: blocked geodesic Voronoi.

Color 5 is an impassable wall.  Every other non-zero cell is a uniquely
colored seed.  A zero cell receives the color of its unique nearest seed under
4-neighbour shortest-path distance through non-wall cells; finite ties and
seedless components remain zero.  Walls and seeds are preserved.

Three consecutive default examples deliberately form a complete lesson:

* ``open_tie`` contains a finite equal-distance locus, so ties must stay zero;
* ``wall_detour`` makes geodesic distance disagree with component-local
  Manhattan distance;
* ``seedless_chamber`` contains an interior chamber unreachable from every
  seed, so it must remain zero.

Every public override is exact, observable from the returned pixels, and valid
in every difficulty band.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "bb432515d2e6"
TASK_ID = GENERATOR_ID
RULE_HASH = "823ef34eb751"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A closed color-5 frame contains two or three distinct-colored seeds. "
    "Zeros take the unique nearest seed color by wall-aware 4-neighbor BFS; "
    "finite ties and seedless chambers remain zero. Three scheduled profiles "
    "guarantee tie, wall-detour, and unreachable-component evidence."
)

INVARIANTS = [
    "grid size is 10..12 by 11..14 and all cells are ARC colors 0..9",
    "all color-5 cells lie on or inside one complete rectangular wall frame",
    "outside the frame is zero and every seed lies strictly inside the frame",
    "there are exactly two or three singleton seeds with globally distinct colors excluding 0 and 5",
    "three consecutive defaults cover finite tie, geodesic detour, and seedless-chamber profiles",
]

SCHEDULE_PROFILES = (
    "open_tie",
    "wall_detour",
    "seedless_chamber",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "keyed draw 10..12",
        "valid": "10..12",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "keyed draw 11..14",
        "valid": "11..14",
        "doc": "Exact returned grid width.",
    },
    "n_seeds": {
        "type": "int",
        "default": "keyed draw 2..3",
        "valid": "2..3",
        "doc": "Exact count of distinct singleton non-{0,5} seeds.",
    },
    "profile": {
        "type": "enum",
        "default": "three-example semantic schedule",
        "valid": "open_tie|wall_detour|seedless_chamber",
        "doc": "Exact recoverable wall topology / semantic lesson profile.",
    },
}

# Every product of the exact public domains is constructively supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SEED_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_SYMMETRIES = ("none", "lr", "ud", "lr_ud")


def schedule_profile(seed, sample_index, difficulty=None):
    """Cycle all three teaching branches in every consecutive lesson window."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    int_domains = {
        "grid_h": range(10, 13),
        "grid_w": range(11, 15),
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


def _frame_bounds(height: int, width: int) -> tuple[int, int, int, int]:
    return 1, 1, height - 2, width - 2


def _interior_bounds(height: int, width: int) -> tuple[int, int, int, int]:
    r0, c0, r1, c1 = _frame_bounds(height, width)
    return r0 + 1, c0 + 1, r1 - 1, c1 - 1


def _base_canvas(height: int, width: int) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    draw_frame(grid, *_frame_bounds(height, width), 5)
    return grid


def _build_open_tie(height: int, width: int, n_seeds: int):
    grid = _base_canvas(height, width)
    row_top, col_left, row_bottom, col_right = _interior_bounds(height, width)
    # Force an even horizontal separation. The midpoint is a finite tie for the
    # first two seeds; a third seed on the opposite row cannot dominate it.
    second_col = col_right
    if (second_col - col_left) % 2:
        second_col -= 1
    positions = [(row_top, col_left), (row_top, second_col)]
    if n_seeds == 3:
        positions.append((row_bottom, col_left))
    return grid, positions


def _build_wall_detour(height: int, width: int, n_seeds: int):
    grid = _base_canvas(height, width)
    row_top, col_left, row_bottom, col_right = _interior_bounds(height, width)
    barrier_col = (col_left + col_right) // 2
    # Attach to the top frame and leave exactly one open row at the bottom.
    # Cells on the far side must route around that gap.
    for row in range(row_top, row_bottom):
        grid[row][barrier_col] = 5
    positions = [(row_top, col_left), (row_bottom, col_left)]
    if n_seeds == 3:
        positions.append((row_bottom, col_right))
    return grid, positions


def _build_seedless_chamber(height: int, width: int, n_seeds: int):
    grid = _base_canvas(height, width)
    row_top, col_left, row_bottom, col_right = _interior_bounds(height, width)
    barrier_col = (col_left + col_right) // 2
    # A complete frame-to-frame separator creates a seedless right chamber.
    for row in range(row_top, row_bottom + 1):
        grid[row][barrier_col] = 5
    positions = [(row_top, col_left), (row_bottom, col_left)]
    if n_seeds == 3:
        positions.append(((row_top + row_bottom) // 2, barrier_col - 1))
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
    """Keep every override legal while making the public difficulty knob live."""
    offsets = {None: 0, "easy": 0, "medium": 1, "hard": 2}
    return _SYMMETRIES[(_SYMMETRIES.index(base) + offsets[difficulty]) % len(_SYMMETRIES)]


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
    height = ctx.draw_int("grid_h", 10, 12)
    width = ctx.draw_int("grid_w", 11, 14)
    n_seeds = ctx.draw_int("n_seeds", 2, 3)
    profile = _draw_profile(ctx, seed, sample_index, difficulty)

    builders = {
        "open_tie": _build_open_tie,
        "wall_detour": _build_wall_detour,
        "seedless_chamber": _build_seedless_chamber,
    }
    grid, positions = builders[profile](height, width, n_seeds)
    base_symmetry = ctx.draw_choice("layout_symmetry", _SYMMETRIES)
    symmetry = _difficulty_symmetry(base_symmetry, difficulty)
    grid, positions = _apply_symmetry(grid, positions, symmetry)

    colors = ctx.draw_rng("seed_colors").sample(list(_SEED_COLORS), n_seeds)
    for (row, col), color in zip(positions, colors):
        if grid[row][col] != 0:
            raise AssertionError(f"seed position {(row, col)} overlaps wall color {grid[row][col]}")
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


def _wall_frame_box(grid) -> tuple[int, int, int, int]:
    walls = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if not walls:
        raise ValueError("no color-5 wall cells")
    rows = [row for row, _ in walls]
    cols = [col for _, col in walls]
    r0, c0, r1, c1 = min(rows), min(cols), max(rows), max(cols)
    if r1 - r0 < 3 or c1 - c0 < 3:
        raise ValueError(f"wall frame is too small: {(r0, c0, r1, c1)}")
    perimeter = (
        {(r0, col) for col in range(c0, c1 + 1)}
        | {(r1, col) for col in range(c0, c1 + 1)}
        | {(row, c0) for row in range(r0, r1 + 1)}
        | {(row, c1) for row in range(r0, r1 + 1)}
    )
    missing = sorted(point for point in perimeter if grid[point[0]][point[1]] != 5)
    if missing:
        raise ValueError(f"wall frame perimeter is incomplete at {missing[0]}")
    return r0, c0, r1, c1


def _seed_cells(grid):
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5)
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task grammar from pixels only, including canonical inputs."""
    del difficulty, meta
    error = _shape_error(grid)
    if error:
        return [error]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if not (10 <= height <= 12):
        errors.append(f"grid height must be 10..12, found {height}")
    if not (11 <= width <= 14):
        errors.append(f"grid width must be 11..14, found {width}")
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

    try:
        r0, c0, r1, c1 = _wall_frame_box(grid)
    except ValueError as exc:
        return [str(exc)]
    if r0 < 1 or c0 < 1 or r1 > height - 2 or c1 > width - 2:
        errors.append("wall frame must leave at least one zero margin cell on every side")

    for row in range(height):
        for col in range(width):
            if not (r0 <= row <= r1 and c0 <= col <= c1) and grid[row][col] != 0:
                errors.append(
                    f"outside-frame cell {(row, col)} must be 0, found {grid[row][col]}"
                )
                if len(errors) >= 5:
                    return errors

    seeds = _seed_cells(grid)
    if len(seeds) not in (2, 3):
        errors.append(f"expected exactly two or three seeds, found {len(seeds)}")
    colors = [color for _, _, color in seeds]
    if len(colors) != len(set(colors)):
        errors.append("seed colors must be globally distinct singleton colors")
    for row, col, _ in seeds:
        if not (r0 < row < r1 and c0 < col < c1):
            errors.append(f"seed {(row, col)} must lie strictly inside the frame")
    interior_zeros = sum(
        grid[row][col] == 0
        for row in range(r0 + 1, r1)
        for col in range(c0 + 1, c1)
    )
    if interior_zeros == 0:
        errors.append("frame interior must contain at least one zero cell")
    return errors


def strict_canonical_like(grid):
    """The generated grammar is deliberately the measured canonical manifold."""
    return self_check(grid)


def _interior_wall_cells(grid, box):
    r0, c0, r1, c1 = box
    return {
        (row, col)
        for row in range(r0 + 1, r1)
        for col in range(c0 + 1, c1)
        if grid[row][col] == 5
    }


def _observe_profile(grid, box) -> str:
    r0, c0, r1, c1 = box
    interior_walls = _interior_wall_cells(grid, box)
    if not interior_walls:
        return "open_tie"
    full_col = any(
        all(grid[row][col] == 5 for row in range(r0 + 1, r1))
        for col in range(c0 + 1, c1)
    )
    full_row = any(
        all(grid[row][col] == 5 for col in range(c0 + 1, c1))
        for row in range(r0 + 1, r1)
    )
    return "seedless_chamber" if (full_col or full_row) else "wall_detour"


def observe_overrides(grid) -> dict[str, int | str]:
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    box = _wall_frame_box(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_seeds": len(_seed_cells(grid)),
        "profile": _observe_profile(grid, box),
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


def _geodesic_output(grid, *, break_ties=False):
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


def _rival_component_manhattan(grid):
    """Wrong rule: walls split components but do not lengthen paths within one."""
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


def _rival_break_ties_low_color(grid):
    """Wrong rule: assign a deterministic color rather than preserving a tie."""
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    return _geodesic_output(grid, break_ties=True)


def _rival_fill_seedless_chambers(grid):
    """Wrong rule: fill unreachable in-frame cells from the global nearest seed."""
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    output = _geodesic_output(grid)
    maps = _seed_distance_maps(grid)
    seeds = _seed_cells(grid)
    r0, c0, r1, c1 = _wall_frame_box(grid)
    for row in range(r0 + 1, r1):
        for col in range(c0 + 1, c1):
            if grid[row][col] != 0:
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


def _has_finite_tie(grid) -> bool:
    maps = _seed_distance_maps(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                continue
            options = [distance[(row, col)] for _, distance in maps if (row, col) in distance]
            if options:
                best = min(options)
                if sum(distance == best for distance in options) >= 2:
                    return True
    return False


def _has_wall_aware_distance(grid) -> bool:
    return rule_mirror(grid) != _rival_component_manhattan(grid)


def _has_unreachable_interior(grid) -> bool:
    maps = _seed_distance_maps(grid)
    r0, c0, r1, c1 = _wall_frame_box(grid)
    return any(
        grid[row][col] == 0
        and not any((row, col) in distance for _, distance in maps)
        for row in range(r0 + 1, r1)
        for col in range(c0 + 1, c1)
    )


SEMANTIC_WITNESSES = {
    "finite_tie_stays_zero": _has_finite_tie,
    "wall_aware_distance": _has_wall_aware_distance,
    "unreachable_stays_zero": _has_unreachable_interior,
}

SEMANTIC_RIVALS = {
    "break_ties_low_color": _rival_break_ties_low_color,
    "component_manhattan": _rival_component_manhattan,
    "fill_seedless_chambers": _rival_fill_seedless_chambers,
}

WITNESS_RIVALS = {
    "finite_tie_stays_zero": ["break_ties_low_color"],
    "wall_aware_distance": ["component_manhattan"],
    "unreachable_stays_zero": ["fill_seedless_chambers"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# All three named rivals are already falsified by at least one canonical pair.
# Keep them as generated-lesson competitors, not canonical-ambiguous shortcuts.
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
            reasons.append(f"demo {index} output disagrees with blocked BFS")
        normalized_demos.append((demo["input"], expected))
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with blocked BFS")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(grid) == expected for grid, expected in normalized_demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons
