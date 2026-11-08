"""Source-bound contact-degree family for task 24b83272f157.

The canonical setting recolors every component by its one-step-halo contact
degree.  The alternative computes the same graph, finds the maximum degree,
and highlights exactly that complete degree class while preserving every other
source object.  Sampling is independent of the private setting.
"""
from __future__ import annotations

import json
from pathlib import Path
import random

TASK_ID = "24b83272f157"
HOME = Path(__file__).resolve().parent
FINISHES = ("degree_palette", "highlight_max_degree")
DEGREE_COLORS = {0: 2, 1: 3, 2: 8, 3: 6, 4: 9}

# Each profile is (height, width, tuple-of-component-cell-tuples). Coordinates
# are absolute before optional whole-canvas reflections. Objects are separated
# as same-color 4-connected components; graph edges use Manhattan distance <=2.
_DEMO_PROFILES = (
    (13, 15, (
        ((4, 5),), ((2, 5),), ((6, 5),), ((4, 3),), ((4, 7),),
        ((10, 11), (10, 12), (10, 13), (11, 11), (11, 12), (11, 13)),
    )),
    (14, 17, (
        ((4, 4),), ((4, 2),), ((4, 6),), ((2, 4),), ((4, 8),),
        ((10, 12), (10, 13), (11, 12), (11, 13)),
    )),
    (15, 18, (
        ((2, 2),), ((2, 4),), ((4, 4),), ((4, 6),), ((6, 6),),
        ((11, 1), (11, 2), (12, 1), (12, 2), (13, 1)),
    )),
    (17, 20, (
        ((6, 8), (7, 8)), ((4, 8),), ((9, 8),), ((6, 6),),
        ((6, 10),), ((6, 12),),
        ((14, 16), (14, 17), (15, 16), (15, 17)),
    )),
    (19, 22, (
        ((7, 7),), ((5, 7),), ((9, 7),), ((7, 5),),
        ((7, 9),), ((5, 9),),
        ((15, 1), (15, 2), (16, 1), (16, 2), (17, 1), (17, 2)),
    )),
    (21, 24, (
        ((8, 10),), ((6, 10),), ((10, 10),), ((8, 8),), ((8, 12),),
        ((6, 12),), ((10, 12),),
        ((17, 20), (17, 21), (18, 20), (18, 21), (19, 20)),
    )),
)

_QUERY_PROFILES = (
    (10, 12, (
        ((3, 4),), ((1, 4),), ((5, 4),), ((3, 2),),
        ((8, 9), (8, 10), (9, 9), (9, 10)),
    )),
    (16, 18, (
        ((5, 5),), ((5, 3),), ((5, 7),), ((3, 5),), ((5, 9),),
        ((12, 13), (12, 14), (13, 13), (13, 14), (14, 13)),
    )),
    (24, 27, (
        ((8, 10),), ((6, 10),), ((10, 10),), ((8, 8),), ((8, 12),),
        ((8, 14),), ((18, 3), (18, 4), (19, 3), (19, 4), (20, 3), (20, 4)),
        ((21, 23), (21, 24), (22, 23), (22, 24)),
    )),
    (30, 30, (
        ((6, 6),), ((4, 6),), ((8, 6),), ((6, 4),), ((6, 8),), ((6, 10),),
        ((28, 27), (28, 28), (28, 29), (29, 27), (29, 28), (29, 29)),
        ((0, 20), (0, 21), (1, 20), (1, 21)),
        ((20, 0), (20, 1), (21, 0), (21, 1)),
    )),
)


