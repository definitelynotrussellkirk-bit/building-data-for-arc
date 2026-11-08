"""Focused regression tests for the ordered-elbow generator b5c887448ed9."""
from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.b5c887448ed9 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _pair(grid):
    return {"input": grid, "output": gen._predict(grid)}


def test_rule_hash_and_unknown_overrides_are_strict():
    assert gen.RULE_HASH == "c56faa67ac6f"
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __typo_axis=3)


def test_every_declared_override_is_exact_and_observable_at_boundaries():
    cases = (
        {"grid_h": 7, "grid_w": 8, "n_colors": 2, "palette_band": "low", "layout_profile": "separated"},
        {"grid_h": 7, "grid_w": 8, "n_colors": 4, "palette_band": "high", "layout_profile": "crossing"},
        {"grid_h": 14, "grid_w": 14, "n_colors": 2, "palette_band": "high", "layout_profile": "separated"},
        {"grid_h": 14, "grid_w": 14, "n_colors": 4, "palette_band": "low", "layout_profile": "crossing"},
    )
    for index, overrides in enumerate(cases):
        grid = gen.generate(100 + index, index, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.strict_canonical_like(grid) == []


def test_canonical_inputs_are_accepted_and_python_diagnostic_matches_outputs():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._predict(pair["input"]) == pair["output"]


def test_four_slot_schedule_rebuts_all_named_competitors_for_every_start():
    seed = 271828
    examples = [_pair(gen.generate(seed, index, difficulty="medium")) for index in range(12)]
    for start in range(8):
        demos = examples[start : start + gen.EXAMPLES_NEEDED]
        query = examples[start + gen.EXAMPLES_NEEDED]
        assert gen.lesson_identifiable(demos, query) == []
        assert {gen.observe_overrides(pair["input"])["layout_profile"] for pair in demos} == {
            "separated",
            "crossing",
        }
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert not all(rival(pair["input"]) == pair["output"] for pair in demos), name


def test_crossing_profile_exposes_later_color_overwrite():
    grid = gen.generate(
        7,
        0,
        grid_h=7,
        grid_w=8,
        n_colors=4,
        palette_band="high",
        layout_profile="crossing",
    )
    analysis = gen._analysis(grid)
    assert analysis["crossing_count"] >= 1
    assert analysis["endpoint_conflicts"] == []
    assert gen._predict(grid) != gen._reverse_overwrite(grid)


def test_self_check_rejects_targeted_structural_mutations():
    valid = gen.generate(5, 0)

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    assert gen.self_check(ragged)

    singleton = copy.deepcopy(valid)
    color = next(v for row in singleton for v in row if v)
    seen = False
    for r, row in enumerate(singleton):
        for c, value in enumerate(row):
            if value == color and not seen:
                singleton[r][c] = 0
                seen = True
                break
        if seen:
            break
    assert any("appears 1 times" in reason for reason in gen.self_check(singleton))

    triplicate = copy.deepcopy(valid)
    zero = next((r, c) for r, row in enumerate(triplicate) for c, value in enumerate(row) if value == 0)
    triplicate[zero[0]][zero[1]] = color
    assert any("appears 3 times" in reason for reason in gen.self_check(triplicate))

    invalid_color = copy.deepcopy(valid)
    invalid_color[0][0] = 10
    assert any("ARC colors" in reason for reason in gen.self_check(invalid_color))


def test_replay_is_deterministic_fresh_and_does_not_touch_global_rng():
    state = random.getstate()
    first = gen.generate(12345, 9, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(12345, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 99
    third = gen.generate(12345, 9, difficulty="hard")
    assert third == second
