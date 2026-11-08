"""Regression coverage for bbox-top-left versus scan-encounter ordering."""
from __future__ import annotations

from collections import deque
import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("generator_26f313fdf812_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
ROOT = find_root(__file__)


def _scan_encounter_sizes(grid: list[list[int]]) -> list[int]:
    """Return same-color component sizes in row-major first-cell order."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    sizes: list[int] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            size = 0
            while queue:
                current_row, current_col = queue.popleft()
                size += 1
                for row_delta, col_delta in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = (current_row + row_delta, current_col + col_delta)
                    neighbor_row, neighbor_col = neighbor
                    if not (0 <= neighbor_row < height and 0 <= neighbor_col < width):
                        continue
                    if neighbor in seen or grid[neighbor_row][neighbor_col] != color:
                        continue
                    seen.add(neighbor)
                    queue.append(neighbor)
            sizes.append(size)
    return sizes


def _comparison_matrix(values: list[int]) -> list[list[int]]:
    return [
        [1 if left == right else (2 if left > right else 3) for right in values]
        for left in values
    ]


def _scan_encounter_rival(grid: list[list[int]]) -> list[list[int]]:
    return _comparison_matrix(_scan_encounter_sizes(grid))


@pytest.mark.parametrize(
    "profile",
    (
        "c9x9_n3_rank",
        "c10x12_n3_rank",
        "x13x15_n4_rank",
        "x17x19_n5_rank",
    ),
)
def test_ordering_witness_profiles_refute_scan_encounter_order(profile: str):
    for offset in range(24):
        grid = GEN.generate(
            20261011 + offset,
            7 * offset + 3,
            difficulty="medium",
            scene_profile=profile,
        )
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) != _scan_encounter_rival(grid)


def test_canonical_pairs_remain_bound_to_the_pinned_rule():
    assert GEN.RULE_HASH == "80930b679862"
    for pair in canonical_pairs(GEN.TASK_ID, root=ROOT):
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_cyclic_four_demo_window_refutes_declared_query_rivals(band: str):
    profiles = GEN._PROFILES_BY_BAND[band]
    for start in range(len(profiles)):
        pairs = []
        for offset in range(GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(41000 + start, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})

        demos, query = pairs[:-1], pairs[-1]
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            if rival(query["input"]) == query["output"]:
                continue
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_rotation_of_cyclic_five_pair_window_is_identifiable(band: str):
    profiles = GEN._PROFILES_BY_BAND[band]
    for start in range(len(profiles)):
        pairs = []
        for offset in range(GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(52000 + start, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})

        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == [], (
                band,
                start,
                query_index,
            )
