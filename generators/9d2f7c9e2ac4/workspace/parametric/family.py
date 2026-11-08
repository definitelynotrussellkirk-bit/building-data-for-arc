"""Constructive native family for H31's rotate-then-use-a-derived-cue lesson.

The two finite settings deliberately share every input.  ``copy_only`` is the
catalog rule: rotate the bottom-left object's bounding box clockwise into the
bottom-right quadrant while preserving its bounding-box offset.  The
``cue_payload`` alternative first forms that exact intermediate, then derives
which cue color touches the newly rotated object and recolors every occurrence
of that cue color with the source color.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import random
from typing import Iterable

MODES = ("copy_only", "cue_payload")
_DELTAS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_TRAIN_SIZES = (9, 10, 12, 14, 18, 26)
_TEST_SIZES = (11, 17, 23, 30)

# Connected, orientation-sensitive polyominoes that fit a 3x3 bounding box.
_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 1), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
    ((0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
)
_EXAMPLE_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (2, 1)),
)


def _rng(*parts: object) -> random.Random:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")
    return random.Random(seed)


def _copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        raise ValueError("cannot normalize an empty cell set")
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _rotate_cw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    shape = _normalize(cells)
    height = 1 + max(r for r, _ in shape)
    return tuple(sorted((c, height - 1 - r) for r, c in shape))


def _split(grid: list[list[int]]) -> tuple[int, int]:
    rows = [r for r, row in enumerate(grid) if row and all(value == 9 for value in row)]
    cols = [
        c
        for c in range(len(grid[0]))
        if all(grid[r][c] == 9 for r in range(len(grid)))
    ]
    if len(rows) != 1 or len(cols) != 1:
        raise ValueError("expected exactly one full color-9 row and column")
    return rows[0], cols[0]


def _bounds(grid: list[list[int]], quadrant: str) -> tuple[int, int, int, int]:
    gr, gc = _split(grid)
    table = {
        "TL": (0, gr, 0, gc),
        "TR": (0, gr, gc + 1, len(grid[0])),
        "BL": (gr + 1, len(grid), 0, gc),
        "BR": (gr + 1, len(grid), gc + 1, len(grid[0])),
    }
    try:
        return table[quadrant]
    except KeyError as exc:
        raise ValueError(f"unknown quadrant: {quadrant}") from exc


def _source_cells(grid: list[list[int]]) -> tuple[int, list[tuple[int, int]]]:
    r0, r1, c0, c1 = _bounds(grid, "BL")
    colored = [
        (grid[r][c], r - r0, c - c0)
        for r in range(r0, r1)
        for c in range(c0, c1)
        if grid[r][c] not in (0, 9)
    ]
    if not colored:
        raise ValueError("bottom-left source is empty")
    colors = {value for value, _, _ in colored}
    if len(colors) != 1:
        raise ValueError("bottom-left source must be monochrome")
    color = colored[0][0]
    return color, [(r, c) for _, r, c in colored]


def _target_cells(grid: list[list[int]]) -> tuple[int, tuple[tuple[int, int], ...]]:
    color, source = _source_cells(grid)
    min_r = min(r for r, _ in source)
    min_c = min(c for _, c in source)
    rotated = _rotate_cw(source)
    br0, br1, bc0, bc1 = _bounds(grid, "BR")
    absolute = tuple((br0 + min_r + r, bc0 + min_c + c) for r, c in rotated)
    if any(not (br0 <= r < br1 and bc0 <= c < bc1) for r, c in absolute):
        raise ValueError("rotated source does not fit in the bottom-right quadrant")
    return color, absolute


def _stage_a(grid: list[list[int]]) -> list[list[int]]:
    color, target = _target_cells(grid)
    out = _copy_grid(grid)
    for r, c in target:
        out[r][c] = color
    return out


def _selected_cue(grid: list[list[int]], stage_a: list[list[int]], source_color: int) -> int:
    r0, r1, c0, c1 = _bounds(grid, "BR")
    candidates: set[int] = set()
    for r in range(r0, r1):
        for c in range(c0, c1):
            value = stage_a[r][c]
            if value in (0, 9, source_color):
                continue
            if any(
                0 <= r + dr < len(stage_a)
                and 0 <= c + dc < len(stage_a[0])
                and stage_a[r + dr][c + dc] == source_color
                for dr, dc in _DELTAS4
            ):
                candidates.add(value)
    if len(candidates) != 1:
        raise ValueError(f"expected one cue adjacent to the rotated intermediate, found {sorted(candidates)}")
    return next(iter(candidates))


def analyze(grid: list[list[int]]) -> dict[str, object]:
    """Expose semantic facts used by audits without exposing generation state."""
    source_color, _ = _source_cells(grid)
    stage_a = _stage_a(grid)
    selected = _selected_cue(grid, stage_a, source_color)
    r0, r1, c0, c1 = _bounds(grid, "BR")
    cue_colors = sorted(
        {
            grid[r][c]
            for r in range(r0, r1)
            for c in range(c0, c1)
            if grid[r][c] not in (0, 9, source_color)
        }
    )
    remote_payload_count = sum(
        value == selected
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if not (r0 <= r < r1 and c0 <= c < c1)
    )
    return {
        "source_color": source_color,
        "selected_cue_color": selected,
        "cue_colors": cue_colors,
        "remote_payload_count": remote_payload_count,
        "stage_a_target_cells": [list(cell) for cell in _target_cells(grid)[1]],
    }


def solve(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    stage_a = _stage_a(grid)
    if mode == "copy_only":
        return stage_a
    info = analyze(grid)
    cue = int(info["selected_cue_color"])
    source = int(info["source_color"])
    return [[source if value == cue else value for value in row] for row in stage_a]


def _paint(
    grid: list[list[int]],
    origin: tuple[int, int],
    cells: Iterable[tuple[int, int]],
    color: int,
) -> None:
    r0, c0 = origin
    for r, c in cells:
        if grid[r0 + r][c0 + c] != 0:
            raise ValueError("attempted to paint over a non-background cell")
        grid[r0 + r][c0 + c] = color


def _empty_cells(
    grid: list[list[int]], bounds: tuple[int, int, int, int]
) -> list[tuple[int, int]]:
    r0, r1, c0, c1 = bounds
    return [(r, c) for r in range(r0, r1) for c in range(c0, c1) if grid[r][c] == 0]


def _construct_pair(seed: int, split_name: str, index: int, size: int, attempt: int) -> list[list[int]]:
    rng = _rng("h31-parametric-v1", seed, split_name, index, attempt)
    grid = [[0 for _ in range(size)] for _ in range(size)]
    middle = size // 2
    for i in range(size):
        grid[middle][i] = 9
        grid[i][middle] = 9

    colors = list(range(1, 9))
    rng.shuffle(colors)
    source_color, example_color = colors[:2]
    cue_palette = sorted(colors[2:5])
    # The selected cue is never the numeric minimum.  This makes the two-demo
    # teaching set reject the fixed-lowest shortcut without changing grammar.
    selected_rank = 1 + ((seed + index + (0 if split_name == "train" else 1)) % 2)
    selected_cue = cue_palette[selected_rank]
    distractor_cues = [color for color in cue_palette if color != selected_cue]

    source_shape = _SHAPES[(seed * 7 + index * 3 + attempt) % len(_SHAPES)]
    example_shape = _EXAMPLE_SHAPES[(seed + index + attempt) % len(_EXAMPLE_SHAPES)]
    capacity = size - middle - 1
    shape_h = 1 + max(r for r, _ in source_shape)
    shape_w = 1 + max(c for _, c in source_shape)
    rotated = _rotate_cw(source_shape)
    rot_h = 1 + max(r for r, _ in rotated)
    rot_w = 1 + max(c for _, c in rotated)
    max_r_off = min(2, capacity - max(shape_h, rot_h))
    max_c_off = min(2, capacity - max(shape_w, rot_w))
    if max_r_off < 0 or max_c_off < 0:
        raise ValueError("grid quadrant is too small for source and rotation")
    row_offset = rng.randrange(max_r_off + 1)
    col_offset = rng.randrange(max_c_off + 1)

    # Worked example in TL/TR.
    ex_rot = _rotate_cw(example_shape)
    ex_h = 1 + max(r for r, _ in example_shape)
    ex_w = 1 + max(c for _, c in example_shape)
    ex_rot_h = 1 + max(r for r, _ in ex_rot)
    ex_rot_w = 1 + max(c for _, c in ex_rot)
    ex_row = rng.randrange(max(1, min(3, middle - max(ex_h, ex_rot_h) + 1)))
    right_capacity = size - middle - 1
    shared_width = min(middle, right_capacity)
    ex_col = rng.randrange(max(1, min(3, shared_width - max(ex_w, ex_rot_w) + 1)))
    _paint(grid, (ex_row, ex_col), example_shape, example_color)
    _paint(grid, (ex_row, middle + 1 + ex_col), ex_rot, example_color)

    # BL source; the canonical stage derives BR from this.
    bl0 = middle + 1
    _paint(grid, (bl0 + row_offset, col_offset), source_shape, source_color)
    _, target = _target_cells(grid)
    target_set = set(target)

    br_bounds = _bounds(grid, "BR")
    br_empty = _empty_cells(grid, br_bounds)
    adjacent = [
        cell
        for cell in br_empty
        if cell not in target_set
        and any((cell[0] + dr, cell[1] + dc) in target_set for dr, dc in _DELTAS4)
    ]
    nonadjacent = [
        cell
        for cell in br_empty
        if cell not in target_set
        and not any((cell[0] + dr, cell[1] + dc) in target_set for dr, dc in _DELTAS4)
    ]
    if not adjacent or len(nonadjacent) < 2:
        raise ValueError("construction lacks cue positions")
    selected_cell = rng.choice(adjacent)
    rng.shuffle(nonadjacent)
    distractor_cells = nonadjacent[:2]
    grid[selected_cell[0]][selected_cell[1]] = selected_cue
    for cell, color in zip(distractor_cells, distractor_cues, strict=True):
        grid[cell[0]][cell[1]] = color

    # Two remote payloads per cue preserve matched grammar while only the
    # intermediate-selected color changes in cue_payload mode.
    upper_empty = _empty_cells(grid, _bounds(grid, "TL")) + _empty_cells(grid, _bounds(grid, "TR"))
    rng.shuffle(upper_empty)
    needed = 2 * len(cue_palette)
    if len(upper_empty) < needed:
        raise ValueError("construction lacks remote-payload positions")
    for color, cells in zip(cue_palette, (upper_empty[i : i + 2] for i in range(0, needed, 2)), strict=True):
        for r, c in cells:
            grid[r][c] = color

    # Assert the intended causal contract at construction time.
    info = analyze(grid)
    if info["selected_cue_color"] != selected_cue or info["remote_payload_count"] < 2:
        raise ValueError("constructed pair does not satisfy cue-payload contract")
    return grid


def _pair(seed: int, split_name: str, index: int, size: int, mode: str, seen: set[str]) -> dict[str, list[list[int]]]:
    for attempt in range(128):
        try:
            grid = _construct_pair(seed, split_name, index, size, attempt)
        except ValueError:
            continue
        fingerprint = json.dumps(grid, separators=(",", ":"))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        return {"input": grid, "output": solve(grid, mode)}
    raise RuntimeError(f"could not construct a distinct lawful {split_name} pair at index {index}")


def generate_episode(seed: int, mode: str, demos: int, queries: int, program_solution: str) -> dict[str, object]:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    seen: set[str] = set()
    train = [
        _pair(seed, "train", index, _TRAIN_SIZES[index], mode, seen)
        for index in range(demos)
    ]
    test = [
        _pair(seed, "test", index, _TEST_SIZES[index], mode, seen)
        for index in range(queries)
    ]
    return {"train": train, "test": test, "program_solution": program_solution}
