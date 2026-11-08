"""Focused regression tests for generator 092360ee834f."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import random

import pytest

TASK_ID = "092360ee834f"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"generator_{TASK_ID}_{abs(hash(str(GENERATOR_PATH)))}", GENERATOR_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs():
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        test = row["test"] if isinstance(row["test"], list) else [row["test"]]
        return [*row["train"], *test]
    raise AssertionError(TASK_ID)


def test_canonical_inputs_pass_structural_check_and_python_rule_mirror():
    gen = _load_generator()
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"], match_order="first") == pair["output"]
    first = gen.analyze(pairs[0]["input"])
    assert first["target_size"] == 3
    assert first["matching_green_count"] == 2
    assert gen.rule_mirror(pairs[0]["input"], match_order="last") != pairs[0]["output"]


def test_exact_override_boundaries_are_observable_and_strict():
    gen = _load_generator()
    grid = gen.generate(
        71,
        4,
        difficulty="easy",
        grid_h=16,
        grid_w=18,
        target_size=8,
        texture="other_color",
    )
    observed = gen.observe_overrides(grid)
    assert observed == {
        "grid_h": 16,
        "grid_w": 18,
        "target_size": 8,
        "texture": "other_color",
    }
    assert gen.self_check(grid) == []
    analysis = gen.analyze(grid)
    assert analysis["matching_green_count"] == 1
    assert analysis["same_size_other_color_count"] >= 1

    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, target_size=True)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, texture="not-a-texture")
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, __unknown_axis__=1)
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_w=7, target_size=8)


def test_degenerate_controls_realize_their_claimed_rule_outcomes():
    gen = _load_generator()
    blank = lambda grid: [[0] * len(grid[0]) for _ in grid]

    no_header = gen.generate(9, 0, texture="no_header", target_size=4)
    assert gen.analyze(no_header)["target_size"] == 0
    assert gen.rule_mirror(no_header) == blank(no_header)

    no_match = gen.generate(9, 1, texture="no_match", target_size=4)
    facts = gen.analyze(no_match)
    assert facts["target_size"] == 4 and facts["matching_green_count"] == 0
    assert gen.rule_mirror(no_match) == blank(no_match)

    multiple = gen.generate(9, 2, texture="multiple_match", target_size=4)
    facts = gen.analyze(multiple)
    assert facts["matching_green_count"] >= 2
    assert gen.rule_mirror(multiple, match_order="first") != gen.rule_mirror(
        multiple, match_order="last"
    )


def test_ordinary_draws_are_deterministic_fresh_and_preserve_global_rng():
    gen = _load_generator()
    random.seed(8675309)
    state = random.getstate()
    first = gen.generate(83, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(83, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert gen.self_check(first) == []
    first[0][0] = (first[0][0] + 1) % 10
    assert gen.generate(83, 7, difficulty="hard") == second
