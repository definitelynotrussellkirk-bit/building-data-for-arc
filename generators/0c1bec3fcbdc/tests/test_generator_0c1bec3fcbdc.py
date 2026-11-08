from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs


mod = importlib.import_module(
    "puzzle_generators.per_puzzle.0c1bec3fcbdc.generator"
)
TASK_ID = "0c1bec3fcbdc"


def test_rule_hash_and_all_canonical_pairs():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    canonical_path = Path(__file__).resolve().parents[1] / "data/canonical/puzzles.jsonl"
    row = next(
        json.loads(line)
        for line in canonical_path.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    source = row["program_solution"]
    expected_hash = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert mod.RULE_HASH == expected_hash == "cbc30556d505"
    for pair in pairs:
        assert mod.self_check(pair["input"]) == []
        assert mod.strict_canonical_like(pair["input"]) == []
        assert mod.rule_mirror(pair["input"]) == pair["output"]


def test_every_exact_override_combination_is_observable():
    sample_index = 0
    for difficulty in ("easy", "medium", "hard"):
        for size_profile in mod.SIZE_PROFILES:
            for n_runs in range(2, 5):
                for scene_profile in mod.SCENE_PROFILES:
                    grid = mod.generate(
                        41,
                        sample_index,
                        difficulty=difficulty,
                        size_profile=size_profile,
                        n_runs=n_runs,
                        scene_profile=scene_profile,
                    )
                    assert mod.self_check(grid) == []
                    assert mod.observe_overrides(grid) == {
                        "size_profile": size_profile,
                        "n_runs": n_runs,
                        "scene_profile": scene_profile,
                    }
                    sample_index += 1


def test_self_check_rejects_structural_impostors():
    all_six = [[6] * 10 for _ in range(8)]
    no_target = [[0] * 10 for _ in range(8)]
    no_target[2][2] = no_target[3][2] = 6
    blue_input = mod.generate(7, 0)
    blue_input[0][0] = 1
    nonlinear = [[0] * 10 for _ in range(8)]
    nonlinear[1][1] = nonlinear[2][1] = nonlinear[3][1] = 6
    nonlinear[3][2] = 6
    mixed_profiles = mod.generate(9, 1, scene_profile="horizontal")
    placed = False
    for col in range(len(mixed_profiles[0])):
        for start in range(len(mixed_profiles) - 2):
            cells = [(row, col) for row in range(start, start + 3)]
            if all(mixed_profiles[row][col] == 0 for row, col in cells):
                for row, col in cells:
                    mixed_profiles[row][col] = 2
                placed = True
                break
        if placed:
            break
    assert placed

    for grid in (all_six, no_target, blue_input, nonlinear, mixed_profiles):
        assert mod.self_check(grid), grid


def test_four_draw_schedule_refutes_all_named_rivals():
    demos = []
    seen_profiles = set()
    for sample_index in range(mod.EXAMPLES_NEEDED):
        grid = mod.generate(73, sample_index, difficulty="medium")
        seen_profiles.add(mod.observe_overrides(grid)["scene_profile"])
        demos.append({"input": grid, "output": mod.rule_mirror(grid)})
    query_grid = mod.generate(73, mod.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_grid, "output": mod.rule_mirror(query_grid)}
    assert seen_profiles == set(mod.SCENE_PROFILES)
    assert mod.lesson_identifiable(demos, query) == []
    for rival in mod.SEMANTIC_RIVALS.values():
        assert any(rival(demo["input"]) != demo["output"] for demo in demos)


def test_determinism_fresh_returns_global_rng_and_band_variation():
    random.seed(12345)
    state = random.getstate()
    first = mod.generate(17, 23, difficulty="easy")
    assert random.getstate() == state
    second = mod.generate(17, 23, difficulty="easy")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9
    assert first != second

    hard = mod.generate(17, 23, difficulty="hard")
    assert hard != second
    assert mod.observe_overrides(hard) == mod.observe_overrides(second)

    with pytest.raises(ValueError):
        mod.generate(1, 2, unknown_axis="typo")
    with pytest.raises(ValueError):
        mod.generate(1, 2, difficulty="extreme")
    with pytest.raises(ValueError):
        mod.generate(1, 2, n_runs=5)
