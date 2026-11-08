"""Proposed largest/smallest component-selector family for d1dd527dba87.

The input grammar is independent of the hidden selector.  Each scene contains
unique small and large blue/red components, and the first three demonstrations
reverse their absolute row/column ordering to block positional selector rivals.
"""
from __future__ import annotations

import hashlib
import random
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "d1dd527dba87"
PARAMETER = "selector"
SETTINGS = ("largest", "smallest")
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
MAX_SEED = 2**63 - 1

_HOME = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    "largest": _HOME / "largest.rkt",
    "smallest": _HOME / "smallest.rkt",
}
_TRAIN_PROFILES = ((9, 11, 0), (10, 13, 1), (12, 15, 2), (15, 18, 3), (20, 24, 4), (24, 28, 5))
_QUERY_PROFILES = ((9, 12, 10), (16, 20, 11), (23, 29, 12), (30, 30, 13))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

_BLUE_LARGE = frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)})
_RED_LARGE = frozenset({(0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 2), (3, 2)})
_BLUE_SMALL = frozenset({(0, 0), (0, 1)})
_RED_SMALL = frozenset({(0, 0), (1, 0)})

# (blue-large, blue-small, red-large, red-small).  The first three schedules
# reverse both row and column predicates for each color, defeating bottommost,
# rightmost, and fixed-corner shortcuts while preserving the object grammar.
_LAYOUTS = (
    ("TL", "BR", "BL", "TR"),
    ("BR", "TL", "TR", "BL"),
    ("TR", "BL", "TL", "BR"),
    ("BL", "TR", "BR", "TL"),
)


def _validate_settings(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return value


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def program(settings: dict[str, str]) -> str:
    return _PROGRAM_FILES[_validate_settings(settings)].read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|inputs-v1|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(shape)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _corner_origin(corner: str, shape: Iterable[tuple[int, int]], h: int, w: int) -> tuple[int, int]:
    sh, sw = _dims(shape)
    return {
        "TL": (0, 0),
        "TR": (0, w - sw),
        "BL": (h - sh, 0),
        "BR": (h - sh, w - sw),
    }[corner]


def _paint(grid: list[list[int]], shape: Iterable[tuple[int, int]], corner: str, color: int) -> None:
    top, left = _corner_origin(corner, shape, len(grid), len(grid[0]))
    for r, c in shape:
        if grid[top + r][left + c] != 0:
            raise RuntimeError("scene components overlap")
        grid[top + r][left + c] = color


def _sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    h, w, tag = (_TRAIN_PROFILES if split == "train" else _QUERY_PROFILES)[index]
    grid = [[0 for _ in range(w)] for _ in range(h)]
    bl, bs, rl, rs = _LAYOUTS[tag % len(_LAYOUTS)]
    _paint(grid, _BLUE_LARGE, bl, 1)
    _paint(grid, _BLUE_SMALL, bs, 1)
    _paint(grid, _RED_LARGE, rl, 2)
    _paint(grid, _RED_SMALL, rs, 2)

    rng = _rng(seed, split, index)
    colors = [4, 5, 6, 7, 9]
    rng.shuffle(colors)
    candidates = [
        (h // 2, w // 2),
        (h // 2, max(0, w // 2 - 2)),
        (min(h - 1, h // 2 + 2), min(w - 1, w // 2 + 1)),
    ]
    if len(set(candidates)) != 3 or any(grid[r][c] for r, c in candidates):
        candidates = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1) if grid[r][c] == 0][:3]
    for color, (r, c) in zip(colors, candidates):
        grid[r][c] = color
    return grid


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30")
    if any(type(row) is not list or len(row) != width or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid must be rectangular with exact ARC colors")
    return len(grid), width


def components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = _validate_grid(grid)
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    found: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        comp = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    comp.add(nxt)
                    stack.append(nxt)
        found.append(comp)
    return found


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def apply_rule(grid: list[list[int]], selector: str) -> list[list[int]]:
    if type(selector) is not str or selector not in SETTINGS:
        raise ValueError(f"selector must be one of {SETTINGS!r}")
    _validate_grid(grid)
    chosen = []
    for color in (1, 2):
        comps = components(grid, color)
        if not comps:
            raise ValueError(f"missing color-{color} component")
        sizes = [len(comp) for comp in comps]
        target_size = (max if selector == "largest" else min)(sizes)
        matches = [comp for comp in comps if len(comp) == target_size]
        if len(matches) != 1:
            raise ValueError(f"selector must have a unique color-{color} result")
        chosen.append(_normalize(matches[0]))
    xor = chosen[0] ^ chosen[1]
    if not xor:
        return [[0]]
    norm = _normalize(xor)
    h = max(r for r, _ in norm) + 1
    w = max(c for _, c in norm) + 1
    return [[8 if (r, c) in norm else 0 for c in range(w)] for r in range(h)]


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, MIN_QUERIES, MAX_QUERIES)
    selected = _validate_settings(settings)
    train = []
    for index in range(demos):
        grid = _sample_input(seed, "train", index)
        train.append({"input": grid, "output": apply_rule(grid, selected)})
    test = []
    for index in range(queries):
        grid = _sample_input(seed, "test", index)
        test.append({"input": grid, "output": apply_rule(grid, selected)})
    serialized = [repr(pair["input"]) for pair in [*train, *test]]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("all demonstration and query inputs must be distinct")
    return {"train": train, "test": test, "program_solution": program(settings)}
