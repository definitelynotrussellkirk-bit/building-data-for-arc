"""Native parametric family for 70205357c60a.

The default is the exact canonical local-neighbour rule.  The alternate first
runs that rule, counts its newly produced red interior cells on the controller
side, and uses the count to select a payload object on the other side.
"""
from __future__ import annotations

from collections import deque
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "70205357c60a"
MODES = ("canonical", "interior_count_relay")
DEFAULT_MODE = "canonical"
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
HERE = Path(__file__).resolve().parent


def _read(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8")


def program_for(mode: str) -> str:
    if mode == "canonical":
        return _read("canonical.rkt")
    if mode == "interior_count_relay":
        return _read("relay.rkt")
    raise ValueError(f"mode must be one of {MODES}")


def counterfactual_program() -> str:
    return _read("wrong_raw_component_count.rkt")


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _validate_mode(mode: Any) -> str:
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return mode


def _blank(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> None:
    h, w = len(grid), len(grid[0])
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w):
            raise ValueError(f"paint cell {(r, c)} outside {h}x{w}")
        if grid[r][c] != 0:
            raise ValueError(f"paint overlap at {(r, c)}")
        grid[r][c] = color


def _rect(r0: int, c0: int, height: int, width: int) -> list[tuple[int, int]]:
    return [(r, c) for r in range(r0, r0 + height) for c in range(c0, c0 + width)]


def _shape_cells(kind: int, r0: int, c0: int, scale: int) -> list[tuple[int, int]]:
    if kind % 3 == 0:
        return _rect(r0, c0, 2 + scale, 2 + scale)
    if kind % 3 == 1:
        cells = _rect(r0, c0, 2 + scale, 2)
        cells += _rect(r0 + 1 + scale, c0, 1, 2 + scale)
        return sorted(set(cells))
    cells = _rect(r0, c0, 1, 3 + scale)
    cells += _rect(r0 + 1, c0 + 1, 1 + scale, 1)
    return sorted(set(cells))


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    todo = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result: list[list[tuple[int, int]]] = []
    while todo:
        start = min(todo)
        todo.remove(start)
        queue = deque([start])
        cells = [start]
        while queue:
            r, c = queue.popleft()
            for dr, dc in DIR4:
                nxt = (r + dr, c + dc)
                if nxt in todo:
                    todo.remove(nxt)
                    queue.append(nxt)
                    cells.append(nxt)
        result.append(sorted(cells))
    return sorted(result, key=lambda cells: cells[0])


def canonical_transform(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5:
                continue
            if all(0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 5
                   for dr, dc in DIR4):
                out[r][c] = 2
    return out


def _separator_col(grid: list[list[int]]) -> int:
    positions = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    cols = {c for _, c in positions}
    if len(cols) != 1:
        raise ValueError("expected one full color-9 separator column")
    col = next(iter(cols))
    if len(positions) != len(grid):
        raise ValueError("separator must span the full height")
    return col


def interior_count(grid: list[list[int]]) -> int:
    stage = canonical_transform(grid)
    sep = _separator_col(grid)
    value = sum(value == 2 for row in stage for value in row[:sep])
    if value not in (1, 2, 3):
        raise ValueError(f"intermediate interior count must be 1..3, got {value}")
    return value


def relay_transform(grid: list[list[int]]) -> list[list[int]]:
    stage = canonical_transform(grid)
    sep = _separator_col(grid)
    payloads = [cells for cells in _components(stage, 3) if cells[0][1] > sep]
    if len(payloads) != 3:
        raise ValueError(f"expected three payloads, found {len(payloads)}")
    target = payloads[interior_count(grid) - 1]
    out = [row[:] for row in stage]
    for r, c in target:
        out[r][c] = 8
    return out


def transform(grid: list[list[int]], mode: str) -> list[list[int]]:
    mode = _validate_mode(mode)
    return canonical_transform(grid) if mode == "canonical" else relay_transform(grid)


def _profile(is_query: bool, index: int) -> tuple[int, int]:
    demos = ((11, 14), (13, 16), (15, 18), (17, 20), (19, 22), (21, 24))
    queries = ((14, 16), (18, 20), (24, 26), (30, 30))
    return (queries if is_query else demos)[index]


def _scene(seed: int, index: int, *, is_query: bool, attempt: int = 0) -> list[list[int]]:
    height, width = _profile(is_query, index)
    token = hashlib.sha256(f"70205357c60a-scene-v2:{seed}:{is_query}:{index}:{attempt}".encode()).digest()
    rng = random.Random(token)
    grid = _blank(height, width)
    sep = width // 2
    for r in range(height):
        grid[r][sep] = 9

    if is_query:
        query_schedule = (1, 2, 3, 1 + (seed % 3))
        k = query_schedule[index]
    else:
        leading = (2, 3) if seed % 2 == 0 else (3, 2)
        demo_schedule = leading + (1, 2, 3, 1)
        k = demo_schedule[index]
    vertical = (seed + index + attempt) % 2 == 1
    if vertical:
        rh, rw = k + 2, 3
    else:
        rh, rw = 3, k + 2
    max_r = max(1, height - rh - 1)
    max_c = max(1, sep - rw - 1)
    r0 = 1 + rng.randrange(max_r)
    c0 = rng.randrange(max_c + 1)
    _paint(grid, _rect(r0, c0, rh, rw), 5)

    # Smaller 5-shapes are deliberate distractors but never contain a fully
    # surrounded cell and never reach the >=9-cell raw-component shortcut.
    distractors = [
        [(0, 0), (0, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)],
    ]
    occupied = {(r, c) for r in range(height) for c in range(sep) if grid[r][c]}
    for shape_index, offsets in enumerate(distractors[: 2 + int(height >= 20)]):
        placed = False
        for _ in range(128):
            sr = rng.randrange(height)
            sc = rng.randrange(max(1, sep - 2))
            cells = {(sr + dr, sc + dc) for dr, dc in offsets}
            halo = {(r + dr, c + dc) for r, c in cells for dr, dc in DIR4} | cells
            if all(0 <= r < height and 0 <= c < sep for r, c in cells) and not (halo & occupied):
                _paint(grid, sorted(cells), 5)
                occupied |= cells
                placed = True
                break
        if not placed:
            raise RuntimeError(f"could not place controller distractor {shape_index}")

    right_start = sep + 1
    right_width = width - right_start
    bands = [(0, height // 3), (height // 3, 2 * height // 3), (2 * height // 3, height)]
    payload_occupied: set[tuple[int, int]] = set()
    for payload_index, (lo, hi) in enumerate(bands):
        scale = 0 if height < 18 else 1 if height < 27 else 2
        kind = payload_index + seed + index
        for _ in range(128):
            cells0 = _shape_cells(kind, 0, 0, scale)
            sh = max(r for r, _ in cells0) + 1
            sw = max(c for _, c in cells0) + 1
            if hi - lo < sh or right_width < sw:
                scale = max(0, scale - 1)
                continue
            pr = lo + rng.randrange(hi - lo - sh + 1)
            pc = right_start + rng.randrange(right_width - sw + 1)
            cells = {(pr + r, pc + c) for r, c in _shape_cells(kind, 0, 0, scale)}
            halo = cells | {(r + dr, c + dc) for r, c in cells for dr, dc in DIR4}
            if all(grid[r][c] == 0 for r, c in cells) and not (halo & payload_occupied):
                _paint(grid, sorted(cells), 3)
                payload_occupied |= cells
                break
        else:
            raise RuntimeError(f"could not place payload {payload_index}")

    # Sparse non-rule distractors and a seed/index marker make episodes visibly
    # varied without affecting the controller or payload semantics.
    for color in (1, 4, 6):
        for _ in range(64):
            r = rng.randrange(height)
            c = rng.randrange(width)
            if c != sep and grid[r][c] == 0:
                grid[r][c] = color
                break

    _validate_scene(grid)
    return grid


def _validate_scene(grid: list[list[int]]) -> None:
    if not grid or not grid[0] or len(grid) > 30 or len(grid[0]) > 30:
        raise ValueError("scene dimensions must be within 1..30")
    if any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("scene must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("scene cells must be exact ARC integers")
    sep = _separator_col(grid)
    if len([cells for cells in _components(grid, 3) if cells[0][1] > sep]) != 3:
        raise ValueError("scene must expose exactly three ordered payloads")
    if len([cells for cells in _components(grid, 5) if max(c for _, c in cells) < sep and len(cells) >= 9]) != 1:
        raise ValueError("scene must expose one large raw controller component")
    interior_count(grid)


def build_episode(seed: int, mode: str, demos: int, queries: int) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)
    mode = _validate_mode(mode)
    seen: set[tuple[tuple[int, ...], ...]] = set()

    def collect(count: int, is_query: bool) -> list[dict[str, list[list[int]]]]:
        pairs = []
        for index in range(count):
            for attempt in range(32):
                grid = _scene(seed, index, is_query=is_query, attempt=attempt)
                key = tuple(tuple(row) for row in grid)
                if key not in seen:
                    seen.add(key)
                    pairs.append({"input": grid, "output": transform(grid, mode)})
                    break
            else:
                raise RuntimeError("bounded sampler exhausted without a distinct input")
        return pairs

    return {
        "train": collect(demos, False),
        "test": collect(queries, True),
        "program_solution": program_for(mode),
    }
