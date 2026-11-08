"""Source-bound parametric family for stacked-panel occupancy XOR.

The input sampler is independent of the hidden setting. Stage A computes the
canonical 4xW XOR occupancy mask. Stage B either emits the whole mask (the
byte-exact canonical default) or retains only its largest 4-connected
component. The first two demonstrations are selected jointly so simple
position, panel-copy, and whole-mask shortcuts cannot fit the visible lesson.
``top-largest.rkt`` remains the protected wrong-intermediate counterfactual.
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
TEACHING_SELECTORS = (
    "xor_mask",
    "largest_xor_component",
    "largest_top_component",
    "largest_bottom_component",
    "first_xor_component",
    "last_xor_component",
    "topmost_xor_component",
    "bottommost_xor_component",
    "leftmost_xor_component",
    "rightmost_xor_component",
)
_TEACHING_VARIANTS = 24


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


def bottom_cells(grid: Sequence[Sequence[int]]) -> tuple[Position, ...]:
    _grid(grid)
    return tuple(
        (r, c)
        for r in range(4)
        for c in range(len(grid[0]))
        if grid[r + 5][c] != 0
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


def _one_component(cells: Iterable[Position], selector: str) -> set[Position]:
    found = list(components(cells))
    if not found:
        return set()
    if selector == "first_xor_component":
        chosen = min(found)
    elif selector == "last_xor_component":
        chosen = max(found)
    elif selector == "topmost_xor_component":
        chosen = min(found, key=lambda part: (min(r for r, _ in part), min(c for _, c in part), part))
    elif selector == "bottommost_xor_component":
        chosen = max(found, key=lambda part: (max(r for r, _ in part), max(c for _, c in part), part))
    elif selector == "leftmost_xor_component":
        chosen = min(found, key=lambda part: (min(c for _, c in part), min(r for r, _ in part), part))
    elif selector == "rightmost_xor_component":
        chosen = max(found, key=lambda part: (max(c for _, c in part), max(r for r, _ in part), part))
    else:
        raise ValueError("unknown component selector")
    return set(chosen)


def transform_with_selector(grid: list[list[int]], selector: str) -> list[list[int]]:
    width = len(_grid(grid)[0])
    if selector == "xor_mask":
        selected = set(xor_cells(grid))
    elif selector == "largest_xor_component":
        selected = _largest_cells(xor_cells(grid))
    elif selector == "largest_top_component":
        selected = _largest_cells(top_cells(grid))
    elif selector == "largest_bottom_component":
        selected = _largest_cells(bottom_cells(grid))
    elif selector in {
        "first_xor_component",
        "last_xor_component",
        "topmost_xor_component",
        "bottommost_xor_component",
        "leftmost_xor_component",
        "rightmost_xor_component",
    }:
        selected = _one_component(xor_cells(grid), selector)
    else:
        raise ValueError("unknown selector")
    return [[3 if (r, c) in selected else 0 for c in range(width)] for r in range(4)]


def transform(grid: list[list[int]], settings: Any) -> list[list[int]]:
    return transform_with_selector(grid, _setting(settings))


def teaching_certificate(train: Any, settings: Any) -> dict[str, Any]:
    """Fit a finite named shortcut family using demonstrations only."""
    selected = _setting(settings)
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("teaching requires 2..6 demonstrations")
    for pair in train:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("each teaching pair needs input and output")
        _grid(pair["input"])
        output = pair["output"]
        if (
            type(output) is not list
            or len(output) != 4
            or any(type(row) is not list or len(row) != len(pair["input"][0]) for row in output)
        ):
            raise ValueError("teaching outputs must be rectangular 4xW grids")

    survivors: list[str] = []
    rejected: dict[str, int] = {}
    for selector in TEACHING_SELECTORS:
        mismatches = [
            index
            for index, pair in enumerate(train)
            if transform_with_selector(pair["input"], selector) != pair["output"]
        ]
        if mismatches:
            rejected[selector] = mismatches[0]
        else:
            survivors.append(selector)
    return {
        "schema": "08eaba8254b2-finite-teaching-certificate-v1",
        "fit_scope": "demonstrations_only",
        "selected": selected,
        "survivors": survivors,
        "declared_shortcuts": list(TEACHING_SELECTORS),
        "rejected_by_demonstration": rejected,
        "limits": "Finite named shortcut family only; not uniqueness over arbitrary programs.",
    }


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
        if not top_components or (
            len(top_components) > 1 and len(top_components[0]) == len(top_components[1])
        ):
            continue
        if _largest_cells(top) == _largest_cells(xor):
            continue

        grid = _build_grid(width, xor, top, rng)
        if transform_with_selector(grid, "xor_mask") == transform_with_selector(
            grid, "largest_xor_component"
        ):
            continue
        if transform_with_selector(grid, "largest_top_component") == transform_with_selector(
            grid, "largest_xor_component"
        ):
            continue
        return grid
    raise RuntimeError(f"could not construct a distinctive 9x{width} stacked-panel scene")


def _teaching_stream(variant: int) -> str:
    return "train" if variant == 0 else f"train-teaching-{variant}"


def _fitting_selectors(grid: list[list[int]], selected: str) -> set[str]:
    expected = transform_with_selector(grid, selected)
    return {
        selector
        for selector in TEACHING_SELECTORS
        if transform_with_selector(grid, selector) == expected
    }


def _teaching_demo_inputs(seed: int) -> list[list[list[int]]]:
    first_pool: list[list[list[int]]] = []
    second_pool: list[list[list[int]]] = []
    first_fits: list[set[str]] = []
    second_fits: list[set[str]] = []
    for variant in range(_TEACHING_VARIANTS):
        stream = _teaching_stream(variant)
        first = sample_input(seed, stream, 0, DEMO_WIDTHS[0])
        first_pool.append(first)
        first_fits.append(_fitting_selectors(first, "largest_xor_component"))
        second = sample_input(seed, stream, 1, DEMO_WIDTHS[1])
        second_pool.append(second)
        second_fits.append(_fitting_selectors(second, "largest_xor_component"))

        for first_index, fits in enumerate(first_fits):
            if fits & second_fits[-1] == {"largest_xor_component"}:
                return [first_pool[first_index], second]
        for second_index, fits in enumerate(second_fits[:-1]):
            if first_fits[-1] & fits == {"largest_xor_component"}:
                return [first, second_pool[second_index]]
    raise RuntimeError("could not construct two demonstrations that reject declared shortcuts")


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    selected = _setting(settings)
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
    teaching_inputs = _teaching_demo_inputs(seed)
    for index, width in enumerate(DEMO_WIDTHS[:demos]):
        grid = (
            teaching_inputs[index]
            if index < 2
            else sample_input(seed, "train", index, width)
        )
        key = json.dumps(grid, separators=(",", ":"))
        if key in seen:
            raise RuntimeError("deterministic sampler produced duplicate inputs")
        seen.add(key)
        result["train"].append({"input": grid, "output": transform_with_selector(grid, selected)})
    for index, width in enumerate(QUERY_WIDTHS[:queries]):
        grid = sample_input(seed, "test", index, width)
        key = json.dumps(grid, separators=(",", ":"))
        if key in seen:
            raise RuntimeError("deterministic sampler produced duplicate inputs")
        seen.add(key)
        result["test"].append({"input": grid, "output": transform_with_selector(grid, selected)})

    certificate = teaching_certificate(result["train"], settings)
    if certificate["survivors"] != [selected]:
        raise RuntimeError(
            "minimum lesson did not uniquely identify selected mode: "
            + repr(certificate["survivors"])
        )
    result["certificate"] = certificate
    return result
