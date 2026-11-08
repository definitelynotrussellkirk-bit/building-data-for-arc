"""Generator for ARC task 20458da8b222 — geodesic nearest-seed fill.

Color 5 is an impassable wall.  Every other non-zero cell is a colored seed.
Each open cell is assigned to its uniquely nearest seed by four-neighbor path
length through non-wall cells; cells tied between nearest seeds become color 8.

The public examples do not distinguish every plausible shortcut (plain
Manhattan distance, component-local flood, or preserving walls without using
them).  The generated profiles therefore include tie-positive and no-tie open Voronoi fields, connected
gated barriers whose detours change winners, and disconnected seeded chambers.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "20458da8b222"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "b4a1c41b804f"

SUMMARY = (
    "Fill every color-5-walled open cell from its nearest colored seed by "
    "four-neighbor geodesic distance, using color 8 for exact nearest-seed ties."
)

INVARIANTS = [
    "the outer border is color 5 and every non-wall component contains a seed",
    "2-4 singleton seeds use distinct colors outside {0, 5, 8}",
    "open profiles include both tie-positive and globally unique-nearest two-seed fields",
    "gated profiles contain a connected wall detour that changes at least one winner relative to Manhattan distance",
    "split profiles contain exactly two independently seeded open components",
]

SCENE_PROFILES = (
    "open_two",
    "open_two_unique",
    "open_three",
    "gated_two",
    "gated_three",
    "split_two",
    "split_four",
    "maze_four",
)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "balanced semantic branch profile",
        "valid": "|".join(SCENE_PROFILES),
        "doc": (
            "Observable topology/seed-count profile: open Voronoi, connected "
            "gated detour, disconnected split chambers, or multi-gate maze."
        ),
    }
}

_SEED_COLORS = (1, 2, 3, 4, 6, 7, 9)
_DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_INF = 10**9


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _draw_border(grid: list[list[int]]) -> None:
    height, width = len(grid), len(grid[0])
    for col in range(width):
        grid[0][col] = 5
        grid[height - 1][col] = 5
    for row in range(height):
        grid[row][0] = 5
        grid[row][width - 1] = 5


def _open_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                component.append((rr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 5
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(component)
    return result


def _distance_map(grid: list[list[int]], start: tuple[int, int]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    distances = [[_INF] * width for _ in range(height)]
    sr, sc = start
    distances[sr][sc] = 0
    queue = deque([(sr, sc)])
    while queue:
        row, col = queue.popleft()
        next_distance = distances[row][col] + 1
        for dr, dc in _DIRS4:
            nr, nc = row + dr, col + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 5
                and next_distance < distances[nr][nc]
            ):
                distances[nr][nc] = next_distance
                queue.append((nr, nc))
    return distances


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror used only for structural auditing/tests.

    The production runner still derives outputs exclusively from the canonical
    Racket program identified by ``RULE_HASH``.
    """
    errors = _validate_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    seeds = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 5)
    ]
    if not seeds:
        raise ValueError("at least one seed is required")
    distance_maps = [_distance_map(grid, (row, col)) for row, col, _ in seeds]
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5:
                continue
            values = [distances[row][col] for distances in distance_maps]
            best = min(values)
            winners = [index for index, value in enumerate(values) if value == best]
            output[row][col] = seeds[winners[0]][2] if len(winners) == 1 else 8
    return output


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    result: dict[str, Any] = {"errors": errors, "scene_profile": None}
    if errors:
        return result

    normalized = [list(row) for row in grid]
    height, width = len(normalized), len(normalized[0])
    if not (5 <= height <= 14 and 7 <= width <= 16):
        errors.append(f"grid dimensions must stay inside the calibrated 5..14 x 7..16 envelope, got {height}x{width}")
    if any(value != 5 for value in normalized[0] + normalized[-1]):
        errors.append("top and bottom borders must be color 5")
    if any(row[0] != 5 or row[-1] != 5 for row in normalized):
        errors.append("left and right borders must be color 5")

    seeds = [
        (row, col, normalized[row][col])
        for row in range(height)
        for col in range(width)
        if normalized[row][col] not in (0, 5)
    ]
    seed_colors = [value for _, _, value in seeds]
    if not 2 <= len(seeds) <= 4:
        errors.append(f"expected 2-4 seeds, found {len(seeds)}")
    if any(value == 8 for value in seed_colors):
        errors.append("input color 8 is reserved for output ties")
    if any(value not in _SEED_COLORS for value in seed_colors):
        errors.append("seed colors must come from {1,2,3,4,6,7,9}")
    if len(set(seed_colors)) != len(seed_colors):
        errors.append("seed colors must be distinct")
    if not any(value == 0 for row in normalized for value in row):
        errors.append("the input must contain open zero territory")

    components = _open_components(normalized)
    seed_positions = {(row, col) for row, col, _ in seeds}
    seeds_per_component = [sum(cell in seed_positions for cell in component) for component in components]
    if any(count == 0 for count in seeds_per_component):
        errors.append("every open component must contain at least one seed")

    internal_walls = sum(
        normalized[row][col] == 5
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    )

    output: list[list[int]] | None = None
    tie_cells = 0
    manhattan_diff_cells = 0
    unreachable_cells = 0
    territory = Counter()
    if seeds:
        distance_maps = [_distance_map(normalized, (row, col)) for row, col, _ in seeds]
        output = [row[:] for row in normalized]
        for row in range(height):
            for col in range(width):
                if normalized[row][col] == 5:
                    continue
                distances = [distance_map[row][col] for distance_map in distance_maps]
                best = min(distances)
                if best >= _INF:
                    unreachable_cells += 1
                winners = [index for index, value in enumerate(distances) if value == best]
                if len(winners) == 1:
                    value = seeds[winners[0]][2]
                    territory[value] += 1
                else:
                    value = 8
                    tie_cells += 1
                output[row][col] = value

                plain_distances = [abs(row - sr) + abs(col - sc) for sr, sc, _ in seeds]
                plain_best = min(plain_distances)
                plain_winners = [index for index, value0 in enumerate(plain_distances) if value0 == plain_best]
                plain_value = seeds[plain_winners[0]][2] if len(plain_winners) == 1 else 8
                if plain_value != value:
                    manhattan_diff_cells += 1

    profile = None
    if len(components) == 2 and internal_walls:
        if len(seeds) == 2:
            profile = "split_two"
        elif len(seeds) == 4:
            profile = "split_four"
    elif len(components) == 1 and not internal_walls:
        if len(seeds) == 2:
            profile = "open_two" if tie_cells else "open_two_unique"
        elif len(seeds) == 3:
            profile = "open_three"
    elif len(components) == 1 and internal_walls:
        if len(seeds) == 2:
            profile = "gated_two"
        elif len(seeds) == 3:
            profile = "gated_three"
        elif len(seeds) == 4:
            profile = "maze_four"

    if profile is None:
        errors.append(
            "topology/seed count does not match a declared scene profile "
            f"(components={len(components)}, internal_walls={internal_walls}, seeds={len(seeds)})"
        )
    elif profile in {"open_two", "open_three"}:
        if tie_cells < 1:
            errors.append(f"{profile} must contain a positive nearest-seed tie witness")
    elif profile == "open_two_unique":
        if tie_cells:
            errors.append("open_two_unique must contain no nearest-seed tie cells")
    elif profile in {"gated_two", "gated_three", "maze_four"}:
        if tie_cells < 1:
            errors.append(f"{profile} must contain a positive nearest-seed tie witness")
        if manhattan_diff_cells < 1:
            errors.append(f"{profile} walls must change at least one winner relative to Manhattan distance")
    elif profile == "split_two":
        if sorted(seeds_per_component) != [1, 1]:
            errors.append("split_two must place exactly one seed in each component")
        if tie_cells:
            errors.append("split_two should be a unique component-local flood without tie cells")
    elif profile == "split_four":
        if sorted(seeds_per_component) != [2, 2]:
            errors.append("split_four must place exactly two seeds in each component")
        if tie_cells < 2:
            errors.append("split_four must contain tie witnesses inside the split components")

    if unreachable_cells:
        errors.append(f"found {unreachable_cells} open cells unreachable from every seed")
    for color in seed_colors:
        if territory.get(color, 0) < 2:
            errors.append(f"seed color {color} must expand beyond its marker cell")

    result.update(
        {
            "height": height,
            "width": width,
            "seeds": seeds,
            "components": components,
            "seeds_per_component": seeds_per_component,
            "internal_walls": internal_walls,
            "tie_cells": tie_cells,
            "manhattan_diff_cells": manhattan_diff_cells,
            "territory_by_color": dict(sorted(territory.items())),
            "output": output,
            "scene_profile": profile,
            "errors": errors,
        }
    )
    return result


