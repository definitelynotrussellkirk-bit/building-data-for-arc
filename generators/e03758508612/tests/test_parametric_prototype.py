"""Focused tests for the proposed priority-direction prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil

import pytest

HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), f"missing runnable prototype: {PROTOTYPE_PATH}"
    spec = importlib.util.spec_from_file_location("e037_parametric_prototype", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_is_bounded_and_chosen_once_per_episode():
    proto = load_prototype()
    assert proto.ALLOWED_PRIORITY_DIRECTIONS == ("left_to_right", "right_to_left")
    assert proto.DEFAULT_PRIORITY_DIRECTION == "left_to_right"
    assert proto.choose_priority_direction(0) == "left_to_right"
    assert proto.choose_priority_direction(1) == "right_to_left"
    episode = proto.build_episode(seed=17)
    assert episode["parameter"]["priority_direction"] == "right_to_left"
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 1


def test_each_setting_has_exact_retained_racket_and_discriminating_demos():
    proto = load_prototype()
    for direction in proto.ALLOWED_PRIORITY_DIRECTIONS:
        path = proto.rule_path(direction)
        assert path.read_text() == proto.racket_program(direction)
        episode = proto.build_episode(seed=29, priority_direction=direction)
        alternative = next(
            value for value in proto.ALLOWED_PRIORITY_DIRECTIONS if value != direction
        )
        for pair in episode["train"]:
            expected = proto.python_fill(pair["input"], direction)
            rival = proto.python_fill(pair["input"], alternative)
            assert pair["output"] == expected
            assert rival != expected


@pytest.mark.skipif(shutil.which("racket") is None, reason="run through review.py run")
def test_racket_execution_matches_both_settings_and_public_query_is_masked():
    proto = load_prototype()
    for direction in proto.ALLOWED_PRIORITY_DIRECTIONS:
        episode = proto.build_episode(seed=41, priority_direction=direction)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert proto.run_racket(direction, pair["input"]) == pair["output"]
        public = proto.public_challenge(episode)
        assert "parameter" not in public
        assert "output" not in public["test"][0]
