"""Native parametric family for flood-fill followed by optional room outlining.

The default setting is the exact canonical Racket program.  The alternate first
performs that canonical flood, then uses the filled result to identify the
largest chamber and recolors only the wall cells touching that chamber with its
seed color.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Callable

PARAMETER_NAME = "finish"
SETTINGS = ("flood", "outline_largest")
DEFAULT_SETTINGS = {PARAMETER_NAME: "flood"}
DEMO_SIZES = ((9, 12), (11, 15), (13, 18), (15, 19), (17, 20), (18, 21))
QUERY_SIZES = ((14, 16), (20, 23), (26, 28), (30, 30))

CANONICAL_PROGRAM = """(rule!
  (let ((seeds (filter (lambda (p)
                         (let ((v (at g (first p) (second p))))
                           (or (= v 1) (= v 2) (= v 3) (= v 4))))
                       (grid-positions g))))
    (foldl (lambda (seed out)
             (let* ((color (at g (first seed) (second seed)))
                    (region (connected-region g (first seed) (second seed) (lambda (r c v) (or (= v 0) (= v color))))))
               (foldl (lambda (p acc)
                        (if (= (at g (first p) (second p)) 0)
                            (set-cell acc (first p) (second p) color)
                            acc))
                      out region)))
           g seeds)))"""

OUTLINE_LARGEST_PROGRAM = """(rule!
  (let* ((seeds (filter (lambda (p)
                          (let ((v (at g (first p) (second p))))
                            (or (= v 1) (= v 2) (= v 3) (= v 4))))
                        (grid-positions g)))
         (filled
           (foldl (lambda (seed out)
                    (let* ((color (at g (first seed) (second seed)))
                           (region (connected-region g (first seed) (second seed)
                                     (lambda (r c v) (or (= v 0) (= v color))))))
                      (foldl (lambda (p acc)
                               (if (= (at g (first p) (second p)) 0)
                                   (set-cell acc (first p) (second p) color)
                                   acc))
                             out region)))
                  g seeds))
         (seed-colors
           (remove-duplicates
             (map (lambda (seed) (at g (first seed) (second seed))) seeds)))
         (largest-color
           (pick-max seed-colors (lambda (color) (count-color filled color))))
         (boundary
           (filter (lambda (p)
                     (let ((r (first p)) (c (second p)))
                       (and (> (at g r c) 4)
                            (> (neighbor-count-4 filled r c largest-color) 0))))
                   (grid-positions g))))
    (recolor-cells filled boundary largest-color)))"""


def _load_generator():
    path = Path(__file__).resolve().parents[2] / "generator.py"
    name = "_task_75422b6b0a4d_base_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load base generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings) -> str:
    if not isinstance(settings, dict) or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain exactly {PARAMETER_NAME!r}")
    value = settings[PARAMETER_NAME]
    if value not in SETTINGS:
        raise ValueError(f"unsupported {PARAMETER_NAME}: {value!r}")
    return value


def program(settings) -> str:
    value = _setting(settings)
    return CANONICAL_PROGRAM if value == "flood" else OUTLINE_LARGEST_PROGRAM


def _rng(seed: int, lane: str, index: int, attempt: int = 0) -> random.Random:
    payload = f"75422b6b0a4d-parametric-v1|{seed}|{lane}|{index}|{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _wall_color(grid) -> int:
    colors = sorted({value for row in grid for value in row if value >= 5})
    if len(colors) != 1:
        raise ValueError(f"expected one wall color, found {colors}")
    return colors[0]


def room_records(grid) -> list[dict]:
    wall = _wall_color(grid)
    records = []
    for cells in GEN._open_components(grid, wall):
        ordered = sorted(cells)
        seeds = [(row, col) for row, col in ordered if grid[row][col] in (1, 2, 3, 4)]
        if len(seeds) != 1:
            raise ValueError(f"each chamber needs exactly one seed, found {len(seeds)}")
        seed = seeds[0]
        rows = [point[0] for point in ordered]
        cols = [point[1] for point in ordered]
        records.append(
            {
                "cells": ordered,
                "seed": seed,
                "color": grid[seed[0]][seed[1]],
                "area": len(ordered),
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            }
        )
    if not 2 <= len(records) <= 4:
        raise ValueError(f"expected 2..4 chambers, found {len(records)}")
    return records


def selected_room(grid, selector: str) -> dict:
    rooms = room_records(grid)
    if selector == "largest":
        return max(rooms, key=lambda room: room["area"])
    if selector == "smallest":
        return min(rooms, key=lambda room: room["area"])
    if selector == "top_left":
        return rooms[0]
    if selector == "color_one":
        return next(room for room in rooms if room["color"] == 1)
    raise ValueError(f"unknown room selector: {selector}")


def boundary_cells(grid, cells, *, outer: bool) -> list[tuple[int, int]]:
    height = len(grid)
    width = len(grid[0])
    room = {tuple(point) for point in cells}
    wall = _wall_color(grid)
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != wall:
                continue
            if not outer and (row in (0, height - 1) or col in (0, width - 1)):
                continue
            if any(point in room for point in GEN._neighbors((row, col), height, width)):
                result.append((row, col))
    return result


def _paint(grid, cells, color: int):
    output = deepcopy(grid)
    for row, col in cells:
        output[row][col] = color
    return output


def _outline_selector(grid, selector: str, *, outer: bool = True):
    flooded = GEN.rule_mirror(grid)
    room = selected_room(grid, selector)
    return _paint(flooded, boundary_cells(grid, room["cells"], outer=outer), room["color"])


def _outline_all_walls(grid):
    flooded = GEN.rule_mirror(grid)
    room = selected_room(grid, "largest")
    wall = _wall_color(grid)
    cells = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == wall
    ]
    return _paint(flooded, cells, room["color"])


def _outline_seed_touch_only(grid):
    flooded = GEN.rule_mirror(grid)
    room = selected_room(grid, "largest")
    row, col = room["seed"]
    wall = _wall_color(grid)
    cells = [
        point
        for point in GEN._neighbors((row, col), len(grid), len(grid[0]))
        if grid[point[0]][point[1]] == wall
    ]
    return _paint(flooded, cells, room["color"])


def transform(grid, setting: str):
    if setting == "flood":
        return GEN.rule_mirror(grid)
    if setting == "outline_largest":
        return _outline_selector(grid, "largest", outer=True)
    raise ValueError(f"unsupported setting: {setting!r}")


SHORTCUTS: dict[str, Callable] = {
    "outline_smallest": lambda grid: _outline_selector(grid, "smallest", outer=True),
    "outline_top_left": lambda grid: _outline_selector(grid, "top_left", outer=True),
    "outline_color_one": lambda grid: _outline_selector(grid, "color_one", outer=True),
    "outline_all_walls": _outline_all_walls,
    "outline_interior_only": lambda grid: _outline_selector(grid, "largest", outer=False),
    "outline_seed_touch_only": _outline_seed_touch_only,
}


def finite_program_survivors(train) -> list[str]:
    survivors = []
    for setting in SETTINGS:
        if all(transform(pair["input"], setting) == pair["output"] for pair in train):
            survivors.append(setting)
    return survivors


def audit_shortcuts(train, *, selected: str) -> list[dict]:
    if selected not in SETTINGS:
        raise ValueError(f"unsupported selected setting: {selected!r}")
    rivals: dict[str, Callable] = {
        setting: (lambda grid, value=setting: transform(grid, value))
        for setting in SETTINGS
        if setting != selected
    }
    rivals.update(SHORTCUTS)
    reports = []
    for name, rival in rivals.items():
        mismatches = [
            index
            for index, pair in enumerate(train)
            if rival(pair["input"]) != pair["output"]
        ]
        reports.append(
            {
                "rival": name,
                "refuted": bool(mismatches),
                "mismatching_demo_indices": mismatches,
            }
        )
    return reports


def _candidate(seed: int, lane: str, slot: int, height: int, width: int):
    for attempt in range(512):
        geometry_rng = _rng(seed, lane + "-geometry", slot, attempt)
        n_rooms = 3 + ((slot + attempt) % 2)
        orientation = "horizontal" if (slot + attempt) % 2 else "vertical"
        wall_color = 5 + ((seed + slot + attempt) % 5)
        try:
            grid = GEN._partition_grid(
                height,
                width,
                wall_color,
                n_rooms,
                irregular=True,
                orientation=orientation,
                rng=geometry_rng,
            )
        except RuntimeError:
            continue
        components = GEN._open_components(grid, wall_color)
        areas = [len(component) for component in components]
        largest_area = max(areas)
        if areas.count(largest_area) != 1:
            continue
        largest_index = areas.index(largest_area)
        if largest_index == 0:
            continue

        colors = list(range(1, len(components) + 1))
        color_rng = _rng(seed, lane + "-colors", slot, attempt)
        color_rng.shuffle(colors)
        if colors[largest_index] == 1:
            swap = next(index for index, color in enumerate(colors) if color != 1)
            colors[largest_index], colors[swap] = colors[swap], colors[largest_index]
        placement_rng = _rng(seed, lane + "-seeds", slot, attempt)
        for component, color in zip(components, colors):
            row, col = placement_rng.choice(sorted(component))
            grid[row][col] = color

        records = room_records(grid)
        chosen = records[largest_index]
        boundary = set(boundary_cells(grid, chosen["cells"], outer=True))
        interior = set(boundary_cells(grid, chosen["cells"], outer=False))
        all_walls = {
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == wall_color
        }
        seed_row, seed_col = chosen["seed"]
        seed_touch = {
            point
            for point in GEN._neighbors((seed_row, seed_col), height, width)
            if grid[point[0]][point[1]] == wall_color
        }
        if (
            not boundary
            or boundary == all_walls
            or boundary == interior
            or not seed_touch
            or boundary == seed_touch
            or chosen["color"] == 1
            or chosen == records[0]
        ):
            continue
        return grid
    raise RuntimeError(
        f"could not construct a decisive {lane} scene {slot} at {height}x{width}"
    )


def _pairs(seed: int, setting: str, lane: str, sizes, count: int):
    result = []
    for slot, (height, width) in enumerate(sizes[:count]):
        grid = _candidate(seed, lane, slot, height, width)
        result.append({"input": grid, "output": transform(grid, setting)})
    return result


def generate(seed, settings, demos, queries):
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    setting = _setting(settings)
    train = _pairs(seed, setting, "demo", DEMO_SIZES, demos)
    test = _pairs(seed, setting, "query", QUERY_SIZES, queries)
    inputs = [_digest(pair["input"]) for pair in train + test]
    if len(inputs) != len(set(inputs)):
        raise RuntimeError("sampler produced duplicate demonstration/query inputs")
    if finite_program_survivors(train) != [setting]:
        raise RuntimeError("demonstrations do not identify the selected finite setting")
    findings = audit_shortcuts(train, selected=setting)
    if any(not item["refuted"] for item in findings):
        raise RuntimeError("demonstrations leave a declared shortcut unrefuted")
    return {
        "train": train,
        "test": test,
        "program_solution": program({PARAMETER_NAME: setting}),
    }


def _digest(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
