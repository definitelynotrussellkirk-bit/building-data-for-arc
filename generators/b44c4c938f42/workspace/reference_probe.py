"""Independent review oracle for b44c4c938f42.

This file deliberately does not import production semantic helpers.  Tests use it
as a second implementation of panel splitting, same-color components, selection,
and greedy conflict-avoiding placement.
"""
from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from types import ModuleType

SHIFTS = (
    (0, 0), (0, -1), (0, 1), (-1, 0), (1, 0),
    (-1, -1), (-1, 1), (1, -1), (1, 1),
    (0, -2), (0, 2), (-2, 0), (2, 0),
)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path: str | None = None) -> ModuleType:
    if path:
        spec = importlib.util.spec_from_file_location("generator_under_test", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load generator from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return importlib.import_module("puzzle_generators.per_puzzle.b44c4c938f42.generator")


def split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    h, w = len(grid), len(grid[0])
    separators = [c for c in range(w) if all(grid[r][c] == 0 for r in range(h))]
    starts = [0] + [c + 1 for c in separators]
    ends = separators + [w]
    return [[row[a:b] for row in grid] for a, b in zip(starts, ends) if a < b]


def components(panel: list[list[int]]) -> list[dict]:
    h, w = len(panel), len(panel[0])
    seen: set[tuple[int, int]] = set()
    out: list[dict] = []
    for r in range(h):
        for c in range(w):
            color = panel[r][c]
            if color == 8 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and panel[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append({"color": color, "cells": tuple(sorted(cells)), "size": len(cells)})
    return out


def _place(objects: list[dict], h: int, w: int, *, shifts=SHIFTS) -> list[list[int]]:
    placed: dict[tuple[int, int], int] = {}
    # Python's stable sort matches the authority's list-order tie behavior on
    # this task's unique-largest lawful domain.
    for obj in sorted(objects, key=lambda item: item["size"], reverse=True):
        for dr, dc in shifts:
            cells = [(r + dr, c + dc) for r, c in obj["cells"]]
            if all(0 <= r < h and 0 <= c < w and (r, c) not in placed for r, c in cells):
                for cell in cells:
                    placed[cell] = obj["color"]
                break
    return [[placed.get((r, c), 8) for c in range(w)] for r in range(h)]


def authority_output(grid: list[list[int]]) -> list[list[int]]:
    panels = split_panels(grid)
    chosen = [max(components(panel), key=lambda obj: obj["size"]) for panel in panels]
    return _place(chosen, len(grid), len(panels[0][0]))


def all_components_output(grid: list[list[int]]) -> list[list[int]]:
    panels = split_panels(grid)
    return _place([obj for panel in panels for obj in components(panel)],
                  len(grid), len(panels[0][0]))


def zero_shift_output(grid: list[list[int]]) -> list[list[int]]:
    panels = split_panels(grid)
    chosen = [max(components(panel), key=lambda obj: obj["size"]) for panel in panels]
    return _place(chosen, len(grid), len(panels[0][0]), shifts=((0, 0),))


def component_sizes_by_panel(grid: list[list[int]]) -> list[list[int]]:
    return [sorted((obj["size"] for obj in components(panel)), reverse=True)
            for panel in split_panels(grid)]


def canonical_profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({v for row in grid for v in row})
