from __future__ import annotations

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "0f5fbe0de38e"
ROOT = find_root(__file__)
GEN, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)

EXPECTED_WITNESS_RIVALS = {
    "unit_scale": ["scaled_only"],
    "scaled_blocks": ["unit_scale_only"],
    "multiple_pairs": ["first_pair_only"],
    "mixed_scales": ["unit_scale_only", "scaled_only"],
    "same_diagonal": ["opposite_diagonal_only"],
    "opposite_diagonal": ["same_diagonal_only"],
    "three_pairs": ["first_two_pairs_only"],
}


def test_every_semantic_witness_declares_a_truthful_rival_disagreement():
    assert GEN.WITNESS_RIVALS == EXPECTED_WITNESS_RIVALS
    assert set(GEN.SEMANTIC_RIVALS) >= {
        name for names in EXPECTED_WITNESS_RIVALS.values() for name in names
    }

    grids = [
        GEN.generate(940_000 + index, index, difficulty="hard")
        for index in range(6)
    ]
    for witness_name, rival_names in EXPECTED_WITNESS_RIVALS.items():
        witness = GEN.SEMANTIC_WITNESSES[witness_name]
        matching = [grid for grid in grids if witness(grid)]
        assert matching, witness_name
        for grid in matching:
            intended = GEN._predict(grid, "canonical")
            assert any(
                GEN.SEMANTIC_RIVALS[rival_name](grid) != intended
                for rival_name in rival_names
            ), (witness_name, rival_names)


def test_first_two_pairs_rival_fits_all_canonical_demos_but_not_query():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    demos = [pair for pair in pairs if pair["split"] == "train"]
    queries = [pair for pair in pairs if pair["split"] == "test"]
    rival = GEN.LESSON_COMPETITORS["first_two_pairs_only"]

    assert demos and queries
    assert all(rival(pair["input"]) == pair["output"] for pair in demos)
    assert any(rival(pair["input"]) != pair["output"] for pair in queries)


def test_retained_first_two_pairs_counterexample_is_reproducible():
    overrides = {
        "grid_h": 22,
        "grid_w": 22,
        "bg_color": 0,
        "fill_color": 8,
        "marker_a_color": 2,
        "marker_b_color": 6,
        "template_profile": "cross4_anti",
        "lesson_profile": "mixed_1_2_3",
        "orientation_profile": "mixed",
    }
    grid = GEN.generate(4242, 5, difficulty="hard", **overrides)
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.self_check(grid) == []

    intended = GEN._predict(grid, "canonical")
    rival = GEN.LESSON_COMPETITORS["first_two_pairs_only"](grid)
    differing = [
        (row, column)
        for row in range(len(grid))
        for column in range(len(grid[0]))
        if intended[row][column] != rival[row][column]
    ]
    assert len(differing) == 36
