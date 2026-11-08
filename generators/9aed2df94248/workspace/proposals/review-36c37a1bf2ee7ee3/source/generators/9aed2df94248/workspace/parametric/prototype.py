#!/usr/bin/env python3
"""Episode-fixed forward/reverse transform analogies for 9aed2df94248."""
from __future__ import annotations

import hashlib
import random
from pathlib import Path
from typing import Iterable

TASK_ID = "9aed2df94248"
DIRECTIONS = ("forward", "reverse")
DEFAULT_DIRECTION = "forward"
DEFAULT_DEMOS = 3
DEFAULT_QUERIES = 4
HOME = Path(__file__).resolve().parent
CANONICAL_PATH = HOME / "canonical.rkt"


def _validate_direction(direction: str) -> None:
    if type(direction) is not str or direction not in DIRECTIONS:
        raise ValueError(f"direction must be one of {DIRECTIONS}, got {direction!r}")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact nonnegative integer below 2**63")


def canonical_source() -> str:
    source = CANONICAL_PATH.read_text(encoding="utf-8")
    if not source.strip():
        raise ValueError("canonical.rkt is empty")
    return source


def program_for(direction: str = DEFAULT_DIRECTION) -> str:
    """Return exact Racket for one analogy direction."""
    _validate_direction(direction)
    source = canonical_source()
    if direction == "forward":
        return source
    needle = "(apply-transform c (if (eq? cmd #f) 0 cmd))"
    if source.count(needle) != 1:
        raise ValueError("canonical source no longer matches the guarded final-expression template")
    replacement = """(if (eq? cmd #f)
          c
          (if (= cmd 1)
              (rotate-cw (rotate-cw (rotate-cw c)))
              (apply-transform c cmd)))"""
    return source.replace(needle, replacement, 1)


def grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _validate_grid(grid: list[list[int]], *, name: str = "grid") -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError(f"{name} must be a nonempty rectangular grid")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError(f"{name} must contain exact integer colors 0..9")
    if len(grid) > 30 or width > 30:
        raise ValueError(f"{name} must fit inside 30x30")
    return len(grid), width


def rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid[::-1]]


def apply_transform(grid: list[list[int]], code: int) -> list[list[int]]:
    """Apply the canonical six transforms plus ccw/anti-transpose diagnostics."""
    _validate_grid(grid)
    if type(code) is not int or not 0 <= code <= 7:
        raise ValueError("transform code must be an exact integer in 0..7")
    if code == 0:
        return [row[:] for row in grid]
    if code == 1:
        return rotate_cw(grid)
    if code == 2:
        return rotate_180(grid)
    if code == 3:
        return transpose(grid)
    if code == 4:
        return flip_lr(grid)
    if code == 5:
        return flip_ud(grid)
    if code == 6:
        return rotate_ccw(grid)
    return rotate_180(transpose(grid))


def inverse_code(code: int) -> int:
    if type(code) is not int or not 0 <= code <= 7:
        raise ValueError("transform code must be an exact integer in 0..7")
    return 6 if code == 1 else 1 if code == 6 else code


def _crop(grid: list[list[int]]) -> list[list[int]]:
    _validate_grid(grid)
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if not cells:
        raise ValueError("panel has no content")
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


def split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    h, w = _validate_grid(grid)
    occupied = [any(grid[r][c] != 0 for r in range(h)) for c in range(w)]
    runs: list[tuple[int, int]] = []
    start = None
    for c, present in enumerate(occupied + [False]):
        if present and start is None:
            start = c
        elif not present and start is not None:
            runs.append((start, c))
            start = None
    if len(runs) != 3:
        raise ValueError(f"expected exactly three content panels, got {len(runs)}")
    return [_crop([row[c1:c2] for row in grid]) for c1, c2 in runs]


def infer_transform(grid: list[list[int]]) -> int:
    a, b, _ = split_panels(grid)
    matches = [code for code in range(6) if apply_transform(a, code) == b]
    if len(matches) != 1:
        raise ValueError(f"expected one canonical A->B transform, got {matches}")
    return matches[0]


def solve_python(grid: list[list[int]], *, direction: str = DEFAULT_DIRECTION) -> list[list[int]]:
    _validate_direction(direction)
    _, _, c = split_panels(grid)
    code = infer_transform(grid)
    return apply_transform(c, code if direction == "forward" else inverse_code(code))


def _all8(shape: list[list[int]]) -> set[tuple[tuple[int, ...], ...]]:
    return {grid_key(apply_transform(shape, code)) for code in range(8)}


