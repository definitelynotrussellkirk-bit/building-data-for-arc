"""Native prototype for episode-fixed query operand order in 0938f7c346fb.

The canonical rule infers one of four color-aware operations from panels A, B,
and RESULT, then applies it to query panels X and Y.  This family keeps that
causal structure and varies only the episode-fixed order of X and Y.
"""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
import json
import random
from pathlib import Path
from typing import Iterable

from reviewer_support import canonical_path, find_root

TASK_ID = "0938f7c346fb"
ROOT = find_root(__file__)
ORDERS = ("xy", "yx")
DEFAULT_ORDER = "xy"
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
CANONICAL_SOURCE_SHA256 = "c2d521df026ad7f4b92ac2fefbf752001c47693a60accb4fcc78b4e317eeffe8"
CANONICAL_RULE_HASH = "c2d521df026a"
_FINAL_XY = "(apply-op op x y))))"
_FINAL_YX = "(apply-op op y x))))"
OPS = ("intersection-eq", "xor", "left-minus", "conflict-merge")
COLORS = (1, 2, 3, 4, 6, 7, 8)
DEMO_SCHEDULE = (
    "left-minus",
    "conflict-merge",
    "intersection-eq",
    "xor",
    "left-minus",
    "conflict-merge",
)
QUERY_SCHEDULE = OPS


