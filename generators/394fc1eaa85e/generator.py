"""Semantic generator for ARC task 394fc1eaa85e.

Treat color 5 as an impassable wall.  From the unique red (2) and green (3)
seeds, measure 4-neighbor shortest-path distance through every non-wall cell.
Paint an open color-0 cell cyan (8) exactly when both seeds can reach it at the
same distance; preserve walls, seeds, unreachable cells, and non-ties.

The four-profile curriculum retains the original no-wall, vertical-gate,
horizontal-gate, and elbow-gate sequence.  Horizontal and elbow scenes also
carry one disjoint closed 3x3 wall island.  Consequently every three-demo
window contains an unreachable-cell negative, and every four-pair lesson
contains two such negatives, so any single query rotation still refutes the
``infinity equals infinity`` shortcut.
"""
from __future__ import annotations

from collections import deque
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "394fc1eaa85e"
TASK_ID = "394fc1eaa85e"
VERSION = "2.3.1"
RULE_HASH = "bc441550caa9"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Treat 5s as walls; paint each open 0 cell cyan (8) iff its 4-neighbor "
    "shortest-path distances from the unique red (2) and green (3) seeds are "
    "both finite and equal. Preserve every other input cell."
)

INVARIANTS = [
    "input palette is a subset of {0,2,3,5}",
    "there is exactly one red(2) seed and exactly one green(3) seed",
    "the two seeds are mutually reachable through non-wall cells",
    "ordinary generated scenes contain at least two equidistant open cells",
    "ordinary generated scenes retain non-tie open cells as negative controls",
    "wall-profile scenes bend the answer away from the wall-blind Manhattan bisector",
    "every three-demo schedule window contains an unreachable open-cell negative",
    "every four-pair lesson keeps that negative under any single query rotation",
]

# Only dimensions are public overrides.  Earlier revisions advertised palette,
# anchor, asymmetry, singleton metadata, and degenerate texture controls that
# were not observable from the returned grid.  Semantic wall profiles are now a
# deterministic lesson schedule rather than a misleading exact override axis.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-biased 7..9", "valid": "7..9"},
    "grid_w": {"type": "int", "default": "difficulty-biased 11..13", "valid": "11..13"},
}

WALL_PROFILES = ("none", "vertical_gate", "horizontal_gate", "elbow_gate")
# Preserve the frozen four-profile curriculum contract.  The last two profiles
# embed a closed island in addition to their primary gate topology, yielding two
# unreachable witnesses per four-pair lesson without adding a fifth profile.
SCHEDULE_PROFILES = WALL_PROFILES


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty rectangle"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(
                    f"cells must be ARC integers 0..9; got {value!r} at "
                    f"({row_index},{col_index})"
                )
    return errors


def _positions(grid, color: int) -> list[tuple[int, int]]:
    return [
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value == color
    ]


def _bfs_distances(grid, start: tuple[int, int]) -> dict[tuple[int, int], int]:
    height, width = len(grid), len(grid[0])
    distances = {start: 0}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        distance = distances[(row, col)]
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, col + dc
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if grid[nr][nc] == 5 or (nr, nc) in distances:
                continue
            distances[(nr, nc)] = distance + 1
            queue.append((nr, nc))
    return distances