def observe_overrides(grid: list[list[int]]) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and semantic branch impostors."""
    return list(_analysis(grid)["errors"])


def _band(difficulty: str | None) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _draw_dimensions(rng, band: str, profile: str) -> tuple[int, int]:
    ranges = {
        "easy": ((5, 8), (7, 10)),
        "medium": ((7, 10), (9, 13)),
        "hard": ((9, 14), (11, 16)),
    }
    (h_lo, h_hi), (w_lo, w_hi) = ranges[band]
    if profile in {"split_four", "maze_four"}:
        h_lo = max(h_lo, 7)
        w_lo = max(w_lo, 9)
    return rng.randint(h_lo, h_hi), rng.randint(w_lo, w_hi)


def _wall_layout(
    height: int,
    width: int,
    profile: str,
    rng,
) -> tuple[list[list[int]], list[list[tuple[int, int]]]]:
    grid = full_grid(height, width, 0)
    _draw_border(grid)
    if profile.startswith("open_"):
        interior = [(row, col) for row in range(1, height - 1) for col in range(1, width - 1)]
        return grid, [interior]

    vertical = rng.choice((True, False))
    split = profile.startswith("split_")
    if vertical:
        divider = rng.randint(2, width - 3)
        for row in range(1, height - 1):
            grid[row][divider] = 5
        if not split:
            gate = rng.randint(1, height - 2)
            grid[gate][divider] = 0
        regions = [
            [(row, col) for row in range(1, height - 1) for col in range(1, divider)],
            [(row, col) for row in range(1, height - 1) for col in range(divider + 1, width - 1)],
        ]
        if profile == "maze_four":
            side = rng.randrange(2)
            row = rng.randint(2, height - 3)
            columns = list(range(1, divider)) if side == 0 else list(range(divider + 1, width - 1))
            if len(columns) >= 3:
                for col in columns:
                    grid[row][col] = 5
                grid[row][rng.choice(columns[1:-1])] = 0
    else:
        divider = rng.randint(2, height - 3)
        for col in range(1, width - 1):
            grid[divider][col] = 5
        if not split:
            gate = rng.randint(1, width - 2)
            grid[divider][gate] = 0
        regions = [
            [(row, col) for row in range(1, divider) for col in range(1, width - 1)],
            [(row, col) for row in range(divider + 1, height - 1) for col in range(1, width - 1)],
        ]
        if profile == "maze_four":
            side = rng.randrange(2)
            col = rng.randint(2, width - 3)
            rows = list(range(1, divider)) if side == 0 else list(range(divider + 1, height - 1))
            if len(rows) >= 3:
                for row in rows:
                    grid[row][col] = 5
                grid[rng.choice(rows[1:-1])][col] = 0

    filtered = [[cell for cell in region if grid[cell[0]][cell[1]] == 0] for region in regions]
    return grid, filtered


def _pick_pair(
    cells: list[tuple[int, int]],
    rng,
    *,
    distance_parity: int | None,
) -> list[tuple[int, int]] | None:
    if len(cells) < 2:
        return None
    for _ in range(160):
        first, second = rng.sample(cells, 2)
        distance = abs(first[0] - second[0]) + abs(first[1] - second[1])
        if distance < 4:
            continue
        if distance_parity is not None and distance % 2 != distance_parity:
            continue
        return [first, second]
    return None


def _pick_many(cells: list[tuple[int, int]], count: int, rng) -> list[tuple[int, int]] | None:
    if len(cells) < count:
        return None
    for _ in range(160):
        chosen = rng.sample(cells, count)
        if all(
            abs(r1 - r2) + abs(c1 - c2) >= 3
            for index, (r1, c1) in enumerate(chosen)
            for r2, c2 in chosen[index + 1 :]
        ):
            return chosen
    return None


def _seed_positions(
    grid: list[list[int]],
    regions: list[list[tuple[int, int]]],
    profile: str,
    rng,
) -> list[tuple[int, int]] | None:
    open_cells = [
        (row, col)
        for row in range(1, len(grid) - 1)
        for col in range(1, len(grid[0]) - 1)
        if grid[row][col] == 0
    ]
    if profile == "open_two":
        return _pick_pair(open_cells, rng, distance_parity=0)
    if profile == "open_two_unique":
        return _pick_pair(open_cells, rng, distance_parity=1)
    if profile == "open_three":
        pair = _pick_pair(open_cells, rng, distance_parity=0)
        if not pair:
            return None
        remaining = [
            cell
            for cell in open_cells
            if cell not in pair and min(abs(cell[0] - r) + abs(cell[1] - c) for r, c in pair) >= 3
        ]
        return pair + [rng.choice(remaining)] if remaining else None
    if profile == "split_two":
        if len(regions) != 2 or any(not region for region in regions):
            return None
        return [rng.choice(region) for region in regions]
    if profile == "split_four":
        if len(regions) != 2:
            return None
        first = _pick_pair(regions[0], rng, distance_parity=0)
        second = _pick_pair(regions[1], rng, distance_parity=0)
        return first + second if first and second else None
    if profile == "gated_two":
        if len(regions) != 2 or any(not region for region in regions):
            return None
        return [rng.choice(region) for region in regions]
    if profile == "gated_three":
        if len(regions) != 2:
            return None
        doubled = rng.randrange(2)
        pair = _pick_pair(regions[doubled], rng, distance_parity=0)
        other = regions[1 - doubled]
        return pair + [rng.choice(other)] if pair and other else None
    if profile == "maze_four":
        if len(regions) != 2:
            return None
        first = _pick_pair(regions[0], rng, distance_parity=0)
        second = _pick_pair(regions[1], rng, distance_parity=0)
        return first + second if first and second else None
    return None


def _candidate(profile: str, band: str, rng) -> list[list[int]] | None:
    height, width = _draw_dimensions(rng, band, profile)
    grid, regions = _wall_layout(height, width, profile, rng)
    positions = _seed_positions(grid, regions, profile, rng)
    if not positions:
        return None
    colors = rng.sample(_SEED_COLORS, len(positions))
    for (row, col), color in zip(positions, colors):
        grid[row][col] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    rng = ctx.draw_rng("layout")
    for _attempt in range(640):
        grid = _candidate(profile, band, rng)
        if grid is None:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return [row[:] for row in grid]
    raise RuntimeError(
        f"failed to construct a valid {profile!r} scene for difficulty {band!r}; "
        "exact overrides are never clamped or replaced by a fallback"
    )
