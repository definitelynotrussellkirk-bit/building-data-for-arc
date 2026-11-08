"""Native parametric family for marker-vector translation.

The canonical setting uses the displacement from marker 1 to marker 2.  The
nearby alternative reverses that relation.  Inputs are matched across settings
and keep every green cell in bounds under both vectors, so demonstrations teach
the hidden direction rather than clipping behavior.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
DIRECTIONS = ("one_to_two", "two_to_one")

_TRAIN_PROFILES = ((9, 11), (10, 12), (12, 14), (14, 16), (18, 20), (22, 24))
_TEST_PROFILES = ((11, 13), (16, 18), (24, 26), (30, 30))
_SHAPES = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
)


def _direction(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"direction"}:
        raise ValueError("settings must contain exactly direction")
    value = settings["direction"]
    if value not in DIRECTIONS:
        raise ValueError(f"direction must be one of {DIRECTIONS}")
    return value


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def program(settings: Any) -> str:
    direction = _direction(settings)
    name = "canonical.rkt" if direction == "one_to_two" else "reverse.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _grid(value: Any) -> list[list[int]]:
    if type(value) is not list or not value or any(type(row) is not list for row in value):
        raise ValueError("grid must be a non-empty list of rows")
    width = len(value[0])
    if width == 0 or any(len(row) != width for row in value):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in value for cell in row):
        raise ValueError("grid cells must be integer ARC colors")
    return deepcopy(value)


def _positions(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def _vector(grid: list[list[int]], direction: str) -> tuple[int, int]:
    ones = _positions(grid, 1)
    twos = _positions(grid, 2)
    if len(ones) != 1 or len(twos) != 1:
        raise ValueError("scene needs exactly one color-1 and one color-2 marker")
    start, end = (ones[0], twos[0]) if direction == "one_to_two" else (twos[0], ones[0])
    return end[0] - start[0], end[1] - start[1]


def transform(value: Any, direction: str) -> list[list[int]]:
    if direction not in DIRECTIONS:
        raise ValueError(f"direction must be one of {DIRECTIONS}")
    grid = _grid(value)
    h, w = len(grid), len(grid[0])
    greens = _positions(grid, 3)
    if not greens:
        raise ValueError("scene needs at least one green cell")
    dr, dc = _vector(grid, direction)
    output = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in greens:
        rr, cc = r + dr, c + dc
        if not (0 <= rr < h and 0 <= cc < w):
            raise ValueError("translated green cell leaves the grid")
        output[rr][cc] = 3
    return output


def green_component_count(value: Any) -> int:
    grid = _grid(value)
    greens = set(_positions(grid, 3))
    count = 0
    while greens:
        count += 1
        stack = [greens.pop()]
        while stack:
            r, c = stack.pop()
            for nbr in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nbr in greens:
                    greens.remove(nbr)
                    stack.append(nbr)
    return count


def scene_invariants(value: Any) -> list[str]:
    try:
        grid = _grid(value)
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    colors = {cell for row in grid for cell in row}
    if not colors <= {0, 1, 2, 3}:
        errors.append(f"unexpected colors: {sorted(colors - {0, 1, 2, 3})}")
    if len(_positions(grid, 1)) != 1:
        errors.append("expected exactly one color-1 marker")
    if len(_positions(grid, 2)) != 1:
        errors.append("expected exactly one color-2 marker")
    if len(_positions(grid, 3)) < 6:
        errors.append("expected at least six green cells")
    if green_component_count(grid) < 2:
        errors.append("expected at least two green components")
    for direction in DIRECTIONS:
        try:
            transform(grid, direction)
        except ValueError as exc:
            errors.append(f"{direction}: {exc}")
    return errors


def _rng(seed: int, split: str, index: int, attempt: int) -> random.Random:
    digest = hashlib.sha256(f"d83b3801c134|{seed}|{split}|{index}|{attempt}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _variant(shape: tuple[tuple[int, int], ...], rng: random.Random) -> tuple[tuple[int, int], ...]:
    cells = list(shape)
    for _ in range(rng.randrange(4)):
        cells = [(c, -r) for r, c in cells]
    if rng.randrange(2):
        cells = [(r, -c) for r, c in cells]
    return _normalize(cells)


def _scene(seed: int, split: str, index: int, attempt: int = 0) -> list[list[int]]:
    profiles = _TRAIN_PROFILES if split == "train" else _TEST_PROFILES
    h, w = profiles[index]
    rng = _rng(seed, split, index, attempt)
    max_delta = 2 if min(h, w) < 12 else (3 if min(h, w) < 20 else 5)
    vectors = [(dr, dc) for dr in range(-max_delta, max_delta + 1)
               for dc in range(-max_delta, max_delta + 1)
               if (dr, dc) != (0, 0) and max(abs(dr), abs(dc)) >= 2]
    rng.shuffle(vectors)

    for dr, dc in vectors:
        margin_r, margin_c = abs(dr), abs(dc)
        inner_h = h - 2 * margin_r
        inner_w = w - 2 * margin_c
        if inner_h < 5 or inner_w < 5:
            continue
        grid = [[0 for _ in range(w)] for _ in range(h)]
        occupied: set[tuple[int, int]] = set()
        forbidden: set[tuple[int, int]] = set()
        target_components = 2 + (1 if h >= 16 else 0) + (1 if h >= 24 else 0) + (1 if h == 30 else 0)
        made = 0
        for component_index in range(target_components):
            base = _SHAPES[(component_index + rng.randrange(len(_SHAPES))) % len(_SHAPES)]
            shape = _variant(base, rng)
            if h >= 24 and component_index == target_components - 1:
                shape = _normalize((*shape, (3, 0), (3, 1), (2, 2)))
            shape_h = 1 + max(r for r, _ in shape)
            shape_w = 1 + max(c for _, c in shape)
            candidates = [(top, left)
                          for top in range(margin_r, h - margin_r - shape_h + 1)
                          for left in range(margin_c, w - margin_c - shape_w + 1)]
            rng.shuffle(candidates)
            placed = False
            for top, left in candidates[:300]:
                cells = {(top + r, left + c) for r, c in shape}
                if cells & forbidden:
                    continue
                occupied |= cells
                for r, c in cells:
                    for rr in range(max(0, r - 1), min(h, r + 2)):
                        for cc in range(max(0, c - 1), min(w, c + 2)):
                            forbidden.add((rr, cc))
                    grid[r][c] = 3
                made += 1
                placed = True
                break
            if not placed:
                break
        if made < target_components or len(occupied) < 6:
            continue

        marker_candidates = [(r, c) for r in range(h) for c in range(w)
                             if 0 <= r + dr < h and 0 <= c + dc < w
                             and (r, c) not in occupied and (r + dr, c + dc) not in occupied]
        rng.shuffle(marker_candidates)
        if not marker_candidates:
            continue
        src = marker_candidates[0]
        dst = (src[0] + dr, src[1] + dc)
        grid[src[0]][src[1]] = 1
        grid[dst[0]][dst[1]] = 2
        if not scene_invariants(grid):
            return grid

    raise RuntimeError(f"could not construct scene for {split}[{index}] attempt {attempt}")


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    direction = _direction(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    seen: set[str] = set()

    def pairs(split: str, count: int) -> list[dict[str, list[list[int]]]]:
        result = []
        for index in range(count):
            for attempt in range(20):
                grid = _scene(seed, split, index, attempt)
                signature = repr(grid)
                if signature not in seen:
                    seen.add(signature)
                    result.append({"input": grid, "output": transform(grid, direction)})
                    break
            else:
                raise RuntimeError("could not make all episode inputs distinct")
        return result

    return {
        "train": pairs("train", demos),
        "test": pairs("test", queries),
        "program_solution": program({"direction": direction}),
    }
