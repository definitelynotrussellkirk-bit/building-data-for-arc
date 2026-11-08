"""Deterministic prototype for direct and feedback-routed concentric rings."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

_HOME = Path(__file__).resolve().parent
_PROGRAMS = {
    "direct": (_HOME / "rules" / "direct.rkt").read_text(),
    "feedback_min": (_HOME / "rules" / "feedback_min.rkt").read_text(),
}


def program_for(routing: str) -> str:
    if type(routing) is not str or routing not in _PROGRAMS:
        raise ValueError("routing must be direct or feedback_min")
    return _PROGRAMS[routing]


def _validate_grid(grid: list[list[int]]) -> tuple[int, int]:
    if type(grid) is not list or not grid or any(type(row) is not list for row in grid):
        raise ValueError("grid must be a non-empty list of row lists")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be non-empty and rectangular")
    height = len(grid)
    if not (2 <= height <= 30 and 2 <= width <= 30):
        raise ValueError("grid dimensions must each be in 2..30")
    if height % 2 or width % 2 or height * width > 60:
        raise ValueError("grid must have even dimensions and at most 60 cells")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integers in 0..9")
    return height, width


def _tiles(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    _validate_grid(grid)
    return [
        (grid[r][c], grid[r][c + 1], grid[r + 1][c], grid[r + 1][c + 1])
        for r in range(0, len(grid), 2)
        for c in range(0, len(grid[0]), 2)
    ]


def _rotate_clockwise(tile: tuple[int, int, int, int], turns: int) -> tuple[int, int, int, int]:
    result = tile
    for _ in range(turns % 4):
        tl, tr, bl, br = result
        result = (bl, tl, br, tr)
    return result


def _oriented_tiles(grid: list[list[int]], routing: str) -> list[tuple[int, int, int, int]]:
    source = _tiles(grid)
    if routing == "direct":
        return source
    program_for(routing)
    oriented = [source[0]]
    for tile in source[1:]:
        previous = oriented[-1]
        turns = previous.index(min(previous))
        oriented.append(_rotate_clockwise(tile, turns))
    return oriented


def feedback_trace(grid: list[list[int]]) -> list[int]:
    oriented = _oriented_tiles(grid, "feedback_min")
    return [tile.index(min(tile)) for tile in oriented[:-1]]


def _render_tiles(tiles: Iterable[tuple[int, int, int, int]]) -> list[list[int]]:
    tiles = list(tiles)
    n = 2 * len(tiles)
    result = [[0] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            layer = min(r, c, n - 1 - r, n - 1 - c)
            index = len(tiles) - 1 - layer
            quadrant = 2 * int(r >= n // 2) + int(c >= n // 2)
            result[r][c] = tiles[index][quadrant]
    return result


def render(grid: list[list[int]], routing: str) -> list[list[int]]:
    return _render_tiles(_oriented_tiles(grid, routing))

import hashlib
import random

DEMO_SHAPES = ((4, 4), (4, 6), (6, 4), (6, 6), (4, 8), (8, 4))
QUERY_SHAPES = ((6, 10), (10, 6), (2, 30), (30, 2))


def _integer(value: int, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"84def340ce03-feedback-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, "seed", 0, 2**63 - 1)
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    shapes = DEMO_SHAPES if split == "demo" else QUERY_SHAPES
    _integer(index, "index", 0, len(shapes) - 1)
    h, w = shapes[index]
    rng = _rng(seed, split, index)
    palette = list(range(10))
    rng.shuffle(palette)
    tiles: list[tuple[int, int, int, int]] = []
    for tile_index in range(h * w // 4):
        colors = [palette[(4 * tile_index + offset) % len(palette)] for offset in range(4)]
        minimum, rest = min(colors), [color for color in colors if color != min(colors)]
        rng.shuffle(rest)
        minimum_position = (1 + (tile_index + index + seed) % 3) if tile_index == 0 else rng.randrange(4)
        tile = [None, None, None, None]
        tile[minimum_position] = minimum
        for position, color in zip((p for p in range(4) if p != minimum_position), rest, strict=True):
            tile[position] = color
        tiles.append(tuple(tile))
    if split == "query":
        # Preserve hard full-canvas content while embedding lawful distractors
        # that defeat tile deduplication and uniform-tile omission shortcuts.
        tiles[5] = tiles[4]
        tiles[8] = (palette[0],) * 4
    grid = [[0] * w for _ in range(h)]
    for tile_index, tile in enumerate(tiles):
        block_row, block_col = divmod(tile_index, w // 2)
        for quadrant, color in enumerate(tile):
            dr, dc = divmod(quadrant, 2)
            grid[2 * block_row + dr][2 * block_col + dc] = color
    return grid


def generate_episode(seed: int, routing: str, demos: int = 3, queries: int = 4) -> dict:
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 4, 4)
    program = program_for(routing)
    demonstration_inputs = [sample_input(seed, "demo", index) for index in range(demos)]
    query_inputs = [sample_input(seed, "query", index) for index in range(queries)]
    pairs = [
        {"input": grid, "output": render(grid, routing)}
        for grid in demonstration_inputs + query_inputs
    ]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program,
    }


def _source_min_feedback(grid: list[list[int]]) -> list[list[int]]:
    source = _tiles(grid)
    oriented = [source[0]]
    for index, tile in enumerate(source[1:], start=1):
        previous = source[index - 1]
        oriented.append(_rotate_clockwise(tile, previous.index(min(previous))))
    return _render_tiles(oriented)


def _global_first_feedback(grid: list[list[int]]) -> list[list[int]]:
    source = _tiles(grid)
    turns = source[0].index(min(source[0]))
    return _render_tiles([source[0], *(_rotate_clockwise(tile, turns) for tile in source[1:])])


def _one_step_feedback(grid: list[list[int]]) -> list[list[int]]:
    source = _tiles(grid)
    if len(source) == 1:
        return _render_tiles(source)
    turns = source[0].index(min(source[0]))
    return _render_tiles([source[0], _rotate_clockwise(source[1], turns), *source[2:]])


def _current_tile_feedback(grid: list[list[int]]) -> list[list[int]]:
    source = _tiles(grid)
    return _render_tiles([
        source[0],
        *(_rotate_clockwise(tile, tile.index(min(tile))) for tile in source[1:]),
    ])


RIVALS = {
    "source_min_not_rendered": _source_min_feedback,
    "global_first_offset": _global_first_feedback,
    "one_step_then_direct": _one_step_feedback,
    "current_tile_offset": _current_tile_feedback,
}
