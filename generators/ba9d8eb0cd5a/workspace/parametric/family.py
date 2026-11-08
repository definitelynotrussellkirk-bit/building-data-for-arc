"""Native matched-input parametric family for ba9d8eb0cd5a.

The canonical setting stably packs each row to the left.  The alternative then
marks packed cells that have a vertical packed neighbor.  Inputs deliberately
have no pre-pack vertical contacts, so the downstream stage truly consumes the
post-pack intermediate and a mark-before-pack shortcut is visibly wrong.
Python labels are claims; qualification replays every pair through protected
Racket.
"""
from __future__ import annotations

from pathlib import Path
import random

TASK_ID = "ba9d8eb0cd5a"
FINISH_RULES = ("pack_only", "mark_vertical_contacts")
DEFAULT = {"finish_rule": "pack_only"}
HERE = Path(__file__).resolve().parent

# height, width, contiguous active rows, nominal row payload length
_DEMO_PROFILES = (
    (6, 9, 4, 3),
    (8, 12, 5, 4),
    (10, 15, 6, 5),
    (12, 18, 8, 6),
    (16, 22, 10, 7),
    (20, 26, 12, 8),
)
_QUERY_PROFILES = (
    (7, 10, 4, 3),
    (11, 14, 7, 5),
    (18, 22, 12, 8),
    (30, 30, 24, 14),
)
_PALETTE = (1, 3, 4, 5, 6, 7, 8, 9)  # 2 is reserved for the downstream mark.


def _integer(value: int, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _finish_rule(settings) -> str:
    if settings is None:
        return DEFAULT["finish_rule"]
    if type(settings) is not dict or set(settings) != {"finish_rule"}:
        raise ValueError("settings must name exactly finish_rule")
    value = settings["finish_rule"]
    if type(value) is not str or value not in FINISH_RULES:
        raise ValueError("finish_rule must be pack_only or mark_vertical_contacts")
    return value


def program(settings=None) -> str:
    finish_rule = _finish_rule(settings)
    name = "canonical.rkt" if finish_rule == "pack_only" else "mark-vertical-contacts.rkt"
    return (HERE / name).read_text()


def _validate_grid(grid) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be exact ARC colors")
    return len(grid), width


def pack(grid):
    _validate_grid(grid)
    result = []
    for row in grid:
        values = [value for value in row if value != 0]
        result.append(values + [0] * (len(row) - len(values)))
    return result


def intermediate(grid) -> dict:
    packed = pack(grid)
    contacts = [
        [r, c]
        for r, row in enumerate(packed)
        for c, value in enumerate(row)
        if value != 0
        and (
            (r > 0 and packed[r - 1][c] != 0)
            or (r + 1 < len(packed) and packed[r + 1][c] != 0)
        )
    ]
    return {"packed": packed, "vertical_contact_cells": contacts}


def transform(grid, settings=None):
    finish_rule = _finish_rule(settings)
    packed = pack(grid)
    if finish_rule == "pack_only":
        return packed
    height, width = len(packed), len(packed[0])
    return [
        [
            2
            if packed[r][c] != 0
            and (
                (r > 0 and packed[r - 1][c] != 0)
                or (r + 1 < height and packed[r + 1][c] != 0)
            )
            else packed[r][c]
            for c in range(width)
        ]
        for r in range(height)
    ]


def _columns(width: int, kind: int) -> list[int]:
    # Adjacent rows alternate between disjoint column sets.  Kind 0 also
    # supplies an anchored row, avoiding the false invariant that every row
    # starts with a gap.
    if kind == 0:
        return [0] + list(range(3, width, 2))
    return list(range(2, width, 2))


def _sequence(seed: int, split: str, scene_index: int, relative_row: int, length: int) -> list[int]:
    shift = (seed + 5 * scene_index + (0 if split == "train" else 3)) % len(_PALETTE)
    sequence = [
        _PALETTE[(shift + 2 * relative_row + j) % len(_PALETTE)]
        for j in range(length)
    ]
    if relative_row == 0 and length >= 2:
        # A literal, independently checkable sort-then-pack counterexample.
        sequence[0], sequence[1] = max(_PALETTE), min(_PALETTE)
    return sequence


def _scene(seed: int, split: str, index: int):
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    height, width, active_count, nominal_length = profiles[index]
    rng = random.Random(f"{TASK_ID}:{seed}:{split}:{index}")
    start = rng.randint(0, height - active_count)
    grid = [[0] * width for _ in range(height)]

    for relative_row in range(active_count):
        columns = _columns(width, relative_row % 2)
        # The dense stress scene reaches at least 336 foreground cells; smaller
        # scenes vary lengths while retaining at least two cells per active row.
        length = min(nominal_length + ((seed + index + relative_row) % 2), len(columns))
        length = max(2, length)
        sequence = _sequence(seed, split, index, relative_row, length)
        row = start + relative_row
        for column, color in zip(columns[:length], sequence):
            grid[row][column] = color

    # Construction invariants that make the two-stage causal claim falsifiable.
    if any(
        grid[r][c] and grid[r + 1][c]
        for r in range(height - 1)
        for c in range(width)
    ):
        raise AssertionError("pre-pack vertical contact escaped the disjoint-column grammar")
    packed = pack(grid)
    if not any(
        packed[r][c] and packed[r + 1][c]
        for r in range(height - 1)
        for c in range(width)
    ):
        raise AssertionError("packing did not create a vertical contact")
    if transform(grid, {"finish_rule": "pack_only"}) == transform(
        grid, {"finish_rule": "mark_vertical_contacts"}
    ):
        raise AssertionError("scene does not distinguish finish_rule")
    return grid


def inputs(seed: int):
    _integer(seed, 0, 2**63 - 1, "seed")
    return (
        [_scene(seed, "train", index) for index in range(len(_DEMO_PROFILES))],
        [_scene(seed, "test", index) for index in range(len(_QUERY_PROFILES))],
    )


def generate(seed: int, settings=None, demos: int = 3, queries: int = 4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    selected = {"finish_rule": _finish_rule(settings)}
    train_inputs, test_inputs = inputs(seed)

    def pairs(grids):
        return [{"input": grid, "output": transform(grid, selected)} for grid in grids]

    return {
        "train": pairs(train_inputs[:demos]),
        "test": pairs(test_inputs[:queries]),
        "program_solution": program(selected),
        "settings": selected,
    }