def _ring_cells(center: tuple[int, int]) -> set[tuple[int, int]]:
    row, col = center
    return {
        (row + dr, col + dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if (dr, dc) != (0, 0)
    }


def _closed_island_centers(grid) -> list[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    centers: list[tuple[int, int]] = []
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] == 0 and all(
                grid[nr][nc] == 5 for nr, nc in _ring_cells((row, col))
            ):
                centers.append((row, col))
    return centers


def _contains_closed_island(grid) -> bool:
    return bool(_closed_island_centers(grid))


def _wall_profile_from_grid(grid) -> str:
    walls = set(_positions(grid, 5))
    if not walls:
        return "none"

    # Closed-island walls are auxiliary teaching negatives.  Remove them before
    # classifying the primary topology so the frozen four-profile schedule stays
    # observable from the returned grid.
    auxiliary = set()
    for center in _closed_island_centers(grid):
        auxiliary.update(_ring_cells(center))
    primary_walls = walls - auxiliary
    if not primary_walls:
        return "island"
    wall_rows = {row for row, _ in primary_walls}
    wall_cols = {col for _, col in primary_walls}
    if len(wall_cols) == 1:
        return "vertical_gate"
    if len(wall_rows) == 1:
        return "horizontal_gate"
    return "elbow_gate"


def _analysis(grid) -> dict[str, object]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    palette = {value for row in grid for value in row}
    if not palette <= {0, 2, 3, 5}:
        errors.append(f"input palette must be a subset of {{0,2,3,5}}, got {sorted(palette)}")

    red = _positions(grid, 2)
    green = _positions(grid, 3)
    if len(red) != 1:
        errors.append(f"expected exactly one red(2) seed, found {len(red)}")
    if len(green) != 1:
        errors.append(f"expected exactly one green(3) seed, found {len(green)}")
    if errors:
        return {"errors": errors, "red": red, "green": green, "palette": palette}

    red_seed, green_seed = red[0], green[0]
    red_dist = _bfs_distances(grid, red_seed)
    green_dist = _bfs_distances(grid, green_seed)
    if green_seed not in red_dist:
        errors.append("red and green seeds must be mutually reachable through non-wall cells")

    tie_cells: list[tuple[int, int]] = []
    non_tie_open: list[tuple[int, int]] = []
    unreachable_open: list[tuple[int, int]] = []
    manhattan_ties: list[tuple[int, int]] = []
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value != 0:
                continue
            point = (row_index, col_index)
            if point not in red_dist or point not in green_dist:
                unreachable_open.append(point)
            elif red_dist[point] == green_dist[point]:
                tie_cells.append(point)
            else:
                non_tie_open.append(point)
            if (
                abs(row_index - red_seed[0]) + abs(col_index - red_seed[1])
                == abs(row_index - green_seed[0]) + abs(col_index - green_seed[1])
            ):
                manhattan_ties.append(point)

    return {
        "errors": errors,
        "red": red_seed,
        "green": green_seed,
        "palette": palette,
        "red_dist": red_dist,
        "green_dist": green_dist,
        "tie_cells": tie_cells,
        "non_tie_open": non_tie_open,
        "unreachable_open": unreachable_open,
        "manhattan_ties": manhattan_ties,
        "wall_sensitive": set(tie_cells) != set(manhattan_ties),
        "wall_profile": _wall_profile_from_grid(grid),
        "wall_count": len(_positions(grid, 5)),
    }


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python audit mirror; canonical Racket remains the output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    tie_cells = set(analysis["tie_cells"])
    return [
        [8 if (row_index, col_index) in tie_cells else value for col_index, value in enumerate(row)]
        for row_index, row in enumerate(grid)
    ]


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_manhattan_distance(grid):
    red = _positions(grid, 2)
    green = _positions(grid, 3)
    if len(red) != 1 or len(green) != 1:
        return [list(row) for row in grid]
    red_seed, green_seed = red[0], green[0]
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value != 0:
                continue
            da = abs(row_index - red_seed[0]) + abs(col_index - red_seed[1])
            db = abs(row_index - green_seed[0]) + abs(col_index - green_seed[1])
            if da == db:
                output[row_index][col_index] = 8
    return output


def _rival_first_tie_only(grid):
    output = [list(row) for row in grid]
    analysis = _analysis(grid)
    if not analysis["errors"] and analysis["tie_cells"]:
        row, col = analysis["tie_cells"][0]
        output[row][col] = 8
    return output


def _rival_unreachable_as_tie(grid):
    """Wrongly treat two absent distances as an equal-distance answer."""
    output = [list(row) for row in grid]
    analysis = _analysis(grid)
    if analysis["errors"]:
        return output
    red_dist = analysis["red_dist"]
    green_dist = analysis["green_dist"]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            point = (row_index, col_index)
            if value == 0 and red_dist.get(point) == green_dist.get(point):
                output[row_index][col_index] = 8
    return output


def _rival_paint_all_open(grid):
    return [[8 if value == 0 else value for value in row] for row in grid]


def _rival_recolor_seeds(grid):
    return [[8 if value in (2, 3) else value for value in row] for row in grid]


SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "manhattan_distance": _rival_manhattan_distance,
    "first_tie_only": _rival_first_tie_only,
    "unreachable_as_tie": _rival_unreachable_as_tie,
    "paint_all_open": _rival_paint_all_open,
    "recolor_seeds": _rival_recolor_seeds,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _has_multiple_ties(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and len(analysis["tie_cells"]) >= 2


def _has_non_tie_controls(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["non_tie_open"])


def _has_wall_detour(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["wall_sensitive"])


def _has_unreachable_open_negative(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["unreachable_open"])


def _preserves_seed_roles(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and len(_positions(grid, 2)) == 1 and len(_positions(grid, 3)) == 1


SEMANTIC_WITNESSES = {
    "multiple_equidistant_cells": _has_multiple_ties,
    "non_tie_open_controls": _has_non_tie_controls,
    "wall_detour_changes_bisector": _has_wall_detour,
    "unreachable_open_is_not_a_tie": _has_unreachable_open_negative,
    "seed_roles_are_not_answers": _preserves_seed_roles,
}
WITNESS_RIVALS = {
    "multiple_equidistant_cells": ["identity", "first_tie_only"],
    "non_tie_open_controls": ["paint_all_open"],
    "wall_detour_changes_bisector": ["manhattan_distance"],
    "unreachable_open_is_not_a_tie": ["unreachable_as_tie"],
    "seed_roles_are_not_answers": ["recolor_seeds"],
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-safe input grammar without imposing lesson scheduling."""
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if not analysis["tie_cells"] and not analysis["non_tie_open"] and not analysis["unreachable_open"]:
        errors.append("expected at least one open color-0 cell")

    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if requested:
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in AXES and observed.get(axis) != value:
                errors.append(f"override {axis} requested {value!r}, observed {observed.get(axis)!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked teaching predicate shared by the strict semantic census."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if len(analysis["tie_cells"]) < 2:
        errors.append("need at least two equidistant open cells to expose a visible locus")
    if not analysis["non_tie_open"]:
        errors.append("need at least one non-tie open cell as a negative control")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact override axis from a generated grid."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def semantic_observables(grid) -> dict[str, object]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    return {
        **observe_overrides(grid),
        "wall_profile": analysis["wall_profile"],
        "wall_count": analysis["wall_count"],
        "tie_count": len(analysis["tie_cells"]),
        "non_tie_open_count": len(analysis["non_tie_open"]),
        "unreachable_open_count": len(analysis["unreachable_open"]),
        "wall_sensitive": analysis["wall_sensitive"],
        "red": analysis["red"],
        "green": analysis["green"],
    }


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson unless all named plausible shortcuts die in its demos."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        structural = strict_canonical_like(pair["input"])
        if structural:
            reasons.append(f"demo {index} is not a lawful teaching scene: {structural[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the wall-distance rule")

    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        reasons.append(f"query is not a lawful teaching scene: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the wall-distance rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"competitor {name!r} still fits every demonstration")
    return reasons


def mutation_fixtures():
    """Named malformed near-misses the structural checker must reject."""
    no_red = full_grid(7, 11, 0)
    no_red[3][8] = 3

    duplicate_green = full_grid(7, 11, 0)
    duplicate_green[3][2] = 2
    duplicate_green[2][8] = 3
    duplicate_green[4][8] = 3

    cyan_in_input = full_grid(7, 11, 0)
    cyan_in_input[3][2] = 2
    cyan_in_input[3][8] = 3
    cyan_in_input[1][5] = 8

    disconnected = full_grid(7, 11, 0)
    for row in range(7):
        disconnected[row][5] = 5
    disconnected[3][2] = 2
    disconnected[3][8] = 3

    illegal_color = full_grid(7, 11, 0)
    illegal_color[3][2] = 2
    illegal_color[3][8] = 3
    illegal_color[1][5] = 4

    return [
        ("missing_red_seed", no_red),
        ("duplicate_green_seed", duplicate_green),
        ("cyan_already_in_input", cyan_in_input),
        ("seeds_disconnected_by_wall", disconnected),
        ("foreign_palette_color", illegal_color),
    ]


def _with_closed_island(
    walls: set[tuple[int, int]], height: int, width: int, rng
) -> tuple[set[tuple[int, int]], tuple[int, int]]:
    candidates = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]
    rng.shuffle(candidates)
    for center in candidates:
        ring = _ring_cells(center)
        if center not in walls and ring.isdisjoint(walls):
            return walls | ring, center
    raise AssertionError("could not place a disjoint closed island")


def _make_walls(profile: str, height: int, width: int, rng) -> tuple[set[tuple[int, int]], dict[str, int | str]]:
    if profile == "none":
        return set(), {}

    if profile in ("vertical_gate", "elbow_gate"):
        barrier_col = rng.randint(3, width - 4)
        gap_row = rng.randint(1, height - 2)
        walls = {(row, barrier_col) for row in range(height) if row != gap_row}
        meta: dict[str, int | str] = {"barrier_col": barrier_col, "gap_row": gap_row}
        if profile == "elbow_gate":
            arm_rows = [row for row in range(1, height - 1) if row != gap_row]
            arm_row = rng.choice(arm_rows)
            direction = rng.choice((-1, 1))
            maximum = min(4, barrier_col if direction < 0 else width - 1 - barrier_col)
            arm_len = rng.randint(2, max(2, maximum))
            for step in range(1, arm_len + 1):
                col = barrier_col + direction * step
                if 0 <= col < width:
                    walls.add((arm_row, col))
            meta.update({"arm_row": arm_row, "arm_direction": direction, "arm_len": arm_len})
            walls, island_center = _with_closed_island(walls, height, width, rng)
            meta.update({"island_row": island_center[0], "island_col": island_center[1]})
        return walls, meta

    if profile == "horizontal_gate":
        barrier_row = rng.randint(2, height - 3)
        gap_col = rng.randint(1, width - 2)
        walls = {(barrier_row, col) for col in range(width) if col != gap_col}
        walls, island_center = _with_closed_island(walls, height, width, rng)
        return walls, {
            "barrier_row": barrier_row,
            "gap_col": gap_col,
            "island_row": island_center[0],
            "island_col": island_center[1],
        }

    raise ValueError(f"unknown wall profile: {profile!r}")


def _opposite_sides(a, b, profile: str, wall_meta: dict[str, int | str]) -> bool:
    if profile in ("vertical_gate", "elbow_gate"):
        barrier_col = int(wall_meta["barrier_col"])
        return (a[1] < barrier_col < b[1]) or (b[1] < barrier_col < a[1])
    if profile == "horizontal_gate":
        barrier_row = int(wall_meta["barrier_row"])
        return (a[0] < barrier_row < b[0]) or (b[0] < barrier_row < a[0])
    return True


def _choose_seed_pair(
    grid: list[list[int]], profile: str, wall_meta: dict[str, int | str], rng
) -> tuple[tuple[int, int], tuple[int, int]] | None:
    height, width = len(grid), len(grid[0])
    open_cells = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] == 0
    ]
    pairs = list(combinations(open_cells, 2))
    rng.shuffle(pairs)
    distance_cache: dict[tuple[int, int], dict[tuple[int, int], int]] = {}

    for first, second in pairs:
        if (first[0] + first[1]) % 2 != (second[0] + second[1]) % 2:
            continue
        if abs(first[0] - second[0]) + abs(first[1] - second[1]) < 4:
            continue
        if not _opposite_sides(first, second, profile, wall_meta):
            continue
        da = distance_cache.setdefault(first, _bfs_distances(grid, first))
        if second not in da:
            continue
        db = distance_cache.setdefault(second, _bfs_distances(grid, second))
        tie_cells = []
        non_tie_count = 0
        manhattan_ties = []
        for row in range(height):
            for col in range(width):
                if grid[row][col] != 0 or (row, col) in (first, second):
                    continue
                point = (row, col)
                if point in da and point in db:
                    if da[point] == db[point]:
                        tie_cells.append(point)
                    else:
                        non_tie_count += 1
                if (
                    abs(row - first[0]) + abs(col - first[1])
                    == abs(row - second[0]) + abs(col - second[1])
                ):
                    manhattan_ties.append(point)
        if len(tie_cells) < 2 or non_tie_count < 8:
            continue
        if profile != "none" and set(tie_cells) == set(manhattan_ties):
            continue
        return (first, second) if rng.random() < 0.5 else (second, first)
    return None


def _construct_scene(height: int, width: int, profile: str, rng) -> list[list[int]]:
    for _ in range(32):
        grid = full_grid(height, width, 0)
        walls, wall_meta = _make_walls(profile, height, width, rng)
        for row, col in walls:
            grid[row][col] = 5
        pair = _choose_seed_pair(grid, profile, wall_meta, rng)
        if pair is None:
            continue
        red, green = pair
        grid[red[0]][red[1]] = 2
        grid[green[0]][green[1]] = 3
        analysis = _analysis(grid)
        if analysis["errors"]:
            continue
        if len(analysis["tie_cells"]) < 2 or not analysis["non_tie_open"]:
            continue
        if profile != "none" and not analysis["wall_sensitive"]:
            continue
        expected_unreachable = 1 if profile in ("horizontal_gate", "elbow_gate") else 0
        if len(analysis["unreachable_open"]) != expected_unreachable:
            continue
        if _wall_profile_from_grid(grid) != profile:
            continue
        return grid
    raise AssertionError(f"could not construct calibrated {profile!r} scene at {height}x{width}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 7, 9)
    width = ctx.draw_int_diff("grid_w", 11, 13)
    profile = schedule_profile(seed, sample_index, difficulty)
    grid = _construct_scene(height, width, profile, ctx.draw_rng("geometry"))

    observed = observe_overrides(grid)
    for axis, requested in ctx.recorded_draws().items():
        if axis in AXES and observed[axis] != requested:
            raise AssertionError(
                f"internal override drift for {axis}: requested {requested!r}, observed {observed[axis]!r}"
            )
    return grid
