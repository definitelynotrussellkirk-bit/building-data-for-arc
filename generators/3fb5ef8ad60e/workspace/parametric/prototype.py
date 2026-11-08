"""Parametric divider reference for the colored-block quadrant summary.

``block_midrange`` is the byte-exact canonical rule: colored block centers
choose their own row/column midrange divider. ``frame_midpoint`` instead uses
the cyan frame's midpoint. Both settings first detect the same input blocks and
then consume an input-derived divider to place their colors in a 2x2 summary.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "3fb5ef8ad60e"
HERE = Path(__file__).resolve().parent
DIVIDER_REFERENCES = ("block_midrange", "frame_midpoint")
SETTINGS = tuple({"divider_reference": value} for value in DIVIDER_REFERENCES)
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SPECS = (
    (14, 15, 1, 1, 2, 2),
    (16, 14, 2, 1, 1, 2),
    (18, 20, 1, 3, 2, 1),
    (20, 18, 3, 1, 1, 3),
    (22, 24, 2, 4, 2, 1),
    (26, 23, 4, 2, 1, 2),
    (15, 19, 1, 2, 1, 3),
    (21, 25, 3, 1, 2, 2),
    (27, 28, 2, 5, 1, 2),
    (30, 30, 3, 2, 2, 4),
)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _reference(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"divider_reference"}
        or type(settings["divider_reference"]) is not str
        or settings["divider_reference"] not in DIVIDER_REFERENCES
    ):
        raise ValueError(
            "settings must contain only divider_reference='block_midrange' or 'frame_midpoint'"
        )
    return settings["divider_reference"]


def program(settings: Any) -> str:
    reference = _reference(settings)
    filename = "canonical.rkt" if reference == "block_midrange" else "frame_midpoint.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not 10 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("input must be a 10..30 rectangular list grid")
    width = len(grid[0])
    if not 10 <= width <= 30:
        raise ValueError("input must be a 10..30 rectangular list grid")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("input must use exact integer ARC colors")
    return len(grid), width


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color in (0, 8) or (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while todo:
                current = todo.pop()
                cells.append(current)
                for dr, dc in _DIRS4:
                    neighbor = (current[0] + dr, current[1] + dc)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        todo.append(neighbor)
            cells.sort()
            result.append({"color": color, "cells": cells})
    result.sort(key=lambda item: item["cells"][0])
    return result


def _quadrant(center: tuple[int, int], divider: tuple[int, int]) -> tuple[int, int]:
    return (0 if center[0] <= divider[0] else 1, 0 if center[1] <= divider[1] else 1)


def render_with_divider(blocks: Any, divider: Any) -> list[list[int]]:
    if (
        type(divider) not in (list, tuple)
        or len(divider) != 2
        or any(type(value) is not int for value in divider)
    ):
        raise ValueError("divider must be an exact integer row/column pair")
    output = [[0, 0], [0, 0]]
    occupied = set()
    for block in blocks:
        color = block["color"]
        center = tuple(block["center"])
        cell = _quadrant(center, (divider[0], divider[1]))
        if cell in occupied:
            raise ValueError("divider maps multiple blocks to one output cell")
        occupied.add(cell)
        output[cell[0]][cell[1]] = color
    return output


def _missing(quadrants: list[tuple[int, int]]) -> int:
    all_cells = [(0, 0), (0, 1), (1, 0), (1, 1)]
    missing = [index for index, cell in enumerate(all_cells) if cell not in quadrants]
    if len(missing) != 1:
        raise ValueError("expected exactly one missing summary quadrant")
    return missing[0]


def analyze(grid: Any) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    frame_cells = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 8]
    if not frame_cells:
        raise ValueError("input needs a cyan frame")
    r0 = min(r for r, _ in frame_cells)
    r1 = max(r for r, _ in frame_cells)
    c0 = min(c for _, c in frame_cells)
    c1 = max(c for _, c in frame_cells)
    if r1 - r0 + 1 < 10 or c1 - c0 + 1 < 10:
        raise ValueError("cyan frame must be at least 10x10")
    for r in range(height):
        for c in range(width):
            inside = r0 <= r <= r1 and c0 <= c <= c1
            if not inside and grid[r][c] != 0:
                raise ValueError("all nonzero cells must lie inside the cyan frame")
            if inside and grid[r][c] == 0:
                raise ValueError("cyan frame interior may only be replaced by colored blocks")

    components = _components(grid)
    if len(components) != 3:
        raise ValueError("input needs exactly three colored blocks")
    colors = [item["color"] for item in components]
    if len(colors) != len(set(colors)):
        raise ValueError("colored blocks must use distinct colors")
    blocks = []
    for item in components:
        cells = item["cells"]
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        br0, br1, bc0, bc1 = min(rows), max(rows), min(cols), max(cols)
        if len(cells) != 4 or br1 - br0 != 1 or bc1 - bc0 != 1 or set(cells) != {
            (br0, bc0), (br0, bc1), (br1, bc0), (br1, bc1)
        }:
            raise ValueError("every colored component must be a solid 2x2 block")
        if not (r0 < br0 and br1 < r1 and c0 < bc0 and bc1 < c1):
            raise ValueError("colored blocks must sit clear of the frame border")
        center = (sum(rows) // len(rows), sum(cols) // len(cols))
        blocks.append({"color": item["color"], "cells": cells, "center": center})

    centers = [block["center"] for block in blocks]
    block_divider = (
        (min(r for r, _ in centers) + max(r for r, _ in centers)) // 2,
        (min(c for _, c in centers) + max(c for _, c in centers)) // 2,
    )
    frame_divider = ((r0 + r1) // 2, (c0 + c1) // 2)
    block_quadrants = [_quadrant(center, block_divider) for center in centers]
    frame_quadrants = [_quadrant(center, frame_divider) for center in centers]
    if len(set(block_quadrants)) != 3 or len(set(frame_quadrants)) != 3:
        raise ValueError("each admitted divider must place blocks in distinct summary cells")
    block_output = render_with_divider(blocks, block_divider)
    frame_output = render_with_divider(blocks, frame_divider)
    if block_output == frame_output:
        raise ValueError("admitted input must distinguish divider settings")
    return {
        "grid_size": [height, width],
        "frame_bbox": [r0, c0, r1, c1],
        "colors": colors,
        "blocks": blocks,
        "block_midrange_divider": list(block_divider),
        "frame_midpoint_divider": list(frame_divider),
        "block_midrange_quadrants": [list(item) for item in block_quadrants],
        "frame_midpoint_quadrants": [list(item) for item in frame_quadrants],
        "block_midrange_missing_quadrant": _missing(block_quadrants),
        "frame_midpoint_missing_quadrant": _missing(frame_quadrants),
        "block_midrange_output": block_output,
        "frame_midpoint_output": frame_output,
    }


def solve(grid: Any, settings: Any) -> list[list[int]]:
    reference = _reference(settings)
    facts = analyze(grid)
    key = "block_midrange_output" if reference == "block_midrange" else "frame_midpoint_output"
    return deepcopy(facts[key])


def _rng(seed: int, index: int, attempt: int) -> random.Random:
    digest = hashlib.sha256(f"3fb5ef8ad60e:parametric:v1:{seed}:{index}:{attempt}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _separated(a: tuple[int, int], b: tuple[int, int]) -> bool:
    ar0, ac0 = a
    br0, bc0 = b
    return ar0 + 1 < br0 - 0 or br0 + 1 < ar0 - 0 or ac0 + 1 < bc0 - 0 or bc0 + 1 < ac0 - 0


def _candidate_grid(spec: tuple[int, int, int, int, int, int], positions: list[tuple[int, int]], colors: list[int]) -> list[list[int]]:
    height, width, r0, c0, bottom_margin, right_margin = spec
    r1 = height - 1 - bottom_margin
    c1 = width - 1 - right_margin
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            grid[row][col] = 8
    for (row, col), color in zip(positions, colors, strict=True):
        for dr in (0, 1):
            for dc in (0, 1):
                grid[row + dr][col + dc] = color
    return grid


def _rival_outputs_from_facts(facts: dict[str, Any]) -> dict[str, list[list[int]]]:
    height, width = facts["grid_size"]
    centers = [tuple(block["center"]) for block in facts["blocks"]]
    canvas_divider = ((height - 1) // 2, (width - 1) // 2)
    numeric = [[0, 0], [0, 0]]
    for cell, color in zip(((0, 0), (0, 1), (1, 0)), sorted(facts["colors"]), strict=True):
        numeric[cell[0]][cell[1]] = color
    result = {"numeric_color_layout": numeric}
    try:
        result["canvas_midpoint"] = render_with_divider(facts["blocks"], canvas_divider)
    except ValueError:
        result["canvas_midpoint"] = [[-1]]
    return result


def _scene(seed: int, index: int) -> list[list[int]]:
    spec = _SPECS[index]
    height, width, r0, c0, bottom_margin, right_margin = spec
    r1 = height - 1 - bottom_margin
    c1 = width - 1 - right_margin
    candidates = [
        (row, col)
        for row in range(r0 + 1, r1 - 1)
        for col in range(c0 + 1, c1 - 1)
    ]
    target_block_missing = (index * 3 + 1) % 4
    target_frame_missing = index % 4
    fallback = None
    for attempt in range(4096):
        rng = _rng(seed, index, attempt)
        positions = rng.sample(candidates, 3)
        if any(not _separated(positions[a], positions[b]) for a in range(3) for b in range(a + 1, 3)):
            continue
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 3)
        grid = _candidate_grid(spec, positions, colors)
        try:
            facts = analyze(grid)
        except ValueError:
            continue
        canonical = facts["block_midrange_output"]
        alternate = facts["frame_midpoint_output"]
        rivals = _rival_outputs_from_facts(facts)
        if canonical in rivals.values() or alternate in rivals.values():
            continue
        fallback = grid
        if (
            facts["block_midrange_missing_quadrant"] == target_block_missing
            and facts["frame_midpoint_missing_quadrant"] == target_frame_missing
        ):
            return grid
    if fallback is not None:
        return fallback
    raise ValueError(f"unable to construct distinguishing scene {seed}/{index}")


@lru_cache(maxsize=128)
def _input_bank(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    scenes = [_scene(seed, index) for index in range(len(_SPECS))]
    demos = scenes[:6]
    queries = scenes[6:]
    rng = random.Random(int.from_bytes(hashlib.sha256(f"3fb5ef8ad60e:query-order:{seed}".encode()).digest(), "big"))
    rng.shuffle(queries)
    signatures = [json.dumps(grid, separators=(",", ":")) for grid in demos + queries]
    if len(signatures) != len(set(signatures)):
        raise ValueError("constructed episode contains duplicate inputs")
    return demos, queries


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _exact_int(seed, "seed", 0, 2**63 - 1)
    demos = _exact_int(demos, "demos", 2, 6)
    queries = _exact_int(queries, "queries", 1, 4)
    _reference(settings)
    demo_bank, query_bank = _input_bank(seed)

    def pair(grid: list[list[int]]) -> dict[str, Any]:
        return {"input": deepcopy(grid), "output": solve(grid, settings)}

    return {
        "train": [pair(grid) for grid in demo_bank[:demos]],
        "test": [pair(grid) for grid in query_bank[:queries]],
        "program_solution": program(settings),
    }


def public_turn(episode: Any, index: Any) -> dict[str, Any]:
    if type(episode) is not dict or set(episode) < {"train", "test"}:
        raise ValueError("episode must contain train and test")
    index = _exact_int(index, "query index", 0, len(episode["test"]) - 1)
    return deepcopy({
        "train": [{"input": pair["input"], "output": pair["output"]} for pair in episode["train"]],
        "test": [{"input": episode["test"][index]["input"]}],
    })


def _rivals(grid: Any, chosen: str) -> dict[str, list[list[int]]]:
    facts = analyze(grid)
    result = _rival_outputs_from_facts(facts)
    for other in DIVIDER_REFERENCES:
        if other != chosen:
            result[other] = solve(grid, {"divider_reference": other})
    return result


def lesson_report(episode: Any, settings: Any) -> dict[str, Any]:
    chosen = _reference(settings)
    names = sorted(_rivals(episode["train"][0]["input"], chosen))
    survivors = []
    query_disagreements = []
    for name in names:
        fits = all(_rivals(pair["input"], chosen)[name] == pair["output"] for pair in episode["train"])
        if fits:
            survivors.append(name)
            if any(_rivals(pair["input"], chosen)[name] != pair["output"] for pair in episode["test"]):
                query_disagreements.append(name)
    return {
        "rivals_tested": names,
        "surviving_rivals": survivors,
        "query_disagreements": query_disagreements,
    }
