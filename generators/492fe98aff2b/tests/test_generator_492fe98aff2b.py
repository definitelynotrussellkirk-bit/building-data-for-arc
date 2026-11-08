from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs

TASK_ID = "492fe98aff2b"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_all_canonical_inputs_are_accepted_and_mirrored_exactly():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_declared_axes_are_exactly_observable_at_both_boundaries():
    cases = [
        dict(grid_h=7, grid_w=9, bbox_h=3, bbox_w=4, palette_size=3, component_count=2),
        dict(grid_h=14, grid_w=16, bbox_h=5, bbox_w=7, palette_size=5, component_count=4),
        dict(grid_h=9, grid_w=12, bbox_h=4, bbox_w=6, palette_size=4, component_count=3),
    ]
    for index, overrides in enumerate(cases):
        grid = GEN.generate(9100 + index, index, difficulty="hard", **overrides)
        assert GEN.observe_overrides(grid) == overrides
        assert GEN.self_check(grid) == []


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, bogus_axis=3)


def test_self_check_rejects_targeted_rule_hiding_impostors():
    blank = [[0] * 9 for _ in range(7)]
    identity_border = [[0] * 9 for _ in range(7)]
    identity_border[0][1] = 2
    identity_border[5][7] = 3
    single_component = [[0] * 9 for _ in range(7)]
    single_component[2][2] = 2
    single_component[2][3] = 3
    solid_bbox = [[0] * 9 for _ in range(7)]
    for r in range(2, 5):
        for c in range(2, 6):
            solid_bbox[r][c] = 2 if (r + c) % 2 else 3
    frame_only = [[0] * 9 for _ in range(7)]
    for c in range(2, 7):
        frame_only[1][c] = 2
        frame_only[5][c] = 3
    for r in range(1, 6):
        frame_only[r][2] = 2
        frame_only[r][6] = 3

    assert GEN.self_check(blank)
    assert GEN.self_check(identity_border)
    assert GEN.self_check(single_component)
    assert GEN.self_check(solid_bbox)
    assert any("fully painted bbox frame" in issue for issue in GEN.self_check(frame_only))


def test_replay_freshness_and_global_rng_purity():
    random.seed(20260727)
    state = random.getstate()
    first = GEN.generate(77, 5, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(77, 5, difficulty="medium")
    assert first == second
    assert first is not second
    first[0][0] = 9
    assert second[0][0] != 9


def test_every_ordinary_draw_refutes_all_named_rivals():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(16):
            grid = GEN.generate(5000 + sample_index, sample_index, difficulty=difficulty)
            expected = GEN.rule_mirror(grid)
            assert GEN.self_check(grid) == []
            for rival in GEN.SEMANTIC_RIVALS.values():
                assert rival(grid) != expected
            assert all(predicate(grid) for predicate in GEN.SEMANTIC_WITNESSES.values())


def test_every_two_demo_sliding_window_identifies_the_rule():
    for difficulty in ("easy", "medium", "hard"):
        pairs = [
            _pair(GEN.generate(8000, index, difficulty=difficulty))
            for index in range(18)
        ]
        for start in range(len(pairs) - GEN.EXAMPLES_NEEDED):
            demos = pairs[start : start + GEN.EXAMPLES_NEEDED]
            query = {"input": pairs[start + GEN.EXAMPLES_NEEDED]["input"]}
            assert GEN.lesson_identifiable(demos, query) == []
