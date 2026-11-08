from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "5e4fa01a0dc0"
ROOT = find_root(Path(__file__).resolve().parents[3] / "repo")
GEN, GENERATOR_PATH, GENERATOR_SHA = load_selected_generator(TASK, root=ROOT)
OUT = Path(__file__).resolve().parent


def distances(grid, start, *, honor_walls):
    height, width = len(grid), len(grid[0])
    result = {start: 0}
    queue = deque([start])
    while queue:
        row, column = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, column + dc
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if honor_walls and grid[nr][nc] == 5:
                continue
            if (nr, nc) in result:
                continue
            result[(nr, nc)] = result[(row, column)] + 1
            queue.append((nr, nc))
    return result


def shortest_union(grid, first, second, *, honor_walls):
    from_first = distances(grid, first, honor_walls=honor_walls)
    from_second = distances(grid, second, honor_walls=honor_walls)
    if second not in from_first:
        return set(), None
    distance = from_first[second]
    cells = {
        position
        for position, value in from_first.items()
        if position in from_second and value + from_second[position] == distance
    }
    return cells, distance


def transform(grid, *, honor_walls):
    markers = {
        color: next(
            (row, column)
            for row, line in enumerate(grid)
            for column, value in enumerate(line)
            if value == color
        )
        for color in (2, 3, 4)
    }
    cells = set()
    distances_by_leg = {}
    for left, right in ((2, 3), (3, 4)):
        leg, distance = shortest_union(
            grid, markers[left], markers[right], honor_walls=honor_walls
        )
        cells.update(leg)
        distances_by_leg[f"{left}->{right}"] = distance
    output = [line[:] for line in grid]
    for row, column in cells:
        if output[row][column] == 0:
            output[row][column] = 8
    return output, distances_by_leg, cells


def adjacent_to_wall(grid, position):
    row, column = position
    return any(
        0 <= row + dr < len(grid)
        and 0 <= column + dc < len(grid[0])
        and grid[row + dr][column + dc] == 5
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
    )


candidate = None
for difficulty in ("easy", "medium", "hard"):
    for seed in range(1000):
        sample_index = seed * 17 + 3
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        errors = GEN.self_check(grid, difficulty=difficulty)
        if errors:
            continue
        intended, wall_distances, intended_cells = transform(grid, honor_walls=True)
        rival, open_distances, _ = transform(grid, honor_walls=False)
        if intended != rival:
            continue
        if wall_distances != open_distances:
            continue
        painted = {
            (row, column)
            for row, line in enumerate(intended)
            for column, value in enumerate(line)
            if value == 8 and grid[row][column] == 0
        }
        if not painted:
            continue
        adjacent_count = sum(adjacent_to_wall(grid, position) for position in painted)
        if adjacent_count != 0:
            continue
        candidate = {
            "schema": "arcpuzzles-audit-counterexample-v1",
            "task_id": TASK,
            "generator_source": str(GENERATOR_PATH.relative_to(ROOT)),
            "generator_sha256": GENERATOR_SHA,
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "overrides": {},
            "self_check_errors": errors,
            "input": grid,
            "intended_python_mirror": intended,
            "rival_output": rival,
            "rival": "ignore every color-5 wall when finding both shortest-path unions; preserve wall cells in the rendered output",
            "wall_aware_distances": wall_distances,
            "wall_ignored_distances": open_distances,
            "painted_cell_count": len(painted),
            "painted_cells_adjacent_to_wall": adjacent_count,
            "intended_equals_rival": intended == rival,
        }
        break
    if candidate:
        break

if candidate is None:
    raise SystemExit("no counterexample found")
(OUT / "input.json").write_text(json.dumps(candidate["input"], indent=2) + "\n")
(OUT / "counterexample.json").write_text(json.dumps(candidate, indent=2) + "\n")
print(json.dumps({key: candidate[key] for key in (
    "generator_sha256", "seed", "sample_index", "difficulty",
    "wall_aware_distances", "wall_ignored_distances",
    "painted_cell_count", "painted_cells_adjacent_to_wall", "intended_equals_rival",
)}, indent=2))
