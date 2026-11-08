"""Regressions for canonical-refuted shortcuts missing from generated lessons."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

TASK_ID = "678b4a951150"
HERE = Path(__file__).resolve()
HOME = HERE.parents[1]
GENERATOR_PATH = Path(
    os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")
).resolve()
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _target_centers(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row in range(len(grid))
        for col in range(1, len(grid[0]) - 1)
        if grid[row][col - 1 : col + 2] == [7, 0, 7]
    ]


def _has_boundary_row_target(grid: list[list[int]]) -> bool:
    last = len(grid) - 1
    return any(row in (0, last) for row, _ in _target_centers(grid))


def _has_target_row_with_six(grid: list[list[int]]) -> bool:
    return any(6 in grid[row] for row, _ in _target_centers(grid))


def _scheduled_profile_indexes(seed: int, band: str, profile: int) -> list[int]:
    return [
        index
        for index in range(8)
        if GEN.schedule_profile(seed, index, band) == profile
    ]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [0, 1, 477, 921])
def test_profiles_zero_and_two_schedule_boundary_row_witness(seed: int, band: str) -> None:
    assert "interior_rows_only" in GEN.LESSON_COMPETITORS
    for profile in (0, 2):
        for index in _scheduled_profile_indexes(seed, band, profile):
            grid = GEN.generate(seed, index, difficulty=band)
            assert _has_boundary_row_target(grid), (seed, band, profile, index)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [0, 1, 477, 921])
def test_profiles_zero_and_two_schedule_target_row_six_witness(seed: int, band: str) -> None:
    assert "target_rows_without_six" in GEN.LESSON_COMPETITORS
    for profile in (0, 2):
        for index in _scheduled_profile_indexes(seed, band, profile):
            grid = GEN.generate(seed, index, difficulty=band)
            assert _has_target_row_with_six(grid), (seed, band, profile, index)


def test_known_ambiguous_lessons_are_now_identifiable() -> None:
    for seed, band in ((477, "easy"), (921, "easy")):
        pairs = []
        for index in range(5):
            grid = GEN.generate(seed, index, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(pairs[:4], pairs[4]) == []
        for name in ("interior_rows_only", "target_rows_without_six"):
            rival = GEN.LESSON_COMPETITORS[name]
            assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:4]), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [0, 1, 477, 921])
def test_five_pair_lessons_support_every_query_rotation(seed: int, band: str) -> None:
    pairs = []
    for index in range(5):
        grid = GEN.generate(seed, index, difficulty=band)
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert GEN.lesson_identifiable(demos, query) == [], (
            seed,
            band,
            query_index,
            GEN.lesson_identifiable(demos, query),
        )
