"""Semantic generator for ARC task 7ed6d6ae68f2.

Gray 5s are impassable walls.  From the unique red (2) and green (3) seeds,
measure four-neighbor shortest-path distance through non-wall cells.  Every
zero reachable from exactly one seed takes that seed's color; a zero reachable
from both takes the nearer seed's color; equal-distance and unreachable zeros
remain zero.  Walls and seed cells are preserved.

The ordinary lesson schedule alternates three complementary scene families:
wall-sensitive connected mazes, disconnected three-chamber mazes, and exact
canonical wall morphologies with varied seed locations.  Every three-demo
sliding window therefore contains both genuine distance competition and
reachability-only evidence, while one third of default draws stays on the
strict empirical canonical wall manifold.
"""
from __future__ import annotations

from collections import deque
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7ed6d6ae68f2"
TASK_ID = "7ed6d6ae68f2"
VERSION = "2.0.0"
# Comment-preserving selected source; synchronized task-scoped canonical patch.
RULE_HASH = "854101294256"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Treat 5s as walls and fill each zero by the uniquely nearest reachable "
    "red(2) or green(3) seed under four-neighbor shortest-path distance; "
    "equal-distance and unreachable zeros stay 0."
)

INVARIANTS = [
    "input palette is exactly {0,2,3,5}",
    "the outer border is entirely color-5 wall",
    "there is exactly one red(2) seed and exactly one green(3) seed",
    "at least one internal color-5 wall cell forms the maze",
    "each seed can reach at least one open zero cell",
    "ordinary lessons cover both shared-component distance competition and disconnected reachability",
]

SIZE_PROFILES = ("9x13", "10x14", "11x11", "10x12", "10x13")
_SIZE_BY_PROFILE = {
    "9x13": (9, 13),
    "10x14": (10, 14),
    "11x11": (11, 11),
    "10x12": (10, 12),
    "10x13": (10, 13),
}
_PROFILE_BY_SIZE = {value: key for key, value in _SIZE_BY_PROFILE.items()}

# Every public override is exact and recoverable from the returned grid.
# The previous metadata advertised eight dead/alias/singleton controls; those
# are deliberately removed instead of pretending they were observable axes.
AXES = {
    "size_profile": {
        "type": "str",
        "default": "uniform over the five canonical dimension profiles",
        "valid": "|".join(SIZE_PROFILES),
    },
}

SCHEDULE_PROFILES = (
    "connected_detour",
    "disconnected_chambers",
    "canonical_morphology",
)

# Canonical wall masks with seeds erased to 0.  The strict predicate compares
# the complete occupied wall bitmap, not merely dimensions or wall count.
_CANONICAL_WALL_ROWS = {
    "9x13": (
        "5555555555555",
        "5000000000005",
        "5000000000005",
        "5000000000005",
        "5555550555555",
        "5000000000005",
        "5000000000005",
        "5000000000005",
        "5555555555555",
    ),
    "10x14": (
        "55555555555555",
        "50000050000005",
        "50000050000005",
        "50000050000005",
        "50000050000005",
        "50000005555555",
        "50000050000005",
        "50000050000005",
        "50000050000005",
        "55555555555555",
    ),
    "11x11": (
        "55555555555",
        "50000500005",
        "50000500005",
        "55555500005",
        "50000500005",
        "50000000005",
        "50000500005",
        "50000555555",
        "50000500005",
        "50000500005",
        "55555555555",
    ),
    "10x12": (
        "555555555555",
        "500000000005",
        "505555555505",
        "500050005005",
        "500050005005",
        "500050005005",
        "500050005005",
        "555555555555",
        "500000000005",
        "555555555555",
    ),
    "10x13": (
        "5555555555555",
        "5000005000005",
        "5000005000005",
        "5000005555555",
        "5000005000005",
        "5000005000005",
        "5000005000005",
        "5555555000005",
        "5000005000005",
        "5555555555555",
    ),
}


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty rectangle"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (7 <= len(grid) <= 24 and 9 <= width <= 24):
        return [f"maze dimensions must lie in 7..24 by 9..24, got {len(grid)}x{width}"]
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(
                    f"cells must be ARC integers 0..9; got {value!r} at ({row_index},{col_index})"
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


def _open_components(grid) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 5
    }
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = next(iter(unseen))
        component = {start}
        queue = deque([start])
        unseen.remove(start)
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (row + dr, col + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)
        components.append(component)
    return components


