"""Focused regression tests for generator 9b028298192f."""
from __future__ import annotations

import importlib
import json
import random
from copy import deepcopy
from pathlib import Path

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.9b028298192f.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    challenges = json.loads((ROOT / "data/raw/arc-agi_training_challenges.json").read_text())
    solutions = json.loads((ROOT / "data/raw/arc-agi_training_solutions.json").read_text())
    task = challenges["cdecee7f"]
    pairs = list(task["train"])
    pairs.extend(
        {"input": row["input"], "output": output}
        for row, output in zip(task["test"], solutions["cdecee7f"])
    )
    return pairs


def test_all_official_pairs_are_accepted_and_solved():
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    observed_profiles = set()
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        observed_profiles.add(gen.observe_overrides(pair["input"])["scene_profile"])
    assert observed_profiles == {
        "canonical_6_distinct",
        "canonical_7_distinct",
        "canonical_9_two_pairs",
        "canonical_9_three_pairs",
    }


def test_every_declared_profile_is_exactly_observable_in_every_band():
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(
                1000 + index,
                40 + index,
                difficulty=band,
                scene_profile=profile,
                grid_h=10 + index % 5,
                grid_w=14 - index % 5,
            )
            observed = gen.observe_overrides(grid)
            assert observed == {
                "grid_h": 10 + index % 5,
                "grid_w": 14 - index % 5,
                "scene_profile": profile,
            }
            assert gen.self_check(grid, difficulty=band, meta={"scene_profile": profile}) == []


def test_unknown_overrides_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, not_a_real_axis=1)


def test_default_schedule_preserves_canonical_support_and_counterexamples():
    for band in ("easy", "medium", "hard"):
        profiles = [
            gen.observe_overrides(gen.generate(2100, index, difficulty=band))["scene_profile"]
            for index in range(80)
        ]
        assert set(profiles) == set(gen.SCENE_PROFILES)
        assert sum(profile in gen._CANONICAL_PROFILES for profile in profiles) == 40
        assert sum(profile == "tie_and_domino_9" for profile in profiles) == 40


def test_named_canonical_shortcuts_are_refuted_only_by_generated_witness():
    pairs = _canonical_pairs()
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name

    witness = gen.generate(3300, 1, scene_profile="tie_and_domino_9")
    answer = gen.rule_mirror(witness)
    assert all(shortcut(witness) != answer for shortcut in gen.CANONICAL_SHORTCUTS.values())
    assert gen.SEMANTIC_WITNESSES["tie_and_domino_refutes_canonical_shortcuts"](witness)


def test_every_three_consecutive_demos_identify_the_query():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            rows = []
            for sample_index in range(start, start + 4):
                grid = gen.generate(4400 + start, sample_index, difficulty=band)
                rows.append({"input": grid, "output": gen.rule_mirror(grid)})
            assert gen.lesson_identifiable(rows[:3], rows[3]) == []


def test_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_negative_recombination_is_rejected():
    grid = gen.generate(5500, 1, scene_profile="tie_and_domino_9")
    facts = gen._analyze(grid)["facts"]
    pair = next(iter(facts["same_color_adjacent_pairs"]))
    mutated = deepcopy(grid)
    used = {value for _, _, value in gen._cells(mutated)}
    replacement = next(color for color in range(1, 10) if color not in used)
    r, c = pair[1]
    mutated[r][c] = replacement
    assert gen.self_check(mutated)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(8675309)
    before = random.getstate()
    first = gen.generate(6600, 17, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(6600, 17, difficulty="hard")
    after = random.getstate()
    assert before == middle == after
    assert first == second
    assert first is not second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_rule_mirror_is_input_pure_and_a_b_a_stable():
    a = gen.generate(7700, 0, scene_profile="canonical_6_distinct")
    b = gen.generate(7701, 1, scene_profile="tie_and_domino_9")
    snapshot = deepcopy(a)
    out_a1 = gen.rule_mirror(a)
    _ = gen.rule_mirror(b)
    out_a2 = gen.rule_mirror(a)
    assert a == snapshot
    assert out_a1 == out_a2
