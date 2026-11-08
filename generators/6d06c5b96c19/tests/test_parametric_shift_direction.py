"""Contract tests for the proposed task-local shift-direction prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "6d06c5b96c19"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    if not PROTOTYPE_PATH.is_file():
        pytest.fail(f"missing proposed prototype: {PROTOTYPE_PATH}")
    spec = importlib.util.spec_from_file_location("_shift_direction_prototype", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task missing")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_default_parametric_setting_is_exact_canonical_program() -> None:
    prototype = _load_prototype()
    assert prototype.PARAMETER_NAME == "shift_direction"
    assert prototype.ALLOWED_SETTINGS == ("down", "up")
    assert prototype.DEFAULT_SETTING == "down"
    assert prototype.program_for("down") == _canonical_program()
    assert _normalized_hash(prototype.program_for("down")) == prototype.CANONICAL_RULE_HASH
    assert prototype.program_for("up") != prototype.program_for("down")


def test_each_episode_uses_one_setting_and_refutes_the_other_in_training() -> None:
    prototype = _load_prototype()
    episodes = {
        setting: prototype.build_episode(20261023, setting=setting)
        for setting in prototype.ALLOWED_SETTINGS
    }
    down_inputs = [pair["input"] for split in ("train", "test") for pair in episodes["down"][split]]
    up_inputs = [pair["input"] for split in ("train", "test") for pair in episodes["up"][split]]
    assert down_inputs == up_inputs

    for setting, episode in episodes.items():
        assert episode["parameter"] == {prototype.PARAMETER_NAME: setting}
        assert episode["program"] == prototype.program_for(setting)
        assert prototype.episode_errors(episode) == []
        rival = next(value for value in prototype.ALLOWED_SETTINGS if value != setting)
        assert any(
            prototype.apply_python(pair["input"], setting)
            != prototype.apply_python(pair["input"], rival)
            for pair in episode["train"]
        )


def test_public_parametric_challenge_hides_rule_and_query_answer() -> None:
    prototype = _load_prototype()
    episode = prototype.build_episode(20261023, setting="up")
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "parameter" not in public and "program" not in public
