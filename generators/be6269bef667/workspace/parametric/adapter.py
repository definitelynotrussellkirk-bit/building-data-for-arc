"""Matched-input ray lessons with an input-derived plurality weighting.

The canonical setting adds one along every directed ray.  The alternative first
counts direction-coded emitters, selects the unique plurality direction, and
then traces every ray while adding two for rays in that selected direction and
one for all others.  Native qualification independently executes all labels in
protected Racket.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
from pathlib import Path
import random


HERE = Path(__file__).resolve().parent
WEIGHTINGS = ("unit", "plurality_double")
DIRECTIONS = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}
TRAIN_PROFILES = (
    (8, 9, 4, 2, 4),
    (9, 11, 4, 2, 4),
    (12, 13, 5, 2, 5),
    (15, 17, 5, 3, 6),
    (20, 22, 6, 3, 7),
    (24, 26, 7, 3, 8),
)
QUERY_PROFILES = (
    (10, 13, 4, 2, 4),
    (17, 19, 6, 3, 6),
    (30, 30, 10, 5, 8),
    (24, 29, 7, 3, 8),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _weighting(settings):
    if (type(settings) is not dict or set(settings) != {"weighting"}
            or type(settings["weighting"]) is not str
            or settings["weighting"] not in WEIGHTINGS):
        raise ValueError(
            "settings must contain only weighting='unit' or 'plurality_double'"
        )
    return settings["weighting"]


def program(settings):
    weighting = _weighting(settings)
    filename = "canonical.rkt" if weighting == "unit" else "plurality_double.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _grid(grid):
    if (type(grid) is not list or not 3 <= len(grid) <= 30
            or type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30):
        raise ValueError("expected a rectangular 3..30 grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def analyze(grid):
    grid = _grid(grid)
    counts = Counter(value for row in grid for value in row if value in DIRECTIONS)
    direction_counts = {direction: counts[direction] for direction in DIRECTIONS}
    if any(value <= 0 for value in direction_counts.values()):
        raise ValueError("scene needs all four emitter directions")
    maximum = max(direction_counts.values())
    plurality = [direction for direction, count in direction_counts.items() if count == maximum]
    if len(plurality) != 1:
        raise ValueError("scene needs one unique plurality direction")
    return {
        "direction_counts": direction_counts,
        "plurality_direction": plurality[0],
        "wall_count": sum(value == 5 for row in grid for value in row),
    }


def solve_weighted(grid, weights):
    grid = _grid(grid)
    if (type(weights) is not dict or set(weights) != set(DIRECTIONS)
            or any(type(value) is not int or value <= 0 for value in weights.values())):
        raise ValueError("weights must give positive exact integers for directions 1..4")
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in DIRECTIONS:
                continue
            dr, dc = DIRECTIONS[value]
            rr, cc = r, c
            while 0 <= rr < height and 0 <= cc < width and grid[rr][cc] != 5:
                out[rr][cc] += weights[value]
                rr += dr
                cc += dc
    return out


def solve(grid, weighting="unit"):
    if type(weighting) is not str or weighting not in WEIGHTINGS:
        raise ValueError("unknown weighting")
    facts = analyze(grid)
    weights = {direction: 1 for direction in DIRECTIONS}
    if weighting == "plurality_double":
        weights[facts["plurality_direction"]] = 2
    return solve_weighted(grid, weights)


def _rng(seed, split, index):
    raw = f"be6269bef667-parametric-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _plurality(seed, split, index):
    offset = 0 if split == "train" else 2
    return 1 + ((seed + index + offset) % 4)


def _scene(seed, split, index, profile):
    height, width, plurality_count, other_count, wall_count = profile
    plurality = _plurality(seed, split, index)
    counts = {direction: other_count for direction in DIRECTIONS}
    counts[plurality] = plurality_count
    rng = _rng(seed, split, index)

    vertical = list(range(1, width - 1))
    horizontal = list(range(1, height - 1))
    rng.shuffle(vertical)
    rng.shuffle(horizontal)
    if counts[1] + counts[3] > len(vertical) or counts[2] + counts[4] > len(horizontal):
        raise ValueError("profile lacks edge positions for disjoint rays")

    columns = {
        1: vertical[:counts[1]],
        3: vertical[counts[1]:counts[1] + counts[3]],
    }
    rows = {
        2: horizontal[:counts[2]],
        4: horizontal[counts[2]:counts[2] + counts[4]],
    }
    grid = [[0] * width for _ in range(height)]
    for c in columns[1]:
        grid[height - 1][c] = 1
    for c in columns[3]:
        grid[0][c] = 3
    for r in rows[2]:
        grid[r][0] = 2
    for r in rows[4]:
        grid[r][width - 1] = 4

    active_rows = rows[2] + rows[4]
    active_cols = columns[1] + columns[3]
    intersections = [(r, c) for r in active_rows for c in active_cols]
    rng.shuffle(intersections)
    if plurality in (1, 3):
        selected_lines = columns[plurality]
        witness_candidates = [(r, c) for c in selected_lines for r in active_rows]
    else:
        selected_lines = rows[plurality]
        witness_candidates = [(r, c) for r in selected_lines for c in active_cols]
    witness = min(
        witness_candidates,
        key=lambda point: (abs(point[0] - height / 2) + abs(point[1] - width / 2), point),
    )
    walls = [witness]
    for point in intersections:
        if point not in walls and len(walls) < min(wall_count, 4):
            walls.append(point)
    interior = [(r, c) for r in range(1, height - 1) for c in range(1, width - 1)
                if grid[r][c] == 0 and (r, c) not in walls]
    rng.shuffle(interior)
    while len(walls) < wall_count:
        walls.append(interior.pop())
    for r, c in walls:
        grid[r][c] = 5

    facts = analyze(grid)
    if facts["plurality_direction"] != plurality or facts["wall_count"] != wall_count:
        raise RuntimeError("constructed scene lost its plurality/wall contract")
    # The witness is interior on a selected ray, so cells exist beyond it.
    if not (0 < witness[0] < height - 1 and 0 < witness[1] < width - 1):
        raise RuntimeError("constructed wall witness is not interior")
    return grid


def _input(seed, split, index):
    profiles = TRAIN_PROFILES if split == "train" else QUERY_PROFILES
    try:
        profile = profiles[index]
    except (IndexError, TypeError) as error:
        raise ValueError("unsupported split/index") from error
    return _scene(seed, split, index, profile)


def sample_inputs(seed, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {
        "train": [_input(seed, "train", index) for index in range(demos)],
        "test": [_input(seed, "test", index) for index in range(queries)],
    }
    serialized = [repr(grid) for split in ("train", "test") for grid in result[split]]
    if len(serialized) != len(set(serialized)):
        raise ValueError("authored episode inputs must be distinct")
    return result


def generate(seed, settings, demos=3, queries=4):
    weighting = _weighting(settings)
    sampled = sample_inputs(seed, demos=demos, queries=queries)
    return {
        "train": [
            {"input": copy.deepcopy(grid), "output": solve(grid, weighting)}
            for grid in sampled["train"]
        ],
        "test": [
            {"input": copy.deepcopy(grid), "output": solve(grid, weighting)}
            for grid in sampled["test"]
        ],
        "program_solution": program(settings),
        "seed": seed,
        "settings": copy.deepcopy(settings),
    }


def public_turn(episode, query_index=0):
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select an existing query")
    try:
        train = [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ]
        query = {"input": copy.deepcopy(episode["test"][query_index]["input"])}
    except (KeyError, TypeError) as error:
        raise ValueError("episode lacks private train/test pairs") from error
    return {"train": train, "test": [query]}
