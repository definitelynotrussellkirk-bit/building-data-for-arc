from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_generator_27080597d778 import LIBRARY, canonical, oracle, pair, subject

TOOL = LIBRARY / "generators/27080597d778/workspace/lesson_gate.py"


def gate():
    assert TOOL.is_file(), "missing exported-lesson gate"
    spec = importlib.util.spec_from_file_location("lesson_gate_under_test", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode(n_train=4):
    branches = ("complement", "overlap", "gap", "balanced")
    return {
        "task_id": subject.TASK_ID, "rule_task_id": subject.TASK_ID,
        "executed_rule_hash": subject.RULE_HASH,
        "program": canonical()["program_solution"], "seed": 149,
        "sample_indices": list(range(n_train + 2)),
        "provenance": {"generator_sha256": hashlib.sha256(Path(subject.__file__).read_bytes()).hexdigest(),
                       "approved": False, "rule_hash": subject.RULE_HASH},
        "train": [pair(subject.generate(49, 8, branch=b, **({} if b == "complement" else {"max_defects": 1}))) for b in branches[:n_train]],
        "test": [pair(subject.generate(149, 4, branch=b, **({} if b == "complement" else {"max_defects": 1}))) for b in ("complement", "balanced")],
    }


def audit(data, module=None, reference=oracle):
    return gate().audit_episode(data, module or subject, reference, rule_hash=subject.RULE_HASH)


def test_four_demo_lesson_is_accepted_and_auditor_is_pure():
    data = episode()
    saved = deepcopy(data)
    result = audit(data)
    assert result["passed"], result
    assert len(result["queries"]) == 2 and result["reference_pairs_checked"] == 6
    assert data == saved


def test_second_query_cannot_hide_behind_a_valid_first_query():
    result = audit(episode(3))
    assert not result["passed"]
    assert result["queries"][0]["passed"]
    assert not result["queries"][1]["passed"]
    assert any("population_count" in x for x in result["queries"][1]["errors"])


@pytest.mark.parametrize("mutation", ["no_test", "missing_output", "bad_output", "wrong_rule",
                                      "wrong_task", "wrong_source", "duplicate_query", "malformed_grid",
                                      "stale_indices", "noninteger_output"])
def test_broken_or_unbound_episodes_fail_closed(mutation):
    data = episode()
    if mutation == "no_test":
        data["test"] = []
    elif mutation == "missing_output":
        del data["test"][1]["output"]
    elif mutation == "bad_output":
        data["test"][1]["output"][0][0] = (data["test"][1]["output"][0][0] + 1) % 10
    elif mutation == "wrong_rule":
        data["executed_rule_hash"] = "0" * 12
    elif mutation == "wrong_task":
        data["task_id"] = "other-task"
    elif mutation == "wrong_source":
        data["provenance"]["generator_sha256"] = "0" * 64
    elif mutation == "duplicate_query":
        data["test"][0] = deepcopy(data["train"][0])
    elif mutation == "malformed_grid":
        data["test"][0]["input"][-1] = [0]
    elif mutation == "stale_indices":
        data["sample_indices"] = [1]
    else:
        data["test"][0]["output"][0][0] = float(data["test"][0]["output"][0][0])
    assert not audit(data)["passed"]


def test_missing_semantic_contract_is_not_a_pass():
    empty = SimpleNamespace(TASK_ID=subject.TASK_ID, RULE_HASH=subject.RULE_HASH)
    result = audit(episode(), empty)
    assert not result["passed"]
    assert any("contract" in reason for reason in result["errors"])


def test_empty_hook_cannot_override_a_surviving_wrong_solver(monkeypatch):
    monkeypatch.setattr(subject, "lesson_identifiable", lambda demos, query: [])
    result = audit(episode(3))
    assert not result["passed"]
    assert "population_count" in result["queries"][1]["conflicting_rivals"]


def test_reference_failure_is_not_silently_a_python_label_fallback():
    def broken_reference(grid):
        raise RuntimeError("Racket unavailable")
    result = audit(episode(), reference=broken_reference)
    assert not result["passed"] and result["reference_pairs_checked"] == 0
    assert any("Racket unavailable" in reason for reason in result["errors"])


def test_mutating_reference_is_rejected_and_does_not_change_input():
    def mutating_reference(grid):
        answer = oracle(grid)
        grid[0][0] = 99
        return answer
    data = episode()
    saved = deepcopy(data)
    result = audit(data, reference=mutating_reference)
    assert not result["passed"] and data == saved
    assert any("mutated" in reason for reason in result["errors"])


def test_shuffle_preserves_pair_index_alignment_and_query_labels():
    data = episode()
    original = deepcopy(data)
    out = gate().shuffle_demos(data)
    assert data == original
    permutation = out["lesson_gate"]["demo_permutation"]
    assert sorted(permutation) == [0, 1, 2, 3]
    assert out["train"] == [original["train"][i] for i in permutation]
    assert out["sample_indices"][:4] == permutation
    assert out["test"] == original["test"]
    assert out == gate().shuffle_demos(original)
    assert audit(out)["passed"]


def test_public_challenge_exposes_only_demos_and_query_inputs():
    data = episode()
    public = gate().public_challenge(data)
    assert set(public) == {"train", "test"}
    assert public["train"] == data["train"]
    assert public["test"] == [{"input": q["input"]} for q in data["test"]]
    public["train"][0]["input"][0][0] = 99
    assert data["train"][0]["input"][0][0] != 99


def test_packaged_rule_wrapper_can_resolve_its_legacy_scripts_namespace():
    gate().load_subject(LIBRARY, subject.TASK_ID)
    from puzzle_generators.runner import wrap_rule
    assert isinstance(wrap_rule(canonical()["program_solution"]), str)


@pytest.mark.parametrize("bad", [None, [], [[True]], [[12]], [[0], []]])
def test_invalid_rival_predictions_are_contract_failures_not_falsifications(bad):
    # A broken competitor must not disappear simply because its invalid output
    # differs from every demonstration. Otherwise the gate fails open.
    module = SimpleNamespace(**{name: getattr(subject, name) for name in
        ('TASK_ID', 'RULE_HASH', '__file__', 'self_check', 'lesson_identifiable')})
    module.SEMANTIC_RIVALS = {**subject.SEMANTIC_RIVALS, 'broken': lambda grid: deepcopy(bad)}
    report = audit(episode(), module=module)
    assert not report['passed']
    assert any('rival broken' in error for error in report['errors'])