def _analysis(grid) -> dict[str, object]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    palette = {value for row in grid for value in row}
    if palette != {0, 2, 3, 5}:
        errors.append(f"input palette must be exactly {{0,2,3,5}}, got {sorted(palette)}")

    if any(grid[0][col] != 5 or grid[height - 1][col] != 5 for col in range(width)):
        errors.append("top and bottom borders must be color-5 walls")
    if any(grid[row][0] != 5 or grid[row][width - 1] != 5 for row in range(height)):
        errors.append("left and right borders must be color-5 walls")

    red = _positions(grid, 2)
    green = _positions(grid, 3)
    if len(red) != 1:
        errors.append(f"expected exactly one red(2) seed, found {len(red)}")
    if len(green) != 1:
        errors.append(f"expected exactly one green(3) seed, found {len(green)}")

    internal_walls = [
        (row, col)
        for row, col in _positions(grid, 5)
        if 0 < row < height - 1 and 0 < col < width - 1
    ]
    if not internal_walls:
        errors.append("expected at least one internal color-5 maze wall")
    if not _positions(grid, 0):
        errors.append("expected at least one open color-0 cell")

    if errors:
        return {
            "errors": errors,
            "palette": palette,
            "red": red,
            "green": green,
            "internal_walls": internal_walls,
        }

    red_seed, green_seed = red[0], green[0]
    red_dist = _bfs_distances(grid, red_seed)
    green_dist = _bfs_distances(grid, green_seed)

    categories = {
        "red_only": [],
        "green_only": [],
        "red_closer": [],
        "green_closer": [],
        "tie": [],
        "unreachable": [],
    }
    manhattan_diff: list[tuple[int, int]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            point = (row, col)
            dr = red_dist.get(point)
            dg = green_dist.get(point)
            if dr is None and dg is None:
                category = "unreachable"
                bfs_value = 0
            elif dg is None:
                category = "red_only"
                bfs_value = 2
            elif dr is None:
                category = "green_only"
                bfs_value = 3
            elif dr < dg:
                category = "red_closer"
                bfs_value = 2
            elif dg < dr:
                category = "green_closer"
                bfs_value = 3
            else:
                category = "tie"
                bfs_value = 0
            categories[category].append(point)

            md_red = abs(row - red_seed[0]) + abs(col - red_seed[1])
            md_green = abs(row - green_seed[0]) + abs(col - green_seed[1])
            manhattan_value = 2 if md_red < md_green else 3 if md_green < md_red else 0
            if manhattan_value != bfs_value:
                manhattan_diff.append(point)

    red_blank_reachable = sum(
        1 for point, distance in red_dist.items() if point != red_seed and grid[point[0]][point[1]] == 0
    )
    green_blank_reachable = sum(
        1 for point, distance in green_dist.items() if point != green_seed and grid[point[0]][point[1]] == 0
    )
    if red_blank_reachable == 0:
        errors.append("red seed must reach at least one open zero cell")
    if green_blank_reachable == 0:
        errors.append("green seed must reach at least one open zero cell")

    components = _open_components(grid)
    component_roles: list[str] = []
    for component in components:
        has_red = red_seed in component
        has_green = green_seed in component
        if has_red and has_green:
            component_roles.append("both")
        elif has_red:
            component_roles.append("red")
        elif has_green:
            component_roles.append("green")
        else:
            component_roles.append("none")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "red": red_seed,
        "green": green_seed,
        "red_dist": red_dist,
        "green_dist": green_dist,
        "categories": categories,
        "manhattan_diff": manhattan_diff,
        "components": components,
        "component_roles": component_roles,
        "internal_walls": internal_walls,
    }


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python audit mirror; canonical Racket remains output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = [list(row) for row in grid]
    categories = analysis["categories"]
    for row, col in categories["red_only"] + categories["red_closer"]:
        output[row][col] = 2
    for row, col in categories["green_only"] + categories["green_closer"]:
        output[row][col] = 3
    return output


