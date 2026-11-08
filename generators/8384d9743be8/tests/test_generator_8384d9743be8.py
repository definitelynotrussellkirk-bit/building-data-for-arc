from __future__ import annotations

import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


GEN = importlib.import_module("puzzle_generators.per_puzzle.8384d9743be8.generator")
TASK_ID = "8384d9743be8"


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def test_rule_hash_is_pinned_to_selected_authority():
    assert GEN.RULE_HASH == "859078164faa"


def test_all_canonical_pairs_are_accepted_and_python_mirror_is_exact():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_default_five_slot_schedule_reproduces_every_canonical_occupancy_signature():
    assert GEN.EXAMPLES_NEEDED == 4
    assert not hasattr(GEN, "LESSON_SCHEDULE_PERIOD")
    assert len(GEN.SCHEDULE_PROFILES) == 5
    expected = {
        (18, 2, 3, 2),
        (18, 2, 2, 3),
        (19, 2, 2, 2),
        (17, 2, 4, 2),
        (17, 4, 0, 4),
    }
    for band in ("easy", "medium", "hard"):
        for start in range(10):
            signatures = {
                GEN.occupancy_signature(
                    GEN.generate(700 + start, start + offset, difficulty=band)
                )
                for offset in range(len(GEN.SCHEDULE_PROFILES))
            }
            assert signatures == expected


def test_exact_density_overrides_round_trip_and_invalid_controls_reject():
    cases = (
        {"density_l": 3, "density_r": 3},
        {"density_l": 9, "density_r": 9},
        {"density_l": 3, "density_r": 9},
        {"density_l": 9, "density_r": 3},
    )
    for index, overrides in enumerate(cases):
        grid = GEN.generate(810 + index, index, difficulty="hard", **overrides)
        assert GEN.observe_overrides(grid) == overrides
        assert GEN.self_check(grid) == []

    for name in ("density_l", "density_r"):
        for bad in (True, False, 1.0, "4", 2, 10):
            with pytest.raises(ValueError):
                GEN.generate(0, 0, **{name: bad})

    for bad_index in (True, False, 1.0, "1", -1):
        with pytest.raises(ValueError):
            GEN.generate(0, bad_index)

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, __override_contract_unknown_axis__=1)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")


def test_every_partial_profile_exposes_all_boolean_states_and_refutes_named_rivals():
    for index in range(4):
        grid = GEN.generate(900 + index, index, difficulty="medium")
        counts = GEN.occupancy_counts(grid)
        assert all(counts[state] > 0 for state in ("00", "10", "01", "11"))
        expected = GEN.rule_mirror(grid)
        for rival in GEN.SEMANTIC_RIVALS.values():
            assert rival(grid) != expected


def test_subset_profile_is_lawful_and_preserves_the_canonical_query_branch():
    grid = GEN.generate(1000, 4, difficulty="medium")
    counts = GEN.occupancy_counts(grid)
    assert counts["01"] == 0
    assert counts["10"] > 0
    assert counts["11"] > 0
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []


def test_every_rotated_five_pair_lesson_refutes_all_named_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(5):
            pairs = []
            for offset in range(5):
                grid = GEN.generate(1100 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for query_index in range(5):
                query = pairs[query_index]
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for competitor in GEN.LESSON_COMPETITORS.values():
                    assert not all(
                        competitor(demo["input"]) == demo["output"]
                        for demo in demos
                    )


def test_self_check_rejects_malformed_and_disconnected_inputs():
    grid = GEN.generate(1200, 0)

    ragged = [row[:] for row in grid]
    ragged[0].pop()
    assert GEN.self_check(ragged) == ["grid must be exactly 5x11"]

    boolean_cell = [row[:] for row in grid]
    boolean_cell[0][0] = True
    assert GEN.self_check(boolean_cell) == ["cells must be literal ARC integers 0..9"]

    bad_separator = [row[:] for row in grid]
    bad_separator[0][5] = 1
    assert any("separator" in reason for reason in GEN.self_check(bad_separator))

    disconnected = [[0] * 11 for _ in range(5)]
    disconnected[0][0] = disconnected[4][4] = 1
    disconnected[0][6] = disconnected[0][7] = disconnected[1][6] = 1
    errors = GEN.self_check(disconnected)
    assert any("left panel" in reason and "connected" in reason for reason in errors)


def test_generation_is_deterministic_fresh_and_preserves_process_global_rng():
    state_before = random.getstate()
    first = GEN.generate(4242, 3, difficulty="hard")
    state_after = random.getstate()
    assert state_after == state_before

    expected = _freeze(first)
    first[0][0] = (first[0][0] + 1) % 10
    second = GEN.generate(4242, 3, difficulty="hard")
    assert _freeze(second) == expected
    assert second is not first
    assert all(left is not right for left, right in zip(first, second))


def test_difficulty_bands_change_shape_without_changing_semantic_profile():
    for sample_index in range(len(GEN.SCHEDULE_PROFILES)):
        grids = {
            band: GEN.generate(5150 + sample_index, sample_index, difficulty=band)
            for band in ("easy", "medium", "hard")
        }
        assert len({_freeze(grid) for grid in grids.values()}) >= 2
        assert len({GEN.occupancy_signature(grid) for grid in grids.values()}) == 1


def test_retained_directional_xor_counterexample_remains_source_bound():
    import json
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[1]
        / "counterexamples"
        / "directional-xor-shortcuts.json"
    )
    evidence = json.loads(path.read_text())
    assert evidence["task_id"] == GEN.TASK_ID
    assert evidence["rule_hash"] == GEN.RULE_HASH
    grid = evidence["input"]
    assert GEN.occupancy_counts(grid) == evidence["occupancy_counts"]
    assert GEN.rule_mirror(grid) == evidence["correct_output"]
    assert GEN.SEMANTIC_RIVALS["xor_left_minus_right"](grid) == evidence[
        "xor_left_minus_right_output"
    ]
    assert GEN.SEMANTIC_RIVALS["xor_right_minus_left"](grid) == evidence[
        "xor_right_minus_left_output"
    ]
    assert evidence["correct_output"] != evidence["xor_left_minus_right_output"]
    assert evidence["correct_output"] != evidence["xor_right_minus_left_output"]
