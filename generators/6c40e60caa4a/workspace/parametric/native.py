"""Native parametric family for deepest versus all seeded frame interiors."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path


HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
SCOPES = ("deepest", "all_seeded")
_DEMO_INDICES = (1, 2, 3, 5, 6, 7)
_QUERY_INDICES = (9, 10, 11)


def _load_generator():
    path = HOME / "generator.py"
    name = "_frame_base_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BASE = _load_generator()


def _settings(settings) -> str:
    if type(settings) is not dict or set(settings) != {"frame_scope"}:
        raise ValueError("settings must contain exactly frame_scope")
    scope = settings["frame_scope"]
    if type(scope) is not str or scope not in SCOPES:
        raise ValueError(f"frame_scope must be one of {SCOPES}")
    return scope


def _seed(seed) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    return seed


def _count(name: str, value, lo: int, hi: int) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def program(settings) -> str:
    scope = _settings(settings)
    name = "canonical.rkt" if scope == "deepest" else "fill_all_seeded.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _draw_frame(grid: list[list[int]], box: tuple[int, int, int, int]) -> None:
    r0, c0, r1, c1 = box
    for c in range(c0, c1 + 1):
        grid[r0][c] = 1
        grid[r1][c] = 1
    for r in range(r0, r1 + 1):
        grid[r][c0] = 1
        grid[r][c1] = 1


def _large_scene(seed: int) -> list[list[int]]:
    rng = random.Random((seed ^ 0x6C40E60CAA4A) & ((1 << 64) - 1))
    grid = [[0] * 30 for _ in range(30)]
    shift = rng.randrange(2)
    outer = (1 + shift, 1, 18 + shift, 18)
    inner = (5 + shift, 5, 14 + shift, 14)
    single = (20, 20 - shift, 28, 28 - shift)
    for box in (outer, inner, single):
        _draw_frame(grid, box)
    grid[rng.randint(inner[0] + 1, inner[2] - 1)][rng.randint(inner[1] + 1, inner[3] - 1)] = 2
    grid[rng.randint(single[0] + 1, single[2] - 1)][rng.randint(single[1] + 1, single[3] - 1)] = 2
    return grid


def sample_inputs(seed: int, demos: int = 3, queries: int = 4):
    seed = _seed(seed)
    demos = _count("demos", demos, 2, 6)
    queries = _count("queries", queries, 1, 4)
    demo_bank = [
        _BASE.generate(seed, index, difficulty="medium" if pos % 2 else None)
        for pos, index in enumerate(_DEMO_INDICES)
    ]
    query_bank = [
        _BASE.generate(seed ^ 0x13579BDF, index, difficulty="medium" if pos % 2 else None)
        for pos, index in enumerate(_QUERY_INDICES)
    ] + [_large_scene(seed)]
    selected = demo_bank[:demos] + query_bank[:queries]
    if len({json.dumps(grid, separators=(",", ":")) for grid in selected}) != len(selected):
        raise RuntimeError("input sampler produced a duplicate visible grid")
    return copy.deepcopy(demo_bank[:demos]), copy.deepcopy(query_bank[:queries])


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[set[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while todo:
                rr, cc = todo.pop()
                cells.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append(cells)
    return result


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _inside(box: tuple[int, int, int, int], point: tuple[int, int]) -> bool:
    r0, c0, r1, c1 = box
    r, c = point
    return r0 < r < r1 and c0 < c < c1


def _strictly_contains(outer, inner) -> bool:
    return outer[0] < inner[0] and outer[1] < inner[1] and inner[2] < outer[2] and inner[3] < outer[3]


def _label(grid: list[list[int]], scope: str) -> list[list[int]]:
    frames = [_bbox(cells) for cells in _components(grid, 1)]
    seeds = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    seeded = [box for box in frames if any(_inside(box, point) for point in seeds)]
    selected = seeded
    if scope == "deepest":
        selected = [box for box in seeded if not any(box != other and _strictly_contains(box, other) for other in seeded)]
    output = copy.deepcopy(grid)
    for r0, c0, r1, c1 in selected:
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                output[r][c] = 3
    return output


def generate(seed, settings, demos=3, queries=4):
    scope = _settings(settings)
    train_inputs, test_inputs = sample_inputs(seed, demos=demos, queries=queries)
    return {
        "train": [{"input": grid, "output": _label(grid, scope)} for grid in train_inputs],
        "test": [{"input": grid, "output": _label(grid, scope)} for grid in test_inputs],
        "program_solution": program(settings),
    }
