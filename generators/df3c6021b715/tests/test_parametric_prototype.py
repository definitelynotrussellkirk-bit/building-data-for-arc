"""Focused tests for the proposed episode-level partition-axis prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "df3c6021b715"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "df3c6021b715_parametric_prototype", PROTOTYPE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load prototype at {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def test_default_axis_program_is_exact_canonical_rule():
    proto = _load_prototype()
    assert proto.PARAMETER_NAME == "partition_axis"
    assert proto.ALLOWED_AXES == ("horizontal", "vertical")
    assert proto.DEFAULT_AXIS == "horizontal"
    assert _normalized_hash(proto.program_for("horizontal")) == _normalized_hash(
        _canonical_program()
    )


@pytest.mark.parametrize("axis", ["horizontal", "vertical"])
def test_complete_episode_fixes_one_axis_and_refutes_the_other(axis):
    proto = _load_prototype()
    episode = proto.build_episode(20261019, partition_axis=axis)
    assert episode["parameter"] == {"partition_axis": axis}
    assert proto.episode_errors(episode) == []
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    rival = proto.other_axis(axis)
    for pair in episode["train"]:
        assert pair["output"] == proto.apply_python(pair["input"], axis)
        assert pair["output"] != proto.apply_python(pair["input"], rival)


def test_every_input_is_lawful_for_both_axis_settings():
    proto = _load_prototype()
    episode = proto.build_episode(73, partition_axis="horizontal")
    for split in ("train", "test"):
        for pair in episode[split]:
            assert proto.input_errors(pair["input"]) == []
            dots = proto.ordered_dots(pair["input"])
            assert len(dots) == 2
            assert len({dot[2] for dot in dots}) == 2


def test_public_challenge_hides_rule_parameter_and_query_answers():
    proto = _load_prototype()
    episode = proto.build_episode(8, partition_axis="vertical")
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert "parameter" not in public and "program" not in public
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])


def test_axis_is_selected_once_per_episode_and_invalid_values_are_rejected():
    proto = _load_prototype()
    first = proto.build_episode(17)
    second = proto.build_episode(17)
    assert first["parameter"] == second["parameter"]
    assert first == second
    for value in (False, True, 0, 1, "diagonal", "", None):
        with pytest.raises((TypeError, ValueError)):
            proto.program_for(value)
