"""Regression tests for the 2026-10-23 review of generator 6d06c5b96c19."""
from __future__ import annotations

from collections import Counter, deque
from pathlib import Path
from typing import Iterable

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "6d06c5b96c19"
ROOT = find_root(__file__)
gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _payload(grid: list[list[int]]) -> list[list[int]]:
    return [row[1:] for row in grid]


def _cyclic_row_period(rows: list[list[int]]) -> int:
    frozen = [tuple(row) for row in rows]
    for shift in range(1, len(frozen) + 1):
        if all(frozen[index] == frozen[(index + shift) % len(frozen)] for index in range(len(frozen))):
            return shift
    raise AssertionError("full-length period must always exist")


def _nonzero_component_sizes(grid: list[list[int]]) -> list[int]:
    height = len(grid)
    width = len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    sizes: list[int] = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        queue = deque([start])
        remaining.remove(start)
        size = 0
        while queue:
            row, col = queue.popleft()
            size += 1
            for next_row, next_col in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                point = (next_row, next_col)
                if point in remaining and grid[next_row][next_col] == color:
                    remaining.remove(point)
                    queue.append(point)
        sizes.append(size)
    return sizes


def _canonical() -> list[dict[str, object]]:
    return canonical_pairs(TASK_ID, root=ROOT)


def test_seed_requires_a_literal_integer() -> None:
    for invalid in (True, False, 1.0, 1.75, "1"):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(invalid, 0, difficulty="easy")


def test_sample_index_requires_a_nonnegative_literal_integer() -> None:
    for invalid in (True, False, 1.0, 1.75, "1", -1):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(991, invalid, difficulty="easy")


def test_integer_overrides_reject_coercible_nonintegers() -> None:
    controls = {
        "grid_h": 5,
        "grid_w": 6,
        "red_row_index": 0,
        "payload_palette_size": 3,
    }
    for axis, control in controls.items():
        for invalid in (True, False, str(control), float(control), control + 0.75):
            with pytest.raises((TypeError, ValueError)):
                gen.generate(991, 0, difficulty="easy", **{axis: invalid})


def test_one_schedule_profile_emits_aperiodic_duplicate_rows() -> None:
    for difficulty in ("easy", "medium", "hard"):
        grids = [gen.generate(77, index, difficulty=difficulty) for index in range(8)]
        repeated = [
            index
            for index, grid in enumerate(grids)
            if len({tuple(row) for row in _payload(grid)}) < len(grid)
        ]
        assert repeated == [2]
        assert all(_cyclic_row_period(_payload(grid)) == len(grid) for grid in grids)


def test_aperiodic_duplicate_canonical_rows_count_as_semantic_witnesses() -> None:
    duplicate_pair = next(
        pair
        for pair in _canonical()
        if len({tuple(row) for row in _payload(pair["input"])}) < len(pair["input"])
    )
    grid = duplicate_pair["input"]
    assert gen.self_check(grid) == []
    assert _cyclic_row_period(_payload(grid)) == len(grid)
    assert gen.SEMANTIC_WITNESSES["nonzero_marker_changes_row_order"](grid)
    assert gen.SEMANTIC_WITNESSES["downward_direction_is_distinguishable"](grid)


def test_canonical_shortcuts_really_fit_every_canonical_pair() -> None:
    shortcuts = gen.CANONICAL_SHORTCUTS
    assert shortcuts, "declare at least one canonical-fitting shortcut"
    for name, shortcut in shortcuts.items():
        for pair in _canonical():
            assert shortcut(pair["input"]) == pair["output"], name


def test_canonical_shortcut_is_refuted_by_generated_bottom_marker_case() -> None:
    grid = gen.generate(707, 6, difficulty="hard")
    assert gen.observe_overrides(grid)["red_row_index"] == len(grid) - 1
    intended = gen.rule_mirror(grid)
    assert any(shortcut(grid) != intended for shortcut in gen.CANONICAL_SHORTCUTS.values())


def test_every_consecutive_lesson_is_decisive_in_every_band() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(24):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(404, sample_index, difficulty=difficulty)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                404,
                start + gen.EXAMPLES_NEEDED,
                difficulty=difficulty,
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []


def test_canonical_top_and_bottom_profiles_have_only_the_red_singleton() -> None:
    # Canonical payload colors should form multi-cell regions.  The red cue is
    # the only singleton component in these edge-marker profiles, matching the
    # canonical training examples' coarse marker-count support.
    for seed in range(1, 9):
        for sample_index in (0, 6):
            grid = gen.generate(seed, sample_index, difficulty="medium")
            assert Counter(_nonzero_component_sizes(grid))[1] == 1