def _literal_int(name: str, value, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a literal integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be in {minimum}..{maximum}")
    return value


def _order(value) -> str:
    if not isinstance(value, str):
        raise TypeError("query operand order must be a string")
    if value not in ORDERS:
        raise ValueError(f"query operand order must be one of {ORDERS}")
    return value


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs: set[str] = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("exactly one canonical Racket program is required")
    program = next(iter(programs))
    if hashlib.sha256(program.encode("utf-8")).hexdigest() != CANONICAL_SOURCE_SHA256:
        raise ValueError("canonical Racket source changed; review the family")
    if hashlib.sha256(" ".join(program.split()).encode("utf-8")).hexdigest()[:12] != CANONICAL_RULE_HASH:
        raise ValueError("canonical normalized rule hash changed; review the family")
    if program.count(_FINAL_XY) != 1:
        raise ValueError("canonical final query application changed; review the family")
    return program


@lru_cache(maxsize=len(ORDERS))
def program_for(order: str) -> str:
    order = _order(order)
    canonical = canonical_program()
    if order == "xy":
        return canonical
    alternate = canonical.replace(_FINAL_XY, _FINAL_YX, 1)
    if alternate == canonical or alternate.count(_FINAL_YX) != 1:
        raise ValueError("failed to derive the yx program exactly once")
    return alternate


def _apply(name: str, left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    if name not in OPS:
        raise ValueError(f"unknown operation: {name}")
    height = len(left)
    width = len(left[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            x = left[row][col]
            y = right[row][col]
            if name == "intersection-eq":
                output[row][col] = x if x != 0 and x == y else 0
            elif name == "xor":
                if (x != 0) != (y != 0):
                    output[row][col] = x or y
            elif name == "left-minus":
                output[row][col] = x if x != 0 and y == 0 else 0
            elif x == 0:
                output[row][col] = y
            elif y == 0 or x == y:
                output[row][col] = x
            else:
                output[row][col] = 9
    return output


def _infer(left: list[list[int]], right: list[list[int]], result: list[list[int]]) -> str:
    matches = [name for name in OPS if _apply(name, left, right) == result]
    if len(matches) != 1:
        raise ValueError(f"demonstration must identify one operation, found {matches}")
    return matches[0]


def _paint(mask: list[list[int]], color: int) -> list[list[int]]:
    return [[color if value else 0 for value in row] for row in mask]


def _rng(seed: int, role: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"0938-query-order-v1:{seed}:{role}:{index}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _category_masks(
    rng: random.Random,
    height: int,
    width: int,
    *,
    dense: bool,
) -> tuple[list[list[int]], list[list[int]]]:
    """Return masks with guaranteed left-only, right-only, and overlap cells."""
    cells = [(row, col) for row in range(height) for col in range(width)]
    rng.shuffle(cells)
    if len(cells) < 3:
        raise ValueError("panel needs at least three cells")
    categories: dict[tuple[int, int], int] = {
        cells[0]: 1,
        cells[1]: 2,
        cells[2]: 3,
    }
    if dense:
        weights = (0, 1, 2, 3)
        probabilities = (0.12, 0.27, 0.27, 0.34)
    else:
        weights = (0, 1, 2, 3)
        probabilities = (0.46, 0.18, 0.18, 0.18)
    for cell in cells[3:]:
        categories[cell] = rng.choices(weights, probabilities, k=1)[0]
    left = [[0 for _ in range(width)] for _ in range(height)]
    right = [[0 for _ in range(width)] for _ in range(height)]
    for (row, col), category in categories.items():
        if category in (1, 3):
            left[row][col] = 1
        if category in (2, 3):
            right[row][col] = 1
    return left, right


def _colors(rng: random.Random, operation: str) -> tuple[int, int]:
    left = rng.choice(COLORS)
    if operation == "intersection-eq":
        return left, left
    right = rng.choice(tuple(color for color in COLORS if color != left))
    return left, right


def _panels_for_operation(
    rng: random.Random,
    operation: str,
    height: int,
    width: int,
    *,
    dense: bool,
) -> tuple[list[list[int]], list[list[int]], list[list[int]]]:
    left_mask, right_mask = _category_masks(rng, height, width, dense=dense)
    left_color, right_color = _colors(rng, operation)
    left = _paint(left_mask, left_color)
    right = _paint(right_mask, right_color)
    result = _apply(operation, left, right)
    if _infer(left, right, result) != operation:
        raise RuntimeError("constructed demonstration lost unique operation inference")
    return left, right, result


def _assemble(panels: Iterable[list[list[int]]]) -> list[list[int]]:
    panels = list(panels)
    if len(panels) != 5:
        raise ValueError("exactly five panels are required")
    height = len(panels[0])
    width = len(panels[0][0])
    if not 1 <= height <= 30 or not 1 <= width <= 5:
        raise ValueError("panel dimensions exceed admitted ARC canvas")
    if any(len(panel) != height or any(len(row) != width for row in panel) for panel in panels):
        raise ValueError("all panels must share dimensions")
    grid = [[0 for _ in range(5 * width + 4)] for _ in range(height)]
    for index, panel in enumerate(panels):
        left = index * (width + 1)
        for row in range(height):
            grid[row][left:left + width] = list(panel[row])
            if index < 4:
                grid[row][left + width] = 5
    return grid


def _split(grid: list[list[int]]) -> list[list[list[int]]]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) and row for row in grid):
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if any(len(row) != width for row in grid) or (width - 4) % 5:
        raise ValueError("grid must contain five equal panels and four separators")
    panel_width = (width - 4) // 5
    return [
        [
            row[index * (panel_width + 1):index * (panel_width + 1) + panel_width]
            for row in grid
        ]
        for index in range(5)
    ]


def infer_operation(grid: list[list[int]]) -> str:
    panels = _split(grid)
    return _infer(panels[0], panels[1], panels[2])


def output_for(grid: list[list[int]], order: str) -> list[list[int]]:
    order = _order(order)
    panels = _split(grid)
    operation = _infer(panels[0], panels[1], panels[2])
    left, right = (panels[3], panels[4]) if order == "xy" else (panels[4], panels[3])
    return _apply(operation, left, right)


def _dimensions(seed: int, role: str, index: int) -> tuple[int, int, bool]:
    if role == "query" and index == QUERY_COUNT - 1:
        return 30, 5, True
    height = 4 + ((seed + index + (0 if role == "demo" else 1)) % 3)
    width = 4 + ((seed // 3 + index) % 2)
    return height, width, False


def _pair(seed: int, role: str, index: int, operation: str, order: str) -> dict:
    height, width, dense = _dimensions(seed, role, index)
    rng = _rng(seed, role, index)
    a, b, result = _panels_for_operation(rng, operation, height, width, dense=dense)
    x, y, _unused = _panels_for_operation(rng, operation, height, width, dense=dense)
    grid = _assemble((a, b, result, x, y))
    output = output_for(grid, order)
    if not any(value != 0 for row in output for value in row):
        raise RuntimeError("constructed query output is empty")
    return {"input": grid, "output": output}


def generate_episode(seed: int, order: str, demos: int, queries: int) -> dict:
    seed = _literal_int("seed", seed, 0, 2**63 - 1)
    order = _order(order)
    demos = _literal_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _literal_int("queries", queries, QUERY_COUNT, QUERY_COUNT)

    train = [
        _pair(seed, "demo", index, DEMO_SCHEDULE[index], order)
        for index in range(demos)
    ]
    test = [
        _pair(seed, "query", index, QUERY_SCHEDULE[index], order)
        for index in range(queries)
    ]
    identifiers = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in [*train, *test]
    ]
    if len(identifiers) != len(set(identifiers)):
        raise RuntimeError("episode contains duplicate inputs")
    # Each setting must be identified from demonstrations alone.  The first
    # demonstration is a directional left-minus witness, so both programs run
    # successfully and disagree on its label.
    if train[0]["output"] == output_for(train[0]["input"], "yx" if order == "xy" else "xy"):
        raise RuntimeError("directional demonstration failed to identify query order")
    return copy.deepcopy({
        "train": train,
        "test": test,
        "program_solution": program_for(order),
    })