def _rival_manhattan(grid):
    """Tempting wall-blind nearest-seed Voronoi rule."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    red, green = analysis["red"], analysis["green"]
    output = [list(row) for row in grid]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                continue
            dr = abs(row - red[0]) + abs(col - red[1])
            dg = abs(row - green[0]) + abs(col - green[1])
            if dr < dg:
                output[row][col] = 2
            elif dg < dr:
                output[row][col] = 3
    return output


def _rival_component_owner(grid):
    """Shortcut: fill only components containing exactly one seed; never compare distances."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    red, green = analysis["red"], analysis["green"]
    output = [list(row) for row in grid]
    for component in analysis["components"]:
        color = 2 if red in component and green not in component else 3 if green in component and red not in component else None
        if color is None:
            continue
        for row, col in component:
            if grid[row][col] == 0:
                output[row][col] = color
    return output


def _rival_ties_to_color(grid, tie_color: int):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    output = rule_mirror(grid)
    for row, col in analysis["categories"]["tie"]:
        output[row][col] = tie_color
    return output


def _rival_ties_red(grid):
    return _rival_ties_to_color(grid, 2)


def _rival_ties_green(grid):
    return _rival_ties_to_color(grid, 3)


SEMANTIC_RIVALS = {
    "wall_blind_manhattan": _rival_manhattan,
    "component_owner_only": _rival_component_owner,
    "ties_go_red": _rival_ties_red,
    "ties_go_green": _rival_ties_green,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _connected_competition(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    categories = analysis["categories"]
    return (
        "both" in analysis["component_roles"]
        and len(categories["red_closer"]) >= 1
        and len(categories["green_closer"]) >= 1
    )


def _wall_sensitive_competition(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and "both" in analysis["component_roles"] and len(analysis["manhattan_diff"]) >= 1


def _disconnected_seed_regions(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    categories = analysis["categories"]
    return bool(
        categories["red_only"]
        and categories["green_only"]
        and _rival_manhattan(grid) != rule_mirror(grid)
    )


def _unreachable_region(grid) -> bool:
    analysis = _analysis(grid)
    return bool(
        not analysis["errors"]
        and analysis["categories"]["unreachable"]
        and _rival_manhattan(grid) != rule_mirror(grid)
    )


def _equal_distance_tie(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["categories"]["tie"])


SEMANTIC_WITNESSES = {
    "connected_distance_competition": _connected_competition,
    "walls_change_nearest_seed": _wall_sensitive_competition,
    "disconnected_single_seed_regions": _disconnected_seed_regions,
    "seedless_unreachable_region": _unreachable_region,
    "equal_distance_stays_blank": _equal_distance_tie,
}
WITNESS_RIVALS = {
    "connected_distance_competition": ["component_owner_only"],
    "walls_change_nearest_seed": ["wall_blind_manhattan"],
    "disconnected_single_seed_regions": ["wall_blind_manhattan"],
    "seedless_unreachable_region": ["wall_blind_manhattan"],
    "equal_distance_stays_blank": ["ties_go_red", "ties_go_green"],
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's structural input grammar, including exact seed roles."""
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if requested:
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in AXES and observed.get(axis) != value:
                errors.append(
                    f"override {axis} requested {value!r}, observed {observed.get(axis)!r}"
                )
    return errors


def _wall_signature(grid) -> tuple[str, ...]:
    return tuple("".join("5" if value == 5 else "0" for value in row) for row in grid)


def strict_canonical_like(grid) -> list[str]:
    """Strict empirical manifold: full canonical wall bitmap plus shared roles."""
    errors = self_check(grid)
    if errors:
        return errors
    profile = _PROFILE_BY_SIZE.get((len(grid), len(grid[0])))
    if profile is None:
        return [f"dimensions {len(grid)}x{len(grid[0])} are not a canonical linked size"]
    expected = _CANONICAL_WALL_ROWS[profile]
    if _wall_signature(grid) != expected:
        return [f"wall bitmap is not the canonical morphology for linked size {profile}"]
    return []


def observe_overrides(grid) -> dict[str, str]:
    """Recover every declared exact override axis from the returned grid."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    profile = _PROFILE_BY_SIZE.get((len(grid), len(grid[0])))
    return {"size_profile": profile} if profile is not None else {}


def semantic_observables(grid) -> dict[str, object]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    categories = analysis["categories"]
    strict = not strict_canonical_like(grid)
    return {
        **observe_overrides(grid),
        "strict_canonical_wall_bitmap": strict,
        "internal_wall_count": len(analysis["internal_walls"]),
        "open_component_count": len(analysis["components"]),
        "component_roles": list(analysis["component_roles"]),
        "red_only": len(categories["red_only"]),
        "green_only": len(categories["green_only"]),
        "red_closer": len(categories["red_closer"]),
        "green_closer": len(categories["green_closer"]),
        "tie": len(categories["tie"]),
        "unreachable": len(categories["unreachable"]),
        "wall_sensitive_cells": len(analysis["manhattan_diff"]),
        "red": analysis["red"],
        "green": analysis["green"],
    }


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    band_offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}.get(difficulty)
    if band_offset is None:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return SCHEDULE_PROFILES[(sample_index + band_offset) % len(SCHEDULE_PROFILES)]


def lesson_identifiable(demos, query) -> list[str]:
    """Require three demos to kill the named plausible shortcut rules."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    demo_inputs = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        structural = self_check(pair["input"])
        if structural:
            reasons.append(f"demo {index} is not structurally lawful: {structural[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the wall-distance rule")
            continue
        demo_inputs.append(pair["input"])

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is not structurally lawful: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the wall-distance rule")
    if reasons:
        return reasons

    if not any(_wall_sensitive_competition(grid) and _equal_distance_tie(grid) for grid in demo_inputs):
        reasons.append("demonstrations lack a wall-sensitive shared-component competition with an equal-distance tie")
    if not any(_disconnected_seed_regions(grid) and _unreachable_region(grid) for grid in demo_inputs):
        reasons.append("demonstrations lack disconnected red/green ownership plus a seedless unreachable region")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
            if not survives:
                continue
            candidate_query = competitor(query["input"])
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if candidate_query != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demonstration but predicts a different query answer"
            )
    return reasons


def mutation_fixtures():
    """Named malformed near-misses the structural checker must reject."""
    base = _decode_wall_mask("9x13")
    base[2][3] = 2
    base[6][9] = 3

    missing_red = [row[:] for row in base]
    missing_red[2][3] = 0

    duplicate_green = [row[:] for row in base]
    duplicate_green[2][4] = 3

    broken_border = [row[:] for row in base]
    broken_border[0][4] = 0

    foreign_color = [row[:] for row in base]
    foreign_color[1][1] = 8

    no_internal_walls = full_grid(9, 13, 0)
    for row in range(9):
        no_internal_walls[row][0] = 5
        no_internal_walls[row][12] = 5
    for col in range(13):
        no_internal_walls[0][col] = 5
        no_internal_walls[8][col] = 5
    no_internal_walls[2][3] = 2
    no_internal_walls[6][9] = 3

    return [
        ("missing_red_seed", missing_red),
        ("duplicate_green_seed", duplicate_green),
        ("broken_outer_wall", broken_border),
        ("foreign_palette_color", foreign_color),
        ("no_internal_maze_wall", no_internal_walls),
    ]


def _decode_wall_mask(profile: str) -> list[list[int]]:
    return [[5 if char == "5" else 0 for char in row] for row in _CANONICAL_WALL_ROWS[profile]]


def _pair_metrics(base_grid, first: tuple[int, int], second: tuple[int, int]) -> dict[str, int | bool]:
    first_dist = _bfs_distances(base_grid, first)
    second_dist = _bfs_distances(base_grid, second)
    if second not in first_dist:
        return {"connected": False}
    red_closer = green_closer = ties = wall_sensitive = 0
    for row, values in enumerate(base_grid):
        for col, value in enumerate(values):
            point = (row, col)
            if value != 0 or point in (first, second):
                continue
            dr = first_dist.get(point)
            dg = second_dist.get(point)
            if dr is None or dg is None:
                continue
            bfs = 2 if dr < dg else 3 if dg < dr else 0
            if bfs == 2:
                red_closer += 1
            elif bfs == 3:
                green_closer += 1
            else:
                ties += 1
            mr = abs(row - first[0]) + abs(col - first[1])
            mg = abs(row - second[0]) + abs(col - second[1])
            manhattan = 2 if mr < mg else 3 if mg < mr else 0
            if bfs != manhattan:
                wall_sensitive += 1
    return {
        "connected": True,
        "red_closer": red_closer,
        "green_closer": green_closer,
        "ties": ties,
        "wall_sensitive": wall_sensitive,
    }


def _connected_wall_grid(height: int, width: int, rng):
    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][0] = 5
        grid[row][width - 1] = 5
    for col in range(width):
        grid[0][col] = 5
        grid[height - 1][col] = 5

    orientation = rng.choice(("vertical", "horizontal"))
    if orientation == "vertical":
        barrier = rng.randint(3, width - 4)
        gap = rng.randint(1, height - 2)
        for row in range(1, height - 1):
            if row != gap:
                grid[row][barrier] = 5
        arm_rows = [row for row in range(2, height - 2) if row != gap]
        if arm_rows:
            arm_row = rng.choice(arm_rows)
            directions = [direction for direction in (-1, 1) if 2 <= barrier + direction * 2 <= width - 3]
            if directions:
                direction = rng.choice(directions)
                max_len = min(3, barrier - 1 if direction < 0 else width - 2 - barrier)
                for step in range(1, max_len + 1):
                    grid[arm_row][barrier + direction * step] = 5
        side_test = lambda a, b: (a[1] < barrier < b[1]) or (b[1] < barrier < a[1])
    else:
        barrier = rng.randint(3, height - 4) if height >= 8 else height // 2
        gap = rng.randint(1, width - 2)
        for col in range(1, width - 1):
            if col != gap:
                grid[barrier][col] = 5
        arm_cols = [col for col in range(2, width - 2) if col != gap]
        if arm_cols:
            arm_col = rng.choice(arm_cols)
            directions = [direction for direction in (-1, 1) if 2 <= barrier + direction * 2 <= height - 3]
            if directions:
                direction = rng.choice(directions)
                max_len = min(3, barrier - 1 if direction < 0 else height - 2 - barrier)
                for step in range(1, max_len + 1):
                    grid[barrier + direction * step][arm_col] = 5
        side_test = lambda a, b: (a[0] < barrier < b[0]) or (b[0] < barrier < a[0])
    return grid, side_test


def _construct_connected_detour(height: int, width: int, rng) -> list[list[int]]:
    for _ in range(48):
        base, opposite_sides = _connected_wall_grid(height, width, rng)
        open_cells = [
            (row, col)
            for row in range(1, height - 1)
            for col in range(1, width - 1)
            if base[row][col] == 0
        ]
        pairs = list(combinations(open_cells, 2))
        rng.shuffle(pairs)
        for first, second in pairs[:1000]:
            if not opposite_sides(first, second):
                continue
            if (first[0] + first[1]) % 2 != (second[0] + second[1]) % 2:
                continue
            if abs(first[0] - second[0]) + abs(first[1] - second[1]) < 4:
                continue
            metrics = _pair_metrics(base, first, second)
            if not metrics.get("connected"):
                continue
            if metrics["red_closer"] < 6 or metrics["green_closer"] < 6:
                continue
            if metrics["ties"] < 2 or metrics["wall_sensitive"] < 2:
                continue
            red, green = (first, second) if rng.random() < 0.5 else (second, first)
            grid = [row[:] for row in base]
            grid[red[0]][red[1]] = 2
            grid[green[0]][green[1]] = 3
            analysis = _analysis(grid)
            if (
                not analysis["errors"]
                and _wall_sensitive_competition(grid)
                and _equal_distance_tie(grid)
                and rule_mirror(grid) != grid
            ):
                return grid
    raise AssertionError(f"could not construct connected wall-sensitive lesson at {height}x{width}")


def _divider_positions(length: int) -> list[tuple[int, int]]:
    candidates = []
    for first in range(2, length - 3):
        for second in range(first + 2, length - 1):
            # Three non-empty chambers inside the outer border.
            if first - 1 >= 1 and second - first - 1 >= 1 and length - 2 - second >= 1:
                candidates.append((first, second))
    return candidates


def _construct_disconnected_chambers(height: int, width: int, rng) -> list[list[int]]:
    for _ in range(32):
        grid = full_grid(height, width, 0)
        for row in range(height):
            grid[row][0] = 5
            grid[row][width - 1] = 5
        for col in range(width):
            grid[0][col] = 5
            grid[height - 1][col] = 5

        orientation = rng.choice(("vertical", "horizontal"))
        if orientation == "vertical":
            choices = _divider_positions(width)
            if not choices:
                continue
            first, second = rng.choice(choices)
            for row in range(1, height - 1):
                grid[row][first] = 5
                grid[row][second] = 5
        else:
            choices = _divider_positions(height)
            if not choices:
                continue
            first, second = rng.choice(choices)
            for col in range(1, width - 1):
                grid[first][col] = 5
                grid[second][col] = 5

        components = [component for component in _open_components(grid) if any(grid[r][c] == 0 for r, c in component)]
        if len(components) != 3 or any(len(component) < 2 for component in components):
            continue
        rng.shuffle(components)
        red_component, green_component, _seedless = components
        red_candidates = sorted(red_component)
        green_candidates = sorted(green_component)
        red = rng.choice(red_candidates)
        green = rng.choice(green_candidates)
        if rng.random() < 0.5:
            red, green = green, red
        grid[red[0]][red[1]] = 2
        grid[green[0]][green[1]] = 3
        analysis = _analysis(grid)
        if (
            not analysis["errors"]
            and _disconnected_seed_regions(grid)
            and _unreachable_region(grid)
            and rule_mirror(grid) != grid
        ):
            return grid
    raise AssertionError(f"could not construct disconnected chamber lesson at {height}x{width}")


def _construct_canonical_morphology(profile: str, rng) -> list[list[int]]:
    base = _decode_wall_mask(profile)
    components = [component for component in _open_components(base) if len(component) >= 2]
    candidates = sorted(point for component in components for point in component)
    pairs = list(combinations(candidates, 2))
    rng.shuffle(pairs)
    for first, second in pairs:
        grid = [row[:] for row in base]
        red, green = (first, second) if rng.random() < 0.5 else (second, first)
        grid[red[0]][red[1]] = 2
        grid[green[0]][green[1]] = 3
        if self_check(grid) or strict_canonical_like(grid):
            continue
        if rule_mirror(grid) == grid:
            continue
        return grid
    raise AssertionError(f"could not place seeds on canonical wall morphology {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    size_profile = ctx.draw_choice("size_profile", SIZE_PROFILES)
    height, width = _SIZE_BY_PROFILE[size_profile]
    profile = schedule_profile(seed, sample_index, difficulty)
    rng = ctx.draw_rng("geometry")

    if profile == "connected_detour":
        grid = _construct_connected_detour(height, width, rng)
    elif profile == "disconnected_chambers":
        grid = _construct_disconnected_chambers(height, width, rng)
    elif profile == "canonical_morphology":
        grid = _construct_canonical_morphology(size_profile, rng)
    else:
        raise AssertionError(f"unknown scheduled profile: {profile!r}")

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generated invalid maze: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed.get("size_profile") != size_profile:
        raise AssertionError(
            f"internal override drift: requested {size_profile!r}, observed {observed.get('size_profile')!r}"
        )
    return grid
