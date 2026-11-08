"""Focused semantic regressions for transform-analogy generator 99e7ba062bec."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared/runtime"))
GENERATOR_PATH = REPO / "generators/99e7ba062bec/generator.py"
SPEC = importlib.util.spec_from_file_location("generator_99e7ba062bec", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _normalize(grid):
    return [[int(char) for char in row] if isinstance(row, str) else list(row) for row in grid]


def _canonical_pairs():
    with (REPO / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return row["train"] + row["test"]
    raise AssertionError("canonical task missing")


def _pair(seed: int, sample_index: int, difficulty: str = "medium"):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_canonical_pairs_match_first_transform_semantics():
    assert GEN.RULE_HASH == "e3f7daceeedf"
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        grid = _normalize(pair["input"])
        assert GEN.self_check(copy.deepcopy(grid)) == []
        assert GEN.rule_mirror(copy.deepcopy(grid)) == _normalize(pair["output"])


def test_generated_distribution_reaches_the_canonical_profile_and_role_palette():
    component_counts = set()
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(20):
            grid = GEN.generate(31_337, sample_index, difficulty=difficulty)
            analysis = GEN._analyze(grid)
            assert len(grid) == 5
            assert all(len(row) == 17 for row in grid)
            assert len({value for row in grid for value in row}) == 3
            assert analysis["errors"] == []
            assert GEN.self_check(grid) == []
            facts = analysis["facts"]
            assert facts["a_color"] == facts["b_color"]
            assert facts["c_color"] != facts["a_color"]
            assert facts["command"] in GEN.CODES
            assert facts["a_transform_discriminative"]
            assert facts["c_transform_discriminative"]
            component_counts.add(facts["total_components"])
    assert 5 in component_counts
    assert min(component_counts) <= 4
    assert max(component_counts) >= 6


def test_five_demo_lessons_are_serializable_and_seven_samples_cover_all_branches():
    assert GEN.EXAMPLES_NEEDED == 5
    for start in range(10):
        window = [_pair(84_001, start + offset) for offset in range(7)]
        commands = {GEN.observe_overrides(pair["input"])["command"] for pair in window}
        assert commands == set(GEN.CODES)

        demos = window[:5]
        query = _pair(84_001, start + 5)
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_boundary_overrides_are_exact_observable_and_unknown_keys_fail():
    for difficulty in ("easy", "medium", "hard"):
        for command in GEN.CODES:
            for a_count, c_count in ((4, 4), (4, 7), (7, 4), (7, 7)):
                requested = {
                    "command": command,
                    "a_active_count": a_count,
                    "c_active_count": c_count,
                }
                grid = GEN.generate(91, 17, difficulty=difficulty, **requested)
                assert GEN.self_check(grid, meta={"overrides": requested}) == []
                assert GEN.observe_overrides(grid) == requested
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis=1)
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(0, 0, a_active_count=3)
    with pytest.raises(ValueError, match="not in options"):
        GEN.generate(0, 0, command=8)


def test_mutation_fixtures_are_rejected_and_generation_is_pure():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert GEN.self_check(grid), name

    random.seed(991)
    before = random.getstate()
    first = GEN.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(42, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
