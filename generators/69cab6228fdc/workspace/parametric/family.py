"""Native parametric family for 69cab6228fdc.

The canonical setting applies the two-row legend and removes the three header
rows.  The alternate first performs that exact transform, counts the resulting
colour-2 regions on the controller side, and uses that count to select one of
three payload components on the other side.
"""
from __future__ import annotations

from collections import deque
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "69cab6228fdc"
MODES = ("canonical", "mapped_region_relay")
DEFAULT_MODE = "canonical"
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
HERE = Path(__file__).resolve().parent


def _read(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8")


def program_for(mode: str) -> str:
    mode = _validate_mode(mode)
    return _read("canonical.rkt" if mode == "canonical" else "relay.rkt")


def counterfactual_program() -> str:
    return _read("wrong_raw_source_components.rkt")


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


def _legend_pairs(grid: list[list[int]]) -> list[tuple[int, int]]:
    if len(grid) < 4:
        raise ValueError("legend input needs at least four rows")
    return [(a, b) for a, b in zip(grid[0], grid[1]) if a != 0 and b != 0]


def canonical_transform(grid: list[list[int]]) -> list[list[int]]:
    pairs = _legend_pairs(grid)
    mapping: dict[int, int] = {}
    for source, target in pairs:
        mapping.setdefault(source, target)
    return [[mapping.get(value, value) for value in row] for row in grid[3:]]


def _separator_col(stage: list[list[int]]) -> int:
    positions = [(r, c) for r, row in enumerate(stage) for c, value in enumerate(row) if value == 9]
    columns = {c for _, c in positions}
    if len(columns) != 1:
        raise ValueError("expected one colour-9 separator column")
    col = next(iter(columns))
    if len(positions) != len(stage):
        raise ValueError("separator must span the transformed canvas")
    return col


def mapped_region_count(grid: list[list[int]]) -> int:
    stage = canonical_transform(grid)
    sep = _separator_col(stage)
    regions = [cells for cells in _components(stage, 2) if max(c for _, c in cells) < sep]
    value = len(regions)
    if value not in (1, 2, 3):
        raise ValueError(f"mapped colour-2 region count must be 1..3, got {value}")
    return value


def raw_source_count(grid: list[list[int]]) -> int:
    body = grid[3:]
    stage = canonical_transform(grid)
    sep = _separator_col(stage)
    return len([cells for cells in _components(body, 1) if max(c for _, c in cells) < sep])


def _payloads(stage: list[list[int]]) -> list[list[tuple[int, int]]]:
    sep = _separator_col(stage)
    payloads = [cells for cells in _components(stage, 6) if min(c for _, c in cells) > sep]
    return sorted(payloads, key=lambda cells: cells[0])


def relay_transform(grid: list[list[int]]) -> list[list[int]]:
    stage = canonical_transform(grid)
    payloads = _payloads(stage)
    if len(payloads) != 3:
        raise ValueError(f"expected three payloads, found {len(payloads)}")
    target = payloads[mapped_region_count(grid) - 1]
    out = [row[:] for row in stage]
    for r, c in target:
        out[r][c] = 8
    return out


def transform(grid: list[list[int]], mode: str) -> list[list[int]]:
    mode = _validate_mode(mode)
    return canonical_transform(grid) if mode == "canonical" else relay_transform(grid)


def _profile(is_query: bool, index: int) -> tuple[int, int]:
    demos = ((15, 18), (15, 18), (17, 20), (19, 22), (22, 24), (24, 26))
    queries = ((16, 18), (20, 22), (26, 28), (30, 30))
    return (queries if is_query else demos)[index]


def _shape_cells(kind: int, r0: int, c0: int, scale: int) -> list[tuple[int, int]]:
    if kind % 3 == 0:
        return [(r, c) for r in range(r0, r0 + 2 + scale) for c in range(c0, c0 + 2)]
    if kind % 3 == 1:
        cells = [(r0, c0 + c) for c in range(3 + scale)]
        cells += [(r0 + r, c0) for r in range(1, 2 + scale)]
        return sorted(set(cells))
    cells = [(r0 + r, c0 + 1) for r in range(2 + scale)]
    cells += [(r0 + 1 + scale, c0 + c) for c in range(3 + scale)]
    return sorted(set(cells))


def _scene(seed: int, index: int, *, is_query: bool, attempt: int = 0) -> list[list[int]]:
    height, width = _profile(is_query, index)
    body_h = height - 3
    token = hashlib.sha256(
        f"69cab6228fdc-mapped-region-v1:{seed}:{is_query}:{index}:{attempt}".encode()
    ).digest()
    rng = random.Random(token)
    grid = _blank(height, width)

    legend = [(1, 2), (3, 4), (5, 7)]
    legend_token = hashlib.sha256(f"69cab6228fdc-legend-v1:{seed}".encode()).digest()
    legend_rng = random.Random(legend_token)
    columns = legend_rng.sample(range(width), len(legend))
    for column, (source, target) in zip(columns, legend):
        grid[0][column] = source
        grid[1][column] = target

    sep = width // 2
    for br in range(body_h):
        grid[3 + br][sep] = 9

    if is_query:
        k = (1, 2, 3, 2)[index]
    else:
        leading = (1, 2) if seed % 2 == 0 else (2, 1)
        k = (leading + (3, 1, 2, 3))[index]

    # Three raw source-colour components.  Their shapes and attached target
    # tails vary independently of k, while optional colour-2 bridges determine
    # how many regions exist only after source 1 maps to target 2.
    anchors = (1, body_h // 2, body_h - 2)
    c0 = 1 + ((seed + index + attempt) % max(1, min(2, sep - 5)))
    source_lengths = [2 + ((seed + j) % 2) for j in range(3)]
    for j, (row, length) in enumerate(zip(anchors, source_lengths)):
        cells = [(3 + row, c) for c in range(c0, c0 + length)]
        _paint(grid, cells, 1)
        tail_len = 1 + ((seed + index + j + attempt) % 2)
        tails = [(3 + row, c) for c in range(c0 + length, c0 + length + tail_len)]
        _paint(grid, tails, 2)

    variant = (seed + index + attempt) % 2
    connected_pairs: set[int]
    if k == 1:
        connected_pairs = {0, 1}
    elif k == 2:
        connected_pairs = {variant}
    else:
        connected_pairs = set()
    for pair_index in connected_pairs:
        top = anchors[pair_index]
        bottom = anchors[pair_index + 1]
        bridge = [(3 + row, c0) for row in range(top + 1, bottom)]
        _paint(grid, bridge, 2)
        if bridge:
            spur_row, spur_col = bridge[len(bridge) // 2]
            spur_len = 1 + ((seed + index + pair_index) % 2)
            for dc in range(1, spur_len + 1):
                if spur_col + dc < sep and grid[spur_row][spur_col + dc] == 0:
                    grid[spur_row][spur_col + dc] = 2

    # Mapped legend distractors demonstrate that the first transform applies
    # to more than the controller colour.
    distractor_positions = [
        (3, max(0, sep - 2)),
        (3 + body_h - 1, max(0, sep - 3)),
    ]
    for position, color in zip(distractor_positions, (3, 5)):
        r, c = position
        if grid[r][c] == 0:
            grid[r][c] = color

    right_start = sep + 1
    right_width = width - right_start
    bands = ((0, body_h // 3), (body_h // 3, 2 * body_h // 3), (2 * body_h // 3, body_h))
    occupied: set[tuple[int, int]] = set()
    for payload_index, (lo, hi) in enumerate(bands):
        scale = 0 if body_h < 16 else 1 if body_h < 24 else 2
        kind = payload_index + seed + index
        for _ in range(128):
            base = _shape_cells(kind, 0, 0, scale)
            sh = max(r for r, _ in base) + 1
            sw = max(c for _, c in base) + 1
            if hi - lo < sh or right_width < sw:
                scale = max(0, scale - 1)
                continue
            br = lo + rng.randrange(hi - lo - sh + 1)
            bc = right_start + rng.randrange(right_width - sw + 1)
            cells = {(3 + br + r, bc + c) for r, c in _shape_cells(kind, 0, 0, scale)}
            halo = cells | {(r + dr, c + dc) for r, c in cells for dr, dc in DIR4}
            if all(grid[r][c] == 0 for r, c in cells) and not (halo & occupied):
                _paint(grid, sorted(cells), 6)
                occupied |= cells
                break
        else:
            raise RuntimeError(f"could not place payload {payload_index}")

    # Normalize the total visible occupancy within each size profile using
    # inert passthrough colour 8.  In particular, the first two demonstrations
    # have the same size and nuisance statistics while requiring different
    # intermediate values, defeating size/occupancy lookup shortcuts.
    target_nonzero = (height * width) // 3
    candidates = [(r, c) for r in range(3, height) for c in range(width)
                  if c != sep and grid[r][c] == 0]
    rng.shuffle(candidates)
    current_nonzero = sum(value != 0 for row in grid for value in row)
    needed = target_nonzero - current_nonzero
    if needed < 0 or needed > len(candidates):
        raise RuntimeError("occupancy normalization target is infeasible")
    for r, c in candidates[:needed]:
        grid[r][c] = 8

    _validate_scene(grid)
    return grid


def _validate_scene(grid: list[list[int]]) -> None:
    if not grid or not grid[0] or len(grid) > 30 or len(grid[0]) > 30:
        raise ValueError("scene dimensions must be within 1..30")
    if any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("scene must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("scene cells must be exact ARC integers")
    if any(grid[2]):
        raise ValueError("third legend row must remain blank")
    if raw_source_count(grid) != 3:
        raise ValueError("scene must contain exactly three raw source-colour components")
    mapped_region_count(grid)
    if len(_payloads(canonical_transform(grid))) != 3:
        raise ValueError("scene must contain exactly three ordered payloads")


def build_episode(seed: int, mode: str, demos: int, queries: int) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)
    mode = _validate_mode(mode)
    seen: set[tuple[tuple[int, ...], ...]] = set()

    def collect(count: int, is_query: bool) -> list[dict[str, list[list[int]]]]:
        result = []
        for index in range(count):
            for attempt in range(32):
                grid = _scene(seed, index, is_query=is_query, attempt=attempt)
                key = tuple(tuple(row) for row in grid)
                if key not in seen:
                    seen.add(key)
                    result.append({"input": grid, "output": transform(grid, mode)})
                    break
            else:
                raise RuntimeError("bounded sampler exhausted without a distinct input")
        return result

    return {
        "train": collect(demos, False),
        "test": collect(queries, True),
        "program_solution": program_for(mode),
    }
