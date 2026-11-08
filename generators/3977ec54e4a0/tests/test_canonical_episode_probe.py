"""Behavioral checks for saved canonical-episode assessment.

These fixtures are deliberately tiny: they isolate evidence handling from
chevron geometry and catch accidental query-label leakage or false success.
"""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest


PROBE = Path(__file__).resolve().parents[1] / "workspace/canonical_episode_probe.py"


def load_probe():
    assert PROBE.is_file(), "the reusable canonical episode probe is not implemented"
    spec = importlib.util.spec_from_file_location("canonical_episode_probe_test", PROBE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_query_answers_never_refute_a_competitor_for_another_query():
    # A rival that fits the only demo must remain ambiguous on both queries,
    # even though either query's answer would refute it if accidentally leaked.
    probe = load_probe()
    episode = {
        "train": [{"input": [[0]], "output": [[0]]}],
        "test": [
            {"input": [[1]], "output": [[1]]},
            {"input": [[2]], "output": [[2]]},
        ],
    }
    result = probe.assess_episode(episode, {"always_zero": lambda grid: [[0]]})
    assert result["rivals"]["always_zero"]["demo_fit"] == "fits"
    assert [query["ambiguous_rivals"] for query in result["queries"]] == [
        ["always_zero"], ["always_zero"]
    ]
    assert result["status"] == "FAIL"


def test_a_surviving_competitor_that_agrees_on_the_query_is_not_ambiguity():
    probe = load_probe()
    episode = {
        "train": [{"input": [[0]], "output": [[0]]}],
        "test": [{"input": [[1]], "output": [[1]]}],
    }
    result = probe.assess_episode(episode, {"identity": copy.deepcopy})
    assert result["queries"][0]["agreeing_rivals"] == ["identity"]
    assert result["queries"][0]["ambiguous_rivals"] == []
    assert result["status"] == "PASS"


def test_duplicate_query_or_demo_inputs_fail_with_pair_locations():
    probe = load_probe()
    episode = {
        "train": [{"input": [[0]], "output": [[0]]}],
        "test": [
            {"input": [[0]], "output": [[0]]},
            {"input": [[0]], "output": [[0]]},
        ],
    }
    result = probe.assess_episode(episode, {"identity": copy.deepcopy})
    assert result["unique_input_count"] == 1
    assert result["duplicate_inputs"][0]["locations"] == [
        "train[0]", "test[0]", "test[1]"
    ]
    assert result["status"] == "FAIL"


def test_a_missing_query_label_is_rejected_instead_of_silently_skipped():
    probe = load_probe()
    with pytest.raises(ValueError, match=r"test\[0\].*output"):
        probe.assess_episode(
            {"train": [{"input": [[0]], "output": [[0]]}],
             "test": [{"input": [[1]]}]},
            {"identity": copy.deepcopy},
        )


def test_a_rival_error_is_not_counted_as_demonstration_refutation():
    probe = load_probe()

    def broken(grid):
        raise RuntimeError("cannot decode")

    result = probe.assess_episode(
        {"train": [{"input": [[0]], "output": [[0]]}],
         "test": [{"input": [[1]], "output": [[1]]}]},
        {"broken": broken},
    )
    assert result["rivals"]["broken"]["demo_fit"] == "error"
    assert result["queries"][0]["error_rivals"] == ["broken"]
    assert result["status"] == "FAIL"


def test_mutating_rivals_cannot_change_saved_pairs_or_each_others_inputs():
    probe = load_probe()
    episode = {
        "train": [{"input": [[0]], "output": [[0]]}],
        "test": [{"input": [[1]], "output": [[1]]}],
    }
    original = copy.deepcopy(episode)

    def mutate(grid):
        grid[0][0] = 9
        return grid

    result = probe.assess_episode(
        episode, {"mutator": mutate, "identity": copy.deepcopy}
    )
    assert episode == original
    assert result["rivals"]["mutator"]["demo_fit"] == "refuted"
    assert result["rivals"]["identity"]["demo_fit"] == "fits"
    assert result["queries"][0]["agreeing_rivals"] == ["identity"]


def test_absence_of_declared_competitors_is_reported_as_no_contract():
    probe = load_probe()
    result = probe.assess_episode(
        {"train": [{"input": [[0]], "output": [[0]]}],
         "test": [{"input": [[1]], "output": [[1]]}]},
        {},
    )
    assert result["status"] == "NO_CONTRACT"


@pytest.mark.parametrize(
    "field,value,expected_error",
    [
        ("generator_sha256", "different-source", "generator source hash"),
        ("executed_rule_hash", "different-rule", "executed rule hash"),
        ("reference", "archival", "canonical reference"),
        ("train", [], "demonstration count"),
        ("test", [], "query count"),
    ],
)
def test_stale_sources_and_incomplete_counts_cannot_pass_bindings(
    field, value, expected_error
):
    probe = load_probe()
    episode = {
        "task_id": "3977ec54e4a0",
        "executed_rule_hash": "correct-rule",
        "provenance": {
            "generator_sha256": "correct-source",
            "reference": "canonical",
            "rule_hash": "correct-rule",
        },
        "train": [None, None, None],
        "test": [None, None, None, None],
    }
    assert probe.binding_errors(episode, "correct-source", "correct-rule") == []
    if field in {"generator_sha256", "reference"}:
        episode["provenance"][field] = value
    else:
        episode[field] = value
    assert any(
        expected_error in error
        for error in probe.binding_errors(episode, "correct-source", "correct-rule")
    )


def test_rotation_ambiguity_is_reported_separately_from_ordered_production():
    probe = load_probe()
    episode = {
        "train": [
            {"input": [[0]], "output": [[0]]},
            {"input": [[1]], "output": [[1]]},
            {"input": [[2]], "output": [[2]]},
        ],
        "test": [{"input": [[3]], "output": [[3]]}],
    }

    def omit_one(grid):
        return [[9]] if grid == [[1]] else copy.deepcopy(grid)

    competitors = {"omit_one": omit_one}
    production = probe.assess_episode(episode, competitors)
    rotations = probe.assess_rotations(episode, competitors)
    assert production["status"] == "PASS"
    assert [row["status"] for row in rotations] == ["PASS", "FAIL", "PASS", "PASS"]
    assert rotations[1]["held_out_pair_index"] == 1
    assert rotations[1]["train_pair_indices"] == [0, 2, 3]
    assert rotations[1]["assessment"]["queries"][0]["ambiguous_rivals"] == ["omit_one"]
    assert production["status"] == "PASS"


def test_rotations_require_a_separate_one_query_episode():
    probe = load_probe()
    with pytest.raises(ValueError, match="exactly one query"):
        probe.assess_rotations(
            {"train": [{"input": [[0]], "output": [[0]]}],
             "test": [{"input": [[1]], "output": [[1]]},
                      {"input": [[2]], "output": [[2]]}]},
            {"identity": copy.deepcopy},
        )
