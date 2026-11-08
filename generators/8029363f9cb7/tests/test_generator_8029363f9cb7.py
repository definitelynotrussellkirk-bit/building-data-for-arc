"""Regression and curriculum tests for the 8029363f9cb7 beam generator."""
from __future__ import annotations

import copy
import importlib
import random

import numpy as np
import pytest

from scripts.canonical_profile_gate import canonical_pairs


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.8029363f9cb7.generator"
)


def _canonical_pairs():
    return canonical_pairs("8029363f9cb7")


def _pair(seed: int, sample_index: int, difficulty: str):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_canonical_oracle_parity():
    assert GEN.RULE_HASH == "a08bfbc3cb49"
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_canonical_off_path_mirrors_are_valid_distractors():
    pairs = _canonical_pairs()
    # These two baseline witnesses were rejected by the old all-mirrors-hit
    # checker.  Their unused mirrors are part of the canonical grammar.
    for canonical_index in (1, 2):
        analysis = GEN._analysis(pairs[canonical_index]["input"])
        assert analysis["off_path_mirrors"]
        assert GEN.self_check(pairs[canonical_index]["input"]) == []
        assert GEN.rule_mirror(pairs[canonical_index]["input"]) == pairs[canonical_index]["output"]


def test_every_profile_override_is_exact_observable_and_deterministic():
    for profile_name in GEN.SCENE_PROFILES:
        profile = GEN._PROFILE_BY_NAME[profile_name]
        for seed in (0, 1, 17, 991):
            first = GEN.generate(
                seed,
                7,
                difficulty=profile.band,
                scene_profile=profile_name,
            )
            second = GEN.generate(
                seed,
                7,
                difficulty=profile.band,
                scene_profile=profile_name,
            )
            assert first == second
            assert GEN.observe_overrides(first) == {"scene_profile": profile_name}
            assert GEN.self_check(
                first,
                meta={"overrides": {"scene_profile": profile_name}},
            ) == []


def test_unknown_and_invalid_overrides_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, difficulty="easy", imaginary_axis="x")
    with pytest.raises(ValueError, match="unknown scene_profile"):
        GEN.generate(0, 0, difficulty="easy", scene_profile="not-a-profile")


def test_generation_preserves_process_global_rng_state():
    random.seed(2468)
    np.random.seed(8642)
    py_before = random.getstate()
    np_before = np.random.get_state()
    GEN.generate(91, 3, difficulty="hard")
    assert random.getstate() == py_before
    np_after = np.random.get_state()
    assert np_after[0] == np_before[0]
    assert np.array_equal(np_after[1], np_before[1])
    assert np_after[2:] == np_before[2:]


def test_four_slot_lessons_are_identifiable_across_bands_and_window_starts():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(40):
            for start in range(8):
                demos = [
                    _pair(seed, start + offset, difficulty)
                    for offset in range(GEN.EXAMPLES_NEEDED)
                ]
                query = _pair(seed, start + GEN.EXAMPLES_NEEDED, difficulty)
                assert GEN.lesson_identifiable(demos, query) == []
                analyses = [GEN._analysis(pair["input"]) for pair in demos]
                assert {color for a in analyses for color in a["hit_colors"]} == {3, 4}
                assert {a["stop_kind"] for a in analyses} == {"interior", "border"}
                assert any(a["off_path_mirrors"] for a in analyses)
                assert any(len(a["hit_mirrors"]) >= 2 for a in analyses)


def test_declared_witnesses_really_kill_their_named_rivals():
    hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(30):
            for index in range(4):
                grid = GEN.generate(seed, index, difficulty=difficulty)
                truth = GEN.rule_mirror(grid)
                for witness_name, predicate in GEN.SEMANTIC_WITNESSES.items():
                    if not predicate(grid):
                        continue
                    hits[witness_name] += 1
                    named_rivals = GEN.WITNESS_RIVALS[witness_name]
                    assert any(
                        GEN.SEMANTIC_RIVALS[rival_name](grid) != truth
                        for rival_name in named_rivals
                    )
    assert all(count > 0 for count in hits.values())


def test_structural_mutations_are_rejected_without_overconstraining_distractors():
    grid = GEN.generate(
        7,
        0,
        difficulty="medium",
        scene_profile="medium_outer_three_turn_distractor",
    )
    assert GEN._analysis(grid)["off_path_mirrors"]
    assert GEN.self_check(grid) == []

    no_source = copy.deepcopy(grid)
    sr, sc = GEN._analysis(grid)["source"]
    no_source[sr][sc] = 0
    assert any("source" in error for error in GEN.self_check(no_source))

    broken_frame = copy.deepcopy(grid)
    broken_frame[0][1] = 0
    assert any("border" in error for error in GEN.self_check(broken_frame))

    unsupported = copy.deepcopy(grid)
    candidate = next(
        (row, col)
        for row in range(1, len(grid) - 1)
        for col in range(1, len(grid[0]) - 1)
        if grid[row][col] == 0
    )
    unsupported[candidate[0]][candidate[1]] = 9
    assert any("unexpected input colors" in error for error in GEN.self_check(unsupported))

    no_hit_mirror = copy.deepcopy(grid)
    for row, col, _color in GEN._analysis(grid)["hit_mirrors"]:
        no_hit_mirror[row][col] = 0
    assert GEN.self_check(no_hit_mirror)


def test_profile_schedule_is_complete_and_strictly_anchored():
    for difficulty in ("easy", "medium", "hard"):
        scheduled = [GEN.schedule_profile(123, index, difficulty) for index in range(4)]
        assert scheduled == list(GEN._PROFILES_BY_BAND[difficulty])
        strict = 0
        for index in range(200):
            grid = GEN.generate(1000 + index, index, difficulty=difficulty)
            strict += not GEN.strict_canonical_like(grid)
        assert strict >= 40
