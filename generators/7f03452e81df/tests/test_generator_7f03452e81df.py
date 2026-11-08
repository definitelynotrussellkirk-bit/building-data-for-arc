from __future__ import annotations

import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
gen, _, _ = load_selected_generator("7f03452e81df", root=ROOT)


def _episode(seed: int, start: int, band: str):
    pairs = []
    for offset in range(gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    return pairs[:-1], pairs[-1]


def test_canonical_pairs_are_accepted_and_match_every_selected_authority_shortcut():
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        # These are genuinely canonical-ambiguous rivals; generated witnesses
        # below, not the canonical pairs, must refute them.
        assert all(
            rival(pair["input"]) == pair["output"]
            for rival in gen.CANONICAL_SHORTCUTS.values()
        )


def test_each_profile_is_observable_and_kills_its_named_shortcut():
    killing_rival = {
        "canonical_anchor": None,
        "repeated_sparse": "first_object",
        "nested_crop": "selected_object_mask",
        "tie_row": "leftmost_minimum",
        "tie_col": "rightmost_minimum",
    }
    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(731, index, difficulty="medium", scene_profile=profile)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert len({value for row in grid for value in row}) == 4
        rival_name = killing_rival[profile]
        if rival_name is not None:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != gen.rule_mirror(grid)


def test_repeated_profile_separately_refutes_scan_bbox_and_frequency_rules():
    grid = gen.generate(991, 0, scene_profile="repeated_sparse")
    truth = gen.rule_mirror(grid)
    for rival_name in ("first_object", "smallest_bbox_area", "least_frequent_color"):
        assert gen.SEMANTIC_RIVALS[rival_name](grid) != truth
    fired = {name for name, pred in gen.SEMANTIC_WITNESSES.items() if pred(grid)}
    assert {
        "target_not_first_scan",
        "cell_count_beats_bbox_area",
        "component_count_beats_color_frequency",
    } <= fired


def test_every_residue_class_five_demo_window_is_identifiable_in_every_band():
    for band in ("easy", "medium", "hard"):
        for start in range(len(gen.SCENE_PROFILES)):
            demos, query = _episode(seed=20260728 + start, start=start, band=band)
            assert {gen.observe_overrides(pair["input"])["scene_profile"] for pair in demos} == set(
                gen.SCENE_PROFILES
            )
            assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_four_targeted_rule_hiding_impostors():
    blank = [[0] * 6 for _ in range(6)]
    single = [[0] * 6 for _ in range(6)]
    single[1][1] = single[1][2] = single[2][1] = 4

    touching_colors = [[0] * 6 for _ in range(6)]
    touching_colors[1][1] = touching_colors[1][2] = 2
    touching_colors[2][2] = touching_colors[2][3] = 7

    answer_equivalent_tie = [[0] * 10 for _ in range(8)]
    for r, c in ((1, 1), (1, 2), (2, 1), (1, 6), (1, 7), (2, 6)):
        answer_equivalent_tie[r][c] = 4
    for c in range(2, 7):
        answer_equivalent_tie[5][c] = 7

    findings = {
        "blank": gen.self_check(blank),
        "single": gen.self_check(single),
        "touching_colors": gen.self_check(touching_colors),
        "answer_equivalent_tie": gen.self_check(answer_equivalent_tie),
    }
    assert all(findings.values())
    assert any("2..8" in item for item in findings["blank"])
    assert any("2..8" in item for item in findings["single"])
    assert any("touch" in item for item in findings["touching_colors"])
    assert any("answer-equivalent" in item for item in findings["answer_equivalent_tie"])

    # The Racket-equivalent rule can execute the latter two; distribution
    # rejection and oracle executability are deliberately separate outcomes.
    assert gen.rule_mirror(touching_colors)
    assert gen.rule_mirror(answer_equivalent_tie)
    with pytest.raises(ValueError):
        gen.rule_mirror(blank)


def test_generation_is_deterministic_fresh_input_pure_and_global_rng_pure():
    state = random.getstate()
    first = gen.generate(12345, 67, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(12345, 67, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    first[0][0] = 9
    replay = gen.generate(12345, 67, difficulty="hard")
    assert replay == second


def test_override_domain_is_exact_and_unknown_keys_fail_loudly():
    for profile in gen.SCENE_PROFILES:
        grid = gen.generate(7, 11, difficulty="easy", scene_profile=profile)
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(7, 11, misspelled_profile="tie_col")
    with pytest.raises(ValueError, match="not in options"):
        gen.generate(7, 11, scene_profile="not_a_profile")
