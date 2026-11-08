"""Native two-rule template-copy family for ARC task ff76baf6c2d9.

The input grammar is shared across settings.  Every pair contains one
asymmetric template anchored by color 2 and one asymmetric template anchored by
a non-2 color, so even the minimum two demonstrations expose both branches.
The hidden episode parameter chooses which anchor class horizontally mirrors
its copied template; the canonical setting mirrors color 2 exactly as the
selected Racket authority does.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Callable


TASK_ID = "ff76baf6c2d9"
PARAMETER = "mirror_when"
SETTINGS = ("anchor_is_2", "anchor_is_not_2")
DEFAULT = "anchor_is_2"
ROOT = Path(__file__).resolve().parent
PROGRAM_FILES = {
    "anchor_is_2": ROOT / "canonical.rkt",
    "anchor_is_not_2": ROOT / "mirror_non_two.rkt",
}

TRAIN_PROFILES = (
    ((13, 13), (1, 1)),
    ((16, 17), (2, 1)),
    ((19, 19), (1, 2)),
    ((21, 24), (2, 2)),
    ((24, 24), (3, 2)),
    ((27, 30), (3, 3)),
)
TEST_PROFILES = (
    ((14, 18), (2, 2)),
    ((20, 22), (3, 2)),
    ((26, 29), (2, 3)),
    ((30, 30), (4, 4)),
)

# Every source is 8-connected, has its unique anchor at (1, 1), and is not
# invariant under reflection of column offsets about that anchor.
SOURCE_FORMS = (
    ((1, 1, "A"), (0, 0, "C"), (0, 1, "C"), (1, 0, "C"), (2, 0, "C")),
    ((1, 1, "A"), (0, 1, "C"), (0, 2, "C"), (1, 2, "C"), (2, 2, "C"), (2, 1, "C")),
    ((1, 1, "A"), (0, 0, "C"), (1, 0, "C"), (2, 0, "C"), (2, 1, "C"), (2, 2, "C")),
    ((1, 1, "A"), (0, 2, "C"), (1, 2, "C"), (2, 0, "C"), (2, 1, "C"), (2, 2, "C")),
    ((1, 1, "A"), (0, 0, "C"), (0, 1, "C"), (0, 2, "C"), (1, 0, "C"), (2, 0, "C")),
    ((1, 1, "A"), (0, 1, "C"), (0, 2, "C"), (1, 0, "C"), (2, 0, "C"), (2, 1, "C")),
    ((1, 1, "A"), (0, 0, "C"), (1, 0, "C"), (2, 0, "C"), (2, 1, "C")),
    ((1, 1, "A"), (0, 2, "C"), (1, 2, "C"), (2, 1, "C"), (2, 2, "C")),
)

KING = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _literal_int(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def _setting(settings: dict[str, str]) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError("settings must contain exactly mirror_when")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"mirror_when must be one of {SETTINGS}")
    return value


def native_program(settings: dict[str, str]) -> str:
    return PROGRAM_FILES[_setting(settings)].read_text(encoding="utf-8")


def _grid(value: list[list[int]]) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with literal ARC colors")
    return [row[:] for row in value]


def _components8(grid: list[list[int]]):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[tuple[int, int], ...]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in KING:
                    nxt = current[0] + dr, current[1] + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and grid[nxt[0]][nxt[1]] != 0
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(tuple(sorted(cells)))
    return tuple(components)


def _instructions(grid: list[list[int]]):
    components = _components8(grid)
    singles = tuple(component[0] for component in components if len(component) == 1)
    sources = tuple(component for component in components if len(component) > 1)
    instructions = []
    for source in sources:
        counts = Counter(grid[row][col] for row, col in source)
        unique = [color for color, count in counts.items() if count == 1]
        if len(counts) != 2 or len(unique) != 1:
            raise ValueError("each source must have one unique anchor and one repeated carrier")
        anchor_color = unique[0]
        anchor = next(cell for cell in source if grid[cell[0]][cell[1]] == anchor_color)
        targets = tuple(cell for cell in singles if grid[cell[0]][cell[1]] == anchor_color)
        if not targets:
            raise ValueError("each source needs at least one matching isolated target")
        instructions.append(
            {
                "cells": source,
                "anchor": anchor,
                "anchor_color": anchor_color,
                "targets": targets,
            }
        )
    if len(instructions) != 2:
        raise ValueError("parametric scenes require exactly two source templates")
    claimed = Counter(target for instruction in instructions for target in instruction["targets"])
    if any(claimed[single] != 1 for single in singles):
        raise ValueError("every singleton must select exactly one source")
    return tuple(instructions)


def _apply_with_predicate(grid: list[list[int]], should_mirror: Callable[[int], bool]):
    source = _grid(grid)
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])
    for instruction in _instructions(source):
        anchor_row, anchor_col = instruction["anchor"]
        anchor_color = instruction["anchor_color"]
        for target_row, target_col in instruction["targets"]:
            for source_row, source_col in instruction["cells"]:
                dr = source_row - anchor_row
                dc = source_col - anchor_col
                if (dr, dc) == (0, 0):
                    continue
                row = target_row + dr
                col = target_col + (-dc if should_mirror(anchor_color) else dc)
                if 0 <= row < height and 0 <= col < width:
                    output[row][col] = source[source_row][source_col]
    return output


def apply_rule(grid: list[list[int]], *, mirror_when: str) -> list[list[int]]:
    if mirror_when not in SETTINGS:
        raise ValueError(f"mirror_when must be one of {SETTINGS}")
    if mirror_when == "anchor_is_2":
        predicate = lambda color: color == 2
    else:
        predicate = lambda color: color != 2
    return _apply_with_predicate(grid, predicate)


def apply_rival(grid: list[list[int]], *, mode: str) -> list[list[int]]:
    if mode == "always_preserve":
        return _apply_with_predicate(grid, lambda _color: False)
    if mode == "always_mirror":
        return _apply_with_predicate(grid, lambda _color: True)
    raise ValueError("mode must be always_preserve or always_mirror")


def _transform_form(form, *, flip_rows: bool, flip_cols: bool):
    result = []
    for row, col, role in form:
        if flip_rows:
            row = 2 - row
        if flip_cols:
            col = 2 - col
        result.append((row, col, role))
    return tuple(sorted(result))


def _target_centers(height: int, width: int):
    left = (
        (height - 3, 2),
        (height // 2, 3),
        (height - 3, width // 2 - 2),
        (height // 2 + 3, max(2, width // 3 - 1)),
    )
    right = (
        (height - 3, width - 3),
        (height // 2, width - 4),
        (height - 3, width // 2 + 2),
        (height // 2 + 3, min(width - 3, 2 * width // 3 + 1)),
    )
    return left, right


def _seed(episode_seed: int, split: str, index: int) -> int:
    token = f"{TASK_ID}:mirror-branch-v1:{episode_seed}:{split}:{index}"
    return int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], "big")


def _whole_flip(grid: list[list[int]], vertical: bool, horizontal: bool):
    result = [row[:] for row in grid]
    if vertical:
        result = list(reversed(result))
    if horizontal:
        result = [list(reversed(row)) for row in result]
    return result


def _build_input(episode_seed: int, split: str, index: int) -> list[list[int]]:
    profiles = TRAIN_PROFILES if split == "train" else TEST_PROFILES
    (height, width), target_counts = profiles[index]
    rng = random.Random(_seed(episode_seed, split, index))

    non_two = [1, 3, 4, 5, 6, 7, 8, 9]
    other_anchor, carrier_two, carrier_other = rng.sample(non_two, 3)
    forms = rng.sample(range(len(SOURCE_FORMS)), 2)
    left_form = _transform_form(
        SOURCE_FORMS[forms[0]],
        flip_rows=bool(rng.randrange(2)),
        flip_cols=bool(rng.randrange(2)),
    )
    right_form = _transform_form(
        SOURCE_FORMS[forms[1]],
        flip_rows=bool(rng.randrange(2)),
        flip_cols=bool(rng.randrange(2)),
    )

    # Reverse which row-major source owns color 2 on alternating pairs.  Draw
    # the whole-grid flips first and compensate for the horizontal flip so the
    # *observed* row-major source order, not merely the pre-transform layout,
    # alternates in the minimum two demonstrations.
    whole_vertical = bool(rng.randrange(2))
    whole_horizontal = bool(rng.randrange(2))
    observed_two_on_left = (index + (0 if split == "train" else 1)) % 2 == 0
    two_on_left = observed_two_on_left ^ whole_horizontal
    left_anchor = 2 if two_on_left else other_anchor
    right_anchor = other_anchor if two_on_left else 2
    left_carrier = carrier_two if two_on_left else carrier_other
    right_carrier = carrier_other if two_on_left else carrier_two

    grid = [[0] * width for _ in range(height)]
    specs = (
        (left_form, 1, 1, left_anchor, left_carrier),
        (right_form, 1, width - 4, right_anchor, right_carrier),
    )
    for form, top, left, anchor_color, carrier_color in specs:
        for row, col, role in form:
            grid[top + row][left + col] = anchor_color if role == "A" else carrier_color

    left_targets, right_targets = _target_centers(height, width)
    count_two, count_other = target_counts
    centers_by_anchor = {
        left_anchor: left_targets,
        right_anchor: right_targets,
    }
    counts_by_anchor = {2: count_two, other_anchor: count_other}
    for anchor_color, centers in centers_by_anchor.items():
        for row, col in centers[: counts_by_anchor[anchor_color]]:
            if grid[row][col] != 0:
                raise AssertionError("target center collided with a source")
            grid[row][col] = anchor_color

    grid = _whole_flip(
        grid,
        vertical=whole_vertical,
        horizontal=whole_horizontal,
    )

    facts = scene_facts(grid)
    if (
        facts["source_count"] != 2
        or set(facts["anchor_colors"]) != {2, other_anchor}
        or facts["asymmetric_source_count"] != 2
    ):
        raise AssertionError(f"constructed invalid teaching scene: {facts}")
    canonical = apply_rule(grid, mirror_when="anchor_is_2")
    alternate = apply_rule(grid, mirror_when="anchor_is_not_2")
    if canonical == alternate:
        raise AssertionError("teaching scene does not distinguish the two settings")
    return grid


def scene_facts(grid: list[list[int]]):
    source = _grid(grid)
    instructions = _instructions(source)
    target_counts: dict[int, int] = {}
    asymmetric = 0
    for instruction in instructions:
        color = instruction["anchor_color"]
        target_counts[color] = len(instruction["targets"])
        anchor_row, anchor_col = instruction["anchor"]
        offsets = {
            (row - anchor_row, col - anchor_col)
            for row, col in instruction["cells"]
        }
        mirrored = {(dr, -dc) for dr, dc in offsets}
        asymmetric += offsets != mirrored
    return {
        "source_count": len(instructions),
        "anchor_colors": tuple(instruction["anchor_color"] for instruction in instructions),
        "target_counts": target_counts,
        "asymmetric_source_count": asymmetric,
    }


def native_generate(seed, settings, demos=3, queries=4):
    episode_seed = _literal_int("seed", seed, 0, 2**63 - 1)
    demo_count = _literal_int("demos", demos, 2, 6)
    query_count = _literal_int("queries", queries, 1, 4)
    mirror_when = _setting(settings)

    train = []
    for index in range(demo_count):
        grid = _build_input(episode_seed, "train", index)
        train.append({"input": grid, "output": apply_rule(grid, mirror_when=mirror_when)})
    test = []
    for index in range(query_count):
        grid = _build_input(episode_seed, "test", index)
        test.append({"input": grid, "output": apply_rule(grid, mirror_when=mirror_when)})
    return {
        "train": train,
        "test": test,
        "program_solution": native_program({PARAMETER: mirror_when}),
        "settings": {PARAMETER: mirror_when},
        "seed": episode_seed,
    }


def generate(seed, settings, demos=3, queries=4):
    return native_generate(seed, settings, demos, queries)


def public_turn(episode: dict, query_index: int = 0):
    if type(query_index) is not int or not 0 <= query_index < len(episode["test"]):
        raise ValueError("query_index must select an available query")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_bytes(episode: dict, query_index: int = 0) -> bytes:
    return (
        json.dumps(public_turn(episode, query_index), sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
