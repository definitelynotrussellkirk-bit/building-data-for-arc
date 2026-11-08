from __future__ import annotations

import copy
import json
import importlib
import random
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
gen = importlib.import_module("puzzle_generators.per_puzzle.a546ac859141.generator")


def _canonical_task():
    path = ROOT / "data" / "canonical" / "puzzles.jsonl"
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task not found")


def test_canonical_inputs_and_outputs_match_python_mirror():
    task = _canonical_task()
    pairs = task["train"] + task["test"]
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("profile", gen.PROFILE_NAMES)
def test_all_exact_overrides_are_observable(band, profile):
    grid = gen.generate(
        1234,
        9,
        difficulty=band,
        grid_h=6,
        grid_w=10,
        multiplicity_profile=profile,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": 6,
        "grid_w": 10,
        "multiplicity_profile": profile,
    }


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)


def test_pre_repair_one_marker_distribution_is_rejected():
    fixture = dict(gen.mutation_fixtures())["pre_repair_one_marker_per_color"]
    findings = gen.self_check(fixture)
    assert findings
    assert any("markers" in finding or "signature" in finding for finding in findings)


def test_every_mutation_fixture_is_rejected():
    for name, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), name


def test_output_erases_border_and_expands_repeated_markers():
    grid = gen.generate(
        91,
        0,
        grid_h=7,
        grid_w=8,
        multiplicity_profile="block_and_single",
    )
    output = gen.rule_mirror(grid)
    assert all(value == 0 for value in output[0])
    assert all(row[0] == 0 for row in output)
    top, left = gen._border_counts(grid)
    expected_nonzero = sum(top[color] * left[color] for color in top)
    actual_nonzero = sum(value != 0 for row in output for value in row)
    assert actual_nonzero == expected_nonzero == 5


def test_four_demo_schedule_refutes_named_competitors():
    demos = []
    for sample_index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(8080, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(8080, gen.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
    for name, competitor in gen.LESSON_COMPETITORS.items():
        assert any(competitor(d["input"]) != d["output"] for d in demos), name


def test_deterministic_fresh_return_and_global_rng_purity():
    random.seed(2026)
    state_before = random.getstate()
    first = gen.generate(314159, 7, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(314159, 7, difficulty="hard")
    assert state_before == state_after
    assert first == second
    assert first is not second
    first[0][0] = 9
    assert second[0][0] == 0


def test_rule_mirror_is_input_pure():
    grid = gen.generate(11, 3, difficulty="easy")
    before = copy.deepcopy(grid)
    gen.rule_mirror(grid)
    assert grid == before
