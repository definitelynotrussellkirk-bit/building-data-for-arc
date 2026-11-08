"""Focused tests for the proposed, non-production hole-selection parameter."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK_HOME / "workspace" / "parametric"
sys.path.insert(0, str(PARAMETRIC))

import prototype


def test_parameter_is_bounded_and_canonical_default_is_all_holes():
    assert prototype.PARAMETER_NAME == "hole_selection"
    assert prototype.ALLOWED_VALUES == ("all_holes", "largest_hole")
    assert prototype.DEFAULT_VALUE == "all_holes"
    assert prototype.program_for("all_holes") == prototype.canonical_program()
    with pytest.raises(ValueError):
        prototype.program_for("unknown")


def test_episode_chooses_one_parameter_and_every_demo_refutes_the_other_setting():
    for policy in prototype.ALLOWED_VALUES:
        episode = prototype.build_episode(seed=17, policy=policy)
        assert episode["meta"]["hole_selection"] == policy
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 1
        rival = next(value for value in prototype.ALLOWED_VALUES if value != policy)
        rival_outputs = prototype.run_program(
            prototype.program_for(rival),
            [pair["input"] for pair in episode["train"]],
        )
        assert all(actual["output"] != rival_output
                   for actual, rival_output in zip(episode["train"], rival_outputs))


def test_setting_changes_the_executed_racket_transformation_on_one_lawful_input():
    grid = prototype.make_input(seed=91, sample_index=0)
    outputs = {
        policy: prototype.run_program(prototype.program_for(policy), [grid])[0]
        for policy in prototype.ALLOWED_VALUES
    }
    assert outputs["all_holes"] != outputs["largest_hole"]
    assert outputs["all_holes"] == prototype.python_apply(grid, "all_holes")
    assert outputs["largest_hole"] == prototype.python_apply(grid, "largest_hole")


def test_materialized_evidence_hashes_match_and_public_challenges_hide_query_answers():
    evidence_path = PARAMETRIC / "evidence.json"
    assert evidence_path.is_file()
    evidence = json.loads(evidence_path.read_text())
    assert evidence["status"] == "proposed_prototype"
    for policy in prototype.ALLOWED_VALUES:
        setting = evidence["settings"][policy]
        rule_path = PARAMETRIC / setting["rule_path"]
        episode_path = PARAMETRIC / setting["episode_path"]
        challenge_path = PARAMETRIC / setting["challenge_path"]
        assert hashlib.sha256(rule_path.read_bytes()).hexdigest() == setting["rule_sha256"]
        episode = json.loads(episode_path.read_text())
        challenge = json.loads(challenge_path.read_text())
        assert episode["meta"]["hole_selection"] == policy
        assert "hole_selection" not in challenge.get("meta", {})
        assert all("output" not in pair for pair in challenge["test"])
