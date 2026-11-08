"""Classify component-local cavities, then fill/recolor and add an exterior rim."""
from __future__ import annotations
from collections import Counter
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import random

TASK_ID = "public_eval_aa4ec2a5"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"hole_connectivity": [4, 8]}
DEFAULT = {"hole_connectivity": 4}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}
INPUT_COLORS = (0, 1, 3, 4, 5, 7, 9)
CONNECTIVITY_BINDING = "(hole-connectivity 4)"
assert CANONICAL.count(CONNECTIVITY_BINDING) == 1
ALTERNATIVE = CANONICAL.replace(CONNECTIVITY_BINDING, "(hole-connectivity 8)", 1)


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"hole_connectivity"}
            or type(settings["hole_connectivity"]) is not int
            or settings["hole_connectivity"] not in (4, 8)):
        raise ValueError("settings must be exactly hole_connectivity=4 or8")
    return settings["hole_connectivity"]


def program(settings):
    return CANONICAL if _setting(settings) == 4 else ALTERNATIVE


def _validate(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30 or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
            or any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row)):
        raise ValueError("need an exact-integer rectangular ARC grid with axes1..30")
    ranking = Counter(v for row in grid for v in row).most_common()
    if len(ranking) != 2 or ranking[0][1] == ranking[1][1]:
        raise ValueError("need two input colors with a unique modal background")
    if any(color not in INPUT_COLORS for color, _ in ranking):
        raise ValueError("input colors must remain distinct from semantic output colors2,6,8")
    return ranking[0][0], ranking[1][0]


def components(cells, connectivity=4):
    remaining = set(cells)
    neighbors = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if connectivity == 8:
        neighbors += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    result = []
    while remaining:
        first = min(remaining)
        group, stack = {first}, [first]
        remaining.remove(first)
        while stack:
            r, c = stack.pop()
            for dr, dc in neighbors:
                p = r + dr, c + dc
                if p in remaining:
                    remaining.remove(p); group.add(p); stack.append(p)
        result.append(tuple(sorted(group)))
    return result


def enclosed_regions(cells, connectivity):
    cells = set(cells)
    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
    r1, c1 = max(r for r, c in cells), max(c for r, c in cells)
    complement = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)} - cells
    return [region for region in components(complement, connectivity)
            if all(r0 < r < r1 and c0 < c < c1 for r, c in region)]


def plan(grid, hole_connectivity=4):
    _setting({"hole_connectivity": hole_connectivity})
    background, foreground = _validate(grid)
    source = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != background}
    groups = components(source, 4)
    owners = {p: i for i, cells in enumerate(groups) for p in cells}
    for (r, c), owner in owners.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (r + dr, c + dc) in owners and owners[r + dr, c + dc] != owner:
                    raise ValueError("distinct foreground components may not have diagonal contacts")
    records = []
    for cells in groups:
        four = enclosed_regions(cells, 4)
        if any(grid[r][c] != background for region in four for r, c in region):
            raise ValueError("nested foreground inside another component's cavity is outside this grammar")
        regions = four if hole_connectivity == 4 else enclosed_regions(cells, 8)
        holes = tuple(sorted(p for region in regions for p in region))
        records.append({"cells": cells, "hole_regions": regions, "holes": holes, "has_hole": bool(holes)})
    holes = {p for record in records for p in record["holes"]}
    holed_cells = {p for record in records if record["has_hole"] for p in record["cells"]}
    support = source | holes
    rim = {(r + dr, c + dc) for r, c in support for dr in (-1, 0, 1) for dc in (-1, 0, 1)
           if 0 <= r + dr < len(grid) and 0 <= c + dc < len(grid[0])} - support
    return {"background": background, "foreground": foreground, "objects": records,
            "source_cells": source, "holes": holes, "holed_cells": holed_cells, "support": support, "rim": rim}


def solve(grid, hole_connectivity=4):
    planned = plan(grid, hole_connectivity)
    output = [row[:] for row in grid]
    for r, c in planned["rim"]:
        output[r][c] = 2
    for r, c in planned["holed_cells"]:
        output[r][c] = 8
    for r, c in planned["holes"]:
        output[r][c] = 6
    return output


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


@lru_cache(maxsize=1)
def _templates():
    path = Path(__file__).with_name("scene_templates.py")
    spec = importlib.util.spec_from_file_location("topology_scene_templates", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _augment(grid, rng, avoid_roles=None):
    background, foreground = _validate(grid)
    if avoid_roles is None:
        new_background, new_foreground = rng.sample(INPUT_COLORS, 2)
    else:
        choices = [(bg, fg) for bg in INPUT_COLORS for fg in INPUT_COLORS
                   if bg != fg and bg != avoid_roles[0] and fg != avoid_roles[1]]
        new_background, new_foreground = rng.choice(choices)
    grid = [[new_background if v == background else new_foreground for v in row] for row in grid]
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    for _ in range(rng.randrange(4)):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def input_bank(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    demos, queries = _templates().input_templates()
    d, q = _rng(seed, "demonstrations"), _rng(seed, "queries")
    augmented = []
    for index, grid in enumerate(demos):
        avoid_roles = _validate(augmented[0]) if index == 1 else None
        augmented.append(_augment(grid, d, avoid_roles))
    demos = augmented
    queries = [_augment(g, q) for g in queries]
    q.shuffle(queries)
    return demos, queries


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"hole_connectivity": _rng(seed, "settings").choice(PARAMETERS["hole_connectivity"])}
    connectivity = _setting(settings)
    train, test = input_bank(seed)
    def pairs(grids):
        return [{"input": grid, "output": solve(grid, connectivity)} for grid in grids]
    return {"train": pairs(train[:demos]), "test": pairs(test[:queries]), "program_solution": program(settings)}
