from __future__ import annotations

import copy
import importlib
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.72416068b0cf.generator"
)


def test_canonical_inputs_are_in_authority_grammar() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    assert [gen.self_check(pair["input"]) for pair in pairs] == [[]] * 5


def test_override_boundaries_are_exact_and_unknown_keys_fail() -> None:
    boundary_cases = (
        {"grid_h": 9},
        {"grid_h": 12},
        {"grid_w": 11},
        {"grid_w": 15},
        {"n_distractors": 2},
        {"n_distractors": 3},
        {"shape_code": 1},
        {"shape_code": 4},
        {"step1": 1},
        {"step1": 7},
        {"step2": 1},
        {"step2": 7},
        {
            "grid_h": 9,
            "grid_w": 11,
            "n_distractors": 3,
            "shape_code": 4,
            "step1": 7,
            "step2": 1,
        },
    )
    for index, overrides in enumerate(boundary_cases):
        grid = gen.generate(101 + index, 7, difficulty="hard", **overrides)
        observed = gen.observe_overrides(grid)
        for name, value in overrides.items():
            assert observed[name] == value

    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, misspelled_axis=1)


def test_self_check_rejects_targeted_impostors() -> None:
    canonical = copy.deepcopy(canonical_pairs(gen.TASK_ID)[0]["input"])

    full_one_color = [[1, 1, 1] + [0] * 8] + [[1] * 11 for _ in range(8)]
    assert gen.self_check(full_one_color)

    extra_header = copy.deepcopy(canonical)
    extra_header[0][3] = 9
    assert gen.self_check(extra_header)

    invalid_transform = copy.deepcopy(canonical)
    invalid_transform[0][1] = 0
    assert gen.self_check(invalid_transform)

    duplicate_target = copy.deepcopy(canonical)
    for dr, dc in gen.TARGETS[1]:
        duplicate_target[5 + dr][4 + dc] = 9
    assert any("exactly one object" in reason for reason in gen.self_check(duplicate_target))

    merged_objects = copy.deepcopy(canonical)
    merged_objects[2][4] = 3
    assert gen.self_check(merged_objects)


def test_every_four_demo_window_identifies_the_query() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(4):
            for start in range(8):
                demos = []
                for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                    grid = gen.generate(seed, sample_index, difficulty=difficulty)
                    demos.append({"input": grid, "output": gen._solve(grid)})
                query_grid = gen.generate(
                    seed, start + gen.EXAMPLES_NEEDED, difficulty=difficulty
                )
                query = {"input": query_grid, "output": gen._solve(query_grid)}
                assert gen.lesson_identifiable(demos, query) == []


def test_distribution_refutes_largest_and_varies_all_header_codes() -> None:
    draws = [gen.generate(700 + i, i, difficulty="medium") for i in range(80)]
    observed = [gen.observe_overrides(grid) for grid in draws]
    assert {row["shape_code"] for row in observed} == {1, 2, 3, 4}
    assert {code for row in observed for code in (row["step1"], row["step2"])} == set(
        range(1, 8)
    )
    disagreements = sum(gen._rival_largest_object(grid) != gen._solve(grid) for grid in draws)
    assert disagreements >= 50


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(9182)
    before = random.getstate()
    first = gen.generate(17, 23, difficulty="hard")
    after = random.getstate()
    second = gen.generate(17, 23, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
