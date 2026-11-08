from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "1bfb2ef9ca71"
ROOT = find_root(__file__)
GEN, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def test_rule_pin_and_python_mirror_match_every_canonical_pair():
    assert GEN.RULE_HASH == "a0ec8172be31"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_exact_override_contract_is_small_observable_and_jointly_constructive():
    assert set(GEN.AXES) == {"grid_h", "grid_w", "rectangles"}
    for band in ("easy", "medium", "hard"):
        for height in (8, 12):
            for width in (7, 14):
                for rectangles in (2, 3):
                    grid = GEN.generate(
                        1907,
                        11,
                        difficulty=band,
                        grid_h=height,
                        grid_w=width,
                        rectangles=rectangles,
                    )
                    assert GEN.self_check(grid) == []
                    assert GEN.observe_overrides(grid) == {
                        "grid_h": height,
                        "grid_w": width,
                        "rectangles": rectangles,
                    }


def test_invalid_scalars_and_unknown_overrides_fail_closed():
    invalid_calls = (
        lambda: GEN.generate(True, 0),
        lambda: GEN.generate(0, -1),
        lambda: GEN.generate(0, 0, difficulty=1.0),
        lambda: GEN.generate(0, 0, typo_axis=3),
        lambda: GEN.generate(0, 0, grid_h=True),
        lambda: GEN.generate(0, 0, rectangles=1.0),
    )
    for call in invalid_calls:
        with pytest.raises((TypeError, ValueError)):
            call()


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_three_demo_schedule_refutes_the_canonical_fixed_height_shortcut():
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.SCHEDULE_PROFILES == ("canonical_height3", "height_variation")
    rival = GEN.SEMANTIC_RIVALS["fixed_height_three"]
    witness = GEN.SEMANTIC_WITNESSES["non_three_height"]
    assert GEN.WITNESS_RIVALS["non_three_height"] == ["fixed_height_three"]
    assert GEN.CANONICAL_SHORTCUTS["fixed_height_three"] is rival
    assert GEN.LESSON_COMPETITORS["fixed_height_three"] is rival

    # The shortcut is genuinely plausible: it agrees with every official pair.
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert rival(pair["input"]) == pair["output"]

    # Every production lesson window contains an explicit disagreement witness,
    # while every ordinary scene also covers both diagonal endpoint orientations.
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(731, sample_index, difficulty=band)
                analysis = GEN._analyze(grid)
                assert analysis["errors"] == []
                assert set(analysis["orientations"]) == {"nw_se", "ne_sw"}
                demos.append(_pair(grid))
            assert any(witness(demo["input"]) for demo in demos)
            assert any(rival(demo["input"]) != demo["output"] for demo in demos)
            query = _pair(
                GEN.generate(731, start + GEN.EXAMPLES_NEEDED, difficulty=band)
            )
            assert GEN.lesson_identifiable(demos, query) == []


def test_generation_is_replayable_none_neutral_and_does_not_touch_global_rng():
    import random

    random.seed(9917)
    before = random.getstate()
    first = GEN.generate(41, 7, difficulty="hard")
    assert random.getstate() == before
    assert GEN.generate(41, 7, difficulty="hard") == first
    assert GEN.generate(
        41,
        7,
        difficulty="hard",
        grid_h=None,
        grid_w=None,
        rectangles=None,
    ) == first


def test_schedule_profiles_are_constructive_across_seeds_and_bands():
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            canonical = GEN.generate(seed, 2, difficulty=band)
            varied = GEN.generate(seed, 3, difficulty=band)
            assert GEN.self_check(canonical) == []
            assert GEN.self_check(varied) == []
            assert set(GEN._analyze(canonical)["orientations"]) == {"nw_se", "ne_sw"}
            assert set(GEN._analyze(varied)["orientations"]) == {"nw_se", "ne_sw"}
            assert GEN.SEMANTIC_WITNESSES["non_three_height"](varied)


def test_retained_fixed_height_counterexample_replays_exactly():
    grid = GEN.generate(731, 1, difficulty="medium")
    assert GEN.self_check(grid) == []
    assert GEN.SEMANTIC_WITNESSES["non_three_height"](grid)
    assert GEN.rule_mirror(grid) != GEN.CANONICAL_SHORTCUTS["fixed_height_three"](grid)

