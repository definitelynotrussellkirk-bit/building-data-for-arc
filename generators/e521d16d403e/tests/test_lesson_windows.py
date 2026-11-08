"""Hand fixtures for the independent lesson-window ambiguity scorer."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "workspace" / "check_lesson_windows.py"
SPEC = importlib.util.spec_from_file_location("lesson_window_checker_tests", SOURCE)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def test_refuted_ambiguous_and_unchanged_survivors_are_distinct():
    matches = {
        "refuted": {41: False, 42: True, 43: True, 44: False},
        "ambiguous": {41: True, 42: True, 43: True, 44: False},
        "unchanged": {41: True, 42: True, 43: True, 44: True},
    }
    result = CHECKER.score_partition(matches, [41, 42, 43], [44])
    assert result["ambiguous_rivals"] == ["ambiguous"]
    assert result["unchanged_survivors"] == ["unchanged"]
    assert result["rivals"]["refuted"]["refuting_demo_indices"] == [41]
    assert result["rivals"]["refuted"]["status"] == "refuted"
    assert result["rivals"]["ambiguous"]["differing_query_indices"] == [44]


def test_multiple_queries_fail_if_any_held_out_answer_changes():
    matches = {"rival": {7: True, 8: True, 9: True, 10: False}}
    result = CHECKER.score_partition(matches, [7, 8], [9, 10])
    assert result["ambiguous_rivals"] == ["rival"]
    assert result["rivals"]["rival"]["differing_query_indices"] == [10]


def test_rotations_reveal_a_single_discriminating_example():
    indices = [3, 4, 5, 6]
    matches = {"rival": {i: i != 4 for i in indices}}
    rotations = [CHECKER.score_partition(matches, [i for i in indices if i != q], [q])
                 for q in indices]
    assert [r["query_indices"][0] for r in rotations if r["ambiguous_rivals"]] == [4]
    assert all(r["rivals"]["rival"]["refuting_demo_indices"] == [4]
               for r in rotations if r["query_indices"] != [4])


def test_two_refutations_survive_every_one_query_rotation():
    indices = [0, 1, 2, 3]
    matches = {"rival": {i: i not in (0, 2) for i in indices}}
    for query in indices:
        scored = CHECKER.score_partition(matches, [i for i in indices if i != query], [query])
        assert not scored["ambiguous_rivals"]
        assert scored["rivals"]["rival"]["refuting_demo_indices"]


def test_identical_grid_positions_keep_their_actual_sample_indices():
    # Equal evidence at two positions must remain two positions after input deduplication.
    matches = {"rival": {20: False, 21: False, 22: True}}
    result = CHECKER.score_partition(matches, [20, 21], [22])
    assert result["rivals"]["rival"]["refuting_demo_indices"] == [20, 21]


def test_overlapping_demonstration_and_query_positions_are_rejected():
    with pytest.raises(ValueError, match="overlap"):
        CHECKER.score_partition({"rival": {0: True, 1: False}}, [0, 1], [1])


def test_empty_rival_set_cannot_pass_vacuously():
    with pytest.raises(ValueError, match="rival"):
        CHECKER.score_partition({}, [0], [1])


def test_missing_rival_output_is_an_error_not_a_refutation():
    with pytest.raises(ValueError, match="None instead of an output grid"):
        CHECKER._prediction(lambda grid: None, [[1]], lambda grid: grid)
    result = CHECKER.score_partition({"invalid": {0: None, 1: False}}, [0], [1])
    assert result["error_rivals"] == ["invalid"]
    assert result["rivals"]["invalid"]["refuting_demo_indices"] == []
    assert result["ambiguous_rivals"] == []
