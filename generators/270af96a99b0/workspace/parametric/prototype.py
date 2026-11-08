"""Task-local native parametric prototype for perimeter-tie ordering.

The input grammar is shared across settings.  Every scene contains equal-
perimeter objects with unequal occupied areas.  The canonical setting keeps the
selected source-position tie-break; the alternative uses smaller occupied area
only inside a true-perimeter tie.  Both then crop and horizontally pack the
resulting ordered component sequence.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any

_HERE = Path(__file__).resolve().parent
_TASK_HOME = _HERE.parents[1]
_GENERATOR_PATH = _TASK_HOME / "generator.py"
_SETTINGS = ("source_position", "smaller_area")


def _load(path: Path, label: str):
    name = "_parametric_270af96a99b0_" + label + "_" + hashlib.sha256(str(path).encode()).hexdigest()
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _oracle():
    return _load(_HERE / "oracle.py", "oracle")


def _generator():
    return _load(_GENERATOR_PATH, "generator")


def _tie_break(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"tie_break"}
        or type(settings["tie_break"]) is not str
        or settings["tie_break"] not in _SETTINGS
    ):
        raise ValueError("settings must contain only tie_break=source_position|smaller_area")
    return settings["tie_break"]


def _count(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _seed(value: Any) -> int:
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2**63-1")
    return value


def _u64(seed: int, *parts: object) -> int:
    payload = json.dumps([seed, *parts], sort_keys=True, separators=(",", ":")).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & (2**63 - 1)


def program(settings: Any) -> str:
    tie_break = _tie_break(settings)
    filename = "canonical.rkt" if tie_break == "source_position" else "smaller_area.rkt"
    return (_HERE / filename).read_text(encoding="utf-8")


def _generated_scene(
    seed: int,
    role: str,
    index: int,
    *,
    height: int,
    width: int,
    profile: str | None = None,
) -> list[list[int]]:
    profiles = ("p8_tie", "p10_tie", "p12_tie")
    palettes = ("low", "mixed", "high")
    if profile is None:
        profile = profiles[(_u64(seed, role, "profile", index) + index) % len(profiles)]
    elif profile not in profiles:
        raise ValueError(f"unsupported profile {profile!r}")
    palette = palettes[(_u64(seed, role, "palette", index) + 2 * index) % len(palettes)]
    difficulty = ("easy", "medium", "hard")[_u64(seed, role, "difficulty", index) % 3]
    sample_seed = _u64(seed, role, "sample", index)
    sample_index = int(_u64(seed, role, "index", index) % 100000) + 1
    return _generator().generate(
        sample_seed,
        sample_index,
        difficulty=difficulty,
        grid_h=height,
        grid_w=width,
        palette_kind=palette,
        shape_profile=profile,
    )


def _rect(height: int, width: int) -> tuple[tuple[int, int], ...]:
    return tuple((row, column) for row in range(height) for column in range(width))


def _normalize(shape: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    r0 = min(row for row, _ in shape)
    c0 = min(column for _, column in shape)
    return tuple(sorted((row - r0, column - c0) for row, column in shape))


def _flip(shape: tuple[tuple[int, int], ...], vertical: bool, horizontal: bool) -> tuple[tuple[int, int], ...]:
    max_row = max(row for row, _ in shape)
    max_column = max(column for _, column in shape)
    return _normalize(
        tuple(
            (
                max_row - row if vertical else row,
                max_column - column if horizontal else column,
            )
            for row, column in shape
        )
    )


def _large_scene(seed: int) -> list[list[int]]:
    rng = random.Random(_u64(seed, "large"))
    colors = rng.sample(range(1, 10), 4)
    tree9 = (
        (0, 0), (1, 0), (2, 0), (2, 1), (2, 2),
        (3, 2), (4, 2), (4, 3), (4, 4),
    )
    tree10 = (
        (0, 0), (1, 0), (2, 0), (3, 0), (3, 1),
        (3, 2), (4, 2), (5, 2), (5, 3), (5, 4),
    )
    shapes = [
        _rect(4, 6),
        _flip(tree9, bool(rng.getrandbits(1)), bool(rng.getrandbits(1))),
        _rect(5, 6),
        _flip(tree10, bool(rng.getrandbits(1)), bool(rng.getrandbits(1))),
    ]
    placements = ((0, 0), (1, 25), (19, 0), (24, 25))
    grid = [[0] * 30 for _ in range(30)]
    for shape, color, (top, left) in zip(shapes, colors, placements):
        for row, column in shape:
            grid[top + row][left + column] = color
    ref = _oracle()
    items = ref.components(grid)
    if [item.perimeter for item in items] != [20, 20, 22, 22]:
        raise AssertionError("large-scene perimeter construction drifted")
    if [item.area for item in items] != [24, 9, 30, 10]:
        raise AssertionError("large-scene area construction drifted")
    return grid


def _banks(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demo_sizes = ((8, 9), (9, 10), (10, 11), (11, 12), (12, 13), (14, 16))
    query_sizes = ((8, 11), (12, 15), (14, 16))
    profile_cycle = ("p8_tie", "p10_tie", "p12_tie")
    offset = _u64(seed, "demo-profile-offset") % len(profile_cycle)
    demos = [
        _generated_scene(
            seed,
            "demo",
            index,
            height=height,
            width=width,
            profile=profile_cycle[(offset + index) % len(profile_cycle)],
        )
        for index, (height, width) in enumerate(demo_sizes)
    ]
    queries = [
        _generated_scene(seed, "query", index, height=height, width=width)
        for index, (height, width) in enumerate(query_sizes)
    ] + [_large_scene(seed)]
    random.Random(_u64(seed, "query-order")).shuffle(queries)
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in [*demos, *queries]]
    if len(serialized) != len(set(serialized)):
        raise AssertionError("parametric input bank contains duplicates")
    ref = _oracle()
    for grid in [*demos, *queries]:
        if ref.solve(grid, "source_position") == ref.solve(grid, "smaller_area"):
            raise AssertionError("input does not expose the episode tie-break")
    return demos, queries


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _seed(seed)
    tie_break = _tie_break(settings)
    demos = _count("demos", demos, 2, 6)
    queries = _count("queries", queries, 1, 4)
    demo_bank, query_bank = _banks(seed)
    ref = _oracle()

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": grid, "output": ref.solve(grid, tie_break)}

    return {
        "train": [pair(grid) for grid in demo_bank[:demos]],
        "test": [pair(grid) for grid in query_bank[:queries]],
        "program_solution": program({"tie_break": tie_break}),
    }
