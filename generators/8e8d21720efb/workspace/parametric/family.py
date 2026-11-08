"""Finite native family for local-cell filtering versus linked-color projection.

Step A discovers which colors participate in at least one same-color cardinal
link.  In ``linked_colors`` mode, step B projects that input-derived color set
across the whole grid, retaining remote occurrences that are not themselves
linked.  The canonical ``local_cells`` mode retains only cells that directly
participate in a link.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import random
from typing import Any


HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text(encoding="utf-8")
LINKED_COLORS_PROGRAM = r'''(rule!
  (let ((linked-colors
         (remove-duplicates
          (for*/list ([r (in-range (rows g))]
                      [c (in-range (cols g))]
                      #:when
                      (let ((v (at g r c)))
                        (and (not (= v 0))
                             (any? (lambda (d)
                                     (let ((nr (+ r (first d)))
                                           (nc (+ c (second d))))
                                       (and (in-bounds? nr nc (rows g) (cols g))
                                            (= (at g nr nc) v))))
                                   cardinal-deltas))))
            (at g r c)))))
    (cellmap g (r c v)
      (if (and (not (= v 0)) (member v linked-colors)) v 0))))'''

PROGRAMS = {
    "local_cells": CANONICAL_PROGRAM,
    "linked_colors": LINKED_COLORS_PROGRAM,
}

# height, width, number of linked colors, number of additional remote active cells
DEMO_SPECS = (
    (7, 8, 1, 8),
    (9, 10, 2, 13),
    (12, 13, 3, 20),
    (8, 14, 2, 18),
    (14, 11, 1, 22),
    (16, 16, 3, 34),
)
QUERY_SPECS = (
    (10, 12, 2, 16),
    (13, 15, 3, 27),
    (18, 17, 1, 38),
    (30, 30, 3, 112),
)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"projection_mode"}:
        raise ValueError("settings must contain exactly projection_mode")
    value = settings["projection_mode"]
    if type(value) is not str or value not in PROGRAMS:
        raise ValueError("projection_mode must be local_cells or linked_colors")
    return value


def _plain_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be a plain integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def dependency_intermediate(grid: list[list[int]]) -> list[int]:
    """Return the sorted colors discovered by step A."""
    height, width = len(grid), len(grid[0])
    linked: set[int] = set()
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 0:
                continue
            if any(
                0 <= row + dr < height
                and 0 <= col + dc < width
                and grid[row + dr][col + dc] == value
                for dr, dc in CARDINAL
            ):
                linked.add(value)
    return sorted(linked)


def local_output(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    return [
        [
            value
            if value != 0
            and any(
                0 <= row + dr < height
                and 0 <= col + dc < width
                and grid[row + dr][col + dc] == value
                for dr, dc in CARDINAL
            )
            else 0
            for col, value in enumerate(values)
        ]
        for row, values in enumerate(grid)
    ]


def linked_colors_output(grid: list[list[int]]) -> list[list[int]]:
    linked = set(dependency_intermediate(grid))
    return [[value if value in linked else 0 for value in row] for row in grid]


def label(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode == "local_cells":
        return local_output(grid)
    if mode == "linked_colors":
        return linked_colors_output(grid)
    raise ValueError("unknown projection mode")


def _neighbors(row: int, col: int, height: int, width: int):
    for dr, dc in CARDINAL:
        rr, cc = row + dr, col + dc
        if 0 <= rr < height and 0 <= cc < width:
            yield rr, cc


def _can_place_isolated(grid: list[list[int]], row: int, col: int, color: int) -> bool:
    if grid[row][col] != 0:
        return False
    height, width = len(grid), len(grid[0])
    return all(grid[rr][cc] != color for rr, cc in _neighbors(row, col, height, width))


def _place_link(grid: list[list[int]], color: int, rng: random.Random) -> None:
    height, width = len(grid), len(grid[0])
    candidates: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if col + 1 < width:
                candidates.append(((row, col), (row, col + 1)))
            if row + 1 < height:
                candidates.append(((row, col), (row + 1, col)))
    rng.shuffle(candidates)
    for first, second in candidates:
        if grid[first[0]][first[1]] == grid[second[0]][second[1]] == 0:
            # Keep the component compact and separated from an existing cell of
            # the same color, so remote occurrences remain genuinely remote.
            cells = {first, second}
            if all(
                grid[rr][cc] != color
                for row, col in cells
                for rr, cc in _neighbors(row, col, height, width)
                if (rr, cc) not in cells
            ):
                for row, col in cells:
                    grid[row][col] = color
                return
    raise RuntimeError("could not place a linked component")


def _place_isolated_many(
    grid: list[list[int]], colors: list[int], count: int, rng: random.Random
) -> None:
    height, width = len(grid), len(grid[0])
    candidates = [(r, c) for r in range(height) for c in range(width)]
    # Put some signal on boundaries first; shuffle the remainder for seed diversity.
    boundary = [
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
        (0, width // 2),
        (height - 1, width // 2),
        (height // 2, 0),
        (height // 2, width - 1),
    ]
    interior = [cell for cell in candidates if cell not in set(boundary)]
    rng.shuffle(boundary)
    rng.shuffle(interior)
    candidates = boundary + interior
    placed = 0
    cursor = 0
    while placed < count and cursor < len(candidates) * max(2, len(colors)):
        row, col = candidates[cursor % len(candidates)]
        color = colors[placed % len(colors)]
        cursor += 1
        if _can_place_isolated(grid, row, col, color):
            grid[row][col] = color
            placed += 1
    if placed != count:
        raise RuntimeError(f"could place only {placed}/{count} isolated active cells")


def _place_decoys(grid: list[list[int]], colors: list[int], rng: random.Random) -> None:
    height, width = len(grid), len(grid[0])
    candidates = [(r, c) for r in range(height - 1) for c in range(width - 1)]
    rng.shuffle(candidates)
    # Same-color diagonal pair: connected under 8-neighborhood but not cardinally.
    diagonal_color = colors[0]
    for row, col in candidates:
        cells = ((row, col), (row + 1, col + 1))
        if all(_can_place_isolated(grid, rr, cc, diagonal_color) for rr, cc in cells):
            for rr, cc in cells:
                grid[rr][cc] = diagonal_color
            break
    else:
        raise RuntimeError("could not place diagonal decoy")

    # Different-color cardinal contact: refutes any-nonzero-neighbor filtering.
    first_color, second_color = colors[1], colors[2]
    rng.shuffle(candidates)
    for row, col in candidates:
        cells = ((row, col, first_color), (row, col + 1, second_color))
        if all(_can_place_isolated(grid, rr, cc, color) for rr, cc, color in cells):
            for rr, cc, color in cells:
                grid[rr][cc] = color
            return
    raise RuntimeError("could not place different-color contact decoy")


def build_input(seed: int, pair_index: int, spec: tuple[int, int, int, int]) -> list[list[int]]:
    height, width, active_count, remote_count = spec
    mixed = (seed * 1_000_003 + pair_index * 97_409 + height * 1_009 + width * 131) % (2**63)
    rng = random.Random(mixed ^ 0x8E8D21720EFB)
    palette = list(range(1, 10))
    rng.shuffle(palette)
    active = palette[:active_count]
    decoys = palette[active_count : active_count + 3]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for color in active:
        _place_link(grid, color, rng)
    _place_isolated_many(grid, active, remote_count, rng)
    _place_decoys(grid, decoys, rng)
    if dependency_intermediate(grid) != sorted(active):
        raise RuntimeError("constructed scene has an invalid linked-color intermediate")
    if local_output(grid) == linked_colors_output(grid):
        raise RuntimeError("constructed scene does not separate the declared settings")
    return grid


def program(settings: dict[str, Any]) -> str:
    return PROGRAMS[_validate_settings(settings)]


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _plain_int("seed", seed, 0, 2**63 - 1)
    _plain_int("demos", demos, 2, 6)
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")
    mode = _validate_settings(settings)
    specs = list(DEMO_SPECS[:demos]) + list(QUERY_SPECS)
    inputs = [build_input(seed, index, spec) for index, spec in enumerate(specs)]
    keys = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    if len(keys) != len(set(keys)):
        raise RuntimeError("episode inputs must be distinct")
    pairs = [
        {"input": deepcopy(grid), "output": label(grid, mode)}
        for grid in inputs
    ]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program(settings),
    }
