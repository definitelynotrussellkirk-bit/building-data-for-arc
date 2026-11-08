from __future__ import annotations

import importlib

import pytest

TASK_ID = "394fc1eaa85e"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
RIVAL_NAME = "unreachable_as_tie"


def _lesson(seed: int, start: int, difficulty: str):
    demos = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_index = start + GEN.EXAMPLES_NEEDED
    query_grid = GEN.generate(seed, query_index, difficulty=difficulty)
    query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
    return demos, query


def test_declares_unreachable_distance_shortcut():
    assert RIVAL_NAME in GEN.LESSON_COMPETITORS


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_three_demo_window_teaches_finite_reachability(difficulty):
    rival = GEN.LESSON_COMPETITORS[RIVAL_NAME]
    for start in range(len(GEN.SCHEDULE_PROFILES)):
        demos, query = _lesson(161803, start, difficulty)
        unreachable_counts = [
            GEN.semantic_observables(pair["input"])["unreachable_open_count"]
            for pair in demos
        ]
        assert any(count > 0 for count in unreachable_counts), (
            start,
            unreachable_counts,
        )
        assert not all(rival(pair["input"]) == pair["output"] for pair in demos)
        assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_query_rotation_keeps_finite_reachability_witness(difficulty):
    rival = GEN.LESSON_COMPETITORS[RIVAL_NAME]
    for start in range(len(GEN.SCHEDULE_PROFILES)):
        pairs = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(271828, sample_index, difficulty=difficulty)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for query_index in range(len(pairs)):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = pairs[query_index]
            unreachable_counts = [
                GEN.semantic_observables(pair["input"])["unreachable_open_count"]
                for pair in demos
            ]
            assert any(count > 0 for count in unreachable_counts), (
                start,
                query_index,
                unreachable_counts,
            )
            assert not all(rival(pair["input"]) == pair["output"] for pair in demos)
            assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    ("seed", "sample_index", "difficulty"),
    [
        (11, 3, "easy"),
        (29, 2, "easy"),
        (101, 10, "medium"),
    ],
)
def test_embedded_island_isolates_only_its_center(seed, sample_index, difficulty):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    profile = GEN.schedule_profile(seed, sample_index, difficulty)
    expected = 1 if profile in ("horizontal_gate", "elbow_gate") else 0
    assert GEN.semantic_observables(grid)["unreachable_open_count"] == expected
