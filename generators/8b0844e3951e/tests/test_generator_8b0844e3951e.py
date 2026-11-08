from __future__ import annotations

import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TASK = "8b0844e3951e"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def canonical_inputs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return [pair["input"] for pair in row["train"] + row["test"]]
    raise AssertionError("canonical row missing")


def test_rule_hash_and_all_canonical_inputs():
    assert MODULE.RULE_HASH == "b2abbd0be28f"
    assert len(canonical_inputs()) == 4
    for grid in canonical_inputs():
        assert MODULE.self_check(grid) == []


def test_every_declared_axis_is_exactly_observable_at_boundaries():
    cases = [
        {"grid_h": 3}, {"grid_h": 5}, {"grid_w": 3}, {"grid_w": 5},
        {"mode_color": 1}, {"mode_color": 9},
        {"mode_strength": "clear"}, {"mode_strength": "near_tie"},
        {"background_profile": "absent"},
        {"background_profile": "sparse"},
        {"background_profile": "dominant"},
    ]
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(20):
            for case in cases:
                grid = MODULE.generate(seed, seed * 17, difficulty=difficulty, **case)
                observed = MODULE.observe_overrides(grid)
                for key, value in case.items():
                    assert observed[key] == value


def test_mixed_override_boundaries_work_or_fail_closed_only_for_unknowns():
    for h in (3, 5):
        for w in (3, 5):
            for strength in MODULE.MODE_STRENGTHS:
                for background in MODULE.BACKGROUND_PROFILES:
                    grid = MODULE.generate(
                        91, 17, grid_h=h, grid_w=w, mode_color=9,
                        mode_strength=strength, background_profile=background,
                    )
                    assert MODULE.self_check(grid) == []
                    assert MODULE.observe_overrides(grid) == {
                        "grid_h": h, "grid_w": w, "mode_color": 9,
                        "mode_strength": strength, "background_profile": background,
                    }
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, texture="random")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, difficulty="extreme")


def test_frequency_branches_rebut_shortcuts():
    near = MODULE.generate(10, 20, mode_strength="near_tie", background_profile="absent")
    clear = MODULE.generate(11, 21, mode_strength="clear", background_profile="sparse")
    dominant_zero = MODULE.generate(12, 22, mode_strength="near_tie", background_profile="dominant")
    for grid in (near, clear, dominant_zero):
        assert MODULE.self_check(grid) == []
    assert MODULE.observe_overrides(near)["mode_strength"] == "near_tie"
    counts = Counter(v for row in dominant_zero for v in row)
    nonzero_mode = max((n, c) for c, n in counts.items() if c != 0)
    assert counts[0] > nonzero_mode[0]
    assert MODULE.observe_overrides(dominant_zero)["mode_color"] == nonzero_mode[1]


def test_self_check_rejects_targeted_impostors():
    impostors = [
        [[1]],
        [[1, 1, 2]],
        [[2, 2], [2, 2]],
        [[1, 1, 2], [2, 3, 3], [4, 4, 0]],  # tied nonzero modes
        [[1, 1, 1], [1, 1, 1], [2, 3, 4]],  # overwhelming mode hides comparison
        [[1, 1, 1], [0, 0, 0], [2, 3, 4]],  # zero ties mode
    ]
    for grid in impostors:
        assert MODULE.self_check(grid), grid


def test_deterministic_fresh_and_global_rng_pure():
    random.seed(123456)
    state = random.getstate()
    first = MODULE.generate(77, 99, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(77, 99, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = (first[0][0] + 1) % 10
    assert MODULE.generate(77, 99, difficulty="hard") == second
