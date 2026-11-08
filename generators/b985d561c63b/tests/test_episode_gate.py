"""Behavior checks using actual selected rivals and concrete labeled grids."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("b985d561c63b_episode_gate", TASK_HOME / "workspace/episode_gate.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


@pytest.fixture(scope="module")
def selection():
    return gate.load_selection(TASK_HOME / "generator.py")


@pytest.fixture(scope="module")
def canonical(selection):
    with Path(selection["canonical_path"]).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == selection["task_id"] and row.get("source") == "training":
                return row
    raise AssertionError("Assigned canonical training row is missing")


def episode(selection, canonical, demos, queries):
    """Test fixture provenance; tests do not claim these are generator replays."""
    return {"task_id": selection["task_id"], "rule_task_id": selection["task_id"],
            "seed": 0, "sample_indices": list(range(len(demos) + len(queries))),
            "program": canonical["program_solution"], "executed_rule_hash": selection["rule_hash"],
            "provenance": {"generator_sha256": selection["generator_sha256"],
                "rule_hash": selection["rule_hash"], "catalog_rule_hash": selection["rule_hash"],
                "reference": "canonical", "difficulty": "medium"},
            "train": deepcopy(demos), "test": deepcopy(queries)}


def extension_pair():
    """Explicit 9x9 fixture: copy a 2x2 source with a zero into a 3x3 target."""
    before = [[0] * 9 for _ in range(9)]
    before[0][5:7] = [2, 4]
    before[1][5:7] = [4, 0]
    for row in range(4, 7):
        before[row][0:3] = [5, 5, 5]
    after = deepcopy(before)
    after[4][0:3] = [2, 4, 5]
    after[5][0:3] = [4, 0, 5]
    after[6][0:3] = [5, 5, 5]
    return {"input": before, "output": after}


def test_answer_equivalent_survivors_are_allowed(selection, canonical):
    value = episode(selection, canonical, canonical["train"], canonical["test"])
    result = gate.assess_episode(value, selection)
    assert result["exit_code"] == 0
    assert result["queries"][0]["disagreeing_rivals"] == []
    assert set(result["queries"][0]["answer_equivalent_survivors"]) == set(selection["rivals"])
    assert set(result["declarations"]) == {"LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"}
    assert result["grants_approval"] is False


def test_ambiguous_query_names_actual_surviving_rivals(selection, canonical):
    value = episode(selection, canonical, canonical["train"][:1], [extension_pair()])
    result = gate.assess_episode(value, selection)
    assert result["exit_code"] == 1
    assert result["status"] == "ambiguous"
    query = result["queries"][0]
    assert set(query["disagreeing_rivals"]) == set(selection["rivals"])
    assert query["sample_index"] == 1
    assert query["counterexample"]["supplied_reference_output"] == extension_pair()["output"]


def test_missing_query_label_is_unbound(selection, canonical):
    value = episode(selection, canonical, canonical["train"], canonical["test"])
    del value["test"][0]["output"]
    result = gate.assess_episode(value, selection)
    assert result["exit_code"] == 2
    assert any("unlabeled" in error for error in result["errors"])


def test_generator_source_mismatch_is_rejected(selection, canonical):
    value = episode(selection, canonical, canonical["train"], canonical["test"])
    value["provenance"]["generator_sha256"] = "0" * 64
    result = gate.assess_episode(value, selection)
    assert result["exit_code"] == 2
    assert any("generator_sha256" in error for error in result["errors"])
    assert result["rivals"] == {}


def test_rule_source_mismatch_is_rejected(selection, canonical):
    value = episode(selection, canonical, canonical["train"], canonical["test"])
    value["provenance"]["rule_hash"] = "0" * 12
    result = gate.assess_episode(value, selection)
    assert result["exit_code"] == 2
    assert any("canonical rule_hash" in error for error in result["errors"])


def test_second_query_is_checked_after_an_equivalent_first_query(selection, canonical):
    value = episode(selection, canonical, canonical["train"][:1], [canonical["test"][0], extension_pair()])
    result = gate.assess_episode(value, selection)
    assert result["exit_code"] == 1
    assert len(result["queries"]) == 2
    assert result["queries"][0]["disagreeing_rivals"] == []
    assert set(result["queries"][1]["disagreeing_rivals"]) == set(selection["rivals"])
    assert result["queries"][1]["query_index"] == 1
    assert result["queries"][1]["sample_index"] == 2


def test_demonstrated_extension_eliminates_rivals(selection, canonical):
    value = episode(selection, canonical, [extension_pair()], canonical["test"])
    result = gate.assess_episode(value, selection)
    assert result["exit_code"] == 0
    assert result["queries"][0]["surviving_rivals"] == []
    assert all(row["refuting_demo_indices"] == [0] for row in result["rivals"].values())
