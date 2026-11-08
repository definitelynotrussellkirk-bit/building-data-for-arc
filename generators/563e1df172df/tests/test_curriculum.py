"""Regression tests for the endpoint-gap teaching curriculum."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_563e1df172df_under_test", SOURCE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load generator from {SOURCE}")
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _gaps(grid) -> tuple[int, int]:
    red = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    )
    green = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    )
    return abs(red[0] - green[0]), abs(red[1] - green[1])


@pytest.mark.parametrize(
    "difficulty,seed,start,query_index",
    [
        pytest.param("easy", 855653619, 77, 0, id="horizontal-only-survived"),
        pytest.param("hard", 3871913577, 3, 3, id="vertical-only-survived-a"),
        pytest.param("hard", 2768040732, 96, 2, id="vertical-only-survived-b"),
    ],
)
def test_census_rotation_regressions_are_identifiable(
    difficulty: str, seed: int, start: int, query_index: int
) -> None:
    pairs = [_pair(seed, start + offset, difficulty)
             for offset in range(gen.EXAMPLES_NEEDED + 1)]
    query = pairs[query_index]
    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
    assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_sliding_window_has_redundant_two_arm_evidence(difficulty: str) -> None:
    """Any one held-out pair leaves evidence against both arm-only rivals."""
    period = gen.LESSON_SCHEDULE_PERIOD
    for start in range(period):
        grids = [gen.generate(424242, start + offset, difficulty=difficulty)
                 for offset in range(gen.EXAMPLES_NEEDED + 1)]
        gaps = [_gaps(grid) for grid in grids]
        assert sum(row_gap > 1 for row_gap, _ in gaps) >= 2
        assert sum(column_gap > 1 for _, column_gap in gaps) >= 2
        pairs = [
            {"input": grid, "output": gen.rule_mirror(grid)}
            for grid in grids
        ]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_gap_curriculum_retains_edge_cases_and_strong_witnesses(
    difficulty: str,
) -> None:
    gaps = [
        _gaps(gen.generate(9917, sample_index, difficulty=difficulty))
        for sample_index in range(gen.LESSON_SCHEDULE_PERIOD)
    ]
    assert any(row_gap == 1 and column_gap > 1 for row_gap, column_gap in gaps)
    assert any(row_gap > 1 and column_gap == 1 for row_gap, column_gap in gaps)
    assert any(row_gap > 1 and column_gap > 1 for row_gap, column_gap in gaps)


def test_infeasible_unit_arm_falls_back_to_strong_witness() -> None:
    profile = "10x16_northeast_far"
    grid = gen.generate(91, 2, difficulty="easy", scene_profile=profile)
    row_gap, column_gap = _gaps(grid)
    assert row_gap > 1 and column_gap > 1
    assert gen.self_check(
        grid, meta={"overrides": {"scene_profile": profile}}
    ) == []


def test_distance_witnesses_are_declared_positive_branches() -> None:
    """Distance predicates measure scheduled coverage, not rival refutation."""
    distance_witnesses = {"near_distance", "medium_distance", "far_distance"}
    assert distance_witnesses <= set(getattr(gen, "BRANCH_WITNESSES", ()))
    assert distance_witnesses.isdisjoint(gen.WITNESS_RIVALS)
