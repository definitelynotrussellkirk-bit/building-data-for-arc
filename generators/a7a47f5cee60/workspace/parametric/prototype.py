"""Native finite parametric family for ARC generator a7a47f5cee60.

``target_role=articulation`` is the exact canonical rule.  The nearby
``largest_articulation_neighbor`` setting first identifies the unique
articulation component, then restricts attention to its graph neighbors and
paints the unique largest one.  That second target cannot be selected before
the articulation identity and contact graph are known.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "a7a47f5cee60"
PARAMETER_NAME = "target_role"
ROLES = ("articulation", "largest_articulation_neighbor")
DEFAULT_SETTINGS = {PARAMETER_NAME: "articulation"}
MOVES = ((-1, 0), (1, 0), (0, -1), (0, 1))

_HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (_HOME / "canonical.rkt").read_text(encoding="utf-8")
LARGEST_NEIGHBOR_PROGRAM = (_HOME / "largest-neighbor.rkt").read_text(encoding="utf-8")

# h,w, top,left, A(h,w), T(h,w), B-width, C/D-height, decoy top/left,
# isolated rectangle(top,left,h,w).  Main graph is A-T plus cycle T-B-D-C-T.
DEMO_SPECS = (
    (18, 22, 5, 8, (2, 2), (3, 3), 4, 5, (0, 0), (13, 0, 5, 5)),
    (19, 24, 6, 9, (2, 3), (3, 4), 5, 5, (0, 0), (14, 0, 5, 6)),
    (20, 25, 6, 10, (3, 2), (4, 3), 5, 7, (0, 0), (16, 0, 4, 8)),
    (22, 26, 7, 10, (2, 3), (4, 4), 5, 6, (0, 0), (17, 0, 5, 7)),
    (23, 27, 8, 11, (3, 3), (4, 4), 6, 7, (0, 0), (17, 0, 6, 8)),
    (24, 28, 8, 12, (2, 4), (5, 4), 6, 8, (0, 0), (17, 0, 7, 7)),
)
QUERY_SPECS = (
    (17, 21, 5, 8, (2, 2), (3, 3), 4, 5, (0, 0), (12, 0, 5, 5)),
    (21, 24, 7, 9, (2, 3), (4, 4), 5, 6, (0, 0), (15, 0, 6, 6)),
    (25, 28, 8, 12, (3, 3), (5, 4), 6, 8, (0, 0), (18, 0, 7, 7)),
    (30, 30, 8, 6, (3, 4), (6, 6), 8, 9, (0, 0), (26, 26, 4, 4)),
)


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain only {PARAMETER_NAME}")
    role = settings[PARAMETER_NAME]
    if type(role) is not str or role not in ROLES:
        raise ValueError(f"{PARAMETER_NAME} must be one of {ROLES}")
    return role


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def program(settings: Any) -> str:
    role = _validate_settings(settings)
    return CANONICAL_PROGRAM if role == "articulation" else LARGEST_NEIGHBOR_PROGRAM


def counterfactual_program(settings: Any) -> str:
    """Opposite target program for a bounded wrong-selection witness."""
    role = _validate_settings(settings)
    return LARGEST_NEIGHBOR_PROGRAM if role == "articulation" else CANONICAL_PROGRAM


def foreground_components(grid: Any) -> list[dict[str, Any]]:
    grid = _validate_grid(grid)
    h, w = len(grid), len(grid[0])
    pending = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result: list[dict[str, Any]] = []
    while pending:
        start = min(pending)
        color = grid[start[0]][start[1]]
        pending.remove(start)
        cells = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in MOVES:
                point = (r + dr, c + dc)
                if point in pending and grid[point[0]][point[1]] == color:
                    pending.remove(point)
                    cells.add(point)
                    stack.append(point)
        ordered = sorted(cells)
        rows = [r for r, _ in ordered]
        cols = [c for _, c in ordered]
        result.append(
            {
                "color": color,
                "cells": ordered,
                "area": len(ordered),
                "bbox": [min(rows), min(cols), max(rows), max(cols)],
            }
        )
    return result


def contact_graph(grid: Any) -> tuple[list[dict[str, Any]], list[set[int]]]:
    components = foreground_components(grid)
    owner = {cell: i for i, component in enumerate(components) for cell in component["cells"]}
    edges = [set() for _ in components]
    for (r, c), i in owner.items():
        for dr, dc in MOVES:
            j = owner.get((r + dr, c + dc))
            if j is not None and j != i:
                edges[i].add(j)
                edges[j].add(i)
    return components, edges


def _graph_component_sets(edges: list[set[int]], skip: int | None = None) -> list[set[int]]:
    remaining = set(range(len(edges)))
    if skip is not None:
        remaining.discard(skip)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            i = stack.pop()
            for j in sorted(edges[i]):
                if j in remaining:
                    remaining.remove(j)
                    component.add(j)
                    stack.append(j)
        result.append(component)
    return result


def articulation_indices(grid: Any) -> list[int]:
    _, edges = contact_graph(grid)
    base = len(_graph_component_sets(edges))
    return [i for i in range(len(edges)) if len(_graph_component_sets(edges, i)) > base]


def graph_intermediate(grid: Any) -> dict[str, Any]:
    """Step A: recover graph, articulation identity, and largest neighbor."""
    components, edges = contact_graph(grid)
    arts = articulation_indices(grid)
    if len(arts) != 1:
        raise ValueError(f"family inputs need one articulation, got {arts}")
    art = arts[0]
    neighbors = sorted(edges[art])
    if not neighbors:
        raise ValueError("articulation has no neighbors")
    max_area = max(components[i]["area"] for i in neighbors)
    largest = [i for i in neighbors if components[i]["area"] == max_area]
    if len(largest) != 1:
        raise ValueError("articulation must have a unique largest neighbor")
    return {
        "components": [
            {
                "color": component["color"],
                "cells": [list(p) for p in component["cells"]],
                "area": component["area"],
                "bbox": list(component["bbox"]),
            }
            for component in components
        ],
        "edges": [sorted(row) for row in edges],
        "degrees": [len(row) for row in edges],
        "component_areas": [component["area"] for component in components],
        "articulation_indices": arts,
        "articulation_index": art,
        "articulation_neighbors": neighbors,
        "largest_neighbor_index": largest[0],
    }


def _paint_indices(grid: list[list[int]], indices) -> list[list[int]]:
    components = foreground_components(grid)
    output = [[0 for _ in row] for row in grid]
    for index in sorted(set(indices)):
        for r, c in components[index]["cells"]:
            output[r][c] = 8
    return output


def transform(grid: Any, settings: Any) -> list[list[int]]:
    grid = _validate_grid(copy.deepcopy(grid))
    role = _validate_settings(settings)
    intermediate = graph_intermediate(grid)
    # Step B consumes the selected graph-role index from Step A.
    target = (
        intermediate["articulation_index"]
        if role == "articulation"
        else intermediate["largest_neighbor_index"]
    )
    return _paint_indices(grid, [target])


def nonzero_cells(grid: Any) -> int:
    grid = _validate_grid(grid)
    return sum(cell != 0 for row in grid for cell in row)


def _fill_rect(grid, top: int, left: int, height: int, width: int, color: int) -> None:
    if type(color) is not int or not 1 <= color <= 9:
        raise ValueError("rectangle color must be 1..9")
    if not (0 <= top and 0 <= left and top + height <= len(grid) and left + width <= len(grid[0])):
        raise ValueError("rectangle leaves grid")
    for r in range(top, top + height):
        for c in range(left, left + width):
            if grid[r][c] != 0:
                raise ValueError("rectangle overlaps existing foreground")
            grid[r][c] = color


def build_block_scene(
    height: int,
    width: int,
    *,
    top: int,
    left: int,
    sizes: dict[str, tuple[int, int]],
    distractors: tuple[tuple[int, int, int, int], ...],
    colors: tuple[int, ...],
) -> list[list[int]]:
    """Small public builder used by tests and future reviewers.

    It creates A--T with a T-B-C triangle. Generated lessons use the stronger
    cycle/decoy builder below, but both obey the same admitted graph grammar.
    """
    _exact_int(height, "height", 1, 30)
    _exact_int(width, "width", 1, 30)
    if set(sizes) != {"A", "T", "B", "C"} or len(colors) != 4 + len(distractors):
        raise ValueError("sizes/colors do not match block-scene contract")
    grid = [[0 for _ in range(width)] for _ in range(height)]
    ah, aw = sizes["A"]
    th, tw = sizes["T"]
    bh, bw = sizes["B"]
    ch, cw = sizes["C"]
    if bh != th or cw != tw + bw:
        raise ValueError("B must match T height and C must span T+B width")
    a_left = left + (tw - aw) // 2
    _fill_rect(grid, top - ah, a_left, ah, aw, colors[0])
    _fill_rect(grid, top, left, th, tw, colors[1])
    _fill_rect(grid, top, left + tw, bh, bw, colors[2])
    _fill_rect(grid, top + th, left, ch, cw, colors[3])
    for rect, color in zip(distractors, colors[4:]):
        _fill_rect(grid, *rect, color)
    graph_intermediate(grid)
    return grid


_DECOY = {
    "P": ((0, 0), (1, 0)),
    "Q": ((0, 1), (0, 2), (1, 2)),
    "R": ((1, 1), (2, 0), (2, 1)),
    "S": ((2, 2),),
}


def _build_generated_scene(spec, colors: dict[str, int]) -> list[list[int]]:
    h, w, top, left, a_size, t_size, b_w, c_h, decoy_pos, isolated = spec
    grid = [[0 for _ in range(w)] for _ in range(h)]
    ah, aw = a_size
    th, tw = t_size
    if c_h * tw <= th * b_w:
        raise ValueError("C must be the unique largest T-neighbor")
    a_left = left + (tw - aw) // 2
    _fill_rect(grid, top - ah, a_left, ah, aw, colors["A"])
    _fill_rect(grid, top, left, th, tw, colors["T"])
    _fill_rect(grid, top, left + tw, th, b_w, colors["B"])
    _fill_rect(grid, top + th, left, c_h, tw, colors["C"])
    _fill_rect(grid, top + th, left + tw, c_h, b_w, colors["D"])
    dt, dl = decoy_pos
    for label, cells in _DECOY.items():
        for dr, dc in cells:
            r, c = dt + dr, dl + dc
            if grid[r][c] != 0:
                raise ValueError("decoy overlaps main graph")
            grid[r][c] = colors[label]
    _fill_rect(grid, *isolated, colors["A"])
    info = graph_intermediate(grid)
    # Generated lessons deliberately refute maximum-degree and global-area shortcuts.
    if len([d for d in info["degrees"] if d == max(info["degrees"])]) < 2:
        raise ValueError("decoy must tie maximum degree")
    if info["largest_neighbor_index"] == max(
        range(len(info["components"])), key=lambda i: info["component_areas"][i]
    ):
        raise ValueError("largest neighbor must not be the global largest component")
    return grid


def _transform_grid(grid: list[list[int]], code: int) -> list[list[int]]:
    result = copy.deepcopy(grid)
    if code >= 4:
        result = [list(reversed(row)) for row in result]
    for _ in range(code % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _stable_seed(seed: int, label: str) -> int:
    payload = f"{TASK_ID}:{seed}:{label}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _scene_from_spec(seed: int, index: int, spec) -> list[list[int]]:
    rng = random.Random(_stable_seed(seed, f"scene:{index}"))
    palette = [1, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(palette)
    labels = ["A", "T", "B", "C", "P", "Q", "R", "S"]
    colors = dict(zip(labels, palette))
    colors["D"] = 2  # persistent visible decoy; neither declared target is D.
    grid = _build_generated_scene(spec, colors)
    transformed = _transform_grid(grid, rng.randrange(8))
    graph_intermediate(transformed)
    return transformed


def _banks(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    demos = [_scene_from_spec(seed, i, spec) for i, spec in enumerate(DEMO_SPECS)]
    queries = [_scene_from_spec(seed, 100 + i, spec) for i, spec in enumerate(QUERY_SPECS)]
    random.Random(_stable_seed(seed, "query-presentation")).shuffle(queries)
    return demos, queries


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    _validate_settings(settings)
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)
    demo_inputs, query_inputs = _banks(seed)
    return {
        "train": [
            {"input": grid, "output": transform(grid, settings)}
            for grid in demo_inputs[:demos]
        ],
        "test": [
            {"input": grid, "output": transform(grid, settings)}
            for grid in query_inputs[:queries]
        ],
        "program_solution": program(settings),
    }


def _input_color_two(grid):
    components = foreground_components(grid)
    return _paint_indices(grid, [i for i, c in enumerate(components) if c["color"] == 2])


def _max_degree(grid):
    _, edges = contact_graph(grid)
    maximum = max((len(row) for row in edges), default=-1)
    return _paint_indices(grid, [i for i, row in enumerate(edges) if len(row) == maximum])


def _global_largest(grid):
    components = foreground_components(grid)
    maximum = max((c["area"] for c in components), default=-1)
    return _paint_indices(grid, [i for i, c in enumerate(components) if c["area"] == maximum])


def _largest_in_articulation_cluster(grid):
    components, edges = contact_graph(grid)
    art = graph_intermediate(grid)["articulation_index"]
    cluster = next(group for group in _graph_component_sets(edges) if art in group)
    maximum = max(components[i]["area"] for i in cluster)
    return _paint_indices(grid, [i for i in cluster if components[i]["area"] == maximum])


def _first_foreground(grid):
    return _paint_indices(grid, [0])


SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "input_color_two": _input_color_two,
    "maximum_degree": _max_degree,
    "global_largest_area": _global_largest,
    "largest_in_articulation_cluster": _largest_in_articulation_cluster,
    "first_foreground": _first_foreground,
}


def lesson_certificate(train: list[dict], query_inputs: list[list[list[int]]]) -> dict[str, Any]:
    if type(train) is not list or not train:
        raise ValueError("train must be nonempty")
    settings_space = [{PARAMETER_NAME: role} for role in ROLES]
    surviving_settings = [
        setting
        for setting in settings_space
        if all(transform(pair["input"], setting) == pair["output"] for pair in train)
    ]
    surviving_shortcuts = [
        name
        for name, rival in SHORTCUTS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in train)
    ]
    return {
        "scope": "finite declared settings and five executable graph shortcuts",
        "surviving_settings": surviving_settings,
        "surviving_shortcuts": surviving_shortcuts,
        "query_count": len(query_inputs),
        "query_outputs_consulted": False,
    }


def public_projection(challenge: dict) -> dict:
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in challenge["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in challenge["test"]],
    }


def public_bytes(challenge: dict) -> bytes:
    return (json.dumps(public_projection(challenge), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def public_id(challenge: dict) -> str:
    return hashlib.sha256(public_bytes(challenge)).hexdigest()


def visible_turn(challenge: dict, index: int) -> dict:
    if type(index) is not int or not 0 <= index < len(challenge["test"]):
        raise ValueError("turn index out of range")
    return {
        "train": public_projection(challenge)["train"],
        "test": [{"input": copy.deepcopy(challenge["test"][index]["input"])}],
    }


def visible_turn_bytes(challenge: dict, index: int) -> bytes:
    return (json.dumps(visible_turn(challenge, index), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
