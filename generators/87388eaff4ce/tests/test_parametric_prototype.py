"""Prototype-only tests for the proposed tie-break parameter.

These do not alter or approve the selected canonical execution path.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

TASK_DIR = Path(__file__).resolve().parents[1]
PROTO = TASK_DIR / "workspace" / "parametric" / "prototype.py"


def load_proto():
    spec = importlib.util.spec_from_file_location("parametric_87388eaff4ce", PROTO)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_canonical_default():
    proto = load_proto()
    assert proto.PARAMETER_NAME == "tie_break"
    assert proto.ALLOWED_SETTINGS == ("color_asc", "color_desc")
    assert proto.DEFAULT_SETTING == "color_asc"
    assert proto.program_for("color_asc") != proto.program_for("color_desc")


@pytest.mark.parametrize("setting", ["color_asc", "color_desc"])
def test_complete_episode_fixes_one_setting_and_teaches_it(setting):
    proto = load_proto()
    episode = proto.generate_episode(41, setting=setting)
    assert episode["meta"]["tie_break"] == setting
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    assert episode["program"] == proto.program_for(setting)
    other = next(value for value in proto.ALLOWED_SETTINGS if value != setting)
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == proto.solve(pair["input"], setting)
        assert pair["output"] != proto.solve(pair["input"], other)


def test_seed_selects_setting_once_per_episode():
    proto = load_proto()
    first = proto.generate_episode(100)
    second = proto.generate_episode(101)
    assert first["meta"]["tie_break"] in proto.ALLOWED_SETTINGS
    assert second["meta"]["tie_break"] in proto.ALLOWED_SETTINGS
    assert first["meta"]["tie_break"] != second["meta"]["tie_break"]


def test_public_challenge_omits_hidden_setting_and_query_answer():
    proto = load_proto()
    episode = proto.generate_episode(41, setting="color_desc")
    challenge = proto.public_challenge(episode)
    assert "program" not in challenge
    assert "meta" not in challenge
    assert all("output" in pair for pair in challenge["train"])
    assert all("output" not in pair for pair in challenge["test"])
