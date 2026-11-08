"""Native matching-versus-opposite prototype family for eb150c0ba566."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import random
import sys
from typing import Any


TASK_ID = "eb150c0ba566"
POLICIES = ("matching", "opposite_shape")
DEMO_LIMIT = 6
QUERY_LIMIT = 4
_HOME = Path(__file__).resolve().parent
CANONICAL_PATH = _HOME / "canonical.rkt"
OPPOSITE_PATH = _HOME / "opposite_shape.rkt"
GENERATOR_PATH = _HOME.parents[1] / "generator.py"


_DEMO_SPECS = (
    (10, 10, 4),
    (11, 13, 6),
    (14, 16, 10),
    (16, 12, 8),
    (18, 18, 16),
    (20, 14, 12),
)
_QUERY_SPECS = (
    (9, 7, 2),
    (15, 20, 12),
    (24, 21, 30),
    (30, 30, 48),
)
_MASKS = (
    ((0, 1), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2)),
    ((0, 2), (1, 1), (1, 2), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 0)),
    ((0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 2), (1, 0), (1, 1), (1, 2), (2, 2)),
    ((0, 1), (1, 1), (2, 0), (2, 1), (2, 2)),
)


def _load_generator():
    name = "_eb150c0ba566_generator_" + hashlib.sha256(str(GENERATOR_PATH).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load production generator at {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_GENERATOR = _load_generator()


def _settings(value: Any) -> str:
    if not isinstance(value, dict) or set(value) != {"prototype_policy"}:
        raise ValueError("settings must name exactly prototype_policy")
    policy = value["prototype_policy"]
    if policy not in POLICIES:
        raise ValueError("prototype_policy must be matching or opposite_shape")
    return policy


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low},{high}]")
    return value


def program(settings: dict[str, str]) -> str:
    policy = _settings(settings)
    path = CANONICAL_PATH if policy == "matching" else OPPOSITE_PATH
    source = path.read_text(encoding="utf-8")
    if not source.startswith("(rule!"):
        raise ValueError(f"invalid Racket program resource: {path.name}")
    return source


def _seed_rng(seed: int, role: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{role}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _mask_grid(cells: tuple[tuple[int, int], ...], color: int) -> list[list[int]]:
    result = [[0, 0, 0] for _ in range(3)]
    for row, col in cells:
        result[row][col] = color
    return result


def _scene(seed: int, role: str, index: int, spec: tuple[int, int, int]) -> list[list[int]]:
    height, width, count = spec
    rng = _seed_rng(seed, role, index)
    mask_index = (seed * 5 + index * 3 + (0 if role == "demo" else 1)) % len(_MASKS)
    other_index = (mask_index + 1 + rng.randrange(len(_MASKS) - 1)) % len(_MASKS)
    if other_index == mask_index:
        other_index = (other_index + 1) % len(_MASKS)
    proto2 = _mask_grid(_MASKS[mask_index], 2)
    proto3 = _mask_grid(_MASKS[other_index], 3)
    if {tuple(map(tuple, proto2)), tuple(map(tuple, proto3))} == set():
        raise AssertionError("unreachable empty prototype set")

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for dr in range(3):
        for dc in range(3):
            grid[dr][dc] = proto2[dr][dc]
            grid[dr][4 + dc] = proto3[dr][dc]
        grid[dr][3] = 9
    for col in range(width):
        grid[3][col] = 9

    candidates = [
        (row, col)
        for row in range(4, height - 2, 3)
        for col in range(0, width - 2, 3)
    ]
    if count > len(candidates):
        raise ValueError(f"scene {height}x{width} cannot fit {count} stamps")
    rng.shuffle(candidates)
    positions = candidates[:count]
    colors = [2, 3] + [2 if i % 2 == 0 else 3 for i in range(max(0, count - 2))]
    rng.shuffle(colors)
    if set(colors) != {2, 3}:
        raise AssertionError("scene must include both seed colors")
    for (row, col), color in zip(positions, colors):
        grid[row][col] = color

    errors = _GENERATOR.self_check(grid)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def _prototype(grid: list[list[int]], color: int) -> list[list[int]]:
    left = 0 if color == 2 else 4
    return [row[left:left + 3] for row in grid[:3]]


def native_transform(grid: list[list[int]], policy: str) -> list[list[int]]:
    if policy not in POLICIES:
        raise ValueError("policy must be matching or opposite_shape")
    errors = _GENERATOR.self_check(grid)
    if errors:
        raise ValueError("input leaves production grammar: " + "; ".join(errors))
    height, width = len(grid), len(grid[0])
    output = [row[:] if row_index < 4 else [0] * width for row_index, row in enumerate(grid)]
    proto2 = _prototype(grid, 2)
    proto3 = _prototype(grid, 3)
    for row in range(4, height):
        for col in range(width):
            seed_color = grid[row][col]
            if seed_color not in (2, 3):
                continue
            shape_color = seed_color if policy == "matching" else 5 - seed_color
            mask = proto2 if shape_color == 2 else proto3
            for dr in range(3):
                for dc in range(3):
                    if mask[dr][dc] == shape_color:
                        output[row + dr][col + dc] = seed_color
    return output


def _pair(grid: list[list[int]], policy: str) -> dict[str, list[list[int]]]:
    return {"input": deepcopy(grid), "output": native_transform(grid, policy)}


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, DEMO_LIMIT)
    queries = _integer("queries", queries, 1, QUERY_LIMIT)
    policy = _settings(settings)

    demo_inputs = [_scene(seed, "demo", index, spec) for index, spec in enumerate(_DEMO_SPECS[:demos])]
    query_bank = [_scene(seed, "query", index, spec) for index, spec in enumerate(_QUERY_SPECS)]
    selected_queries = query_bank[:queries]
    all_inputs = demo_inputs + selected_queries
    if len({repr(grid) for grid in all_inputs}) != len(all_inputs):
        raise RuntimeError("episode inputs must be distinct")
    for grid in all_inputs:
        matching = native_transform(grid, "matching")
        opposite = native_transform(grid, "opposite_shape")
        if matching == opposite:
            raise RuntimeError("scene does not distinguish prototype policies")

    return {
        "train": [_pair(grid, policy) for grid in demo_inputs],
        "test": [_pair(grid, policy) for grid in selected_queries],
        "program_solution": program(settings),
    }
