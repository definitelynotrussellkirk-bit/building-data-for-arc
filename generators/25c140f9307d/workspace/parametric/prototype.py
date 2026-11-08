"""Deterministic two-policy parametric family for 25c140f9307d.

The visible input grammar is shared by both settings.  The selected payload
policy changes only the second stage after a key has been matched and rotated:
``preserve`` stamps each oriented payload color at its own position, while
``swap`` exchanges the two oriented payload colors before stamping.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import random
import sys
from typing import Callable, Iterable

TASK_ID = "25c140f9307d"
POLICIES = ("preserve", "swap")
HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
GENERATOR_PATH = HOME / "generator.py"
RULES = {
    "preserve": HERE / "rules" / "canonical.rkt",
    "swap": HERE / "rules" / "swap_payloads.rkt",
}


def _load_generator():
    name = "_arc_parametric_generator_" + hashlib.sha256(
        str(GENERATOR_PATH).encode("utf-8")
    ).hexdigest()
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load production generator: {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _policy(settings: dict) -> str:
    if not isinstance(settings, dict) or set(settings) != {"payload_policy"}:
        raise ValueError("payload_policy settings must name exactly payload_policy")
    value = settings["payload_policy"]
    if type(value) is not str or value not in POLICIES:
        raise ValueError("payload_policy must be preserve or swap")
    return value


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def program(settings: dict) -> str:
    policy = _policy(settings)
    return RULES[policy].read_text(encoding="utf-8")


def _seed(base: int, slot: int, purpose: str) -> int:
    payload = f"25c140f9307d-parametric-v1:{base}:{slot}:{purpose}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & (2**63 - 1)


def _components(grid: list[list[int]], predicate: Callable[[int], bool], *, eight: bool) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if eight:
        steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for start_r in range(height):
        for start_c in range(width):
            start = (start_r, start_c)
            if start in seen or not predicate(grid[start_r][start_c]):
                continue
            stack = [start]
            seen.add(start)
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in steps:
                    nr, nc = r + dr, c + dc
                    candidate = (nr, nc)
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and candidate not in seen
                        and predicate(grid[nr][nc])
                    ):
                        seen.add(candidate)
                        stack.append(candidate)
            result.append(cells)
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = list(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _crop(grid: list[list[int]], cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    r0, c0, r1, c1 = _bbox(cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _orientations(grid: list[list[int]]) -> list[list[list[int]]]:
    cw = _rotate_cw(grid)
    half = _rotate_cw(cw)
    ccw = _rotate_cw(half)
    return [copy.deepcopy(grid), cw, half, ccw]


def _key_info(grid: list[list[int]]) -> dict:
    teeth: list[tuple[int, int]] = []
    payload: list[tuple[int, int]] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2:
                teeth.append((r, c))
            elif value != 0:
                payload.append((r, c))
    return {"grid": grid, "teeth": teeth, "payload": payload}


def solve(grid: list[list[int]], payload_policy: str) -> list[list[int]]:
    if payload_policy not in POLICIES:
        raise ValueError("payload_policy must be preserve or swap")
    objects = _components(grid, lambda value: value != 0, eight=True)
    objects.sort(key=lambda cells: -len(cells))
    if len(objects) < 2:
        raise ValueError("input needs a plate and detached keys")
    interior = _crop(grid, objects[0])
    holes = _components(interior, lambda value: value == 0, eight=True)
    oriented_keys = [
        _key_info(oriented)
        for key in objects[1:]
        for oriented in _orientations(_crop(grid, key))
    ]
    result = copy.deepcopy(interior)
    height, width = len(result), len(result[0])
    for hole in holes:
        hole_r = min(r for r, _ in hole)
        hole_c = min(c for _, c in hole)
        hit = None
        for candidate in oriented_keys:
            teeth = candidate["teeth"]
            payload = candidate["payload"]
            if len(teeth) != len(hole) or len(payload) != 2:
                continue
            dr = hole_r - min(r for r, _ in teeth)
            dc = hole_c - min(c for _, c in teeth)
            teeth_fit = all(
                0 <= r + dr < height
                and 0 <= c + dc < width
                and result[r + dr][c + dc] == 0
                for r, c in teeth
            )
            payload_fit = all(
                0 <= r + dr < height
                and 0 <= c + dc < width
                and result[r + dr][c + dc] == 2
                for r, c in payload
            )
            if teeth_fit and payload_fit:
                hit = (candidate, dr, dc)
                break
        if hit is None:
            continue
        candidate, dr, dc = hit
        key_grid = candidate["grid"]
        payload = candidate["payload"]
        swapped: dict[tuple[int, int], int] = {}
        if payload_policy == "swap":
            first, second = payload
            swapped[first] = key_grid[second[0]][second[1]]
            swapped[second] = key_grid[first[0]][first[1]]
        for key_r, row in enumerate(key_grid):
            for key_c, value in enumerate(row):
                target_r, target_c = key_r + dr, key_c + dc
                if not (0 <= target_r < height and 0 <= target_c < width):
                    continue
                if value == 2 and result[target_r][target_c] == 0:
                    result[target_r][target_c] = 2
                elif value not in (0, 2):
                    result[target_r][target_c] = (
                        swapped[(key_r, key_c)] if payload_policy == "swap" else value
                    )
    return result


def _stress_scene(scene_seed: int) -> list[list[int]]:
    generator = _load_generator()
    rng = random.Random(scene_seed)
    height = width = 30
    plate_h = plate_w = 22
    plate_r = plate_c = 1
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for r in range(plate_r, plate_r + plate_h):
        for c in range(plate_c, plate_c + plate_w):
            grid[r][c] = 2

    anchors = [(2, 2), (2, 17), (17, 2), (17, 17)]
    templates = list(generator._KEY_TEMPLATES)
    rng.shuffle(anchors)
    rng.shuffle(templates)
    selected = []
    for index in range(4):
        _name, teeth, body = templates[index]
        hole_teeth = generator._rotate_cells(teeth, rng.randrange(4))
        key_turns = rng.randrange(4)
        key_teeth = generator._rotate_cells(teeth, key_turns)
        key_body = generator._rotate_cells(body, key_turns)
        anchor_r, anchor_c = anchors[index]
        for dr, dc in hole_teeth:
            grid[plate_r + anchor_r + dr][plate_c + anchor_c + dc] = 0
        selected.append((key_teeth, key_body))

    payload_colors = rng.sample([1, 3, 4, 5, 6, 7, 8, 9], 8)
    key_col = 27
    for index, (teeth, body) in enumerate(selected):
        key_row = 1 + 7 * index
        for dr, dc in teeth:
            grid[key_row + dr][key_col + dc] = 2
        for payload_index, (dr, dc) in enumerate(sorted(body)):
            grid[key_row + dr][key_col + dc] = payload_colors[2 * index + payload_index]
    return grid


_ORDINARY = (
    (9, 2),
    (14, 4),
    (11, 3),
    (9, 4),
    (14, 2),
    (12, 3),
    (10, 2),
    (13, 4),
    (11, 2),
)


def _inputs(seed: int, count: int) -> list[list[list[int]]]:
    generator = _load_generator()
    result: list[list[list[int]]] = []
    ordinary_index = 0
    for slot in range(count):
        scene_seed = _seed(seed, slot, "input")
        if slot == 3:
            grid = _stress_scene(scene_seed)
        else:
            size, n_keys = _ORDINARY[ordinary_index % len(_ORDINARY)]
            ordinary_index += 1
            grid = generator.generate(
                scene_seed,
                slot,
                rect_size=size,
                n_keys=n_keys,
            )
        result.append(copy.deepcopy(grid))
    fingerprints = {
        hashlib.sha256(repr(grid).encode("utf-8")).hexdigest() for grid in result
    }
    if len(fingerprints) != len(result):
        raise RuntimeError("deterministic input schedule produced a duplicate")
    return result


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 4, 4)
    policy = _policy(settings)
    pairs = [
        {"input": copy.deepcopy(grid), "output": solve(grid, policy)}
        for grid in _inputs(seed, demos + queries)
    ]
    return {
        "train": copy.deepcopy(pairs[:demos]),
        "test": copy.deepcopy(pairs[demos:]),
        "program_solution": program(settings),
    }
