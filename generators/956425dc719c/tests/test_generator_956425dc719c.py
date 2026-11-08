from __future__ import annotations

import copy
import json
from pathlib import Path

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.956425dc719c.generator")


TASK_ID = "956425dc719c"


def _canonical_inputs():
    path = Path("data/canonical/puzzles.jsonl")
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        test = row["test"] if isinstance(row["test"], list) else [row["test"]]
        return [pair["input"] for pair in row["train"]] + [pair["input"] for pair in test]
    raise AssertionError("canonical task missing")


def test_canonical_inputs_are_accepted_and_python_mirror_matches():
    path = Path("data/canonical/puzzles.jsonl")
    row = next(
        json.loads(line)
        for line in path.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    pairs = list(row["train"]) + ([row["test"]] if isinstance(row["test"], dict) else list(row["test"]))
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.solve_python(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_overrides_are_observable_at_boundaries():
    for band in ("easy", "medium", "hard"):
        for profile in gen.SCENE_PROFILES:
            for transform in (0, 7):
                grid = gen.generate(
                    9173,
                    2,
                    difficulty=band,
                    scene_profile=profile,
                    transform=transform,
                )
                assert gen.self_check(grid, difficulty=band) == []
                assert gen.observe_overrides(grid) == {
                    "scene_profile": profile,
                    "transform": transform,
                }


def test_self_check_rejects_four_structural_impostors():
    grid = gen.generate(8101, 0, difficulty="medium", scene_profile="role_alias", transform=0)
    analysis = gen._analyze(grid)
    assert analysis["strict"]

    no_target = copy.deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for obj in gen._components(no_target):
        if obj["color"] == 7 and len(gen._touch_sides(obj["cells"], h, w)) == 1:
            for row, col in obj["cells"]:
                no_target[row][col] = 0
    assert "missing_one_border_target" in gen.self_check(no_target)

    no_retained = copy.deepcopy(grid)
    for obj in gen._components(no_retained):
        if obj["color"] == 7 and len(gen._touch_sides(obj["cells"], h, w)) != 1:
            for row, col in obj["cells"]:
                no_retained[row][col] = 0
    assert "missing_retained_orange_contrast" in gen.self_check(no_retained)

    no_distractor = copy.deepcopy(grid)
    for obj in gen._components(no_distractor):
        if obj["color"] != 7:
            for row, col in obj["cells"]:
                no_distractor[row][col] = 0
    assert "distractor_component_count" in gen.self_check(no_distractor)

    answer_leak = copy.deepcopy(grid)
    answer_leak[0][0] = 5
    assert "gray_answer_leakage" in gen.self_check(answer_leak)


def test_replay_is_deterministic_fresh_and_global_rng_independent():
    import random

    random.seed(314159)
    before = random.getstate()
    first = gen.generate(12345, 7, difficulty="hard")
    after = random.getstate()
    second = gen.generate(12345, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    assert before == after
