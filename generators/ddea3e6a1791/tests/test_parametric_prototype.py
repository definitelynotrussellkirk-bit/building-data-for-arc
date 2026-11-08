"""Focused tests for the proposed episode-level background-color prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "ddea3e6a1791"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


def _load_prototype():
    spec = importlib.util.spec_from_file_location("ddea_parametric_prototype", PROTOTYPE_PATH)
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


def test_default_parameter_program_is_exact_canonical_rule():
    proto = _load_prototype()
    assert proto.PARAMETER_NAME == "background_color"
    assert proto.ALLOWED_VALUES == (0, 9)
    assert proto.DEFAULT_VALUE == 0
    assert _normalized_hash(proto.program_for(0)) == _normalized_hash(_canonical_program())


@pytest.mark.parametrize("background", [0, 9])
def test_complete_episode_fixes_one_setting_and_refutes_the_other(background):
    proto = _load_prototype()
    episode = proto.build_episode(20261019, background_color=background)
    assert episode["parameter"] == {"background_color": background}
    assert proto.episode_errors(episode) == []
    rival = proto.other_value(background)
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    for pair in episode["train"]:
        assert pair["output"] == proto.apply_python(pair["input"], background)
        assert pair["output"] != proto.apply_python(pair["input"], rival)


def test_public_challenge_hides_rule_parameter_and_query_answers():
    proto = _load_prototype()
    episode = proto.build_episode(8, background_color=9)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert "parameter" not in public and "program" not in public
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])


def test_invalid_parameter_values_are_rejected_without_coercion():
    proto = _load_prototype()
    for value in (False, True, 1, "0", None):
        with pytest.raises((TypeError, ValueError)):
            proto.program_for(value)