def _shape(rng: random.Random, h: int, w: int, *, density: float) -> list[list[int]]:
    if not (2 <= h <= 20 and 2 <= w <= 20 and 0.2 <= density <= 0.85):
        raise ValueError("unsupported shape request")
    target = max(h + w - 1, min(h * w - 1, round(h * w * density)))
    for _ in range(96):
        cells = {(0, c) for c in range(w)} | {(r, 0) for r in range(h)}
        while len(cells) < target:
            frontier = {
                (nr, nc)
                for r, c in cells
                for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1))
                if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in cells
            }
            if not frontier:
                break
            cells.add(rng.choice(sorted(frontier)))
        shape = [[1 if (r, c) in cells else 0 for c in range(w)] for r in range(h)]
        if len(_all8(shape)) == 8:
            return shape
    # Fully asymmetric, connected and row/column-complete; used only if a dense
    # request repeatedly lands on a symmetry.
    fallback = [[0 for _ in range(w)] for _ in range(h)]
    for c in range(w):
        fallback[0][c] = 1
    for r in range(h):
        fallback[r][0] = 1
    if h > 2 and w > 2:
        fallback[1][1] = 1
        fallback[h - 1][1] = 1
    if len(_all8(fallback)) != 8:
        # Small dimensions can make the generic fallback symmetric.
        return [[1, 1, 1], [1, 0, 0]]
    return fallback


def _paint(shape: list[list[int]], color: int) -> list[list[int]]:
    return [[color if value else 0 for value in row] for row in shape]


def _rng(seed: int, role: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{role}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _code_for(role: str, index: int) -> int:
    if role == "train":
        return (1, 4, 3, 2, 5, 1)[index]
    return (3, 1, 5, 2)[index]


def _dimensions(seed: int, role: str, index: int, code: int, stress: bool) -> tuple[int, int, int, int, float]:
    if stress:
        return 12, 8, 12, 8, 0.62
    salt = seed + index * 7 + (0 if role == "train" else 31)
    a_h = 3 + salt % 4
    a_w = 3 + (salt // 3) % 4
    c_h = 3 + (salt // 5 + 1) % 4
    c_w = 3 + (salt // 7 + 2) % 4
    # Quarter-turn/transpose samples can consume extra horizontal space after A->B.
    while a_w + (a_h if code in (1, 3) else a_w) + c_w > 22:
        c_w = max(3, c_w - 1)
        a_w = max(3, a_w - 1)
        a_h = max(3, a_h - 1)
    return a_h, a_w, c_h, c_w, 0.48 + 0.04 * (index % 3)


def _compose(panels: list[list[list[int]]], rng: random.Random, *, stress: bool) -> list[list[int]]:
    heights = [len(panel) for panel in panels]
    widths = [len(panel[0]) for panel in panels]
    content_width = sum(widths)
    if stress:
        total_h = total_w = 30
    else:
        total_h = min(30, max(heights) + 2 + rng.randrange(4))
        total_w = min(30, content_width + 4 + rng.randrange(4))
    if content_width + 2 > total_w or max(heights) > total_h:
        raise ValueError("panels do not fit requested canvas")

    # Two mandatory separators; distribute all remaining blank columns among
    # outer margins and the separators without changing the three-panel parse.
    blanks = total_w - content_width
    slots = [0, 1, 1, 0]  # left, gap1, gap2, right
    for _ in range(blanks - 2):
        slots[rng.randrange(4)] += 1
    left, gap1, gap2, _right = slots

    if stress:
        offsets = [0, (total_h - heights[1]) // 2, total_h - heights[2]]
    else:
        offsets = [rng.randrange(total_h - height + 1) for height in heights]
    grid = [[0 for _ in range(total_w)] for _ in range(total_h)]
    col = left
    for idx, panel in enumerate(panels):
        for r, row in enumerate(panel):
            for c, value in enumerate(row):
                if value:
                    grid[offsets[idx] + r][col + c] = value
        col += widths[idx]
        if idx == 0:
            col += gap1
        elif idx == 1:
            col += gap2
    return grid


def build_input(seed: int, *, role: str, index: int) -> list[list[int]]:
    _validate_seed(seed)
    if role not in {"train", "test"}:
        raise ValueError("role must be train or test")
    limit = 6 if role == "train" else 4
    if type(index) is not int or not 0 <= index < limit:
        raise ValueError("sample index is out of range")
    code = _code_for(role, index)
    stress = role == "test" and index == 3
    rng = _rng(seed, role, index)
    a_h, a_w, c_h, c_w, density = _dimensions(seed, role, index, code, stress)
    a = _shape(rng, a_h, a_w, density=density)
    c = _shape(rng, c_h, c_w, density=min(0.78, density + 0.05))
    color = 1 + rng.randrange(9)
    a = _paint(a, color)
    b = apply_transform(a, code)
    c = _paint(c, color)
    grid = _compose([a, b, c], rng, stress=stress)
    if infer_transform(grid) != code:
        raise AssertionError("constructed analogy does not preserve its intended transform")
    return grid


def generate_claims(
    seed: int,
    *,
    direction: str = DEFAULT_DIRECTION,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
) -> dict:
    _validate_seed(seed)
    _validate_direction(direction)
    _validate_counts(demos, queries)
    train_inputs = [build_input(seed, role="train", index=i) for i in range(demos)]
    test_inputs = [build_input(seed, role="test", index=i) for i in range(queries)]
    all_inputs = train_inputs + test_inputs
    if len({grid_key(grid) for grid in all_inputs}) != len(all_inputs):
        raise AssertionError("episode inputs must be distinct")
    pair = lambda grid: {"input": grid, "output": solve_python(grid, direction=direction)}
    return {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": program_for(direction),
    }
