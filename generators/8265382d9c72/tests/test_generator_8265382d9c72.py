from __future__ import annotations

import random

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "8265382d9c72"
ROOT = find_root(__file__)


def load_generator():
    module, _source, _sha256 = load_selected_generator(TASK_ID, root=ROOT)
    return module


def components(grid: list[list[int]]) -> list[dict]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            stack = [(row, col)]
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            found.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return found


def solve(grid: list[list[int]]) -> list[list[int]]:
    objects = components(grid)
    assert len(objects) == 2
    left, right = sorted(objects, key=lambda obj: obj["bbox"][1])

    def holes(obj: dict) -> int:
        r0, c0, r1, c1 = obj["bbox"]
        return sum(
            grid[row][col] == 0
            for row in range(r0 + 1, r1)
            for col in range(c0 + 1, c1)
        )

    first_count, second_count = holes(left), holes(right)
    output = [[0, 0, 0] for _ in range(3)]
    for index in range(first_count):
        if index < 9:
            output[index // 3][index % 3] = left["color"]
    second_start = (first_count + 2) // 3
    for index in range(second_count):
        row, col = second_start + index // 3, index % 3
        if row < 3:
            output[row][col] = right["color"]
    return output


def test_all_canonical_labels_match_independent_solver_and_inputs_are_accepted():
    generator = load_generator()
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 7
    for pair in pairs:
        assert pair["output"] == solve(pair["input"])
        assert generator.self_check(pair["input"]) == []


def test_ordinary_generation_supports_none_and_medium_and_is_replay_pure():
    generator = load_generator()
    before = random.getstate()
    for difficulty in (None, "medium"):
        for seed in range(12):
            first = generator.generate(seed, seed * 7 + 3, difficulty=difficulty)
            second = generator.generate(seed, seed * 7 + 3, difficulty=difficulty)
            assert first == second
            assert first is not second
            assert generator.self_check(first, difficulty=difficulty) == []
            assert solve(first) != first
    assert random.getstate() == before


def test_self_check_rejects_malformed_or_ambiguous_scenes():
    generator = load_generator()
    valid = generator.generate(4, 9, difficulty="medium")

    blank = [[0 for _ in row] for row in valid]
    one_object = [row[:] for row in valid]
    right_color = max(cell for row in valid for cell in row)
    one_object = [[0 if cell == right_color else cell for cell in row] for row in one_object]
    third_object = [row[:] for row in valid]
    third_object[-1][len(third_object[0]) // 2] = 5
    ragged = [row[:] for row in valid]
    ragged[-1].pop()

    for scene in ([], blank, one_object, third_object, ragged):
        assert generator.self_check(scene)