def _integer(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def _finish(value: object) -> str:
    if type(value) is not str or value not in FINISHES:
        raise ValueError("finish must be degree_palette or highlight_max_degree")
    return value


def program_for(finish: str) -> str:
    finish = _finish(finish)
    name = "canonical.rkt" if finish == "degree_palette" else "highlight_max_degree.rkt"
    return (HOME / "rules" / name).read_text(encoding="utf-8")


def _build(seed: int, profile_index: int, profile) -> list[list[int]]:
    _integer("seed", seed, 0, 2**63 - 1)
    height, width, groups = profile
    rng = random.Random((seed + 1) * 1_000_003 + profile_index * 9_973)
    flip_v = bool(rng.getrandbits(1)); flip_h = bool(rng.getrandbits(1))
    transformed = []
    for group in groups:
        transformed.append(tuple(sorted(
            (height - 1 - row if flip_v else row,
             width - 1 - col if flip_h else col)
            for row, col in group
        )))
    palette = list(range(1, 9)); rng.shuffle(palette)
    colors = [palette[index % len(palette)] for index in range(len(transformed))]
    # A repeated color is placed only on remote components, never on adjacent ones.
    if len(colors) >= 9:
        colors[-1] = colors[-2]

    # Keep source color from becoming a seed-dependent proxy for graph degree.
    # The highest source color is assigned to a non-maximum-degree group.  Swap
    # only with a uniquely colored group so the move cannot merge components.
    degrees = []
    for first_index, first in enumerate(transformed):
        degree = 0
        for second_index, second in enumerate(transformed):
            if first_index == second_index:
                continue
            distance = min(
                abs(row_a - row_b) + abs(col_a - col_b)
                for row_a, col_a in first
                for row_b, col_b in second
            )
            degree += int(distance <= 2)
        degrees.append(degree)
    maximum = max(degrees)
    highest = max(colors)
    highest_max = next(
        (index for index, degree in enumerate(degrees)
         if degree == maximum and colors[index] == highest),
        None,
    )
    if highest_max is not None:
        target = next(
            index for index, degree in enumerate(degrees)
            if degree < maximum and colors.count(colors[index]) == 1
        )
        colors[highest_max], colors[target] = colors[target], colors[highest_max]

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for group, color in zip(transformed, colors):
        for row, col in group:
            if grid[row][col] != 0:
                raise AssertionError("profile components overlap")
            grid[row][col] = color
    facts = contact_intermediate(grid)
    if len(facts["components"]) != len(groups):
        raise AssertionError("same-color profile components merged")
    if facts["max_degree"] < 2:
        raise AssertionError("profile lost its nontrivial contact graph")
    if set(facts["max_degree_indices"]) == set(facts["largest_object_indices"]):
        raise AssertionError("profile does not refute the largest-object shortcut")
    highest_source = max(component["color"] for component in facts["components"])
    if any(
        facts["components"][index]["color"] == highest_source
        for index in facts["max_degree_indices"]
    ):
        raise AssertionError("profile lets highest source color proxy maximum degree")
    return grid


def sample_demo(seed: int, index: int) -> list[list[int]]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demo index", index, 0, len(_DEMO_PROFILES) - 1)
    return _build(seed, index, _DEMO_PROFILES[index])


def sample_query(seed: int, index: int) -> list[list[int]]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("query index", index, 0, len(_QUERY_PROFILES) - 1)
    return _build(seed ^ 0x5DEECE66D, 100 + index, _QUERY_PROFILES[index])


def _validate_grid(grid) -> tuple[int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be a rectangular list of lists")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("cells must be exact ARC integer colors 0..9")
    return len(grid), width


def _components(grid) -> list[dict]:
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set(); result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]; seen.add((row, col)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc)); stack.append((nr, nc))
            result.append({"color": color, "cells": tuple(sorted(cells)), "size": len(cells)})
    if len(result) < 3:
        raise ValueError("contact-degree family needs at least three objects")
    return result


def _distance(first: dict, second: dict) -> int:
    return min(abs(r1 - r2) + abs(c1 - c2)
               for r1, c1 in first["cells"] for r2, c2 in second["cells"])


def _graph(components: list[dict], threshold: int = 2) -> tuple[tuple[int, ...], ...]:
    neighbors = [set() for _ in components]
    for i, first in enumerate(components):
        for j in range(i + 1, len(components)):
            if _distance(first, components[j]) <= threshold:
                neighbors[i].add(j); neighbors[j].add(i)
    return tuple(tuple(sorted(values)) for values in neighbors)


def contact_intermediate(grid) -> dict:
    components = _components(grid)
    graph = _graph(components)
    degrees = [len(values) for values in graph]
    maximum = max(degrees)
    max_size = max(component["size"] for component in components)
    return {
        "components": [
            {"color": component["color"], "size": component["size"],
             "cells": [list(cell) for cell in component["cells"]]}
            for component in components
        ],
        "graph": [list(values) for values in graph],
        "degrees": degrees,
        "max_degree": maximum,
        "max_degree_indices": [i for i, degree in enumerate(degrees) if degree == maximum],
        "largest_object_indices": [i for i, component in enumerate(components) if component["size"] == max_size],
    }


