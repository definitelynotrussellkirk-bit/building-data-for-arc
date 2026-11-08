"""Independent probes for the 51db77fe24c5 square-selector generator.

This file deliberately does not import production helpers.  Reviewer tests and
future audits can therefore compare the generator and Racket authority against a
small, transparent Python oracle and the historically vulnerable shortcut.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Iterable

TASK_ID = "51db77fe24c5"
HOME = Path(__file__).resolve().parents[1]

SQUARE = ((0, 0), (0, 1), (1, 0), (1, 1))
SIZE4_CONTROL = ((0, 1), (0, 2), (1, 0), (1, 1))
LEGACY_DISTRACTOR_MASKS = {
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3)),
    ((0, 0), (1, 0), (1, 1)),
}


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def transforms(mask: Iterable[tuple[int, int]]) -> set[tuple[tuple[int, int], ...]]:
    result = set()
    points = tuple(mask)
    for reflect in (False, True):
        transformed = [(r, -c if reflect else c) for r, c in points]
        for _ in range(4):
            result.add(normalize(transformed))
            transformed = [(c, -r) for r, c in transformed]
    return result


L_TRIOMINOES = transforms(((0, 0), (1, 0), (1, 1)))
NONLEGACY_L_TRIOMINOES = L_TRIOMINOES - LEGACY_DISTRACTOR_MASKS
T_TETROMINOES = transforms(((0, 0), (0, 1), (0, 2), (1, 1)))


def blue_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    """Return 4-connected color-1 components."""
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[set[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def masks(grid: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    return [normalize(cells) for cells in blue_components(grid)]


def oracle_output(grid: list[list[int]]) -> list[list[int]]:
    """Recolor exactly those blue components whose normalized mask is 2x2."""
    out = [list(row) for row in grid]
    for cells in blue_components(grid):
        if normalize(cells) == SQUARE:
            for r, c in cells:
                out[r][c] = 2
    return out


def legacy_memorizer_output(grid: list[list[int]]) -> list[list[int]]:
    """Historical shortcut: memorize three distractors; recolor everything else."""
    out = [list(row) for row in grid]
    for cells in blue_components(grid):
        if normalize(cells) not in LEGACY_DISTRACTOR_MASKS:
            for r, c in cells:
                out[r][c] = 2
    return out


def bbox_2x2_output(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: recolor every component with a 2x2 bounding box."""
    out = [list(row) for row in grid]
    for cells in blue_components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        if max(rows) - min(rows) == 1 and max(cols) - min(cols) == 1:
            for r, c in cells:
                out[r][c] = 2
    return out


def all_blue_output(grid: list[list[int]]) -> list[list[int]]:
    return [[2 if value == 1 else value for value in row] for row in grid]


def size4_output(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: recolor every four-cell blue component."""
    out = [list(row) for row in grid]
    for cells in blue_components(grid):
        if len(cells) == 4:
            for r, c in cells:
                out[r][c] = 2
    return out


def _line_mask(length: int, vertical: bool) -> tuple[tuple[int, int], ...]:
    return tuple((index, 0) if vertical else (0, index) for index in range(length))


def classify_broad_mask(mask: tuple[tuple[int, int], ...]) -> str:
    if mask in {_line_mask(2, False), _line_mask(2, True)}:
        return "domino"
    if mask in {_line_mask(3, False), _line_mask(3, True)}:
        return "line3"
    if mask in {_line_mask(4, False), _line_mask(4, True)}:
        return "line4"
    if mask in T_TETROMINOES:
        return "t4"
    if 5 <= len(mask) <= 8:
        return "polyomino"
    raise ValueError(f"unclassified broad distractor mask: {mask}")


def observed(grid: list[list[int]]) -> dict[str, int | str]:
    found = masks(grid)
    squares = [mask for mask in found if mask == SQUARE]
    nonsquares = [mask for mask in found if mask != SQUARE]
    mandatory = [mask for mask in nonsquares if mask in NONLEGACY_L_TRIOMINOES]
    if len(mandatory) != 1:
        raise ValueError(f"expected one nonlegacy L witness, found {mandatory}")
    controls = [mask for mask in nonsquares if mask == SIZE4_CONTROL]
    if len(controls) != 1:
        raise ValueError(f"expected one size-4 control, found {controls}")
    broad = list(nonsquares)
    broad.remove(mandatory[0])
    broad.remove(controls[0])
    if len(broad) != 1:
        raise ValueError(f"expected one broad distractor, found {broad}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "square_count": len(squares),
        "distractor_kind": classify_broad_mask(broad[0]),
    }


def historical_shortcut_fixture(*, novel: bool) -> list[list[int]]:
    """A small old-grammar lesson, optionally with the missing rotated-L witness."""
    grid = [[0 for _ in range(14)] for _ in range(10)]
    shapes = [
        (SQUARE, (1, 1)),
        (((0, 0), (1, 0), (2, 0), (2, 1)), (1, 5)),
        (((0, 0), (0, 1), (0, 2), (0, 3)), (6, 1)),
        (((0, 0), (1, 0), (1, 1)), (5, 8)),
    ]
    if novel:
        novel_mask = sorted(NONLEGACY_L_TRIOMINOES)[0]
        shapes.append((novel_mask, (1, 11)))
    for mask, (r0, c0) in shapes:
        for dr, dc in mask:
            grid[r0 + dr][c0 + dc] = 1
    return grid
