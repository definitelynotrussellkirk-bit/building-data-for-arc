"""Focused regression tests for generator 4d0f228177b0."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
gen = importlib.import_module("puzzle_generators.per_puzzle.4d0f228177b0.generator")


def _canonical_row():
    with (REPO_ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def test_rule_hash_and_all_canonical_pairs():
    row = _canonical_row()
    actual = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == actual
    pairs = list(row["train"]) + list(row["test"])
    assert len(pairs) == 7
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(original) == []
        assert gen.strict_canonical_like(original) == []
        assert gen.rule_mirror(original) == pair["output"]
        assert original == pair["input"]


def test_all_axis_values_are_exact_lawful_and_observable():
    for size in range(9, 12):
        for scenario in gen.SCENARIOS:
            seen = set()
            for template in gen.LAYOUT_TEMPLATES:
                grid = gen.generate(
                    11,
                    7,
                    difficulty="hard",
                    grid_size=size,
                    scenario=scenario,
                    layout_template=template,
                )
                assert gen.self_check(grid) == []
                assert gen.observe_overrides(grid) == {
                    "grid_size": size,
                    "scenario": scenario,
                    "layout_template": template,
                }
                frozen = tuple(map(tuple, grid))
                assert frozen not in seen
                seen.add(frozen)
            assert len(seen) == len(gen.LAYOUT_TEMPLATES)


def test_seven_demo_schedule_covers_the_rule_and_changes_query_placement():
    for band in (None, "easy", "medium", "hard"):
        for start in range(20):
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(71, start + offset, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                71,
                start + gen.EXAMPLES_NEEDED,
                difficulty=band,
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            scenarios = {
                gen._analyse(demo["input"])["facts"]["scenario"] for demo in demos
            }
            assert scenarios == set(gen.SCENARIOS)
            assert {len(demo["input"]) for demo in demos} == {9, 10, 11}
            assert all(query_grid != demo["input"] for demo in demos)
            assert gen.lesson_identifiable(demos, query) == []


def test_named_witnesses_refute_their_named_rivals():
    grids = [gen.generate(5, index) for index in range(84)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        hits = [grid for grid in grids if witness(grid)]
        assert hits, witness_name
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            rival = gen.SEMANTIC_RIVALS[rival_name]
            assert all(rival(grid) != gen.rule_mirror(grid) for grid in hits), (
                witness_name,
                rival_name,
            )


def test_self_check_rejects_targeted_rule_hiding_mutations():
    valid = gen.generate(
        1,
        1,
        grid_size=11,
        scenario="all_four_cross_six",
        layout_template="p05",
    )
    assert gen.self_check(valid) == []

    duplicate = copy.deepcopy(valid)
    duplicate[10][10] = 6

    wrong_two_offset = copy.deepcopy(valid)
    row2, col2 = gen._analyse(valid)["facts"]["cues"][2]
    wrong_two_offset[row2][col2] = 0
    wrong_two_offset[row2][col2 - 1] = 2

    right_side_became_center = copy.deepcopy(valid)
    row3, col3 = gen._analyse(valid)["facts"]["cues"][3]
    right_side_became_center[row3][col3] = 0
    right_side_became_center[row3][col2 - 1] = 3

    clipped = gen.generate(1, 1, texture="clipped_six")
    unexpected = gen.generate(1, 1, texture="unexpected_color")

    for mutated in (
        duplicate,
        wrong_two_offset,
        right_side_became_center,
        clipped,
        unexpected,
    ):
        assert gen.self_check(mutated)


def test_determinism_fresh_returns_global_rng_and_invalid_calls():
    random.seed(42281770)
    state = random.getstate()
    first = gen.generate(17, 9, difficulty="medium")
    second = gen.generate(17, 9, difficulty="medium")
    assert random.getstate() == state
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert first != second
    assert second != gen.generate(17, 10, difficulty="medium")

    with pytest.raises(ValueError):
        gen.generate(1, 1, difficulty="extreme")
    with pytest.raises(ValueError):
        gen.generate(1, 1, scenario="single_two")
    with pytest.raises(ValueError):
        gen.generate(1, 1, grid_size=12)
    with pytest.raises(ValueError):
        gen.generate(1, 1, layout_template="p12")
    with pytest.raises(ValueError):
        gen.generate(1, 1, typo_axis=True)
    with pytest.raises(ValueError):
        gen.generate(1, 1, texture="clipped_six", scenario="single_six")
