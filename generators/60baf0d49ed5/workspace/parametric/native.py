"""Native parametric family for 60baf0d49ed5.

The canonical setting infers the panel A->B transform and applies it once to C.
The alternative applies that same inferred transform a second time.  Its causal
chain is explicit: Step A infers the operation and creates the once-transformed
C; Step B consumes that intermediate and applies the inferred operation again.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "60baf0d49ed5"
PARAMETER = "application_mode"
CANONICAL = "direct"
ALTERNATIVE = "repeat_transform"
SETTINGS = (CANONICAL, ALTERNATIVE)
OPERATIONS = ("rot90", "rot270", "rot180", "flip-h", "flip-v")
HOME = Path(__file__).resolve().parent

# side, A->B operation, target colored cells in each panel, color count
DEMO_SPECS = (
    (3, "rot90", 5, 1),
    (4, "flip-h", 9, 2),
    (5, "rot180", 12, 3),
    (6, "rot270", 15, 2),
    (7, "flip-v", 18, 3),
    (8, "rot90", 22, 2),
)
QUERY_SPECS = (
    (4, "rot270", 9, 3),
    (5, "flip-v", 12, 2),
    (6, "flip-h", 16, 3),
    (9, "rot180", 26, 3),
)


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS}")
    return value


def program(settings: dict[str, Any]) -> str:
    mode = _setting(settings)
    name = "canonical.rkt" if mode == CANONICAL else "repeat_transform.rkt"
    return (HOME / name).read_text(encoding="utf-8")


def counterfactual_program() -> str:
    """Skip Step B of the alternative by returning the once-applied rule."""
    return (HOME / "canonical.rkt").read_text(encoding="utf-8")


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    height, width = len(grid), len(grid[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be 1..30")
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid cells must be exact integer ARC colors")
    return height, width


def apply_transform(grid: list[list[int]], operation: str) -> list[list[int]]:
    if operation not in OPERATIONS:
        raise ValueError(f"unknown operation: {operation!r}")
    n = len(grid)
    if not n or any(len(row) != n for row in grid):
        raise ValueError("transforms require a nonempty square grid")
    if operation == "rot90":
        return [[grid[n - 1 - c][r] for c in range(n)] for r in range(n)]
    if operation == "rot270":
        return [[grid[c][n - 1 - r] for c in range(n)] for r in range(n)]
    if operation == "rot180":
        return [[grid[n - 1 - r][n - 1 - c] for c in range(n)] for r in range(n)]
    if operation == "flip-h":
        return [list(reversed(row)) for row in grid]
    return [row[:] for row in reversed(grid)]


def split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    height, width = _validate_grid(grid)
    dividers = [c for c in range(width) if all(grid[r][c] == 9 for r in range(height))]
    if len(dividers) != 2:
        raise ValueError("expected exactly two full-height color-9 divider columns")
    if dividers != [height, 2 * height + 1] or width != 3 * height + 2:
        raise ValueError("divider positions must form three equal square panels")
    starts = (0, dividers[0] + 1, dividers[1] + 1)
    return [[row[left : left + height] for row in grid] for left in starts]


def infer_transform(grid: list[list[int]]) -> str:
    a, b, _ = split_panels(grid)
    matches = [operation for operation in OPERATIONS if apply_transform(a, operation) == b]
    if len(matches) != 1:
        raise ValueError(f"expected one A->B transform, got {matches}")
    return matches[0]


def transform(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode not in SETTINGS:
        raise ValueError(f"unknown mode: {mode!r}")
    operation = infer_transform(grid)
    c = split_panels(grid)[2]
    once = apply_transform(c, operation)
    return once if mode == CANONICAL else apply_transform(once, operation)


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    panels = split_panels(grid)
    operation = infer_transform(grid)
    return {
        "shape": [len(grid), len(grid[0])],
        "operation": operation,
        "panel_nonzero": [sum(cell != 0 for row in panel for cell in row) for panel in panels],
        "direct_output": transform(grid, CANONICAL),
        "repeat_output": transform(grid, ALTERNATIVE),
    }


def _rng(seed: int, *parts: Any) -> random.Random:
    payload = json.dumps([TASK_ID, "native-repeat-v1", seed, *parts], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _base_cells(side: int) -> set[tuple[int, int]]:
    if side == 3:
        return {(0, 0), (0, 1), (1, 1), (1, 2), (2, 1)}
    cells = {(r, 0) for r in range(side)} | {(side - 1, c) for c in range(side)}
    cells |= {(1, 1), (1, 2)}
    return cells


def _images(panel: list[list[int]]) -> set[tuple[tuple[int, ...], ...]]:
    return {
        tuple(tuple(row) for row in image)
        for image in [panel] + [apply_transform(panel, operation) for operation in OPERATIONS]
    }


def _panel(seed: int, index: int, role: str, side: int, target: int, colors: list[int]) -> list[list[int]]:
    target = max(target, len(colors), len(_base_cells(side)))
    target = min(target, side * side - 1)
    for attempt in range(200):
        rng = _rng(seed, index, role, side, target, colors, attempt)
        cells = set(_base_cells(side))
        while len(cells) < target:
            frontier = []
            for r, c in cells:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < side and 0 <= nc < side and (nr, nc) not in cells:
                        frontier.append((nr, nc))
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        order = sorted(cells)
        rng.shuffle(order)
        panel = [[0] * side for _ in range(side)]
        for position, (r, c) in enumerate(order):
            panel[r][c] = colors[position] if position < len(colors) else rng.choice(colors)
        if len(_images(panel)) == 6:
            return panel
    raise RuntimeError("failed to construct a fully asymmetric panel")


def sample_input(
    seed: int,
    index: int,
    spec: tuple[int, str, int, int],
) -> tuple[list[list[int]], dict[str, Any]]:
    side, operation, target_cells, color_count = spec
    _exact_int(seed, 0, 2**63 - 1, "seed")
    _exact_int(index, 0, 1000, "index")
    if operation not in OPERATIONS:
        raise ValueError("invalid operation in spec")
    colors = list(range(1, 9))
    _rng(seed, index, "palette").shuffle(colors)
    colors = colors[:color_count]
    a = _panel(seed, index, "a", side, target_cells, colors)
    b = apply_transform(a, operation)
    c = _panel(seed, index, "c", side, target_cells, list(reversed(colors)))
    width = 3 * side + 2
    grid = [[0] * width for _ in range(side)]
    for divider in (side, 2 * side + 1):
        for r in range(side):
            grid[r][divider] = 9
    for panel_index, panel in enumerate((a, b, c)):
        left = panel_index * (side + 1)
        for r, row in enumerate(panel):
            grid[r][left : left + side] = row
    if infer_transform(grid) != operation:
        raise RuntimeError("constructed input does not uniquely encode its operation")
    if transform(grid, CANONICAL) == transform(grid, ALTERNATIVE):
        raise RuntimeError("constructed input does not distinguish the settings")
    return grid, {
        "side": side,
        "operation": operation,
        "target_cells": target_cells,
        "colors": colors,
        "input_shape": [side, width],
    }


def _query_order(seed: int) -> list[int]:
    offset = (seed + 1) % len(QUERY_SPECS)
    order = list(range(len(QUERY_SPECS)))
    return order[offset:] + order[:offset]


def _fixed_output(grid: list[list[int]], operation: str, repeats: int) -> list[list[int]]:
    value = split_panels(grid)[2]
    for _ in range(repeats):
        value = apply_transform(value, operation)
    return value


def lesson_certificate(train: list[dict[str, Any]], chosen: str) -> dict[str, Any]:
    settings = [
        {PARAMETER: mode}
        for mode in SETTINGS
        if all(transform(pair["input"], mode) == pair["output"] for pair in train)
    ]
    rivals: dict[str, Any] = {"identity": lambda grid: split_panels(grid)[2]}
    for operation in OPERATIONS:
        rivals[f"fixed_{operation}_once"] = lambda grid, op=operation: _fixed_output(grid, op, 1)
        rivals[f"fixed_{operation}_twice"] = lambda grid, op=operation: _fixed_output(grid, op, 2)
    ambiguous = [
        name
        for name, rival in rivals.items()
        if all(rival(pair["input"]) == pair["output"] for pair in train)
    ]
    return {
        "chosen": {PARAMETER: chosen},
        "surviving_settings": settings,
        "ambiguous_rivals": ambiguous,
        "tested_rivals": sorted(rivals),
    }


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    seed = _exact_int(seed, 0, 2**63 - 1, "seed")
    demos = _exact_int(demos, 2, 6, "demos")
    queries = _exact_int(queries, 1, 4, "queries")
    mode = _setting(settings)
    demo_rows = [sample_input(seed, i, DEMO_SPECS[i]) for i in range(demos)]
    query_rows = [sample_input(seed, 100 + i, spec) for i, spec in enumerate(QUERY_SPECS)]
    query_rows = [query_rows[i] for i in _query_order(seed)][:queries]

    def pair(row):
        grid, _meta = row
        return {"input": copy.deepcopy(grid), "output": transform(grid, mode)}

    train = [pair(row) for row in demo_rows]
    test = [pair(row) for row in query_rows]
    certificate = lesson_certificate(train, mode)
    if certificate["surviving_settings"] != [{PARAMETER: mode}]:
        raise ValueError("visible demonstrations do not uniquely teach the selected setting")
    if certificate["ambiguous_rivals"]:
        raise ValueError(f"finite shortcut ambiguity: {certificate['ambiguous_rivals']}")
    return {
        "train": train,
        "test": test,
        "program_solution": program(settings),
        "settings": copy.deepcopy(settings),
        "seed": seed,
        "certificate": certificate,
        "sampling": {
            "demo_specs": [list(spec) for spec in DEMO_SPECS[:demos]],
            "query_order": _query_order(seed),
            "domain_max": "9x29; exact 30x30 is incompatible with three square panels plus two divider columns",
        },
        "status": "proposed",
        "training_admitted": False,
    }


def public_turn(episode: dict[str, Any], index: int) -> dict[str, Any]:
    from reviewer_support import public_challenge_bytes

    index = _exact_int(index, 0, len(episode["test"]) - 1, "query index")
    return json.loads(
        public_challenge_bytes({"train": episode["train"], "test": [episode["test"][index]]})
    )
