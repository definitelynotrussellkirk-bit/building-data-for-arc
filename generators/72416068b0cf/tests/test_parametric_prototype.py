"""Executable evidence for the task-local composition-order prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root


TASK_ID = "72416068b0cf"
PROTOTYPE_PATH = Path(__file__).parents[1] / "workspace" / "parametric" / "prototype.py"
SPEC = importlib.util.spec_from_file_location("task_72416068b0cf_parametric", PROTOTYPE_PATH)
assert SPEC is not None and SPEC.loader is not None
PROTOTYPE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTOTYPE)


def _canonical_program() -> str:
    root = find_root(__file__)
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError(TASK_ID)


def test_forward_program_is_canonical_and_reverse_changes_only_composition_order():
    canonical = _canonical_program()
    forward = PROTOTYPE.program_for("forward", root=find_root(__file__))
    reverse = PROTOTYPE.program_for("reverse", root=find_root(__file__))

    assert forward == canonical
    assert forward.count(PROTOTYPE.FORWARD_FRAGMENT) == 1
    assert PROTOTYPE.REVERSE_FRAGMENT not in forward
    assert reverse.count(PROTOTYPE.REVERSE_FRAGMENT) == 1
    assert PROTOTYPE.FORWARD_FRAGMENT not in reverse
    assert reverse == forward.replace(
        PROTOTYPE.FORWARD_FRAGMENT,
        PROTOTYPE.REVERSE_FRAGMENT,
        1,
    )


@pytest.mark.parametrize("seed,expected_order", [(0, "reverse"), (2, "forward")])
def test_episode_parameter_is_chosen_once_and_racket_demos_distinguish_it(seed, expected_order):
    evidence = PROTOTYPE.materialize_episode(
        seed,
        difficulty="easy",
        root=find_root(__file__),
    )

    assert evidence["parameter"] == {
        "composition_order": expected_order,
        "allowed": ["forward", "reverse"],
        "canonical_default": "forward",
    }
    assert len(evidence["private"]["train"]) == 4
    assert len(evidence["private"]["test"]) == 1
    assert evidence["demonstration_difference_indices"]
    assert evidence["racket_verified"] is True

    selected = evidence["programs"][expected_order]
    rival_order = "forward" if expected_order == "reverse" else "reverse"
    rival = evidence["programs"][rival_order]
    assert selected["sha256"] == hashlib.sha256(selected["text"].encode()).hexdigest()
    assert rival["sha256"] == hashlib.sha256(rival["text"].encode()).hexdigest()

    public = evidence["public"]
    assert set(public) == {"schema", "task_id", "train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    assert "composition_order" not in serialized
    assert "program_solution" not in serialized


def test_racket_execution_does_not_require_repository_scripts(monkeypatch):
    """The README command runs from the packet source tree, which has no scripts package."""
    import builtins

    root = find_root(__file__)
    first_input = None
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                first_input = row["train"][0]["input"]
                break
    assert first_input is not None

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "scripts" or name.startswith("scripts."):
            raise ModuleNotFoundError("scripts intentionally unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    outputs = PROTOTYPE._racket_outputs(
        PROTOTYPE.program_for("forward", root=root),
        [first_input],
    )
    assert len(outputs) == 1
