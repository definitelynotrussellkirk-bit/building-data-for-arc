"""Native Manhattan/Chebyshev nearest-seed partition family for e438ce3e02ce.

The input bank is setting-independent.  Step A computes the nearest seed set
under the selected metric; Step B emits the sole seed color or cyan (8) when
that intermediate set contains more than one seed.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random


HERE = Path(__file__).resolve().parent
METRICS = ("manhattan", "chebyshev")
DEFAULT = {"distance_metric": "manhattan"}
PALETTE = (1, 2, 3, 4, 5, 6, 7, 9)

# Fixed, bounded layouts found once by an offline constructive search.  Each
# layout has ties under both metrics, gives every seed a nontrivial region, and
# yields different Manhattan/Chebyshev labels.  Runtime generation only applies
# deterministic reflections and color permutations; it performs no rejection
# sampling.
_DEMO_PROFILES = (
    (9, 9, ((5, 2), (1, 6), (6, 1))),
    (10, 12, ((2, 1), (6, 3), (0, 9), (8, 0))),
    (12, 15, ((7, 1), (1, 7), (11, 13), (6, 2), (0, 12))),
    (16, 18, ((12, 15), (4, 10), (7, 4))),
    (22, 24, ((4, 15), (2, 8), (9, 13), (21, 1))),
    (26, 28, ((0, 12), (25, 10), (6, 0), (13, 27), (17, 6))),
)
_QUERY_PROFILES = (
    (9, 11, ((6, 1), (2, 7), (2, 4), (8, 7))),
    (18, 21, ((8, 1), (1, 6), (9, 3), (8, 18), (11, 18))),
    (30, 30, ((0, 16), (29, 13), (7, 0), (16, 29), (14, 23))),
    (27, 29, ((20, 21), (19, 12), (2, 2))),
)


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _metric(settings) -> str:
    if (type(settings) is not dict or set(settings) != {"distance_metric"}
            or type(settings["distance_metric"]) is not str
            or settings["distance_metric"] not in METRICS):
        raise ValueError("settings must contain only a supported distance_metric")
    return settings["distance_metric"]


def program(settings) -> str:
    metric = _metric(settings)
    name = "canonical.rkt" if metric == "manhattan" else "chebyshev.rkt"
    return (HERE / name).read_text()


def _validate_grid(grid) -> tuple[int, int, list[tuple[int, int, int]]]:
    if (type(grid) is not list or not 5 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 5 <= len(grid[0]) <= 30):
        raise ValueError("expected a rectangular 5..30 grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid cells must be exact ARC integer colors")
    seeds = [(row, column, value) for row, line in enumerate(grid)
             for column, value in enumerate(line) if value != 0]
    if not 3 <= len(seeds) <= 5:
        raise ValueError("input must contain exactly 3..5 seeds")
    colors = [value for _, _, value in seeds]
    if 8 in colors or len(colors) != len(set(colors)):
        raise ValueError("seed colors must be pairwise distinct and exclude 8")
    return len(grid), width, seeds


def _distance(metric: str, row: int, column: int, seed_row: int, seed_column: int) -> int:
    dr, dc = abs(row - seed_row), abs(column - seed_column)
    return dr + dc if metric == "manhattan" else max(dr, dc)


def nearest_sets(grid, distance_metric="manhattan"):
    if type(distance_metric) is not str or distance_metric not in METRICS:
        raise ValueError("unknown distance metric")
    height, width, seeds = _validate_grid(grid)
    result = []
    for row in range(height):
        line = []
        for column in range(width):
            if grid[row][column] != 0:
                line.append((grid[row][column],))
                continue
            distances = [_distance(distance_metric, row, column, sr, sc)
                         for sr, sc, _ in seeds]
            minimum = min(distances)
            line.append(tuple(seeds[index][2] for index, distance in enumerate(distances)
                              if distance == minimum))
        result.append(line)
    return result


def solve(grid, distance_metric="manhattan"):
    nearest = nearest_sets(grid, distance_metric)
    return [[colors[0] if len(colors) == 1 else 8 for colors in row] for row in nearest]


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"e438ce3e02ce-parametric-v1:{seed}:{split}:{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _profile(seed: int, split: str, index: int):
    height, width, source_points = (_DEMO_PROFILES if split == "train" else _QUERY_PROFILES)[index]
    rng = _rng(seed, split, index)
    flip_rows = bool(rng.getrandbits(1))
    flip_columns = bool(rng.getrandbits(1))
    points = [
        (height - 1 - row if flip_rows else row,
         width - 1 - column if flip_columns else column)
        for row, column in source_points
    ]
    colors = rng.sample(PALETTE, len(points))
    grid = [[0] * width for _ in range(height)]
    for (row, column), color in zip(points, colors):
        grid[row][column] = color
    return grid


def generate(seed, settings, demos, queries):
    metric = _metric(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    banks = {
        "train": [_profile(seed, "train", index) for index in range(6)],
        "test": [_profile(seed, "test", index) for index in range(4)],
    }
    result = {}
    for split, count in (("train", demos), ("test", queries)):
        result[split] = [
            {"input": copy.deepcopy(grid), "output": solve(grid, metric)}
            for grid in banks[split][:count]
        ]
    return {**result, "program_solution": program(settings), "seed": seed,
            "settings": copy.deepcopy(settings)}


def public_turn(episode, query_index):
    _integer(query_index, 0, 3, "query_index")
    if (type(episode) is not dict or type(episode.get("train")) is not list
            or type(episode.get("test")) is not list or query_index >= len(episode["test"])):
        raise ValueError("episode does not contain the requested query")
    return {"train": copy.deepcopy(episode["train"]),
            "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}]}
