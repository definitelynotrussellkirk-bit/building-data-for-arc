"""Source-bound authoring helpers for the post-lookup repeat-policy family.

The canonical setting preserves the selected task exactly: each isolated blue
body object is recolored from the full header above its bbox-left column.  The
alternate setting consumes that first-stage result: every object whose looked-up
color is shared by another object is then marked 9.  Inputs are matched across
settings and extend the lawful grammar through substantive 30x30 cases.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Callable, Iterable

TASK_ID = "0dba62203065"
POLICIES = ("retain", "mark_repeated")
COLORS = tuple(range(2, 9))
HOME = Path(__file__).resolve().parent

DEMO_DIMS = ((9, 12), (11, 15), (14, 18), (16, 21), (19, 24), (22, 26))
QUERY_DIMS = ((12, 14), (18, 20), (24, 27), (30, 30))
DEMO_COUNTS = (4, 5, 5, 6, 6, 7)
QUERY_COUNTS = (4, 5, 6, 8)

LEFT_TRAP = ((0, 1), (1, 0), (1, 1))
RIGHT_TRAP = ((0, 0), (0, 1), (1, 0))
WIDE_THREE = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2))
WIDE_FOUR = ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3))
EXTRA_SHAPES = (
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (2, 3), (1, 3)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (2, 2)),
)

Grid = list[list[int]]
Cell = tuple[int, int]
Shape = tuple[Cell, ...]


def _plain_int(value, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a plain integer in {low}..{high}")
    return value


def validate_request(seed: int, demos: int, queries: int) -> None:
    _plain_int(seed, "seed", 0, 2**63 - 1)
    _plain_int(demos, "demos", 2, 6)
    _plain_int(queries, "queries", 1, 4)


def validate_policy(policy: object) -> str:
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError("repeat_policy must be retain or mark_repeated")
    return policy


def _program_path(policy: str) -> Path:
    return HOME / "programs" / f"{validate_policy(policy)}.rkt"


def program_for(policy: str) -> str:
    path = _program_path(policy)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing regular program source: {path.name}")
    return path.read_text(encoding="utf-8")


def _shape_bounds(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _translate(shape: Shape, top: int, left: int) -> tuple[Cell, ...]:
    return tuple((top + r, left + c) for r, c in shape)


def _moat_clear(cells: Iterable[Cell], occupied: set[Cell]) -> bool:
    return all(
        (row + dr, col + dc) not in occupied
        for row, col in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    )


def _place_shapes(height: int, width: int, shapes: tuple[Shape, ...], rng: random.Random) -> list[tuple[Cell, ...]]:
    last_h, last_w = _shape_bounds(shapes[1])
    forced = [
        _translate(shapes[0], 1, 0),
        _translate(shapes[1], height - last_h, (width - 1) - last_w),
    ]
    occupied = set(forced[0]) | set(forced[1])
    if not _moat_clear(forced[0], set(forced[1])):
        raise ValueError("forced boundary shapes overlap")
    forced_anchors = {min(c for _, c in cells) for cells in forced}
    if len(forced_anchors) != len(forced):
        raise ValueError("forced anchors must be distinct")

    candidate_sets: list[list[tuple[Cell, ...]]] = []
    for shape in shapes[2:]:
        shape_h, shape_w = _shape_bounds(shape)
        max_left = (width - 1) - shape_w
        candidates = [
            _translate(shape, top, left)
            for top in range(1, height - shape_h + 1)
            for left in range(max_left + 1)
        ]
        rng.shuffle(candidates)
        candidate_sets.append(candidates)

    def search(index: int, used: set[Cell], anchors: set[int], chosen: list[tuple[Cell, ...]]):
        if index == len(candidate_sets):
            return chosen[:]
        for cells in candidate_sets[index]:
            anchor = min(c for _, c in cells)
            if anchor in anchors or not _moat_clear(cells, used):
                continue
            chosen.append(cells)
            found = search(index + 1, used | set(cells), anchors | {anchor}, chosen)
            if found is not None:
                return found
            chosen.pop()
        return None

    rest = search(0, occupied, forced_anchors, [])
    if rest is None:
        raise ValueError(f"cannot place {len(shapes)} uniquely anchored objects in {height}x{width}")
    return forced + rest


def _components(grid: Grid) -> list[tuple[Cell, ...]]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    found: list[tuple[Cell, ...]] = []
    for row in range(1, height):
        for col in range(width - 1):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = r + dr, c + dc
                    if (1 <= rr < height and 0 <= cc < width - 1
                            and grid[rr][cc] != 0 and (rr, cc) not in seen):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            found.append(tuple(sorted(cells)))
    return sorted(found, key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells)))


def analyze(grid: object) -> dict[str, object]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a rectangular 1..30 list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid cells must be plain ARC integers")
    if any(v not in COLORS for v in grid[0]):
        raise ValueError("header must contain only colors 2..8")
    if any(grid[r][c] not in (0, 1) for r in range(1, len(grid)) for c in range(width)):
        raise ValueError("body must contain only 0 and 1")
    if any(grid[r][width - 1] != 0 for r in range(1, len(grid))):
        raise ValueError("last body column must remain blank")
    components = _components(grid)
    if not components:
        raise ValueError("body needs at least one object")
    return {"height": len(grid), "width": width, "header": list(grid[0]), "components": components}


def _lookup_records(grid: Grid) -> list[dict[str, object]]:
    records = []
    for cells in analyze(grid)["components"]:
        left = min(c for _, c in cells)
        right = max(c for _, c in cells)
        records.append({"cells": cells, "left": left, "right": right, "color": grid[0][left], "size": len(cells)})
    return records


def lookup_stage(grid: Grid) -> Grid:
    output = deepcopy(grid)
    for record in _lookup_records(grid):
        for row, col in record["cells"]:
            output[row][col] = record["color"]
    return output


def _mark_records(stage: Grid, records: list[dict[str, object]], predicate: Callable[[dict[str, object]], bool]) -> Grid:
    output = deepcopy(stage)
    for record in records:
        if predicate(record):
            for row, col in record["cells"]:
                output[row][col] = 9
    return output


def transform(grid: Grid, policy: str) -> Grid:
    policy = validate_policy(policy)
    records = _lookup_records(grid)
    stage = lookup_stage(grid)
    if policy == "retain":
        return stage
    frequencies = Counter(record["color"] for record in records)
    return _mark_records(stage, records, lambda record: frequencies[record["color"]] > 1)


def _row_major_column(cells: tuple[Cell, ...], first: bool) -> int:
    return (min(cells) if first else max(cells))[1]


def _paint_by_column(grid: Grid, selector: Callable[[tuple[Cell, ...]], int]) -> Grid:
    output = deepcopy(grid)
    for cells in analyze(grid)["components"]:
        color = grid[0][selector(cells)]
        for row, col in cells:
            output[row][col] = color
    return output


def _rival_first_cell(grid: Grid) -> Grid:
    return _paint_by_column(grid, lambda cells: _row_major_column(cells, True))


def _rival_last_cell(grid: Grid) -> Grid:
    return _paint_by_column(grid, lambda cells: _row_major_column(cells, False))


def _rival_center_floor(grid: Grid) -> Grid:
    return _paint_by_column(grid, lambda cells: (min(c for _, c in cells) + max(c for _, c in cells)) // 2)


def _rival_center_ceil(grid: Grid) -> Grid:
    return _paint_by_column(grid, lambda cells: (min(c for _, c in cells) + max(c for _, c in cells) + 1) // 2)


def _rival_per_cell(grid: Grid) -> Grid:
    output = deepcopy(grid)
    for cells in analyze(grid)["components"]:
        for row, col in cells:
            output[row][col] = grid[0][col]
    return output


def _rival_size_at_most_four(grid: Grid) -> Grid:
    output = deepcopy(grid)
    for record in _lookup_records(grid):
        if record["size"] <= 4:
            for row, col in record["cells"]:
                output[row][col] = record["color"]
    return output


def _rival_skip_row_one(grid: Grid) -> Grid:
    output = lookup_stage(grid)
    for record in _lookup_records(grid):
        for row, col in record["cells"]:
            if row == 1:
                output[row][col] = 1
    return output


def _rival_cycle_from_first_two(grid: Grid) -> Grid:
    start = grid[0][0] - 2
    delta = (grid[0][1] - grid[0][0]) % 7
    step = 1 if delta in (1, 2, 3) else -1
    inferred = [2 + ((start + step * col) % 7) for col in range(len(grid[0]))]
    output = deepcopy(grid)
    for record in _lookup_records(grid):
        color = inferred[record["left"]]
        for row, col in record["cells"]:
            output[row][col] = color
    return output


def _rival_mark_all(grid: Grid) -> Grid:
    records = _lookup_records(grid)
    return _mark_records(lookup_stage(grid), records, lambda record: True)


def _rival_mark_repeated_size(grid: Grid) -> Grid:
    records = _lookup_records(grid)
    frequencies = Counter(record["size"] for record in records)
    return _mark_records(lookup_stage(grid), records, lambda record: frequencies[record["size"]] > 1)


def _rival_mark_global_header_duplicate(grid: Grid) -> Grid:
    records = _lookup_records(grid)
    frequencies = Counter(grid[0])
    return _mark_records(lookup_stage(grid), records, lambda record: frequencies[record["color"]] > 1)


def _rival_mark_right_edge_duplicate(grid: Grid) -> Grid:
    records = _lookup_records(grid)
    right_colors = [grid[0][record["right"]] for record in records]
    frequencies = Counter(right_colors)
    stage = lookup_stage(grid)
    return _mark_records(stage, records, lambda record: frequencies[grid[0][record["right"]]] > 1)


def _rival_mark_largest_of_repeated(grid: Grid) -> Grid:
    records = _lookup_records(grid)
    groups: dict[int, list[dict[str, object]]] = {}
    for record in records:
        groups.setdefault(record["color"], []).append(record)
    selected: set[tuple[Cell, ...]] = set()
    for group in groups.values():
        if len(group) > 1:
            largest = max(group, key=lambda record: (record["size"], record["cells"]))
            selected.add(largest["cells"])
    return _mark_records(lookup_stage(grid), records, lambda record: record["cells"] in selected)


def _rival_mark_color_two(grid: Grid) -> Grid:
    records = _lookup_records(grid)
    return _mark_records(lookup_stage(grid), records, lambda record: record["color"] == 2)


RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "first_cell_column": _rival_first_cell,
    "right_edge_column": _rival_last_cell,
    "bbox_center_floor": _rival_center_floor,
    "bbox_center_ceil": _rival_center_ceil,
    "per_cell_column": _rival_per_cell,
    "size_at_most_four": _rival_size_at_most_four,
    "skip_row_one": _rival_skip_row_one,
    "cycle_from_first_two": _rival_cycle_from_first_two,
    "mark_all_objects": _rival_mark_all,
    "mark_repeated_size": _rival_mark_repeated_size,
    "mark_global_header_duplicate": _rival_mark_global_header_duplicate,
    "mark_repeated_right_edge": _rival_mark_right_edge_duplicate,
    "mark_largest_of_repeated": _rival_mark_largest_of_repeated,
    "mark_fixed_color_two": _rival_mark_color_two,
}


def _column_graph(width: int, placements: list[tuple[Cell, ...]]) -> dict[int, set[int]]:
    graph = {col: set() for col in range(width)}
    for cells in placements:
        columns = sorted({col for _, col in cells})
        for i, a in enumerate(columns):
            for b in columns[i + 1:]:
                graph[a].add(b)
                graph[b].add(a)
    return graph


def _header(width: int, placements: list[tuple[Cell, ...]], rng: random.Random) -> list[int]:
    """Color columns while forcing one mixed-size repeated object color class.

    All object left anchors are distinct. Exactly one anchor-color pair repeats;
    other anchor colors are unique. One unique anchor color is duplicated only at
    a non-anchor decoy column, making global-header-frequency a wrong shortcut.
    """
    graph = _column_graph(width, placements)
    anchors = [min(c for _, c in cells) for cells in placements]
    if len(anchors) != len(set(anchors)):
        raise ValueError("object left anchors must be distinct")
    candidates = [
        (i, j)
        for i in range(len(placements))
        for j in range(i + 1, len(placements))
        if len(placements[i]) != len(placements[j]) and anchors[j] not in graph[anchors[i]]
    ]
    if not candidates:
        raise ValueError("no lawful mixed-size duplicate anchor pair")
    rng.shuffle(candidates)
    pair = candidates[0]

    duplicate_color = rng.choice(tuple(color for color in COLORS if color != 2))
    forced: dict[int, int] = {anchors[pair[0]]: duplicate_color, anchors[pair[1]]: duplicate_color}
    other_indices = [index for index in range(len(anchors)) if index not in pair]
    rng.shuffle(other_indices)
    if not other_indices:
        raise ValueError("repeat-policy scenes need a unique anchor color")
    unique_index = other_indices[0]
    forced[anchors[unique_index]] = 2
    remaining_colors = [color for color in COLORS if color not in (duplicate_color, 2)]
    rng.shuffle(remaining_colors)
    if len(other_indices) - 1 > len(remaining_colors):
        raise ValueError("not enough colors for unique nonduplicate anchors")
    for index, color in zip(other_indices[1:], remaining_colors, strict=False):
        forced[anchors[index]] = color

    unique_anchor = anchors[unique_index]
    anchor_set = set(anchors)
    decoys = [
        col for col in range(width)
        if col not in anchor_set and col not in graph[unique_anchor]
    ]
    if not decoys:
        raise ValueError("no non-anchor decoy column for global-frequency trap")
    rng.shuffle(decoys)
    forced[decoys[0]] = 2

    for col, color in forced.items():
        if any(forced.get(neighbor) == color for neighbor in graph[col]):
            raise ValueError("forced header colors violate an object-column clique")

    assigned = dict(forced)
    order = sorted((col for col in range(width) if col not in assigned), key=lambda col: (-len(graph[col]), col))

    def color(index: int) -> bool:
        if index == len(order):
            return True
        col = order[index]
        choices = [candidate for candidate in COLORS if all(assigned.get(n) != candidate for n in graph[col])]
        rng.shuffle(choices)
        for candidate in choices:
            assigned[col] = candidate
            if color(index + 1):
                return True
            del assigned[col]
        return False

    if not color(0):
        raise ValueError("header coloring constraints are unsatisfiable")
    return [assigned[col] for col in range(width)]


def _shape_sequence(count: int, rng: random.Random) -> tuple[Shape, ...]:
    if count < 4:
        raise ValueError("scene needs at least four objects")
    extra = list(EXTRA_SHAPES)
    rng.shuffle(extra)
    while len(extra) < count - 4:
        extra.extend(EXTRA_SHAPES)
    return (LEFT_TRAP, RIGHT_TRAP, WIDE_THREE, WIDE_FOUR, *extra[: count - 4])


def _scene(seed: int, split: str, index: int, height: int, width: int, count: int) -> Grid:
    rng = random.Random(f"{TASK_ID}:repeat-policy-v2:{seed}:{split}:{index}")
    placements = _place_shapes(height, width, _shape_sequence(count, rng), rng)
    for _ in range(256):
        header = _header(width, placements, rng)
        grid = [[0] * width for _ in range(height)]
        grid[0] = header
        for cells in placements:
            for row, col in cells:
                grid[row][col] = 1
        truths = {policy: transform(grid, policy) for policy in POLICIES}
        if truths["retain"] == truths["mark_repeated"]:
            continue
        if all(rival(grid) != truth for truth in truths.values() for rival in RIVALS.values()):
            return grid
    raise ValueError("could not color a decisive repeat-policy scene")


def sample_inputs(seed: int, demos: int, queries: int) -> tuple[list[Grid], list[Grid]]:
    validate_request(seed, demos, queries)
    train = [_scene(seed, "train", index, *DEMO_DIMS[index], DEMO_COUNTS[index]) for index in range(demos)]
    test = [_scene(seed, "test", index, *QUERY_DIMS[index], QUERY_COUNTS[index]) for index in range(queries)]
    keys = [json.dumps(grid, separators=(",", ":")) for grid in train + test]
    if len(keys) != len(set(keys)):
        raise AssertionError("episode inputs must be distinct")
    return train, test


def generate_episode(seed: int, policy: str, demos: int, queries: int) -> dict[str, object]:
    policy = validate_policy(policy)
    train_inputs, test_inputs = sample_inputs(seed, demos, queries)
    make = lambda grid: {"input": grid, "output": transform(grid, policy)}
    return {
        "train": [make(grid) for grid in train_inputs],
        "test": [make(grid) for grid in test_inputs],
        "program_solution": program_for(policy),
    }


def public_challenge(episode: dict[str, object]) -> dict[str, object]:
    return {
        "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in episode["train"]],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def sequential_views(episode: dict[str, object]) -> list[dict[str, object]]:
    public = public_challenge(episode)
    return [{"train": deepcopy(public["train"]), "test": [deepcopy(query)]} for query in public["test"]]


def audit_episode(episode: dict[str, object], policy: str) -> dict[str, object]:
    policy = validate_policy(policy)
    demos = episode["train"]
    queries = episode["test"]
    setting_survivors = [
        candidate for candidate in POLICIES
        if all(transform(pair["input"], candidate) == pair["output"] for pair in demos)
    ]
    refuted: list[str] = []
    harmful: list[str] = []
    for name, rival in RIVALS.items():
        fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if not fits:
            refuted.append(name)
        elif any(rival(pair["input"]) != pair["output"] for pair in queries):
            harmful.append(name)
    return {
        "policy": policy,
        "setting_survivors": setting_survivors,
        "refuted_rivals": refuted,
        "harmful_survivors": harmful,
    }


def dependency_facts(grid: Grid, policy: str) -> dict[str, object]:
    policy = validate_policy(policy)
    records = _lookup_records(grid)
    frequencies = Counter(record["color"] for record in records)
    objects = []
    for record in records:
        objects.append({
            "cells": [list(cell) for cell in record["cells"]],
            "left_column": record["left"],
            "right_column": record["right"],
            "selected_column": record["left"],
            "post_lookup_color": record["color"],
            "post_lookup_frequency": frequencies[record["color"]],
            "marked": policy == "mark_repeated" and frequencies[record["color"]] > 1,
        })
    return {
        "policy": policy,
        "step_a": "left-edge header lookup recolors each body object",
        "intermediate": "post-lookup object colors and their object-class multiplicities",
        "step_b": "mark every post-lookup color class with multiplicity above one",
        "post_lookup_color_frequencies": {str(color): count for color, count in sorted(frequencies.items())},
        "objects": objects,
    }


def grid_sha256(grid: Grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
