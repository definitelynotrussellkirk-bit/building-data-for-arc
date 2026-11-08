"""Source-bound parametric family for stacked-panel occupancy XOR.

The input sampler is independent of the hidden setting.  Stage A computes the
canonical 4xW XOR occupancy mask.  Stage B either emits the whole mask (the
byte-exact canonical default) or retains only its largest 4-connected
component.  ``top-largest.rkt`` is a causal counterfactual which changes Stage
A to top-panel occupancy while keeping the same Stage-B component selector.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable, Sequence

TASK_ID = "08eaba8254b2"
HERE = Path(__file__).resolve().parent
MODES = ("xor_mask", "largest_xor_component")
DEMO_WIDTHS = (8, 14, 11, 17, 21, 27)
QUERY_WIDTHS = (3, 12, 23, 30)
Position = tuple[int, int]
Component = tuple[Position, ...]


def _integer(value: Any, label: str, minimum: int | None = None, maximum: int | None = None) -> int:
    if type(value) is not int:
        raise ValueError(f"{label} must be an exact integer")
    if minimum is not None and value < minimum or maximum is not None and value > maximum:
        raise ValueError(f"{label} must be in {minimum}..{maximum}")
    return value


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"output_mode"}:
        raise ValueError("settings must contain exactly output_mode")
    value = settings["output_mode"]
    if type(value) is not str or value not in MODES:
        raise ValueError("output_mode must be xor_mask or largest_xor_component")
    return value


def _grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or len(grid) != 9:
        raise ValueError("grid must have exactly 9 rows")
    if type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 3..30 columns")
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
    mode = _setting(settings)
    name = "canonical.rkt" if mode == "xor_mask" else "largest.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def counterfactual_program(selector: str) -> str:
    if selector != "largest_top_component":
        raise ValueError("counterfactual selector must be largest_top_component")
    return (HERE / "top-largest.rkt").read_text(encoding="utf-8")


def xor_cells(grid: Sequence[Sequence[int]]) -> tuple[Position, ...]:
    _grid(grid)
    return tuple(
        (r, c)
        for r in range(4)
        for c in range(len(grid[0]))
        if (grid[r][c] == 0) != (grid[r + 5][c] == 0)
    )


def top_cells(grid: Sequence[Sequence[int]]) -> tuple[Position, ...]:
    _grid(grid)
    return tuple(
        (r, c)
        for r in range(4)
        for c in range(len(grid[0]))
        if grid[r][c] != 0
    )


def components(cells: Iterable[Position]) -> tuple[Component, ...]:
    """Return deterministic 4-connected components of a cell set."""
    remaining = set(cells)
    found: list[Component] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        found.append(tuple(sorted(component)))
    return tuple(sorted(found, key=lambda component: (-len(component), component)))


def _largest_cells(cells: Iterable[Position]) -> set[Position]:
    found = components(cells)
    if not found:
        return set()
    maximum = len(found[0])
    return {cell for component in found if len(component) == maximum for cell in component}


def transform_with_selector(grid: list[list[int]], selector: str) -> list[list[int]]:
    width = len(_grid(grid)[0])
    if selector == "xor_mask":
        selected = set(xor_cells(grid))
    elif selector == "largest_xor_component":
        selected = _largest_cells(xor_cells(grid))
    elif selector == "largest_top_component":
        selected = _largest_cells(top_cells(grid))
    else:
        raise ValueError("unknown selector")
    return [[3 if (r, c) in selected else 0 for c in range(width)] for r in range(4)]


def transform(grid: list[list[int]], settings: Any) -> list[list[int]]:
    return transform_with_selector(grid, _setting(settings))


def _rng(seed: int, stream: str, index: int, attempt: int) -> random.Random:
    payload = json.dumps([seed, stream, index, attempt], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _unique_largest(found: Sequence[Component]) -> bool:
    return len(found) >= 2 and len(found[0]) > len(found[1])


def _build_grid(width: int, xor: set[Position], top: set[Position], rng: random.Random) -> list[list[int]]:
    top_color, bottom_color, separator_color = rng.sample(range(1, 10), 3)
    bottom = top.symmetric_difference(xor)
    grid = [[0 for _ in range(width)] for _ in range(9)]
    grid[4] = [separator_color for _ in range(width)]
    for r, c in top:
        grid[r][c] = top_color
    for r, c in bottom:
        grid[r + 5][c] = bottom_color
    return grid


def sample_input(seed: int, stream: str, index: int, width: int) -> list[list[int]]:
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0)
    _integer(width, "width", 3, 30)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be a nonempty string")

    universe = {(r, c) for r in range(4) for c in range(width)}
    minimum_xor = max(4, min(12, width // 2 + 3))
    for attempt in range(4096):
        rng = _rng(seed, stream, index, attempt)
        xor_probability = 0.19 + 0.15 * rng.random()
        xor = {cell for cell in universe if rng.random() < xor_probability}
        if not minimum_xor <= len(xor) <= len(universe) - 2:
            continue
        xor_components = components(xor)
        if not _unique_largest(xor_components):
            continue
        if width >= 20 and (len(xor_components) < 3 or len(xor_components[0]) < 4):
            continue
        if width >= 12:
            columns = {c for _, c in xor}
            if min(columns) > 1 or max(columns) < width - 2:
                continue

        top_probability = 0.34 + 0.28 * rng.random()
        top = {cell for cell in universe if rng.random() < top_probability}
        bottom = top.symmetric_difference(xor)
        if not top or top == universe or not bottom or bottom == universe:
            continue
        non_xor = universe - xor
        if not (top & non_xor) or not (non_xor - top):
            continue
        top_components = components(top)
        if not top_components or (len(top_components) > 1 and len(top_components[0]) == len(top_components[1])):
            continue
        if _largest_cells(top) == _largest_cells(xor):
            continue

        grid = _build_grid(width, xor, top, rng)
        if transform_with_selector(grid, "xor_mask") == transform_with_selector(grid, "largest_xor_component"):
            continue
        if transform_with_selector(grid, "largest_top_component") == transform_with_selector(grid, "largest_xor_component"):
            continue
        return grid
    raise RuntimeError(f"could not construct a distinctive 9x{width} stacked-panel scene")


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    _setting(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    result: dict[str, Any] = {
        "train": [],
        "test": [],
        "program_solution": program(settings),
        "settings": dict(settings),
        "seed": seed,
        "prototype": True,
    }
    seen: set[str] = set()
    for split, widths in (("train", DEMO_WIDTHS[:demos]), ("test", QUERY_WIDTHS[:queries])):
        for index, width in enumerate(widths):
            grid = sample_input(seed, split, index, width)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise RuntimeError("deterministic sampler produced duplicate inputs")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result
