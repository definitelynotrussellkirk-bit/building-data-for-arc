"""Focused regression tests for generator bd24325c2939."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from puzzle_generators.per_puzzle.bd24325c2939 import generator as gen  # noqa: E402


def _canonical_row():
    with (REPO_ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def test_rule_hash_and_all_canonical_pairs():
    row = _canonical_row()
    actual = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == actual
    for pair in list(row["train"]) + list(row["test"]):
        input_grid = copy.deepcopy(pair["input"])
        assert gen.self_check(input_grid) == []
        assert gen.rule_mirror(input_grid) == pair["output"]


def test_exact_override_boundaries_are_observable():
    single_cases = [
        {"grid_h": 9},
        {"grid_h": 15},
        {"grid_w": 9},
        {"grid_w": 15},
        {"component_size": 3},
        {"component_size": 6},
        {"component_palette_size": 2},
        {"component_palette_size": 4},
        {"distractor_count": 0},
        {"distractor_count": 2},
        {"source_quadrant": "upper_left"},
        {"source_quadrant": "lower_right"},
    ]
    for index, case in enumerate(single_cases):
        grid = gen.generate(800 + index, 91, difficulty="easy", **case)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        for key, value in case.items():
            assert observed[key] == value

    full = {
        "grid_h": 9,
        "grid_w": 9,
        "component_size": 6,
        "component_palette_size": 4,
        "distractor_count": 2,
        "source_quadrant": "lower_right",
    }
    grid = gen.generate(901, 37, difficulty="hard", **full)
    assert gen.observe_overrides(grid) == full


def test_incompatible_and_unknown_overrides_reject_loudly():
    with pytest.raises(ValueError, match="exceeds"):
        gen.generate(
            1,
            1,
            component_size=3,
            component_palette_size=4,
        )
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 1, unknown_axis=2)
    with pytest.raises(ValueError, match="unsupported difficulty"):
        gen.generate(1, 1, difficulty="extreme")


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(24325)
    before = random.getstate()
    first = gen.generate(17, 9, difficulty="medium")
    after = random.getstate()
    second = gen.generate(17, 9, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9
    assert first != second
    assert second != gen.generate(18, 9, difficulty="medium")
    assert second != gen.generate(17, 10, difficulty="medium")


def test_sequential_lesson_schedule_exposes_decisive_branches():
    examples = [gen.generate(555, index, difficulty="medium") for index in range(4)]
    facts = [gen._analyze_scene(grid) for grid in examples]
    assert all(not item["errors"] for item in facts)
    assert facts[0]["source_quadrant"] == "upper_left"
    assert facts[1]["distractor_count"] >= 1
    assert facts[2]["source_quadrant"] != "upper_left"
    assert all(gen.rule_mirror(grid) != grid for grid in examples)


def test_targeted_impostors_are_rejected():
    base = gen.generate(
        999,
        6,
        difficulty="hard",
        grid_h=15,
        grid_w=15,
        component_size=5,
        component_palette_size=3,
        distractor_count=1,
        source_quadrant="upper_left",
    )
    facts = gen._analyze_scene(base)
    assert facts["errors"] == []
    mutations = []

    all_background = [[0 for _ in row] for row in base]
    mutations.append(all_background)

    no_pivot = copy.deepcopy(base)
    pr, pc = facts["pivot"]
    no_pivot[pr][pc] = 0
    mutations.append(no_pivot)

    two_pivots = copy.deepcopy(base)
    extra_pivot = next(
        cell
        for cell in sorted(facts["orbit"])
        if cell not in set(facts["main"])
    )
    two_pivots[extra_pivot[0]][extra_pivot[1]] = 8
    mutations.append(two_pivots)

    monochrome = copy.deepcopy(base)
    color = monochrome[facts["main"][0][0]][facts["main"][0][1]]
    for r, c in facts["main"]:
        monochrome[r][c] = color
    mutations.append(monochrome)

    tied_largest = copy.deepcopy(base)
    for r, c in facts["main"]:
        rr, cc = 2 * pr - r, 2 * pc - c
        tied_largest[rr][cc] = color
    mutations.append(tied_largest)

    for mutation in mutations:
        assert gen.self_check(mutation), mutation


def test_absent_feature_recombination_is_distribution_invalid_but_oracle_executes():
    grid = gen.generate(
        333,
        13,
        difficulty="medium",
        distractor_count=0,
        source_quadrant="upper_left",
    )
    facts = gen._analyze_scene(grid)
    used = {value for row in grid for value in row}
    replacement = next(color for color in range(1, 10) if color not in used)
    target = next(cell for cell in sorted(facts["orbit"]) if cell not in set(facts["main"]))
    recombined = copy.deepcopy(grid)
    recombined[target[0]][target[1]] = replacement
    findings = gen.self_check(recombined)
    assert findings
    assert any("answer-orbit" in finding for finding in findings)
    output = gen.rule_mirror(recombined)
    assert output == gen.rule_mirror(grid)


def test_sampled_outputs_match_oracle_grammar():
    distinct_inputs = set()
    distinct_outputs = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for seed in range(30):
            grid = gen.generate(10000 + 100 * band_index + seed, seed * 11 + 5, difficulty=band)
            assert gen.self_check(grid) == []
            output = gen.rule_mirror(grid)
            assert output != grid
            distinct_inputs.add(json.dumps(grid, separators=(",", ":")))
            distinct_outputs.add(json.dumps(output, separators=(",", ":")))
    assert len(distinct_inputs) >= 85
    assert len(distinct_outputs) >= 80