def _paint(grid, components: list[dict], colors: list[int]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    for component, color in zip(components, colors):
        for row, col in component["cells"]:
            out[row][col] = color
    return out


def _solve_from_graph(grid, finish: str, graph: tuple[tuple[int, ...], ...]) -> list[list[int]]:
    finish = _finish(finish)
    components = _components(grid)
    degrees = [len(values) for values in graph]
    if finish == "degree_palette":
        colors = [DEGREE_COLORS.get(degree, 9) for degree in degrees]
    else:
        maximum = max(degrees)
        colors = [9 if degree == maximum else component["color"]
                  for component, degree in zip(components, degrees)]
    return _paint(grid, components, colors)


def solve(grid, finish: str) -> list[list[int]]:
    components = _components(grid)
    return _solve_from_graph(grid, finish, _graph(components))


def rival_output(grid, finish: str, rival: str) -> list[list[int]]:
    finish = _finish(finish); components = _components(grid)
    graph = _graph(components); degrees = [len(values) for values in graph]
    if rival == "opposite_finish":
        return solve(grid, "highlight_max_degree" if finish == "degree_palette" else "degree_palette")
    if rival == "identity":
        return [list(row) for row in grid]
    if rival == "all_nine":
        return _paint(grid, components, [9] * len(components))
    if rival == "first_object":
        return _paint(grid, components, [9 if i == 0 else obj["color"] for i, obj in enumerate(components)])
    if rival == "largest_object":
        maximum = max(obj["size"] for obj in components)
        return _paint(grid, components, [9 if obj["size"] == maximum else obj["color"] for obj in components])
    if rival == "highest_input_color":
        maximum = max(obj["color"] for obj in components)
        return _paint(grid, components, [9 if obj["color"] == maximum else obj["color"] for obj in components])
    if rival == "degree_at_least_two":
        return _paint(grid, components, [9 if degree >= 2 else obj["color"]
                                         for obj, degree in zip(components, degrees)])
    if rival == "min_degree":
        minimum = min(degrees)
        return _paint(grid, components, [9 if degree == minimum else obj["color"]
                                         for obj, degree in zip(components, degrees)])
    if rival == "distance_one":
        return _solve_from_graph(grid, finish, _graph(components, threshold=1))
    if rival == "size_palette":
        return _paint(grid, components, [DEGREE_COLORS.get(obj["size"], 9) for obj in components])
    raise ValueError(f"unknown rival: {rival}")


DECLARED_RIVALS = (
    "opposite_finish", "identity", "all_nine", "first_object",
    "largest_object", "highest_input_color", "degree_at_least_two",
    "min_degree", "distance_one", "size_palette",
)


def analyze(grid) -> dict:
    height, width = _validate_grid(grid)
    state = contact_intermediate(grid)
    foreground = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return {
        "shape": [height, width],
        "component_count": len(state["components"]),
        "foreground_cells": len(foreground),
        "touches_all_canvas_sides": (
            any(r == 0 for r, _ in foreground) and any(r == height - 1 for r, _ in foreground)
            and any(c == 0 for _, c in foreground) and any(c == width - 1 for _, c in foreground)
        ),
        "degrees": state["degrees"],
        "max_degree": state["max_degree"],
        "max_degree_indices": state["max_degree_indices"],
        "largest_object_indices": state["largest_object_indices"],
        "graph": state["graph"],
    }


def episode_pairs(seed: int, finish: str, demos: int, queries: int = 4):
    _integer("seed", seed, 0, 2**63 - 1); _finish(finish)
    _integer("demos", demos, 2, 6); _integer("queries", queries, 4, 4)
    train = []
    for index in range(demos):
        grid = sample_demo(seed, index); train.append({"input": grid, "output": solve(grid, finish)})
    test = []
    for index in range(queries):
        grid = sample_query(seed, index); test.append({"input": grid, "output": solve(grid, finish)})
    encoded = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(encoded) != len(set(encoded)):
        raise AssertionError("sampler emitted duplicate episode inputs")
    return train, test


def audit_episode(seed: int, finish: str, *, demos: int = 2, queries: int = 4) -> dict:
    train, test = episode_pairs(seed, finish, demos, queries)
    survivors = [
        rival for rival in DECLARED_RIVALS
        if all(rival_output(pair["input"], finish, rival) == pair["output"] for pair in train)
    ]
    return {
        "seed": seed, "finish": finish, "demo_count": demos, "query_count": queries,
        "surviving_rivals": survivors,
        "has_30x30_query": any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30 for pair in test),
        "query_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in test],
        "scope": "finite declared rivals only; not universal rule uniqueness",
    }
