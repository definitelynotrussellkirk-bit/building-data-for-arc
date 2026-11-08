from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.af6f35b0279d.generator"
)


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_pairs_are_accepted_and_mirrored_exactly():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_rule_hash_pins_the_selected_canonical_rule():
    assert gen.RULE_HASH == "5fd8695d776f"


def test_all_exact_axes_are_observable_at_declared_boundaries():
    cases = (
        {
            "grid_h": 8,
            "grid_w": 8,
            "marker_corner": "top_left",
            "marker_color": 1,
            "n_decoy_colors": 1,
            "target_cells": 4,
            "target_size_relation": "target_smaller",
            "intrusion": False,
        },
        {
            "grid_h": 16,
            "grid_w": 16,
            "marker_corner": "bottom_right",
            "marker_color": 9,
            "n_decoy_colors": 3,
            "target_cells": 9,
            "target_size_relation": "target_larger",
            "intrusion": True,
        },
    )
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = gen.generate(991 + index, index, difficulty=band, **overrides)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == overrides


def test_every_sliding_four_demo_window_identifies_the_rule():
    for band in ("easy", "medium", "hard"):
        rows = [_pair(gen.generate(404, i, difficulty=band)) for i in range(16)]
        for start in range(12):
            demos = rows[start : start + gen.EXAMPLES_NEEDED]
            query = rows[start + gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == []


def test_intrusion_is_a_real_regression_witness_against_color_mask_crop():
    grid = gen.generate(
        73,
        1,
        difficulty="medium",
        grid_h=8,
        grid_w=8,
        marker_corner="top_right",
        marker_color=4,
        n_decoy_colors=1,
        target_cells=4,
        target_size_relation="target_smaller",
        intrusion=True,
    )
    observed = gen.observe_overrides(grid)
    assert observed["intrusion"] is True
    official = gen.rule_mirror(grid)
    shortcut = gen.CANONICAL_SHORTCUTS["selected_color_mask_only"](grid)
    assert official != shortcut
    assert any(value not in (0, observed["marker_color"]) for row in official for value in row)


def test_size_relations_refute_largest_and_smallest_object_rivals():
    smaller = gen.generate(
        81,
        2,
        target_size_relation="target_smaller",
        n_decoy_colors=3,
        target_cells=4,
    )
    larger = gen.generate(
        82,
        3,
        target_size_relation="target_larger",
        n_decoy_colors=3,
        target_cells=9,
    )
    assert gen.rule_mirror(smaller) != gen.SEMANTIC_RIVALS["largest_body_object"](smaller)
    assert gen.rule_mirror(larger) != gen.SEMANTIC_RIVALS["smallest_body_object"](larger)


def test_self_check_rejects_targeted_impostors():
    for name in ("no_corner_marker", "no_match", "multiple_matches"):
        assert gen.self_check(gen.make_degenerate(name)), name

    solid = [[0] * 9 for _ in range(9)]
    solid[0][0] = 4
    for r, c in ((3, 3), (3, 4), (4, 3), (4, 4)):
        solid[r][c] = 4
    solid[7][7] = 6
    assert any("fills its bbox" in reason for reason in gen.self_check(solid))

    missing_external_decoy = gen.generate(90, 1, intrusion=True)
    info = gen.observe_overrides(missing_external_decoy)
    r0, c0, r1, c1 = gen._analyse(missing_external_decoy)[0]["target_bbox"]
    bad = copy.deepcopy(missing_external_decoy)
    for r, row in enumerate(bad):
        for c, value in enumerate(row):
            if value not in (0, info["marker_color"]) and not (r0 <= r <= r1 and c0 <= c <= c1):
                bad[r][c] = 0
    assert any("outside the selected bbox" in reason for reason in gen.self_check(bad))


def test_replay_returns_fresh_objects_and_preserves_global_rng_state():
    random.seed(123456)
    before = random.getstate()
    a = gen.generate(55, 7, difficulty="hard")
    after = random.getstate()
    b = gen.generate(55, 7, difficulty="hard")
    assert before == after
    assert a == b and a is not b
    assert all(row_a is not row_b for row_a, row_b in zip(a, b))
    a[0][0] = 9
    assert gen.generate(55, 7, difficulty="hard") == b


def test_unknown_override_and_unknown_difficulty_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 0, difficulty="extreme")
