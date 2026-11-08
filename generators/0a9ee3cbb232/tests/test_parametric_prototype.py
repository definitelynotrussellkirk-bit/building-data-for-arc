"""Focused tests for the separate run-axis prototype."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_HOME / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert PROTOTYPE_PATH.exists(), "the requested parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("run_axis_prototype", PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_default_setting_is_exact_canonical_program():
    prototype = load_prototype()
    assert prototype.DEFAULT_AXIS == "horizontal"
    assert prototype.program_for("horizontal") == prototype.canonical_program()


def test_episode_parameter_is_fixed_and_demonstrations_distinguish_axis():
    prototype = load_prototype()
    for axis in prototype.ALLOWED_AXES:
        episode = prototype.build_episode(20261021, run_axis=axis)
        assert episode["parameter"] == {"run_axis": axis}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        other = prototype.other_axis(axis)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == prototype.apply_python(pair["input"], axis)
                assert pair["output"] != prototype.apply_python(pair["input"], other)


def test_public_challenge_hides_rule_and_query_labels():
    prototype = load_prototype()
    episode = prototype.build_episode(7, run_axis="vertical")
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    assert "run_axis" not in serialized
    assert "rule!" not in serialized


@pytest.mark.parametrize("bad", [True, 0, None, "diagonal"])
def test_invalid_axis_is_rejected(bad):
    prototype = load_prototype()
    with pytest.raises((TypeError, ValueError)):
        prototype.program_for(bad)
