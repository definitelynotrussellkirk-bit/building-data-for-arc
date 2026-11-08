from __future__ import annotations

import copy
import importlib
import random

from scripts.canonical_profile_gate import canonical_pairs

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.37aaf7d1e52e.generator"
)


def test_canonical_pairs_are_accepted_and_python_mirror_matches():
    pairs = canonical_pairs(GEN.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_all_profiles_honor_min_and_max_dimensions_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index, profile in enumerate(GEN.SCENE_PROFILES):
            for height, width in ((5, 7), (12, 14)):
                grid = GEN.generate(
                    seed=991,
                    sample_index=sample_index,
                    difficulty=difficulty,
                    grid_h=height,
                    grid_w=width,
                    scene_profile=profile,
                )
                expected = {
                    "grid_h": height,
                    "grid_w": width,
                    "scene_profile": profile,
                }
                assert GEN.observe_overrides(grid) == expected
                assert GEN.self_check(grid, meta={"overrides": expected}) == []


def test_every_seven_example_window_covers_all_profiles_and_refutes_rivals():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(14):
            demos = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(777, sample_index, difficulty=difficulty)
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            query_grid = GEN.generate(
                777, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty
            )
            query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []


def test_structural_selfcheck_rejects_targeted_impostors():
    bad = {
        name: GEN.generate(0, 0, texture=name)
        for name in GEN.DEGENERATE_TEXTURES
    }
    for name, grid in bad.items():
        errors = GEN.self_check(grid)
        assert errors, f"diagnostic impostor {name} was accepted"

    valid = GEN.generate(41, 0, scene_profile="single_rect")
    filled = copy.deepcopy(valid)
    analysis = GEN._analyze(filled)
    hole = next(iter(analysis["hole_objects"][0]["holes"][0]))
    filled[hole[0]][hole[1]] = analysis["hole_objects"][0]["color"]
    assert GEN.self_check(filled)


def test_regression_ring_only_shortcut_is_killed_by_irregular_profile():
    grid = GEN.generate(
        123,
        1,
        difficulty="easy",
        grid_h=5,
        grid_w=7,
        scene_profile="single_irregular",
    )
    authoritative = GEN.rule_mirror(grid)
    assert any(value for row in authoritative for value in row)
    assert GEN._rival_ring_centers_only(grid) != authoritative
    assert GEN.SEMANTIC_WITNESSES["irregular_enclosure"](grid)


def test_multi_hole_and_distractor_profiles_kill_center_shortcuts():
    for profile in ("wide_hole", "multi_hole", "with_distractor"):
        index = GEN.SCENE_PROFILES.index(profile)
        grid = GEN.generate(456, index, scene_profile=profile)
        authoritative = GEN.rule_mirror(grid)
        assert GEN._rival_bbox_center_each_object(grid) != authoritative


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(918273)
    before = random.getstate()
    first = GEN.generate(314159, 6, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(314159, 6, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
